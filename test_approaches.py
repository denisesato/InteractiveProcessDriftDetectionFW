import os

from components.dfg_definitions import Metric
from components.evaluate.manage_evaluation_metrics import EvaluationMetricList
from components.ippd_fw import IPDDParametersFixed, IPDDParametersAdaptiveControlflow
from components.parameters import Approach, WindowUnityFixed, ReadLogAs, AdaptivePerspective, \
    ControlflowAdaptiveApproach
from ipdd_cli import run_IPDD_script


def test_fixed_control_flow_ok1():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 250
    parameters = IPDDParametersFixed(logname=log_filename, approach=Approach.FIXED.name,
                                     read_log_as=ReadLogAs.TRACE.name, metrics=[Metric.NODES.name, Metric.EDGES.name],
                                     winunity=WindowUnityFixed.UNITY.name, winsize=window)
    expected_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    assert metrics[EvaluationMetricList.F_SCORE.value] == 1


def test_fixed_control_flow_detection_nok1():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    # with a window of 500 no drift is detected
    window = 500
    parameters = IPDDParametersFixed(logname=log_filename, approach=Approach.FIXED.name,
                                     read_log_as=ReadLogAs.TRACE.name, metrics=[Metric.NODES.name, Metric.EDGES.name],
                                     winunity=WindowUnityFixed.UNITY.name, winsize=window)
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    expected_drifts = []
    assert detected_drifts == expected_drifts
    assert metrics[EvaluationMetricList.F_SCORE.value] == 0


def test_fixed_control_flow_detection_nok2():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    # with Nodes metric no drift is detected
    window = 250
    parameters = IPDDParametersFixed(logname=log_filename, approach=Approach.FIXED.name,
                                     read_log_as=ReadLogAs.TRACE.name, metrics=[Metric.NODES.name],
                                     winunity=WindowUnityFixed.UNITY.name, winsize=window)
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    expected_drifts = []
    assert detected_drifts == expected_drifts
    assert metrics[EvaluationMetricList.F_SCORE.value] == 0


def test_adaptive_control_flow_trace_ok1():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cm2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 125
    delta = 0.002
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   delta=delta)
    expected_drifts = [255, 543, 767, 1023, 1279, 1535, 1759, 2015, 2271]
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    # F-score 1 Mean delay 21.89
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 1
    assert mean_delay == 21.89


def test_adaptive_control_flow_trace_ok2():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'pm2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 125
    delta = 0.1
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   delta=delta)
    expected_drifts = [255, 511, 767, 1023, 1279, 1471, 1599, 1759, 1983, 2271]
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    # F-score 0.84 Mean delay 26.75
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 0.84
    assert mean_delay == 26.75

def test_adaptive_control_flow_windowing_ok1():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 100
    delta = 0.002
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.WINDOW.name,
                                                   delta=delta)
    expected_drifts = [319, 508, 799, 1020, 1311, 1500, 1759, 2012, 2271]
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    # F-score 1 Mean delay 27.66
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 1
    assert mean_delay == 27.67
