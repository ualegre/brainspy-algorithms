'''
Library that handles saving data results from the execution of the algorithm.
'''
import os
import time
import json
import codecs
import pickle
import shutil
import torch
import yaml
import io

import numpy as np


def save(mode, file_path, **kwargs):  # filename, overwrite=False, timestamp=True, **kwargs):
   # if timestamp:
   #     path = create_directory_timestamp(path, 'experiment', overwrite=overwrite)
   # else:
   #     path = create_directory(path, overwrite=overwrite)
   # file_path = os.path.join(path, filename)

    if mode == 'numpy':
        np.savez(file_path, **kwargs)
    elif not kwargs['data']:
        raise ValueError(f"Value dictionary is missing in kwargs.")
    else:
        if mode == 'configs':
            save_configs(kwargs['data'], file_path)
        elif mode == 'pickle':
            save_pickle(kwargs['data'], file_path)
        elif mode == 'torch':
            save_torch(kwargs['data'], file_path)
        else:
            raise NotImplementedError(f"Mode {mode} is not recognised. Please choose a value between 'numpy', 'torch', 'pickle' and 'configs'.")
    # return path


def save_pickle(pickle_data, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(pickle_data, f)
        f.close()


def save_torch(torch_model, file_path):
    """
        Saves the model in given path, all other attributes are saved under
        the 'info' key as a new dictionary.
    """
    torch_model.eval()
    state_dic = torch_model.state_dict()
    state_dic['info'] = torch_model.info
    torch.save(state_dic, file_path)


# def load_configs(file):
#     object_text = codecs.open(file, 'r', encoding='utf-8').read()
#     return json.loads(object_text)


def load_configs(file_name):
    with open(file_name) as f:
        return yaml.load(f, Loader=IncludeLoader)


# def save_configs(configs, file):
#     with open(file, 'w') as f:
#         for key in configs:
#             if type(configs[key]) is np.ndarray:
#                 configs[key] = configs[key].tolist()
#         json.dump(configs, f, indent=4)
#         f.close()
def save_configs(configs, file_name):
    with open(file_name, 'w') as f:
        yaml.dump(configs, f, default_flow_style=False)


def create_directory(path, overwrite=False):
    '''
    This function checks if there exists a directory filepath+datetime_name.
    If not it will create it and return this path.
    '''
    if not os.path.exists(path):
        os.makedirs(path)
    elif overwrite:
        shutil.rmtree(path)
        os.makedirs(path)
    return path


def create_directory_timestamp(path, name, overwrite=False):
    datetime = time.strftime("%Y_%m_%d_%H%M%S")
    path = os.path.join(path, name + '_' + datetime)
    return create_directory(path, overwrite=overwrite)


class IncludeLoader(yaml.Loader):
    """
    yaml.Loader subclass handles "!include path/to/foo.yml" directives in config
    files.  When constructed with a file object, the root path for includes
    defaults to the directory containing the file, otherwise to the current
    working directory. In either case, the root path can be overridden by the
    `root` keyword argument.

    When an included file F contain its own !include directive, the path is
    relative to F's location.

    Example:
        YAML file /home/frodo/one-ring.yml:
            ---
            Name: The One Ring
            Specials:
                - resize-to-wearer
            Effects:
                - !include path/to/invisibility.yml

        YAML file /home/frodo/path/to/invisibility.yml:
            ---
            Name: invisibility
            Message: Suddenly you disappear!

        Loading:
            data = IncludeLoader(open('/home/frodo/one-ring.yml', 'r')).get_data()

        Result:
            {'Effects': [{'Message': 'Suddenly you disappear!', 'Name':
                'invisibility'}], 'Name': 'The One Ring', 'Specials':
                ['resize-to-wearer']}
    """

    def __init__(self, *args, **kwargs):
        super(IncludeLoader, self).__init__(*args, **kwargs)
        self.add_constructor('!include', self._include)
        if 'root' in kwargs:
            self.root = kwargs['root']
        elif isinstance(self.stream, io.TextIOWrapper):
            self.root = os.path.dirname(self.stream.name)
        else:
            self.root = os.path.curdir

    def _include(self, loader, node):
        oldRoot = self.root
        filename = os.path.join(self.root, loader.construct_scalar(node))
        self.root = os.path.dirname(filename)
        self.root = oldRoot
        with open(filename, 'r') as f:
            return yaml.load(f)


if __name__ == '__main__':

    GA_EVALUATION_CONFIGS = {}

    GA_EVALUATION_CONFIGS['platform'] = 'simulation'
    GA_EVALUATION_CONFIGS['simulation_type'] = 'neural_network'
    GA_EVALUATION_CONFIGS['torch_model_path'] = r'tmp/NN_model/checkpoint3000_02-07-23h47m.pt'

    GA_EVALUATION_CONFIGS['input_indices'] = [0, 5, 6]  # indices of NN input
    # TODO: See how to deal with the amplification parameters; possible source of semantic bugs
    GA_EVALUATION_CONFIGS['amplification'] = 10.

    # Parameters to define target waveforms
    GA_WAVEFORM_CONFIGS = {}
    GA_WAVEFORM_CONFIGS['lengths'] = 80     # Length of data in the waveform
    GA_WAVEFORM_CONFIGS['slopes'] = 0        # Length of ramping from one value to the next

    GA_HYPERPARAMETERS = {}

    # Voltage range of CVs in V
    GA_HYPERPARAMETERS['generange'] = [[-1.2, 0.6], [-1.2, 0.6], [-1.2, 0.6], [-0.7, 0.3], [-0.7, 0.3]]
    GA_HYPERPARAMETERS['partition'] = [5] * 5  # Partitions of population
    GA_HYPERPARAMETERS['mutationrate'] = 0.1
    GA_HYPERPARAMETERS['epochs'] = 100
    GA_HYPERPARAMETERS['fitness_function_type'] = 'corrsig_fit'
    GA_HYPERPARAMETERS['seed'] = None
    # Parameters to define the fitness function and the evaluation method (hardware or simulation dependent)

    GA_CONFIGS = {}

    GA_CONFIGS['save_path'] = r'./tmp/output/genetic_algorithm/'
    GA_CONFIGS['directory'] = 'OPTIMIZATION_TEST'

    GA_CONFIGS['hyperparameters'] = GA_HYPERPARAMETERS
    GA_CONFIGS['waveform_configs'] = GA_WAVEFORM_CONFIGS
    GA_CONFIGS['ga_evaluation_configs'] = GA_EVALUATION_CONFIGS    # Dictionary containing all variables for the platform

    save_configs(GA_CONFIGS, './configs/ga/ga_configs_template.json')

    # Make config dict for GD
    SGD_HYPERPARAMETERS = {}
    SGD_HYPERPARAMETERS['nr_epochs'] = 3000
    SGD_HYPERPARAMETERS['batch_size'] = 128
    SGD_HYPERPARAMETERS['learning_rate'] = 1e-4
    SGD_HYPERPARAMETERS['save_interval'] = 10

    SGD_MODEL_CONFIGS = {}
    SGD_MODEL_CONFIGS['input_indices'] = [0, 1]
    SGD_MODEL_CONFIGS['torch_model_path'] = r'tmp/NN_model/checkpoint3000_02-07-23h47m.pt'

    SGD_CONFIGS = {}
    SGD_CONFIGS['platform'] = 'simulation'
    SGD_CONFIGS['get_network'] = 'dnpu'
    SGD_CONFIGS['results_path'] = r'tmp/NN_test/'
    SGD_CONFIGS['experiment_name'] = 'TEST'
    SGD_CONFIGS['hyperparameters'] = SGD_HYPERPARAMETERS
    SGD_CONFIGS['model_configs'] = SGD_MODEL_CONFIGS

    save_configs(SGD_CONFIGS, './configs/gd/gd_configs_model_template.json')
