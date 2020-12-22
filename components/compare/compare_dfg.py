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
    # retorna o grafo com os labels sem frequencia
    @staticmethod
    def remove_frequencies_from_labels(g):
        # Remove as frequências dos nós dos grafos
        mapping = {}
        for node in g.nodes.data():
            old_label = node[1]['label']
            new_label = old_label.partition('(')[0]
            mapping[node[0]] = new_label
        g_new = nx.relabel_nodes(g, mapping)
        return g_new

    # remove nós diferentes entre os grafos
    @staticmethod
    def remove_different_nodes(g1, g2, diff_nodes):
        for node in diff_nodes:
            if node in g1.nodes:
                g1.remove_node(node)
            if node in g2.nodes:
                g2.remove_node(node)
        return g1, g2

    # retorna o conjunto de labels sem as frequências
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

        # usar ou não timeout
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

        # calcula similaridade entre nós primeiro
        nodes_metric = DfgNodesSimilarityMetric(self.window, self.metric_name, self.model1, self.model2)
        nodes_metric.calculate()

        # verifica a métrica de similaridade de nós
        # se for diferente de 1 devemos primeiro remover os nós
        # diferentes para depois calcular a métrica de similaridade de arestas
        if nodes_metric.value < 1:
            new_g1, new_g2 = DfgMetricUtil.remove_different_nodes(new_g1, new_g2,
                                                                  set.union(nodes_metric.diff_added,
                                                                            nodes_metric.diff_removed))
        # obtem as diferenças de arestas entre grafos
        self.diff_removed = set()
        diff_removed = nx.difference(new_g1, new_g2)
        for e in diff_removed.edges:
            self.diff_removed.add(e)

        self.diff_added = set()
        diff_added = nx.difference(new_g2, new_g1)
        for e in diff_added.edges:
            self.diff_added.add(e)

        # calcula a métrica de similaridade entre arestas
        inter = set(new_g1.edges).intersection(set(new_g2.edges))
        self.value = 2 * len(inter) / (len(new_g1.edges) + len(new_g2.edges))
        return self.value, self.diff_added, self.diff_removed
