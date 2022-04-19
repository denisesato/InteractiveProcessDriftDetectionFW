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
from enum import Enum
from components.parameters import Approach


class PnDefinitions:
    def __init__(self):
        self.model_path = 'pn'
        self.current_parameters = None

    def set_current_parameters(self, current_parameters):
        self.current_parameters = current_parameters

    def get_model_filename(self, log_name, window):
        map_file = f'{self.model_path}_w{window}.gv'
        return map_file

    def get_metrics_filename(self, current_parameters, metric_name):
        filename = f'{metric_name}_winsize_{current_parameters.winsize}.txt'
        return filename

    def get_metrics_path(self, generic_metrics_path, original_filename):
        path = os.path.join(generic_metrics_path, self.model_path, original_filename)
        return path

    def get_models_path(self, generic_models_path, original_filename, activity):
        if self.current_parameters.approach == Approach.FIXED.name:
            models_path = os.path.join(generic_models_path, self.models_path, original_filename, activity,
                                       f'winsize_{self.current_parameters.win_size}')
        elif self.current_parameters.approach == Approach.ADAPTIVE.name:
            models_path = os.path.join(generic_models_path, self.models_path, original_filename, activity,
                                       f'adaptive_{self.current_parameters.attribute}')
        else:
            print(f'Incorrect approach: {self.current_parameters.approach} - using default name')
            models_path = os.path.join(generic_models_path, self.models_path, original_filename, activity)
        return models_path

    def get_implemented_metrics(self):
        return []

    def get_default_metrics(self):
        return []

    def metrics_factory(self, metric_name, window, initial_trace, name, m1, m2, l1, l2):
        # define todas as métricas existentes para o tipo de modelo de processo
        # porém só serão calculadas as escolhidas pelo usuário (definidas em self.metrics)
        # classes = {
        #     Metric.PLACES.value: PlacesSimilarityMetric(window, initial_trace, name, m1, m2, l1, l2),
        #     Metric.TRANSITIONS.value: TransitionsSimilarityMetric(window, initial_trace, name, m1, m2, l1, l2),
        # }
        # return classes[metric_name]
        pass


class PNModel:
    def __init__(self, net, im, fm):
        self.net = net
        self.initial_marking = im
        self.final_marking = fm
