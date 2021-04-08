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

import networkx

from components.compare.compare_dfg import DfgEdgesSimilarityMetric, DfgEditDistanceMetric, DfgNodesSimilarityMetric


class DfgDefinitions:
    def __init__(self):
        self.dfg_path = 'dfg'
        # define quais métricas serão calculadas
        #self.metrics = {'nodes_similarity': 'DfgNodesSimilarityMetric',
        #                'edges_similarity': 'DfgEdgesSimilarityMetric',
        #                'edit_distance': 'DfgEditDistanceMetric'}

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

    @staticmethod
    def metrics_factory(class_name, window, name, m1, m2):
        # define todas as métricas existentes, mas só serão calculadas as definidas por tipo de
        # modelo de processo - Acho que isso deveria ficar nas definições de cada tipo
        classes = {
            'DfgEdgesSimilarityMetric': DfgEdgesSimilarityMetric(window, name, m1, m2),
            'DfgEditDistanceMetric': DfgEditDistanceMetric(window, name, m1, m2),
            'DfgNodesSimilarityMetric': DfgNodesSimilarityMetric(window, name, m1, m2),
        }
        return classes[class_name]

    @staticmethod
    def get_model_from_file(complete_filename, filename, filepath):
        model = networkx.drawing.nx_agraph.read_dot(complete_filename)
        return model

        #with open(complete_filename, 'rt') as f:
        #    model = nx.drawing.nx_agraph.read_dot(f)
        #gviz = Source.from_file(filename=filename, directory=filepath)
        #return gviz
        #print(f'Try to read [{complete_filename}]')
        #g = networkx.drawing.nx_pydot.read_dot(complete_filename)
        #return g

        # várias tentativas frustradas
        #gviz = Source.from_file(filename=filename, directory=filepath)
        #f = open(complete_filename, 'rt')
        #graph_data = f.read()
        #f.close()
        #graph = agraph.graph_from_dot_data(graph_data)
        #G = pgv.AGraph(complete_filename)
        #graphs = agraph.graph_from_dot_data(gviz.source)
        # G = AGraph()
        # G.read(filename1)
        # G.close()
        # G.from_string(gviz1.source)
        # G.clear()
        # G.close()
        # graph1 = nx.nx_agraph.from_agraph(G)

        # graph1 = nx.nx_agraph.read_dot(filename1)
        # graph1 = nx.nx_pydot.read_dot(filename1)
        # self.g1 = nx.drawing.nx_agraph.read_dot(filename1)
        # G = AGraph(string=graph_data)
        # graph1 = nx.nx_agraph.from_agraph(G)
        # G.clear()
        # G.close()
        # G = None

        # gviz1.close()
        # self.g1 = nx.drawing.nx_agraph.read_dot(filename1)
