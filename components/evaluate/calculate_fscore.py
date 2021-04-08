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


class EvaluationMetric:
    def __init__(self, window_size):
        self.real_drifts = []
        self.detected_windows = []
        self.window_size = window_size
        self.fscore = 0

    def __init__(self, real_drifts, detected_windows, window_size):
        self.real_drifts = real_drifts
        self.detected_windows = detected_windows
        self.window_size = window_size
        self.fscore = 0

    def add_real_drift(self, trace_index):
        self.real_drifts.append(trace_index)

    def add_detected_window(self, detected_window):
        self.detected_windows.append(detected_window)

    def calculate_fscore(self):
        self.calculate_basic_metrics()
        self.calculate_precision()
        self.calculate_recall()

        fscore = 0
        if self.precision + self.recall > 0:
            fscore = (2 * self.precision * self.recall) / (self.precision + self.recall)

        return fscore

    def calculate_precision(self):
        self.precision = 0
        if self.tp + self.fp > 0:
            self.precision = self.tp / (self.tp + self.fp)

    def calculate_recall(self):
        self.recall = 0
        if self.tp + self.fn > 0:
            self.recall = self.tp / (self.tp + self.fn)

    # count the basic metrics TP, FP, and FN
    def calculate_basic_metrics(self):
        tps = []
        fns = []
        window_detected_correctly = [False for w in self.detected_windows]
        tp_found = False
        for drift in self.real_drifts:
            for i, window in enumerate(self.detected_windows):
                tp_found = False
                if ((window - 1) * self.window_size) <= drift < (window * self.window_size):
                    # actual drift is within a detected window
                    tps.append(drift)
                    tp_found = True
                    window_detected_correctly[i] = True
                    break
            if not tp_found:
                fns.append(drift)

        self.tp = len(tps)
        self.fn = len(fns)
        self.fp = 0
        for w in window_detected_correctly:
            if not w:
                self.fp += 1

