import os

from networkx import graph_edit_distance
from networkx.drawing.nx_agraph import read_dot
from components.dfg_definitions import get_dfg_filename, dfg_path
from components.info import Info


def compare_dfg(log_name, current_window):
    if current_window > 1:
        map_file1 = get_dfg_filename(log_name, current_window-1)
        map_file2 = get_dfg_filename(log_name, current_window)

        filename1 = os.path.join(Info.data_models_path, dfg_path, map_file1)
        filename2 = os.path.join(Info.data_models_path, dfg_path, map_file2)

        if not os.path.exists(filename1):
            print(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file1}]')
            return

        if not os.path.exists(filename2):
            print(f'[compare_dfg]: Erro tentando acessar dfg do arquivo [{map_file2}]')
            return

        g1 = read_dot(filename1)
        g2 = read_dot(filename2)

        edit_distance = graph_edit_distance(g1, g2)
        print(f'Graph edit distance [{map_file1}]-[{map_file2}]: {edit_distance}')
