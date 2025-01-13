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
from unittest.mock import inplace

from apps.app_process_models import evaluate
from components.adaptive.detectors import SelectDetector, ConceptDriftDetector
from components.parameters import AttributeAdaptive
from ipdd_massive import run_massive_adaptive_time, DETECTOR_KEY, ACTIVITY_KEY
import matplotlib.pyplot as plt
import os
from pm4py.objects.log.util import interval_lifecycle
import pm4py
import pandas as pd
import re
from autorank import autorank, plot_stats, create_report, latex_table

plots_path = 'plots'
f_score_key = 'F-score'
detector_key = 'detector'

class AllSyntheticEventLogsConfiguration:
    dataset_name = 'synthetic_datasets_production'

    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:\\Users\\denise\\OneDrive\\Documents\\Doutorado\\Bases de ' \
                 'Dados\\DadosConceptDrift\\LogsProducao\\Artificiais'
    lognames = [
        'LogArtificial01P300C10A.xes',
        'LogArtificial01P300C100A.xes',
        'LogArtificial01P300C1000A.xes',
        'LogArtificial1P350C10A.xes',
        'LogArtificial1P350C100A.xes',
        'LogArtificial1P350C1000A.xes',
        'LogArtificial5P400C10A.xes',
        'LogArtificial5P400C100A.xes',
        'LogArtificial5P400C100A.xes',
        'LogArtificial5P400C1000A.xes',
        'PerdaDesempenho0-Manut0-Data.xes',
        'PerdaDesempenho1-Manut0-Data.xes',
        'PerdaDesempenho1-Manut1-Data.xes',
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



class SyntheticEventLogsConfiguration:
    dataset_name = 'synthetic_datasets_production'

    # for generating the plots for the paper
    output_path = 'data/output/plots'
    duration_activity = "Machine_Operating"
    attribute_for_duration = "@@duration"
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    input_path = 'C:\\Users\\denise\\OneDrive\\Documents\\Doutorado\\Bases de ' \
                 'Dados\\DadosConceptDrift\\LogsProducao\\SelecionadosArtigo\\1stRevision'
    lognames = [
        'ST_01.xes.gz',
        'ST_02.xes.gz',
        'ST_03.xes.gz',
        'ST_04.xes.gz',
        'ST_05.xes.gz',
        'ST_06.xes.gz',
        'ST_07.xes.gz',
        'ST_08.xes.gz',
        'ST_09.xes.gz',
        'ST_10.xes.gz',
        'DR_01.xes.gz',
        'DR_02.xes.gz',
        'DR_03.xes.gz',
        'DR_04.xes.gz',
        'DR_05.xes.gz',
        'DR_06.xes.gz',
        'DR_07.xes.gz',
        'DR_08.xes.gz',
        'DR_09.xes.gz',
        'DR_10.xes.gz',
        'DR_MS_01.xes.gz',
        'DR_MS_02.xes.gz',
        'DR_MS_03.xes.gz',
        'DR_MS_04.xes.gz',
        'DR_MS_05.xes.gz',
        'DR_MS_06.xes.gz',
        'DR_MS_07.xes.gz',
        'DR_MS_08.xes.gz',
        'DR_MS_09.xes.gz',
        'DR_MS_10.xes.gz',
        'DR_MS_ST_01.xes.gz',
        'DR_MS_ST_02.xes.gz',
        'DR_MS_ST_03.xes.gz',
        'DR_MS_ST_04.xes.gz',
        'DR_MS_ST_05.xes.gz',
        'DR_MS_ST_06.xes.gz',
        'DR_MS_ST_07.xes.gz',
        'DR_MS_ST_08.xes.gz',
        'DR_MS_ST_09.xes.gz',
        'DR_MS_ST_10.xes.gz',
    ]
    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.1}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.3}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 1}),
    ]

    # deltas = [
    #     0.002,
    #     0.05,
    #     0.1,
    #     0.3,
    #     1
    # ]

    attribute = AttributeAdaptive.SOJOURN_TIME.name
    attribute_name = AttributeAdaptive.SOJOURN_TIME

    ###############################################################
    # Information for calculating evaluation metricso
    ###############################################################
    activities = ['Machine_Operating']
    activities_for_plot = ['Machine_Operating']
    actual_change_points = {
        'Machine_Operating': {
            'ST_01.xes.gz': [],
            'ST_02.xes.gz': [],
            'ST_03.xes.gz': [],
            'ST_04.xes.gz': [],
            'ST_05.xes.gz': [],
            'ST_06.xes.gz': [],
            'ST_07.xes.gz': [],
            'ST_08.xes.gz': [],
            'ST_09.xes.gz': [],
            'ST_10.xes.gz': [],
            'DR_01.xes.gz': [250],
            'DR_02.xes.gz': [250],
            'DR_03.xes.gz': [250],
            'DR_04.xes.gz': [250],
            'DR_05.xes.gz': [250],
            'DR_06.xes.gz': [250],
            'DR_07.xes.gz': [250],
            'DR_08.xes.gz': [250],
            'DR_09.xes.gz': [250],
            'DR_10.xes.gz': [250],
            'DR_MS_01.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_02.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_03.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_04.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_05.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_06.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_07.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_08.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_09.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_10.xes.gz': [0, 52, 103, 154, 205, 256, 307, 358, 409, 460],
            'DR_MS_ST_01.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_02.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_03.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_04.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_05.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_06.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_07.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_08.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_09.xes.gz': [50, 150, 250, 350, 450],
            'DR_MS_ST_10.xes.gz': [50, 150, 250, 350, 450],
        }
    }

    number_of_instances = {
        'Machine_Operating': {
            'ST_01.xes.gz': 5000,
            'ST_02.xes.gz': 5000,
            'ST_03.xes.gz': 5000,
            'ST_04.xes.gz': 5000,
            'ST_05.xes.gz': 5000,
            'ST_06.xes.gz': 5000,
            'ST_07.xes.gz': 5000,
            'ST_08.xes.gz': 5000,
            'ST_09.xes.gz': 5000,
            'ST_10.xes.gz': 5000,
            'DR_01.xes.gz': 500,
            'DR_02.xes.gz': 500,
            'DR_03.xes.gz': 500,
            'DR_04.xes.gz': 500,
            'DR_05.xes.gz': 500,
            'DR_06.xes.gz': 500,
            'DR_07.xes.gz': 500,
            'DR_08.xes.gz': 500,
            'DR_09.xes.gz': 500,
            'DR_10.xes.gz': 500,
            'DR_MS_01.xes.gz': 5000,
            'DR_MS_02.xes.gz': 5000,
            'DR_MS_03.xes.gz': 5000,
            'DR_MS_04.xes.gz': 5000,
            'DR_MS_05.xes.gz': 5000,
            'DR_MS_06.xes.gz': 5000,
            'DR_MS_07.xes.gz': 5000,
            'DR_MS_08.xes.gz': 5000,
            'DR_MS_09.xes.gz': 5000,
            'DR_MS_10.xes.gz': 5000,
            'DR_MS_ST_01.xes.gz': 500,
            'DR_MS_ST_02.xes.gz': 500,
            'DR_MS_ST_03.xes.gz': 500,
            'DR_MS_ST_04.xes.gz': 500,
            'DR_MS_ST_05.xes.gz': 500,
            'DR_MS_ST_06.xes.gz': 500,
            'DR_MS_ST_07.xes.gz': 500,
            'DR_MS_ST_08.xes.gz': 500,
            'DR_MS_ST_09.xes.gz': 500,
            'DR_MS_ST_10.xes.gz': 500,
        }
    }


class TemperatureLogConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'synthetic_dataset_temperature'

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
    dataset_name = 'real_dataset_production'

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


def generate_plot(plot_df, attribute_name, duration_activity, output_path, logname, target_drifts=None):
    print(f'Plot duration...')
    # get the min and max durations
    y_min = plot_df[attribute_name].min()
    y_max = plot_df[attribute_name].max()
    x_min = plot_df.index.min() - 0.02 * len(plot_df)
    x_max = plot_df.index.max() + 0.02 * len(plot_df)

    x_label = 'trace'

    fig, ax = plt.subplots()
    ax.plot(attribute_name, data=plot_df, color='#136EA8')
    ax.set(xlim=(x_min, x_max), ylim=(y_min, y_max))
    ax.set(xlabel=x_label, ylabel="Sojourn Time (seconds)")
    ax.set_title(f'{logname} - Activity {duration_activity}')

    # plot vertical lines for drifts
    if target_drifts:
        color_value = '#C20203'
        style = 'dotted'
        print(f'Plot real drifts ...')
        for drift in target_drifts:
            # add x-positions as a list of strings using the trace_index or event
            ax.vlines(x=drift,
                      ymin=y_min,
                      ymax=y_max,
                      # colors=log_configuration.activity_colors[i],
                      # colors='black',
                      colors=color_value,
                      # ls=log_configuration.activity_styles[i],
                      ls=style,
                      lw=2,
                      label="drifts")


    # save the plot
    # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    # ax.legend(loc="best")
    filename = f'{logname}_{duration_activity}_{attribute_name}'

    filename = os.path.join(output_path, f'{filename}.png')
    plt.savefig(filename, bbox_inches='tight')
    # plt.show()
    # clean memory
    plt.close()
    plt.cla()
    plt.clf()

