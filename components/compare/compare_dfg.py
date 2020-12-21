import threading
import networkx as nx

from components.compare.metric_info import MetricInfo


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class Metric(threading.Thread):
    def __init__(self, window, metric_name, g1, g2):
        super().__init__()
        self.diff_added = set()
        self.diff_removed = set()
        self.value = 0
        self.window = window
        self.metric_name = metric_name
        self.g1 = g1
        self.g2 = g2
        self.metric_info = MetricInfo(window, metric_name)
        self.filename = None
        self.lock = None
        self.manager_similarity_metrics = None

    def set_saving_definitions(self, filename, lock, manager_similarity_metrics):
        self.filename = filename
        self.lock = lock
        self.manager_similarity_metrics = manager_similarity_metrics

    def get_info(self):
        return self.metric_info

    def save_metrics(self):
        file = None
        if self.is_dissimilar():
            self.lock.acquire()
            try:
                # Atualiza arquivo com métricas
                file = open(self.filename, 'a+')
                file.write(self.get_info().serialize())
                file.write('\n')
            finally:
                if file:
                    file.close()
                self.manager_similarity_metrics.increment_metrics_count()
                self.lock.release()
        else:
            self.manager_similarity_metrics.increment_metrics_count()
        print(f'Saving [{self.metric_name}] for windows [{self.window}-{self.window - 1}]')
        self.manager_similarity_metrics.check_finish()

    def run(self):
        value, diff_added, diff_removed = self.calculate()
        self.metric_info.set_value(value)
        self.metric_info.set_diff_added(diff_added)
        self.metric_info.set_diff_removed(diff_removed)
        self.save_metrics()


class DfgMetric(Metric):
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

    # remove nós diferentes entre os grafos
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
    def __init__(self, window, metric_name, g1, g2):
        super().__init__(window, metric_name, g1, g2)
        self.diff_nodes = set()

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        labels_g1 = super().get_labels(self.g1)
        labels_g2 = super().get_labels(self.g2)

        self.diff_removed = set(labels_g1).difference(set(labels_g2))
        self.diff_added = set(labels_g2).difference(set(labels_g1))
        # self.diff = set(labels_g1).symmetric_difference(set(labels_g2))

        # utilizado para remover nós diferentes para poder calcular edges similarity
        self.diff_nodes = set(self.g1.nodes()).symmetric_difference(set(self.g2.nodes()))
        inter = set(labels_g1).intersection(set(labels_g2))
        self.value = 2 * len(inter) / (len(labels_g1) + len(labels_g2))
        return self.value, self.diff_added, self.diff_removed


class DfgEditDistanceMetric(DfgMetric):
    def __init__(self, window, metric_name, g1, g2):
        super().__init__(window, metric_name, g1, g2)

    def is_dissimilar(self):
        return self.value > 0

    def calculate(self):
        new_g1 = super().remove_frequencies_from_labels(self.g1)
        new_g2 = super().remove_frequencies_from_labels(self.g2)

        # usar ou não timeout
        # self.value = nx.graph_edit_distance(g1, g2, timeout=30)
        self.value = nx.graph_edit_distance(new_g1, new_g2)
        self.diff_added = set()
        self.diff_removed = set()
        return self.value, self.diff_added, self.diff_removed


class DfgEdgesSimilarityMetric(DfgMetric):
    def __init__(self, window, metric_name, g1, g2):
        super().__init__(window, metric_name, g1, g2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        new_g1 = super().remove_frequencies_from_labels(self.g1)
        new_g2 = super().remove_frequencies_from_labels(self.g2)

        # calcula similaridade entre nós primeiro
        nodes_metric = DfgNodesSimilarityMetric(self.window, self.metric_name, self.g1, self.g2)
        nodes_metric.calculate()

        # verifica a métrica de similaridade de nós
        # se for diferente de 1 devemos primeiro remover os nós
        # diferentes para depois calcular a métrica de similaridade de arestas
        if nodes_metric.value < 1:
            new_g1, new_g2 = self.remove_different_nodes(new_g1, new_g2,
                                                         set.union(nodes_metric.diff_added, nodes_metric.diff_removed))

        # calcula a métrica de similaridade entre arestas
        inter = set(new_g1.edges).intersection(set(new_g2.edges))
        # diff_graph = nx.symmetric_difference(new_g1, new_g2)
        self.diff_removed = set()
        diff_removed = nx.difference(new_g1, new_g2)
        for e in diff_removed.edges:
            self.diff_removed.add(e)

        self.diff_added = set()
        diff_added = nx.difference(new_g2, new_g1)
        for e in diff_added.edges:
            self.diff_added.add(e)

        self.value = 2 * len(inter) / (len(new_g1.edges) + len(new_g2.edges))
        return self.value, self.diff_added, self.diff_removed
