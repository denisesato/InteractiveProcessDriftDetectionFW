import json
import os
import time
from threading import Thread, RLock

import networkx as nx

from app import app
from components.dfg_definitions import get_dfg_filename, dfg_path, get_metrics_filename
from components.info import Info
from json_tricks import dumps, loads


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class ManageSimilarityMetrics:

    def __init__(self, original_filename, control):
        app.logger.info('**************************************************************************')
        app.logger.info(f'*** Cálculo de métricas iniciado para arquivo {original_filename}')
        app.logger.info('**************************************************************************')
        self.original_filename = original_filename
        self.final_window = 0
        self.metrics_count = 0
        self.control = control
        self.g1 = None
        self.g2 = None

        # Aqui deve ser atualizado sempre que incluir métrica
        self.metrics = ['nodes_similarity', 'edit_distance']

        # Para cada métrics deve ser criado um locker gerenciar acesso ao arquivo
        self.locks = {}
        for m in self.metrics:
            self.locks[m] = RLock()

        # Define o caminho para os arquivos de métricas
        # Será criado um arquivo para cada métrica implementada
        self.metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
        self.filenames = {}

        # verifica os arquivos de métricas
        self.verify_files()

        # para gerenciar timeout de métrica
        self.timeout = 60 # em segundos
        self.time_started = time.time()
        self.running = True
        self.check_metrics_timeout()

    # Organiza a estrutura de arquivos para que as métricas novas sejam armazenadas corretamente
    def verify_files(self):
        # Verifica se o diretório para salvar as metricas existe
        # caso contrário cria
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

        for metric in self.metrics:
            self.filenames[metric] = os.path.join(self.metrics_path,
                                                  get_metrics_filename(self.original_filename, metric))

            # Se o arquivo já existe apaga, para salvar as novas métricas
            # para o janelamento escolhido
            if os.path.exists(self.filenames[metric]):
                app.logger.info(f'Apagando arquivo {self.filenames[metric]}')
                os.remove(self.filenames[metric])

            # Cria o arquivo
            with open(self.filenames[metric], 'w') as fp:
                pass
            fp.close()

    def set_final_window(self, w):
        self.final_window = w

    def calculate_dfg_metrics(self, current_window):
        map_file1 = get_dfg_filename(self.original_filename, current_window - 1)
        map_file2 = get_dfg_filename(self.original_filename, current_window)

        filename1 = os.path.join(Info.data_models_path, dfg_path, self.original_filename, map_file1)
        filename2 = os.path.join(Info.data_models_path, dfg_path, self.original_filename, map_file2)

        files_ok = False
        while not files_ok:
            if os.path.exists(filename1) and os.path.exists(filename2):
                files_ok = True
            elif not os.path.exists(filename1):
                app.logger.error(f'[compare_dfg]: Não foi possível acessar dfg do arquivo [{map_file1}]')
            if not os.path.exists(filename2):
                app.logger.error(f'[compare_dfg]: Não foi possível acessar dfg do arquivo [{map_file2}]')

        # Obtem os dois dfgs
        self.g1 = nx.drawing.nx_agraph.read_dot(filename1)
        self.g2 = nx.drawing.nx_agraph.read_dot(filename2)

        # Calcula as métricas escolhidas e salva no arquivo
        # Aqui deve conter as chamadas as métricas que foram definidas em self.metrics
        self.calculate_nodes_similarity(current_window)
        self.calculate_edit_distance(current_window)

    @threaded
    def check_metrics_timeout(self):
        app.logger.error(f'Iniciando thread que monitora timeout so cálculo de métricas')
        while self.running:
            calculated_timeout = self.time_started + self.timeout
            if time.time() > calculated_timeout:
                app.logger.error(f'Timeout calculando métricas ')
                self.running = False
                self.control.time_out_metrics_calculation()
        app.logger.error(f'Encerrando thread que monitora timeout so cálculo de métricas')


    @threaded
    def calculate_edit_distance(self, current_window):
        metrics_info = EditDistanceMetric(current_window, 'edit_distance')
        metrics_info.calculate(self.g1, self.g2)
        self.save_metrics(metrics_info, self.filenames['edit_distance'], self.locks['edit_distance'])

    @threaded
    def calculate_nodes_similarity(self, current_window):
        metrics_info = NodesSimilarityMetric(current_window, 'nodes_similarity')
        metrics_info.calculate(self.g1, self.g2)
        self.save_metrics(metrics_info, self.filenames['nodes_similarity'], self.locks['nodes_similarity'])

    @threaded
    def calculate_edges_similarity(self, current_window):
        # rever
        metric, diff = SimilarityMetrics.edges_similarity(self.g1, self.g2)
        metrics_info = Metric(current_window, metric, diff)
        self.save_metrics(metrics_info, self.filenames['edges_similarity'], self.locks['edges_similarity'])

    @threaded
    def calculate_nodes_with_frequency_similarity(self, current_window):
        # rever
        metric, diff = SimilarityMetrics.nodes_with_frequency_similarity(self.g1, self.g2)
        metrics_info = Metric(current_window, 'nodes_with_frequency_similarity', metric, diff)
        self.save_metrics(metrics_info, self.filenames['nodes_with_frequency_similarity'],
                          self.locks['nodes_with_frequency_similarity'])

    @threaded
    def save_metrics(self, metric, filename, lock):
        file = None
        if metric.is_dissimilar():
            lock.acquire()
            try:
                # Atualiza arquivo com métricas
                file = open(filename, 'a+')
                # app.logger.info(f'Abriu arquivo: {filename} para adicionar métricas')
                file.write(metric.serialize())
                file.write('\n')
            finally:
                if file:
                    # app.logger.info(f'Fechou arquivo: {filename} para adicionar métricas')
                    file.close()
                self.metrics_count += 1
                lock.release()
        else:
            self.metrics_count += 1

        app.logger.info(f'METRICS COUNT: {self.metrics_count}')
        if self.final_window != 0 and self.metrics_count == ((self.final_window - 1) * len(self.metrics)):
            app.logger.info('**************************************************************************')
            app.logger.info(f'*** Cálculo da métrica finalizado para arquivo {self.original_filename}')
            app.logger.info('**************************************************************************')
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


