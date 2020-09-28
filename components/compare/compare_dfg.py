import json
import os
from threading import Thread, RLock

import networkx as nx
from networkx.drawing.nx_agraph import read_dot

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


class CalculateMetrics:

    def __init__(self, original_filename, control):
        app.logger.info('**************************************************************************')
        app.logger.info(f'*** Cálculo de métricas iniciado para arquivo {original_filename}')
        app.logger.info('**************************************************************************')
        self.original_filename = original_filename
        self.final_window = 0
        self.metrics_count = 0
        self.control = control

        # Aqui deve ser atualizado sempre que incluir métrica
        # self.metrics = ['edit_distance', 'nodes_similarity', 'nodes_with_frequency_similarity']
        # self.metrics = ['nodes_similarity', 'edges_similarity']
        self.metrics = ['nodes_similarity']

        # Para cada métrics deve ser criado um locker gerenciar acesso ao arquivo
        self.locks = {}
        for m in self.metrics:
            self.locks[m] = RLock()

        # Define o caminho para os arquivos de métricas
        # Será criado um arquivo para cada métrica implementada
        self.metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
        self.output_files = {}

        # verifica os arquivos de métricas
        self.verify_files()

    # Organiza a estrutura de arquivos para que as métricas novas sejam armazenadas corretamente
    def verify_files(self):
        # Verifica se o diretório para salvar as metricas existe
        # caso contrário cria
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

        for metric in self.metrics:
            self.output_files[metric] = os.path.join(self.metrics_path,
                                                     get_metrics_filename(self.original_filename, metric))

            # Se o arquivo já existe apaga, para salvar as novas métricas
            # para o janelamento escolhido
            if os.path.exists(self.output_files[metric]):
                os.remove(self.output_files[metric])

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
        g1 = read_dot(filename1)
        g2 = read_dot(filename2)

        # Calcula novas métricas e adiciona no objeto
        # Aqui deve conter as chamadas as métricas que foram definidas
        # em self.metrics
        self.calculate_nodes_similarity(current_window, g1, g2)
        # self.calculate_edges_similarity(current_window, g1, g2)

    @threaded
    def calculate_edit_distance(self, current_window, g1, g2):
        edit_distance = nx.edit_distance(g1, g2)
        # app.logger.info(f'Graph edit distance entre janelas [{current_window - 1}]-[{current_window}]: {edit_distance}')
        metrics_dict = {f'window[{current_window}]': edit_distance}
        self.save_metrics(metrics_dict, self.output_files['edit_distance'], self.locks['edit_distance'])

    @threaded
    def calculate_nodes_similarity(self, current_window, g1, g2):
        metric, diff = SimilarityMetrics.nodes_similarity(g1, g2)
        # app.logger.info(f'Nodes similarity entre janelas [{current_window - 1}]-[{current_window}]: {metric}')
        metrics_info = Metric(current_window, metric, diff)
        self.save_metrics(metrics_info, self.output_files['nodes_similarity'], self.locks['nodes_similarity'])

    @threaded
    def calculate_edges_similarity(self, current_window, g1, g2):
        metric, diff = SimilarityMetrics.edges_similarity(g1, g2)
        # app.logger.info(f'Edges similarity entre janelas [{current_window - 1}]-[{current_window}]: {metric}')
        metrics_info = Metric(current_window, metric, diff)
        self.save_metrics(metrics_info, self.output_files['edges_similarity'], self.locks['edges_similarity'])

    @threaded
    def calculate_nodes_with_frequency_similarity(self, current_window, g1, g2):
        metric, diff = SimilarityMetrics.nodes_with_frequency_similarity(g1, g2)
        # app.logger.info(f'Nodes with_frequency_similarity entre janelas [{current_window - 1}]-[{current_window}]: {metric}')
        metrics_info = Metric(current_window, metric, diff)
        self.save_metrics(metrics_info, self.output_files['nodes_with_frequency_similarity'],
                          self.locks['nodes_with_frequency_similarity'])

    @threaded
    def save_metrics(self, metric, file, lock):
        lock.acquire()
        try:
            # Atualiza arquivo com métricas
            file = open(file, 'a+')
            file.write(metric.serialize())
            file.write('\n')
            file.close()
        finally:
            self.metrics_count += 1
            lock.release()

        if self.final_window != 0 and self.metrics_count == ((self.final_window - 1) * len(self.metrics)):
            app.logger.info('**************************************************************************')
            app.logger.info(f'*** Cálculo de métricas finalizado para arquivo {self.original_filename}')
            app.logger.info('**************************************************************************')
            self.control.finish_metrics_calculation()


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
    def __init__(self, window, value, diff):
        self.window = window
        self.metric_value = value
        self.diff = diff

    def serialize(self):
        return dumps(self)


class RecoverMetrics:
    def __init__(self, original_filename):
        # Aqui deve ser atualizado sempre que incluir métrica
        self.metrics = ['nodes_similarity']
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

    def get_window_candidates(self):
        for m in self.metrics:
            self.locks[m].acquire()
            file = open(self.filenames[m], "r")
            for line in file:
                self.metrics_info.append(loads(line, ignore_comments=True))
            self.locks[m].release()
        candidates = set()
        for metric in self.metrics_info:
            if metric.metric_value < 1:
                candidates.add(metric.window)
        return candidates

    def get_metric_and_diff(self, window):
        for m in self.metrics:
            self.locks[m].acquire()
            file = open(self.filenames[m], "r")
            for line in file:
                self.metrics_info.append(loads(line, ignore_comments=True))
            self.locks[m].release()
        diff = set()
        metric_mean = 0
        for metric in self.metrics_info:
            if metric.window == window:
                diff = diff.union(metric.diff)
                metric_mean += metric.metric_value
        # aqui depois vou ter que dividir pela quantidade de métricas escolhidas
        metric_mean = metric_mean
        return metric_mean, diff
