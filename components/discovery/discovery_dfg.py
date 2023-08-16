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
from pm4py.visualization.dfg import visualizer as dfg_visualization
from pm4py.algo.filtering.dfg import dfg_filtering
from components.dfg_definitions import DfgDefinitions
from components.discovery.discovery import Discovery


class DiscoveryDfg(Discovery):
    def __init__(self):
        self.model_type_definitions = DfgDefinitions()

    def set_current_parameters(self, current_parameters):
        self.model_type_definitions.set_current_parameters(current_parameters)

    # mine the DFG (directly-follows graph) from the sub-log
    # defined by the windowing strategy
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count, activity='',
                               save_model_svg=False):
        # create the folder for saving the process map if does not exist
        models_path = self.model_type_definitions.get_models_path(models_path, event_data_original_name, activity)
        if not os.path.exists(models_path):
            os.makedirs(models_path)

        # mine the DFG (using Pm4Py)
        # DMVS CONFERIR
        activities_dict = pm4py.get_event_attribute_values(sub_log, 'concept:name', case_id_key='case:concept:name')

        dfg, sa, ea = pm4py.discover_directly_follows_graph(sub_log)
        # filter only 6% of paths - FOR UTFPR analysis
        # percentual_paths = 0.006
        # TODO - define a parameter
        percentual_paths = 1
        dfg, sa, ea, activities_count = dfg_filtering.filter_dfg_on_paths_percentage(dfg, sa, ea,
                                                                                     activities_dict, percentual_paths)

        # save the process model
        if activity and activity != '':  # adaptive approach generates models per activity
            output_filename = self.model_type_definitions.get_model_filename(event_data_original_name,
                                                                             w_count[activity])
            output_filename_svg = os.path.join(models_path, self.model_type_definitions.get_model_filename_svg(w_count[activity]))
        else:  # fixed approach generate the models based on the window size
            output_filename = self.model_type_definitions.get_model_filename(event_data_original_name, w_count)
            output_filename_svg = os.path.join(models_path, self.model_type_definitions.get_model_filename_svg(w_count))

        print(f'Saving {models_path} - {output_filename}')
        parameters = {dfg_visualization.Variants.FREQUENCY.value.Parameters.START_ACTIVITIES: sa,
                      dfg_visualization.Variants.FREQUENCY.value.Parameters.END_ACTIVITIES: ea}
        gviz = dfg_visualization.apply(dfg, log=sub_log, parameters=parameters)
        gviz.save(filename=output_filename, directory=models_path)

        if save_model_svg:
            print(f'Saving {models_path} - {output_filename} - SVG format')
            pm4py.save_vis_performance_dfg(dfg, sa, ea, output_filename_svg)
        return dfg
