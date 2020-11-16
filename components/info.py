import os


class Info:
    pathname = ''

    @staticmethod
    def get_data_input_path():
        data_input_path = os.path.join('data', 'input')
        return data_input_path

    @staticmethod
    def get_data_models_path():
        data_models_path = os.path.join('data', 'models')
        return data_models_path

    @staticmethod
    def get_data_metrics_path():
        data_metrics_path = os.path.join('data', 'metrics')
        return data_metrics_path
