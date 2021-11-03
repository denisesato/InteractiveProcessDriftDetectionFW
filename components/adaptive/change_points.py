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
from components.adaptive.change_points_info import ChangePointsInfo


class ChangePoints:
    def __init__(self, attribute_name, activity, metrics_path):
        self.attribute_name = attribute_name
        self.activity = activity
        self.metrics_path = metrics_path
        self.lock = RLock()
        self.change_points = []
        self.change_points_info = ChangePointsInfo(attribute_name, activity)
        self.filename = os.path.join(self.metrics_path, f'ADWIN_change_points_{attribute_name}.txt')

    def add_cp(self, change_point):
        self.change_points.append(change_point)
        self.change_points_info.add_cp(change_point)

    def get_info(self):
        return self.change_points_info

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
        print(f'Saving drifts detected at [{self.change_points}] using attribute [{self.attribute_name}]')
