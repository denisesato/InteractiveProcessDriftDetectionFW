import os
import time
from threading import Thread, RLock

import networkx as nx
from graphviz import Source
from pygraphviz import AGraph

from app import app
from components.dfg_definitions import get_model_filename, dfg_path, get_metrics_filename
from json_tricks import dumps, loads

# import win32file as wfile


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class ManageSimilarityMetrics:
    def __init__(self, original_filename, control, models_path, metrics_path):
        app.logger.info(f'**************************************************************************')
        app.logger.info(f'*** Similarity metrics calculation started for the file {original_filename}')
        app.logger.info(f'**************************************************************************')
        self.original_filename = original_filename
        self.final_window = 0
        self.metrics_count = 0
        self.control = control
        self.metrics_path = metrics_path
        self.models_path = models_path

        # Aqui deve ser atualizado sempre que incluir métrica
        #self.metrics = ['nodes_similarity', 'edges_similarity', 'edit_distance']
        self.metrics = ['nodes_similarity', 'edges_similarity']

        # Para cada métrics deve ser criado um locker gerenciar acesso ao arquivo
        self.locks = {}
        for m in self.metrics:
            self.locks[m] = RLock()

        # Define o caminho para os arquivos de métricas
        # Será criado um arquivo para cada métrica implementada
        self.metrics_path = os.path.join(self.metrics_path, dfg_path)
        # Verifica se o diretório existe, caso contrário cria
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

        self.filenames = {}

        # verifica os arquivos de métricas
        self.verify_files()

        # para gerenciar timeout de métrica
        self.timeout = 60  # em segundos
        self.time_started = time.time()
        self.running = True
        self.check_metrics_timeout()

        # alterando quantidade de arquivos abertos para verificar se problema muda
        #print("OLD max open files: {0:d}".format(wfile._getmaxstdio()))
        # 513 is enough for your original code (170 graphs), but you can set it up to 8192
        #wfile._setmaxstdio(5)  # !!! COMMENT this line to reproduce the crash !!!
        #print("NEW max open files: {0:d}".format(wfile._getmaxstdio()))

    # Organiza a estrutura de arquivos para que as métricas novas sejam armazenadas corretamente
    def verify_files(self):
        for metric in self.metrics:
            self.filenames[metric] = os.path.join(self.metrics_path,
                                                  get_metrics_filename(self.original_filename, metric))

            # Se o arquivo já existe apaga, para salvar as novas métricas
            # para o janelamento escolhido
            if os.path.exists(self.filenames[metric]):
                app.logger.info(f'Deleting file {self.filenames[metric]}')
                os.remove(self.filenames[metric])

            # Cria o arquivo
            with open(self.filenames[metric], 'w+') as fp:
                pass
            fp.close()

    def set_final_window(self, w):
        self.final_window = w

    def calculate_dfg_metrics(self, current_window):
        map_file1 = get_model_filename(self.original_filename, current_window - 1)
        map_file2 = get_model_filename(self.original_filename, current_window)

        dfg_models_path = os.path.join(self.models_path, dfg_path, self.original_filename)
        filename1 = os.path.join(dfg_models_path, map_file1)
        filename2 = os.path.join(dfg_models_path, map_file2)

        files_ok = False
        while not files_ok:
            if os.path.exists(filename1) and os.path.exists(filename2):
                files_ok = True
            elif not os.path.exists(filename1):
                print(f'[compare_dfg]: Problem trying to access dfg from file [{map_file1}]')
            if not os.path.exists(filename2):
                print(f'[compare_dfg]: Problem trying to access dfg from file [{map_file2}]')

        # Obtem os dois dfgs
        #print(f'Reading file: {[filename1]} ...')
        graph1 = nx.drawing.nx_agraph.read_dot(filename1)

        # várias tentativas frustradas
        #gviz1 = Source.from_file(filename=map_file1, directory=dfg_models_path)
        #f = open(filename1, 'rt')
        #graph_data = f.read()
        #f.close()
        #graph = pydot.graph_from_dot_data(graph_data)
        #graphs = pydot.graph_from_dot_data(gviz1.source)
        #G = AGraph()
        #G.read(filename1)
        #G.close()
        #G.from_string(gviz1.source)
        #G.clear()
        #G.close()
        #graph1 = nx.nx_agraph.from_agraph(G)

        #graph1 = nx.nx_agraph.read_dot(filename1)
        #graph1 = nx.nx_pydot.read_dot(filename1)
        # self.g1 = nx.drawing.nx_agraph.read_dot(filename1)
        #G = AGraph(string=graph_data)
        #graph1 = nx.nx_agraph.from_agraph(G)
        #G.clear()
        #G.close()
        #G = None

        #gviz1.close()
        #self.g1 = nx.drawing.nx_agraph.read_dot(filename1)

        #print(f'Reading file: {[filename2]} ...')
        graph2 = nx.drawing.nx_agraph.read_dot(filename2)

        # várias tentativas frustradas
        #f = open(filename2, 'rt')
        #graph_data = f.read()
        #f.close()
        #G = AGraph(string=graph_data)
        #graph2 = nx.nx_agraph.from_agraph(G)
        #G = AGraph(filename2)
        #self.g2 = nx.nx_agraph.from_agraph(G)
        #G.clear()
        #G.close()
        #G = None

        #gviz2 = Source.from_file(filename=map_file2, directory=dfg_models_path)
        #self.g2 = nx.nx_pydot.from_pydot(pydot.graph_from_dot_data(gviz2.source))
        #gviz2.close()
        #self.g2 = nx.drawing.nx_agraph.read_dot(filename2)

        #print(f'Starting to calculate similarity metrics between windows [{current_window-1}]-[{current_window}] ...')

        # Calcula as métricas escolhidas e salva no arquivo
        # Aqui deve conter as chamadas as métricas que foram definidas em self.metrics
        self.calculate_nodes_similarity(current_window, graph1, graph2)
        self.calculate_edges_similarity(current_window, graph1, graph2)
        #self.calculate_edit_distance(current_window)

    @threaded
    def check_metrics_timeout(self):
        print(f'\nStarting monitoring thread for similarity metrics calculation')
        while self.running:
            calculated_timeout = self.time_started + self.timeout
            if time.time() > calculated_timeout:
                print(f'Timeout reached')
                self.running = False
                self.control.time_out_metrics_calculation()
        print(f'\nFinishing monitoring thread for metrics calculation\n')

    @threaded
    def calculate_edit_distance(self, current_window, g1, g2):
        metrics_info = EditDistanceMetric(current_window, 'edit_distance')
        metrics_info.calculate(g1, g2)
        self.save_metrics(metrics_info, self.filenames['edit_distance'], self.locks['edit_distance'])

    @threaded
    def calculate_nodes_similarity(self, current_window, g1, g2):
        metrics_info = NodesSimilarityMetric(current_window, 'nodes_similarity')
        metrics_info.calculate(g1, g2)
        self.save_metrics(metrics_info, self.filenames['nodes_similarity'], self.locks['nodes_similarity'])

    @threaded
    def calculate_edges_similarity(self, current_window, g1, g2):
        metrics_info = EdgesSimilarityMetric(current_window, 'edges_similarity')
        metrics_info.calculate(g1, g2)
        self.save_metrics(metrics_info, self.filenames['edges_similarity'], self.locks['edges_similarity'])

    @threaded
    def save_metrics(self, metric, filename, lock):
        file = None
        if metric.is_dissimilar():
            lock.acquire()
            try:
                # Atualiza arquivo com métricas
                file = open(filename, 'a+')
                file.write(metric.serialize())
                file.write('\n')
            finally:
                if file:
                    file.close()
                self.metrics_count += 1
                lock.release()
        else:
            self.metrics_count += 1

        #print(f'METRICS COUNT: {self.metrics_count}')
        if self.final_window != 0 and self.metrics_count == ((self.final_window - 1) * len(self.metrics)):
            print(f'**************************************************************************')
            print(f'*** Similarity metrics calculation finished for the file {self.original_filename}')
            print(f'**************************************************************************')
            self.running = False
            self.control.finish_metrics_calculation()

    def get_window_candidates(self):
        candidates = set()
        file = None
        for m in self.metrics:
            self.locks[m].acquire()
            try:
                file = open(self.filenames[m], "r")
                for line in file:
                    metrics_info = loads(line, ignore_comments=True)
                    candidates.add(metrics_info.window)
            finally:
                if file:
                    file.close()
                self.locks[m].release()

        filename = os.path.join(self.metrics_path, self.original_filename + '_drift_windows.txt')
        print(f'Saving drift windows: {filename}')
        file_drift_windows = None
        try:
            file_drift_windows = open(filename, 'w+')
            file_drift_windows.write(str(candidates))
        finally:
            if file_drift_windows:
                file_drift_windows.close()

        return candidates

    def get_metrics_info(self, window):
        metrics = []
        for m in self.metrics:
            self.locks[m].acquire()
            file = open(self.filenames[m], "r")
            for line in file:
                metric_read = loads(line, ignore_comments=True)
                if metric_read.window == window:
                    metrics.append(metric_read)
                    break
            self.locks[m].release()
        return metrics


