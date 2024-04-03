import os
import re
import pandas as pd
from evaluation_metrics import change_points_key, detected_at_key

def get_VDD_files(log_file_path, key, ftype):
    # get the .txt files with the results reported by Apromore
    files = [i for i in os.listdir(log_file_path)
             if os.path.isfile(os.path.join(log_file_path, i))
             and i.endswith(ftype)
             and i.startswith(key)]

    return files


def convert_list_to_int(string_list):
    number_of_itens = len(string_list)
    integer_list = []
    if number_of_itens > 0 and string_list[0] != '':  # to avoid error in case of list with ''
        integer_map = map(int, string_list.copy())
        integer_list = list(integer_map)
    return integer_list


def read_drifts_VDD(file, winsize, winstep):
    file = open(file, 'r')
    lines = file.readlines()

    get_next_line = False
    line_with_windows = ''
    for line in lines:
        if get_next_line:
            line_with_windows = line
            break
        if line.startswith('x lines:'):
            get_next_line = True
    file.close()
    line_with_windows = line_with_windows.strip()
    list_of_windows = line_with_windows.strip('][').split(', ')
    list_of_windows = convert_list_to_int(list_of_windows)
    list_of_windows = list_of_windows[:-1]
    reported_drifts = [int(w * winstep) for w in list_of_windows]
    return reported_drifts


def compile_results_from_VDD(filepath, filenames, key):
    print(f'Looking for results...')
    results = {}

    for file in filenames:
        print(f'*****************************************************************')
        print(f'Reading file {file}...')
        print(f'*****************************************************************')
        complete_filename = os.path.join(filepath, file)
        reexp = rf'{key}([a-zA-Z]*)(.*?)_w(\d*)_s(\d*)_(\D*).txt'
        if match := re.search(reexp, file):
            pattern = match.group(1)
            logsize = match.group(2)
            winsize = match.group(3)
            winstep = match.group(4)
            approach = match.group(5)
        else:
            print(f'Filename {file} do not follow the expected patter {reexp} - IGNORING...')
            continue

        detected_drifts = read_drifts_VDD(complete_filename, int(winsize), int(winsize)/2)
        logname = pattern + logsize + '.xes'
        configuration_drifts = change_points_key + approach + ' ' + winsize
        configuration_delays = detected_at_key + approach + ' ' + winsize
        if logname not in results.keys():
            results[logname] = {}

        results[logname][configuration_drifts] = detected_drifts
    df = pd.DataFrame(results).T
    out_filename = f'results_VDD.xlsx'
    out_complete_filename = os.path.join(filepath, out_filename)
    print(f'*****************************************************************')
    print(f'Saving results at file {out_complete_filename}...')
    df.to_excel(out_complete_filename)
    print(f'*****************************************************************')


if __name__ == '__main__':
    results_filepath = 'E://Doutorado_Experimentos//VDD//experimento2//dataset2//output_console'
    file_type = '.txt'
    key = 'out_'
    filenames = get_VDD_files(results_filepath, key, file_type)
    compile_results_from_VDD(results_filepath, filenames, key)
