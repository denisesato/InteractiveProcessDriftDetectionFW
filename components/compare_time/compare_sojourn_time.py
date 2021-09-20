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
import pandas as pd
from pm4py.objects.log.obj import EventLog
from pm4py.objects.log.util import interval_lifecycle
import numpy as np
from scipy import stats
from components.compare_time.time_metric import TimeMetric
import math


def print_event(event):
    print(event)


def print_event_time(event):
    print(f'Event concept name: {event["concept:name"]}')
    print(f'@@duration: {event["@@duration"]}')
    if "@@approx_bh_partial_cycle_time" in event:
        print(f'@@approx_bh_partial_cycle_time: {event["@@approx_bh_partial_cycle_time"]}')
    if "approx_bh_partial_lead_time" in event:
        print(f'@@approx_bh_partial_lead_time: {event["@@"]}')


def print_log(log, name='', time=False):
    if time:
        print(f'Showing lead and cycle time for log [{name}]')
    else:
        print(f'Showing log [{name}]')
    for trace in log:
        print(f'Trace: {trace.attributes["concept:name"]}')
        for event in trace:
            if time:
                print_event_time(event)
            else:
                print_event(event)


class SojournTime:
    @staticmethod
    # Remove activities not listed in list_activities
    def filter_activities_from_log(time_log, list_activities):
        keys = time_log.keys()
        to_remove = []
        for k in keys:
            if k.casefold() not in (a.casefold() for a in list_activities):
                to_remove.append(k)
        # removing
        for key in to_remove:
            time_log.pop(key)
        return time_log

    @staticmethod
    def filter_activities(time_log1, time_log2, list_activities):
        time_log1 = SojournTime.filter_activities_from_log(time_log1, list_activities)
        time_log2 = SojournTime.filter_activities_from_log(time_log2, list_activities)
        return time_log1, time_log2

    @staticmethod
    def remove_activity_differences(time_log1, time_log2):  # TODO ver se precisa, pois removi nos samples
        keys1 = time_log1.keys()
        keys2 = time_log2.keys()
        remove_from1 = []
        remove_from2 = []
        # get keys to remove from log1
        for k1 in keys1:
            if k1 not in keys2:
                remove_from1.append(k1)
        # get keys to remove from log2
        for k2 in keys2:
            if k2 not in keys1:
                remove_from2.append(k2)

        # removing
        for key in remove_from1:
            time_log1.pop(key)
        for key in remove_from2:
            time_log2.pop(key)

        return time_log1, time_log2

    @staticmethod
    # accept an interval log as input
    def get_durations(log):
        activities = [ev['concept:name'] for trace in log for ev in trace]
        activities = np.unique(np.array(activities))
        sample = {}
        for a in activities:
            sample[a] = []

        # get sojourn time for each trace
        for trace in log:
            for event in trace:
                activity = event['concept:name']
                start_time = event['start_timestamp'].timestamp()
                complete_time = event['time:timestamp'].timestamp()
                sample[activity].append(complete_time - start_time)
        return sample

    @staticmethod
    def calculate_sojourn_time_similarity(log1, log2, window, parameters):
        # convert to interval log
        new_log1 = EventLog(log1)
        new_log2 = EventLog(log2)
        interval_log1 = interval_lifecycle.to_interval(new_log1)
        interval_log2 = interval_lifecycle.to_interval(new_log2)

        # for debug purpose
        # from pm4py.objects.conversion.log import converter as log_converter
        # dataframe = log_converter.apply(interval_log1, variant=log_converter.Variants.TO_DATA_FRAME)
        # dataframe.to_csv(f'data/debug/{window}_interval_log1.csv')
        # dataframe = log_converter.apply(interval_log2, variant=log_converter.Variants.TO_DATA_FRAME)
        # dataframe.to_csv(f'data/debug/{window}_interval_log2.csv')

        # get the samples, containing a list of values for each activity
        sample1 = SojournTime.get_durations(interval_log1)
        sample2 = SojournTime.get_durations(interval_log2)

        # remove activities that are not present in both samples
        keys_to_remove = []
        for a1 in sample1.keys():
            if a1 not in sample2:
                keys_to_remove.append(a1)
        for key in keys_to_remove:
            sample1.pop(key)

        keys_to_remove = []
        for a2 in sample2.keys():
            if a2 not in sample1:
                keys_to_remove.append(a2)
        for key in keys_to_remove:
            sample2.pop(key)

        # create list of all activities containing the difference in the sojourn time compared to the previous window
        # 1 - significant difference
        # 0 - no significant difference
        activities = {}
        for k in sample1.keys():
            activities[k] = 0

        # TODO Remove after finishing the debug
        # Save the samples
        # Create target directory & all intermediate directories if don't exists
        experiment_name = f'{parameters.logname}_winsize{parameters.winsize}'
        folder_name = os.path.join('data', 'debug', experiment_name, 'samples')
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        activities_with_difference = []
        for activity in sample1.keys():
            t = None
            p_value = None
            try:
                t, p_value = stats.ttest_rel(sample1[activity], sample2[activity])
            except ValueError as e:
                error = f'T Test paired cannot be calculated for activity {activity} windows {window - 1}-{window}: [{e}]'
                print(error)

            # TODO Remove after finishing the debug
            # create a file for each activity
            dict = {f'w{window - 1}': sample1[activity], f'w{window}': sample2[activity]}
            df = pd.DataFrame({key: pd.Series(value) for key, value in dict.items()})
            filename = f'test{window - 1}-{window}_{activity}.csv'
            # print(f'Saving CSV file {filename}')
            df.to_csv(os.path.join(folder_name, filename))
            # filename = f'test{window - 1}-{window}_{activity}.xlsx'
            # print(f'Saving excel file {filename}')
            # df.to_excel(os.path.join(folder_name, filename))

            if p_value and p_value < 0.05:
                # assume alternative hypothesis - evidence of significant difference between the samples
                activities_with_difference.append(activity)

            # to avoid error on the serialization for saving the metric's information
            if not p_value:
                p_value = f'Not calculated [{error}]'
            elif p_value and math.isnan(p_value):
                p_value = f'NaN'
            activities[activity] = p_value  # save the calculated p-value

        total_of_activities = len(sample1)
        percentual_of_difference = len(activities_with_difference) / total_of_activities

        return 1 - percentual_of_difference, activities_with_difference, activities


