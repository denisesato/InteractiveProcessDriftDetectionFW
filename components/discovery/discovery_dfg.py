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
import pm4py
from graphviz import Source
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from components.dfg_definitions import DfgDefinitions
from components.discovery.discovery import Discovery


class DiscoveryDfg(Discovery):
    def __init__(self):
        self.model_type_definitions = DfgDefinitions()

    def set_current_parameters(self, current_parameters):
        self.model_type_definitions.set_current_parameters(current_parameters)

    # mine the DFG (directly-follows graph) from the sub-log
    # defined by the windowing strategy
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count, activity=''):
        # create the folder for saving the process map if does not exist
        models_path = self.model_type_definitions.get_models_path(models_path, event_data_original_name, activity)
        if not os.path.exists(models_path):
            os.makedirs(models_path)

        # mine the DFG (using Pm4Py)
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(sub_log)
        parameters = {dfg_visualization.Variants.FREQUENCY.value.Parameters.START_ACTIVITIES: start_activities,
                      dfg_visualization.Variants.FREQUENCY.value.Parameters.END_ACTIVITIES: end_activities}
        gviz = dfg_visualization.apply(dfg, log=sub_log, parameters=parameters)
        # dfg = dfg_discovery.apply(sub_log, variant=dfg_discovery.Variants.PERFORMANCE)
        # gviz = dfg_visualization.apply(dfg, log=sub_log, variant=dfg_visualization.Variants.PERFORMANCE)

        # save the process model
        if activity and activity != '': # adaptive approach generates models per activity
            output_filename = self.model_type_definitions.get_model_filename(event_data_original_name, w_count[activity])
        else: # fixed approach generate the models based on the window size
            output_filename = self.model_type_definitions.get_model_filename(event_data_original_name, w_count)
        print(f'Saving {models_path} - {output_filename}')
        # Source.save(gviz, filename=output_filename, directory=models_path)
        gviz.save(filename=output_filename, directory=models_path)
        return gviz

