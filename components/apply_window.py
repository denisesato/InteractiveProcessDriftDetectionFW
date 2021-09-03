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
from threading import Thread
from enum import Enum
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventStream, EventLog
from datetime import datetime, date
from components.manage_similarity_metrics import ManageSimilarityMetrics


class WindowType(str, Enum):
    TRACE = 'Stream of Traces'
    EVENT = 'Event Stream'


class WindowUnity(str, Enum):
    UNITY = 'Item'
    HOUR = 'Hours'
    DAY = 'Days'


class WindowInitialIndex(str, Enum):
    TRACE_INDEX = 'Trace index'
    TRACE_CONCEPT_NAME = 'Trace concept name'


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class AnalyzeDrift:
    def __init__(self, model_type, current_parameters, control, input_path,
                 models_path, metrics_path, current_log, discovery):
        self.current_parameters = current_parameters
        self.control = control
        self.input_path = input_path
        self.models_path = models_path
        self.metrics_path = metrics_path
        self.model_type = model_type
        # current loaded event log information
        self.current_log = current_log
        # class that implements the discovery method for the current model
        self.discovery = discovery

    # generate all the process models based on the windowing strategy
    # selected by the user and start the metrics calculation between
    # consecutive windows
    def generate_models(self):
        # get the current loaded event log
        event_data = self.current_log.log
        if event_data is not None:
            # iterate on the log (event by event or trace by trace)
            if self.current_parameters.wintype == WindowType.EVENT.name:
                # convert the log into an event stream
                event_data = log_converter.apply(event_data, variant=log_converter.Variants.TO_EVENT_STREAM)

            # call for the implementation of the different windowing strategies
            # TODO: check if I can pass the AnalyzeDrift object instead of all this parameters
            windowing = ApplyWindowing(self.model_type, self.current_parameters, self.control, self.input_path,
                                       self.models_path, self.metrics_path, self.discovery)

            # execute actions for a checkpoint (end of a window)
            window_count, metrics_manager, initial_indexes = windowing.apply_window(event_data)

            # stores the instance of the metrics manager, responsible to manage the asynchronous
            # calculation of the metrics
            # no metrics manager instantiated when IPDD calculates one windows
            if metrics_manager:
                self.control.set_metrics_manager(metrics_manager)
            return window_count, initial_indexes


