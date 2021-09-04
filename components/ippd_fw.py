"""
    This file is part of Interactive Process Drift (IPDD) Framework.
    IPDD is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    IPDD is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with IPDD. If not, see <https://www.gnu.org/licenses/>.
"""
import os
import shutil

from components.apply_window import AnalyzeDrift
from components.dfg_definitions import DfgDefinitions
from components.discovery.discovery_dfg import DiscoveryDfg
from components.pn_definitions import PnDefinitions
from components.discovery.discovery_pn import DiscoveryPn
from components.evaluate.calculate_fscore import EvaluationMetric
from threading import Thread
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.objects.log.obj import EventLog
from components.log_info import LogInfo


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class IPDDProcessingStatus:
    NOT_STARTED = 'NOT_STARTED'  # nothing started yet
    IDLE = 'IDLE'  # after finishing an execution, status is changed to idle
    RUNNING = 'RUNNING'  # executing mining or metrics
    FINISHED = 'FINISHED'  # finished mining


class MetricsProcessingStatus:
    NOT_STARTED = 'NOT_STARTED'
    RUNNING = 'RUNNING'
    IDLE = 'IDLE'  # after finishing an execution
    FINISHED = 'FINISHED'  # normally
    TIMEOUT = 'TIMEOUT'  # by timeout


class Control:
    def __init__(self):
        self.metrics_status = MetricsProcessingStatus.NOT_STARTED
        self.mining_status = IPDDProcessingStatus.NOT_STARTED
        self.metrics_manager = None
        self.tasks_completed = 0
        self.total_of_windows = 0

    def restart_status(self):
        self.metrics_status = MetricsProcessingStatus.NOT_STARTED
        self.mining_status = IPDDProcessingStatus.NOT_STARTED

    def finished_run(self):
        result = self.tasks_completed >= 2  # for some reason sometimes it goes to 3 (maybe it is the TIMEOUT)
        return result

    def reset_tasks_counter(self):
        self.tasks_completed = 0

    def finish_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.FINISHED
        self.tasks_completed += 1
        print(f'Finished mining calculation')

    def start_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.RUNNING

    def reset_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.IDLE

    def get_mining_status(self):
        return self.mining_status

    def finish_metrics_calculation(self):
        self.metrics_status = MetricsProcessingStatus.FINISHED
        self.tasks_completed += 1
        print(f'Finished metrics calculation')

    def start_metrics_calculation(self):
        self.metrics_status = MetricsProcessingStatus.RUNNING

    def reset_metrics_calculation(self):
        self.metrics_status = MetricsProcessingStatus.IDLE

    def time_out_metrics_calculation(self):
        self.metrics_status = MetricsProcessingStatus.TIMEOUT

    def get_metrics_status(self):
        return self.metrics_status

    def set_metrics_manager(self, metrics_manager):
        self.metrics_manager = metrics_manager

    def get_metrics_manager(self):
        return self.metrics_manager


class IPDDParameters:
    def __init__(self, logname, wintype, winunity, winsize, metrics):
        self.logname = logname
        self.wintype = wintype
        self.winunity = winunity
        self.winsize = winsize
        self.metrics = metrics
        self.session_id = None


def check_user_path(generic_path, user_id):
    path = os.path.join(generic_path, user_id)
    if not os.path.exists(path):
        print(f'Creating path {generic_path} for user {user_id}')
        os.makedirs(path)
    return path


