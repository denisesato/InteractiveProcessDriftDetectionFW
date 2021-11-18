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

from components.compare_models.compare_dfg import DfgEdgesSimilarityMetric, DfgEditDistanceMetric, \
    DfgNodesSimilarityMetric
from components.compare_time.compare_sojourn_time import SojournTimeSimilarityMetric, WaitingTimeSimilarityMetric, \
    SojournTimeSimilarityAdaptiveMetric
from enum import Enum

from components.parameters import Approach, AttributeAdaptive


class Metric(str, Enum):
    NODES = 'Nodes'
    EDGES = 'Edges'
    # EDIT_DISTANCE = 'Edit distance'
    # SOJOURN_TIME = 'Sojourn time'
    # WAITING_TIME = 'Waiting time'


class DfgDefinitions:
    def __init__(self):
        self.models_path = 'dfg'
        self.current_parameters = None
        self.metrics = None

    def set_current_parameters(self, current_parameters):
        self.current_parameters = current_parameters
        self.metrics = current_parameters.metrics

    def get_implemented_metrics(self):
        return Metric

    def get_default_metrics(self):
        return [Metric.NODES]

    def get_model_filename(self, log_name, window):
        map_file = f'{self.models_path}_w{window}.gv'
        return map_file

    def get_metrics_filename(self, current_parameters, metric_name):
        if current_parameters.approach == Approach.FIXED.name:
            filename = f'{metric_name}_winsize_{current_parameters.win_size}.txt'
        elif current_parameters.approach == Approach.ADAPTIVE.name:
            filename = f'{metric_name}_adaptive_{current_parameters.attribute}.txt'
        else:
            print(f'Incorrect approach: {current_parameters.approach} - using default name')
            filename = f'{metric_name}.txt'
        return filename

    def get_metrics_path(self, generic_metrics_path, original_filename):
        path = os.path.join(generic_metrics_path, self.models_path, original_filename)
        return path

    def get_models_path(self, generic_models_path, original_filename, activity):
        if self.current_parameters.approach == Approach.FIXED.name:
            dfg_models_path = os.path.join(generic_models_path, self.models_path, original_filename,
                                           f'winsize_{self.current_parameters.win_size}')
        elif self.current_parameters.approach == Approach.ADAPTIVE.name:
            dfg_models_path = os.path.join(generic_models_path, self.models_path, original_filename, activity,
                                           f'adaptive_{self.current_parameters.attribute}')
        else:
            print(f'Incorrect approach: {self.current_parameters.approach} - using default name')
            dfg_models_path = os.path.join(generic_models_path, self.models_path, original_filename, activity)
        return dfg_models_path

    def get_metrics_list(self):
        return self.metrics

    def metrics_factory(self, metric_name, window, initial_trace, name, m1, m2, l1, l2, parameters):
        # define todas as métricas existentes para o tipo de modelo de processo
        # porém só serão calculadas as escolhidas pelo usuário (definidas em self.metrics)
        classes = {
            Metric.EDGES.value: DfgEdgesSimilarityMetric(window, initial_trace, name, m1, m2),
            # Metric.EDIT_DISTANCE.value: DfgEditDistanceMetric(window, initial_trace, name, m1, m2),
            Metric.NODES.value: DfgNodesSimilarityMetric(window, initial_trace, name, m1, m2),
            # Metric.SOJOURN_TIME.value: SojournTimeSimilarityMetric(window, initial_trace, name, l1, l2, parameters),
            # Metric.WAITING_TIME.value: WaitingTimeSimilarityMetric(window, initial_trace, name, l1, l2, parameters)
        }
        return classes[metric_name]

    def adaptive_metrics_factory(self, metric_name, window, initial_trace, change_point, total_of_activities):
        # define todas as métricas existentes para o tipo de modelo de processo
        # porém só serão calculadas as escolhidas pelo usuário (definidas em self.metrics)
        classes = {
            AttributeAdaptive.SOJOURN_ACTIVITY_TIME.name: SojournTimeSimilarityAdaptiveMetric(window, initial_trace, metric_name, change_point, total_of_activities),
        }
        return classes[metric_name]