class ApplyWindowing:
    def __init__(self, model_type, current_parameters, control, input_path,
                 models_path, metrics_path, discovery):
        self.current_parameters = current_parameters
        self.input_path = input_path
        self.models_path = models_path
        self.window_count = 0
        self.model_type = model_type
        self.previous_sub_log = None
        self.previous_model = None
        self.discovery = discovery
        self.control = control
        self.metrics_path = metrics_path
        self.metrics = None

    def apply_window(self, event_data):
        initial_index = 0
        initial_indexes = {}
        initial_trace_index = None
        for i, item in enumerate(event_data):
            # get the current case id
            if self.current_parameters.wintype == WindowType.EVENT.name:
                case_id = item['case:concept:name']
            elif self.current_parameters.wintype == WindowType.TRACE.name:
                case_id = item.attributes['concept:name']
            else:
                print(f'Incorrect window type: {self.window_type}.')

            # calculate the time_difference (options hours, days)
            time_difference = 0
            if self.current_parameters.winunity == WindowUnity.UNITY.name:
                # nothing should be done, i is enough
                pass
            elif self.current_parameters.winunity == WindowUnity.HOUR.name:
                current_timestamp = self.get_current_timestamp(item)

                # initialize the initial timestamp of the first window
                if i == 0:
                    initial_timestamp = current_timestamp

                time_difference = current_timestamp - initial_timestamp
                # conversion to hours
                time_difference = time_difference / 60 / 60
            elif self.current_parameters.winunity == WindowUnity.DAY.name:
                current_date = self.get_current_date(item)

                # initialize the initial day of the first window
                if i == 0:
                    initial_day = date(current_date.year, current_date.month, current_date.day)

                # window checkpoint
                current_day = date(current_date.year, current_date.month, current_date.day)
                time_difference = current_day - initial_day
            else:
                print(f'Windowing strategy not implemented [{self.window_type}-{self.window_unity}].')

            # # initialize the initial case id of the first window
            if i == 0:
                initial_trace_index = case_id

            # window checkpoint
            if self.verify_window_ckeckpoint(i, event_data, time_difference):
                # process new window
                self.new_window(event_data, initial_index, i)
                # save information about the initial of the processed window
                initial_indexes[initial_index] = initial_trace_index

                # update the beginning of the next window
                initial_index = i
                initial_trace_index = case_id
                # store the initial timestamp or day of the next window
                if self.current_parameters.winunity == WindowUnity.HOUR.name:
                    initial_timestamp = current_timestamp
                elif self.current_parameters.winunity == WindowUnity.DAY.name:
                    initial_day = current_day
        # process remaining traces as last window
        if initial_index < len(event_data):
            size = len(event_data) - initial_index
            print(f'Analyzing final window... size {size} window_count {self.window_count}')
            # set the final window used by metrics manager to identify all the metrics have been calculated
            if self.window_count > 1:  # if it is only one window IPDD do not calculates any similarity metric
                self.metrics.set_final_window(self.window_count)
            # process final window
            self.new_window(event_data, initial_index, len(event_data))
            # save information about the initial of the processed window
            initial_indexes[initial_index] = initial_trace_index

        return self.window_count, self.metrics, initial_indexes

    def verify_window_ckeckpoint(self, i, event_data, time_difference=0):
        if self.current_parameters.winunity == WindowUnity.UNITY.name:
            if i > 0 and i % self.current_parameters.winsize == 0:
                return True
            return False
        elif self.current_parameters.winunity == WindowUnity.HOUR.name:
            if time_difference > self.current_parameters.winsize:
                return True
            return False
        elif self.current_parameters.winunity == WindowUnity.DAY.name:
            if time_difference.days > self.current_parameters.winsize:
                return True
            return False
        else:
            print(f'Incorrent windowing unity [{self.current_parameters.winunity}].')
        return False

    def get_current_timestamp(self, item):
        timestamp_aux = None
        # get the current timestamp
        if self.current_parameters.wintype == WindowType.EVENT.name:
            timestamp_aux = datetime.timestamp(item['time:timestamp'])
        elif self.current_parameters.wintype == WindowType.TRACE.name:
            # use the date of the first event within the trace
            timestamp_aux = datetime.timestamp(item[0]['time:timestamp'])
        else:
            print(f'Incorrect window type: {self.current_parameters.wintype}.')
        return timestamp_aux

    def get_current_date(self, item):
        date_aux = None
        if self.current_parameters.wintype == WindowType.EVENT.name:
            date_aux = item['time:timestamp']
        elif self.current_parameters.wintype == WindowType.TRACE.name:
            # use the date of the first event within the trace
            date_aux = item[0]['time:timestamp']
        else:
            print(f'Incorrect window type: {self.current_parameters.wintype}.')
        return date_aux

    def new_window(self, event_data, initial_index, i):
        # increment the id of the window
        self.window_count += 1

        if self.current_parameters.wintype == WindowType.EVENT.name:
            # generate the sub-log for the window
            window = EventStream(event_data[initial_index:i])
            sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
        elif self.current_parameters.wintype == WindowType.TRACE.name:
            sub_log = EventLog(event_data[initial_index:i])
        else:
            print(f'Incorrect window type: {self.current_parameters.wintype}.')

        self.execute_processes_for_window(sub_log)

    def execute_processes_for_window(self, sub_log):
        model = self.discovery.generate_process_model(sub_log, self.models_path, self.current_parameters.logname,
                                                      self.window_count)

        # if it is the second window initialize the Metrics Manager
        if self.window_count == 2:
            self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                                   self.models_path, self.metrics_path)
            self.metrics.start_metrics_timeout()
            self.control.start_metrics_calculation()

        # calculate the similarity metrics between consecutive windows
        if self.window_count > 1:
            self.metrics.calculate_metrics(self.window_count, self.previous_sub_log, sub_log, self.previous_model,
                                           model)
        # save the current model and sub_log for the next window
        self.previous_sub_log = sub_log
        self.previous_model = model
