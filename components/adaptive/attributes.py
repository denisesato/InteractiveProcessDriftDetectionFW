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
from enum import Enum

from components.parameters import AttributeAdaptive


class Activity(str, Enum):
    ALL = 'all'


class SelectAttribute:
    @staticmethod
    def get_selected_attribute_class(attribute_name):
        # define the class for each available attribute for applying the change detector
        # the one selected by the user is returned
        classes = {
            AttributeAdaptive.SOJOURN_TIME.name: SojournTime(attribute_name),
            AttributeAdaptive.WAITING_TIME.name: WaitingTime(attribute_name)
        }
        return classes[attribute_name]


# classes for the specific attribute that can be used for the change detector
class SojournTime:
    def __init__(self, name):
        self.name = name

    def get_value(self, event):
        # get the duration of the event
        # the input must be an interval log
        start_time = event['start_timestamp'].timestamp()
        complete_time = event['time:timestamp'].timestamp()
        duration = complete_time - start_time
        return duration


class WaitingTime:
    def __init__(self, name):
        self.name = name

    def get_value(self, event):
        # the input must be an interval log
        # return the wasted time ONLY with regards to the activity described by the ‘interval’ event
        waiting_time = event['@@approx_bh_this_wasted_time']
        return waiting_time
