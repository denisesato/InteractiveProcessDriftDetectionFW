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
import networkx as nx

from components.compare.metric import Metric

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class DfgMetricUtil:
    # remove frequency information from activity name, returning a new process map
    @staticmethod
    def remove_frequencies_from_labels(g):
        # remove frequency information from labels
        mapping = {}
        for node in g.nodes.data():
            old_label = node[1]['label']
            new_label = old_label.partition('(')[0]
            mapping[node[0]] = new_label
        g_new = nx.relabel_nodes(g, mapping)
        return g_new

    # remove nodes not existent in both process maps
    @staticmethod
    def remove_different_nodes(g1, g2, diff_nodes):
        for node in diff_nodes:
            if node in g1.nodes:
                g1.remove_node(node)
            if node in g2.nodes:
                g2.remove_node(node)
        return g1, g2

    # return the set of labels (activity names) without frequency
    @staticmethod
    def get_labels(g):
        nodes_g = [n[1]['label'] for n in g.nodes.data()]
        labels_g = [l.partition('(')[0] for l in nodes_g]
        return labels_g


class DfgNodesSimilarityMetric(Metric):
    def __init__(self, window, metric_name, model1, model2):
        super().__init__(window, metric_name, model1, model2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        labels_g1 = DfgMetricUtil.get_labels(self.model1)
        labels_g2 = DfgMetricUtil.get_labels(self.model2)

        self.diff_removed = set(labels_g1).difference(set(labels_g2))
        self.diff_added = set(labels_g2).difference(set(labels_g1))

        inter = set(labels_g1).intersection(set(labels_g2))
        self.value = 2 * len(inter) / (len(labels_g1) + len(labels_g2))
        return self.value, self.diff_added, self.diff_removed


class DfgEditDistanceMetric(Metric):
    def __init__(self, window, metric_name, model1, model2):
        super().__init__(window, metric_name, model1, model2)

    def is_dissimilar(self):
        return self.value > 0

    def calculate(self):
        new_g1 = DfgMetricUtil.remove_frequencies_from_labels(self.model1)
        new_g2 = DfgMetricUtil.remove_frequencies_from_labels(self.model2)

        # option for setting the timeout in the nx library
        # self.value = nx.graph_edit_distance(g1, g2, timeout=30)
        self.value = nx.graph_edit_distance(new_g1, new_g2)
        self.diff_added = set()
        self.diff_removed = set()
        return self.value, self.diff_added, self.diff_removed


class DfgEdgesSimilarityMetric(Metric):
    def __init__(self, window, metric_name, model1, model2):
        super().__init__(window, metric_name, model1, model2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        new_g1 = DfgMetricUtil.remove_frequencies_from_labels(self.model1)
        new_g2 = DfgMetricUtil.remove_frequencies_from_labels(self.model2)

        # calulate the nodes similarity first
        nodes_metric = DfgNodesSimilarityMetric(self.window, self.metric_name, self.model1, self.model2)
        nodes_metric.calculate()

        # if the nodes similarity is different than 1
        # IPDD removes the different nodes
        # then it calculated the edges similarity metric
        if nodes_metric.value < 1:
            new_g1, new_g2 = DfgMetricUtil.remove_different_nodes(new_g1, new_g2,
                                                                  set.union(nodes_metric.diff_added,
                                                                            nodes_metric.diff_removed))
        # get the different edges
        self.diff_removed = set()
        diff_removed = nx.difference(new_g1, new_g2)
        for e in diff_removed.edges:
            self.diff_removed.add(e)

        self.diff_added = set()
        diff_added = nx.difference(new_g2, new_g1)
        for e in diff_added.edges:
            self.diff_added.add(e)

        # calculate the edges similarity metric
        inter = set(new_g1.edges).intersection(set(new_g2.edges))
        self.value = 2 * len(inter) / (len(new_g1.edges) + len(new_g2.edges))
        return self.value, self.diff_added, self.diff_removed
