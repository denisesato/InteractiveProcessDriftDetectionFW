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
from pm4py.objects.log.util import interval_lifecycle
from components.apply_window import AnalyzeDrift
from components.dfg_definitions import DfgDefinitions
from components.discovery.discovery_dfg import DiscoveryDfg
from components.evaluate.manage_evaluation_metrics import ManageEvaluationMetrics, EvaluationMetricList
from components.parameters import Approach, ReadLogAs
from components.pn_definitions import PnDefinitions
from components.discovery.discovery_pn import DiscoveryPn
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
        # self.total_of_windows = 0

    def restart_status(self):
        self.metrics_status = MetricsProcessingStatus.NOT_STARTED
        self.mining_status = IPDDProcessingStatus.NOT_STARTED

    # applied for CLI
    def finished_run(self):
        if self.metrics_manager is not None:
            result = self.tasks_completed >= 2  # for some reason sometimes it goes to 3 (maybe it is the TIMEOUT)
        else:
            result = self.tasks_completed >= 1
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

    def get_metrics_manager(self, activity=None):
        if activity:
            return self.metrics_manager[activity]
        return self.metrics_manager


class IPDDParameters:
    def __init__(self, logname, approach, read_log_as, metrics):
        self.logname = logname
        self.approach = approach
        self.read_log_as = read_log_as
        self.metrics = metrics
        self.session_id = None


class IPDDParametersFixed(IPDDParameters):
    def __init__(self, logname, approach, read_log_as, metrics, winunity, winsize):
        super().__init__(logname, approach, read_log_as, metrics)
        self.win_unity = winunity
        self.win_size = winsize


