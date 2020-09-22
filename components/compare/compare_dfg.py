import json
import os
from threading import Thread, RLock
from typing import Any

from networkx import graph_edit_distance, optimize_graph_edit_distance
from networkx.drawing.nx_agraph import read_dot

from app import app
from components.dfg_definitions import get_dfg_filename, dfg_path, get_metrics_filename
from components.info import Info


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
        self.lock = RLock()
        self.verify_file()
        self.final_window = 0
        self.count_window = 1
        self.control = control

    def verify_file(self):
        # Verifica se o diretório para salvar as metricas existe
        # caso contrário cria
        metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
        if not os.path.exists(metrics_path):
            os.makedirs(metrics_path)

        # Define nome do arquivo de métricas
        filename = get_metrics_filename(self.original_filename)
        output_file = os.path.join(metrics_path, filename)

        # Se o arquivo já existe apaga, para gerar as novas métricas
        # para o janelamento escolhido
        if os.path.exists(output_file):
            os.remove(output_file)

    def set_final_window(self, w):
        self.final_window = w

    @threaded
    def calculate_dfg_metrics(self, current_window):
        map_file1 = get_dfg_filename(self.original_filename, current_window - 1)
        map_file2 = get_dfg_filename(self.original_filename, current_window)

        filename1 = os.path.join(Info.data_models_path, dfg_path, self.original_filename, map_file1)
        filename2 = os.path.join(Info.data_models_path, dfg_path, self.original_filename, map_file2)

        if not os.path.exists(filename1):
            app.logger.error(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file1}]')
            return -1

        if not os.path.exists(filename2):
            app.logger.error(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file2}]')
            return -1

        # Obtem os dois dfgs
        g1 = read_dot(filename1)
        g2 = read_dot(filename2)

        metrics = {}

        # Calcula novas métricas e adiciona no objeto
        edit_distance = graph_edit_distance(g1, g2)
        app.logger.info(f'Graph edit distance entre janelas [{current_window-1}]-[{current_window}]: {edit_distance}')
        metrics[f'edit_distance[{current_window}]'] = edit_distance

        # Define nome do arquivo de métricas
        metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
        filename = get_metrics_filename(self.original_filename)
        output_file = os.path.join(metrics_path, filename)

        self.lock.acquire()
        try:
            # Atualiza arquivo com métricas
            file = open(output_file, 'a+')
            file.write(json.dumps(metrics))
            file.write('\n')
            file.close()
        finally:
            self.count_window += 1
            self.lock.release()

        if self.final_window != 0 and self.count_window == self.final_window:
            app.logger.info('**************************************************************************')
            app.logger.info(f'*** Cálculo de métricas finalizado para arquivo {self.original_filename}')
            app.logger.info('**************************************************************************')
            self.control.set_metrics_finished(True)