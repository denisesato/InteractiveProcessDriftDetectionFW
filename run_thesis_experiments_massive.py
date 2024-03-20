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
from components.adaptive.detectors import SelectDetector, ConceptDriftDetector
from ipdd_massive import run_massive_fixed_controlflow, run_massive_adaptive_controlflow_trace_by_trace, \
    calculate_metrics_massive, run_massive_adaptive_controlflow_windowing


def define_change_points_dataset1(inter_drift_distance):
    actual_change_points = []
    for i in range(inter_drift_distance, inter_drift_distance * 10, inter_drift_distance):
        actual_change_points.append(i)
    return actual_change_points


class Dataset1Configuration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'dataset1'
    input_path = 'datasets/dataset1'
    lognames2500 = [
        'cb2.5k.xes',
        'cd2.5k.xes',
        'cf2.5k.xes',
        'cm2.5k.xes',
        'cp2.5k.xes',
        # 'fr2.5k.xes', # not used because IPDD only detects structural drifts in the control-flow perspective
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
        # 'fr5k.xes', # not used because IPDD only detects structural drifts in the control-flow perspective
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
        # 'fr7.5k.xes', # not used because IPDD only detects structural drifts in the control-flow perspective
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
        # 'fr10k.xes', # not used because IPDD only detects structural drifts in the control-flow perspective
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

    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.1}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.3}),
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


class Dataset2Configuration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'dataset2'
    input_path = 'datasets/dataset2'
    lognames3000 = [
        'cb3k.xes',
        'cd3k.xes',
        'cf3k.xes',
        'cm3k.xes',
        'cp3k.xes',
        'IOR3k.xes',
        'IRO3k.xes',
        'lp3k.xes',
        'OIR3k.xes',
        'ORI3k.xes',
        'pl3k.xes',
        'pm3k.xes',
        're3k.xes',
        'RIO3k.xes',
        'ROI3k.xes',
        'rp3k.xes',
        'sw3k.xes',
    ]
    lognames4500 = [
        'cb4.5k.xes',
        'cd4.5k.xes',
        'cf4.5k.xes',
        'cm4.5k.xes',
        'cp4.5k.xes',
        'IOR4.5k.xes',
        'IRO4.5k.xes',
        'lp4.5k.xes',
        'OIR4.5k.xes',
        'ORI4.5k.xes',
        'pl4.5k.xes',
        'pm4.5k.xes',
        're4.5k.xes',
        'RIO4.5k.xes',
        'ROI4.5k.xes',
        'rp4.5k.xes',
        'sw4.5k.xes',
    ]
    lognames8000 = [
        'cb8k.xes',
        'cd8k.xes',
        'cf8k.xes',
        'cm8k.xes',
        'cp8k.xes',
        'IOR8k.xes',
        'IRO8k.xes',
        'lp8k.xes',
        'OIR8k.xes',
        'ORI8k.xes',
        'pl8k.xes',
        'pm8k.xes',
        're8k.xes',
        'RIO8k.xes',
        'ROI8k.xes',
        'rp8k.xes',
        'sw8k.xes',
    ]

    lognames = lognames3000 + lognames4500 + lognames8000
    windows = [i for i in range(25, 301, 25)]
    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.1}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.3}),
    ]

    # sample for testing one specific scenario
    # lognames = ['cb3k.xes']
    # windows = [100]
    # detectors = [SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002})]

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    actual_change_points = {
        '3k': [],
        '4.5k': [],
        '8k': [],
    }

    number_of_instances = {
        '3k': 3000,
        '4.5k': 4500,
        '8k': 8000,
    }


class RealDatasetConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'italian_help_desk_company'
    input_path = 'datasets/real'
    lognames = ['italian_help_desk_company.xes']
    windows = [100]
    deltas = [0.002]


if __name__ == '__main__':
    dataset1 = Dataset1Configuration()
    # run_massive_fixed_controlflow(dataset1)
    run_massive_adaptive_controlflow_trace_by_trace(dataset1, evaluate=True)
    run_massive_adaptive_controlflow_windowing(dataset1, evaluate=True)

    dataset2 = Dataset2Configuration()
    # run_massive_fixed_controlflow(dataset2)
    run_massive_adaptive_controlflow_trace_by_trace(dataset2, evaluate=True)
    run_massive_adaptive_controlflow_windowing(dataset2, evaluate=True)

    real_dataset = RealDatasetConfiguration()
    # run_massive_fixed_controlflow(real_dataset)
    run_massive_adaptive_controlflow_trace_by_trace(real_dataset)
    run_massive_adaptive_controlflow_windowing(real_dataset)
