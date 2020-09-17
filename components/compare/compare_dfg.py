import json
import os

from networkx import graph_edit_distance, optimize_graph_edit_distance
from networkx.drawing.nx_agraph import read_dot

from app import app
from components.dfg_definitions import get_dfg_filename, dfg_path, get_metrics_filename
from components.info import Info


def calculate_dfg_metrics(current_window, original_file_name):
    map_file1 = get_dfg_filename(original_file_name, current_window - 1)
    map_file2 = get_dfg_filename(original_file_name, current_window)

    filename1 = os.path.join(Info.data_models_path, dfg_path, map_file1)
    filename2 = os.path.join(Info.data_models_path, dfg_path, map_file2)

    if not os.path.exists(filename1):
        app.logger.error(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file1}]')
        return -1

    if not os.path.exists(filename2):
        app.logger.error(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file2}]')
        return -1

    # Obtem os dois dfgs
    g1 = read_dot(filename1)
    g2 = read_dot(filename2)

    # Verifica se o diretório para salvar as metricas existe
    # caso contrário cria
    metrics_path = os.path.join(Info.data_metrics_path, dfg_path)
    if not os.path.exists(metrics_path):
        os.makedirs(metrics_path)

    # Define nome do arquivo de métricas
    filename = get_metrics_filename(original_file_name)
    output_file = os.path.join(metrics_path, filename)

    # Recupera métricas já calculadas
    if os.path.exists(output_file):
        metrics = json.load(open(filename))
    else:
        metrics = {}


    # Calcula novas métricas e adiciona no objeto
    edit_distance = graph_edit_distance(g1, g2)
    app.logger.info(f'Graph edit distance [{map_file1}]-[{map_file2}]: {edit_distance}')
    metrics[f'edit_distance[{current_window}]'] = edit_distance

    # Atualiza arquivo com métricas
    app.logger.info(f'Salvando {output_file}')
    #json.dump(metrics, open(output_file, 'wb'))

    file = open(output_file, 'w')
    file.write(json.dumps(metrics))
    file.close()
