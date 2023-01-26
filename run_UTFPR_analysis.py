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
import subprocess

from components.dfg_definitions import Metric
from ipdd_massive import run_massive_fixed_controlflow, run_massive_adaptive_controlflow_trace_by_trace, \
    calculate_metrics_massive, run_massive_adaptive_controlflow_windowing, run_massive_adaptive_data


def define_change_points_dataset1(inter_drift_distance):
    actual_change_points = []
    for i in range(inter_drift_distance, inter_drift_distance * 10, inter_drift_distance):
        actual_change_points.append(i)
    return actual_change_points


class UTFPRConfigurationControlflow:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:/Users/denis/Documents/ProjetoUTFPR'
    lognames = [
        # 'log_formados.gz.xes.gz',
        # 'log_desistentes.gz.xes.gz',
        'CP.Sheet1.xes.gz'
    ]

    windows = [20]
    deltas = [0.002]


class UTFPRConfigurationData:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:/Users/denis/Documents/ProjetoUTFPR'
    lognames = [
        'log_formados.gz.xes.gz',
        # 'log_desistentes.gz.xes.gz',
    ]
    deltas = [0.002]
    attribute_name = 'Média'


def one_experiment_for_testing():
    folder = 'C:/Users/denis/Documents/ProjetoUTFPR'
    lognames = [
        'log_formados.gz.xes.gz',
        # 'log_desistentes.gz.xes.gz',
    ]

    deltas = [0.002]

    attribute = 'Média';

    for log in lognames:
        file = os.path.join(folder, log)
        for delta in deltas:
            print(
                f'Executando experimento para o log {file} adaptativo OTHER ATTRIBUTE {attribute} com delta {delta} ...')
            subprocess.run(f"ipdd_cli.py -a a -l {file} -d {delta} -p td -at ot -atname {attribute}", shell=True)


if __name__ == '__main__':
    datasetconfig_controlflow = UTFPRConfigurationControlflow()
    run_massive_adaptive_controlflow_trace_by_trace(datasetconfig_controlflow,
                                                    metrics=[Metric.NODES],
                                                    save_sublogs=True,
                                                    save_model_svg=True)
    # datasetconfig_data = UTFPRConfigurationData()
    # run_massive_adaptive_data(datasetconfig_data)
