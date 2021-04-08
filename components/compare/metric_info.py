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
from json_tricks import dumps

class MetricInfo:
    def __init__(self, window, metric_name):
        self.diff_added = set()
        self.diff_removed = set()
        self.value = 0
        self.window = window
        self.metric_name = metric_name

    def serialize(self):
        result = dumps(self)
        return result

    def set_value(self, value):
        self.value = value

    def set_diff_added(self, diff):
        self.diff_added = diff

    def set_diff_removed(self, diff):
        self.diff_removed = diff

    def serialize(self):
        result = dumps(self)
        return result