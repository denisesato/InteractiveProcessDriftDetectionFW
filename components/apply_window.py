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
import pm4py
from threading import Thread
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from pm4py.algo.discovery.footprints import algorithm as fp_discovery
from pm4py.algo.conformance.footprints.util import evaluation
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from datetime import datetime, date
from components.adaptive.attributes import SelectAttribute, Activity
from components.adaptive.change_points_info import ChangePointInfo
from components.parameters import Approach, AttributeAdaptive, AdaptivePerspective, ControlflowAdaptiveApproach, \
    get_value_of_parameter
from components.compare_models.manage_similarity_metrics import ManageSimilarityMetrics
from skmultiflow.drift_detection.adwin import ADWIN
from components.parameters import ReadLogAs, WindowUnityFixed
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from enum import Enum


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class QualityDimension(str, Enum):
    FITNESS = 'fitness'
    PRECISION = 'precision'


def calculate_quality_metric(metric_name, log, net, im, fm):
    if metric_name == 'precisionETC':
        return precision_evaluator.apply(log, net, im, fm,
                                         variant=precision_evaluator.Variants.ETCONFORMANCE_TOKEN)
    elif metric_name == 'precisionAL':
        precision = precision_evaluator.apply(log, net, im, fm,
                                              variant=precision_evaluator.Variants.ALIGN_ETCONFORMANCE)
        return precision
    elif metric_name == 'fitnessTBR':
        return replay_fitness_evaluator.apply(log, net, im, fm,
                                              variant=replay_fitness_evaluator.Variants.TOKEN_BASED)[
            'average_trace_fitness']
    elif metric_name == 'fitnessAL':
        fitness = replay_fitness_evaluator.apply(log, net, im, fm,
                                                 variant=replay_fitness_evaluator.Variants.ALIGNMENT_BASED)
        return fitness['average_trace_fitness']
    else:
        print(f'metric name not identified {metric_name} in calculate_metric')
        return 0


def calculate_quality_metric_footprints(metric_name, log, tree):
    if metric_name == 'precisionFP':
        fp_log = fp_discovery.apply(log, variant=fp_discovery.Variants.TRACE_BY_TRACE)
        fp_tree = fp_discovery.apply(tree, variant=fp_discovery.Variants.PROCESS_TREE)
        precision = evaluation.fp_precision(fp_log, fp_tree)
        return precision


