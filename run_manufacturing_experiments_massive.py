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
from enum import Enum

from components.adaptive.detectors import SelectDetector, ConceptDriftDetector
from components.evaluate.manage_evaluation_metrics import EvaluationMetricList
from components.parameters import AttributeAdaptive
from ipdd_massive import run_massive_adaptive_time, DETECTOR_KEY, ACTIVITY_KEY
import matplotlib.pyplot as plt
import os
from pm4py.objects.log.util import interval_lifecycle
import pm4py
import pandas as pd
import re
from autorank import autorank, plot_stats, create_report, latex_table
from itertools import chain
from pymoo.core.problem import ElementwiseProblem
from pymoo.visualization.scatter import Scatter
from pymoo.decomposition.asf import ASF
import numpy as np
from pymoo.util.misc import stack


plots_path = 'plots'
detector_key = 'detector'

class MCDM(str, Enum):
    MAX = 'maximize'
    MIN = 'minimize'
    

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
    input_path = 'datasets\\dataset_manufacturing'
    samples = 30
    ST = [f'ST_{(i+1):02d}.xes.gz' for i in range(samples)]
    DR = [f'DR_{(i + 1):02d}.xes.gz' for i in range(samples)]
    DR_MS = [f'DR_MS_{(i + 1):02d}.xes.gz' for i in range(samples)]
    DR_MS_ST = [f'DR_MS_ST_{(i + 1):02d}.xes.gz' for i in range(samples)]
    lognames = ST + DR + DR_MS + DR_MS_ST

    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.1}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.3}),
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 1}),
    ]


    attribute = AttributeAdaptive.SOJOURN_TIME.name
    attribute_name = AttributeAdaptive.SOJOURN_TIME

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    activities = ['Machine_Operating']
    activities_for_plot = ['Machine_Operating']

    # ST
    ST_drifts = dict(zip(ST, [[] for i in range(samples*4)]))

    # DR
    DR_drifts = dict(zip(DR, [[((i+1)*11)-1] for i in range(samples*4)]))

    # DR_MS
    DR_MS_current_change_points = [i*100 for i in range(5)]
    DR_MS_change_points = [DR_MS_current_change_points]
    for i in range(samples - 1):
        DR_MS_current_change_points = [0] + [x+1 for x in DR_MS_current_change_points[1:]]
        DR_MS_change_points = DR_MS_change_points + [DR_MS_current_change_points]
    DR_MS_drifts = dict(zip(DR_MS, DR_MS_change_points))

    # DR_MS_ST
    DR_MS_ST_current_change_points = [(i*40)+20 for i in range(5)]
    DR_MS_ST_increment = [1, 3, 5, 7, 9]
    DR_MS_ST_change_points = [DR_MS_ST_current_change_points]
    for i in range(samples-1):
        DR_MS_ST_current_change_points = [x + y for x, y in zip(DR_MS_ST_current_change_points, DR_MS_ST_increment)]
        DR_MS_ST_change_points = DR_MS_ST_change_points + [DR_MS_ST_current_change_points]
    DR_MS_ST_drifts = dict(zip(DR_MS_ST, DR_MS_ST_change_points))

    actual_change_points = {
        'Machine_Operating': dict(chain.from_iterable(d.items() for d in (ST_drifts, DR_drifts, DR_MS_drifts, DR_MS_ST_drifts)))
    }

    no_of_instances = [500 for i in range(samples * 4)]
    ST_inst = dict(zip(ST, no_of_instances))
    DR_inst = dict(zip(DR, no_of_instances))
    DR_MS_inst = dict(zip(DR_MS, no_of_instances))
    DR_MS_ST_inst = dict(zip(DR_MS_ST, no_of_instances))

    number_of_instances = {
        'Machine_Operating': dict(chain.from_iterable(d.items() for d in (ST_inst, DR_inst, DR_MS_inst, DR_MS_ST_inst)))
    }


