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


class EvaluationMetric:
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        self.real_drifts = real_drifts
        self.detected_drifts = detected_drifts
        # tolerance in number of items, used in the F-score, for instance
        self.error_tolerance = error_tolerance
        # traces or events, according to the selected option for reading the log
        self.number_of_items = items
        # basic metrics
        self.tp = 0
        self.fp = 0
        self.fn = 0
        self.tn = 0
        self.recall = 0
        self.precision = 0
        # value of the calculated metric
        self.value = 0

    # count the basic metrics TP, FP, FN, and TN
    def calculate_basic_metrics(self):
        tps = []
        fns = []
        self.real_drifts.sort()
        self.detected_drifts.sort()
        for i, real_drift in enumerate(self.real_drifts):
            tp_found = False
            for detected_drift in self.detected_drifts:
                tolerance_interval = self.error_tolerance
                # if there is another real drift, check the interval of tolerance
                if (i+1) < len(self.real_drifts):
                    interval_to_next_drift = self.real_drifts[i+1] - real_drift
                    if self.error_tolerance > interval_to_next_drift:
                        # if error_tolerance is greater than the distance to the next real drift
                        # use the distance as interval
                        tolerance_interval = interval_to_next_drift

                if real_drift <= detected_drift < (real_drift + tolerance_interval):
                    # real drift is within a detected window
                    tps.append(real_drift)
                    tp_found = True
                    # remove the drift counted as TP
                    self.detected_drifts.remove(detected_drift)
                    break
            if not tp_found:
                # if the real drift it is not detected, it is counted as a false negative
                fns.append(real_drift)
        self.tp = len(tps)
        self.fn = len(fns)
        self.fp = len(self.detected_drifts)  # the true positives are removed from the list
        self.tn = self.number_of_items - self.tp - self.fn - self.fp

    def calculate(self):
        pass

    def get_value(self):
        return self.value


class Fscore(EvaluationMetric):
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        super().__init__(real_drifts, detected_drifts, error_tolerance, items)

    def calculate(self):
        self.calculate_basic_metrics()
        precision = self.calculate_precision()
        recall = self.calculate_recall()
        fscore = 0
        if precision + recall > 0:
            fscore = 2 * ((precision * recall) / (precision + recall))
        return fscore

    def calculate_precision(self):
        precision = 0
        if self.tp + self.fp > 0:
            precision = self.tp / (self.tp + self.fp)
        return precision

    def calculate_recall(self):
        recall = 0
        if self.tp + self.fn > 0:
            recall = self.tp / (self.tp + self.fn)
        return recall


# False positive rate
class FPR(EvaluationMetric):
    def __init__(self, real_drifts, detected_drifts, error_tolerance, items):
        super().__init__(real_drifts, detected_drifts, error_tolerance, items)

    def calculate(self):
        self.calculate_basic_metrics()
        fpr = self.fp / (self.fp + self.tn)
        return fpr


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
        # else:
        #     # remove file that contains the evaluation metrics calculated from previous run
        #     if os.path.isfile(self.filename):
        #         print(f'Remove file {self.filename}')
        #         os.remove(self.filename)

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

    def calculate_selected_evaluation_metrics(self, real_drifts, detected_drifts, error_tolerance, items, activity=None):
        metrics_info = []
        metrics_summary = {}
        for metric_name in self.metrics_list:
            print(f'Calculating evaluation metric [{metric_name}]')
            metric = ManageEvaluationMetrics.evaluation_metrics_factory(metric_name, real_drifts, detected_drifts,
                                                                 error_tolerance, items)
            value = metric.calculate()
            metric_info = EvaluationMetricInfo(metric_name, real_drifts, detected_drifts, value)
            if activity:  # used when the user selected the ADAPTIVE approach
                metric_info.add_attribute('activity', activity)
            metrics_info.append(metric_info)
            metrics_summary[metric_name] = value
        self.save_metrics(metrics_info)
        return metrics_summary

    @staticmethod
    def evaluation_metrics_factory(metric_name, real_drifts, detected_drifts, error_tolerance, items):
        # define all implemented evaluation metrics
        real_drifts_copy = real_drifts.copy()
        detected_drifts_copy = detected_drifts.copy()
        classes = {
            EvaluationMetricList.F_SCORE.value: Fscore(real_drifts_copy, detected_drifts_copy, error_tolerance, items),
            EvaluationMetricList.FPR.value: FPR(real_drifts_copy, detected_drifts_copy, error_tolerance, items),
        }
        return classes[metric_name]