class SojournTimeSimilarityMetric(TimeMetric):
    def __init__(self, window, trace, metric_name, sublog1, sublog2, parameters):
        super().__init__(window, trace, metric_name, sublog1, sublog2, parameters)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        self.value, self.diff, self.activities = SojournTime.calculate_sojourn_time_similarity(self.sublog1,
                                                                                               self.sublog2,
                                                                                               self.window,
                                                                                               self.parameters)
        return self.value, self.diff, self.activities


class WaitingTime:
    @staticmethod
    # accept an interval log as input
    def get_waiting_time(log):
        activities = [ev['concept:name'] for trace in log for ev in trace]
        activities = np.unique(np.array(activities))
        sample = {}
        sample_total = {}
        for a in activities:
            sample[a] = []
            sample_total[a] = 0

        # enriched the log with lead, cycle and waiting time
        enriched_log = interval_lifecycle.assign_lead_cycle_time(log)

        # get the waiting time trace by trace
        for trace in enriched_log:
            # event = trace[-1]
            for event in trace:
                # return the wasted time ONLY with regards to the activity described by the ‘interval’ event
                waiting_time = event['@@approx_bh_this_wasted_time']
                sample[event['concept:name']].append(waiting_time)
        return sample

    @staticmethod
    def calculate_waiting_time_similarity(log1, log2, window):
        # convert to interval log
        new_log1 = EventLog(log1)
        new_log2 = EventLog(log2)
        interval_log1 = interval_lifecycle.to_interval(new_log1)
        interval_log2 = interval_lifecycle.to_interval(new_log2)

        # get the samples, containing a list of values for each activity
        sample1 = WaitingTime.get_waiting_time(interval_log1)
        sample2 = WaitingTime.get_waiting_time(interval_log2)

        # remove activities that are not present in both samples
        keys_to_remove = []
        for a1 in sample1.keys():
            if a1 not in sample2:
                keys_to_remove.append(a1)
        for key in keys_to_remove:
            sample1.pop(key)

        keys_to_remove = []
        for a2 in sample2.keys():
            if a2 not in sample1:
                keys_to_remove.append(a2)
        for key in keys_to_remove:
            sample2.pop(key)

        # create list of all activities containing the difference in the sojourn time compared to the previous window
        # 1 - significant difference
        # 0 - no significant difference
        activities = {}
        for k in sample1.keys():
            activities[k] = 0

        # TODO Remove after finishing the debug
        # Save the samples
        # Create target directory & all intermediate directories if don't exists
        folder_name = os.path.join('data', 'debug', 'samples_waiting_time')
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        activities_with_difference = []
        for activity in sample1.keys():
            t = None
            p_value = None
            try:
                t, p_value = stats.ttest_ind(sample1[activity], sample2[activity])
            except ValueError as e:
                error = f'T Test paired cannot be calculated for activity {activity}: [{e}]'
                print(error)

            # TODO Remove after finishing the debug
            # create a file for each activity
            dict = {f'w{window - 1}': sample1[activity], f'w{window}': sample2[activity]}
            df = pd.DataFrame({key: pd.Series(value) for key, value in dict.items()})
            filename = f'test{window - 1}-{window}_{activity}.csv'
            print(f'Saving CSV file {filename}')
            df.to_csv(os.path.join(folder_name, filename))
            # filename = f'test{window - 1}-{window}_{activity}.xlsx'
            # print(f'Saving excel file {filename}')
            # df.to_excel(os.path.join(folder_name, filename))

            if p_value and p_value < 0.05:
                # assume alternative hypothesis - evidence of significant difference between the samples
                activities_with_difference.append(activity)

            # to avoid error on the serialization for saving the metric's information
            if not p_value:
                p_value = f'Not calculated [{error}]'
            elif p_value and math.isnan(p_value):
                p_value = f'NaN'
            activities[activity] = p_value  # save the calculated p-value

        total_of_activities = len(sample1)
        percentual_of_difference = len(activities_with_difference) / total_of_activities

        return 1 - percentual_of_difference, activities_with_difference, activities


class WaitingTimeSimilarityMetric(TimeMetric):
    def __init__(self, window, trace, metric_name, sublog1, sublog2, parameters):
        super().__init__(window, trace, metric_name, sublog1, sublog2, parameters)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        self.value, self.diff, self.activities = WaitingTime.calculate_waiting_time_similarity(self.sublog1,
                                                                                               self.sublog2,
                                                                                               self.window)
        return self.value, self.diff, self.activities
