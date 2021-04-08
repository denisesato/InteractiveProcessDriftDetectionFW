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

from app import app
from components.dfg_definitions import DfgDefinitions
from json_tricks import loads
# workaround for graphviz problem to release file handlers in windows
# import win32file as wfile


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class ManageSimilarityMetrics:
    def __init__(self, model_type, original_filename, control, models_path, metrics_path):
        print(f'**************************************************************************')
        print(f'*** Similarity metrics calculation started for the file {original_filename}')
        print(f'**************************************************************************')
        self.original_filename = original_filename
        self.final_window = 0
        self.metrics_count = 0
        self.control = control
        self.models_path = models_path
        self.model_type = model_type

        if self.model_type == 'dfg':
            self.model_type_definitions = DfgDefinitions()
        else:
            print(f'Model type [{self.model_type}] does not have similarity metrics implemented.')
            self.finish()
            self.metrics_list = None
            return

        self.metrics_list = self.model_type_definitions.get_metrics()

        # Create a locker for each metric to manage the access to the file where the information is saved
        self.locks = {}
        for m in self.metrics_list:
            self.locks[m] = RLock()

        # Define the path for the metrics's file
        # IPDD creates one file by each implemented metric
        self.metrics_path = self.model_type_definitions.get_metrics_path(metrics_path)
        # Check if the folder already exists, and create it if not
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

        self.filenames = {}

        self.verify_files()

        # for managing metrics' timeout
        self.timeout = 60  # in seconds
        self.time_started = time.time()
        self.running = True
        self.check_metrics_timeout()

        # workaround for graphviz problem - the library do not release file handlers
        # in windows - this should be verified again
        # change the maximum number of open files
        # wfile._setmaxstdio(8192)  # !!! COMMENT this line to reproduce the crash !!!
        # print(f'NEW max open files: {[wfile._getmaxstdio()]}')

    # organize the file's structure for storing information about the
    # calculated metrics
    def verify_files(self):
        for metric in self.metrics_list:
            self.filenames[metric] = os.path.join(self.metrics_path,
                                                  self.model_type_definitions.get_metrics_filename(
                                                      self.original_filename, metric))

            # if the file already exists, IPDD deletes it
            if os.path.exists(self.filenames[metric]):
                app.logger.info(f'Deleting file {self.filenames[metric]}')
                os.remove(self.filenames[metric])

            # create the file
            with open(self.filenames[metric], 'w+') as fp:
                pass

    def set_final_window(self, w):
        self.final_window = w

    def calculate_metrics(self, current_window):
        process_model1 = self.model_type_definitions.get_model_filename(self.original_filename, current_window - 1)
        process_model2 = self.model_type_definitions.get_model_filename(self.original_filename, current_window)

        models_path = self.model_type_definitions.get_models_path(self.models_path, self.original_filename)
        filename1 = os.path.join(models_path, process_model1)
        filename2 = os.path.join(models_path, process_model2)

        files_ok = False
        while not files_ok:
            if os.path.exists(filename1) and os.path.exists(filename2):
                files_ok = True
            elif not os.path.exists(filename1):
                print(f'[compare]: Problem trying to access process model from file [{process_model1}]')
            if not os.path.exists(filename2):
                print(f'[compare]: Problem trying to access process model from file [{process_model2}]')

        model1 = self.model_type_definitions.get_model_from_file(filename1, process_model1, models_path)
        model2 = self.model_type_definitions.get_model_from_file(filename2, process_model2, models_path)

        # print(f'Starting to calculate similarity metrics between windows [{current_window-1}]-[{current_window}] ...')

        # calculate the chosen metrics and save the values on the file
        self.calculate_configured_similarity_metrics(current_window, model1, model2)

    def calculate_configured_similarity_metrics(self, current_window, m1, m2):
        for metric_name in self.metrics_list:
            #print(f'Starting [{metric_name}] calculation between windows [{current_window}-{current_window-1}]')
            metric = self.model_type_definitions.metrics_factory(self.metrics_list[metric_name], current_window, metric_name, m1, m2)
            metric.set_saving_definitions(self.filenames[metric_name], self.locks[metric_name], self)
            metric.start()

    def increment_metrics_count(self):
        self.metrics_count += 1

    def check_finish(self):
        # print(f'Checking if similarity metrics calculation finished: metrics_count [{self.metrics_count}] - '
        #      f'total of calculated metrics [{((self.final_window - 1) * len(self.metrics_list))}]')
        if self.final_window != 0 and self.metrics_count == ((self.final_window - 1) * len(self.metrics_list)):
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

    def finish(self):
        print(f'\n**************************************************************************')
        print(f'*** Similarity metrics calculation finished for the file {self.original_filename}')
        print(f'**************************************************************************')
        self.running = False
        self.control.finish_metrics_calculation()

    def get_window_candidates(self):
        candidates = set()
        # avoiding errors when the process model does not have any similarity metric implemented yet
        if self.metrics_list:
            for m in self.metrics_list:
                self.locks[m].acquire()
                with open(self.filenames[m], "r") as file:
                    for line in file:
                        metrics_info = loads(line, ignore_comments=True)
                        candidates.add(metrics_info.window)
                self.locks[m].release()
            filename = os.path.join(self.metrics_path, self.original_filename + '_drift_windows.txt')
            print(f'Saving drift windows: {filename}')
            with open(filename, 'w+') as file_drift_windows:
                file_drift_windows.write(str(candidates))
        return candidates

    def get_metrics_info(self, window):
        metrics = []
        # avoiding errors when the process model does not have any similarity metric implemented yet
        if self.metrics_list:
            for m in self.metrics_list:
                self.locks[m].acquire()
                with open(self.filenames[m], "r") as file:
                    for line in file:
                        metric_read = loads(line, ignore_comments=True)
                        if metric_read.window == window:
                            metrics.append(metric_read)
                            break
                self.locks[m].release()
        return metrics
