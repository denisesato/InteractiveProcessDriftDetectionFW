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
import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventStream, EventLog
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from pm4py.algo.discovery.footprints import algorithm as fp_discovery
from pm4py.algo.conformance.footprints.util import evaluation
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from datetime import datetime, date
from components.adaptive.attributes import SelectAttribute, Activity
from components.adaptive.change_points_info import ChangePointInfo
from components.adaptive.detectors import SelectDetector
from components.parameters import Approach, AttributeAdaptive, AdaptivePerspective, ControlflowAdaptiveApproach, \
    get_value_of_parameter
from components.compare_models.manage_similarity_metrics import ManageSimilarityMetrics

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
                 output_path_adaptive_detector,
                 output_path_adaptive_models_detector):

        self.current_parameters = current_parameters
        self.user = user
        self.control = control
        self.input_path = input_path
        self.models_path = models_path
        self.metrics_path = metrics_path
        self.logs_path = logs_path
        self.output_path_adaptive_detector = output_path_adaptive_detector
        self.output_path_adaptive_models_detector = output_path_adaptive_models_detector
        self.model_type = model_type
        self.current_trace = 0

        # instance of the MetricsManager
        if current_parameters.approach == Approach.FIXED.name or \
                (current_parameters.approach == Approach.ADAPTIVE.name and
                 current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name):
            self.metrics = None

        elif current_parameters.approach == Approach.ADAPTIVE.name:
            self.detector_class = self.current_parameters.detector_class
            self.metrics = {}

        # current loaded event log information
        self.current_log = current_log
        # convert do dataframe in case of the user set to read the log ordered by event timestamp
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # convert the log to a dataframe for reading ordered by event
            dataframe = pm4py.convert_to_dataframe(self.current_log.log)
            self.current_log.log = dataframe.sort_values('time:timestamp').reset_index()
            self.current_log.log.rename(columns={'index': 'event_id'}, inplace=True)

        self.event_data = self.current_log.log

        # class that implements the discovery method for the current model
        self.discovery = discovery

    # save the change points in a txt file
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
    def plot_signal_adaptive_time_data(self, values_for_activity, activity_name, change_points=None,
                                       change_points_time_based=None):
        df = pd.DataFrame(values_for_activity).T.reset_index()

        # save temporal series to a csv file
        df.columns = ['index', 'value', 'timestamp', 'case_id']
        filename_attributes = f'{activity_name}'
        if self.current_parameters.attribute_name_for_plot:
            attribute = self.current_parameters.attribute_name_for_plot
        elif self.current_parameters.attribute == AttributeAdaptive.SOJOURN_TIME.name:
            attribute = f'{AttributeAdaptive.SOJOURN_TIME.value} (seconds)'
        elif self.current_parameters.attribute == AttributeAdaptive.WAITING_TIME.name:
            attribute = f'{AttributeAdaptive.WAITING_TIME.value}  (seconds)'
        else:
            attribute = self.current_parameters.attribute_name
        # save temporal serie into csv and excel for analysis
        output_filename = os.path.join(self.output_path_adaptive_detector, f'{filename_attributes}.csv')
        df.to_csv(output_filename, index=False)
        output_filename = os.path.join(self.output_path_adaptive_detector, f'{filename_attributes}.xlsx')
        df.to_excel(output_filename, index=False)

        # generate plot
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # for plotting based on timestamp
            x_column_name_time_based = 'timestamp'
            x_name_time_based = 'timestamp'
            self.plot_signal(df, x_column_name_time_based, x_name_time_based, activity_name, attribute,
                             change_points_time_based)

            # for plotting based on event index
            df.drop(['index'], axis=1, inplace=True)
            x_column_name_event_based = 'index'
            x_name_event_based = 'event index'
            df.reset_index(inplace=True)
            self.plot_signal(df, x_column_name_event_based, x_name_event_based, activity_name, attribute,
                             change_points)
        else:
            x_colum_name = 'index'
            x_name = 'trace'
            self.plot_signal(df, x_colum_name, x_name, activity_name, attribute, change_points)

    def plot_signal(self, df_plot, x_column_name, x_axis_name, activity_name, attribute, change_points):
        sns.set_style("whitegrid")
        plot = sns.lineplot(data=df_plot, x=x_column_name, y='value')
        plot.set_xlabel(x_axis_name)
        plot.set_ylabel(f'{attribute}')

        if change_points:
            for cp in change_points:
                plt.axvline(x=cp, color='r', linestyle=':')
        # save the plot
        filename = os.path.join(self.output_path_adaptive_detector, f'{activity_name}_{x_axis_name}.png')
        plt.title(f'Adaptive Time/Data - {activity_name}')
        plt.savefig(filename)
        print(f'Saving plot for activity  - {activity_name}')
        plt.close()
        plt.cla()
        plt.clf()

    # generate the plot with the fitness and precision metrics and the drifts
    # used for adaptive change detection in the control-flow perspective
    def plot_signal_adaptive_controlflow(self, values, metrics, drifts=None):
        # plt.style.use('seaborn-whitegrid')
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
        output_name = os.path.join(self.output_path_adaptive_detector,
                                   f'adaptive_controlflow_metrics.png')

        plt.title(f'Adaptive Control-flow {approach}')
        # save the plot
        print(f'Saving plot for adaptive control-flow {approach} - {self.current_parameters.logname}')
        plt.savefig(output_name, bbox_inches='tight')
        # save the time series (fitness and precision)
        for m in metrics.keys():
            df = pd.DataFrame(values[m])
            df.to_excel(os.path.join(self.output_path_adaptive_detector, f'{metrics[m]}.xlsx'))
            df.index.name = 'Index'
            df.to_csv(os.path.join(self.output_path_adaptive_detector, f'{metrics[m]}.csv'), header=['Value'])
        plt.close()
        plt.cla()
        plt.clf()

    # generate all the process models based on the windowing strategy
    # selected by the user and start the metrics calculation between
    # consecutive windows
    def start_drift_analysis(self):
        initial_event_ids = None
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
                    self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:  # IPDD adaptive on time or data attributes
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

                if self.current_parameters.attribute == AttributeAdaptive.OTHER.name:
                    attribute_class = SelectAttribute.get_selected_attribute_class(
                        self.current_parameters.attribute,
                        self.current_parameters.attribute_name)
                else:
                    attribute_class = SelectAttribute.get_selected_attribute_class(
                        self.current_parameters.attribute)

                window_count, metrics_manager, initial_indexes, initial_event_ids = \
                    self.apply_detector_on_attribute(self.event_data,
                                                     attribute_class,
                                                     self.current_parameters.detector_class,
                                                     activities,
                                                     self.user)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                    self.current_parameters.adaptive_controlflow_approach == ControlflowAdaptiveApproach.TRACE.name:
                # IPDD adaptive trace by trace approach
                window_count, metrics_manager, initial_indexes = \
                    self.apply_detector_on_quality_metrics_trace_by_trace(self.event_data,
                                                                          self.current_parameters.detector_class,
                                                                          self.current_parameters.win_size,
                                                                          self.user)
            elif self.current_parameters.approach == Approach.ADAPTIVE.name and \
                    self.current_parameters.adaptive_controlflow_approach == ControlflowAdaptiveApproach.WINDOW.name:
                # IPDD adaptive windowing approach
                window_count, metrics_manager, initial_indexes = \
                    self.apply_detector_on_quality_metrics_windowing(self.event_data,
                                                                     self.current_parameters.detector_class,
                                                                     self.current_parameters.win_size,
                                                                     self.user)
            else:
                print(f'Incorrect approach (start_drift_analysis): {self.current_parameters.approach}')

            # stores the instance of the metrics manager, responsible to manage the asynchronous
            # calculation of the metrics
            # no metrics manager instantiated when IPDD calculates one window
            if metrics_manager:
                self.control.set_metrics_manager(metrics_manager)
            return window_count, initial_indexes, activities, initial_event_ids

    # get the current case id from the trace or event
    def get_case_id(self, item):
        # get the initial case id of the window
        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            case_id = item['case:concept:name']
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            case_id = item.attributes['concept:name']
        else:
            print(f'Incorrect window type (start_drift_analysis): {self.window_type}.')
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
        activities = attributes_filter.get_attribute_values(self.current_log.log, "concept:name")
        return activities

    # IPDD adaptive approach for time or numeric data attributes
    def apply_detector_on_attribute(self, event_data, attribute_class, detector_class, activities, user):
        self.current_trace = 0
        print(f'Applying {detector_class.get_name()} to log {self.current_log.filename} attribute {attribute_class.name}')
        for key in detector_class.parameters.keys():
            print(f'{key}: {detector_class.parameters[key]}')
        detector_dict = {}
        attribute_values = {}
        change_points = {}
        change_points_time_based = {}
        change_points_info = {}
        initial_index = {}
        initial_case_ids = {}
        initial_event_indexes = {}
        event_indexes = {}
        self.metrics = {}
        # initialize one detector for each activity
        for a in activities:
            detector_dict[a] = SelectDetector.get_detector_instance(detector_class.get_definition(),
                                                                    detector_class.parameters)
            detector_dict[a].instantiate_detector()
            attribute_values[a] = {}
            change_points[a] = []
            change_points_time_based[a] = []
            event_indexes[a] = 0
            detector_info = ChangePointInfo(detector_class.get_name(), a)
            for key in detector_class.parameters:
                detector_info.add_detector_attribute(key, detector_class.parameters[key])
            change_points_info[a] = detector_info
            initial_case_ids[a] = {}
            initial_index[a] = 0
            self.window_count[a] = 0
            self.previous_model[a] = None
            self.previous_sub_log[a] = None

        self.current_parameters.total_of_activities = len(activities)

        # when reading the log trace by trace we need to iterate over the events
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            for i, item in enumerate(event_data):
                self.current_trace = i + 1
                # get the current case id
                case_id = self.get_case_id(item)
                timestamp = self.get_current_timestamp(item)
                # save the first case id as the beginning of the first window
                if i == 0:
                    for a in activities:
                        initial_case_ids[a][i] = case_id
                        initial_index[a] = 0

                for event in item:
                    activity = event['concept:name']
                    if activity in activities:
                        try:
                            value = attribute_class.get_value(event)
                        except AttributeError as err:
                            print(f'Error getting the value of attribute: {err}')
                            return
                        except KeyError as kerr:
                            print(f'Error getting the value of attribute: {kerr}')
                            return
                        attribute_values[activity][i] = {
                            'value': value,
                            'timestamp': timestamp,
                            'case_id': case_id,
                        }
                        detector_dict[activity].update_val(value)
                        if detector_dict[activity].detected_change():
                            # create the manager for similarity metrics if a change is detected
                            if activity not in self.metrics.keys():
                                self.metrics[activity] = ManageSimilarityMetrics(self.model_type,
                                                                                 self.current_parameters,
                                                                                 self.control,
                                                                                 self.models_path, self.metrics_path,
                                                                                 activity)

                            change_points[activity].append(i)
                            change_points_info[activity].add_change_point(i)
                            change_points_info[activity].add_case_id(case_id)
                            change_points_info[activity].add_timestamp(self.get_current_date(event_data[i]))
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
            for j, a in enumerate(activities):
                if len(change_points[a]) > 0:
                    find_any_drift = True
                    if initial_index[a] < len(event_data):
                        size = len(event_data) - initial_index[a]
                        print(
                            f'Analyzing final window... size {size} window_count {self.window_count[a]} activity {a}')
                        # set the final window used by metrics manager to identify all the metrics have been calculated
                        self.metrics[a].set_final_window(self.window_count[a])
                        # process final window for all activities where a drift has been detected
                        self.new_window(initial_index[a], len(event_data), a)
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activities_for_plot[j],
                                                            change_points[a])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a, change_points[a])
                else:
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activities_for_plot[j])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a)
            if find_any_drift:
                # save the change points for the activity
                filename = os.path.join(self.output_path_adaptive_detector,
                                        f'drifts_{self.current_parameters.attribute}.txt')
                self.save_change_points(filename, change_points, change_points_info, activities)
            else:
                # if no drift is detected, generate the complete model and the plot with attribute values for each activity
                print(f'Analyzing unique window because no drift is detected...')
                # save the plot with attribute values for each activity
                for j, a in enumerate(activities):
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activities_for_plot[j])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a)
                # process the unique window
                initial_index[Activity.ALL.value] = 0
                initial_case_ids[Activity.ALL.value] = {}
                initial_case_ids[Activity.ALL.value][0] = case_id
                self.window_count[Activity.ALL.value] = 0
                self.new_window(initial_index[Activity.ALL.value], len(event_data), Activity.ALL.value)
            return self.window_count, self.metrics, initial_case_ids, None
        else:
            # read the events from the dataframe
            for i in event_data.index:
                # get the current case id and event id
                case_id = event_data['case:concept:name'][i]

                # save the first case id as the beginning of the first window
                if i == 0:
                    for a in activities:
                        initial_case_ids[a][i] = case_id
                        initial_index[a] = 0
                        initial_event_indexes[a] = [0]

                # for each new event, collect the duration per activity
                activity = event_data['concept:name'][i]
                if activity in activities:
                    timestamp = event_data['time:timestamp'][i]
                    value = attribute_class.get_value_df(event_data, i)
                    attribute_values[activity][i] = {
                        'value': value,
                        'timestamp': timestamp,
                        'case_id': case_id,
                    }

                    detector_dict[activity].update_val(value)
                    if detector_dict[activity].detected_change():
                        # create the manager for similarity metrics if a change is detected
                        if activity not in self.metrics.keys():
                            self.metrics[activity] = ManageSimilarityMetrics(self.model_type, self.current_parameters,
                                                                             self.control,
                                                                             self.models_path, self.metrics_path,
                                                                             activity)

                        # save the index of the event where the change is detected
                        event_id_for_activity = event_indexes[activity]  # count the events for the specified activity
                        change_points[activity].append(event_id_for_activity)
                        # save the timestamp of the event where the change is detected
                        change_points_time_based[activity].append(self.get_current_date_df(event_data, i))

                        change_points_info[activity].add_change_point(event_id_for_activity)
                        change_points_info[activity].add_case_id(case_id)
                        change_points_info[activity].add_timestamp(self.get_current_date_df(event_data, i))
                        print(
                            f'Change detected in data: {value} - at index: {i} - '
                            f'case: {case_id} - activity: {activity} - event if for activity {event_id_for_activity}')

                        # process new window
                        self.new_window(initial_index[activity], i, activity)
                        # save the initial of the processed window
                        initial_case_ids[activity][i] = case_id
                        # update the beginning of the next window
                        initial_index[activity] = i
                        # save the initial index id
                        initial_event_indexes[activity].append(event_id_for_activity)
                    # index of the event
                    event_indexes[activity] += 1
            # process remaining items as the last window
            find_any_drift = False
            for j, a in enumerate(activities):
                if len(change_points[a]) > 0:
                    find_any_drift = True
                    if initial_index[a] < len(event_data):
                        size = len(event_data) - initial_index[a]
                        print(
                            f'Analyzing final window... size {size} window_count {self.window_count[a]} activity {a}')
                        # set the final window used by metrics manager to identify all the metrics have been calculated
                        self.metrics[a].set_final_window(self.window_count[a])
                        # process final window for all activities where a drift has been detected
                        self.new_window(initial_index[a], len(event_data), a)
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activities_for_plot[j],
                                                            change_points[a],
                                                            change_points_time_based[a])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a, change_points[a],
                                                            change_points_time_based[a])
                else:
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activities_for_plot[j])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a)
            if find_any_drift:
                # save the change points for the activity
                filename = os.path.join(self.output_path_adaptive_detector, f'drifts_{attribute_class.name}.txt')
                self.save_change_points(filename, change_points, change_points_info, activities)
            else:
                # if no drift is detected, generate the complete model and the plot with attribute values for each activity
                print(f'Analyzing unique window because no drift is detected...')
                # save the plot with attribute values for each activity
                for j, a in enumerate(activities):
                    if self.current_parameters.activities_for_plot:
                        self.plot_signal_adaptive_time_data(attribute_values[a],
                                                            self.current_parameters.activitie_for_plot[j])
                    else:
                        self.plot_signal_adaptive_time_data(attribute_values[a], a)
                # process the unique window
                initial_index[Activity.ALL.value] = 0
                initial_case_ids[Activity.ALL.value] = {}
                initial_case_ids[Activity.ALL.value][0] = case_id
                initial_event_indexes[Activity.ALL.value] = [0]
                self.window_count[Activity.ALL.value] = 0
                self.new_window(initial_index[Activity.ALL.value], len(event_data), Activity.ALL.value)
            return self.window_count, self.metrics, initial_case_ids, initial_event_indexes

    # IPDD adaptive trace by trace approach
    # Apply the ADWIN detector (scikit-multiflow) in two quality dimensions: fitness and precision
    # The metrics for each dimension are defined by parameter metrics (dictionary)
    # The metrics are calculated using the last trace read and the model generated using the first traces (stable_period)
    # When a drift is detected a new model may be discovered using the next traces (stable_period)
    # The process model is discovered using the inductive miner
    def apply_detector_on_quality_metrics_trace_by_trace(self, event_data, detector_class, window_size, user):
        self.current_trace = 0
        print(f'Trace by trace approach - {detector_class.get_name()} to log {self.current_log.filename}')
        for key in detector_class.parameters:
            print(f'{key}: {detector_class.parameters[key]}')
        # different metrics can be used for each dimension evaluated
        # by now we expected one metric for fitness quality dimension and other for precision quality dimension
        metrics = {
            QualityDimension.FITNESS.name: 'fitnessTBR',
            QualityDimension.PRECISION.name: 'precisionETC',
        }
        # derive the initial model using the parameter stable_period
        print(f'Initial model discovered using traces from 0 to {window_size - 1}')
        log_for_model = EventLog(event_data[0:window_size])
        net, im, fm = pm4py.discover_petri_net_inductive(log_for_model, activity_key='concept:name',
                                                         case_id_key='case:concept:name',
                                                         timestamp_key='time:timestamp')
        pnml_filename = os.path.join(self.output_path_adaptive_models_detector,
                                     f'model1_0-{window_size - 1}.pnml')
        pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
        # other discovery algorithms can be applied
        # net, im, fm = heuristics_miner.apply(log_for_model)
        # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMf)
        # net, im, fm = inductive_miner.apply(log_for_model, variant=inductive_miner.Variants.IMd)
        detector_dict = {}
        drifts = {}
        values = {}
        # for saving the change points
        change_points = []
        detector_info = ChangePointInfo(detector_class.get_name())
        for key in detector_class.parameters:
            detector_info.add_detector_attribute(key, detector_class.parameters[key])
        change_points_info = detector_info

        # instantiate the detector
        for dimension in metrics.keys():
            # instantiate one detector for each evaluated dimension (fitness and precision)
            detector_dict[dimension] = SelectDetector.get_detector_instance(detector_class.get_definition(),
                                                                            detector_class.parameters)
            detector_dict[dimension].instantiate_detector()
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
            last_trace = EventLog(event_data[i:(i + 1)])
            # check if one of the metrics report a drift
            drift_detected = False
            for dimension in metrics.keys():
                # calculate the metric for each dimension
                # for each dimension decide if the metric should be calculated using only the last trace read or all
                # the traces read since the last drift
                new_value = calculate_quality_metric(metrics[dimension], last_trace, net, im, fm) * detector_class.factor
                values[dimension].append(new_value)
                # update the new value in the detector
                detector_dict[dimension].update_val(new_value)
                if detector_dict[dimension].detected_change():
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
                    detector_dict[dimension].reset()

                # discover a new model using the next traces (window_size)
                final_trace_id = i + window_size
                if final_trace_id > total_of_traces:
                    final_trace_id = total_of_traces

                if self.current_parameters.update_model:
                    print(f'Discover a new model using traces from {i} to {final_trace_id - 1}')
                    log_for_model = EventLog(event_data[i:final_trace_id])
                    net, im, fm = pm4py.discover_petri_net_inductive(log_for_model, activity_key='concept:name',
                                                                     case_id_key='case:concept:name',
                                                                     timestamp_key='time:timestamp')
                    pnml_filename = os.path.join(self.output_path_adaptive_models_detector,
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
            filename = os.path.join(self.output_path_adaptive_detector, f'drifts_{approach}.txt')
            self.save_change_points(filename, change_points, change_points_info)
        return self.window_count, self.metrics, self.initial_case_ids

    # IPDD adaptive windowing approach
    def apply_detector_on_quality_metrics_windowing(self, event_data, detector_class, window_size, user):
        factor = 100
        self.current_trace = 0
        print(f'Windowing approach - {detector_class.get_name()} to log {self.current_log.filename}')
        for key in detector_class.parameters:
            print(f'{key}: {detector_class.parameters[key]}')

        metrics = {
            QualityDimension.FITNESS.name: 'fitnessTBR',
            QualityDimension.PRECISION.name: 'precisionFP'
        }
        total_of_traces = len(event_data)
        # derive the model for evaluating the quality metrics
        initial_trace_id_for_stable_period = 0
        final_trace_id = initial_trace_id_for_stable_period + window_size
        log_for_model = EventLog(event_data[initial_trace_id_for_stable_period:final_trace_id])
        net, im, fm = pm4py.discover_petri_net_inductive(log_for_model, activity_key='concept:name',
                                                         case_id_key='case:concept:name',
                                                         timestamp_key='time:timestamp')
        pnml_filename = os.path.join(self.output_path_adaptive_models_detector,
                                     f'model1_{initial_trace_id_for_stable_period}-{final_trace_id - 1}.pnml')
        pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
        tree = pm4py.discover_process_tree_inductive(log_for_model, activity_key='concept:name',
                                                     case_id_key='case:concept:name',
                                                     timestamp_key='time:timestamp')
        print(f'Initial model discovered using traces [{initial_trace_id_for_stable_period}-{final_trace_id - 1}]')
        # initialize similarity metrics manager
        self.metrics = ManageSimilarityMetrics(self.model_type, self.current_parameters, self.control,
                                               self.models_path, self.metrics_path)
        # initialize window count and case ids
        self.window_count = 0
        self.initial_case_ids = {}
        values = dict.fromkeys(metrics)
        detector_dict = dict.fromkeys(metrics)
        drifts = dict.fromkeys(metrics)
        # for saving the change points
        change_points = []
        detector_info = ChangePointInfo(detector_class.get_name())
        for key in detector_class.parameters:
            detector_info.add_detector_attribute(key, detector_class.parameters[key])
        change_points_info = detector_info

        for m in metrics.keys():
            values[m] = []
            detector_dict[m] = SelectDetector.get_detector_instance(detector_class.get_definition(),
                                                                            detector_class.parameters)
            detector_dict[m].instantiate_detector()
            drifts[m] = []

        initial_trace_id = 0  # start of the window (change point)
        for i in range(0, total_of_traces):
            self.current_trace = i + 1
            # print(f'Reading trace {i}')
            current_trace = EventLog(event_data[i:i + 1])
            if i == initial_trace_id_for_stable_period:
                print(
                    f'Setup phase - traces [{initial_trace_id_for_stable_period}-{initial_trace_id_for_stable_period + window_size - 1}]')
                # initial of the stable period
                # during the stable period we apply the same value for the metrics
                # fitness - calculated using the initial trace of the stable period
                # precision - calculated using all the traces inside the stable period
                traces_stable_period = EventLog(
                    event_data[initial_trace_id_for_stable_period:initial_trace_id_for_stable_period + window_size])
                precision = calculate_quality_metric_footprints(metrics[QualityDimension.PRECISION.name],
                                                                traces_stable_period,
                                                                tree) * factor
                fitness = calculate_quality_metric(metrics[QualityDimension.FITNESS.name], current_trace, net, im,
                                                   fm) * factor
            elif i >= initial_trace_id_for_stable_period + window_size:
                print(f'Detection phase - reading trace {i}')
                window = EventLog(event_data[i - window_size + 1:i + 1])
                # after the stable period calculate the metrics after reading a new trace
                precision = calculate_quality_metric_footprints(metrics[QualityDimension.PRECISION.name], window,
                                                                tree) * factor
                fitness = calculate_quality_metric(metrics[QualityDimension.FITNESS.name], current_trace, net, im,
                                                   fm) * factor

            values[QualityDimension.PRECISION.name].append(precision)
            detector_dict[QualityDimension.PRECISION.name].update_val(precision)

            values[QualityDimension.FITNESS.name].append(fitness)
            detector_dict[QualityDimension.FITNESS.name].update_val(fitness)

            drift_detected = False
            change_point = 0
            # check for drift in precision
            if detector_dict[QualityDimension.PRECISION.name].detected_change():
                # define the change point as the initial of the window
                change_point = i - window_size + 1
                drifts[QualityDimension.PRECISION.name].append(change_point)
                print(f'Metric [{QualityDimension.PRECISION.value}] detected a drift in trace: {change_point}')
                drift_detected = True
            # check for drift in fitness
            elif detector_dict[QualityDimension.FITNESS.name].detected_change():
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
                    detector_dict[m].reset()
                if self.current_parameters.update_model:
                    # Discover a new model using window
                    log_for_model = EventLog(event_data[change_point:change_point + window_size])
                    net, im, fm = pm4py.discover_petri_net_inductive(log_for_model, activity_key='concept:name',
                                                                     case_id_key='case:concept:name',
                                                                     timestamp_key='time:timestamp')
                    pnml_filename = os.path.join(self.output_path_adaptive_models_detector,
                                                 f'model{self.window_count + 1}_{change_point}-{change_point + window_size - 1}.pnml')
                    pnml_exporter.apply(net, im, pnml_filename, final_marking=fm)
                    tree = pm4py.discover_process_tree_inductive(log_for_model, activity_key='concept:name',
                                                                 case_id_key='case:concept:name',
                                                                 timestamp_key='time:timestamp')
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
            filename = os.path.join(self.output_path_adaptive_detector, f'drifts_{approach}.txt')
            self.save_change_points(filename, change_points, change_points_info)
        return self.window_count, self.metrics, self.initial_case_ids

    def get_current_timestamp(self, item):
        # use the date of the first event within the trace
        timestamp_aux = datetime.timestamp(item[0]['time:timestamp'])
        return timestamp_aux

    def get_current_date(self, item):
        # use the date of the first event within the trace
        date_aux = item[0]['time:timestamp']
        return date_aux

    def get_current_date_df(self, event_data, index):
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

        if self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            # generate the sub-log for the window
            window = self.event_data[begin:end]
            sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
            initial_timestamp = self.get_current_date_df(window, begin)
        elif self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            sub_log = EventLog(self.event_data[begin:end])
            # get initial timestamp
            initial_timestamp = self.get_current_date(sub_log[0])
        else:
            print(f'Incorrect window type: {self.current_parameters.read_log_as}.')
            return

        # save the sublog
        if self.current_parameters.save_sublogs:
            self.save_sublog(sub_log, begin, end)

        self.execute_processes_for_window(sub_log, begin, initial_timestamp, activity)

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