def extract_durations_from_log(log_configuration):
    # create output_path if does not exist
    if not os.path.exists(log_configuration.output_path):
        os.makedirs(log_configuration.output_path)

    # create file for saving real drifts
    file_for_drifts = os.path.join(log_configuration.output_path, 'real_drifts.txt')
    with open(file_for_drifts, 'w') as output:
        for logname in log_configuration.lognames:
            # read the log, convert the two events with interval lifecyle (two timestamps - start and complete)
            # to one event, and then convert do dataframe
            logname_complete = os.path.join(log_configuration.input_path, logname)
            interval_log = pm4py.read_xes(logname_complete)
            interval_log = pm4py.convert_to_event_log(interval_log)
            log = interval_lifecycle.to_interval(interval_log)
            log = pm4py.convert_to_dataframe(log)

            # sort the log based based on the first event of each trace
            # get the first event of each trace
            first_events = log.groupby("case:concept:name").first()
            # sort by the timestamp of the first event, creating the trace_index
            first_events.sort_values(by="time:timestamp", inplace=True)
            first_events["trace_index"] = range(0, first_events.shape[0])
            # merge with complete dataframe and sort using the trace_index created
            sorted_log = pd.merge(log, first_events[["trace_index"]], how="inner", on=["case:concept:name"])
            # sort the log by trace (using the first event) and the timestamp of the other events
            sorted_log.sort_values(by=["trace_index", "time:timestamp"], inplace=True, ignore_index=True)

            # filter duration activity and group activity when a case has more than one instance
            # filter events based on the specified activity
            activity_log = sorted_log[sorted_log["concept:name"] == log_configuration.duration_activity]
            # group events by case index and sum/last the numeric attribute (decidir com Portela)
            # plot_df = activity_log.groupby("case:concept:name", as_index=False, sort=False)[
            #      log_configuration.attribute_name].sum()
            plot_df = activity_log.groupby("case:concept:name", as_index=False, sort=False)[
                log_configuration.attribute_for_duration].last()
            plot_df.index.name = 'Trace Index'

            # Filter rows where potential failure is true
            df_complete_grouped = activity_log.groupby(["case:concept:name", 'case:Potential_Failure'], as_index=False, sort=False).first()
            filtered_df = df_complete_grouped[df_complete_grouped['case:Potential_Failure'] == True]
            real_drifts = filtered_df.index.tolist()
            splits = [0] + [idx + 1 for idx, (i, j) in enumerate(zip(real_drifts, real_drifts[1:])) if j - i > 1] + [len(real_drifts)]
            result = [real_drifts[start] for start, end in zip(splits, splits[1:]) if end - start > 2]

            filename_durations = os.path.join(log_configuration.output_path,
                                              f'{logname}_{log_configuration.duration_activity}_{log_configuration.attribute_name}.xlsx')
            plot_df.to_excel(filename_durations)
            generate_plot(plot_df, log_configuration.attribute_for_duration, log_configuration.duration_activity,
                          log_configuration.output_path, logname, target_drifts=result)
            output.write(f'{logname}: {result}\n')
    output.close()