class AnalyzeDrift:
    def __init__(self, model_type, current_parameters, control, input_path,
                 models_path, metrics_path, logs_path, current_log, discovery, user,
                 output_path_adaptive_adwin,
                 output_path_adaptive_models_adwin):

        self.current_parameters = current_parameters
        self.user = user
        self.control = control
        self.input_path = input_path
        self.models_path = models_path
        self.metrics_path = metrics_path
        self.logs_path = logs_path
        self.output_path_adaptive_adwin = output_path_adaptive_adwin
        self.output_path_adaptive_models_adwin = output_path_adaptive_models_adwin
        self.model_type = model_type
        self.current_trace = 0

        # instance of the MetricsManager
        if current_parameters.approach == Approach.FIXED.name or \
                (current_parameters.approach == Approach.ADAPTIVE.name and
                 current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name):
            self.metrics = None
        elif current_parameters.approach == Approach.ADAPTIVE.name:
            self.metrics = {}

        # current loaded event log information
        self.current_log = current_log
        # set the event_data as requested by the user (read event by event or trace by trace)
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            self.event_data = self.current_log.log
        elif self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # convert the log into an event stream
            self.event_data = self.current_log.log.sort_values('time:timestamp').reset_index()
            self.event_data.rename(columns={'index': 'event_id'}, inplace=True)
        else:
            self.event_data = self.converted_log
            print(
                f'The window type received is not defined for IPDD {self.current_parameters.read_log_as}, assuming STREAM OF TRACES')
        # class that implements the discovery method for the current model
        self.discovery = discovery

    # save the change points in an txt file
    # used in the adaptive approaches
    def save_change_points(self, filename, change_points, change_points_info, activities=None):
        with open(filename, 'w+') as file:
            if activities:
                for a in activities:
                    if len(change_points[a]) > 0:
                        file.write(change_points_info[a].serialize())
                        file.write('\n')
            else:
                if len(change_points) > 0:
                    file.write(change_points_info.serialize())
                    file.write('\n')
        print(f'Saving change points to file {filename}')

    # generate the plot with the attribute selected for a specific activity
    # used for adaptive change detection in an activity attribute (time or data perspectives)
    def plot_signal_adaptive_time_data(self, values_for_activity, activity_name, change_points=None):
        # save data and plot about the data
        df = pd.DataFrame(values_for_activity).T.reset_index()
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            x_name = 'trace'

        elif self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            x_name = 'timestamp'
        else:
            print(f'Problem saving plots in plot_signal_adaptive_time_data: Parameter ReadLogAs not identified '
                  f'{self.current_parameters.read_log_as}')
            return

        df.columns = ['index', 'value', 'timestamp', 'case_id']
        filename_attributes = f'{activity_name}.csv'
        attribute = self.current_parameters.attribute_name
        output_filename = os.path.join(self.output_path_adaptive_adwin, filename_attributes)
        df.to_csv(output_filename, index=False)
        sns.set_style("whitegrid")
        # for generating the time series based on timestamp
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            df_plot = df[['timestamp', 'value']]
            df_plot.set_index('timestamp')
            plot = sns.lineplot(data=df_plot, x='timestamp', y='value')
        else:
            df_plot = df[['index', 'value']]
            plot = sns.lineplot(data=df_plot, x='index', y='value')

        plot.set_xlabel(x_name)
        plot.set_ylabel(f'{activity_name}')

        if change_points:
            for cp in change_points:
                plt.axvline(x=cp, color='r', linestyle=':')
        # save the plot
        filename = os.path.join(self.output_path_adaptive_adwin, f'{activity_name}.png')
        plt.title(f'Adaptive Time/Data - Attribute [{attribute}]')
        plt.savefig(filename)
        print(f'Saving plot for activity [{activity_name}]')
        plt.close()
        plt.cla()
        plt.clf()

    # generate the plot with the fitness and precision metrics and the drifts
    # used for adaptive change detection in the control-flow perspective
    def plot_signal_adaptive_controlflow(self, values, metrics, drifts=None):
        plt.style.use('seaborn-whitegrid')
        for metric in metrics.keys():
            plt.plot(values[metric], label=metrics[metric])
            no_values = len(values[metric])
        gap = int(no_values * 0.1)
        if gap == 0:  # less than 10 values
            gap = 1
        xpos = range(0, no_values + 1, gap)

        # draw a line for each reported drift
        indexes = [int(x) for x in drifts]
        for d in indexes:
            plt.axvline(x=d, label=d, color='k', linestyle=':')

        if len(drifts) > 0:
            plt.xlabel('Trace')
        else:
            plt.xlabel('Trace - no drifts detected')

        plt.xticks(xpos, xpos, rotation=90)
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.ylabel(f'Metric value')
        approach = get_value_of_parameter(self.current_parameters.adaptive_controlflow_approach)
        output_name = os.path.join(self.output_path_adaptive_adwin,
                                   f'adaptive_controlflow_metrics.png')

        plt.title(f'Adaptive Control-flow {approach}')
        # save the plot
        print(f'Saving plot for adaptive control-flow {approach} - {self.current_parameters.logname}')
        plt.savefig(output_name, bbox_inches='tight')
        # save the time series (fitness and precision)
        for m in metrics.keys():
            df = pd.DataFrame(values[m])
            df.to_excel(os.path.join(self.output_path_adaptive_adwin, f'{metrics[m]}.xlsx'))
        plt.close()
        plt.cla()
        plt.clf()

    # generate all the process models based on the windowing strategy
    # selected by the user and start the metrics calculation between
    # consecutive windows
    def start_drift_analysis(self):
        window_count = 0
        initial_indexes = {}
        if self.current_parameters.approach == Approach.FIXED.name or \
                (self.current_parameters.approach == Approach.ADAPTIVE.name and \
                 self.current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name):
            self.window_count = 0
            self.previous_sub_log = None
            self.previous_model = None
        elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            self.window_count = {}
            self.previous_sub_log = {}
            self.previous_model = {}

        metrics_manager = None
        # get all activities from the event log
        activities = self.get_all_activities()

        if self.event_data is not None:
            # call for the implementation of the different windowing strategies
            if self.current_parameters.approach == Approach.FIXED.name:
                window_count, metrics_manager, initial_indexes = self.apply_tumbling_window(self.event_data)
                # window_count, metrics_manager, initial_indexes = self.apply_sliding_window(event_data)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                    self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:
                # the user may select the activities that contain the attribute
                # for applying the detection (only available in the CLI interface by now)
                selected_activities = self.current_parameters.activities
                filter_activities = False
                if len(selected_activities) > 0:  # the user select the activities to consider
                    filter_activities = True
                    for act in selected_activities:
                        if act not in activities:
                            print(
                                f'Activity {act} not exist in the event log. Considering all activities for applying the detector..')
                            filter_activities = False
                # if the user do not define the activities or set any activity not existent, use all activities
                if filter_activities:
                    activities = selected_activities
                else:  # IPDD adaptive on time or data attributes
                    if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
                        attribute_class = SelectAttribute.get_selected_attribute_class(
                            self.current_parameters.attribute,
                            self.current_parameters.attribute_name)
                    else:
                        attribute_class = SelectAttribute.get_selected_attribute_class(
                            self.current_parameters.attribute)

                    window_count, metrics_manager, initial_indexes = \
                        self.apply_detector_on_attribute(self.event_data,
                                                         attribute_class,
                                                         self.current_parameters.delta,
                                                         activities,
                                                         self.user)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                    self.current_parameters.adaptive_controlflow_approach == ControlflowAdaptiveApproach.TRACE.name:
                # IPDD adaptive trace by trace approach
                window_count, metrics_manager, initial_indexes = \
                    self.apply_detector_on_quality_metrics_trace_by_trace(self.event_data,
                                                                          self.current_parameters.delta,
                                                                          self.current_parameters.win_size,
                                                                          self.user)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                    self.current_parameters.adaptive_controlflow_approach == ControlflowAdaptiveApproach.WINDOW.name:
                # IPDD adaptive windowing approach
                window_count, metrics_manager, initial_indexes = \
                    self.apply_detector_on_quality_metrics_windowing(self.event_data,
                                                                     self.current_parameters.delta,
                                                                     self.current_parameters.win_size,
                                                                     self.user)
            else:
                print(f'Incorrect approach (start_drift_analysis): {self.current_parameters.approach}')

            # stores the instance of the metrics manager, responsible to manage the asynchronous
            # calculation of the metrics
            # no metrics manager instantiated when IPDD calculates one window
            if metrics_manager:
                self.control.set_metrics_manager(metrics_manager)
            return window_count, initial_indexes, activities

    # get the current case id from the trace or event
    def get_case_id(self, event_data, item):
        # get the initial case id of the window
        # TODO verificar se vai funcionar quando ler trace a trace
        case_id = event_data['case:concept:name'][item]
        return case_id

    # Sliding window approach implemented for fixed window - NOT USED
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

    # windowing method for fixed window approach
    def apply_tumbling_window(self, event_data):
        self.current_trace = 0
        initial_index = 0
        initial_indexes = {}
        initial_trace_index = None

        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)

        for i, item in enumerate(event_data):
            self.current_trace = i + 1
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
        activities = pm4py.get_event_attribute_values(self.current_log.log, 'concept:name',
                                                      case_id_key='case:concept:name')
        return activities

    # IPDD adaptive approach for time or data attributes
    def apply_detector_on_attribute(self, event_data, attribute_class, delta, activities, user):
        self.current_trace = 0
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
        traces_in_window = []
        begin_event = 0
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            # get case ids for reading trace by trace
            case_ids = event_data['case:concept:name'].unique().tolist()
            for case_id in case_ids:
                # get the trace information from dataframe
                trace = event_data.loc[(event_data['case:concept:name'] == case_id)]
                traces_in_window.append(case_id)
                # save the first case id as the beginning of the first window
                if self.current_trace == 0:
                    for a in activities:
                        initial_case_ids[a][self.current_trace] = case_id
                        initial_index[a] = 0

                # read the events from the current trace
                for i in trace.index:
                    # for each new event, collect the duration per activity
                    activity = trace['concept:name'][i]
                    timestamp = trace['time:timestamp'][i]
                    value = attribute_class.get_value(trace, i)
                    attribute_values[activity][self.current_trace] = value
                    attribute_values[activity][self.current_trace] = {
                        'value': value,
                        'timestamp': timestamp,
                        'case_id': case_id
                    }

                    adwin[activity].add_element(value)
                    if adwin[activity].detected_change():
                        # create the manager for similarity metrics if a change is detected
                        if activity not in self.metrics.keys():
                            self.metrics[activity] = ManageSimilarityMetrics(self.model_type, self.current_parameters,
                                                                             self.control,
                                                                             self.models_path, self.metrics_path,
                                                                             activity)
                        change_points[activity].append(self.current_trace)
                        change_points_info[activity].add_change_point(self.current_trace)
                        change_points_info[activity].add_timestamp(self.get_current_date(trace, i))
                        print(
                            f'Change detected in data: {value} - at index: {i} - case index: {self.current_trace} - case: {case_id} - activity: {activity}')

                        # process new window
                        self.new_window(begin_event, i, activity)
                        # save the initial of the processed window
                        initial_case_ids[activity][self.current_trace] = case_id
                        # update the beginning of the next window
                        initial_index[activity] = self.current_trace
                        traces_in_window = []
                        begin_event = i + 1
                self.current_trace += 1
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
                    self.plot_signal_adaptive_time_data(attribute_values[a], a, change_points[a])
                else:
                    self.plot_signal_adaptive_time_data(attribute_values[a], a)
            if find_any_drift:
                # save the change points for the activity
                filename = os.path.join(self.output_path_adaptive_adwin, f'drifts_{attribute_class.name}.txt')
                self.save_change_points(filename, change_points, change_points_info, activities)
            else:
                # if no drift is detected, generate the complete model and the plot with attribute values for each activity
                print(f'Analyzing unique window because no drift is detected...')
                # save the plot with attribute values for each activity
                for a in activities:
                    self.plot_signal_adaptive_time_data(attribute_values[a], a)
                # process the unique window
                initial_index[Activity.ALL.value] = 0
                initial_case_ids[Activity.ALL.value] = {}
                initial_case_ids[Activity.ALL.value][0] = case_id
                self.window_count[Activity.ALL.value] = 0
                self.new_window_events(initial_index[Activity.ALL.value], len(event_data), Activity.ALL.value)
            return self.window_count, self.metrics, initial_case_ids
        elif self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # read the events from the dataframe
            for i in event_data.index:
                # get the current case id and event id
                case_id = event_data['case:concept:name'][i]

                # save the first case id as the beginning of the first window
                if i == 0:
                    for a in activities:
                        initial_case_ids[a][i] = case_id
                        initial_index[a] = 0

                # for each new event, collect the duration per activity
                activity = event_data['concept:name'][i]
                timestamp = event_data['time:timestamp'][i]
                value = attribute_class.get_value(event_data, i)
                attribute_values[activity][i] = value
                attribute_values[activity][i] = {
                    'value': value,
                    'timestamp': timestamp,
                    'case_id': case_id,
                }

                adwin[activity].add_element(value)
                if adwin[activity].detected_change():
                    # create the manager for similarity metrics if a change is detected
                    if activity not in self.metrics.keys():
                        self.metrics[activity] = ManageSimilarityMetrics(self.model_type, self.current_parameters,
                                                                         self.control,
                                                                         self.models_path, self.metrics_path,
                                                                         activity)
                    change_points[activity].append(self.get_current_date(event_data, i))
                    change_points_info[activity].add_change_point(i)
                    change_points_info[activity].add_timestamp(self.get_current_date(event_data, i))
                    print(
                        f'Change detected in data: {value} - at index: {i} - '
                        f'case: {case_id} - activity: {activity}')

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
                    self.plot_signal_adaptive_time_data(attribute_values[a], a, change_points[a])
                else:
                    self.plot_signal_adaptive_time_data(attribute_values[a], a)
            if find_any_drift:
                # save the change points for the activity
                filename = os.path.join(self.output_path_adaptive_adwin, f'drifts_{attribute_class.name}.txt')
                self.save_change_points(filename, change_points, change_points_info, activities)
            else:
                # if no drift is detected, generate the complete model and the plot with attribute values for each activity
                print(f'Analyzing unique window because no drift is detected...')
                # save the plot with attribute values for each activity
                for a in activities:
                    self.plot_signal_adaptive_time_data(attribute_values[a], a)
                # process the unique window
                initial_index[Activity.ALL.value] = 0
                initial_case_ids[Activity.ALL.value] = {}
                initial_case_ids[Activity.ALL.value][0] = case_id
                self.window_count[Activity.ALL.value] = 0
                self.new_window(initial_index[Activity.ALL.value], len(event_data), Activity.ALL.value)
            return self.window_count, self.metrics, initial_case_ids

    # IPDD adaptive trace by trace approach
    # Apply the ADWIN detector (scikit-multiflow) in two quality dimensions: fitness and precision
    # The metrics for each dimension are defined by parameter metrics (dictionary)
    # The metrics are calculated using the last trace read and the model generated using the first traces (stable_period)
    # When a drift is detected a new model may be discovered using the next traces (stable_period)
    # The process model is discovered using the inductive miner
    def apply_detector_on_quality_metrics_trace_by_trace(self, event_data, delta, window_size, user):
        factor = 100
        self.current_trace = 0
        print(f'Trace by trace approach - ADWIN to log {self.current_log.filename} delta {delta}')
        # different metrics can be used for each dimension evaluated
        # by now we expected one metric for fitness quality dimension and other for precision quality dimension
        metrics = {
            QualityDimension.FITNESS.name: 'fitnessTBR',
            QualityDimension.PRECISION.name: 'precisionETC',
        }
        # derive the initial model using the parameter stable_period
        print(f'Initial model discovered using traces from 0 to {window_size - 1}')
        log_for_model = event_data[0:window_size]
        net, im, fm = inductive_miner.apply(log_for_model)
        pnml_filename = os.path.join(self.output_path_adaptive_models_adwin,
                                     f'model1_0-{window_size - 1}.pnml')
        pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
        # other discovery algorithms can be applied
        # net, im, fm = heuristics_miner.apply(log_for_model)
        # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMf)
        # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMd)
        adwin_detection = {}
        drifts = {}
        values = {}
        # for saving the change points
        change_points = []
        detector_info = ChangePointInfo('ADWIN')
        detector_info.add_detector_attribute('delta', delta)
        change_points_info = detector_info
        for dimension in metrics.keys():
            # instantiate one detector for each evaluated dimension (fitness and precision)
            adwin_detection[dimension] = ADWIN(delta=self.current_parameters.delta)
            drifts[dimension] = []
            values[dimension] = []

        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)
        # initialize window count and case ids
        self.window_count = 0
        self.initial_case_ids = {}
        initial_trace_id = 0
        final_trace_id = initial_trace_id + window_size
        total_of_traces = len(event_data)
        for i in range(0, total_of_traces):
            self.current_trace = i + 1
            print(f'Reading trace [{i}]...')
            last_trace = event_data[i:(i + 1)]
            # check if one of the metrics report a drift
            drift_detected = False
            for dimension in metrics.keys():
                # calculate the metric for each dimension
                # for each dimension decide if the metric should be calculated using only the last trace read or all
                # the traces read since the last drift
                new_value = calculate_quality_metric(metrics[dimension], last_trace, net, im, fm) * factor
                values[dimension].append(new_value)
                # update the new value in the detector
                adwin_detection[dimension].add_element(new_value)
                if adwin_detection[dimension].detected_change():
                    # drift detected, save it
                    drifts[dimension].append(i)
                    print(f'Metric [{dimension}] - Drift detected at trace {i}')
                    drift_detected = True

            # if at least one metric report a drift a new model is discovered
            if drift_detected:
                # save information about change point for saving the file
                change_points.append(i)
                change_points_info.add_change_point(i)
                change_points_info.add_timestamp(self.get_current_date(event_data[i]))
                # process new window
                self.new_window(initial_trace_id, final_trace_id)
                # get the  case id
                case_id = self.get_case_id(event_data[initial_trace_id])
                # save the initial of the processed window
                self.initial_case_ids[initial_trace_id] = case_id
                # update the beginning of the next window
                initial_trace_id = i

                for dimension in metrics.keys():
                    # reset the detectors to avoid a new drift during the stable period
                    adwin_detection[dimension].reset()

                # discover a new model using the next traces (window_size)
                final_trace_id = i + window_size
                if final_trace_id > total_of_traces:
                    final_trace_id = total_of_traces

                if self.current_parameters.update_model:
                    print(f'Discover a new model using traces from {i} to {final_trace_id - 1}')
                    log_for_model = event_data[i:final_trace_id]
                    net, im, fm = inductive_miner.apply(log_for_model)
                    pnml_filename = os.path.join(self.output_path_adaptive_models_adwin,
                                                 f'model{self.window_count + 1}_{i}-{final_trace_id - 1}.pnml')
                    pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
                    # other discovery algorithms can be applied
                    # net, im, fm = heuristics_miner.apply(log_for_model)
                    # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMf)
                    # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMd)
        # process remaining items as the last window
        if 0 < initial_trace_id < total_of_traces:
            final_trace_id = initial_trace_id + window_size
            if final_trace_id > total_of_traces:
                final_trace_id = total_of_traces
            print(
                f'Analyzing final window... size {final_trace_id - initial_trace_id} window_count {self.window_count}')
            # set the final window used by metrics manager to identify all the metrics have been calculated
            self.metrics.set_final_window(self.window_count)
            # process final window for all activities where a drift has been detected
            self.new_window(initial_trace_id, final_trace_id)
            case_id = self.get_case_id(event_data[initial_trace_id])
            self.initial_case_ids[initial_trace_id] = case_id
        elif initial_trace_id == 0:
            # if no drift is detected, generate the complete model and the plot with attribute values for each activity
            print(f'Analyzing unique window because no drift is detected...')
            # process the unique window
            case_id = self.get_case_id(event_data[initial_trace_id])
            self.initial_case_ids[0] = case_id
            # set the final window used by metrics manager to identify all the metrics have been calculated
            self.metrics.set_final_window(self.window_count)
            self.new_window(initial_trace_id, total_of_traces)
        # join all detected drifts for the plot
        all_drifts = []
        for m in metrics.keys():
            all_drifts += drifts[m]
        all_drifts = list(set(all_drifts))
        all_drifts.sort()
        # save plot and data
        self.plot_signal_adaptive_controlflow(values, metrics, all_drifts)
        # save information about drifts
        if len(all_drifts) > 0:
            approach = get_value_of_parameter(self.current_parameters.adaptive_controlflow_approach)
            filename = os.path.join(self.output_path_adaptive_adwin, f'drifts_{approach}.txt')
            self.save_change_points(filename, change_points, change_points_info)
        return self.window_count, self.metrics, self.initial_case_ids

    # IPDD adaptive windowing approach
    def apply_detector_on_quality_metrics_windowing(self, event_data, delta, window_size, user):
        factor = 100
        self.current_trace = 0
        print(f'Windowing approach - ADWIN to log {self.current_log.filename} delta {delta}')
        metrics = {
            QualityDimension.FITNESS.name: 'fitnessTBR',
            QualityDimension.PRECISION.name: 'precisionFP'
        }
        total_of_traces = len(event_data)
        # derive the model for evaluating the quality metrics
        initial_trace_id_for_stable_period = 0
        final_trace_id = initial_trace_id_for_stable_period + window_size
        log_for_model = event_data[initial_trace_id_for_stable_period:final_trace_id]
        net, im, fm = inductive_miner.apply(log_for_model)
        pnml_filename = os.path.join(self.output_path_adaptive_models_adwin,
                                     f'model1_{initial_trace_id_for_stable_period}-{final_trace_id - 1}.pnml')
        pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
        tree = inductive_miner.apply_tree(log_for_model)
        print(f'Initial model discovered using traces [{initial_trace_id_for_stable_period}-{final_trace_id - 1}]')
        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)
        # initialize window count and case ids
        self.window_count = 0
        self.initial_case_ids = {}
        values = dict.fromkeys(metrics)
        adwin = dict.fromkeys(metrics)
        drifts = dict.fromkeys(metrics)
        # for saving the change points
        change_points = []
        detector_info = ChangePointInfo('ADWIN')
        detector_info.add_detector_attribute('delta', delta)
        change_points_info = detector_info

        for m in metrics.keys():
            values[m] = []
            if delta:
                adwin[m] = ADWIN(delta=delta)
            else:
                adwin[m] = ADWIN()
            drifts[m] = []

        initial_trace_id = 0  # start of the window (change point)
        for i in range(0, total_of_traces):
            self.current_trace = i + 1
            # print(f'Reading trace {i}')
            current_trace = event_data[i:i + 1]
            if i == initial_trace_id_for_stable_period:
                print(
                    f'Setup phase - traces [{initial_trace_id_for_stable_period}-{initial_trace_id_for_stable_period + window_size - 1}]')
                # initial of the stable period
                # during the stable period we apply the same value for the metrics
                # fitness - calculated using the initial trace of the stable period
                # precision - calculated using all the traces inside the stable period
                traces_stable_period = event_data[
                                       initial_trace_id_for_stable_period:initial_trace_id_for_stable_period + window_size]
                precision = calculate_quality_metric_footprints(metrics[QualityDimension.PRECISION.name],
                                                                traces_stable_period,
                                                                tree) * factor
                fitness = calculate_quality_metric(metrics[QualityDimension.FITNESS.name], current_trace, net, im,
                                                   fm) * factor
            elif i >= initial_trace_id_for_stable_period + window_size:
                print(f'Detection phase - reading trace {i}')
                window = event_data[i - window_size + 1:i + 1]
                # after the stable period calculate the metrics after reading a new trace
                precision = calculate_quality_metric_footprints(metrics[QualityDimension.PRECISION.name], window,
                                                                tree) * factor
                fitness = calculate_quality_metric(metrics[QualityDimension.FITNESS.name], current_trace, net, im,
                                                   fm) * factor

            values[QualityDimension.PRECISION.name].append(precision)
            adwin[QualityDimension.PRECISION.name].add_element(precision)

            values[QualityDimension.FITNESS.name].append(fitness)
            adwin[QualityDimension.FITNESS.name].add_element(fitness)

            drift_detected = False
            change_point = 0
            # check for drift in precision
            if adwin[QualityDimension.PRECISION.name].detected_change():
                # define the change point as the initial of the window
                change_point = i - window_size + 1
                drifts[QualityDimension.PRECISION.name].append(change_point)
                print(f'Metric [{QualityDimension.PRECISION.value}] detected a drift in trace: {change_point}')
                drift_detected = True
            # check for drift in fitness
            elif adwin[QualityDimension.FITNESS.name].detected_change():
                change_point = i
                drifts[QualityDimension.FITNESS.name].append(change_point)
                print(f'Metric [{QualityDimension.FITNESS.value}] detected a drift in trace: {change_point}')
                drift_detected = True

            if drift_detected:
                change_points.append(change_point)
                change_points_info.add_change_point(change_point)
                change_points_info.add_timestamp(self.get_current_date(event_data[change_point]))
                # process new window
                final_trace_id = initial_trace_id + window_size
                if final_trace_id > total_of_traces:
                    final_trace_id = total_of_traces
                self.new_window(initial_trace_id, final_trace_id)
                # get the current case id
                case_id = self.get_case_id(event_data[initial_trace_id])
                # save the initial of the processed window
                self.initial_case_ids[initial_trace_id] = case_id
                # update the beginning of the next window
                initial_trace_id_for_stable_period = i + 1
                initial_trace_id = change_point
                for m in metrics:
                    # reset the detectors to avoid a new drift during the stable period
                    adwin[m].reset()
                if self.current_parameters.update_model:
                    # Discover a new model using window
                    log_for_model = event_data[change_point:change_point + window_size]
                    net, im, fm = inductive_miner.apply(log_for_model)
                    pnml_filename = os.path.join(self.output_path_adaptive_models_adwin,
                                                 f'model{self.window_count + 1}_{change_point}-{change_point + window_size - 1}.pnml')
                    pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
                    tree = inductive_miner.apply_tree(log_for_model)
                    print(f'New model discovered using traces [{change_point}-{change_point + window_size - 1}]')

        # process remaining items as the last window
        if 0 < initial_trace_id < total_of_traces:
            final_trace_id = initial_trace_id + window_size
            if final_trace_id > total_of_traces:
                final_trace_id = total_of_traces
            print(
                f'Analyzing final window... size {final_trace_id - initial_trace_id} window_count {self.window_count}')
            # set the final window used by metrics manager to identify all the metrics have been calculated
            self.metrics.set_final_window(self.window_count)
            # process final window for all activities where a drift has been detected
            self.new_window(initial_trace_id, final_trace_id)
            case_id = self.get_case_id(event_data[initial_trace_id])
            self.initial_case_ids[initial_trace_id] = case_id
        elif initial_trace_id == 0:
            # if no drift is detected, generate the complete model and the plot with attribute values for each activity
            print(f'Analyzing unique window because no drift is detected...')
            # process the unique window
            case_id = self.get_case_id(event_data[initial_trace_id])
            self.initial_case_ids[0] = case_id
            # set the final window used by metrics manager to identify all the metrics have been calculated
            self.metrics.set_final_window(self.window_count)
            self.new_window(initial_trace_id, total_of_traces)

        # join all detected drifts for the plot
        all_drifts = []
        for m in metrics.keys():
            all_drifts += drifts[m]
        all_drifts = list(set(all_drifts))
        all_drifts.sort()
        # save plot and data
        self.plot_signal_adaptive_controlflow(values, metrics, all_drifts)
        # save information about drifts
        if len(all_drifts) > 0:
            approach = get_value_of_parameter(self.current_parameters.adaptive_controlflow_approach)
            filename = os.path.join(self.output_path_adaptive_adwin, f'drifts_{approach}.txt')
            self.save_change_points(filename, change_points, change_points_info)
        return self.window_count, self.metrics, self.initial_case_ids

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

    def get_current_date(self, event_data, index):
        date_aux = event_data['time:timestamp'][index]
        return date_aux

    def save_sublog(self, sub_log, begin, end):
        output_path = self.logs_path
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_filename = os.path.join(output_path,
                                       f'sublog{self.window_count}_{begin}_{end - 1}.xes')
        xes_exporter.apply(sub_log, output_filename)

    def new_window(self, begin, end, activity=''):
        # increment the id of the window
        if activity:  # when using a detector for an attribute of the activity
            print(
                f'Generating model for sub-log [{begin} - {end - 1}] - window [{self.window_count[activity]}] - activity [{activity}]')
            self.window_count[activity] += 1
        else:
            print(f'Generating model for sub-log [{begin} - {end - 1}] - window [{self.window_count}]')
            self.window_count += 1

        window = self.event_data[begin:end]

        # save the sublog
        if self.current_parameters.save_sublogs:
            self.save_sublog(window, begin, end)
        # get initial timestamp
        initial_timestamp = self.get_current_date(window, begin)
        self.execute_processes_for_window(window, begin, initial_timestamp, activity)

    def calculate_metrics_between_adjacent_time_slots(self, model, sub_log, initial_trace_index, initial_timestamp,
                                                      activity):
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
            metrics.calculate_metrics(window, previous_model, model, previous_sub_log, sub_log, self.current_parameters,
                                      initial_trace_index, initial_timestamp)

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
    def execute_processes_for_window(self, sub_log, initial_trace_index, initial_timestamp, activity):
        model = self.discovery.generate_process_model(sub_log, self.models_path, self.current_parameters.logname,
                                                      self.window_count, activity,
                                                      self.current_parameters.save_model_svg)
        self.calculate_metrics_between_adjacent_time_slots(model, sub_log, initial_trace_index, initial_timestamp,
                                                           activity)

    # create for sliding windows
    def process_two_fixed_sliding_windows(self, event_data, initial_index_w1, initial_index_w2, winsize):
        print(f'process_two_windows w1: {initial_index_w1} w2: {initial_index_w2} winsize: {winsize}')
        sub_log1 = event_data[initial_index_w1:initial_index_w1 + winsize]
        sub_log2 = event_data[initial_index_w2:(initial_index_w2 + winsize)]

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
