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
from threading import Thread

import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.log import EventStream
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.util import dataframe_utils
from datetime import datetime, date

from components.compare.compare import ManageSimilarityMetrics
from components.discovery.discovery_dfg import DiscoveryDfg
from components.discovery.discovery_pn import DiscoveryPn


class WindowType:
    TRACE = 'TRACE'
    EVENT = 'EVENTO'


class WindowUnity:
    UNITY = 'ITEM'
    HOUR = 'HORA'
    DAY = 'DIA'


class WindowInitialIndex:
    TRACE_INDEX = 'TRACE_INDEX'
    TRACE_CONCEPT_NAME = 'TRACE_CONCEPT_NAME'


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class AnalyzeDrift:
    def __init__(self, model_type, window_type, window_unity, window_size, original_filename, control, input_path,
                 models_path, metrics_path):
        self.original_filename = original_filename
        self.window_type = window_type
        self.window_unity = window_unity
        self.window_size = window_size
        self.control = control
        self.input_path = input_path
        self.models_path = models_path
        self.metrics_path = metrics_path
        self.model_type = model_type

    # generate all the process models based on the windowing strategy
    # selected by the user and start the metrics calculation between
    # consecutive windows
    def generate_models(self):
        input = os.path.join(self.input_path, self.original_filename)
        print(f'Reading input file: {input}')

        # import the event log
        event_data = self.import_event_data(input)
        if event_data is not None:
            # iterate on the log (event by event or trace by trace)
            if self.window_type == WindowType.EVENT:
                # convert the log into an event stream
                event_data = log_converter.apply(event_data, variant=log_converter.Variants.TO_EVENT_STREAM)

            # call for the implementation of the different windowing strategies
            windowing = ApplyWindowing(self.model_type, self.window_type, self.window_unity, self.window_size,
                                       self.original_filename, self.control, self.input_path, self.models_path,
                                       self.metrics_path)

            # execute actions for a checkpoint (end of a window)
            window_count, metrics_manager, initial_indexes = windowing.apply_window(event_data)

            # stores the instance of the metrics manager, responsible to manage the asynchronous
            # calculation of the metrics
            self.control.set_metrics_manager(metrics_manager)
            return window_count, initial_indexes

    # import the event log (CSV ou XES)
    # currently only XES files are accepted
    def import_event_data(self, filename):
        event_data = None
        try:
            if 'csv' in filename:
                log_csv = pd.read_csv(filename, sep=';')
                log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
                # by now use a column named 'timestamp' for sorting the log
                # TODO change for allow the user to set the column
                log_csv = log_csv.sort_values('timestamp')
                event_data = log_converter.apply(log_csv)
            elif 'xes' in filename:
                variant = xes_importer.Variants.ITERPARSE
                # sorting by timestamp
                parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
                event_data = xes_importer.apply(filename, variant=variant, parameters=parameters)
        except Exception as e:
            print(e)
            print(f'Error trying to access the file {filename}')
        return event_data


class ApplyWindowing:
    def __init__(self, model_type, window_type, window_unity, window_size, original_filename, control, input_path, models_path, metrics_path):
        self.window_type = window_type
        self.window_unity = window_unity
        self.window_size = window_size
        self.original_filename = original_filename
        self.input_path = input_path
        self.metrics = ManageSimilarityMetrics(model_type, original_filename, control, models_path, metrics_path)
        self.models_path = models_path
        self.window_count = 0
        self.model_type = model_type

    def apply_window(self, event_data):
        initial_index = 0
        initial_indexes = {}
        initial_trace_index = None
        for i, item in enumerate(event_data):
            # get the current case id
            if self.window_type == WindowType.EVENT:
                case_id = item['case:concept:name']
            elif self.window_type == WindowType.TRACE:
                case_id = item.attributes['concept:name']
            else:
                print(f'Incorrect window type: {self.window_type}.')

            # calculate the time_difference (options hours, days)
            time_difference = 0
            if self.window_unity == WindowUnity.UNITY:
                # nothing should be done, i is enough
                pass
            elif self.window_unity == WindowUnity.HOUR:
                current_timestamp = self.get_current_timestamp(item)

                # initialize the initial timestamp of the first window
                if i == 0:
                    initial_timestamp = current_timestamp

                time_difference = current_timestamp - initial_timestamp
                # conversion to hours
                time_difference = time_difference / 60 / 60
            elif self.window_unity == WindowUnity.DAY:
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
                # if it is the last trace/event, increments the i to consider it within the window
                if i == len(event_data) - 1:
                    print(f'Analyzing final window...')
                    i += 1
                    self.metrics.set_final_window(self.window_count + 1)

                self.new_window(event_data, initial_index, i)

                # update the beginning of the next window
                initial_indexes[initial_index] = initial_trace_index
                initial_index = i
                initial_trace_index = case_id
                # store the initial timestamp or day of the next window
                if self.window_unity == WindowUnity.HOUR:
                    initial_timestamp = current_timestamp
                elif self.window_unity == WindowUnity.DAY:
                    initial_day = current_day
        return self.window_count, self.metrics, initial_indexes

    def verify_window_ckeckpoint(self, i, event_data, time_difference=0):
        if self.window_unity == WindowUnity.UNITY:
            if (i > 0 and i % self.window_size == 0) or i == len(event_data) - 1:
                return True
            return False
        elif self.window_unity == WindowUnity.HOUR:
            if time_difference > self.window_size or i == len(event_data) - 1:
                return True
            return False
        elif self.window_unity == WindowUnity.DAY:
            if time_difference.days > self.window_size or i == len(event_data) - 1:
                return True
            return False
        else:
            print(f'Incorrent windowing unity [{self.window_unity}].')
        return False

    def get_current_timestamp(self, item):
        timestamp_aux = None
        # get the current timestamp
        if self.window_type == WindowType.EVENT:
            timestamp_aux = datetime.timestamp(item['time:timestamp'])
        elif self.window_type == WindowType.TRACE:
            # use the date of the first event within the trace
            timestamp_aux = datetime.timestamp(item[0]['time:timestamp'])
        else:
            print(f'Incorrect window type: {self.window_type}.')
        return timestamp_aux

    def get_current_date(self, item):
        date_aux = None
        if self.window_type == WindowType.EVENT:
            date_aux = item['time:timestamp']
        elif self.window_type == WindowType.TRACE:
            # use the date of the first event within the trace
            date_aux = item[0]['time:timestamp']
        else:
            print(f'Incorrect window type: {self.window_type}.')
        return date_aux

    def new_window(self, event_data, initial_index, i):
        # increment the id of the window
        self.window_count += 1

        if self.window_type == WindowType.EVENT:
            # generate the sub-log for the window
            window = EventStream(event_data[initial_index:i])
            sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
        elif self.window_type == WindowType.TRACE:
            sub_log = event_data[initial_index:i]
        else:
            print(f'Incorrect window type: {self.window_type}.')
        self.execute_processes_for_window(sub_log)

    def execute_processes_for_window(self, sub_log):
        discovery = None
        # mine the process model and save it
        if self.model_type == 'dfg':
            discovery = DiscoveryDfg()
        elif self.model_type == 'pn':
            discovery = DiscoveryPn()
        else:
            print(f'Model type not implemented {self.model_type}')

        discovery.generate_process_model(sub_log, self.models_path, self.original_filename, self.window_count)

        # calculate the similarity metrics's between consecutive windows
        if self.window_count > 1 and self.model_type == 'dfg':
            self.metrics.calculate_metrics(self.window_count)

