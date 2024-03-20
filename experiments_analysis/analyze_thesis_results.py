import pandas as pd
import os
import matplotlib.pyplot as plt
import re
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator
from pm4py.algo.evaluation.earth_mover_distance import algorithm as emd_evaluator
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.statistics.variants.log import get as variants_module
from pm4py.objects.log.obj import EventLog
from pm4py.objects.log.util import interval_lifecycle
from run_thesis_experiments_massive import Dataset1Configuration, Dataset2Configuration
from scipy import stats
import scikit_posthocs as sp

metric_key = 'metric'
path_key = 'path'
filename_key = 'filename'
series_key = 'series'
delta_key = 'delta'
plots_path = 'plots'


def plot_window_size_grouping_by_logsize(path, df, selected_column, title, dataset, order=None, delta=None, scale=None):
    ############################################################
    # Grouping by logsize
    ############################################################
    df_filtered = df.filter(like=selected_column, axis=1)
    df_filtered.index.name = 'log size'
    if delta:
        df_filtered = df_filtered.filter(like=f'd={delta}', axis=1)

    # maintain only the last number in the column names (window)
    df_plot = df_filtered.rename(
        columns={element: re.sub(r'(\D.*?)(\d+)(?!.*\d)', r'\2', element, count=1)
                 for element in df_filtered.columns.tolist()})

    # sort columns
    ordered_columns = [int(w) for w in df_plot.columns]
    ordered_columns.sort()
    ordered_columns = [str(w) for w in ordered_columns]
    df_plot = df_plot[ordered_columns]

    pattern = '[a-zA-Z]*(\d.*).xes$'
    size = df_plot.index.str.extract(pattern, expand=False)
    df_plot = df_plot.groupby(size).mean().T
    plt.cla()
    plt.clf()
    df_plot.plot(kind='line')
    plt.xlabel('Window size')
    plt.ylabel(selected_column)
    if delta:
        plt.title(f'{title}\nImpact of the window size on the {selected_column} delta={delta}')
    else:
        plt.title(f'{title}\nImpact of the window size on the {selected_column}')
    if 'f_score' in selected_column:
        plt.ylim(0.0, 1.0)
    elif scale:
        plt.ylim(scale[0], scale[1])
    plt.grid(True)
    if order:
        # get handles and labels
        handles, labels = plt.gca().get_legend_handles_labels()
        # specify order of items in legend
        # add legend to plot
        plt.legend([handles[idx] for idx in order], [labels[idx] for idx in order])
    else:
        plt.legend()
    # plt.show()
    output_path = os.path.join(path, plots_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if delta:
        output_filename = f'{title}_{dataset}_{selected_column}_delta{delta}.png'
    else:
        output_filename = f'{title}_{dataset}_{selected_column}.png'
    plt.savefig(os.path.join(output_path, output_filename))
    plt.close()


def plot_window_size_grouping_by_change_pattern(path, df, selected_column, title, dataset, window=None, delta=None):
    ############################################################
    # Grouping by logsize
    ############################################################
    df_filtered = df.filter(like=selected_column, axis=1)
    df_filtered.index.name = 'change pattern'
    if delta:
        df_filtered = df_filtered.filter(like=f'd={delta}', axis=1)

    # maintain only the last number in the column names (window)
    df_plot = df_filtered.rename(
        columns={element: re.sub(r'(\D.*?)(\d+)(?!.*\d)', r'\2', element, count=1)
                 for element in df_filtered.columns.tolist()})

    # filter only the results for the defined window if the parameter is set
    if window:
        df_plot = df_plot.filter(items=[f'{window}'], axis=1)
        window_str = f'window {window}'

    # grouped by change pattern
    regexp = '([a-zA-Z]*)\d.*.xes$'
    change_pattern = df_plot.index.str.extract(regexp, expand=False)
    df_plot = df_plot.groupby(change_pattern).mean()

    # if window is not informed calculate the mean value considering all windows
    if not window:
        df_plot = df_plot.T.mean().to_frame()
        window_str = f'all windows'

    # sort columns
    df_plot['labels'] = df_plot.index.str.lower()
    df_plot = df_plot.sort_values('labels').drop('labels', axis=1)
    plt.cla()
    plt.clf()
    df_plot.plot(kind='bar', legend=None)
    plt.xlabel('Change pattern')
    plt.ylabel(selected_column)
    output_filename = ''
    if delta:
        plt.title(f'{title}\n{selected_column} by change pattern - {window_str} - delta={delta}')
        output_filename = f'change_pattern_{title}_{selected_column}_{window_str}_delta{delta}.png'
    else:
        plt.title(f'{title}\n{selected_column} by change pattern - {window_str}')
        output_filename = f'change_pattern_{title}_{selected_column}_{window_str}.png'
    if 'f_score' in selected_column:
        plt.ylim(0.0, 1.0)
    plt.tight_layout()
    plt.grid(False)
    # plt.show()
    output_path = os.path.join(path, plots_path)
    if not os.path.join(output_path):
        os.makedirs(output_path)
    plt.savefig(os.path.join(output_path, output_filename))
    plt.close()


def analyze_metrics_ipdd(input_path, filename, dataset_config, selected_column, title, dataset, scale=None):
    complete_filename = os.path.join(input_path, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    ############################################################
    # Impact of the window size on the metrics
    ############################################################
    order = None
    if dataset_config.order_legend:
        order = dataset_config.order_legend
    for d in dataset_config.deltas:
        plot_window_size_grouping_by_logsize(input_path, df, selected_column, title, dataset, order, d, scale)
        # plot_window_size_grouping_by_change_pattern(df, selected_column, title, delta=d)
        # plot_window_size_grouping_by_change_pattern(df, selected_column, title)


def ipdd_plot_change_pattern(input_path, filename, selected_column, title, dataset, winsize, delta):
    complete_filename = os.path.join(input_path, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    ############################################################
    # Impact of the window size on the metrics
    ############################################################
    plot_window_size_grouping_by_change_pattern(input_path, df, selected_column, title, dataset, window=winsize, delta=delta)


def analyze_metrics(dataset_config, input_path, filename, selected_column, title, dataset):
    complete_filename = os.path.join(input_path, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    ############################################################
    # Impact of the window size on the metrics
    ############################################################
    order = None
    if dataset_config.order_legend:
        order = dataset_config.order_legend
    plot_window_size_grouping_by_logsize(input_path, df, selected_column, title, dataset, order)
    plot_window_size_grouping_by_change_pattern(input_path, df, selected_column, title, dataset)


def analyze_dataset_trace(dataset_config, dataset_name, scale=None):
    f_score_column_ipdd = 'f_score'
    mean_delay_column_ipdd = 'mean_delay'

    ipdd_quality_trace_path = f'data/experiments_results/IPDD_controlflow_adaptive//detection_on_quality_metrics_trace_by_trace//{dataset_name}'
    ipdd_quality_trace_filename = 'metrics_experiments_quality_metrics_trace_by_trace.xlsx'
    analyze_metrics_ipdd(ipdd_quality_trace_path, ipdd_quality_trace_filename, dataset_config, f_score_column_ipdd,
                         'Adaptive IPDD Trace by Trace', dataset_name)
    analyze_metrics_ipdd(ipdd_quality_trace_path, ipdd_quality_trace_filename, dataset_config, mean_delay_column_ipdd,
                         'Adaptive IPDD Trace by Trace', dataset_name, scale)


def analyze_dataset_windowing(dataset_config, dataset_name, scale=None):
    f_score_column_ipdd = 'f_score'
    mean_delay_column_ipdd = 'mean_delay'

    ipdd_quality_windowing_path = f'data/experiments_results/IPDD_controlflow_adaptive//detection_on_quality_metrics_fixed_window//{dataset_name}'
    ipdd_quality_windowing_filename = 'metrics_experiments_quality_metrics_fixed_window.xlsx'
    analyze_metrics_ipdd(ipdd_quality_windowing_path, ipdd_quality_windowing_filename, dataset_config,
                         f_score_column_ipdd,
                         'Adaptive IPDD Windowing', dataset_name)
    analyze_metrics_ipdd(ipdd_quality_windowing_path, ipdd_quality_windowing_filename, dataset_config,
                         mean_delay_column_ipdd,
                         'Adaptive IPDD Windowing', dataset_name, scale)


def analyze_dataset_model_simmilarity(dataset_config, dataset_name):
    f_score_column_ipdd = 'f_score'
    mean_delay_column_ipdd = 'mean_delay'

    ipdd_model_similarity_path = f'data/experiments_results/IPDD_controlflow_adaptive//detection_on_model_similarity_fixed_window//{dataset_name}'
    ipdd_model_similarity_filename = 'metrics_experiments_model_similarity_fixed_window.xlsx'
    analyze_metrics_ipdd(ipdd_model_similarity_path, ipdd_model_similarity_filename, dataset_config,
                         f_score_column_ipdd,
                         'IPDD Adaptive - Model Similarity Approach', dataset_name)
    analyze_metrics_ipdd(ipdd_model_similarity_path, ipdd_model_similarity_filename, dataset_config,
                         mean_delay_column_ipdd,
                         'IPDD Adaptive - Model Similarity Approach', dataset_name)


def analyze_dataset_apromore(dataset_config, dataset_name):
    apromore_path = f'data/experiments_results/Apromore/experimento2/{dataset_name}'
    apromore_filename = 'metrics_results_prodrift.xlsx'
    analyze_metrics(dataset_config, apromore_path, apromore_filename, 'f_score awin', 'AWIN', dataset_name)
    analyze_metrics(dataset_config, apromore_path, apromore_filename, 'mean_delay awin', 'AWIN', dataset_name)
    analyze_metrics(dataset_config, apromore_path, apromore_filename, 'f_score fwin', 'FWIN', dataset_name)
    analyze_metrics(dataset_config, apromore_path, apromore_filename, 'mean_delay fwin', 'FWIN', dataset_name)


def analyze_dataset_vdd(dataset_config, dataset_name):
    vdd_path = f'data/experiments_results/VDD/experimento2/{dataset_name}/output_console'
    vdd_filename = 'metrics_results_vdd.xlsx'
    # We decided to use the CLUSTER configuration, which is the one that reported the best results
    # in the author's paper
    # analyze_metrics(dataset_config, vdd_path, vdd_filename, 'f_score all', 'ALL', dataset_name)
    # analyze_metrics(dataset_config, vdd_path, vdd_filename, 'mean_delay all', 'ALL', dataset_name)
    analyze_metrics(dataset_config, vdd_path, vdd_filename, 'f_score cluster', 'CLUSTER', dataset_name)
    analyze_metrics(dataset_config, vdd_path, vdd_filename, 'mean_delay cluster', 'CLUSTER', dataset_name)


def generate_plot_tools(output_folder, approaches, metric_name, dataset, plot_name=None, scale=None):
    # firstly enrich dict with dataframe from excel
    for key in approaches.keys():
        input_path = approaches[key][path_key]
        filename = approaches[key][filename_key]
        complete_filename = os.path.join(input_path, filename)
        df = pd.read_excel(complete_filename, index_col=0)
        df.index.name = 'logname'
        print(f'Reading file {filename}')
        # filter the selected metric
        df_filtered = df.filter(like=approaches[key][metric_key], axis=1)
        df_filtered.index.name = 'log size'
        # if IPDD filter the selected delta
        if 'IPDD' in key:
            df_filtered = df_filtered.filter(like=f'd={approaches[key][delta_key]}', axis=1)
        # maintain only the last number in the column names (window)
        df_filtered = df_filtered.rename(
            columns={element: re.sub(r'(\D.*?)(\d+)(?!.*\d)', r'\2', element, count=1)
                     for element in df_filtered.columns.tolist()})
        series = df_filtered.mean()
        series.name = key
        approaches[key][series_key] = series

    # combine all approaches into one dataframe
    df_plot = pd.concat([approaches[approach][series_key] for approach in approaches.keys()], axis=1)
    df_plot.sort_index(axis=1, inplace=True)
    plt.cla()
    plt.clf()
    df_plot.plot(kind='line')
    plt.xlabel('Window size')
    plt.ylabel(metric_name)
    output_filename = ''
    if plot_name:
        plt.title(plot_name)
        output_filename = f'tools_{plot_name}_{dataset}.png'
    else:
        plt.title(f'Impact of the window size on the {metric_name}')
        output_filename = f'tools_window_size_impact_{metric_name}_{dataset}.png'
    if 'f_score' in metric_name:
        plt.ylim(0.0, 1.0)
    elif scale:
        plt.ylim(scale[0], scale[1])
    plt.grid(True)
    plt.legend()
    # plt.show()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(os.path.join(output_folder, output_filename))
    plt.close


def generate_ipdd_plot_deltas(approach, folder, filename, metric_name, deltas, dataset):
    complete_filename = os.path.join(folder, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    # filter the selected metric
    df_filtered = df.filter(like=metric_name, axis=1)
    df_filtered.index.name = 'log size'
    series = []
    for d in deltas:
        df_delta = df_filtered.filter(like=f'd={d}', axis=1)
        # maintain only the last number in the column names (window)
        df_delta = df_delta.rename(
            columns={element: re.sub(r'(\D.*?)(\d+)(?!.*\d)', r'\2', element, count=1)
                     for element in df_delta.columns.tolist()})
        s = df_delta.mean()
        s.name = f'delta {d}'
        series.append(s)

    # combine all approaches into one dataframe
    df_plot = pd.concat([s for s in series], axis=1)
    df_plot.sort_index(axis=1, inplace=True)
    plt.cla()
    plt.clf()
    df_plot.plot(kind='line')
    plt.xlabel('Window size')
    plt.ylabel(metric_name)
    plt.title(f'{approach}\nImpact of the delta on the {metric_name}')
    if 'f_score' in metric_name:
        plt.ylim(0.0, 1.0)
    plt.grid(True)
    plt.legend()
    # plt.show()
    output_path = os.path.join(folder, plots_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_filename = os.path.join(output_path, f'delta_analysis_{metric_name}_{approach}_{dataset}.png')
    plt.savefig(output_filename)
    plt.close()


def generate_plot_approach(approach, folder, filename, metric_name):
    complete_filename = os.path.join(folder, filename)
    df = pd.read_excel(complete_filename, index_col=0)
    df.index.name = 'logname'
    print(f'Reading file {filename}')
    # filter the selected metric
    df_filtered = df.filter(like=metric_name, axis=1)
    df_filtered.index.name = 'log size'

    # combine all approaches into one dataframe
    df_plot = df_filtered.copy()
    df_plot.sort_index(axis=1, inplace=True)
    plt.cla()
    plt.clf()
    df_plot.plot(kind='line')
    plt.xlabel('Window size')
    plt.ylabel(metric_name)
    plt.title(f'{approach}\nImpact of the window size on the {metric_name}')
    if 'f_score' in metric_name:
        plt.ylim(0.0, 1.0)
    plt.grid(True)
    plt.legend()
    plt.show()


def compare_tools_dataset(output_folder, dataset_name, metric_name, scale=None):
    approaches = {
        'Adaptive IPDD Trace by Trace':
            {
                metric_key: metric_name,
                path_key: f'data/experiments_results' \
                          f'/IPDD_controlflow_adaptive/detection_on_quality_metrics_trace_by_trace//{dataset_name}',
                filename_key: 'metrics_experiments_quality_metrics_trace_by_trace.xlsx',
                delta_key: 0.002
            },
        'Adaptive IPDD Windowing':
            {
                metric_key: metric_name,
                path_key: f'data/experiments_results' \
                          f'/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window//{dataset_name}',
                filename_key: 'metrics_experiments_quality_metrics_fixed_window.xlsx',
                delta_key: 0.002
            },
        'Apromore ProDrift AWIN':
            {
                metric_key: f'{metric_name} awin',
                path_key: f'data/experiments_results/Apromore/experimento2/{dataset_name}',
                filename_key: 'metrics_results_prodrift.xlsx'
            },
        'Apromore ProDrift FWIN':
            {
                metric_key: f'{metric_name} fwin',
                path_key: f'data/experiments_results/Apromore/experimento2/{dataset_name}',
                filename_key: 'metrics_results_prodrift.xlsx'
            },
        'VDD':
            {
                metric_key: f'{metric_name} cluster',
                path_key: f'data/experiments_results/VDD/experimento2/{dataset_name}/output_console',
                filename_key: 'metrics_results_VDD.xlsx'
            },
    }
    generate_plot_tools(output_folder, approaches, metric_name, dataset_name, scale=scale)


def friedman_tools(output_folder, dataset_name, metric_name, windows):
    approaches = {
        'Adaptive IPDD Trace by Trace':
            {
                metric_key: metric_name,
                path_key: f'data/experiments_results' \
                          f'/IPDD_controlflow_adaptive/detection_on_quality_metrics_trace_by_trace/{dataset_name}',
                filename_key: 'metrics_experiments_quality_metrics_trace_by_trace.xlsx',
                delta_key: 0.002
            },
        'Adaptive IPDD Windowing':
            {
                metric_key: metric_name,
                path_key: f'data/experiments_results' \
                          f'/IPDD_controlflow_adaptive//detection_on_quality_metrics_fixed_window//{dataset_name}',
                filename_key: 'metrics_experiments_quality_metrics_fixed_window.xlsx',
                delta_key: 0.002
            },
        'Apromore ProDrift AWIN':
            {
                metric_key: f'{metric_name} awin',
                path_key: f'data/experiments_results/Apromore/experimento2/{dataset_name}',
                filename_key: 'metrics_results_prodrift.xlsx'
            },
        'Apromore ProDrift FWIN':
            {
                metric_key: f'{metric_name} fwin',
                path_key: f'data/experiments_results/Apromore/experimento2/{dataset_name}',
                filename_key: 'metrics_results_prodrift.xlsx'
            },
        'VDD':
            {
                metric_key: f'{metric_name} cluster',
                path_key: f'data/experiments_results/VDD/experimento2/{dataset_name}/output_console',
                filename_key: 'metrics_results_VDD.xlsx'
            },
    }

    # firstly enrich dict with dataframe from excel
    for key in approaches.keys():
        input_path = approaches[key][path_key]
        filename = approaches[key][filename_key]
        complete_filename = os.path.join(input_path, filename)
        df = pd.read_excel(complete_filename, index_col=0)
        df.index.name = 'logname'
        # print(f'Reading file {filename}')
        # filter the selected metric
        df_filtered = df.filter(like=approaches[key][metric_key], axis=1)
        df_filtered.index.name = 'log size'
        # if IPDD filter the selected delta
        if 'IPDD' in key:
            df_filtered = df_filtered.filter(like=f'd={approaches[key][delta_key]}', axis=1)
        # maintain only the last number in the column names (window)
        df_filtered = df_filtered.rename(
            columns={element: re.sub(r'(\D.*?)(\d+)(?!.*\d)', r'\2', element, count=1)
                     for element in df_filtered.columns.tolist()})
        series = df_filtered.mean()
        series = series.filter(items=windows)
        series.name = key
        approaches[key][series_key] = series


    # compare samples
    stat, p = stats.friedmanchisquare(
        approaches['Adaptive IPDD Trace by Trace'][series_key],
        approaches['Adaptive IPDD Windowing'][series_key],
        approaches['Apromore ProDrift AWIN'][series_key],
        approaches['Apromore ProDrift FWIN'][series_key],
        approaches['VDD'][series_key]
    )
    print(f'Friedman results for {metric_name} {dataset_name}')
    print('Statistics=%.3f, p=%.3f' % (stat, p))
    # interpret
    alpha = 0.05
    if p > alpha:
        print('Same distributions (fail to reject H0)')
    else:
        print('Different distributions (reject H0)')
        # combine all approaches into one dataframe
        df_tools = pd.concat([approaches[approach][series_key] for approach in approaches.keys()], axis=1)
        result = sp.posthoc_nemenyi_friedman(df_tools)
        filename = os.path.join(output_folder, f'{dataset_name}_{metric_name}_data.xlsx')
        df_tools.to_excel(filename)
        # print(f'Posthoc Nemenyi Friedman: {result}')
        plt.cla()
        plt.clf()
        heatmap_args = {'linewidths': 0.25, 'linecolor': '0.5', 'clip_on': False, 'square': True,
                        'cbar_ax_bbox': [0.80, 0.35, 0.04, 0.3]}
        sp.sign_plot(result, **heatmap_args)
        # plt.title(f'Posthoc Nemenyi Friedman {metric_name} {dataset_name}', loc='left')
        filename = os.path.join(output_folder, f'{dataset_name}_{metric_name}.png')
        plt.savefig(filename, bbox_inches='tight')


def extract_sample_logs():
    path = 'data/input/logs/controlflow/dataset1'
    interval = 500
    variant = xes_importer.Variants.ITERPARSE
    parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
    original_eventlog = xes_importer.apply(os.path.join(path, 'cb5k.xes'), variant=variant, parameters=parameters)
    eventlog = interval_lifecycle.to_interval(original_eventlog)
    base_sample_log = EventLog(eventlog[0:interval])
    output_path = 'data/input/logs/controlflow/sample_logs'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # save base sample log
    xes_exporter.apply(base_sample_log, os.path.join(output_path, 'base.xes'))
    change_patterns = [
        'cb', 'cd', 'cf', 'cm', 'cp', 'IOR', 'IRO', 'lp', 'OIR', 'ORI', 'pl',
        'pm', 're', 'RIO', 'ROI', 'rp', 'sw'
    ]
    for code in change_patterns:
        original_eventlog = xes_importer.apply(os.path.join(path, f'{code}5k.xes'), variant=variant,
                                               parameters=parameters)
        eventlog = interval_lifecycle.to_interval(original_eventlog)
        changed_sample_log = EventLog(eventlog[interval:2 * interval])
        xes_exporter.apply(changed_sample_log, os.path.join(output_path, f'{code}.xes'))


def check_emd_between_sample_logs():
    path = 'data/input/logs/controlflow/sample_logs'
    log = xes_importer.apply(os.path.join(path, 'base.xes'))
    language_base = variants_module.get_language(log)
    change_patterns = [
        'cb', 'cd', 'cf', 'cm', 'cp', 'IOR', 'IRO', 'lp', 'OIR', 'ORI', 'pl',
        'pm', 're', 'RIO', 'ROI', 'rp', 'sw'
    ]
    print(f'EMD:')
    for code in change_patterns:
        log = xes_importer.apply(os.path.join(path, f'{code}.xes'))
        language_change_pattern = variants_module.get_language(log)
        emd = emd_evaluator.apply(language_base, language_change_pattern)
        print(f'{code}: {emd}')


if __name__ == '__main__':
    # I suggest to only uncomment one analysis per execution
    ######################################################################
    # EVALUATION OF THE IPDD ADAPTIVE ON SYNTHETIC EVENT LOGS
    ######################################################################
    ######################################################################
    # ANALYSIS 1 - Trace by trace approach
    # Impact of the delta and window size on the accuracy
    ######################################################################
    deltas = [0.002, 0.05, 0.1, 0.3]
    plot_name = 'Adaptive IPDD Trace by Trace'
    folder = 'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_trace_by_trace/dataset1'
    file = 'metrics_experiments_quality_metrics_trace_by_trace.xlsx'
    generate_ipdd_plot_deltas(plot_name, folder, file, "f_score", deltas, 'dataset1')

    plot_name = 'Adaptive IPDD Trace by Trace'
    folder = 'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_trace_by_trace/dataset2'
    file = 'metrics_experiments_quality_metrics_trace_by_trace.xlsx'
    generate_ipdd_plot_deltas(plot_name, folder, file, "f_score", deltas, 'dataset2')

    ######################################################################
    # ANALYSIS 2 - Trace by Trace approach
    # F-score and mean delay for all configurations to select the best
    # configuration
    ######################################################################
    scale = [0.0, 70.0]
    dataset_config = Dataset1Configuration()
    analyze_dataset_trace(dataset_config, "dataset1", scale)
    dataset_config = Dataset2Configuration()
    analyze_dataset_trace(dataset_config, "dataset2", scale)

    ######################################################################
    # ANALYSIS 3 - Trace by Trace approach
    # Accuracy per change pattern
    # Best parameter configuration window size - 75 0 delta 0.002
    ######################################################################
    dataset_name = "dataset1"
    ipdd_quality_trace_path = f'data/experiments_results/IPDD_controlflow_adaptive//detection_on_quality_metrics_trace_by_trace//{dataset_name}'
    ipdd_quality_trace_filename = 'metrics_experiments_quality_metrics_trace_by_trace.xlsx'
    metric = 'f_score'
    ipdd_plot_change_pattern(ipdd_quality_trace_path, ipdd_quality_trace_filename, metric,
                             'Adaptive IPDD Trace by Trace', dataset_name,
                             75, 0.002)
    dataset_name = "dataset2"
    ipdd_quality_trace_path = f'data/experiments_results/IPDD_controlflow_adaptive//detection_on_quality_metrics_trace_by_trace//{dataset_name}'
    ipdd_quality_trace_filename = 'metrics_experiments_quality_metrics_trace_by_trace.xlsx'
    metric = 'f_score'
    ipdd_plot_change_pattern(ipdd_quality_trace_path, ipdd_quality_trace_filename, metric,
                             'Adaptive IPDD Trace by Trace', dataset_name,
                             75, 0.002)

    ######################################################################
    # ANALYSIS 4 - Trace by Trace approach
    # Investigating pattern cd
    # Evaluating simplicity of the change patterns
    ######################################################################
    path = 'data/input/logs/controlflow/models'
    files = [
        'base', 'cb', 'cd', 'cf', 'cm', 'cp', 'IOR', 'IRO', 'lp', 'OIR', 'ORI', 'pl',
        'pm', 're', 'RIO', 'ROI', 'rp', 'sw'
    ]
    print(f'Simplicity information:')
    for f in files:
        net, im, fm = pnml_importer.apply(os.path.join(path, f'{f}.pnml'))
        simp = simplicity_evaluator.apply(net)
        print(f'{f}: {simp}')

    ######################################################################
    # ANALYSIS 1 - Windowing approach
    # Impact of the delta and window size on the accuracy
    ######################################################################
    deltas = [0.002, 0.05, 0.1, 0.3]
    plot_name = 'Adaptive IPDD Windowing'
    folder = 'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window/dataset1'
    file = 'metrics_experiments_quality_metrics_fixed_window.xlsx'
    generate_ipdd_plot_deltas(plot_name, folder, file, "f_score", deltas, 'dataset1')

    plot_name = 'Adaptive IPDD Windowing'
    folder = 'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window/dataset2'
    file = 'metrics_experiments_quality_metrics_fixed_window.xlsx'
    generate_ipdd_plot_deltas(plot_name, folder, file, "f_score", deltas, 'dataset2')

    ######################################################################
    # ANALYSIS 2 - Windowing approach
    # F-score and mean delay for all configurations to select the best
    # configuration
    ######################################################################
    scale = [0.0, 110.0]
    dataset_config = Dataset1Configuration()
    analyze_dataset_windowing(dataset_config, "dataset1", scale)
    dataset_config = Dataset2Configuration()
    analyze_dataset_windowing(dataset_config, "dataset2", scale)

    ######################################################################
    # ANALYSIS 3 - Windowing approach
    # Accuracy per change pattern
    # Best parameter configuration window size - 75 0 delta 0.002
    ######################################################################
    dataset_name = "dataset1"
    ipdd_quality_window_path = f'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window//{dataset_name}'
    ipdd_quality_window_filename = 'metrics_experiments_quality_metrics_fixed_window.xlsx'
    metric = 'f_score'
    ipdd_plot_change_pattern(ipdd_quality_window_path, ipdd_quality_window_filename, metric,
                             'Adaptive IPDD Windowing', dataset_name, 175, 0.002)
    dataset_name = "dataset2"
    ipdd_quality_window_path = f'data/experiments_results/IPDD_controlflow_adaptive/detection_on_quality_metrics_fixed_window//{dataset_name}'
    ipdd_quality_window_filename = 'metrics_experiments_quality_metrics_fixed_window.xlsx'
    metric = 'f_score'
    ipdd_plot_change_pattern(ipdd_quality_window_path, ipdd_quality_window_filename, metric,
                             'Adaptive IPDD Windowing', dataset_name, 175, 0.002)

    ######################################################################
    # Comparing tools using the synthetic event logs
    ######################################################################
    output_folder = 'data/experiments_results/analysis/comparative_analysis'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    scale = [0.0, 360.0]
    compare_tools_dataset(output_folder, "dataset1", 'f_score')
    compare_tools_dataset(output_folder, "dataset1", 'mean_delay', scale=scale)
    compare_tools_dataset(output_folder, "dataset2", 'f_score')
    compare_tools_dataset(output_folder, "dataset2", 'mean_delay')
    windows = [str(i) for i in range(50, 301, 25)]
    friedman_tools(output_folder, "dataset1", "f_score", windows)
    friedman_tools(output_folder, "dataset1", "mean_delay", windows)
    friedman_tools(output_folder, "dataset2", "f_score", windows)
    friedman_tools(output_folder, "dataset2", "mean_delay", windows)

    ######################################################################
    # Plot Apromore results
    ######################################################################
    dataset_config = Dataset1Configuration()
    analyze_dataset_apromore(dataset_config, "dataset1")
    dataset_config = Dataset2Configuration()
    analyze_dataset_apromore(dataset_config, "dataset2")

    ######################################################################
    # Plot VDD results
    ######################################################################
    dataset_config = Dataset1Configuration()
    analyze_dataset_vdd(dataset_config, "dataset1")
    dataset_config = Dataset2Configuration()
    analyze_dataset_vdd(dataset_config, "dataset2")