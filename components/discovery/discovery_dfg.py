import os
from graphviz import Source
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization

from components.dfg_definitions import get_dfg_filename, dfg_path
from components.info import Info


# Função que aplica o algoritmo de descoberta (DFG) para gerar
# o modelo de processo de uma janela e pipsalva no TXT
def generate_dfg(sub_log, event_data_original_name, w_count):
    # verifica se o diretório para salvar os DFGs existe
    # caso contrário cria
    model_path = os.path.join(Info.data_models_path, dfg_path)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    # Gera o dfg do sublog e o grafo correspondente (dot)
    dfg = dfg_discovery.apply(sub_log)
    gviz = dfg_visualization.apply(dfg, log=sub_log)

    # Salva grafo no txt
    output_filename = get_dfg_filename(event_data_original_name, w_count)
    print(f'Salvando {output_filename}')
    Source.save(gviz, filename=output_filename, directory=model_path)


def get_dfg(log_name, window):
    map_file = get_dfg_filename(log_name, window)

    models_path = os.path.join(Info.data_models_path, dfg_path)

    if os.path.exists(os.path.join(models_path, map_file)):
        gviz = Source.from_file(filename=map_file, directory=models_path)
        return gviz.source

    return """
        digraph  {
          node[style="filled"]
          a ->b->d
          a->c->d
        }
        """
