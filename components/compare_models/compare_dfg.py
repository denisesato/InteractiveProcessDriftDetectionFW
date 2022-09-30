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
import threading
from pm4py.algo.filtering.log.attributes import attributes_filter
from components.compare_models.controlflow_metric import ControlFlowMetric


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class DfgNodesSimilarityMetric(ControlFlowMetric):
    def __init__(self, window, trace, timestamp, metric_name, model1, model2, sublog1, sublog2):
        super().__init__(window, trace, timestamp, metric_name, model1, model2, sublog1, sublog2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        # get the current nodes from the traces using the name of the activities
        nodes_model1 = list(attributes_filter.get_attribute_values(self.sublog1, "concept:name").keys())
        nodes_model2 = list(attributes_filter.get_attribute_values(self.sublog2, "concept:name").keys())

        self.diff_removed = set(nodes_model1).difference(set(nodes_model2))
        self.diff_added = set(nodes_model2).difference(set(nodes_model1))

        inter = set(nodes_model1).intersection(set(nodes_model2))
        self.value = 2 * len(inter) / (len(nodes_model1) + len(nodes_model2))
        return self.value, self.diff_added, self.diff_removed


class DfgEdgesSimilarityMetric(ControlFlowMetric):
    def __init__(self, window, trace, timestamp, metric_name, model1, model2, sublog1, sublog2):
        super().__init__(window, trace, timestamp, metric_name, model1, model2, sublog1, sublog2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        edges1 = self.model1
        edges2 = self.model2

        self.diff_removed = set(edges1).difference(set(edges2))
        self.diff_added = set(edges2).difference(set(edges1))

        inter = set(edges1).intersection(set(edges2))
        self.value = 2 * len(inter) / (len(edges1) + len(edges2))
        return self.value, self.diff_added, self.diff_removed
