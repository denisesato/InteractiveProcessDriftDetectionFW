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
import math

from components.adaptive.detectors import SelectDetector, ConceptDriftDetector

"""
For running IPDD massively, the user must define the dataset configuration:

1) For control-flow perspective analysis, create a class using the template
below for defining the scenarios information:

class DatasetSampleConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'dataset1'
    input_folder = '/IPDD_Datasets/dataset1'
    lognames = ['cb2.5k.xes', cd5k.xes]
    windows = [25, 50]
    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.HDDM_W.name, parameters={'two_sided_test': True})
    ]

    ###############################################################
    # Information for calculating evaluation metrics
    # The information about change points and number of instances
    # is only requested when defining option evaluate=True
    ###############################################################
    actual_change_points = {
        '2.5k': define_change_points_dataset1(250),
        '5k': define_change_points_dataset1(500),
    }

    number_of_instances = {
        '2.5k': 2500,
        '5k': 5000,
    } 
    
2) For data perspective analysis, create a class using the template
below for defining the scenarios information:

class DatasetSampleConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_folder = '/IPDD_Datasets/dataset1'
    lognames = ['cb2.5k.xes', cd5k.xes]
    deltas = [0.002, 0.05]
    attribute_name = 'Attribute Name'
"""

import os
import time
import pandas as pd
import re

from components.evaluate.manage_evaluation_metrics import EvaluationMetricList
from components.parameters import ReadLogAs, WindowUnityFixed, Approach, AttributeAdaptive, AdaptivePerspective, \
    ControlflowAdaptiveApproach
from components.ippd_fw import InteractiveProcessDriftDetectionFW, IPDDParametersFixed, IPDDParametersAdaptive, \
    IPDDParametersAdaptiveControlflow

DRIFTS_KEY = 'drifts - '
DETECTED_AT_KEY = 'detected at - '
ACTIVITY_KEY = 'activity'
DETECTOR_KEY = 'detector'


def run_massive_adaptive_data(dataset_config, metrics=None):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    read_log_as = ReadLogAs.TRACE.name
    if hasattr(dataset_config, "ordered_by_event"):
        read_log_as = ReadLogAs.EVENT.name

    dict_results = {}
    for log in dataset_config.lognames:
        dict_results[log] = {}
        for d in dataset_config.deltas:
            for at in dataset_config.attribute_names:
                print('----------------------------------------------')
                print(f'Running new scenario')
                print(f'Approach: {Approach.ADAPTIVE.value}')
                print(f'Metrics: {[m.value for m in metrics]}')
                print(f'Event log: {log}')
                print('----------------------------------------------')
                log_filename = os.path.join(dataset_config.input_path, log)

                # parameter for define activities
                activities = []
                if hasattr(dataset_config, "activities"):
                    activities = dataset_config.activities

                # parameters for customizing information inside the plots_thesis
                activities_for_plot = None
                if hasattr(dataset_config, "activities_for_plot"):
                    activities_for_plot = dataset_config.activities_for_plot

                attribute_name_for_plot = None
                if hasattr(dataset_config, "attribute_name_for_plot"):
                    attribute_name_for_plot = dataset_config.attribute_name_for_plot

                parameters = IPDDParametersAdaptive(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                    perspective=AdaptivePerspective.TIME_DATA.name,
                                                    read_log_as=read_log_as, metrics=metrics,
                                                    attribute=AttributeAdaptive.OTHER.name,
                                                    attribute_name=at, delta=d,
                                                    activities_for_plot=activities_for_plot,
                                                    attribute_name_for_plot=attribute_name_for_plot,
                                                    activities=activities)
                framework.run_script(parameters)

                running = framework.get_status_running()
                while running:
                    print(f'Waiting for IPDD finishes ... Status running: {running}')
                    time.sleep(2)  # in seconds
                    running = framework.get_status_running()
                print(f'Adaptive IPDD finished drift analysis on the data perspective')
                detected_drifts = {}
                # get the activities that report a drift using the change detector
                for activity in framework.get_activities_with_drifts():
                    indexes = framework.get_initial_trace_indexes(activity)
                    detected_drifts[activity] = indexes[1:]
                    print(
                        f'Adaptive IPDD detect drifts for attribute {AttributeAdaptive.OTHER.name}-{at} in activity {activity} in indexes {detected_drifts}')
                    # get information about control-flow metrics
                    windows, traces = framework.get_windows_with_drifts(activity)
                    if len(traces) > 0:
                        print(
                            f'IPDD detect control-flow drift for activity {activity} in windows {windows} - traces {traces}')

                out_filename = os.path.join(framework.get_evaluation_path('script'), f'{dataset_config.dataset_name}_results_IPDD_{Approach.ADAPTIVE.name}_'
                                                                                     f'{AdaptivePerspective.TIME_DATA.name}_'
                                                                                     f'{AttributeAdaptive.OTHER.name}-'
                                                                                     f'{at}.xlsx')
                df = pd.DataFrame.from_dict(dict_results, orient='index')
                df.to_excel(out_filename)


