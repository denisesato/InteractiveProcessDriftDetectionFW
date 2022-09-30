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
from components.compare_models.metric_info import MetricInfo, MetricAdditionalInfo


class ControlFlowMetricInfo(MetricInfo):
    def __init__(self, window, trace, timestamp, metric_name):
        super().__init__(window, trace, timestamp, metric_name)

    def set_diff_added(self, diff):
        if len(diff) > 0:
            self.add_additional_info(MetricAdditionalInfo('Added', diff))

    def set_diff_removed(self, diff):
        if len(diff) > 0:
            self.add_additional_info(MetricAdditionalInfo('Removed', diff))
