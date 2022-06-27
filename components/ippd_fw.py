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
from components.evaluate.manage_evaluation_metrics import ManageEvaluationMetrics, EvaluationMetricList
from components.parameters import Approach, ReadLogAs, AdaptivePerspective, get_value_of_parameter
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

    def restart_status(self):
        self.metrics_status = MetricsProcessingStatus.NOT_STARTED
        self.mining_status = IPDDProcessingStatus.NOT_STARTED

    # applied for CLI
    def finished_run(self):
        if self.metrics_manager is not None:
            result = (self.metrics_status == MetricsProcessingStatus.FINISHED or \
                      self.metrics_status == MetricsProcessingStatus.IDLE) and \
                     self.mining_status == IPDDProcessingStatus.FINISHED
        else:
            result = self.mining_status == IPDDProcessingStatus.FINISHED
        return result

    def finish_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.FINISHED
        print(f'Finished mining calculation')

    def start_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.RUNNING

    def reset_mining_calculation(self):
        self.mining_status = IPDDProcessingStatus.IDLE

    def get_mining_status(self):
        return self.mining_status

    def finish_metrics_calculation(self):
        self.metrics_status = MetricsProcessingStatus.FINISHED
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

    def print(self):
        print(f'----- IPDD general parameters -----')
        print(f'Logname: {self.logname}')
        print(f'Approach: {self.approach}')
        print(f'Read log as: {self.read_log_as}')
        print(f'Similarity metrics: {self.metrics}')


class IPDDParametersFixed(IPDDParameters):
    def __init__(self, logname, approach, read_log_as, metrics, winunity, winsize):
        super().__init__(logname, approach, read_log_as, metrics)
        self.win_unity = winunity
        self.win_size = winsize

    def print(self):
        super().print()
        print(f'----- IPDD fixed window for control-flow drifts - parameters -----')
        print(f'Read log as: {self.win_unity}')
        print(f'Window size: {self.win_size}')


class IPDDParametersAdaptive(IPDDParameters):
    def __init__(self, logname, approach, perspective, read_log_as, metrics, attribute,
                 attribute_name=None, activities=[], delta=None):
        super().__init__(logname, approach, read_log_as, metrics)
        self.perspective = perspective
        self.attribute = attribute
        self.attribute_name = attribute_name
        self.activities = activities
        if delta:
            self.delta = delta
        else:  # default value
            self.delta = 0.002

    def print(self):
        super().print()
        print(f'----- Adaptive IPDD for time and data drifts - parameters ----- ')
        print(f'Perspective: {self.perspective}')
        print(f'Attribute name: {self.attribute_name}')
        print(f'Attribute: {self.attribute}')
        print(f'Activities: {self.activities}')
        print(f'ADWIN delta: {self.delta}')


