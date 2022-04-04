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
import numpy as np
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventStream, EventLog
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.util import interval_lifecycle
from datetime import datetime, date
from components.adaptive.attributes import SelectAttribute, Activity
from components.adaptive.change_points_info import ChangePointInfo
from components.parameters import Approach, AttributeAdaptive
from components.manage_similarity_metrics import ManageSimilarityMetrics
from skmultiflow.drift_detection.adwin import ADWIN
from components.parameters import ReadLogAs, WindowUnityFixed
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class AnalyzeDrift:
    def __init__(self, model_type, current_parameters, control, input_path,
                 models_path, metrics_path, logs_path, current_log, discovery, user,
                 drifts_output_path):

        self.current_parameters = current_parameters
        self.user = user
        self.control = control
        self.input_path = input_path
        self.models_path = models_path
        self.metrics_path = metrics_path
        self.logs_path = logs_path
        self.drifts_output_path = drifts_output_path
        self.model_type = model_type

        # instance of the MetricsManager
        if current_parameters.approach == Approach.FIXED.name:
            self.metrics = None
        elif current_parameters.approach == Approach.ADAPTIVE.name:
            self.metrics = {}

        # current loaded event log information
        self.current_log = current_log
        # convert to interval time log if needed
        self.converted_log = interval_lifecycle.to_interval(self.current_log.log)
        # set the event_data as requested by the user (read event by event or trace by trace)
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            self.event_data = self.converted_log
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # convert the log into an event stream
            self.event_data = log_converter.apply(self.converted_log, variant=log_converter.Variants.TO_EVENT_STREAM)
        else:
            self.event_data = self.converted_log
            print(
                f'The window type received is not defined for IPDD {self.current_parameters.read_log_as}, assuming STREAM OF TRACES')
        # class that implements the discovery method for the current model
        self.discovery = discovery

    # generate the plot with the attribute selected for a specific activity
    # used for adaptive change detection in an activity attribute
    def plot_signal(self, values_for_activity, activity_name, change_points=None):
        # save data and plot about the data
        df = pd.DataFrame([values_for_activity.keys(), values_for_activity.values()]).T
        df.columns = ['trace', 'value']
        if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
            filename_attributes = f'{activity_name}_{self.current_parameters.attribute_name}.csv'
        else:
            filename_attributes = f'{activity_name}_{self.current_parameters.attribute}.csv'
        output_filename = os.path.join(self.drifts_output_path, filename_attributes)
        df.to_csv(output_filename, index=False)
        sns.set_style("whitegrid")
        plot = sns.lineplot(data=df, x='trace', y='value')
        if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
            plot.set_ylabel(f'Activity {activity_name} - {self.current_parameters.attribute_name}')
        else:
            plot.set_ylabel(f'Activity {activity_name} - {self.current_parameters.attribute}')
        if change_points:
            for cp in change_points:
                plt.axvline(x=cp, color='r', linestyle=':')
        # save the plot
        if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
            filename = os.path.join(self.drifts_output_path, f'{activity_name}_{self.current_parameters.attribute_name}.png')
        else:
            filename = os.path.join(self.drifts_output_path, f'{activity_name}_{self.current_parameters.attribute}.png')
        plt.savefig(filename)
        print(f'Saving plot for activity [{activity_name}]')
        plt.close()
        plt.cla()
        plt.clf()

    # generate all the process models based on the windowing strategy
    # selected by the user and start the metrics calculation between
    # consecutive windows
    def start_drift_analysis(self):
        if self.current_parameters.approach == Approach.FIXED.name:
            self.window_count = 0
            self.previous_sub_log = None
            self.previous_model = None
        elif self.current_parameters.approach == Approach.ADAPTIVE.name:
            self.window_count = {}
            self.previous_sub_log = {}
            self.previous_model = {}

        metrics_manager = None
        if self.event_data is not None:
            # get the activities
            activities = self.get_all_activities()
            # call for the implementation of the different windowing strategies
            if self.current_parameters.approach == Approach.FIXED.name:
                window_count, metrics_manager, initial_indexes = self.apply_tumbling_window(self.event_data)
                # window_count, metrics_manager, initial_indexes = self.apply_sliding_window(event_data)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name:
                attribute_class = None
                if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
                    attribute_class = SelectAttribute.get_selected_attribute_class(
                        self.current_parameters.attribute,
                        self.current_parameters.attribute_name)
                else:
                    attribute_class = SelectAttribute.get_selected_attribute_class(
                        self.current_parameters.attribute)
                window_count, metrics_manager, initial_indexes = \
                    self.apply_detector(self.event_data,
                                        attribute_class,
                                        self.current_parameters.delta,
                                        activities,
                                        self.user)

            else:
                print(f'Incorrect approach: {self.current_parameters.approach}')

            # stores the instance of the metrics manager, responsible to manage the asynchronous
            # calculation of the metrics
            # no metrics manager instantiated when IPDD calculates one window
            if metrics_manager:
                self.control.set_metrics_manager(metrics_manager)
            return window_count, initial_indexes, activities

    # get the current case id from the trace or event
    def get_case_id(self, item):
        # get the initial case id of the window
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            case_id = item['case:concept:name']
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            case_id = item.attributes['concept:name']
        else:
            print(f'Incorrect window type: {self.window_type}.')
        return case_id

    # only for new trace or event
    def apply_sliding_window(self, event_data):
        initial_indexes = {}
        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)
        # check if there is at least two windows
        no_traces = len(event_data)
        if no_traces > self.current_parameters.win_size / 2:
            last_index = no_traces - self.current_parameters.win_size * 2 + 1
            print(f'for até {last_index}')
            for i in range(0, last_index):
                start_index_w1 = i
                start_index_w2 = i + self.current_parameters.win_size

                item = event_data[start_index_w1]
                case_id1 = self.get_case_id(item)
                item2 = event_data[start_index_w1]
                case_id2 = self.get_case_id(item2)
                initial_indexes[self.window_count + 1] = case_id1
                initial_indexes[self.window_count + 2] = case_id2

                if i == last_index - 1:
                    print(f'Analyzing final window... window_count {self.window_count}')
                    # set the final window used by metrics manager to identify all the metrics have been calculated
                    self.metrics.set_final_window(self.window_count + 2)

                # process and compare the two windows
                self.process_two_fixed_sliding_windows(event_data, start_index_w1, start_index_w2,
                                                       self.current_parameters.win_size)
        return self.window_count, self.metrics, initial_indexes

    def apply_tumbling_window(self, event_data):
        initial_index = 0
        initial_indexes = {}
        initial_trace_index = None

        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)

        for i, item in enumerate(event_data):
            # get the current case id
            case_id = self.get_case_id(item)

            # calculate the time_difference (options hours, days)
            time_difference = 0
            if self.current_parameters.win_unity == WindowUnityFixed.UNITY.name:
                # nothing should be done, i is enough
                pass
            elif self.current_parameters.win_unity == WindowUnityFixed.HOUR.name:
                current_timestamp = self.get_current_timestamp(item)

                # initialize the initial timestamp of the first window
                if i == 0:
                    initial_timestamp = current_timestamp

                time_difference = current_timestamp - initial_timestamp
                # conversion to hours
                time_difference = time_difference / 60 / 60
            elif self.current_parameters.win_unity == WindowUnityFixed.DAY.name:
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
                self.new_window(initial_index, i)
                # save information about the initial of the processed window
                initial_indexes[initial_index] = initial_trace_index

                # update the beginning of the next window
                initial_index = i
                initial_trace_index = case_id
                # store the initial timestamp or day of the next window
                if self.current_parameters.win_unity == WindowUnityFixed.HOUR.name:
                    initial_timestamp = current_timestamp
                elif self.current_parameters.win_unity == WindowUnityFixed.DAY.name:
                    initial_day = current_day
        # process remaining items as last window
        if initial_index < len(event_data):
            size = len(event_data) - initial_index
            print(f'Analyzing final window... size {size} window_count {self.window_count}')
            # set the final window used by metrics manager to identify all the metrics have been calculated
            self.metrics.set_final_window(self.window_count)
            # process final window
            self.new_window(initial_index, len(event_data))
            # save information about the initial of the processed window
            initial_indexes[initial_index] = initial_trace_index

        return self.window_count, self.metrics, initial_indexes

    def verify_window_ckeckpoint(self, i, event_data, time_difference=0):
        if self.current_parameters.win_unity == WindowUnityFixed.UNITY.name:
            if i > 0 and i % self.current_parameters.win_size == 0:
                return True
            return False
        elif self.current_parameters.win_unity == WindowUnityFixed.HOUR.name:
            if time_difference > self.current_parameters.win_size:
                return True
            return False
        elif self.current_parameters.win_unity == WindowUnityFixed.DAY.name:
            if time_difference.days > self.current_parameters.win_size:
                return True
            return False
        else:
            print(f'Incorrent windowing unity [{self.current_parameters.win_unity}].')
        return False

    def get_all_activities(self):
        # get the activities
        activities = [ev['concept:name'] for trace in self.current_log.log for ev in trace]
        activities = np.unique(np.array(activities))
        return activities

    def apply_detector(self, event_data, attribute_class, delta, activities, user):
        print(f'Applying ADWIN to log {self.current_log.filename} attribute {attribute_class.name} delta {delta}')
        adwin = {}
        attribute_values = {}
        change_points = {}
        change_points_info = {}
        initial_index = {}
        initial_case_ids = {}
        self.metrics = {}
        # initialize one detector for each activity
        for a in activities:
            adwin[a] = ADWIN(delta=delta)
            attribute_values[a] = {}
            change_points[a] = []
            detector_info = ChangePointInfo('ADWIN', a)
            detector_info.add_detector_attribute('delta', delta)
            change_points_info[a] = detector_info
            initial_case_ids[a] = {}
            initial_index[a] = 0
            self.window_count[a] = 0
            self.previous_model[a] = None
            self.previous_sub_log[a] = None

        self.current_parameters.total_of_activities = len(activities)
        for i, item in enumerate(event_data):
            # get the current case id
            case_id = self.get_case_id(item)
            # save the first case id as the beginning of the first window
            if i == 0:
                for a in activities:
                    initial_case_ids[a][i] = case_id
                    initial_index[a] = 0

            # when reading the log trace by trace we need to iterate over the events
            if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
                for event in item:
                    activity = event['concept:name']
                    value = attribute_class.get_value(event)
                    attribute_values[activity][i] = value
                    adwin[activity].add_element(value)
                    if adwin[activity].detected_change():
                        # create the manager for similarity metrics if a change is detected
                        if activity not in self.metrics.keys():
                            self.metrics[activity] = ManageSimilarityMetrics(self.model_type, self.current_parameters,
                                                                             self.control,
                                                                             self.models_path, self.metrics_path,
                                                                             activity)

                        change_points[activity].append(i)
                        change_points_info[activity].add_change_point(i)
                        print(
                            f'Change detected in data: {value} - at index: {i} - case: {case_id} - activity: {activity}')

                        # process new window
                        self.new_window(initial_index[activity], i, activity)
                        # save the initial of the processed window
                        initial_case_ids[activity][i] = case_id
                        # update the beginning of the next window
                        initial_index[activity] = i
            else:
                print(f'Adaptive approach not implemented yet for EVENT STREAM')
                # for each new event, collect the duration per activity
                activity = item['concept:name']
                value = attribute_class.get_value(item)
                attribute_values[activity][i] = value
                adwin[activity].add_element(value)
                if adwin[activity].detected_change():
                    # create the manager for similarity metrics if a change is detected
                    if activity not in self.metrics.keys():
                        self.metrics[activity] = ManageSimilarityMetrics(self.model_type, self.current_parameters,
                                                                         self.control,
                                                                         self.models_path, self.metrics_path, activity)
                    change_points[activity].append(i)
                    change_points_info[activity].add_change_point(i)
                    print(
                        f'Change detected in data: {value} - at index: {i} - case: {case_id} - activity: {activity}')

                    # process new window
                    self.new_window(initial_index[activity], i, activity)
                    # save the initial of the processed window
                    initial_case_ids[activity][i] = case_id
                    # update the beginning of the next window
                    initial_index[activity] = i
        # process remaining items as the last window
        find_any_drift = False
        for a in activities:
            if len(change_points[a]) > 0:
                find_any_drift = True
                if initial_index[a] < len(event_data):
                    size = len(event_data) - initial_index[a]
                    print(f'Analyzing final window... size {size} window_count {self.window_count[a]} activity {a}')
                    # set the final window used by metrics manager to identify all the metrics have been calculated
                    self.metrics[a].set_final_window(self.window_count[a])
                    # process final window for all activities where a drift has been detected
                    self.new_window(initial_index[a], len(event_data), a)
                self.plot_signal(attribute_values[a], a, change_points[a])
            else:
                self.plot_signal(attribute_values[a], a)
        if find_any_drift:
            # save the change points for the activity
            filename = os.path.join(self.drifts_output_path, f'Change_points_{self.current_parameters.attribute}.txt')
            with open(filename, 'w+') as file:
                for a in activities:
                    if len(change_points[a]) > 0:
                        file.write(change_points_info[a].serialize())
                        file.write('\n')
            print(f'Saving change points...')
        else:
            # if no drift is detected, generate the complete model and the plot with attribute values for each activity
            print(f'Analyzing unique window because no drift is detected...')
            # save the plot with attribute values for each activity
            for a in activities:
                self.plot_signal(attribute_values[a], a)
            # process the unique window
            initial_index[Activity.ALL.value] = 0
            initial_case_ids[Activity.ALL.value] = {}
            initial_case_ids[Activity.ALL.value][0] = case_id
            self.window_count[Activity.ALL.value] = 0
            self.new_window(initial_index[Activity.ALL.value], len(event_data), Activity.ALL.value)
        return self.window_count, self.metrics, initial_case_ids

    def get_current_timestamp(self, item):
        timestamp_aux = None
        # get the current timestamp
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            timestamp_aux = datetime.timestamp(item['time:timestamp'])
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            # use the date of the first event within the trace
            timestamp_aux = datetime.timestamp(item[0]['time:timestamp'])
        else:
            print(f'Incorrect window type: {self.current_parameters.read_log_as}.')
        return timestamp_aux

    def get_current_date(self, item):
        date_aux = None
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            date_aux = item['time:timestamp']
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            # use the date of the first event within the trace
            date_aux = item[0]['time:timestamp']
        else:
            print(f'Incorrect window type: {self.current_parameters.read_log_as}.')
        return date_aux

    def new_window(self, begin, end, activity=''):
        # increment the id of the window
        if activity:  # when using a detector for an attribute of the activity
            print(
                f'Generating model for sub-log [{begin} - {end - 1}] - window [{self.window_count[activity]}] - activity [{activity}]')
            self.window_count[activity] += 1
        else:
            print(f'Generating model for sub-log [{begin} - {end - 1}] - window [{self.window_count}]')
            self.window_count += 1

        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # generate the sub-log for the window
            window = EventStream(self.event_data[begin:end])
            sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            sub_log = EventLog(self.event_data[begin:end])
        else:
            print(f'Incorrect window type: {self.current_parameters.read_log_as}.')

        # save the sub-log
        # TODO create a parameter to save the sublogs
        # output_path = os.path.join(self.logs_path, self.current_parameters.logname, activity)
        # if not os.path.exists(output_path):
        #     os.makedirs(output_path)
        # if activity and activity != '':
        #     output_filename = os.path.join(output_path, f'sublog_w{self.window_count[activity]}_{begin}_{end - 1}.xes')
        # else:
        #     output_filename = os.path.join(output_path, f'sublog_w{self.window_count}_{begin}_{end - 1}.xes')
        # xes_exporter.apply(sub_log, output_filename)

        self.execute_processes_for_window(sub_log, begin, activity)

    def calculate_metrics_between_adjacent_time_slots(self, model, sub_log, initial_trace_index, activity):
        if activity:
            if activity == Activity.ALL.value:  # adaptive approach with no drift detected, nothing to be done
                return
            metrics = self.metrics[activity]
            window = self.window_count[activity]
            previous_model = self.previous_model[activity]
            previous_sub_log = self.previous_sub_log[activity]
        else:
            metrics = self.metrics
            window = self.window_count
            previous_model = self.previous_model
            previous_sub_log = self.previous_sub_log

        # if it is the second window start the metrics calculation and timeout
        if window == 2:
            metrics.start_metrics_timeout()
            self.control.start_metrics_calculation()

        # calculate the similarity metrics between consecutive windows
        if window > 1:
            metrics.calculate_metrics(window, previous_sub_log, sub_log, previous_model,
                                      model, self.current_parameters, initial_trace_index)

        if activity:
            # save the current model and sub_log for the next window
            self.previous_sub_log[activity] = sub_log
            self.previous_model[activity] = model
        else:
            # save the current model and sub_log for the next window
            self.previous_sub_log = sub_log
            self.previous_model = model

    # after defining a window (fixed or adaptive) IPDD must mine the models and calculate the similarity metrics
    # between adjacent ones
    # def execute_processes_for_window(self, sub_log, initial_trace_index, change_point, activity):
    def execute_processes_for_window(self, sub_log, initial_trace_index, activity):
        model = self.discovery.generate_process_model(sub_log, self.models_path, self.current_parameters.logname,
                                                      self.window_count, activity)
        self.calculate_metrics_between_adjacent_time_slots(model, sub_log, initial_trace_index, activity)

    # create for sliding windows
    def process_two_fixed_sliding_windows(self, event_data, initial_index_w1, initial_index_w2, winsize):
        print(f'process_two_windows w1: {initial_index_w1} w2: {initial_index_w2} winsize: {winsize}')
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # generate the sub-log for the window
            window1 = EventStream(event_data[initial_index_w1:initial_index_w1 + winsize])
            window2 = EventStream(event_data[initial_index_w2:initial_index_w2 + winsize])
            sub_log1 = log_converter.apply(window1, variant=log_converter.Variants.TO_EVENT_LOG)
            sub_log2 = log_converter.apply(window2, variant=log_converter.Variants.TO_EVENT_LOG)
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            sub_log1 = EventLog(event_data[initial_index_w1:initial_index_w1 + winsize])
            sub_log2 = EventLog(event_data[initial_index_w2:(initial_index_w2 + winsize)])
            print(f'Sub-log1: {len(sub_log1)} - Sub-log2: {len(sub_log2)}')
        else:
            print(f'Incorrect window type: {self.current_parameters.read_log_as}.')

        # TODO remove after debugging
        # for debug purpose
        # dataframe = log_converter.apply(sub_log1, variant=log_converter.Variants.TO_DATA_FRAME)
        # dataframe.to_csv(f'data/debug/{self.current_parameters.logname}_{self.window_count}_log1.csv')
        # dataframe = log_converter.apply(sub_log2, variant=log_converter.Variants.TO_DATA_FRAME)
        # dataframe.to_csv(f'data/debug/{self.current_parameters.logname}_{self.window_count}_log2.csv')
        self.compare_sliding_fixed_windows(sub_log1, sub_log2)

    # create for sliding windows
    def compare_sliding_fixed_windows(self, sl1, sl2):
        # increment the id of the window
        self.window_count += 1
        model1 = self.discovery.generate_process_model(sl1, self.models_path, self.current_parameters.logname,
                                                       self.window_count)

        # increment the id of the window
        self.window_count += 1
        model2 = self.discovery.generate_process_model(sl2, self.models_path, self.current_parameters.logname,
                                                       self.window_count)

        # if it is the second window start the metrics calculation and timeout
        if self.window_count == 2:
            self.metrics.start_metrics_timeout()
            self.control.start_metrics_calculation()

        self.metrics.calculate_metrics(self.window_count, sl1, sl2, model1, model2, self.current_parameters)