class TemperatureLogConfiguration:
    ###############################################################
    # Information about the data for performing the experiments
    ###############################################################
    dataset_name = 'synthetic_dataset_temperature'

    input_path = 'datasets\\dataset_manufacturing'
    lognames = [
        'TD.xes',
    ]

    detectors = [
        SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002}),
        # SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.05}),
        # SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.1}),
        # SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.3}),
        # SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 1}),
    ]

    attribute = AttributeAdaptive.OTHER.name
    attribute_name = 'Temperatura'
    attribute_name_for_plot = 'Temperature (ºCelsius)'

    ###############################################################
    # Information for calculating evaluation metrics
    ###############################################################
    activities = ['Maquina Trabalhando']
    activities_for_plot = ['Machine_Operating']


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

    detectors = [SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name, parameters={'delta': 0.002})]

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
    ax.set_title(f'{logname} - {duration_activity}')

    # plot vertical lines for drifts
    if target_drifts:
        color_value = '#18a558'
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
            # df_complete_grouped = activity_log.groupby(["case:concept:name", 'case:Potential_Failure'], as_index=False, sort=False).first()
            # filtered_df = df_complete_grouped[df_complete_grouped['case:Potential_Failure'] == True]
            # real_drifts = filtered_df.index.tolist()
            # splits = [0] + [idx + 1 for idx, (i, j) in enumerate(zip(real_drifts, real_drifts[1:])) if j - i > 1] + [len(real_drifts)]
            # result = [real_drifts[start] for start, end in zip(splits, splits[1:]) if end - start > 2]

            # Get real drifts
            for activity in log_configuration.activities_for_plot:
                result = log_configuration.actual_change_points[activity][logname]

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

    if metric_name == EvaluationMetricList.FPR.value:
        metric_for_re = r'False positive rate \(FPR\)'
        metric_name = 'FPR'
    else:
        metric_for_re = metric_name

    for d in dataset_config.detectors:
        df_detectors = df_filtered.filter(like=f'{detector_key}={d.get_complete_configuration()}', axis=1)
        # maintain only the information about detector in the column names
        df_detectors = df_detectors.rename(
            columns={element: re.sub(fr'{metric_for_re}  {DETECTOR_KEY}=(.*) ({ACTIVITY_KEY}=.*)', r'\1', element, count=2)
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

    print('Usando autorank para calcular os testes estatísticos - exportando gráfico com CD')
    df_autorank = df_filtered.rename(
        columns={
            element: re.sub(fr'{metric_name}  {DETECTOR_KEY}=(.*) ({ACTIVITY_KEY}=.*)', r'\1', element, count=2)
            for element in df_filtered.columns.tolist()})
    index_ST = df_autorank[df_autorank.index.str.startswith('ST')].index.to_list()
    if metric_name == EvaluationMetricList.FPR:
        df_autorank = df_autorank[df_autorank.index.isin(index_ST)]
    else:
        df_autorank = df_autorank[~df_autorank.index.isin(index_ST)]


    result = autorank(df_autorank, alpha=0.05, verbose=True)
    plot_stats(result)
    create_report(result)
    latex_table(result)
    filename = os.path.join(output_path, f'{dataset_config.dataset_name}_{metric_name}_Nemenyi_CD')
    # plt.savefig(f'{filename}.eps', format='eps', bbox_inches='tight')
    # plt.savefig(f'{filename}.png', bbox_inches='tight')
    plt.savefig(f'{filename}.pdf', bbox_inches='tight')
    plt.close()


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
    if metric_name == EvaluationMetricList.FPR.value:
        metric_for_re = r'False positive rate \(FPR\)'
        metric_name = 'FPR'
    else:
        metric_for_re = metric_name
    df_filtered = df_filtered.rename(
        columns={
            element: re.sub(fr'^{metric_for_re}  {DETECTOR_KEY}={detector_complete_name}(.*) ({ACTIVITY_KEY}=.*)',
                            r'\1', element, count=2)
            for element in df_filtered.columns.tolist()})

    df_detectors = df_filtered.reset_index()
    df_detectors['log type'] = df_detectors['log type'].replace(to_replace=r'([a-zA-Z]+)_\d.(.*).xes.gz',  value=r'\1\2', regex=True)
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

    # print('Usando autorank para calcular os testes estatísticos - exportando gráfico com CD')
    # # df_analysis = df_detectors.set_index('log type', drop=True)
    # logtypes = df_detectors['log type'].unique()
    # for type in logtypes:
    #     simplified_type = type.replace('.xes.gz', '')
    #     df_type = df_filtered.loc[df_filtered.index.str.startswith(simplified_type, na=False)]
    #     # df_type = df_filtered.filter(like=simplified_type, axis=0)
    #     result = autorank(df_type, alpha=0.05, verbose=True)
    #     plot_stats(result)
    #     create_report(result)
    #     latex_table(result)
    #     filename = os.path.join(output_path, f'{dataset_config.dataset_name}_{metric_name}_Nemenyi_CD_by_type_{type}')
    # # plt.savefig(f'{filename}.eps', format='eps', bbox_inches='tight')
    # # plt.savefig(f'{filename}.png', bbox_inches='tight')
    # plt.savefig(f'{filename}.pdf', bbox_inches='tight')
    # plt.close()


def MCDM_analysis(plot_name, folder, file, metrics_MCDM):
    complete_filename = os.path.join(folder, file)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {file}')

    metric_series = {}
    metric_values = {}
    # filter the selected metrics
    for metric_name in metrics_MCDM.keys():
        df_filtered = df.filter(like=metric_name, axis=1)
        df_filtered.index.name = 'log type'

        result = []
        # maintain only the information about detector in the column names
        detector_complete_name = 'adwin_delta'
        detector_name = 'adwin delta'
        df_filtered = df_filtered.rename(
            columns={
                element: re.sub(fr'{metric_name}  {DETECTOR_KEY}={detector_complete_name}(.*) ({ACTIVITY_KEY}=.*)', r'\1',
                                element, count=2)
                for element in df_filtered.columns.tolist()})
        df_detectors = df_filtered.reset_index()
        # df_detectors['log type'] = df_detectors['log type'].replace(to_replace=r'([a-zA-Z]+)_\d.(.*)', value=r'\1\2',
        #                                                             regex=True)
        df_detectors.drop(columns=['log type'], inplace=True)
        metric_series[metric_name] = df_detectors.mean().rename(metric_name)
        metric_values[metric_name] = df_detectors

    plot_pareto_frontier(metric_series[EvaluationMetricList.RECALL], metric_series[EvaluationMetricList.MEAN_DELAY],
                         f'{EvaluationMetricList.RECALL.value} - maximize',
                         f'{EvaluationMetricList.MEAN_DELAY.value} - minimize',
                         metric_series[EvaluationMetricList.RECALL.value].index.to_list(),
                         True, False)


    problem = AdwinDeltaProblem(metric_series[EvaluationMetricList.RECALL], metric_series[EvaluationMetricList.MEAN_DELAY])

    pf_a, pf_b = problem.pareto_front(use_cache=False, flatten=False)

    plt.figure(figsize=(7, 5))
    # plt.scatter(metric_series[EvaluationMetricList.RECALL], metric_series[EvaluationMetricList.MEAN_DELAY], s=30,
    #             facecolors='none', edgecolors='b', label="Solutions")
    plt.scatter(metric_values[EvaluationMetricList.RECALL], metric_values[EvaluationMetricList.MEAN_DELAY], s=30,
                             facecolors='none', edgecolors='b', label="Solutions")
    # plt.plot(pf_a[:, 0], pf_a[:, 1], alpha=0.5, linewidth=2.0, color="red", label="Pareto-front")
    # plt.plot(pf_b[:, 0], pf_b[:, 1], alpha=0.5, linewidth=2.0, color="red")
    plt.title("Objective Space")
    plt.legend()
    plt.show()


def plot_pareto_frontier(Xs, Ys, obj1, obj2, solutions, maxX=True, maxY=True):
    '''Pareto frontier selection process'''
    sorted_list = sorted([[Xs[i], Ys[i]] for i in range(len(Xs))], reverse=maxY)
    pareto_front = [sorted_list[0]]
    for pair in sorted_list[1:]:
        if maxY:
            if pair[1] >= pareto_front[-1][1]:
                pareto_front.append(pair)
        else:
            if pair[1] <= pareto_front[-1][1]:
                pareto_front.append(pair)

    '''Plotting process'''
    plt.scatter(Xs, Ys)
    pf_X = [pair[0] for pair in pareto_front]
    pf_Y = [pair[1] for pair in pareto_front]
    plt.plot(pf_X, pf_Y)
    for a, b, label in zip(pf_X, pf_Y, solutions):
        plt.text(a, b, label)
    plt.xlabel(obj1)
    plt.ylabel(obj2)
    plt.show()


class AdwinDeltaProblem(ElementwiseProblem):
    def __init__(self, recall_series, mean_delay_series):
        super().__init__(n_var=2,
                         n_obj=2,
                         n_ieq_constr=2,
                         xl=np.array([0, 0]),
                         xu=np.array([1.0, mean_delay_series.max()]))
        self.recall = recall_series
        self.mean_delay = mean_delay_series

    def _evaluate(self, x, out, *args, **kwargs):
        f1 = self.recall
        f2 = self.mean_delay

        g1 = x
        g2 = -x

        out["F"] = [f1, f2]
        out["G"] = [g1, g2]

    def _calc_pareto_front(self, flatten=True, *args, **kwargs):
        f_max = lambda f1: np.linspace(f1.max(), f1.min())
        f_min = lambda f1: np.linspace(f1.min(), f1.max())
        f_max = lambda f1: f1
        f_min = lambda f1: f1
        F1_a, F1_b = self.recall, self.mean_delay
        F2_a, F2_b = f_max(F1_a), f_min(F1_b)

        pf_a = np.column_stack([F1_a, F1_b])
        pf_b = np.column_stack([F2_a, F2_b])

        return stack(pf_a, pf_b, flatten=flatten)

    # def _calc_pareto_set(self, *args, **kwargs):
    #     x1_a = self.recall
    #     x1_b = self.mean_delay
    #     x2 = np.zeros(50)
    #
    #     a, b = np.column_stack([x1_a, x2]), np.column_stack([x1_b, x2])
    #     return stack(a, b, flatten=flatten)




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
    generate_ipdd_plot_detectors(plot_name, folder, file, EvaluationMetricList.F_SCORE.value, dataset_config, print_plot_name=False)
    generate_ipdd_plot_detectors(plot_name, folder, file, EvaluationMetricList.FPR.value, dataset_config,
                                 print_plot_name=False)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, EvaluationMetricList.F_SCORE.value, dataset_config, print_plot_name=True)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, EvaluationMetricList.PRECISION.value, dataset_config, print_plot_name=True)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, EvaluationMetricList.RECALL.value, dataset_config, print_plot_name=True)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, EvaluationMetricList.FPR.value, dataset_config,
                                         print_plot_name=True)
    generate_ipdd_plot_detectors_by_type(plot_name, folder, file, EvaluationMetricList.MEAN_DELAY.value, dataset_config,
                                         print_plot_name=True)

    plot_name = 'MCDM analysis for the delta parameter'
    metrics_MCDM = {
        EvaluationMetricList.RECALL.value: MCDM.MAX,
        EvaluationMetricList.MEAN_DELAY.value: MCDM.MIN,
        EvaluationMetricList.FPR.value: MCDM.MIN
    }
    # MCDM_analysis(plot_name, folder, file, metrics_MCDM)
    # delta_analysis(plot_name, folder, file, metrics_MCDM)


