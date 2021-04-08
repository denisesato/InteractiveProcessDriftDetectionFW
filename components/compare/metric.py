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
import threading

from components.compare.metric_info import MetricInfo

class Metric(threading.Thread):
    def __init__(self, window, metric_name, model1, model2):
        super().__init__()
        self.diff_added = set()
        self.diff_removed = set()
        self.value = 0
        self.window = window
        self.metric_name = metric_name
        self.model1 = model1
        self.model2 = model2
        self.metric_info = MetricInfo(window, metric_name)
        self.filename = None
        self.lock = None
        self.manager_similarity_metrics = None

    def set_saving_definitions(self, filename, lock, manager_similarity_metrics):
        self.filename = filename
        self.lock = lock
        self.manager_similarity_metrics = manager_similarity_metrics

    def get_info(self):
        return self.metric_info

    def save_metrics(self):
        if self.is_dissimilar():
            self.lock.acquire()
            # update the file containing the metrics' values
            with open(self.filename, 'a+') as file:
                file.write(self.get_info().serialize())
                file.write('\n')
            self.manager_similarity_metrics.increment_metrics_count()
            self.lock.release()
        else:
            self.manager_similarity_metrics.increment_metrics_count()
        print(f'Saving [{self.metric_name}] for windows [{self.window}-{self.window - 1}]')
        self.manager_similarity_metrics.check_finish()

    def run(self):
        value, diff_added, diff_removed = self.calculate()
        self.metric_info.set_value(value)
        self.metric_info.set_diff_added(diff_added)
        self.metric_info.set_diff_removed(diff_removed)
        self.save_metrics()