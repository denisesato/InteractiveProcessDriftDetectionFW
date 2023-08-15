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
from components.parameters import AttributeAdaptive
from ipdd_massive import run_massive_adaptive_time


class SyntheticEventLogsConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:\\Users\\denise\\OneDrive\\Documents\\Doutorado\\Bases de ' \
                 'Dados\\DadosConceptDrift\\LogsProducao\\SelecionadosArtigo'
    lognames = [
        'ST.xes',
        'DR.xes',
        'DR_MS.xes',
        'DR_MS_ST.xes',
    ]

    deltas = [
        0.002,
        0.05,
        0.1,
        0.3,
        1
    ]

    attribute = AttributeAdaptive.SOJOURN_TIME.name
    attribute_name = AttributeAdaptive.SOJOURN_TIME

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    activities = ['Maquina Trabalhando']
    activities_for_plot = ['Machine Working']
    actual_change_points = {
        'Maquina Trabalhando': {
            'ST.xes': [],
            'DR.xes': [349],  # trace marcado no nome do log
            'DR_MS.xes': [0, 26, 100, 148, 215],  # trace inicial e traces após a parada para manutenção
            'DR_MS_ST.xes': [205, 858, 1246, 1555, 2006],  # traces marcados como QuedaDesempenho - TRUE
        }
    }

    number_of_instances = {
        'Maquina Trabalhando': {
            'ST.xes': 250,
            'DR.xes': 500,
            'DR_MS.xes': 250,
            'DR_MS_ST.xes': 2500
        }
    }


class TemperatureLogConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:\\Users\\denise\\OneDrive\\Documents\\Doutorado\\Bases de ' \
                 'Dados\\DadosConceptDrift\\LogsProducao\\SelecionadosArtigo'
    lognames = [
        'TD.xes',
    ]

    deltas = [
        0.002,
        0.05,
        0.1,
        0.3,
        1
    ]

    attribute = AttributeAdaptive.OTHER.name
    attribute_name = 'Temperatura'
    attribute_name_for_plot = 'Temperature (ºCelsius)'

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    activities = ['Maquina Trabalhando']
    activities_for_plot = ['Machine Working']
    actual_change_points = {
        'Maquina Trabalhando': {
            'TD.xes': [1075, 2314, 3310, 4485, 6094, 7968],
        }
    }

    number_of_instances = {
        'Maquina Trabalhando': {
            'TD.xes': 2499,
        }
    }


class RealEventLogConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:\\Users\\denise\\OneDrive\\Documents\\Doutorado\\Bases de ' \
                 'Dados\\DadosConceptDrift\\LogsProducao\\SelecionadosArtigo'
    lognames = [
        'LogLatheMachine_IPDD_Ingles.xes.gz',
    ]

    deltas = [
        0.002,
        0.05,
        0.1,
        0.3,
        1
    ]

    attribute = AttributeAdaptive.SOJOURN_TIME.name
    attribute_name = AttributeAdaptive.SOJOURN_TIME

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    activities = ['Machine working']
    activities_for_plot = ['Machine Working']


if __name__ == '__main__':
    dataset1 = SyntheticEventLogsConfiguration()
    run_massive_adaptive_time(dataset1, evaluate=True)
    dataset2 = TemperatureLogConfiguration()
    run_massive_adaptive_time(dataset2, evaluate=True)
    dataset3 = RealEventLogConfiguration()
    run_massive_adaptive_time(dataset3)