class IPDDParametersAdaptive(IPDDParameters):
    def __init__(self, logname, approach, read_log_as, metrics, attribute, delta=None):
        super().__init__(logname, approach, read_log_as, metrics)
        self.attribute = attribute
        self.delta = delta


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
        self.input_path = None
        self.models_path = None
        self.metrics_path = None
        self.script = False
        self.user_id = None
        self.model_type_definitions = None
        self.discovery = None
        self.script = script
        self.model_type = model_type
        self.total_of_windows = None
        self.windows_with_drifts = None
        self.initial_indexes = None
        self.activities = []
        self.all_activities = []
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
        self.logs_path = os.path.join('data', 'sublogs')
        self.metrics_path = os.path.join('data', 'metrics')
        self.adaptive_path = os.path.join('data', 'adaptive')

        # workaround for pygraphviz problem - the library do not release file handlers
        # in windows - this should be verified again
        # change the maximum number of open files
        import win32file as wfile
        wfile._setmaxstdio(4096)
        # print(f'NEW max open files: {[wfile._getmaxstdio()]}')

    # return the activities where a drift was detected in the last run
    def get_activities_with_drifts(self):
        return self.activities

    # return all the activities from the event log used on the last run
    def get_all_activities(self):
        return self.all_activities

    def get_approach(self):
        if self.current_parameters:
            return self.current_parameters.approach
        return None

    def get_first_activity(self):
        if len(self.activities) > 0:
            return self.activities[0]
        return ''

    def get_total_of_windows(self, activity=None):
        if self.total_of_windows and self.get_approach() == Approach.ADAPTIVE.name and activity and activity != '':
            return self.total_of_windows[activity]
        elif self.total_of_windows and self.get_approach() == Approach.FIXED.name:
            return self.total_of_windows
        else:
            return 0

    def get_implemented_metrics(self):
        return self.model_type_definitions.get_implemented_metrics()

    def get_default_metrics(self):
        return self.model_type_definitions.get_default_metrics()

    def get_implemented_evaluation_metrics(self):
        return [item for item in EvaluationMetricList]

    def get_input_path(self, user_id=''):
        return check_user_path(self.input_path, user_id)

    def get_models_path(self, user_id):
        return check_user_path(self.models_path, user_id)

    def get_metrics_path(self, user_id):
        return check_user_path(self.metrics_path, user_id)

    def get_logs_path(self, user_id):
        return check_user_path(self.logs_path, user_id)

    def get_adaptive_path(self, user_id):
        return check_user_path(self.adaptive_path, user_id)

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
            self.current_log.total_of_events = len(self.current_log.log)
            print(
                f'Log [{filename}] - total of cases [{self.current_log.total_of_cases}] - median case duration '
                f'[{self.current_log.median_case_duration / 60 / 60}hrs]')

            # convert to interval time log if needed
            # self.current_log.log = interval_lifecycle.to_interval(self.current_log.log)

    @threaded
    def run(self, parameters, user_id='script'):
        self.user_id = user_id
        if not self.script:
            # clean data generated from previous runs
            self.clean_generated_data(user_id)
        self.control.start_mining_calculation()

        # if the user is running from command line
        # first IPDD needs to copy the event log into the folder data\input
        # then, remove the original path
        if self.script:
            complete_filename = parameters.logname
            parameters.logname = self.copy_event_log(complete_filename)
            if parameters.logname is None:
                self.control.finish_mining_calculation()
                self.control.finish_metrics_calculation()
                return
            print(f'Importing event log: {parameters.logname}')
            # import the event log from the XES file and save it into self.current_log object
            # if the user is using the web interface, the log was imported by the app_preview_file
            self.import_log(complete_filename, parameters.logname)
        elif self.current_log is None:  # to prevent problems when user reload the process drift analysis page
            complete_filename = os.path.join(self.get_input_path(user_id), parameters.logname)

            print(f'Importing event log: {parameters.logname}')
            self.import_log(complete_filename, parameters.logname)

        # if metrics not defined, use default metrics for process model
        if not parameters.metrics:
            parameters.metrics = self.model_type_definitions.get_default_metrics()

        # initializing attributes that depend of the approach
        if parameters.approach == Approach.FIXED.name:
            self.windows_with_drifts = {}
            self.total_of_windows = {}
            self.outputpath_changepoints = os.path.join(self.get_adaptive_path(user_id),
                                                        self.current_parameters.logname,
                                                        f'delta{self.current_parameters.delta}')
        elif parameters.approach == Approach.ADAPTIVE.name:
            self.windows_with_drifts = None
            self.total_of_windows = 0
            # only working for ADWIN parameters, TODO make it generic
            # output_path for saving plots, attribute values, change points, and evaluation metrics
            self.outputpath_drifts = os.path.join(self.get_adaptive_path(user_id),
                                                        parameters.logname,
                                                        f'delta{parameters.delta}')
            if not os.path.exists(self.outputpath_drifts):
                os.makedirs(self.outputpath_drifts)

        else:
            print(f'Approach not identified in ippd_fw.run() {parameters.approach}')

        # set the parameters selected for the current run
        self.current_parameters = parameters
        self.discovery.set_current_parameters(parameters)
        self.control.reset_tasks_counter()
        print(f'User selected approach={parameters.approach} reading log as={parameters.read_log_as}')
        print(f'Metrics={parameters.metrics}')
        print(f'Starting windowing process...')
        analyze = AnalyzeDrift(self.model_type, parameters, self.control,
                               self.get_input_path(user_id), self.get_models_path(user_id),
                               self.get_metrics_path(user_id), self.get_logs_path(user_id),
                               self.current_log, self.discovery, user_id, self.outputpath_drifts)
        self.total_of_windows, self.initial_indexes, self.all_activities = analyze.start_drift_analysis()
        if parameters.approach == Approach.ADAPTIVE.name:
            self.activities = list(i for i in self.initial_indexes.keys() if len(self.initial_indexes[i].keys()) > 1)
            print(f'Setting the activities with drifts: {self.activities}')

        self.control.finish_mining_calculation()
        print(f'*** Initial indexes for generated windows: {self.initial_indexes}')
        print(f'*** Number of windows: [{self.total_of_windows}]')
        return self.total_of_windows

    def copy_event_log(self, event_log):
        path, log = os.path.split(event_log)
        new_filepath = os.path.join(self.get_input_path(self.user_id), log)
        print(f'Copying event log to input_folder: {new_filepath}')
        try:
            shutil.copyfile(event_log, new_filepath)
            print(f'Event log successfully copied {new_filepath}')
        except OSError as err:
            print(f'Error occurred while copying file. {err}')
            log = None
        except:
            print(f'Unknown error occurred while copying file.')
            log = None
        return log

    def get_number_of_items(self):
        # return the total of traces or events of the event log applied in the last run
        # according to the parameter Read log as selected by the user
        if self.current_parameters.read_log_as == ReadLogAs.TRACE.name:
            return self.current_log.total_of_cases
        elif self.current_parameters.read_log_as == ReadLogAs.EVENT.name:
            return self.current_log.total_of_events
        else:
            print(f'Parameter ReadLogAs not identified in ipdd_fw.get_number_of_items(): {self.current_parameters.read_log_as}')

    def evaluate(self, real_drifts, detected_drifts, error_tolerance, items, activity=None):
        manage_evaluation = ManageEvaluationMetrics(self.get_implemented_evaluation_metrics(), self.outputpath_drifts, activity)
        manage_evaluation.calculate_selected_evaluation_metrics(real_drifts, detected_drifts, error_tolerance, items)

    def get_initial_trace_indexes(self, activity=''):
        if self.initial_indexes:
            if activity:
                return list(self.initial_indexes[activity].keys())
            return list(self.initial_indexes.keys())
        return None

    def get_initial_trace_concept_names(self):
        return list(self.initial_indexes.values())

    def get_metrics_status(self):
        return self.control.get_metrics_status()

    def get_metrics_manager(self, activity=''):
        if self.get_approach() == Approach.ADAPTIVE.name and activity != '':
            return self.control.get_metrics_manager(activity)
        elif self.get_approach() == Approach.FIXED.name:
            return self.control.get_metrics_manager()
        else:
            print(f'No metrics manager instantiated...')
            return None

    def get_mining_status(self):
        return self.control.get_mining_status()

    def reset_mining_calculation(self):
        self.control.reset_mining_calculation()

    def reset_metrics_calculation(self):
        self.control.reset_metrics_calculation()

    def restart_status(self):
        self.control.restart_status()

    def get_model(self, original_filename, window, user, activity=''):
        return self.discovery.get_process_model(self.get_models_path(user), original_filename, window, activity)

    def get_activity_plot_src(self, user, activity, attribute):
        filename = os.path.join(self.get_adaptive_path(user), self.current_log.filename,
                                f'{activity}_{attribute}.png')
        return filename

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
        if self.get_metrics_status() == MetricsProcessingStatus.NOT_STARTED or self.get_metrics_status() == MetricsProcessingStatus.IDLE:
            self.status_similarity_metrics = ''
        if self.get_metrics_status() == MetricsProcessingStatus.RUNNING:
            self.status_similarity_metrics = 'Calculating similarity metrics...'
        if (self.get_metrics_status() == MetricsProcessingStatus.FINISHED
                or self.get_metrics_status() == MetricsProcessingStatus.TIMEOUT):
            if self.get_metrics_status() == MetricsProcessingStatus.FINISHED:
                self.status_similarity_metrics = f'Similarity metrics calculated.'
            elif self.get_metrics_status() == MetricsProcessingStatus.TIMEOUT:
                self.status_similarity_metrics = f'Similarity metrics TIMEOUT. Some metrics will not be presented...'
            self.reset_metrics_calculation()

        return self.status_similarity_metrics

    def get_drifts_info(self, activity=''):
        if self.get_approach() == Approach.ADAPTIVE.name and activity != '':
            return self.get_metrics_manager(activity).get_drifts_info()
        elif self.get_approach() == Approach.FIXED.name:
            return self.get_metrics_manager().get_drifts_info()
        else:
            print(f'Approach not identified {self.get_approach()} in self.get_approach()')
            return ()

    def clean_generated_data(self, user_id):
        # cleaning data from previous executions - only for web acess
        print(f'Cleaning files from previous run...')
        models_path = self.get_models_path(user_id)
        if os.path.exists(models_path):
            shutil.rmtree(models_path)
        logs_path = self.get_logs_path(user_id)
        if os.path.exists(logs_path):
            shutil.rmtree(logs_path)
        metrics_path = self.get_metrics_path(user_id)
        if os.path.exists(metrics_path):
            shutil.rmtree(metrics_path)
        adaptive_path = self.get_adaptive_path(user_id)
        if os.path.exists(adaptive_path):
            shutil.rmtree(adaptive_path)
