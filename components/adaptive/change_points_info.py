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


class ChangePointInfo:
    def __init__(self, detector, activity):
        self.detector = detector
        self.activity = activity
        self.change_points = []

    def add_change_point(self, cp):
        self.change_points.append(cp)

    def serialize(self):
        result = dumps(self)
        return result

    def __str__(self):
        info = f'Change points detected using detector {self.detector}\n'
        info += f'Activity: {self.activity}\n'
        info += f'Change points: {self.change_points}'
        return info
