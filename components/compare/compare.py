import os
import time
from threading import RLock, Thread

import networkx as nx
from app import app
from components.dfg_definitions import DfgDefinitions
from json_tricks import loads
# comentar para executar no linux
import win32file as wfile


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class ManageSimilarityMetrics:
    def __init__(self, model_type, original_filename, control, models_path, metrics_path):
        print(f'**************************************************************************')
        print(f'*** Similarity metrics calculation started for the file {original_filename}')
        print(f'**************************************************************************')
        self.original_filename = original_filename
        self.final_window = 0
        self.metrics_count = 0
        self.control = control
        self.models_path = models_path
        self.model_type = model_type

        if self.model_type == 'dfg':
            self.model_type_definitions = DfgDefinitions()
        else:
            print(f'Model type [{self.model_type}] does not have similarity metrics implemented.')
            self.finish()
            self.metrics_list = None
            return

        self.metrics_list = self.model_type_definitions.get_metrics()

        # Para cada métrics deve ser criado um locker gerenciar acesso ao arquivo
        self.locks = {}
        for m in self.metrics_list:
            self.locks[m] = RLock()

        # Define o caminho para os arquivos de métricas
        # Será criado um arquivo para cada métrica implementada
        self.metrics_path = self.model_type_definitions.get_metrics_path(metrics_path)
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

        # print("OLD max open files: {0:d}".format(wfile._getmaxstdio()))
        # 513 is enough for your original code (170 graphs), but you can set it up to 8192

        # alterando quantidade permotida de arquivos abertos
        # comentar para executar no linux
        wfile._setmaxstdio(8192)  # !!! COMMENT this line to reproduce the crash !!!
        print(f'NEW max open files: {[wfile._getmaxstdio()]}')

    # Organiza a estrutura de arquivos para que as métricas novas sejam armazenadas corretamente
    def verify_files(self):
        for metric in self.metrics_list:
            self.filenames[metric] = os.path.join(self.metrics_path,
                                                  self.model_type_definitions.get_metrics_filename(
                                                      self.original_filename, metric))

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

    def calculate_metrics(self, current_window):
        map_file1 = self.model_type_definitions.get_model_filename(self.original_filename, current_window - 1)
        map_file2 = self.model_type_definitions.get_model_filename(self.original_filename, current_window)

        dfg_models_path = self.model_type_definitions.get_models_path(self.models_path, self.original_filename)
        filename1 = os.path.join(dfg_models_path, map_file1)
        filename2 = os.path.join(dfg_models_path, map_file2)

        files_ok = False
        while not files_ok:
            if os.path.exists(filename1) and os.path.exists(filename2):
                files_ok = True
            elif not os.path.exists(filename1):
                print(f'[compare]: Problem trying to access dfg from file [{map_file1}]')
            if not os.path.exists(filename2):
                print(f'[compare]: Problem trying to access dfg from file [{map_file2}]')

        # Obtem os dois dfgs
        # print(f'Reading file: {[filename1]} ...')
        model1 = nx.drawing.nx_agraph.read_dot(filename1)

        # várias tentativas frustradas
        # gviz1 = Source.from_file(filename=map_file1, directory=dfg_models_path)
        # f = open(filename1, 'rt')
        # graph_data = f.read()
        # f.close()
        # graph = pydot.graph_from_dot_data(graph_data)
        # graphs = pydot.graph_from_dot_data(gviz1.source)
        # G = AGraph()
        # G.read(filename1)
        # G.close()
        # G.from_string(gviz1.source)
        # G.clear()
        # G.close()
        # graph1 = nx.nx_agraph.from_agraph(G)

        # graph1 = nx.nx_agraph.read_dot(filename1)
        # graph1 = nx.nx_pydot.read_dot(filename1)
        # self.g1 = nx.drawing.nx_agraph.read_dot(filename1)
        # G = AGraph(string=graph_data)
        # graph1 = nx.nx_agraph.from_agraph(G)
        # G.clear()
        # G.close()
        # G = None

        # gviz1.close()
        # self.g1 = nx.drawing.nx_agraph.read_dot(filename1)

        # print(f'Reading file: {[filename2]} ...')
        model2 = nx.drawing.nx_agraph.read_dot(filename2)

        # print(f'Starting to calculate similarity metrics between windows [{current_window-1}]-[{current_window}] ...')

        # Calcula as métricas escolhidas e salva no arquivo
        # Aqui deve conter as chamadas as métricas que foram definidas em self.metrics
        self.calculate_configured_similarity_metrics(current_window, model1, model2)

    def calculate_configured_similarity_metrics(self, current_window, m1, m2):
        for metric_name in self.metrics_list:
            #print(f'Starting [{metric_name}] calculation between windows [{current_window}-{current_window-1}]')
            metric = self.model_type_definitions.metrics_factory(self.metrics_list[metric_name], current_window, metric_name, m1, m2)
            metric.set_saving_definitions(self.filenames[metric_name], self.locks[metric_name], self)
            metric.start()

    def increment_metrics_count(self):
        self.metrics_count += 1

    def check_finish(self):
        #print(f'Checking if similarity metrics calculation finished: metrics_count [{self.metrics_count}] - '
        #      f'total of calculated metrics [{((self.final_window - 1) * len(self.metrics_list))}]')
        if self.final_window != 0 and self.metrics_count == ((self.final_window - 1) * len(self.metrics_list)):
            self.finish()

    @threaded
    def check_metrics_timeout(self):
        print(f'**************************************************************************')
        print(f'Starting monitoring thread for similarity metrics calculation')
        print(f'**************************************************************************')
        while self.running:
            calculated_timeout = self.time_started + self.timeout
            if time.time() > calculated_timeout:
                print(f'******* Timeout reached ********')
                self.running = False
                self.control.time_out_metrics_calculation()
        print(f'**************************************************************************')
        print(f'Finishing monitoring thread for metrics calculation')
        print(f'**************************************************************************')

    def finish(self):
        print(f'\n**************************************************************************')
        print(f'*** Similarity metrics calculation finished for the file {self.original_filename}')
        print(f'**************************************************************************')
        self.running = False
        self.control.finish_metrics_calculation()

    def get_window_candidates(self):
        candidates = set()
        file = None
        if self.metrics_list: # para evitar erros quando modelo ainda não tem métricas implementadas
            for m in self.metrics_list:
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
        if self.metrics_list: # para evitar erros quando modelo ainda não tem métricas implementadas
            for m in self.metrics_list:
                self.locks[m].acquire()
                file = open(self.filenames[m], "r")
                for line in file:
                    metric_read = loads(line, ignore_comments=True)
                    if metric_read.window == window:
                        metrics.append(metric_read)
                        break
                self.locks[m].release()
        return metrics
