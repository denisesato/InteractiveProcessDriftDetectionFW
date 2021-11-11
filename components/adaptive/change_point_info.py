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
    def __init__(self, attribute_name, cp):
        self.attribute_name = attribute_name
        self.change_point = cp
        self.info = []
        self.activities = []

    def add_activity(self, activity):
        self.activities.append(activity)

    def add_additional_info(self, additional_info):
        self.info.append(additional_info)

    def serialize(self):
        result = dumps(self)
        return result

    def get_additional_info(self):
        return self.info

    def __str__(self):
        info = f'Attribute name: {self.attribute_name_name}\n'
        info = f'Activities: {self.activities}\n'
        info += f'Window: {self.window}\n'
        info += f'Initial trace: {self.initial_trace}\n'
        info += f'Change point (final trace): {self.change_point}\n'
        info += f'Additional info: {[info.get_status_info() for info in self.info]}\n'
        return info


class AdditionalInfo:
    def __init__(self, name, information_set):
        self.name = name
        self.information_set = information_set

    def get_status_info(self):
        strType = f'{self.name}: '
        strList = ''
        for info in self.information_set:
            strList += f'[{info}] '
        return strType, strList
