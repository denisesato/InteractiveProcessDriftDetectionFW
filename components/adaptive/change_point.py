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
from threading import RLock
from components.adaptive.change_point_info import ChangePointInfo

# created when considering the change detector analysis for all the activities combined
# after we have changed to define change points per activity is not needed anymore
class ChangePoint:
    def __init__(self, attribute_name, cp, metrics_path):
        self.attribute_name = attribute_name
        self.cp = cp
        self.metrics_path = metrics_path
        self.lock = RLock()
        self.activities = []
        self.change_point_info = ChangePointInfo(attribute_name, cp)
        self.filename = os.path.join(self.metrics_path, f'ADWIN_change_points_{attribute_name}.txt')

    def add_activity(self, activity):
        self.activities.append(activity)
        self.change_point_info.add_activity(activity)

    def get_info(self):
        return self.change_point_info

    def get_value(self, event):
        pass

    def save_drift_info(self):
        # save the drift detected by the change detector
        self.lock.acquire()
        # update the file containing the metrics' values
        with open(self.filename, 'a+') as file:
            file.write(self.get_info().serialize())
            file.write('\n')
        self.lock.release()
        print(f'Saving drift detected at [{self.cp}], activities {self.activities}, using attribute [{self.attribute_name}]')
