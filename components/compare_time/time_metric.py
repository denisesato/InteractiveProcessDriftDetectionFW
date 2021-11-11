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
from components.compare_time.time_metric_info import TimeMetricInfo
from components.metric import Metric


class TimeMetric(Metric):
    def __init__(self, window, trace, metric_name, sublog1, sublog2, parameters):
        super().__init__(window, metric_name)
        self.sublog1 = sublog1
        self.sublog2 = sublog2
        self.initial_trace = trace
        self.parameters = parameters
        self.metric_info = TimeMetricInfo(window, trace, metric_name)

    def is_dissimilar(self):
        pass

    def run(self):
        value, diff, activities = self.calculate()
        self.metric_info.set_value(value)
        self.metric_info.set_significant_difference(diff)
        self.metric_info.set_activities(activities)
        self.metric_info.set_dissimilar(self.is_dissimilar())
        self.save_metrics()


class TimeAdaptiveMetric(Metric):
    def __init__(self, window, trace, metric_name, change_point, total_of_activities):
        super().__init__(window, metric_name)
        self.initial_trace = trace
        self.change_point = change_point
        self.total_of_activities = total_of_activities
        self.metric_info = TimeMetricInfo(window, trace, metric_name)

    def is_dissimilar(self):
        pass

    def run(self):
        value, diff, activities = self.calculate()
        self.metric_info.set_value(value)
        self.metric_info.set_activities(activities)
        self.metric_info.set_dissimilar(self.is_dissimilar())
        self.save_metrics()
