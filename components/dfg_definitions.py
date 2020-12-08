import os


class DfgDefinitions:
    def __init__(self):
        self.dfg_path = 'dfg'
        self.metrics = {'nodes_similarity': 'DfgNodesSimilarityMetric',
                        'edges_similarity': 'DfgEdgesSimilarityMetric'}

    def get_metrics(self):
        return self.metrics

    def get_model_filename(self, log_name, window):
        map_file = f'{self.dfg_path}_w{window}.gv'
        return map_file

    def get_metrics_filename(self, log_name, metric_name):
        filename = f'{self.dfg_path}_metrics_{metric_name}.txt'
        return filename

    def get_metrics_path(self, generic_metrics_path):
        path = os.path.join(generic_metrics_path, self.dfg_path)
        return path

    def get_models_path(self, generic_models_path, original_filename):
        dfg_models_path = os.path.join(generic_models_path, self.dfg_path, original_filename)
        return dfg_models_path

    def get_metrics_list(self):
        return self.metrics
