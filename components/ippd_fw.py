from components.apply_window import AnalyzeDrift
from components.discovery.discovery_dfg import get_dfg


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


class InteractiveProcessDriftDetectionFW:
    def __init__(self, pathname=''):
        self.control = Control()
        self.windows = 0
        self.windows_with_drifts = None
        self.status_mining = ''
        self.status_similarity_metrics = ''

    def run(self, event_log, win_type, win_unity, win_size):
        self.control.reset_tasks_counter()
        print(f'Usuário selecionou janela {win_type}-{win_unity} de tamanho {win_size} - arquivo {event_log}')
        self.control.start_metrics_calculation()
        self.control.start_mining_calculation()
        models = AnalyzeDrift(win_type, win_unity, win_size, event_log, self.control)
        self.windows = models.generate_models()
        self.control.finish_mining_calculation()
        print(f'Total de janelas geradas: [{self.windows}]')
        return self.windows

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

    @staticmethod
    def get_model(original_filename, window):
        return get_dfg(original_filename, window)

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