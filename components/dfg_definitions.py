dfg_path = 'dfg'


def get_dfg_filename(log_name, window):
    map_file = f'{dfg_path}_w{window}.gv'
    return map_file


def get_metrics_filename(log_name, metric_name):
    filename = f'{dfg_path}_metrics_{metric_name}.txt'
    return filename