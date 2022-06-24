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

"""
For running IPDD massively, the user must define the dataset configuration:

class DatasetSampleConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_folder = '/IPDD_Datasets/dataset1'
    lognames = ['cb2.5k.xes', cd5k.xes]
    windows = [25, 50]
    deltas = [0.002, 0.05]

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    actual_change_points = {
        '2.5k': define_change_points_dataset1(250),
        '5k': define_change_points_dataset1(500),
    }

    number_of_instances = {
        '2.5k': 2500,
        '5k': 5000,
    } 
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
    out_filename = os.path.join(framework.get_evaluation_path('script'), f'results_IPDD_{Approach.FIXED.name}.xlsx')
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_filename)


def run_massive_adaptive_controlflow(dataset_config, adaptive_approach, metrics=None, evaluate=False):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    dict_results = {}
    for log in dataset_config.lognames:
        dict_results[log] = {}
        for w in dataset_config.windows:
            for delta in dataset_config.deltas:
                print('----------------------------------------------')
                print(f'Running new scenario')
                print(f'Approach: {Approach.ADAPTIVE.value}')
                print(f'Adaptive approach: {adaptive_approach.value}')
                print(f'Window size: {w}')
                print(f'Delta: {delta}')
                print(f'Metrics: {[m.value for m in metrics]}')
                print(f'Event log: {log}')
                print('----------------------------------------------')
                log_filename = os.path.join(dataset_config.input_path, log)
                parameters = IPDDParametersAdaptiveControlflow(log_filename, Approach.ADAPTIVE.name,
                                                               AdaptivePerspective.CONTROL_FLOW.name,
                                                               ReadLogAs.TRACE.name,
                                                               w, metrics, adaptive_approach.name,
                                                               delta)
                framework.run_script(parameters)

                running = framework.get_status_running()
                while running:
                    print(f'Waiting for IPDD finishes ... Status running: {running}')
                    time.sleep(20)  # in seconds
                    running = framework.get_status_running()
                print(f'Adaptive IPDD finished drift analysis')
                detected_drifts = framework.get_initial_trace_indexes()
                # remove the index 0
                detected_drifts = detected_drifts[1:]
                dict_results[log][f'{DRIFTS_KEY}w={w} d={delta}'] = detected_drifts
                print(
                    f'Adaptive IPDD detect control-flow drifts in traces {detected_drifts}')

    out_filename = f'results_IPDD_{Approach.ADAPTIVE.name}' \
                   f'_{AdaptivePerspective.CONTROL_FLOW.name}' \
                   f'_{adaptive_approach.name}.xlsx'
    out_complete_filename = os.path.join(framework.get_evaluation_path('script'),
                                         out_filename)
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_complete_filename)
    if evaluate:
        calculate_metrics_massive(framework.get_evaluation_path('script'),
                                  out_filename, dataset_config, True)


def run_massive_adaptive_controlflow_trace_by_trace(dataset_config, metrics=None, evaluate=False):
    run_massive_adaptive_controlflow(dataset_config,
                                     ControlflowAdaptiveApproach.TRACE,
                                     metrics, evaluate)


def run_massive_adaptive_controlflow_windowing(dataset_config, metrics=None, evaluate=False):
    run_massive_adaptive_controlflow(dataset_config,
                                     ControlflowAdaptiveApproach.WINDOW,
                                     metrics, evaluate)


def convert_list_to_int(string_list):
    number_of_itens = len(string_list)
    integer_list = []
    if number_of_itens > 0 and string_list[0] != '':  # to avoid error in case of list with ''
        integer_map = map(int, string_list.copy())
        integer_list = list(integer_map)
    return integer_list


def calculate_metrics_massive(filepath, filename, dataset_config, save_input_for_calculation=False):
    metrics = [item for item in EvaluationMetricList]
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
            print(f'Problem getting the logsize. File {input_filename} NOT PROCESSED!')
            return

        change_points = {}
        detected_at = {}
        for key in complete_results[logname].keys():
            # get list of trace ids from excel and convert to a list of integers
            trace_ids_list = complete_results[logname][key][1:-1].split(",")
            trace_ids_list = convert_list_to_int(trace_ids_list)

            # insert into change points or detected points
            if DRIFTS_KEY in key:
                configuration = key[len(DRIFTS_KEY):]
                change_points[configuration] = trace_ids_list
            elif DETECTED_AT_KEY in key:
                configuration = key[len(DETECTED_AT_KEY):]
                detected_at[configuration] = trace_ids_list

        for configuration in change_points.keys():
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
