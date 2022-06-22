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
import time
import pandas as pd

from components.parameters import ReadLogAs, WindowUnityFixed, Approach, AttributeAdaptive, AdaptivePerspective, \
    ControlflowAdaptiveApproach
from components.ippd_fw import InteractiveProcessDriftDetectionFW, IPDDParametersFixed, IPDDParametersAdaptive, \
    IPDDParametersAdaptiveControlflow

DRIFTS = 'drifts'


def run_massive_fixed_controlflow(input_path, lognames, windows, metrics=None):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    dict_results = {}
    for log in lognames:
        dict_results[log] = {}
        for w in windows:
            print('----------------------------------------------')
            print(f'Running new scenario')
            print(f'Approach: {Approach.FIXED.value}')
            print(f'Window size: {w}')
            print(f'Metrics: {[m.value for m in metrics]}')
            print(f'Event log: {log}')
            print('----------------------------------------------')
            log_filename = os.path.join(input_path, log)
            parameters = IPDDParametersFixed(log_filename, Approach.FIXED.name, ReadLogAs.TRACE.name,
                                             metrics, WindowUnityFixed.UNITY.name, w)
            framework.run(parameters, user_id='script')

            running = framework.get_status_running()
            while running:
                print(f'Waiting for IPDD finishes ... Status running: {running}')
                time.sleep(2)  # in seconds
                running = framework.get_status_running()
            print(f'Fixed IPDD finished drift analysis')
            windows_with_drifts, detected_drifts = framework.get_drifts_info()
            dict_results[log][f'{DRIFTS} - w={w}'] = detected_drifts
            print(f'Fixed IPDD detect control-flow drift in windows {windows_with_drifts} - traces {detected_drifts}')
    out_filename = os.path.join(framework.get_evaluation_path('script'), f'results_IPDD_{Approach.FIXED.value}.xlsx')
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_filename)


def run_massive_adaptive_controlflow(input_path, lognames, windows, deltas, adaptive_approach, metrics=None):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)
    if not metrics:
        metrics = framework.get_default_metrics()

    dict_results = {}
    for log in lognames:
        dict_results[log] = {}
        for w in windows:
            for delta in deltas:
                print('----------------------------------------------')
                print(f'Running new scenario')
                print(f'Approach: {Approach.ADAPTIVE.value}')
                print(f'Adaptive approach: {adaptive_approach.value}')
                print(f'Window size: {w}')
                print(f'Delta: {delta}')
                print(f'Metrics: {[m.value for m in metrics]}')
                print(f'Event log: {log}')
                print('----------------------------------------------')
                log_filename = os.path.join(input_path, log)
                parameters = IPDDParametersAdaptiveControlflow(log_filename, Approach.ADAPTIVE.name,
                                                               AdaptivePerspective.CONTROL_FLOW.name,
                                                               ReadLogAs.TRACE.name,
                                                               w, metrics, adaptive_approach.name,
                                                               delta)
                framework.run(parameters, user_id='script')

                running = framework.get_status_running()
                while running:
                    print(f'Waiting for IPDD finishes ... Status running: {running}')
                    time.sleep(20)  # in seconds
                    running = framework.get_status_running()
                print(f'Adaptive IPDD finished drift analysis')
                windows_with_drifts, detected_drifts = framework.get_drifts_info()
                dict_results[log][f'{DRIFTS} - w={w} d={delta}'] = detected_drifts
                print(f'Adaptive IPDD detect control-flow drift in windows {windows_with_drifts} - traces {detected_drifts}')
    out_filename = os.path.join(framework.get_evaluation_path('script'),
                                f'results_IPDD_{Approach.ADAPTIVE.value}'
                                f'_{AdaptivePerspective.CONTROL_FLOW.value}'
                                f'_{adaptive_approach.value}.xlsx')
    df = pd.DataFrame.from_dict(dict_results, orient='index')
    df.to_excel(out_filename)


def run_massive_adaptive_controlflow_trace_by_trace(path, logs, windows, deltas, metrics=None):
    run_massive_adaptive_controlflow(path, logs, windows, deltas,
                                     ControlflowAdaptiveApproach.TRACE,
                                     metrics)


def run_massive_adaptive_controlflow_windowing(path, logs, windows, deltas, metrics=None):
    run_massive_adaptive_controlflow(path, logs, windows,
                                     ControlflowAdaptiveApproach.WINDOW, deltas,
                                     metrics)
