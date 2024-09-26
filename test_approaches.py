import os

from components.adaptive.detectors import SelectDetector, ConceptDriftDetector
from components.dfg_definitions import Metric
from components.evaluate.manage_evaluation_metrics import EvaluationMetricList
from components.ippd_fw import IPDDParametersFixed, IPDDParametersAdaptiveControlflow, IPDDParametersAdaptive
from components.parameters import Approach, WindowUnityFixed, ReadLogAs, AdaptivePerspective, \
    ControlflowAdaptiveApproach, AttributeAdaptive
from ipdd_cli import run_IPDD_script


def test_fixed_control_flow_ok1():
    input_path = 'datasets/dataset1'
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
    input_path = 'datasets/dataset1'
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
    input_path = 'datasets/dataset1'
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
    input_path = 'datasets/dataset1'
    log = 'cm2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 125
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   detector_class=detector_class)
    # expected_drifts = [255, 543, 767, 1023, 1279, 1535, 1791, 2047, 2303]
    expected_drifts = [255, 543, 767, 1023, 1279, 1535, 1759, 2015, 2271] # after fixing river
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 1
    # assert mean_delay == 39.67
    assert mean_delay == 21.89 # after fixing river


def test_adaptive_control_flow_trace_ok2():
    input_path = 'datasets/dataset1'
    log = 'pm2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 125
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name,
                                                          parameters={'delta': 0.1})
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   detector_class=detector_class)
    # expected_drifts = [287, 543, 767, 1023, 1279, 1535, 1759, 2015, 2271]
    expected_drifts = [255, 511, 767, 1023, 1279, 1471, 1599, 1759, 1983, 2271] # after fixing river
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    # assert f_score == 1
    assert f_score == 0.84 # after fixing river
    # assert mean_delay == 25.44
    assert mean_delay == 26.75 # after fixing river


def test_adaptive_control_flow_trace_ok3():
    input_path = 'datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 75
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   detector_class=detector_class,
                                                   save_sublogs=True)
    # Using Pm4Py 2.2.20.1 (thesis results )
    # expected_drifts = [319, 991, 1471, 1983, 2399]
    # Using Pm4Py 2.7.5 (refactoring of the inductive miner - email from Alessandro Berti
    # expected_drifts = [383]
    expected_drifts = [319] # after fixing river
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 0.2
    # assert mean_delay == 133
    assert mean_delay == 69 # after fixing river


def test_adaptive_control_flow_windowing_ok1():
    input_path = 'datasets/dataset1'
    log = 'cb2.5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 100
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)
    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.WINDOW.name,
                                                   detector_class=detector_class)
    # expected_drifts = [383, 508, 863, 1020, 1375, 1500, 1823, 2012, 2335]
    expected_drifts = [319, 508, 799, 1020, 1311, 1500, 1759, 2012, 2271] # after fixing river
    real_drifts = [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts == expected_drifts
    f_score = round(metrics[EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 1
    # assert mean_delay == 63.22
    assert mean_delay == 27.67 # after fixing river


def test_adaptive_time_ok1():
    input_path = ('C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de '
                  'Dados/DadosConceptDrift/LogsProducao/SelecionadosArtigo')
    log = 'DR_MS.xes'
    log_filename = os.path.join(input_path, log)
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name,
                                                          parameters={'delta': 0.05})
    parameters = IPDDParametersAdaptive(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                        perspective=AdaptivePerspective.TIME_DATA.name,
                                        read_log_as=ReadLogAs.TRACE.name,
                                        metrics=[Metric.NODES.name, Metric.EDGES.name],
                                        attribute=AttributeAdaptive.SOJOURN_TIME.name,
                                        detector_class=detector_class)
    # expected_drifts = [95]
    expected_drifts = [63, 127, 159] # after fixing river
    activity = 'Maquina Trabalhando'
    real_drifts = [0, 26, 100, 148, 215]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts[activity] == expected_drifts
    f_score = round(metrics[activity][EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[activity][EvaluationMetricList.MEAN_DELAY.value], 2)
    # assert f_score == 0.33
    assert f_score == 0.75 # after fixing river
    # assert mean_delay == 69
    assert mean_delay == 25  # after fixing river


def test_adaptive_time_ok2():
    input_path = ('C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de '
                  'Dados/DadosConceptDrift/LogsProducao/SelecionadosArtigo')
    log = 'DR.xes'
    log_filename = os.path.join(input_path, log)
    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)
    activity = 'Maquina Trabalhando'

    parameters = IPDDParametersAdaptive(logname=log_filename, approach=Approach.ADAPTIVE.name,
                                        perspective=AdaptivePerspective.TIME_DATA.name,
                                        read_log_as=ReadLogAs.TRACE.name,
                                        metrics=[Metric.NODES.name, Metric.EDGES.name],
                                        attribute=AttributeAdaptive.SOJOURN_TIME.name,
                                        detector_class=detector_class,
                                        activities=[activity],
                                        activities_for_plot=['Machine Working'],
                                        attribute_name_for_plot='duration (seconds)')
    # expected_drifts = [447]
    expected_drifts = [415] # after fixing river
    real_drifts = [349]
    detected_drifts, metrics = run_IPDD_script(parameters, real_drifts)
    assert detected_drifts[activity] == expected_drifts
    f_score = round(metrics[activity][EvaluationMetricList.F_SCORE.value], 2)
    mean_delay = round(metrics[activity][EvaluationMetricList.MEAN_DELAY.value], 2)
    assert f_score == 1
    # assert mean_delay == 98
    assert mean_delay == 66 # after fixing river

