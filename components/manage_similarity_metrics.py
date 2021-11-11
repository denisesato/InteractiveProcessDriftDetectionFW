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
import time
from threading import RLock, Thread
from components.dfg_definitions import DfgDefinitions
from json_tricks import loads

from components.parameters import Approach
from components.pn_definitions import PnDefinitions


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class ManageSimilarityMetrics:
    def __init__(self, model_type, current_parameters, control, models_path, metrics_path):
        print(f'**************************************************************************')
        print(f'*************** Similarity metrics calculation started *******************')
        print(f'**************************************************************************')

        self.current_parameters = current_parameters
        self.final_window = 0
        self.metrics_count = 0
        self.control = control
        self.models_path = models_path
        self.model_type = model_type

        if self.model_type == 'dfg':
            self.model_type_definitions = DfgDefinitions()
        elif self.model_type == 'pn':
            self.model_type_definitions = PnDefinitions()
        else:
            print(f'Model type [{self.model_type}] does not have similarity metrics implemented.')
            self.finish()
            self.metrics_list = None
            return None

        # get the metrics selected by the user
        self.metrics_list = current_parameters.metrics
        # Create a locker for each metric to manage the access to the file where the information is saved
        self.locks = {}
        for m in self.metrics_list:
            self.locks[m] = RLock()
        if self.current_parameters.approach == Approach.ADAPTIVE.name:
            self.locks[self.current_parameters.attribute] = RLock()

        # Define the path for the metrics file
        # IPDD creates one file by each implemented metric
        self.metrics_path = self.model_type_definitions.get_metrics_path(metrics_path, self.current_parameters.logname)
        # Check if the folder already exists, and create it if not
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

        self.filenames = {}
        self.verify_files()
        self.running = False
        self.timeout = 60  # in seconds
        self.time_started = None

    # organize the file's structure for storing information about the
    # calculated metrics
    def verify_files(self):
        for metric in self.metrics_list:
            self.create_file(metric)
        if self.current_parameters.approach == Approach.ADAPTIVE.name:
            self.create_file(self.current_parameters.attribute)

    def create_file(self, metric):
        self.filenames[metric] = os.path.join(self.metrics_path,
                                              self.model_type_definitions.get_metrics_filename(
                                                  self.current_parameters, metric))

        # if the file already exists, IPDD deletes it
        if os.path.exists(self.filenames[metric]):
            print(f'Deleting file {self.filenames[metric]}')
            os.remove(self.filenames[metric])

        # create the file
        with open(self.filenames[metric], 'w+') as fp:
            pass

    def set_final_window(self, w):
        print(f'Setting final window value {w}')
        self.final_window = w

    def calculate_metrics(self, current_window, sublog1, sublog2, model1, model2, parameters, initial_trace=None):
        # print(f'Starting to calculate similarity metrics between windows [{current_window-1}]-[{current_window}] ...')
        # calculate the chosen metrics and save the values on the file
        print(f'calculate_metrics - current window {current_window} - initial_trace = {initial_trace}')
        self.calculate_configured_similarity_metrics(current_window, initial_trace, model1, model2, sublog1, sublog2,
                                                     parameters)

    def calculate_adaptive_metrics(self, current_window, change_point, parameters, initial_trace=None):
        print(
            f'Starting to calculate adaptive similarity metrics between windows [{current_window - 1}]-[{current_window}] ...')
        # calculate the chosen metrics and save the values on the file
        print(f'calculate_metrics - current window {current_window} - initial_trace = {initial_trace}')
        self.calculate_adaptive_similarity_metrics(current_window, initial_trace, change_point, parameters)

    def calculate_configured_similarity_metrics(self, current_window, initial_trace, m1, m2, l1, l2, parameters):
        self.model_type_definitions.set_current_parameters(self.current_parameters)
        for metric_name in self.metrics_list:
            print(f'Starting [{metric_name}] calculation between windows [{current_window - 1}-{current_window}]')
            metric = self.model_type_definitions.metrics_factory(metric_name, current_window,
                                                                 initial_trace, metric_name, m1, m2, l1, l2, parameters)

            metric.set_saving_definitions(self.filenames[metric_name], self.current_parameters, self.locks[metric_name],
                                          self)
            metric.start()

    def calculate_adaptive_similarity_metrics(self, current_window, initial_trace, change_point, parameters):
        print(
            f'Starting [{parameters.attribute}] calculation between windows [{current_window - 1}-{current_window}] - '
            f'change point [{change_point}]')
        metric = self.model_type_definitions.adaptive_metrics_factory(parameters.attribute, current_window,
                                                                      initial_trace, change_point,
                                                                      parameters.total_of_activities)

        metric.set_saving_definitions(self.filenames[parameters.attribute], self.current_parameters,
                                      self.locks[parameters.attribute], self)
        metric.start()

    def increment_metrics_count(self):
        self.metrics_count += 1

    def check_finish(self):
        # print(
        #     f'check_finish - final_window {self.final_window} - metrics_count {self.metrics_count} - total de metricas {len(self.metrics_list)}')
        # TODO this is the check for tumbling windows
        # check to create a check that works with tumbling and sliding windows
        if self.final_window != 0 and self.metrics_count == (
                self.final_window * len(self.metrics_list)):  # for tumbling windows
            # if self.final_window != 0 and self.metrics_count == (self.final_window / 2 * len(self.metrics_list)): # for sliding windows
            self.finish()

    @threaded
    def check_metrics_timeout(self):
        print(f'**************************************************************************')
        print(f'Starting monitoring thread for similarity metrics calculation')
        print(f'**************************************************************************')
        while self.running:
            calculated_timeout = self.time_started + self.timeout
            if time.time() > calculated_timeout:
                print(f'******* Timeout reached ********')
                self.running = False
                self.control.time_out_metrics_calculation()
        print(f'**************************************************************************')
        print(f'Finishing monitoring thread for metrics calculation')
        print(f'**************************************************************************')

    def start_metrics_timeout(self):
        # for managing metrics' timeout
        self.running = True
        self.time_started = time.time()
        self.check_metrics_timeout()

    def finish(self):
        print(f'\n**************************************************************************')
        print(f'*** Similarity metrics calculation finished for the file {self.current_parameters.logname}')
        print(f'**************************************************************************')
        self.running = False
        self.control.finish_metrics_calculation()

    def consider_metric(self, m, candidates):
        self.locks[m].acquire()
        with open(self.filenames[m], "r") as file:
            for line in file:
                metrics_info = loads(line, ignore_comments=True)
                if metrics_info.is_dissimilar():
                    candidates.add(metrics_info.window)
        self.locks[m].release()

    def get_window_candidates(self):
        candidates = set()
        # avoiding errors when the process model does not have any similarity metric implemented yet
        if self.metrics_list:
            for m in self.metrics_list:
                self.consider_metric(m, candidates)
            if self.current_parameters.approach == Approach.ADAPTIVE.name:
                self.consider_metric(self.current_parameters.attribute, candidates)

            if self.current_parameters.approach == Approach.FIXED.name:
                filename = os.path.join(self.metrics_path,
                                        f'winsize_{self.current_parameters.win_size}_drift_windows.txt')
            elif self.current_parameters.approach == Approach.ADAPTIVE.name:
                filename = os.path.join(self.metrics_path, f'adaptive_drift_windows.txt')
            else:
                filename = os.path.join(self.metrics_path, f'_drift_windows.txt')
            print(f'Saving drift windows: {filename}')
            with open(filename, 'w+') as file_drift_windows:
                file_drift_windows.write(str(candidates))
        return candidates

    def get_info(self, m, window, metrics):
        self.locks[m].acquire()
        with open(self.filenames[m], "r") as file:
            for line in file:
                metric_read = loads(line, ignore_comments=True)
                if metric_read.window == window and metric_read.is_dissimilar():
                    metrics.append(metric_read)
                    break
        self.locks[m].release()

    def get_metrics_info(self, window):
        metrics = []
        # avoiding errors when the process model does not have any similarity metric implemented yet
        if self.metrics_list:
            for m in self.metrics_list:
                self.get_info(m, window, metrics)
        if self.current_parameters.approach == Approach.ADAPTIVE.name:
            self.get_info(self.current_parameters.attribute, window, metrics)
        return metrics
