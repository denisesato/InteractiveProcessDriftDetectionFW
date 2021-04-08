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
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization

from components.dfg_definitions import DfgDefinitions
from components.discovery.discovery import Discovery


class DiscoveryDfg(Discovery):
    def __init__(self):
        self.model_type_definitions = DfgDefinitions()

    # mine the DFG (directly-follows graph) from the sub-log
    # defined by the windowing strategy
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count):
        # create the folder for saving the process map if does not exist
        dfg_models_path = self.model_type_definitions.get_models_path(models_path, event_data_original_name)
        if not os.path.exists(dfg_models_path):
            os.makedirs(dfg_models_path)

        # mine the DFG (using Pm4Py)
        dfg = dfg_discovery.apply(sub_log)
        gviz = dfg_visualization.apply(dfg, log=sub_log)

        # save the process model
        output_filename = self.model_type_definitions.get_model_filename(event_data_original_name, w_count)
        print(f'Saving {dfg_models_path} - {output_filename}')
        Source.save(gviz, filename=output_filename, directory=dfg_models_path)

    def get_process_model(self, models_path, log_name, window):
        map_file = self.model_type_definitions.get_model_filename(log_name, window)

        dfg_models_path = self.model_type_definitions.get_models_path(models_path, log_name)

        if os.path.exists(os.path.join(dfg_models_path, map_file)):
            gviz = Source.from_file(filename=map_file, directory=dfg_models_path)
            return gviz.source

        return """
            digraph  {
              node[style="filled"]
              a ->b->d
              a->c->d
            }
            """
