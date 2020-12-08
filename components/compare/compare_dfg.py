from threading import Thread

import networkx as nx
from json_tricks import dumps


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class DfgMetric:
    def __init__(self, window, name):
        self.diff = set()
        self.value = 0
        self.metrics = []
        self.window = window
        self.name = name

    def serialize(self):
        return dumps(self)

    # retorna o grafo com os labels sem frequencia
    def remove_frequencies_from_labels(self, g):
        # Remove as frequências dos nós dos grafos
        mapping = {}
        for node in g.nodes.data():
            old_label = node[1]['label']
            new_label = old_label.partition('(')[0]
            mapping[node[0]] = new_label
        g_new = nx.relabel_nodes(g, mapping)
        return g_new

    # COM PROBLEMAS, RESOLVER
    def remove_different_nodes(self, g1, g2, diff_nodes):
        for node in diff_nodes:
            if node in g1.nodes:
                g1.remove_node(node)
            if node in g2.nodes:
                g2.remove_node(node)

        return g1, g2

    # retorna o conjunto de labels sem as frequências
    def get_labels(self, g):
        nodes_g = [n[1]['label'] for n in g.nodes.data()]
        labels_g = [l.partition('(')[0] for l in nodes_g]
        return labels_g


class DfgNodesSimilarityMetric(DfgMetric):
    def __init__(self, window, name):
        super().__init__(window, name)
        self.diff_nodes = set()

    def is_dissimilar(self):
        return self.value < 1

    @threaded
    def calculate(self, g1, g2):
        labels_g1 = super().get_labels(g1)
        labels_g2 = super().get_labels(g2)
        self.diff = set(labels_g1).symmetric_difference(set(labels_g2))
        # utilizado para remover nós diferentes para poder calcular edges similarity
        self.diff_nodes = set(g1.nodes()).symmetric_difference(set(g2.nodes()))
        inter = set(labels_g1).intersection(set(labels_g2))
        self.value = 2 * len(inter) / (len(labels_g1) + len(labels_g2))


class DfgEditDistanceMetric(DfgMetric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value > 0

    @threaded
    def calculate(self, g1, g2):
        new_g1 = super().remove_frequencies_from_labels(g1)
        new_g2 = super().remove_frequencies_from_labels(g2)

        # usar ou não timeout
        # self.value = nx.graph_edit_distance(g1, g2, timeout=30)
        self.value = nx.graph_edit_distance(new_g1, new_g2)
        self.diff = set()


class DfgEdgesSimilarityMetric(DfgMetric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value < 1

    @threaded
    def calculate(self, g1, g2):
        new_g1 = super().remove_frequencies_from_labels(g1)
        new_g2 = super().remove_frequencies_from_labels(g2)

        # calcula similaridade entre nós primeiro
        nodes_metric = DfgNodesSimilarityMetric(self.window, self.name)
        nodes_metric.calculate(new_g1, new_g2)

        # verifica a métrica de similaridade de nós
        # se for diferente de 1 devemos primeiro remover os nós
        # diferentes para depois calcular a métrica de similaridade de arestas
        if nodes_metric.value < 1:
            new_g1, new_g2 = self.remove_different_nodes(new_g1, new_g2, nodes_metric.diff_nodes)

        # calcula a métrica de similaridade entre arestas
        inter = set(new_g1.edges).intersection(set(new_g2.edges))
        diff_graph = nx.symmetric_difference(new_g1, new_g2)
        self.diff = set()
        for e in diff_graph.edges:
            self.diff.add(e)
        self.value = 2 * len(inter) / (len(new_g1.edges) + len(new_g2.edges))

