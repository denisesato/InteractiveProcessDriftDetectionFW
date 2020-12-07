import os

from graphviz import Source
from pm4py.algo.discovery.inductive import algorithm as inductive_miner

from components.discovery.discovery import Discovery
from components.pn_definitions import get_model_filename, pn_path
from pm4py.visualization.petrinet import visualizer as pn_visualizer


class DiscoveryPn(Discovery):
    # Função que aplica o algoritmo de descoberta para gerar
    # o modelo de processo de uma janela e salva no arquivo
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count):
        # verifica se o diretório para salvar os DFGs existe caso contrário cria
        dfg_models_path = os.path.join(models_path, pn_path, event_data_original_name)
        if not os.path.exists(dfg_models_path):
            os.makedirs(dfg_models_path)

        # Gera a petri net do sublog e o grafo correspondente (dot)
        net, initial_marking, final_marking = inductive_miner.apply(sub_log)
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)

        # Salva grafo
        output_filename = get_model_filename(event_data_original_name, w_count)
        print(f'Saving {dfg_models_path} - {output_filename}')
        Source.save(gviz, filename=output_filename, directory=dfg_models_path)

    def get_process_model(self, models_path, log_name, window):
        map_file = get_model_filename(log_name, window)

        pn_models_path = os.path.join(models_path, pn_path, log_name)

        if os.path.exists(os.path.join(pn_models_path, map_file)):
            gviz = Source.from_file(filename=map_file, directory=pn_models_path)
            return gviz.source

        return """
            digraph  {
              node[style="filled"]
              a ->b->d
              a->c->d
            }
            """
