import os
import shutil

from components.apply_window import AnalyzeDrift
from components.discovery.discovery_dfg import DiscoveryDfg
from components.discovery.discovery_pn import DiscoveryPn
from components.evaluate.calculate_fscore import EvaluationMetric
from threading import Lock


class ProcessingStatus:
    NOT_STARTED = 'NOT_STARTED' # nenhuma execução realizada ainda
    IDLE = 'IDLE' # terminou a execução
    RUNNING = 'RUNNING' # em execução
    FINISHED = 'FINISHED'
    TIMEOUT = 'TIMEOUT'


class Control:
    def __init__(self):
        self.metrics_status = ProcessingStatus.NOT_STARTED
        self.mining_status = ProcessingStatus.NOT_STARTED
        self.metrics_manager = None
        self.tasks_completed = 0

    def finished_run(self):
        return self.tasks_completed == 2

    def reset_tasks_counter(self):
        self.tasks_completed = 0

    def finish_mining_calculation(self):
        self.mining_status = ProcessingStatus.FINISHED
        self.tasks_completed += 1

    def start_mining_calculation(self):
        self.mining_status = ProcessingStatus.RUNNING

    def reset_mining_calculation(self):
        self.mining_status = ProcessingStatus.IDLE

    def get_mining_status(self):
        return self.mining_status

    def finish_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.FINISHED
        self.tasks_completed += 1

    def start_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.RUNNING

    def reset_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.IDLE

    def time_out_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.TIMEOUT

    def get_metrics_status(self):
        return self.metrics_status

    def set_metrics_manager(self, metrics_manager):
        self.metrics_manager = metrics_manager

    def get_metrics_manager(self):
        return self.metrics_manager


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class InteractiveProcessDriftDetectionFW(metaclass=SingletonMeta):
    def __init__(self, script=False, model_type='dfg') -> None:
        self.control = Control()
        self.windows = 0
        self.initial_indexes = []
        self.windows_with_drifts = None
        self.status_mining = ''
        self.status_similarity_metrics = ''
        self.input_path = os.path.join('data', 'input')
        self.models_path = os.path.join('data', 'models')
        self.metrics_path = os.path.join('data', 'metrics')
        self.initialize_paths()
        self.script = script

        self.model_type = model_type
        if self.model_type == 'dfg':
            self.discovery = DiscoveryDfg()
        elif self.model_type == 'pn':
            self.discovery = DiscoveryPn()
        print(f'Initializing IPDD Framework: model [{self.model_type}]')

    def initialize_paths(self):
        print(f'Initializing paths used by IPDD Framework...')
        # Verifica se o diretório para salvar o event log existe, caso contrário cria
        if not os.path.exists(self.input_path):
            os.makedirs(self.input_path)

        # Verificar se o diretório para salvar os modelos existe, caso contrário cria
        if not os.path.exists(self.models_path):
            os.makedirs(self.models_path)

        # Verifica se o diretório para salvar as metricas existe, caso contrário cria
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

    def get_input_path(self):
        return self.input_path

    def get_models_path(self):
        return self.models_path

    def get_metrics_path(self):
        return self.metrics_path

    def run(self, event_log, win_type, win_unity, win_size):
        # se o usuário estiver rodando via linha de comando devemos primeiro copiar o event log
        # para o diretório de data\input e depois retirar o caminho original
        if self.script:
            event_log = self.copy_event_log(event_log)

        self.control.reset_tasks_counter()
        print(f'User selected window={win_type}-{win_unity} with size={win_size} - event log={event_log}')
        self.control.start_metrics_calculation()
        self.control.start_mining_calculation()
        models = AnalyzeDrift(self.model_type, win_type, win_unity, win_size, event_log, self.control,
                              self.input_path, self.models_path, self.metrics_path)
        self.windows, self.initial_indexes = models.generate_models()
        self.control.finish_mining_calculation()
        print(f'*** Initial indexes for generated windows: {self.initial_indexes}')
        print(f'*** Number of windows: [{self.windows}]')
        return self.windows

    def copy_event_log(self, event_log):
        path, log = os.path.split(event_log)
        new_filepath = os.path.join(self.input_path, log)
        print(f'Copying event log to input_folder: {new_filepath}')
        shutil.copyfile(event_log, new_filepath)
        return log

    def evaluate(self, windows_drifts, real_drifts, win_size):
        metric = EvaluationMetric(real_drifts, windows_drifts, win_size)
        return metric.calculate_fscore()

    def get_windows(self):
        return self.windows

    def get_initial_indexes(self):
        return list(self.initial_indexes.keys())

    def get_metrics_status(self):
        return self.control.get_metrics_status()

    def get_metrics_manager(self):
        return self.control.get_metrics_manager()

    def get_mining_status(self):
        return self.control.get_mining_status()

    def reset_mining_calculation(self):
        self.control.reset_mining_calculation()

    def reset_metrics_calculation(self):
        self.control.reset_metrics_calculation()

    def get_model(self, original_filename, window):
        return self.discovery.get_process_model(self.models_path, original_filename, window)

    # Método utilizado para verificar se uma execução do run encerrou
    # é utilizado somente para a interface via linha de comando
    def get_status_running(self):
        return self.control.finished_run()

    # Método utilizado para verificar o status do framework, que pode ser IDLE (após uma execução), RUNNING ou
    # NOT_STARTED (quando nenhuma execução foi realizada ainda)
    def get_status_framework(self):
        if self.get_mining_status() == ProcessingStatus.NOT_STARTED and self.get_metrics_status() == ProcessingStatus.NOT_STARTED:
            return ProcessingStatus.NOT_STARTED
        if self.get_mining_status() == ProcessingStatus.RUNNING or self.get_metrics_status() == ProcessingStatus.RUNNING:
            return ProcessingStatus.RUNNING
        else:
            return ProcessingStatus.IDLE

    def check_status_mining(self):
        if self.get_mining_status() == ProcessingStatus.FINISHED:
            self.reset_mining_calculation()
            self.status_mining = f'Finished to mine the process models.'
        elif self.get_mining_status() == ProcessingStatus.RUNNING:
            self.status_mining = f'Mining process models...'

        return self.status_mining

    def check_status_similarity_metrics(self):
        if self.get_metrics_status() == ProcessingStatus.RUNNING:
            self.status_similarity_metrics = 'Calculating similarity metrics...'
        # verifica se o cálculo de métricas terminou normalmente ou por timeout
        if (self.get_metrics_status() == ProcessingStatus.FINISHED
                or self.get_metrics_status() == ProcessingStatus.TIMEOUT)\
                and self.windows > 0:
            if self.get_metrics_status() == ProcessingStatus.FINISHED:
                self.status_similarity_metrics = f'Similarity metrics calculated.'
            elif self.get_metrics_status() == ProcessingStatus.TIMEOUT:
                self.status_similarity_metrics = f'Similarity metrics TIMEOUT. Some metrics will not be presented...'

            self.windows_with_drifts = self.get_metrics_manager().get_window_candidates()
            self.reset_metrics_calculation()

        return self.status_similarity_metrics, self.windows, self.windows_with_drifts

    def get_windows_candidates(self):
        return self.get_metrics_manager().get_window_candidates()