class InteractiveProcessDriftDetectionFW:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not InteractiveProcessDriftDetectionFW.__instance:
            InteractiveProcessDriftDetectionFW.__instance = object.__new__(cls)
        return InteractiveProcessDriftDetectionFW.__instance

    def __init__(self, script=False, model_type='dfg'):
        mode = 'web interface'
        if script:
            mode = 'command line interface'
        print(f'Initializing IPDD Framework: model type [{model_type}] - [{mode}]')
        self.MAX_TRACES = 20
        self.current_log = None
        self.current_parameters = None
        self.status_similarity_metrics = ''
        self.status_mining = ''
        self.control = Control()
        self.windows_with_drifts = None
        self.initial_indexes = []
        self.total_of_windows = 0
        self.input_path = None
        self.models_path = None
        self.metrics_path = None
        self.script = False
        self.user_id = None
        self.model_type_definitions = None
        self.discovery = None
        self.script = script
        self.model_type = model_type
        # mine the process model and save it
        if self.model_type == 'dfg':
            self.discovery = DiscoveryDfg()
            self.model_type_definitions = DfgDefinitions()
        elif self.model_type == 'pn':
            self.discovery = DiscoveryPn()
            self.model_type_definitions = PnDefinitions()
        else:
            print(f'Model type not implemented {self.model_type}')
        self.input_path = os.path.join('data', 'input')
        self.models_path = os.path.join('data', 'models')
        self.metrics_path = os.path.join('data', 'metrics')
        self.initialize_paths()

    def initialize_paths(self):
        # verify if the folder for saving the events logs exist, if not create it
        if not os.path.exists(self.input_path):
            os.makedirs(self.input_path)
        # verify if the folder for saving the process models exist, if not create it
        if not os.path.exists(self.models_path):
            os.makedirs(self.models_path)
        # verify if the folder for saving the metrics exist, if not create it
        if not os.path.exists(self.metrics_path):
            os.makedirs(self.metrics_path)

    def get_implemented_metrics(self):
        return self.model_type_definitions.get_implemented_metrics()

    def get_default_metrics(self):
        return self.model_type_definitions.get_default_metrics()

    def get_input_path(self, user_id):
        return check_user_path(self.input_path, user_id)

    def get_models_path(self, user_id):
        return check_user_path(self.models_path, user_id)

    def get_metrics_path(self, user_id):
        return check_user_path(self.metrics_path, user_id)

    def import_log(self, complete_filename, filename):
        # import the chosen event log and calculate some statistics
        self.current_log = LogInfo(complete_filename, filename)
        if '.xes' in complete_filename:
            # Assume that it is a XES file
            variant = xes_importer.Variants.ITERPARSE
            parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
            self.current_log.log = xes_importer.apply(complete_filename, variant=variant, parameters=parameters)
            self.current_log.first_traces = log_converter.apply(EventLog(self.current_log.log[0:self.MAX_TRACES]),
                                                                variant=log_converter.Variants.TO_DATA_FRAME)

            self.current_log.median_case_duration = case_statistics.get_median_caseduration(self.current_log.log,
                                                                                            parameters={
                                                                                                case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
            self.current_log.median_case_duration_in_hours = self.current_log.median_case_duration / 60 / 60
            self.current_log.total_of_cases = len(self.current_log.log)
            print(
                f'Log [{filename}] - total of cases [{self.current_log.total_of_cases}] - median case duration '
                f'[{self.current_log.median_case_duration / 60 / 60}hrs]')

    @threaded
    def run(self, event_log, win_type, win_unity, win_size, metrics=None, user_id='script'):
        self.user_id = user_id
        if not self.script:
            # clean data generated from previous runs
            self.clean_generated_data(user_id)
        self.control.start_mining_calculation()
        self.total_of_windows = 0

        # if the user is running from command line
        # first IPDD needs to copy the event log into the folder data\input
        # then, remove the original path
        if self.script:
            complete_filename = event_log
            event_log = self.copy_event_log(complete_filename)
            print(f'Importing event log: {event_log}')
            # import the event log from the XES file and save it into self.current_log object
            # if the user is using the web interface, the log was imported by the app_preview_file
            self.import_log(complete_filename, event_log)
        elif self.current_log is None:  # to prevent problems when user reload the process drift analysis page
            complete_filename = os.path.join(self.get_input_path(user_id), event_log)
            print(f'Importing event log: {event_log}')
            self.import_log(complete_filename, event_log)

        # if metrics not defined, use default metrics for process model
        if not metrics:
            metrics = self.model_type_definitions.get_default_metrics()

        # set the parameters selected for the current run
        self.current_parameters = IPDDParameters(event_log, win_type, win_unity, win_size, metrics)
        self.discovery.set_current_parameters(self.current_parameters)

        self.control.reset_tasks_counter()
        print(f'User selected window={win_type}-{win_unity} with size={win_size}')
        print(f'Metrics={metrics}')
        print(f'Starting windowing process...')
        models = AnalyzeDrift(self.model_type, self.current_parameters, self.control,
                              self.get_input_path(user_id), self.get_models_path(user_id),
                              self.get_metrics_path(user_id), self.current_log, self.discovery)
        self.total_of_windows, self.initial_indexes = models.generate_models()
        self.control.finish_mining_calculation()
        print(f'*** Initial indexes for generated windows: {self.initial_indexes}')
        print(f'*** Number of windows: [{self.total_of_windows}]')
        return self.total_of_windows

    def copy_event_log(self, event_log):
        path, log = os.path.split(event_log)
        new_filepath = os.path.join(self.get_input_path(self.user_id), log)
        print(f'Copying event log to input_folder: {new_filepath}')
        shutil.copyfile(event_log, new_filepath)
        return log

    def evaluate(self, windows_drifts, real_drifts, win_size):
        metric = EvaluationMetric(real_drifts, windows_drifts, win_size)
        return metric.calculate_fscore()

    def get_windows(self):
        return self.total_of_windows

    def get_initial_trace_indexes(self):
        return list(self.initial_indexes.keys())

    def get_initial_trace_concept_names(self):
        return list(self.initial_indexes.values())

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

    def restart_status(self):
        self.control.restart_status()

    def get_model(self, original_filename, window, user):
        return self.discovery.get_process_model(self.get_models_path(user), original_filename, window)

    # method that verify if one execution of IPDD finished running
    # used by the command line interface
    def get_status_running(self):
        return not self.control.finished_run()

    # method that returns the status of IPDD
    # used by the web interface
    def get_status_framework(self):
        if self.get_mining_status() == IPDDProcessingStatus.NOT_STARTED:
            return IPDDProcessingStatus.NOT_STARTED
        if self.get_mining_status() == IPDDProcessingStatus.RUNNING or \
                self.get_metrics_status() == IPDDProcessingStatus.RUNNING:
            return IPDDProcessingStatus.RUNNING
        else:
            return IPDDProcessingStatus.IDLE

    def get_status_mining_text(self):
        if self.get_mining_status() == IPDDProcessingStatus.IDLE:
            self.status_mining = f'Finished to mine the process models.'
        if self.get_mining_status() == IPDDProcessingStatus.NOT_STARTED:
            self.status_mining = f'Mining not started.'
        if self.get_mining_status() == IPDDProcessingStatus.FINISHED:
            self.reset_mining_calculation()
            self.status_mining = f'Finished to mine the process models.'
        elif self.get_mining_status() == IPDDProcessingStatus.RUNNING:
            self.status_mining = f'Mining process models...'

        return self.status_mining

    def get_status_similarity_metrics_text(self):
        if self.get_metrics_status() == MetricsProcessingStatus.NOT_STARTED:
            self.status_similarity_metrics = ''
        if self.get_metrics_status() == MetricsProcessingStatus.RUNNING:
            self.status_similarity_metrics = 'Calculating similarity metrics...'
        # check if the metrics' calculation finished by timeout
        # and correctly define the status message for the web interface
        if (self.get_metrics_status() == MetricsProcessingStatus.FINISHED
            or self.get_metrics_status() == MetricsProcessingStatus.TIMEOUT) \
                and self.total_of_windows > 0:
            if self.get_metrics_status() == MetricsProcessingStatus.FINISHED:
                self.status_similarity_metrics = f'Similarity metrics calculated.'
            elif self.get_metrics_status() == MetricsProcessingStatus.TIMEOUT:
                self.status_similarity_metrics = f'Similarity metrics TIMEOUT. Some metrics will not be presented...'

            self.windows_with_drifts = self.get_metrics_manager().get_window_candidates()
            self.reset_metrics_calculation()

        return self.status_similarity_metrics, self.total_of_windows, self.windows_with_drifts

    def get_windows_candidates(self):
        return self.get_metrics_manager().get_window_candidates()

    def clean_generated_data(self, user_id):
        # cleaning data from previous executions - only for web acess
        print(f'Cleaning files from previous run...')
        models_path = self.get_models_path(user_id)
        if os.path.exists(models_path):
            shutil.rmtree(models_path)

        metrics_path = self.get_metrics_path(user_id)
        if os.path.exists(metrics_path):
            shutil.rmtree(metrics_path)