def run_massive_adaptive_time(dataset_config, metrics=None, evaluate=False):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    read_log_as = ReadLogAs.TRACE.name
    if hasattr(dataset_config, "ordered_by_event"):
        read_log_as = ReadLogAs.EVENT.name

    dict_results = {}
    for log in dataset_config.lognames:
        dict_results[log] = {}
        for delta in dataset_config.deltas:

            print('----------------------------------------------')
            print(f'Running new scenario')
            print(f'Approach: {Approach.ADAPTIVE.value}')
            print(f'Metrics: {[m.value for m in metrics]}')
            print(f'Attribute: {dataset_config.attribute}')
            print(f'Attribute name: {dataset_config.attribute_name}')
            attribute_name_for_plot = None
            if hasattr(dataset_config, "attribute_name_for_plot"):
                attribute_name_for_plot = dataset_config.attribute_name_for_plot
                print(f'Attribute name: {attribute_name_for_plot}')
            activities = []
            if hasattr(dataset_config, "activities"):
                activities = dataset_config.activities
                print(f'Activities: {activities}')
            activities_for_plot = None
            if hasattr(dataset_config, "activities_for_plot"):
                activities_for_plot = dataset_config.activities_for_plot
                print(f'Activities for plot: {activities_for_plot}')
            print(f'Event log: {log}')
            print('----------------------------------------------')
            log_filename = os.path.join(dataset_config.input_path, log)
            detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name,
                                                                  {'delta': delta})
            parameters = IPDDParametersAdaptive(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                perspective=AdaptivePerspective.TIME_DATA.name,
                                                read_log_as=read_log_as, metrics=metrics,
                                                attribute=dataset_config.attribute,
                                                attribute_name=dataset_config.attribute_name,
                                                detector_class=detector_class,
                                                attribute_name_for_plot=attribute_name_for_plot,
                                                activities=activities,
                                                activities_for_plot=activities_for_plot)
            framework.run_script(parameters)

            running = framework.get_status_running()
            while running:
                print(f'Waiting for IPDD finishes ... Status running: {running}')
                time.sleep(2)  # in seconds
                running = framework.get_status_running()
            print(f'Adaptive IPDD finished drift analysis on the data perspective')
            detected_drifts = {}
            # get the activities that report a drift using the change detector
            for activity in framework.get_all_activities():
                indexes = framework.get_initial_trace_indexes(activity)
                detected_drifts[activity] = indexes[1:]
                print(
                    f'Adaptive IPDD detect drifts for attribute {dataset_config.attribute} in activity {activity} in '
                    f'traces {detected_drifts}')
                dict_results[log][f'{DRIFTS_KEY}{DETECTOR_KEY}={delta} {ACTIVITY_KEY}={activity}'] = detected_drifts[activity]

    out_filepath = framework.get_evaluation_path('script')
    out_filename = f'{dataset_config.dataset_name}_results_IPDD_{Approach.ADAPTIVE.name}_'\
                   f'{AdaptivePerspective.TIME_DATA.name}_' \
                   f'{dataset_config.attribute}.xlsx'

    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(os.path.join(out_filepath, out_filename))
    if evaluate:
        calculate_metrics_massive(out_filepath, out_filename, dataset_config, True)


