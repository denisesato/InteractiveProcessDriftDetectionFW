import subprocess
import os

from components.adaptive.detectors import SelectDetector, ConceptDriftDetector
from components.dfg_definitions import Metric
from components.ippd_fw import IPDDParametersAdaptiveControlflow
from components.parameters import Approach, ReadLogAs, AdaptivePerspective, ControlflowAdaptiveApproach
from ipdd_cli import run_IPDD_script


def trace_by_trace_without_update_model():
    input_path = 'C:/Users/Denise/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    log = 'cb5k.xes'
    log_filename = os.path.join(input_path, log)
    window = 100

    detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name)

    parameters = IPDDParametersAdaptiveControlflow(logname=log_filename,
                                                   approach=Approach.ADAPTIVE.name,
                                                   perspective=AdaptivePerspective.CONTROL_FLOW.name,
                                                   read_log_as=ReadLogAs.TRACE.name,
                                                   win_size=window,
                                                   metrics=[Metric.NODES.name, Metric.EDGES.name],
                                                   adaptive_controlflow_approach=ControlflowAdaptiveApproach.TRACE.name,
                                                   detector_class=detector_class,
                                                   update_model=False)
    detected_drifts = run_IPDD_script(parameters)
    print(f'IPDD detected: {detected_drifts}')


if __name__ == '__main__':
    trace_by_trace_without_update_model()
