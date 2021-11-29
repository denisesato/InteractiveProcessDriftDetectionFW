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
from components.parameters import AttributeAdaptive


class SelectAttribute:
    @staticmethod
    def get_selected_attribute_class(attribute_name):
        # define todas as classes de atributo disponíveis
        # porém só será retornada aquela escolhida pelo usuário
        classes = {
            AttributeAdaptive.SOJOURN_ACTIVITY_TIME.name: SojournActivityTime(attribute_name),
        }
        return classes[attribute_name]


class SojournActivityTime:
    def __init__(self, name):
        self.name = name

    def get_value(self, event):
        # get the duration of the event
        # the input must be an interval log
        start_time = event['start_timestamp'].timestamp()
        complete_time = event['time:timestamp'].timestamp()
        duration = complete_time - start_time
        return duration
