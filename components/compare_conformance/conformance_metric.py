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
from components.compare_conformance.conformance_metric_info import ConformanceMetricInfo
from components.metric import Metric


class ConformanceMetric(Metric):
    def __init__(self, window, trace, metric_name, model1, model2, sublog1, sublog2):
        super().__init__(window, metric_name)
        self.model1 = model1
        self.model2 = model2
        self.sublog1 = sublog1
        self.sublog2 = sublog2
        self.initial_trace = trace
        self.metric_info = ConformanceMetricInfo(window, trace, metric_name)

    def get_info(self):
        return self.metric_info

    def is_dissimilar(self):
        pass

    def run(self):
        value = self.calculate()
        self.metric_info.set_value(value)
        self.save_metrics()
