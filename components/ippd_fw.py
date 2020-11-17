import os
import shutil

from components.apply_window import AnalyzeDrift
from components.discovery.discovery_dfg import get_dfg
from threading import Lock
from pathlib import Path


class ProcessingStatus:
    NOT_STARTED = 'NOT_STARTED'
    IDLE = 'IDLE'
    STARTED = 'STARTED'
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
        self.mining_status = ProcessingStatus.STARTED

    def reset_mining_calculation(self):
        self.mining_status = ProcessingStatus.IDLE

    def get_mining_status(self):
        return self.mining_status

    def finish_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.FINISHED
        self.tasks_completed += 1

    def start_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.STARTED

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
    def __init__(self, script=False) -> None:
        self.control = Control()
        self.windows = 0
        self.windows_with_drifts = None
        self.status_mining = ''
        self.status_similarity_metrics = ''
        self.script = script
        self.input_path = os.path.join('data', 'input')
        self.models_path = os.path.join('data', 'models')
        self.metrics_path = os.path.join('data', 'metrics')
        self.initialize_paths()

    def initialize_paths(self):
        print('Initializing paths used by IPDD Framework...')
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
        models = AnalyzeDrift(win_type, win_unity, win_size, event_log, self.control,
                              self.input_path, self.models_path, self.metrics_path)
        self.windows = models.generate_models()
        self.control.finish_mining_calculation()
        print(f'Windows generated: [{self.windows}]')
        return self.windows

    def copy_event_log(self, event_log):
        path, log = os.path.split(event_log)
        new_filepath = os.path.join(self.input_path, log)
        print(f'Copying event log to input_folder: {new_filepath}')
        shutil.copyfile(event_log, new_filepath)
        return log

    def get_windows(self):
        return self.windows

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
        return get_dfg(self.models_path, original_filename, window)

    def get_status_running(self):
        return self.control.finished_run()

    def check_status_mining(self):
        if self.get_mining_status() == ProcessingStatus.FINISHED:
            self.reset_mining_calculation()
            self.status_mining = f'Finished to mine the process models.'
        elif self.get_mining_status() == ProcessingStatus.STARTED:
            self.status_mining = f'Mining process models...'

        return self.status_mining

    def check_status_similarity_metrics(self):
        if self.get_metrics_status() == ProcessingStatus.STARTED:
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