def run_massive_fixed_controlflow(dataset_config, metrics=None):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    dict_results = {}
    for log in dataset_config.lognames:
        dict_results[log] = {}
        for w in dataset_config.windows:
            print('----------------------------------------------')
            print(f'Running new scenario')
            print(f'Approach: {Approach.FIXED.value}')
            print(f'Window size: {w}')
            print(f'Metrics: {[m.value for m in metrics]}')
            print(f'Event log: {log}')
            print('----------------------------------------------')
            log_filename = os.path.join(dataset_config.input_path, log)
            parameters = IPDDParametersFixed(log_filename, Approach.FIXED.name, ReadLogAs.TRACE.name,
                                             metrics, WindowUnityFixed.UNITY.name, w)
            framework.run_script(parameters)

            running = framework.get_status_running()
            while running:
                print(f'Waiting for IPDD finishes ... Status running: {running}')
                time.sleep(2)  # in seconds
                running = framework.get_status_running()
            print(f'Fixed IPDD finished drift analysis')
            windows_with_drifts, detected_drifts = framework.get_windows_with_drifts()
            dict_results[log][f'{DRIFTS_KEY}w={w}'] = detected_drifts
            print(f'Fixed IPDD detect control-flow drift in windows {windows_with_drifts} - traces {detected_drifts}')
    out_filename = os.path.join(framework.get_evaluation_path('script'),
                                f'{dataset_config.dataset_name}_results_IPDD_{Approach.FIXED.name}.xlsx')
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_filename)


def run_massive_adaptive_controlflow(dataset_config, adaptive_approach, metrics=None, evaluate=False,
                                     save_sublogs=False, save_model_png=False):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    dict_results = {}
    for log in dataset_config.lognames:
        dict_results[log] = {}
        for w in dataset_config.windows:
            for detector in dataset_config.detectors:
                print('----------------------------------------------')
                print(f'Running new scenario')
                print(f'Approach: {Approach.ADAPTIVE.value}')
                print(f'Adaptive approach: {adaptive_approach.value}')
                print(f'Window size: {w}')
                print(f'Detector: {detector.get_name()}')
                for key in detector.parameters:
                    print(f'Detector [{key}]: {detector.parameters[key]}')
                print(f'Metrics: {[m.value for m in metrics]}')
                print(f'Event log: {log}')
                print('----------------------------------------------')
                log_filename = os.path.join(dataset_config.input_path, log)
                parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                               perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                               read_log_as=ReadLogAs.TRACE.name,
                                                               win_size=w, metrics=metrics,
                                                               adaptive_controlflow_approach=adaptive_approach.name,
                                                               detector_class=detector, save_sublogs=save_sublogs,
                                                               save_model_svg=save_model_png)
                framework.run_script(parameters)

                running = framework.get_status_running()
                while running:
                    print(f'Waiting for IPDD finishes ... Status running: {running}')
                    time.sleep(20)  # in seconds
                    running = framework.get_status_running()
                print(f'Adaptive IPDD finished drift analysis')
                detected_drifts = framework.get_initial_trace_indexes()
                # remove the index 0
                if detected_drifts:
                    detected_drifts = detected_drifts[1:]
                dict_results[log][f'{DRIFTS_KEY}w={w} {DETECTOR_KEY}={detector.get_name()}{detector.get_parameters_string()}'] = detected_drifts
                print(
                    f'Adaptive IPDD detect control-flow drifts in traces {detected_drifts}')

    out_filename = f'{dataset_config.dataset_name}_results_IPDD_{Approach.ADAPTIVE.name}' \
                   f'_{AdaptivePerspective.CONTROL_FLOW.name}' \
                   f'_{adaptive_approach.name}.xlsx'
    out_complete_filename = os.path.join(framework.get_evaluation_path('script'),
                                         out_filename)
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_complete_filename)
    if evaluate:
        calculate_metrics_massive(framework.get_evaluation_path('script'),
                                  out_filename, dataset_config, True)


def run_massive_adaptive_controlflow_mixed(dataset_config, metrics=None, evaluate=False,
                                                    save_sublogs=False, save_model_svg=False):
    run_massive_adaptive_controlflow(dataset_config,
                                     ControlflowAdaptiveApproach.MIXED,
                                     metrics, evaluate, save_sublogs, save_model_svg)


def run_massive_adaptive_controlflow_trace_by_trace(dataset_config, metrics=None, evaluate=False,
                                                    save_sublogs=False, save_model_svg=False):
    run_massive_adaptive_controlflow(dataset_config,
                                     ControlflowAdaptiveApproach.TRACE,
                                     metrics, evaluate, save_sublogs, save_model_svg)


def run_massive_adaptive_controlflow_windowing(dataset_config, metrics=None, evaluate=False,
                                               save_sublogs=False, save_model_svg=False):
    run_massive_adaptive_controlflow(dataset_config,
                                     ControlflowAdaptiveApproach.WINDOW,
                                     metrics, evaluate, save_sublogs, save_model_svg)


