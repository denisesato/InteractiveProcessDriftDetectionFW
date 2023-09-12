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
from ipdd_massive import run_massive_fixed_controlflow, run_massive_adaptive_controlflow_trace_by_trace, \
    run_massive_adaptive_controlflow_windowing
from components.adaptive.detectors import ConceptDriftDetector, SelectDetector
from components.dfg_definitions import Metric
from components.evaluate.manage_evaluation_metrics import EvaluationMetricList
from components.ippd_fw import IPDDParametersAdaptiveControlflow
from components.parameters import Approach, ReadLogAs, AdaptivePerspective, ControlflowAdaptiveApproach
from ipdd_cli import run_IPDD_script


def define_change_points_dataset1(inter_drift_distance):
    actual_change_points = []
    for i in range(inter_drift_distance, inter_drift_distance * 10, inter_drift_distance):
        actual_change_points.append(i)
    return actual_change_points


class Dataset1Configuration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    lognames2500 = [
        'cb2.5k.xes',
        'cd2.5k.xes',
        'cf2.5k.xes',
        'cm2.5k.xes',
        'cp2.5k.xes',
        # 'fr2.5k.xes',
        'IOR2.5k.xes',
        'IRO2.5k.xes',
        'lp2.5k.xes',
        'OIR2.5k.xes',
        'ORI2.5k.xes',
        'pl2.5k.xes',
        'pm2.5k.xes',
        're2.5k.xes',
        'RIO2.5k.xes',
        'ROI2.5k.xes',
        'rp2.5k.xes',
        'sw2.5k.xes',
    ]
    lognames5000 = [
        'cb5k.xes',
        'cd5k.xes',
        'cf5k.xes',
        'cm5k.xes',
        'cp5k.xes',
        # 'fr5k.xes',
        'IOR5k.xes',
        'IRO5k.xes',
        'lp5k.xes',
        'OIR5k.xes',
        'ORI5k.xes',
        'pl5k.xes',
        'pm5k.xes',
        're5k.xes',
        'RIO5k.xes',
        'ROI5k.xes',
        'rp5k.xes',
        'sw5k.xes',
    ]
    lognames7500 = [
        'cb7.5k.xes',
        'cd7.5k.xes',
        'cf7.5k.xes',
        'cm7.5k.xes',
        'cp7.5k.xes',
        # 'fr7.5k.xes',
        'IOR7.5k.xes',
        'IRO7.5k.xes',
        'lp7.5k.xes',
        'OIR7.5k.xes',
        'ORI7.5k.xes',
        'pl7.5k.xes',
        'pm7.5k.xes',
        're7.5k.xes',
        'RIO7.5k.xes',
        'ROI7.5k.xes',
        'rp7.5k.xes',
        'sw7.5k.xes',
    ]
    lognames10000 = [
        'cb10k.xes',
        'cd10k.xes',
        'cf10k.xes',
        'cm10k.xes',
        'cp10k.xes',
        # 'fr10k.xes',
        'IOR10k.xes',
        'IRO10k.xes',
        'lp10k.xes',
        'OIR10k.xes',
        'ORI10k.xes',
        'pl10k.xes',
        'pm10k.xes',
        're10k.xes',
        'RIO10k.xes',
        'ROI10k.xes',
        'rp10k.xes',
        'sw10k.xes',
    ]

    lognames = lognames2500 + lognames5000 + lognames7500 + lognames10000
    windows = [i for i in range(25, 301, 25)]
    deltas = [0.002, 0.05, 0.1, 0.3]

    # for testing one specific scenario
    lognames = ['cb2.5k.xes', 're2.5k.xes']
    windows = [i for i in range(25, 301, 25)]
    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name),
        SelectDetector.get_detector_instance(ConceptDriftDetector.HDDM_W.name),
    ]

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    actual_change_points = {
        '2.5k': define_change_points_dataset1(250),
        '5k': define_change_points_dataset1(500),
        '7.5k': define_change_points_dataset1(750),
        '10k': define_change_points_dataset1(1000)
    }

    number_of_instances = {
        '2.5k': 2500,
        '5k': 5000,
        '7.5k': 7500,
        '10k': 10000
    }

    ###############################################################
    # Plot specific information
    ###############################################################
    # For defining the correct order for the legend of the plots
    order_legend = [1, 2, 3, 0]


def run_adaptive_control_flow_trace_ok1():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 100

    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)
    # detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.HDDM_W.name)
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.WINDOW.name,
                                                   detector_class=detector_class)
    # real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    real_drifts = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]
    # Drifts detected by ADWIN
    # [319, 991, 1471, 1983, 2399]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    print(f'Detected drifts: {detected_drifts}')
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    print(f'F-score: {f_score}')
    print(f'Mean delay: {mean_delay}')


if __name__ == '__main__':
    # run_adaptive_control_flow_trace_ok1()
    dataset1 = Dataset1Configuration()
    # run_massive_fixed_controlflow(dataset1)
    run_massive_adaptive_controlflow_trace_by_trace(dataset1, evaluate=True)
    # run_massive_adaptive_controlflow_windowing(dataset1, evaluate=True)
