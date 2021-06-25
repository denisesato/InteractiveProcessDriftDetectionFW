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
from statistics import mean
from pm4py.objects.log.util import interval_lifecycle
from pm4py.statistics.sojourn_time.log import get as soj_time_get
from scipy import spatial

from components.compare_time.time_metric import TimeMetric


class CycleTime:
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
        time_log1 = CycleTime.filter_activities_from_log(time_log1, list_activities)
        time_log2 = CycleTime.filter_activities_from_log(time_log2, list_activities)
        return time_log1, time_log2

    @staticmethod
    def remove_activity_differences(time_log1, time_log2):
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
    def calculate_sojourn_time_similarity(log1, log2, list_of_activities=None):
        parameters = {'worktiming': [8, 17],
                      'weekends': [6, 7]}

        enriched_log1 = interval_lifecycle.assign_lead_cycle_time(log1, parameters=parameters)
        enriched_log2 = interval_lifecycle.assign_lead_cycle_time(log2, parameters=parameters)

        # soj_time1 = CycleTime.cycle_time_get(enriched_log1)
        # soj_time2 = CycleTime.cycle_time_get(enriched_log2)

        parameters = {soj_time_get.Parameters.TIMESTAMP_KEY: "time:timestamp",
                      soj_time_get.Parameters.START_TIMESTAMP_KEY: "start_timestamp", }

        soj_time1 = soj_time_get.apply(enriched_log1, parameters=parameters)
        soj_time2 = soj_time_get.apply(enriched_log2, parameters=parameters)

        # only compare times between activities existent in both logs
        soj_time1, soj_time2 = CycleTime.remove_activity_differences(soj_time1, soj_time2)

        # if the user define a list of activities, apply filter
        if list_of_activities:
            print(f'Considering only activities: {[a.casefold() for a in list_of_activities]}')
            soj_time1, soj_time2 = CycleTime.filter_activities(soj_time1, soj_time2, list_of_activities)

        # sort by the name of activity
        soj_time1 = dict(sorted(soj_time1.items()))
        soj_time2 = dict(sorted(soj_time2.items()))

        # print(f'Sojourn time sub-log1: {soj_time1}')
        # print(f'Sojourn time sub-log2: {soj_time2}')

        # get only the values
        values1 = tuple(soj_time1.values())
        values2 = tuple(soj_time2.values())

        # calculate cosine similarity
        cosine_distance = spatial.distance.cosine(values1, values2)
        cosine_similarity = 1 - cosine_distance
        # print(f'Cosine similarity: {cosine_similarity}')
        return cosine_similarity

    @staticmethod
    def cycle_time_get(log, activity_key='concept:name'):
        durations_dict = {}
        activities = [ev[activity_key] for trace in log for ev in trace]
        for act in activities:
            durations_dict[act] = []

        for trace in log:
            for event in trace:
                activity = event[activity_key]
                durations_dict[activity].append(event['@@approx_bh_partial_cycle_time'])

        for act in durations_dict:
            durations_dict[act] = mean(durations_dict[act])
        return durations_dict


class CycleTimeSimilarityMetric(TimeMetric):
    def __init__(self, window, trace, metric_name, sublog1, sublog2):
        super().__init__(window, trace, metric_name, sublog1, sublog2)
        # define activities to be considered in the CycleTimeSimilarityMetric
        # TODO use a parameter to define
        #self.list_activities = ['Alimentacao de Maquina', 'Parada de Curta Duracao', 'Maquina Trabalhando',
        #                  'Retirada do Produto']
        self.list_activities = None

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        # print(f'Calculate CycleTimeSimilarityMetric for window {self.window} - {self.list_activities}')
        #self.value = CycleTime.calculate_cycle_time_similarity(self.sublog1, self.sublog2)
        self.value = CycleTime.calculate_sojourn_time_similarity(self.sublog1, self.sublog2, self.list_activities)
        return self.value
