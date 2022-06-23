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
from enum import Enum

from components.evaluate.evaluation_metric_info import EvaluationMetricInfo


class EvaluationMetricList(str, Enum):
    F_SCORE = 'F-score'
    FPR = 'False positive rate (FPR)'
    MEAN_DELAY = 'Mean delay'


class EvaluationMetric:
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        self.real_drifts = real_drifts
        self.detected_drifts = detected_drifts
        # traces or events, according to the selected option for reading the log
        self.number_of_items = items
        # basic metrics
        self.tp = 0
        self.fp = 0
        self.fn = 0
        self.tn = 0
        self.total_distance = 0  # used for the mean delay
        # value of the calculated metric
        self.value = 0

    # count the basic metrics TP, FP, FN, and TN
    def calculate_basic_metrics(self):
        real_drifts = self.real_drifts.copy()
        # sort the both lists (real and detected drifts)
        real_drifts.sort()
        self.detected_drifts.sort()

        # create lists to store the tp's and fp's
        tp_list = []
        fp_list = []
        fn_list = []
        self.total_distance = 0
        for i, detected_cp in enumerate(self.detected_drifts):
            possible_real_drifts = [cp for cp in real_drifts if detected_cp >= cp]
            possible_real_drifts.sort(reverse=True)
            if len(possible_real_drifts) > 0:
                detected_real_cp = possible_real_drifts[0]
                # the mean delay considers the distance between the real change point and the reported change point
                delay = detected_cp - detected_real_cp
                self.total_distance += delay

                tp_list.append(detected_cp)
                real_drifts.remove(detected_real_cp)
                possible_real_drifts.remove(detected_real_cp)
                # if other possible real drifts are not detected they are FALSE NEGATIVES
                for rp in possible_real_drifts:
                    fn_list.append(rp)
                    real_drifts.remove(rp)
            else:
                fp_list.append(detected_cp)

        # the remaining real drifts are also FALSE NEGATIVES
        for d in real_drifts:
            fn_list.append(d)

        self.tp = len(tp_list)
        self.fp = len(fp_list)
        self.fn = len(fn_list)
        self.tn = self.number_of_items - self.tp - self.fp - self.fn

    def calculate(self):
        pass

    def get_value(self):
        return self.value


class Fscore(EvaluationMetric):
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        super().__init__(real_drifts, detected_drifts, error_tolerance, items)

    def calculate(self):
        self.calculate_basic_metrics()
        if self.tp + self.fp > 0:
            precision = self.tp / (self.tp + self.fp)
            if self.tp + self.fn > 0:
                recall = self.tp / (self.tp + self.fn)
            if precision > 0 or recall > 0:
                f_score = 2 * ((precision * recall) / (precision + recall))
                return f_score
        return 0


# False positive rate
class FPR(EvaluationMetric):
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        super().__init__(real_drifts, detected_drifts, error_tolerance, items)

    def calculate(self):
        self.calculate_basic_metrics()
        fpr = self.fp / (self.fp + self.tn)
        return fpr

class MeanDelay(EvaluationMetric):
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        super().__init__(real_drifts, detected_drifts, error_tolerance, items)

    def calculate(self):
        if self.total_distance == 0:
            return 0
        return self.total_distance / self.tp


class ManageEvaluationMetrics:
    def __init__(self, evaluation_metrics, evaluation_path):
        # get the metrics selected by the user
        self.metrics_list = evaluation_metrics
        # create the path if it does not exist
        self.path = evaluation_path
        self.filename = os.path.join(self.path, f'Evaluation_metrics.txt')
        if not os.path.exists(self.path):
            print(f'Creating evaluation path {self.path}')
            os.makedirs(self.path)

    def add_real_drift(self, trace_index):
        self.real_drifts.append(trace_index)

    def add_detected_drift(self, drift):
        self.detected_drifts.append(drift)

    def save_metrics(self, metrics_info):
        # save the calculated metrics
        with open(self.filename, 'a+') as file:
            for info in metrics_info:
                file.write(info.serialize())
                file.write('\n')
        print(f'Saving evaluation metrics...')

    def calculate_selected_evaluation_metrics(self, real_drifts, detected_drifts, items,
                                              activity=None):
        metrics_info = []
        metrics_summary = {}
        for metric_name in self.metrics_list:
            print(f'Calculating evaluation metric [{metric_name}]')
            metric = ManageEvaluationMetrics.evaluation_metrics_factory(metric_name, real_drifts,
                                                                        detected_drifts, items)
            value = metric.calculate()
            metric_info = EvaluationMetricInfo(metric_name, real_drifts, detected_drifts, value)
            if activity:  # used when the user selected the ADAPTIVE approach
                metric_info.add_attribute('activity', activity)
            metrics_info.append(metric_info)
            metrics_summary[metric_name] = value
        self.save_metrics(metrics_info)
        return metrics_summary

    @staticmethod
    def evaluation_metrics_factory(metric_name, real_drifts, detected_drifts, items):
        # define all implemented evaluation metrics
        real_drifts_copy = real_drifts.copy()
        detected_drifts_copy = detected_drifts.copy()
        classes = {
            EvaluationMetricList.F_SCORE.value: Fscore(real_drifts_copy, detected_drifts_copy, items),
            EvaluationMetricList.FPR.value: FPR(real_drifts_copy, detected_drifts_copy, items),
            EvaluationMetricList.MEAN_DELAY.value: MeanDelay(real_drifts_copy, detected_drifts_copy, items),
        }
        return classes[metric_name]