def convert_list_to_int(string_list):
    number_of_itens = len(string_list)
    integer_list = []
    if number_of_itens > 0 and string_list[0] != '':  # to avoid error in case of list with ''
        integer_map = map(int, string_list.copy())
        integer_list = list(integer_map)
    return integer_list


def calculate_metrics_massive(filepath, filename, dataset_config, save_input_for_calculation=False):
    metrics = [item.value for item in EvaluationMetricList]
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)

    input_filename = os.path.join(filepath, filename)
    print(f'*****************************************************************')
    print(f'Calculating metrics for file {input_filename}...')
    print(f'*****************************************************************')
    df = pd.read_excel(input_filename, index_col=0)
    complete_results = df.T.to_dict()
    metrics_results = {}
    for logname in complete_results.keys():
        if logname not in dataset_config.lognames:
            print(f'Logname {logname} not configured for the dataset. IGNORING...')
            continue
        metrics_results[logname] = {}
        regexp = r'(\d.*).xes'
        if match := re.search(regexp, logname):
            logsize = match.group(1)
        else:
            # if the name do not use the pattern for log size, use the logname
            logsize = logname

        change_points = {}
        detected_at = {}
        for key in complete_results[logname].keys():
            # get list of trace ids from excel and convert to a list of integers
            if type(complete_results[logname][key]) == str:
                trace_ids_list = complete_results[logname][key][1:-1].split(",")
            else:  # for activities not present in the log
                trace_ids_list = []
            trace_ids_list = convert_list_to_int(trace_ids_list)

            # insert into change points or detected points
            if DRIFTS_KEY in key:
                configuration = key[len(DRIFTS_KEY):]
                change_points[configuration] = trace_ids_list
            elif DETECTED_AT_KEY in key:
                configuration = key[len(DETECTED_AT_KEY):]
                detected_at[configuration] = trace_ids_list

        for configuration in change_points.keys():
            if hasattr(dataset_config, "activities") and dataset_config.activities is not None:
                # get the activity name in the configuration
                regexp = f"{DETECTOR_KEY}=(\d.*) {ACTIVITY_KEY}=(.*)"
                if match := re.search(regexp, configuration):
                    activity_reported = match.group(2)
                else:
                    print('Could not find the activity name in the results')
                    return

                # in this case the drifts are reported by activity (Time/Data perspective)
                for a in dataset_config.activities:
                    if a == activity_reported:
                        # get the actual change points
                        real_change_points = dataset_config.actual_change_points[activity_reported][logsize]
                        instances = dataset_config.number_of_instances[activity_reported][logsize]

                        # get the detected at information if available and convert to a list of integers
                        metrics_summary = framework.evaluate(real_change_points,
                                                             change_points[configuration],
                                                             instances)
                        # add the calculated metrics to the dictionary
                        if save_input_for_calculation:
                            metrics_results[logname][f'Detected drifts {configuration}'] = change_points[configuration]
                            if len(detected_at) > 0:
                                metrics_results[logname][f'Detected at {configuration}'] = detected_at[configuration]
                            metrics_results[logname][f'Real drifts {configuration}'] = real_change_points
                        for m in metrics:
                            metrics_results[logname][f'{m} {configuration}'] = metrics_summary[m]
            else:
                # get the actual change points
                real_change_points = dataset_config.actual_change_points[logsize]
                instances = dataset_config.number_of_instances[logsize]

                # get the detected at information if available and convert to a list of integers
                metrics_summary = framework.evaluate(real_change_points,
                                                     change_points[configuration],
                                                     instances)
                # add the calculated metrics to the dictionary
                if save_input_for_calculation:
                    metrics_results[logname][f'Detected drifts {configuration}'] = change_points[configuration]
                    if len(detected_at) > 0:
                        metrics_results[logname][f'Detected at {configuration}'] = detected_at[configuration]
                    metrics_results[logname][f'Real drifts {configuration}'] = real_change_points
                for m in metrics:
                    metrics_results[logname][f'{m} {configuration}'] = metrics_summary[m]
    df = pd.DataFrame(metrics_results).T
    out_filename = filename[:-(len('.xlsx'))]
    out_filename = f'metrics_{out_filename}.xlsx'
    out_complete_filename = os.path.join(filepath, out_filename)
    print(f'*****************************************************************')
    print(f'Metrics for file {input_filename} calculated')
    print(f'Saving results at file {out_complete_filename}...')
    df.to_excel(out_complete_filename)
    print(f'*****************************************************************')
