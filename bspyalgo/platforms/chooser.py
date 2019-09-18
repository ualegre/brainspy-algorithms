# -*- coding: utf-8 -*-
"""Contains the platforms used in all SkyNEt experiments to be optimized by Genetic Algo.

The classes in Platform must have a method self.evaluate() which takes as arguments
the inputs inputs_wfm, the gene pool and the targets target_wfm. It must return
outputs as numpy array of shape (len(pool), inputs_wfm.shape[-1]).

Created on Wed Aug 21 11:34:14 2019

@author: HCRuiz
"""
import importlib
import numpy as np

from bspyalgo.utils.pytorch import TorchModel

# TODO: Add chip platform
# TODO: Add simulation platform
# TODO: Target wave form as argument can be left out if output dimension is known internally

# %% Chip platform to measure the current output from
# voltage configurations of disordered NE systems


def get_platform(platform_configs):
    '''Gets an instance of the determined class from Platforms.
    The classes in Platform must have a method self.evaluate() which takes as
    arguments the inputs inputs_wfm, the gene pool and the targets target_wfm.
    It must return outputs as numpy array of shape (self.genomes, len(self.target_wfm))
    '''
    if platform_configs['modality'] == 'single_chip':
        return SingleChip(platform_configs)
    elif platform_configs['modality'] == 'single_chip_simulation_nn':
        return SingleChipSimulationNN(platform_configs)
    elif platform_configs['modality'] == 'single_chip_simulation_kmc':
        return SingleChipSimulationKMC(platform_configs)
    else:
        raise NotImplementedError(f"Platform {platform_configs['modality']} is not recognized!")


class SingleChip:
    '''Platform which connects to a single boron-doped silicon chip through
    digital-to-analog and analog-to-digital converters. '''

    def __init__(self, platform_dict):
        pass

    def optimize(self, inputs_wfm, gene_pool, target_wfm):
        '''Optimisation function of the platform '''
        pass

# %% NN platform using models loaded form staNNet


class SingleChipSimulationNN:
    '''Platform which simulates a single boron-doped silicon chip using a
    torch-based neural network. '''

    def __init__(self, platform_dict):
        # Import required packages
        self.torch = importlib.import_module('torch')
        # self.staNNet = importlib.import_module('SkyNEt.modules.Nets.staNNet').staNNet

        # Initialize NN
        # self.net = self.staNNet(platform_dict['path2NN'])
        self.torch_model = TorchModel()
        self.torch_model.load_model(platform_dict['torch_model_path'])
        self.torch_model.model.eval()
        # Set parameters
        self.amplification = self.torch_model.get_model_info()['amplification']

        self.nn_input_dim = len(self.torch_model.get_model_info()['amplitude'])
        self.input_indices = platform_dict['input_indices']
        self.nr_control_genes = self.nn_input_dim - len(self.input_indices)

        print(f'Initializing NN platform with {self.nr_control_genes} control genes')
        self.control_indx = platform_dict['control_indices']
        assert self.nr_control_genes == len(self.control_indx)

        if platform_dict.__contains__('trafo_indx'):
            self.trafo_indx = platform_dict['trafo_indx']
            self.trafo = platform_dict['trafo']  # explicitly define the trafo func
        else:
            self.trafo_indx = None
            self.trafo = lambda x, y: x  # define trafo as identity

    def optimize(self, inputs_wfm, gene_pool, target_wfm):
        '''Optimisation function of the platform '''
        genomes = len(gene_pool)
        output_popul = np.zeros((genomes, target_wfm.shape[-1]))

        for j in range(genomes):
            # Feed input to NN
            # target_wfm.shape, genePool.shape --> (time-steps,) , (nr-genomes,nr-genes)
            control_voltage_genes = np.ones_like(target_wfm)[:, np.newaxis] * gene_pool[j, self.control_indx, np.newaxis].T
            control_voltage_genes_index = np.delete(np.arange(self.nn_input_dim), self.input_indices)
            # g.shape,x.shape --> (time-steps,nr-CVs) , (input-dim, time-steps)
            x_dummy = np.empty((control_voltage_genes.shape[0], self.nn_input_dim))  # dims of input (time-steps)xD_in
            # Set the input scaling
            # inputs_wfm.shape -> (nr-inputs,nr-time-steps)
            x_dummy[:, self.input_indices] = self.trafo(inputs_wfm, gene_pool[j, self.trafo_indx]).T
            x_dummy[:, control_voltage_genes_index] = control_voltage_genes

            output = self.torch_model.inference_in_nanoamperes(x_dummy)

            output_popul[j] = output[:, 0]

        return output_popul
# %% Simulation platform for physical MC simulations of devices


class SingleChipSimulationKMC:
    '''Platform which simulates a single boron-doped silicon chip using kinetic Monte Carlo. '''

    def __init__(self, platform_dict):
        pass

    def optimize(self, inputs_wfm, gene_pool, target_wfm):
        '''Optimisation function of the platform '''
        pass


# %% MAIN function (for debugging)
if __name__ == '__main__':

    # Define platform
    PLATFORM = {}
    PLATFORM['torch_model_path'] = r'/home/unai/Documents/3-programming/boron-doped-silicon-chip-simulation/checkpoint3000_02-07-23h47m.pt'
    PLATFORM['input_indices'] = [0, 5, 6]  # indices of NN input
    PLATFORM['control_indices'] = np.arange(4)  # indices of gene array

    SIMULATION = SingleChipSimulationNN(PLATFORM)

    OUTPUT = SIMULATION.optimize(np.array([[0.3, 0.5, 0], [0.3, 0.5, 0], [0.3, 0.5, 0]]),
                                 np.array([[0.1, -0.5, 0.33, -1.2], [0.1, -0.5, 0.33, -1.2]]),
                                 np.array([1, 1, 1]))

    print(f'nn output: \n {OUTPUT}')