def delta_analysis(plot_name, folder, file, metrics_MCDM):
    complete_filename = os.path.join(folder, file)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {file}')

    metric_mean_values = {}
    metric_mean_values_without_ST = {}
    metric_mean_values_ST = {}
    metric_values = {}
    deltas = []
    # filter the selected metrics
    for metric_name in metrics_MCDM.keys():
        df_filtered = df.filter(like=metric_name, axis=1)
        df_filtered.index.name = 'log type'

        if metric_name == EvaluationMetricList.FPR.value:
            metric_for_re = r'False positive rate \(FPR\)'
        else:
            metric_for_re = metric_name

        result = []
        # maintain only the information about detector in the column names
        detector_complete_name = 'adwin_delta'
        detector_name = 'adwin delta'
        df_filtered = df_filtered.rename(
            columns={
                element: re.sub(fr'^{metric_for_re}  {DETECTOR_KEY}={detector_complete_name}(.*) ({ACTIVITY_KEY}=.*)',
                                r'\1',
                                element, count=2)
                for element in df_filtered.columns.tolist()})
        df_detectors = df_filtered.reset_index()
        # df_detectors['log type'] = df_detectors['log type'].replace(to_replace=r'([a-zA-Z]+)_\d.(.*)', value=r'\1\2',
        #                                                             regex=True)
        df_detectors_without_ST = df_detectors.drop(df_detectors[df_detectors['log type'].str.startswith('ST')].index)
        df_detectors_without_ST.drop(columns=['log type'], inplace=True)
        index_ST = df_detectors[df_detectors['log type'].str.startswith('ST')].index.to_list()
        df_detectors_ST = df_detectors[df_detectors.index.isin(index_ST)]
        df_detectors.drop(columns=['log type'], inplace=True)
        df_detectors_ST.drop(columns=['log type'], inplace=True)

        metric_mean_values[metric_name] = df_detectors.mean().rename(metric_name)
        metric_values[metric_name] = df_detectors
        metric_mean_values_without_ST[metric_name] = df_detectors_without_ST.mean().rename(metric_name)
        metric_mean_values_ST[metric_name] = df_detectors_ST.mean().rename(metric_name)
        deltas = list(df_detectors.columns)
        deltas = np.array(deltas, dtype=float)

    # =============================================================================
    # 1) DEFINING THE DATA (delta, recall, mean_delay)
    # =============================================================================
    data_points = []
    for d, r, m, f in zip(deltas, metric_mean_values_without_ST[EvaluationMetricList.RECALL.value],
                       metric_mean_values_without_ST[EvaluationMetricList.MEAN_DELAY.value],
                          metric_mean_values_ST[EvaluationMetricList.FPR.value]):
        data_points.append((d, r, m, f))

    # =============================================================================
    # 2) SEPARATING DATA INTO ARRAYS
    # =============================================================================
    delta_values      = np.array([d[0] for d in data_points])
    recall_values     = np.array([d[1] for d in data_points])
    mean_delay_values = np.array([d[2] for d in data_points])
    fpr_values        = np.array([d[3] for d in data_points])


    # =============================================================================
    # 3) CHOOSE NORMALIZATION (if desired)
    #    Aqui apenas dividindo recall e mean_delay pelos máximos.
    # =============================================================================
    r_min, r_max = recall_values.min(), recall_values.max()
    md_min, md_max = mean_delay_values.min(), mean_delay_values.max()
    fpr_min, fpr_max = fpr_values.min(), fpr_values.max()

    # Exemplo: normalização Min-Max (comentado)
    #recall_norm     = (recall_values - r_min) / (r_max - r_min)
    #mean_delay_norm = (mean_delay_values - md_min) / (md_max - md_min)

    # Exemplo: normalização Max
    recall_norm     = recall_values / r_max
    mean_delay_norm = mean_delay_values / md_max
    fpr_norm        = fpr_values / fpr_max

    # =============================================================================
    # 4) REGRESSION FUNCTIONS
    # =============================================================================
    def power_regression_positive(x, y):
        mask = (x > 0) & (y > 0)
        x_ = x[mask]
        y_ = y[mask]

        lx = np.log(x_)
        ly = np.log(y_)

        b, ln_a = np.polyfit(lx, ly, 1)
        a = np.exp(ln_a)

        def f(x_val):
            return a * (x_val ** b)

        y_pred = f(x)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
        return a, b, r2, f

    def power_regression_negative(x, y):
        mask = (x > 0) & (y > 0)
        x_ = x[mask]
        y_ = y[mask]

        lx = np.log(x_)
        ly = np.log(y_)

        slope, ln_a = np.polyfit(lx, ly, 1)
        b = -slope
        a = np.exp(ln_a)

        def f(x_val):
            return a * (x_val ** (-b))

        y_pred = f(x)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
        return a, b, r2, f

    # =============================================================================
    # 5) MULTI-OBJECTIVE ANALYSIS (PARETO FRONT)
    # =============================================================================
    def is_dominated(solution, solutions_list):
        delta_s, recall_s, delay_s, fpr_s = solution
        for (delta_o, recall_o, delay_o, fpr_o) in solutions_list:
            if (recall_o >= recall_s) and (delay_o <= delay_s) and \
               ((recall_o > recall_s) or (delay_o < delay_s)):
                return True
        return False

    pareto_front = []
    for sol in data_points:
        if not is_dominated(sol, data_points):
            pareto_front.append(sol)

    print("\nSolutions (delta, recall, mean_delay):")
    for (d, r, m, f) in data_points:
        print(f"  delta={d}, recall={r}, mean_delay={m}, fpr={f}")

    print("\nPareto Frontier:")
    for (d, r, m, f) in pareto_front:
        print(f"  delta={d}, recall={r}, mean_delay={m}, fpr={f}")

    # =============================================================================
    # 6) FITTING POWER MODELS: Recall(Norm) -> y=a*x^b, MeanDelay(Norm) -> y=a/x^b
    # =============================================================================
    a_rn, b_rn, r2_rn, f_rn = power_regression_positive(delta_values, recall_norm)
    a_md, b_md, r2_md, f_md = power_regression_negative(delta_values, mean_delay_norm)
    a_fpr, b_fpr, r2_fpr, f_fpr = power_regression_negative(delta_values, fpr_norm)

    # Montamos strings de equações para incluir na legenda
    #   - Recall(Norm):    y = a x^b
    #   - MeanDelay(Norm): y = a / x^b
    recall_norm_label = (f"Recall (Norm=x/max)\n"
                         f"  y={a_rn:.3f}·x^{b_rn:.3f}, R²={r2_rn:.2f}")

    mean_delay_label = (f"Mean delay (Norm=x/max)\n"
                        f"  y={a_md:.3f}/x^{b_md:.3f}, R²={r2_md:.2f}")

    fpr_label = (f"FPR (Norm=x/max)\n"
                        f"  y={a_fpr:.3f}/x^{b_fpr:.3f}, R²={r2_fpr:.2f}")

    # =============================================================================
    # 7) PLOTTING (DATA ONLY), COM LEGENDA DA EQUAÇÃO
    # =============================================================================
    plt.figure(figsize=(8, 5))
    plt.title("Recall (Norm=x/max) and Mean delay(Norm=x/max) vs. Delta")

    # Adicionamos a equação + R² no label dos pontos medidos
    plt.plot(delta_values, recall_norm, '-^', label=recall_norm_label)
    plt.plot(delta_values, mean_delay_norm, '-s', label=mean_delay_label)
    plt.plot(delta_values, fpr_norm, '-s', label=fpr_label)

    plt.xlabel("Delta")
    plt.ylabel("Normalized Value")
    plt.grid(True)

    # A legenda agora exibirá também a equação e o R²
    plt.legend(loc='best')

    # =============================================================================
    # 8) ENCONTRANDO E PLOTTANDO O(S) PONTO(S) DE INTERSEÇÃO (OPCIONAL)
    # =============================================================================
    intersections = []
    for i in range(len(delta_values) - 1):
        x0, y0 = delta_values[i],   recall_norm[i]
        x1, y1 = delta_values[i+1], recall_norm[i+1]

        d0 = mean_delay_norm[i]
        d1 = mean_delay_norm[i+1]

        slope_r = (y1 - y0) / (x1 - x0) if (x1 != x0) else 0
        slope_d = (d1 - d0) / (x1 - x0) if (x1 != x0) else 0
        denom = slope_r - slope_d
        if abs(denom) > 1e-15:
            x_star = x0 + (d0 - y0)/denom
            if min(x0, x1) <= x_star <= max(x0, x1):
                y_star = y0 + slope_r * (x_star - x0)
                intersections.append((x_star, y_star))

    if intersections:
        xi, yi = zip(*intersections)
        plt.scatter(xi, yi, marker='X', c='red', s=100, zorder=5, label="Intersection")
        for (ix, iy) in intersections:
            plt.annotate(
                f"δ={ix:.4f}\nval={iy:.4f}",
                xy=(ix, iy),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                color='red'
            )

    plt.tight_layout()
    plt.show()


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
    dataset2 = TemperatureLogConfiguration()
    dataset3 = RealEventLogConfiguration()


    # run experiments
    # run_massive_adaptive_time(dataset1, evaluate=True)
    # run_massive_adaptive_time(dataset2)
    run_massive_adaptive_time(dataset3)

    # extract sojourn times and generate plots
    # also save information about real drifts
    # based on the attribute Potential_Failure
    # extract_durations_from_log(dataset1)

    # analyze experiments results
    # analyze_IPDD_time()
