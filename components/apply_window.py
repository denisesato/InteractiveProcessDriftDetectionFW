import os
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.log import EventStream
from pm4py.objects.log.importer.xes import importer as xes_importer
from datetime import datetime
from datetime import timedelta

from components.compare.compare_dfg import compare_dfg
from components.info import Info
from components.discovery.discovery_dfg import generate_dfg, get_dfg, get_dfg_filename


class WindowType:
    TRACE = 'TRACE'
    EVENT = 'EVENTO'


class WindowUnity:
    UNITY = 'ITEM'
    HOUR = 'HORA'
    DAY = 'DIA'



# por enquando o nome do arquivo de log ainda está fixo no código
event_data_path = Info.data_input_path
#event_data_original_name = 'cb2.5k.xes'


def apply_window_unit(event_data, window_type, window_size, original_file_name):
    w_count = 1
    for i, item in enumerate(event_data):
        # window checkpoint
        if i > 0 and i % window_size == 0:
            if window_type == WindowType.EVENT:
                # Gera o sublog da janela
                window = EventStream(event_data[(i - window_size):i])
                sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
            elif window_type == WindowType.TRACE:
                sub_log = event_data[(i - window_size):i]
            else:
                print(f'Tipo de janela informado incorretamente: {window_type}.')

            # Gera o dfg e salva
            generate_dfg(sub_log, original_file_name, w_count)

            # Incrementa janela
            w_count += 1
    return w_count


def apply_window_time(event_data, window_type, window_size, original_file_name):
    w_count = 1
    initial_window_index = -1
    for i, item in enumerate(event_data):
        if window_type == WindowType.EVENT:
            timestamp_aux = datetime.timestamp(item['time:timestamp'])
        elif window_type == WindowType.TRACE:
            # utiliza a data do primeiro evento do trace
            timestamp_aux = datetime.timestamp(item[0]['time:timestamp'])
        else:
            print(f'Tipo de janela informado incorretamente: {window_type}.')

        # inicializa o tempo e o índice inicial da janela
        if initial_window_index == -1:
            initial_window_index = i
            initial_timestamp = timestamp_aux

        # window checkpoint
        actual_timestamp = timestamp_aux
        time_difference = actual_timestamp - initial_timestamp
        # converte para horas
        time_difference = time_difference / 1000 / 60 / 60
        if time_difference > window_size:
            if window_type == WindowType.EVENT:
                # Gera o sublog da janela
                window = EventStream(event_data[initial_window_index:i])
                sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
            elif window_type == WindowType.TRACE:
                sub_log = event_data[initial_window_index:i]
            else:
                print(f'Tipo de janela informado incorretamente: {window_type}.')

            # Gera o dfg e salva
            generate_dfg(sub_log, original_file_name, w_count)

            w_count += 1

            # reinicializa variáveis para nova janela
            initial_window_index = i
            initial_timestamp = datetime.timestamp(item['time:timestamp'])
    return w_count


def apply_window_day(event_data, window_type, window_size, original_file_name):
    w_count = 1
    initial_window_index = -1
    for i, item in enumerate(event_data):
        if window_type == WindowType.EVENT:
            date_aux = item['time:timestamp']
        elif window_type == WindowType.TRACE:
            # utiliza a data do primeiro evento do trace
            date_aux = item[0]['time:timestamp']
        else:
            print(f'Tipo de janela informado incorretamente: {window_type}.')

        # inicializa o tempo e o índice inicial da janela
        if initial_window_index == -1:
            initial_window_index = i
            initial_day = datetime(date_aux.year, date_aux.month, date_aux.day)

        # window checkpoint
        actual_day = datetime(date_aux.year, date_aux.month, date_aux.day)
        day_difference = actual_day - initial_day

        if day_difference > timedelta(days=window_size):
            if window_type == WindowType.EVENT:
                # Gera o sublog da janela
                window = EventStream(event_data[initial_window_index:i])
                sub_log = log_converter.apply(window, variant=log_converter.Variants.TO_EVENT_LOG)
            elif window_type == WindowType.TRACE:
                sub_log = event_data[initial_window_index:i]
            else:
                print(f'Tipo de janela informado incorretamente: {window_type}.')

            # Gera o dfg e salva
            generate_dfg(sub_log, original_file_name, w_count)

            w_count += 1

            # reinicializa variáveis para nova janela
            initial_window_index = i
            if window_type == WindowType.EVENT:
                date_aux = item['time:timestamp']
            elif window_type == WindowType.TRACE:
                # utiliza a data do primeiro evento do trace
                date_aux = item[0]['time:timestamp']
            else:
                print(f'Tipo de janela informado incorretamente: {window_type}.')
            initial_day = datetime(date_aux.year, date_aux.month, date_aux.day)
    return w_count


# Função que importa os dados de evento de acordo com o tipo
# do arquivo (CSV ou XES)
def import_event_data(filename):
    event_data = None
    try:
        if 'csv' in filename:
            log_csv = pd.read_csv(filename, sep=';')
            event_data = log_converter.apply(log_csv)
        elif 'xes' in filename:
            # Assume that the user uploaded an excel file
            event_data = xes_importer.apply(filename)
    except Exception as e:
        print(e)
        print(f'Problemas ao carregar o arquivo {filename}')
    return event_data


# Função que gera todos os modelos de processos para o tipo de janelamento
# escolhido
def generate_models(window_type, window_unity, window_size, event_data_original_name):
    variant = xes_importer.Variants.ITERPARSE
    parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}

    # verificar se o diretório para salvar os modelos existe
    # caso contrário cria - ACHO QUE DEVE FICAR EM OUTRO LUGAR
    if not os.path.exists(Info.data_models_path):
        os.makedirs(Info.data_models_path)

    input = os.path.join(Info.data_input_path, event_data_original_name)
    print(f'Analisando arquivo de entrada: {input}')

    # faz a importação do arquivo de acordo com o seu tipo (CSV ou XES)
    # importa o log
    event_data = import_event_data(input)
    if event_data is not None:
        # caso o usuário utilize o janelamento por evento ou tempo precisamos ler como stream
        if window_type == WindowType.EVENT:
            # converte para event stream, será que preciso conterter ou posso importar direto?
            event_data = log_converter.apply(event_data, variant=log_converter.Variants.TO_EVENT_STREAM)

        # para os janelamentos por evento ou trace, itera na event stream ou no log
        # verificando checkpoint de acordo com tamanho da janela
        if window_unity == WindowUnity.UNITY:
            return apply_window_unit(event_data, window_type, window_size, event_data_original_name)
        elif window_unity == WindowUnity.HOUR:
            return apply_window_time(event_data, window_type, window_size, event_data_original_name)
        elif window_unity == WindowUnity.DAY:
            return apply_window_day(event_data, window_type, window_size, event_data_original_name)
        else:
            print(f'Janelamento não implementado [{window_type}-{window_unity}].')
            return 0


def get_model(file, window):
    return get_dfg(file, window)


def get_model_filename(file, window):
    return get_dfg_filename(file, window)


def get_model_to_model_comparison(file, current_window):
    return compare_dfg(file, current_window)