class IPDDParametersAdaptiveControlflow(IPDDParameters):
    def __init__(self, logname, approach, perspective, read_log_as, win_size, metrics,
                 adaptive_controlflow_approach, delta=None, save_sublogs=False):
        super().__init__(logname, approach, read_log_as, metrics)
        self.win_size = win_size
        self.perspective = perspective
        self.adaptive_controlflow_approach = adaptive_controlflow_approach
        if delta:
            self.delta = delta
        else:  # default value
            self.delta = 0.002
        self.save_sublogs = save_sublogs

    def print(self):
        super().print()
        print(f'----- Adaptive IPDD for control-flow drifts - parameters -----')
        print(f'Perspective: {self.perspective}')
        print(f'Approach: {self.adaptive_controlflow_approach}')
        print(f'Window size: {self.win_size}')
        print(f'ADWIN delta: {self.delta}')


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class InteractiveProcessDriftDetectionFW(metaclass=SingletonMeta):
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
        self.script = False
        self.user_id = None
        self.model_type_definitions = None
        self.discovery = None
        self.script = script
        self.model_type = model_type
        self.total_of_windows = None
        self.windows_with_drifts = None
        self.initial_indexes = None
        self.analyze = None
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
        self.manage_evaluation = None  # evaluation module

        # paths for saving the results
        self.data_path = 'data'
        self.output_path = 'output'
        self.input_path = 'input'
        self.models_path = 'models'
        self.similarity_metrics_path = 'similarity_metrics'
        self.logs_path = 'sublogs'
        self.adaptive_path = 'adaptive'
        self.evaluation_path = 'evaluation'

    def check_user_path(self, generic_path, user_id, output=True):
        if output:
            path = os.path.join(self.data_path, self.output_path, user_id, generic_path)
        else:
            path = os.path.join(self.data_path, generic_path, user_id)

        if not os.path.exists(path):
            print(f'Creating path "{generic_path}" for user {user_id}')
            os.makedirs(path)
        return path

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

    def get_adaptive_perpective(self):
        if self.current_parameters:
            return self.current_parameters.perspective
        return None

    def get_first_activity(self):
        if len(self.activities) > 0:
            return self.activities[0]
        return ''

    def get_total_of_windows(self, activity=None):
        if self.total_of_windows and self.get_approach() == Approach.ADAPTIVE.name and \
                self.get_adaptive_perpective() == AdaptivePerspective.TIME_DATA.name and activity and activity != '':
            return self.total_of_windows[activity]
        elif self.total_of_windows and (self.get_approach() == Approach.FIXED.name or
                                        (self.get_approach() == Approach.ADAPTIVE.name and
                                         self.get_adaptive_perpective() == AdaptivePerspective.CONTROL_FLOW.name)):
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
        path = self.check_user_path(self.input_path, user_id, False)
        # print(f'get_input_path: {path}')
        return path

    def get_models_path(self, user_id):
        return self.check_user_path(self.models_path, user_id)

    def get_similarity_metrics_path(self, user_id):
        return self.check_user_path(self.similarity_metrics_path, user_id)

    def get_adaptive_logs_path(self, user_id):
        path = os.path.join(self.adaptive_path, self.current_parameters.logname,
                            f'{self.current_parameters.perspective}'
                            f'_{self.current_parameters.adaptive_controlflow_approach}'
                            f'_win{self.current_parameters.win_size}'
                            f'_delta{self.current_parameters.delta}', self.logs_path)
        return self.check_user_path(path, user_id)

    def get_evaluation_path(self, user_id):
        return self.check_user_path(self.evaluation_path, user_id)

    def get_adaptive_path(self, user_id):
        return self.check_user_path(self.adaptive_path, user_id)

    def get_adaptive_adwin_path(self, user_id):
        path = os.path.join(self.adaptive_path, self.current_parameters.logname)
        if self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            path = os.path.join(self.adaptive_path, self.current_parameters.logname,
                                f'{self.current_parameters.perspective}'
                                f'_{self.current_parameters.attribute}'
                                f'_delta{self.current_parameters.delta}')
        elif self.current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            path = os.path.join(self.adaptive_path, self.current_parameters.logname,
                                f'{self.current_parameters.perspective}'
                                f'_{self.current_parameters.adaptive_controlflow_approach}'
                                f'_win{self.current_parameters.win_size}'
                                f'_delta{self.current_parameters.delta}')
        else:
            print(f'Incorrect adaptive perspective, using default path for evaluation: {path}')
        return self.check_user_path(path, user_id)

    def get_adaptive_evaluation_path(self, user_id):
        path = os.path.join(self.get_evaluation_path(user_id),
                            self.current_parameters.logname)
        if self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            path = os.path.join(self.get_evaluation_path(user_id),
                                self.current_parameters.logname,
                                f'{self.current_parameters.approach}'
                                f'_{self.current_parameters.perspective}'
                                f'_{self.current_parameters.attribute}'
                                f'_delta{self.current_parameters.delta}')
        elif self.current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            path = os.path.join(self.get_evaluation_path(user_id),
                                self.current_parameters.logname,
                                f'{self.current_parameters.approach}'
                                f'_{self.current_parameters.perspective}'
                                f'_w{self.current_parameters.win_size}'
                                f'_delta{self.current_parameters.delta}')
        else:
            print(f'Incorrect adaptive perspective, using default path for evaluation: {path}')
        return path

    def get_adaptive_adwin_models_path(self, user_id):
        path = os.path.join(self.adaptive_path, self.current_parameters.logname,
                            f'{self.current_parameters.perspective}'
                            f'_{self.current_parameters.adaptive_controlflow_approach}'
                            f'_win{self.current_parameters.win_size}'
                            f'_delta{self.current_parameters.delta}', self.models_path)
        return self.check_user_path(path, user_id)

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

    def get_running_percentage(self):
        if not self.analyze or not self.current_log:
            p = 0
        else:
            p = float(self.analyze.current_trace) / float(self.current_log.total_of_cases) * 100.0
            # print(f'get_running_percentage: {self.analyze.current_trace} - {p}')
        return p

    @threaded
    def run_web(self, parameters, user_id):
        self.run(parameters, user_id)

    def run_script(self, parameters):
        self.run(parameters, 'script')

    def run(self, parameters, user_id='script'):
        # reset information about windows
        self.initial_indexes = None
        # set the parameters selected for the current run
        self.current_parameters = parameters
        self.discovery.set_current_parameters(parameters)
        self.current_parameters.print()
        self.user_id = user_id
        if not self.script:
            # clean data generated from previous runs
            self.clean_generated_data(user_id)
        self.control.start_mining_calculation()
        self.control.reset_metrics_calculation()

        # if the user is running from command line
        # first IPDD needs to copy the event log into the folder data\input
        # then, remove the original path
        if self.script:
            complete_filename = parameters.logname
            self.current_parameters.logname = self.copy_event_log(complete_filename)
            if self.current_parameters.logname is None:
                self.control.finish_mining_calculation()
                self.control.finish_metrics_calculation()
                return
            print(f'Importing event log: {self.current_parameters.logname}')
            # import the event log from the XES file and save it into self.current_log object
            # if the user is using the web interface, the log was imported by the app_preview_file
            self.import_log(complete_filename, self.current_parameters.logname)
        elif self.current_log is None:  # to prevent problems when user reload the process drift analysis page
            complete_filename = os.path.join(self.get_input_path(user_id), self.current_parameters.logname)

            print(f'Importing event log: {self.current_parameters.logname}')
            self.import_log(complete_filename, self.current_parameters.logname)

        # if metrics not defined, use default metrics for process model
        if not self.current_parameters.metrics:
            self.current_parameters.metrics = self.model_type_definitions.get_default_metrics()

        # initializing attributes that depend of the approach
        outputpath_adaptive_sublogs = ''
        outputpath_adaptive_adwin = ''
        outputpath_adaptive_adwin_models = ''
        if self.current_parameters.approach == Approach.FIXED.name:
            self.windows_with_drifts = {}
            self.total_of_windows = {}

        elif self.current_parameters.approach == Approach.ADAPTIVE.name:
            self.windows_with_drifts = None
            self.total_of_windows = 0
            # ADWIN adaptive path
            # output_path for saving plots, attribute values, drift, and evaluation metrics
            outputpath_adaptive_adwin = self.get_adaptive_adwin_path(user_id)
            if self.current_parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
                outputpath_adaptive_adwin_models = self.get_adaptive_adwin_models_path(user_id)
                outputpath_adaptive_sublogs = self.get_adaptive_logs_path(user_id)
        else:
            print(f'Approach not identified in ippd_fw.run() {parameters.approach}')

        evaluation_path = self.get_evaluation_path(user_id)
        # initialize evaluation module
        self.manage_evaluation = ManageEvaluationMetrics(self.get_implemented_evaluation_metrics(),
                                                         evaluation_path, self.current_parameters)

        print(
            f'User selected approach={self.current_parameters.approach} reading log as={self.current_parameters.read_log_as}')
        print(f'Metrics={self.current_parameters.metrics}')
        print(f'Starting windowing process...')
        self.analyze = AnalyzeDrift(self.model_type, self.current_parameters, self.control,
                               self.get_input_path(user_id), self.get_models_path(user_id),
                               self.get_similarity_metrics_path(user_id), outputpath_adaptive_sublogs,
                               self.current_log, self.discovery, user_id,
                               outputpath_adaptive_adwin, outputpath_adaptive_adwin_models)
        self.total_of_windows, self.initial_indexes, self.all_activities = self.analyze.start_drift_analysis()
        if self.current_parameters.approach == Approach.ADAPTIVE.name and \
                self.current_parameters.perspective == AdaptivePerspective.TIME_DATA.name:
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
            print(
                f'Parameter ReadLogAs not identified in ipdd_fw.get_number_of_items(): {self.current_parameters.read_log_as}')

    def evaluate(self, real_drifts, detected_drifts, items, activity=None):
        return self.manage_evaluation.calculate_selected_evaluation_metrics(real_drifts, detected_drifts,
                                                                            items, activity)

    def get_initial_trace_indexes(self, activity=''):
        if self.initial_indexes:
            if activity != '':
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
        elif self.get_approach() == Approach.ADAPTIVE.name and \
                self.get_adaptive_perpective() == AdaptivePerspective.CONTROL_FLOW.name:
            return self.control.get_metrics_manager()
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

    def get_activity_plot_src(self, user, activity):
        filename = os.path.join(self.get_adaptive_adwin_path(user),
                                f'{activity}.png')
        return filename

    def get_adaptive_plot_src(self, user):
        path = self.get_adaptive_adwin_path(user)
        filename = os.path.join(path, f'adaptive_controlflow_metrics.png')
        return filename

    # method that verify if one execution of IPDD finished running
    # used by the command line interface
    def get_status_running(self):
        return not self.control.finished_run()

    # method that returns the status of IPDD
    # used by the web interface
    def get_status_framework(self):
        if self.get_mining_status() == IPDDProcessingStatus.NOT_STARTED:
            # print(f'get_status_framework IPDDProcessingStatus.NOT_STARTED')
            return IPDDProcessingStatus.NOT_STARTED
        if self.get_mining_status() == IPDDProcessingStatus.RUNNING or \
                self.get_metrics_status() == IPDDProcessingStatus.RUNNING:
            # print(f'get_status_framework IPDDProcessingStatus.RUNNING')
            return IPDDProcessingStatus.RUNNING
        else:
            # print(f'get_status_framework IPDDProcessingStatus.IDLE')
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

    def get_windows_with_drifts(self, activity=''):
        if self.get_metrics_manager():
            if self.get_approach() == Approach.FIXED.name:
                return self.get_metrics_manager().get_drifts_info()
            elif self.get_approach() == Approach.ADAPTIVE.name:
                if self.get_adaptive_perpective() == AdaptivePerspective.TIME_DATA.name:
                    windows, traces = self.get_metrics_manager().get_drifts_info(activity)
                    return windows, self.get_initial_trace_indexes(activity)[1:]
                else:
                    windows, traces = self.get_metrics_manager().get_drifts_info()
                    return windows, self.get_initial_trace_indexes()[1:]
            else:
                print(f'Approach not identified {self.get_approach()} in self.get_approach()')
                return [], []
        else:
            print(f'Metrics manager not instantiated')
            return [], []


    def clean_generated_data(self, user_id):
        # cleaning data from previous executions - only for web acess
        print(f'Cleaning files from previous run...')
        models_path = self.get_models_path(user_id)
        if os.path.exists(models_path):
            shutil.rmtree(models_path)
        metrics_path = self.get_similarity_metrics_path(user_id)
        if os.path.exists(metrics_path):
            shutil.rmtree(metrics_path)
        adaptive_path = self.get_adaptive_path(user_id)
        if os.path.exists(adaptive_path):
            shutil.rmtree(adaptive_path)
        evaluation_path = self.get_evaluation_path(user_id)
        if os.path.exists(evaluation_path):
            shutil.rmtree(evaluation_path)