class Metric:
    def __init__(self, window, name):
        self.window = window
        self.name = name
        self.diff = set()
        self.value = 0

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


class NodesSimilarityMetric(Metric):
    def __init__(self, window, name):
        super().__init__(window, name)
        self.diff_nodes = set()

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self, g1, g2):
        labels_g1 = super().get_labels(g1)
        labels_g2 = super().get_labels(g2)
        self.diff = set(labels_g1).symmetric_difference(set(labels_g2))
        # utilizado para remover nós diferentes para poder calcular edges similarity
        self.diff_nodes = set(g1.nodes()).symmetric_difference(set(g2.nodes()))
        inter = set(labels_g1).intersection(set(labels_g2))
        self.value = 2 * len(inter) / (len(labels_g1) + len(labels_g2))


class EditDistanceMetric(Metric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value > 0

    def calculate(self, g1, g2):
        new_g1 = super().remove_frequencies_from_labels(g1)
        new_g2 = super().remove_frequencies_from_labels(g2)

        # usar ou não timeout
        # self.value = nx.graph_edit_distance(g1, g2, timeout=30)
        self.value = nx.graph_edit_distance(new_g1, new_g2)
        self.diff = set()


class EdgesSimilarityMetric(Metric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self, g1, g2):
        new_g1 = super().remove_frequencies_from_labels(g1)
        new_g2 = super().remove_frequencies_from_labels(g2)

        # calcula similaridade entre nós primeiro
        nodes_metric = NodesSimilarityMetric(self.window, self.name)
        nodes_metric.calculate(new_g1, new_g2)

        # verifica a métrica de similaridade de nós
        # se for diferente de 1 devemos primeiro remover os nós
        # diferentes para depois calcular a métrica de similaridade de arestas
        if nodes_metric.value < 1:
            new_g1, new_g2 = self.remove_different_nodes(new_g1, new_g2, nodes_metric.diff_nodes)

        # calcula a métrics de similaridade entre arestas
        inter = set(new_g1.edges).intersection(set(new_g2.edges))
        diff_graph = nx.symmetric_difference(new_g1, new_g2)
        self.diff = set()
        for e in diff_graph.edges:
            self.diff.add(e)
        self.value = 2 * len(inter) / (len(new_g1.edges) + len(new_g2.edges))
