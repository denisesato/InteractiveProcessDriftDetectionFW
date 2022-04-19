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
from components.compare_models.controlflow_metric_info import ControlFlowMetricInfo
from components.metric import Metric


class ControlFlowMetric(Metric):
    def __init__(self, window, trace, metric_name, model1, model2, sublog1, sublog2):
        super().__init__(window, metric_name)
        self.diff_added = set()
        self.diff_removed = set()
        self.model1 = model1
        self.model2 = model2
        self.sublog1 = sublog1
        self.sublog2 = sublog2

        self.initial_trace = trace
        self.metric_info = ControlFlowMetricInfo(window, trace, metric_name)

    def is_dissimilar(self):
        pass

    def run(self):
        value, diff_added, diff_removed = self.calculate()
        self.metric_info.set_value(value)
        self.metric_info.set_diff_added(diff_added)
        self.metric_info.set_diff_removed(diff_removed)
        self.metric_info.set_dissimilar(self.is_dissimilar())
        self.save_metrics()