def generate_ipdd_plot_detectors(approach, folder, filename, metric_name, dataset_config, print_plot_name=True):
    complete_filename = os.path.join(folder, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    # filter the selected metric
    df_filtered = df.filter(like=metric_name, axis=1)
    # df_filtered.index.name = 'log size'
    dict_mean_metric = {}
    for d in dataset_config.detectors:
        df_detectors = df_filtered.filter(like=f'{detector_key}={d.get_complete_configuration()}', axis=1)
        # maintain only the information about detector in the column names
        df_detectors = df_detectors.rename(
            columns={element: re.sub(fr'{metric_name}  {DETECTOR_KEY}=(.*) ({ACTIVITY_KEY}=.*)', r'\1', element, count=2)
                     for element in df_detectors.columns.tolist()})
        dict_mean_metric[d.get_complete_configuration()] = df_detectors.mean()[d.get_complete_configuration()]

    # combine all approaches into one dataframe
    # df_plot = pd.concat([s for s in series], axis=1)
    # df_plot.sort_index(axis=1, inplace=True)
    plt.cla()
    plt.clf()
    series_plot = pd.Series(dict_mean_metric)
    series_plot.plot.line()
    plt.xticks(rotation=45, ha="right")
    plt.ylabel(metric_name)
    if print_plot_name:
        plt.title(f'{approach}\nImpact of the detector configuration on the {metric_name}')

    plt.grid(True)
    plt.legend()
    # plt.show()
    output_path = os.path.join(folder, plots_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_filename = os.path.join(output_path,
                                   f'detector_analysis_{metric_name}_{approach}_{dataset_config.dataset_name}')
    # plt.savefig(f'{output_filename}.eps', format='eps', bbox_inches='tight')
    # plt.savefig(f'{output_filename}.png', bbox_inches='tight')
    plt.savefig(f'{output_filename}.pdf', bbox_inches='tight')
    plt.close()

    # print('Usando autorank para calcular os testes estatísticos - exportando gráfico com CD')
    # result = autorank(df_filtered, alpha=0.05, verbose=True)
    # plot_stats(result)
    # create_report(result)
    # latex_table(result)
    # filename = os.path.join(output_path, f'{dataset_config.dataset_name}_{metric_name}_Nemenyi_CD')
    # # plt.savefig(f'{filename}.eps', format='eps', bbox_inches='tight')
    # # plt.savefig(f'{filename}.png', bbox_inches='tight')
    # plt.savefig(f'{filename}.pdf', bbox_inches='tight')
    # plt.close()


def generate_ipdd_plot_detectors_by_type(approach, folder, filename, metric_name, dataset_config, print_plot_name=True):
    complete_filename = os.path.join(folder, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    # filter the selected metric
    df_filtered = df.filter(like=metric_name, axis=1)
    df_filtered.index.name = 'log type'

    result = []
    # maintain only the information about detector in the column names
    detector_complete_name = 'adwin_delta'
    detector_name = 'adwin delta'
    df_detectors = df_filtered.rename(
        columns={element: re.sub(fr'{metric_name}  {DETECTOR_KEY}={detector_complete_name}(.*) ({ACTIVITY_KEY}=.*)', r'\1', element, count=2)
                 for element in df_filtered.columns.tolist()})
    df_detectors.reset_index(inplace=True)
    df_detectors['log type'] = df_detectors['log type'].replace(to_replace=r'([a-zA-Z]+)_\d.(.*)',  value=r'\1\2', regex=True)
    df_plot = df_detectors.groupby('log type').mean()

    plt.cla()
    plt.clf()
    df_plot.T.plot(kind="line")
    # plt.xticks(rotation=45, ha="right")
    plt.xlabel(detector_name)
    plt.ylabel(metric_name)
    if print_plot_name:
        plt.title(f'{approach}\nImpact of the detector configuration on the {metric_name}')

    plt.grid(True)
    plt.legend(loc='best')
    output_path = os.path.join(folder, plots_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_filename = os.path.join(output_path,
                                   f'detector_analysis_by_type_{metric_name}_{approach}_{dataset_config.dataset_name}')
    # plt.savefig(f'{output_filename}.eps', format='eps', bbox_inches='tight')
    # plt.savefig(f'{output_filename}.png', bbox_inches='tight')
    plt.savefig(f'{output_filename}.pdf', bbox_inches='tight')
    plt.close()

    print('Usando autorank para calcular os testes estatísticos - exportando gráfico com CD')
    df_analysis = df_detectors.set_index('log type', drop=True)
    result = autorank(df_analysis, alpha=0.05, verbose=True)
    plot_stats(result)
    create_report(result)
    latex_table(result)
    filename = os.path.join(output_path, f'{dataset_config.dataset_name}_{metric_name}_Nemenyi_CD_by_type')
    # plt.savefig(f'{filename}.eps', format='eps', bbox_inches='tight')
    # plt.savefig(f'{filename}.png', bbox_inches='tight')
    plt.savefig(f'{filename}.pdf', bbox_inches='tight')
    plt.close()


def analyze_IPDD_time():
    plt.rcParams.update({'pdf.fonttype': 42})
    # I suggest to only uncomment one analysis per execution
    ######################################################################
    # EVALUATION OF THE IPDD ADAPTIVE ON SYNTHETIC EVENT LOGS
    ######################################################################
    ######################################################################
    # ANALYSIS 1 - Trace by trace approach
    # Impact of the delta and window size on the accuracy
    ######################################################################
    dataset_config = SyntheticEventLogsConfiguration()
    plot_name = 'Adaptive IPDD for Time Drifts'
    folder = 'data/output/script/evaluation'
    file = f'metrics_{dataset_config.dataset_name}_results_IPDD_ADAPTIVE_TIME_DATA_SOJOURN_TIME.xlsx'
    generate_ipdd_plot_detectors(plot_name, folder, file, f_score_key, dataset_config, print_plot_name=False)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, f_score_key, dataset_config, print_plot_name=True)


if __name__ == '__main__':
    # first submitted version
    # dataset_complete = AllSyntheticEventLogsConfiguration()
    # run_massive_adaptive_time(dataset_complete)
    # dataset2 = TemperatureLogConfiguration()
    # run_massive_adaptive_time(dataset2, evaluate=True)
    # dataset3 = RealEventLogConfiguration()
    # run_massive_adaptive_time(dataset3)

    # datasets used on paper 1st revision
    dataset1 = SyntheticEventLogsConfiguration()

    # run experiments
    # run_massive_adaptive_time(dataset1, evaluate=True)

    # extract sojourn times and generate plots
    # also save information about real drifts
    # based on the attribute Potential_Failure
    # extract_durations_from_log(dataset1)

    # analyze experiments results
    analyze_IPDD_time()
