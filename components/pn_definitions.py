pn_path = 'pn'


def get_model_filename(log_name, window):
    map_file = f'{pn_path}_w{window}.gv'
    return map_file


def get_metrics_filename(log_name, metric_name):
    filename = f'{pn_path}_metrics_{metric_name}.txt'
    return filename