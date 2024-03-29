"""
    This file is part of Interactive Process Drift (IPDD) Framework.
    IPDD is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    IPDD is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with IPDD. If not, see <https://www.gnu.org/licenses/>.
"""
import os

from graphviz import Source
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from components.discovery.discovery import Discovery
from components.pn_definitions import PnDefinitions, PNModel
from pm4py.visualization.petri_net import visualizer as pn_visualizer


class DiscoveryPn(Discovery):
    def __init__(self):
        self.model_type_definitions = PnDefinitions()

    def set_current_parameters(self, current_parameters):
        self.model_type_definitions.set_current_parameters(current_parameters)

    # mine the Petri Net from the sub-log
    # defined by the windowing strategy
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count, activity=''):
        # create the folder for saving the process map if does not exist
        models_path = self.model_type_definitions.get_models_path(models_path, event_data_original_name, activity)
        if not os.path.exists(models_path):
            os.makedirs(models_path)

        # mine the petri net (using Pm4Py - Inductive Miner)
        net, initial_marking, final_marking = inductive_miner.apply(sub_log)
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)

        # save the process model
        output_filename = self.model_type_definitions.get_model_filename(event_data_original_name, w_count)
        print(f'Saving {models_path} - {output_filename}')
        Source.save(gviz, filename=output_filename, directory=models_path)
        return PNModel(net, initial_marking, final_marking)

