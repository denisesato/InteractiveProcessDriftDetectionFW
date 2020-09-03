import os

from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization

from info import Info

dfg_path = 'dfg'


# Função que aplica o algoritmo de descoberta (DFG) para gerar
# o modelo de processo de uma janela e salva no TXT
def generate_dfg(sub_log, event_data_original_name, w_count):
    # verifica se o diretório para salvar os DFGs existe
    # caso contrário cria
    model_path = os.path.join(Info.data_models_path, dfg_path)
    if os.path.exists(model_path):
        os.makedirs(model_path)

    # Gera o dfg do sublog e o grafo correspondente (dot)
    dfg = dfg_discovery.apply(sub_log)
    gviz = dfg_visualization.apply(dfg, log=sub_log)

    # Salva grafo no txt
    output_file = os.path.join(model_path,
                               f'{event_data_original_name}_dfg_w{w_count}.txt')
    print(f'Saving {output_file}')
    file = open(f'{output_file}', 'w+')
    file.write(str(gviz))
    file.close()


def get_dfg(log_name, window):
    map_file = os.path.join(Info.data_input_path, dfg_path,
                            f'{log_name}_dfg_w{window}.txt')

    gviz = """
        digraph  {
          node[style="filled"]
          a ->b->d
          a->c->d
        }
        """

    if os.path.exists(f'{map_file}'):
        file = open(f'{map_file}', 'r')
        gviz = file.read()
        file.close()

    return gviz