class SimilarityMetrics:
    @staticmethod
    def nodes_similarity(g1, g2):
        nodes_g1 = [n[1]['label'] for n in g1.nodes.data()]
        labels_g1 = [l.partition('(')[0] for l in nodes_g1]
        nodes_g2 = [n[1]['label'] for n in g2.nodes.data()]
        labels_g2 = [l.partition('(')[0] for l in nodes_g2]
        diff = set(labels_g1).symmetric_difference(set(labels_g2))
        inter = set(labels_g1).intersection(set(labels_g2))
        sim_metric = 2 * len(inter) / (len(labels_g1) + len(labels_g2))
        return sim_metric, diff

    @staticmethod
    def nodes_with_frequency_similarity(g1, g2):
        nodes_g1 = [n[1]['label'] for n in g1.nodes.data()]
        nodes_g2 = [n[1]['label'] for n in g2.nodes.data()]
        diff = set(nodes_g1).symmetric_difference(set(nodes_g2))
        inter = set(nodes_g1).intersection(set(nodes_g2))
        sim_metric = 2 * len(inter) / (len(nodes_g1) + len(nodes_g2))
        return sim_metric, diff

    @staticmethod
    def edges_similarity(g1, g2):
        new_g1 = SimilarityMetrics.remove_frequencies_from_labels(g1)
        new_g2 = SimilarityMetrics.remove_frequencies_from_labels(g2)

        new_g1, new_g2 = SimilarityMetrics.remove_different_nodes(new_g1, new_g2)

        diff = nx.difference(new_g1, new_g2)
        for edge in diff.edges:
            print(edge)
        return 0

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

    @staticmethod
    def remove_different_nodes(g1, g2):
        metric, diff = SimilarityMetrics.nodes_similarity(g1, g2)
        # se não houver nós diferentes já retorna os grafos
        if metric == 1:
            return g1, g2

        # falta terminar
        return g1, g2


class Metric:
    def __init__(self, window, name):
        self.window = window
        self.name = name
        self.diff = set()
        self.value = 0

    def serialize(self):
        return dumps(self)

    def remove_frequencies_from_labels(self, g):
        # Remove as frequências dos nós dos grafos
        mapping = {}
        for node in g.nodes.data():
            old_label = node[1]['label']
            new_label = old_label.partition('(')[0]
            mapping[node[0]] = new_label
        g_new = nx.relabel_nodes(g, mapping)
        return g_new

    def get_labels(self, g):
        nodes_g = [n[1]['label'] for n in g.nodes.data()]
        labels_g = [l.partition('(')[0] for l in nodes_g]
        return labels_g


class NodesSimilarityMetric(Metric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self, g1, g2):
        labels_g1 = super().get_labels(g1)
        labels_g2 = super().get_labels(g2)
        self.diff = set(labels_g1).symmetric_difference(set(labels_g2))
        inter = set(labels_g1).intersection(set(labels_g2))
        self.value = 2 * len(inter) / (len(labels_g1) + len(labels_g2))


class EditDistanceMetric(Metric):
    def __init__(self, window, name):
        super().__init__(window, name)

    def is_dissimilar(self):
        return self.value > 0

    def calculate(self, g1, g2):
        self.value = nx.graph_edit_distance(g1, g2)
        self.diff = set()


class RecoverMetrics:
    def __init__(self, original_filename):
        # Aqui deve ser atualizado sempre que incluir métrica
        self.metrics = ['nodes_similarity', 'edit_distance']
        self.metrics_info = []

        # Para cada métrics deve ser criado um locker gerenciar acesso ao arquivo
        self.locks = {}
        for m in self.metrics:
            self.locks[m] = RLock()

        # Define o caminho para os arquivos de métricas
        # Será criado um arquivo para cada métrica implementada
        self.original_filename = original_filename
        self.metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
        self.filenames = {}
        for metric in self.metrics:
            self.filenames[metric] = os.path.join(self.metrics_path,
                                                  get_metrics_filename(self.original_filename, metric))
