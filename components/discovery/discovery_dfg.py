import os

from graphviz import Source
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization

from components.dfg_definitions import get_dfg_filename, dfg_path


# Função que aplica o algoritmo de descoberta (DFG) para gerar
# o modelo de processo de uma janela e salva no arquivo
def generate_dfg(sub_log, models_path, event_data_original_name, w_count):
    # verifica se o diretório para salvar os DFGs existe caso contrário cria
    dfg_models_path = os.path.join(models_path, dfg_path, event_data_original_name)
    if not os.path.exists(dfg_models_path):
        os.makedirs(dfg_models_path)

    # Gera o dfg do sublog e o grafo correspondente (dot)
    dfg = dfg_discovery.apply(sub_log)
    gviz = dfg_visualization.apply(dfg, log=sub_log)

    # Salva grafo
    output_filename = get_dfg_filename(event_data_original_name, w_count)
    print(f'Saving {dfg_models_path} - {output_filename}')
    Source.save(gviz, filename=output_filename, directory=dfg_models_path)


def get_dfg(models_path, log_name, window):
    map_file = get_dfg_filename(log_name, window)

    dfg_models_path = os.path.join(models_path, dfg_path, log_name)

    if os.path.exists(os.path.join(dfg_models_path, map_file)):
        gviz = Source.from_file(filename=map_file, directory=dfg_models_path)
        return gviz.source

    return """
        digraph  {
          node[style="filled"]
          a ->b->d
          a->c->d
        }
        """
