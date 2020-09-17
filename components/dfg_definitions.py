dfg_path = 'dfg'


def get_dfg_filename(log_name, window):
    map_file = f'{log_name}_{dfg_path}_w{window}.gv'
    return map_file


def get_metrics_filename(log_name):
    filename = f'{log_name}_{dfg_path}_metrics.txt'
    return filename