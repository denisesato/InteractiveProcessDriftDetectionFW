import os
import pandas as pd
import re

change_points_key = 'drifts - '
detected_at_key = 'detected at - '


def calculate_f_score(tp, fp, fn):
    if tp + fp > 0:
        precision = tp / (tp + fp)
        if tp + fn > 0:
            recall = tp / (tp + fn)
        if precision > 0 or recall > 0:
            f_score = 2 * ((precision * recall) / (precision + recall))
            return f_score
    return 0


def calculate_fpr(tn, fp):
    return fp / (fp + tn)


def calculate_mean_delay(total_distance, tp):
    if total_distance == 0:
        return 0
    return total_distance / tp


# Calculate the metrics F-score, mean delay, and FPR (false positive rate)
# The f-score consider a TP a drift reported after an actual drift + et (error tolerance)
# The mean delay is the average of the delta between the trace where the drift was detected and the actual drift
# The delays is the difference between the actual drift and the moment where it is detected
# If the moment of detection occurs after the change point it should be informed in the parameter detected_at_list
def calculate_metrics(metrics, detected_drifts, actual_drifts_informed, total_of_instances, et,
                      detected_at_list=None):
    real_drifts = actual_drifts_informed.copy()
    # sort the both lists (real and detected drifts)
    real_drifts.sort()
    detected_drifts.sort()
    if detected_at_list:
        detected_at_list.sort()

    # create lists to store the tp's and fp's
    tp_list = []
    fp_list = []
    total_distance = 0
    for i, detected_cp in enumerate(detected_drifts):
        tp_found = False
        for real_cp in real_drifts:
            if detected_at_list:
                dist_detection = detected_at_list[i] - real_cp
            else:
                dist_detection = detected_cp - real_cp
            dist = detected_cp - real_cp
            if 0 <= dist <= et:
                total_distance += dist_detection
                tp_list.append(detected_cp)
                tp_found = True
                real_drifts.remove(real_cp)
                break
            elif dist < 0:
                break
        if not tp_found:
            fp_list.append(detected_cp)

    tp = len(tp_list)
    fp = len(fp_list)
    fn = len(real_drifts)  # list contains only the real drifts not correctly detected
    tn = total_of_instances - tp - fp - fn
    metrics_result = {}
    for m in metrics:
        if m == 'f_score':
            metrics_result[m] = calculate_f_score(tp, fp, fn)
        if m == 'FPR':
            metrics_result[m] = calculate_fpr(tn, fp)
        if m == 'mean_delay':
            metrics_result[m] = calculate_mean_delay(total_distance, tp)
    return metrics_result


# Calculate the F-score without the error tolerance
# a TP is set when there is a drift detected after a real change point - the distance is reported in the mean delay
# if there is more than one real change point consider the TP the closest one
def calculate_metrics_new(metrics, detected_drifts, actual_drifts_informed, total_of_instances, detected_at_list=None):
    real_drifts = actual_drifts_informed.copy()
    # sort the both lists (real and detected drifts)
    real_drifts.sort()
    detected_drifts.sort()
    if detected_at_list:
        detected_at_list.sort()

    # create lists to store the tp's and fp's
    tp_list = []
    fp_list = []
    fn_list = []
    total_distance = 0
    total_detection_distance = 0
    for i, detected_cp in enumerate(detected_drifts):
        possible_real_drifts = [cp for cp in real_drifts if detected_cp >= cp]
        possible_real_drifts.sort(reverse=True)
        if len(possible_real_drifts) > 0:
            detected_real_cp = possible_real_drifts[0]

            # if there is information about the trace of detection apply it for
            # calculating the mean detection delay
            if detected_at_list:
                detection_delay = detected_at_list[i] - detected_real_cp
            else:
                detection_delay = detected_cp - detected_real_cp
            total_detection_distance += detection_delay

            # the mean delay considers the distance between the real change point and the reported change point
            delay = detected_cp - detected_real_cp
            total_distance += delay

            tp_list.append(detected_cp)
            real_drifts.remove(detected_real_cp)
            possible_real_drifts.remove(detected_real_cp)
            # if other possible real drifts are not detected they are FALSE NEGATIVES
            for rp in possible_real_drifts:
                fn_list.append(rp)
                real_drifts.remove(rp)
        else:
            fp_list.append(detected_cp)

    # the remaining real drifts are also FALSE NEGATIVES
    for d in real_drifts:
        fn_list.append(d)

    tp = len(tp_list)
    fp = len(fp_list)
    fn = len(fn_list)
    tn = total_of_instances - tp - fp - fn
    metrics_result = {}
    for m in metrics:
        if m == 'f_score':
            metrics_result[m] = calculate_f_score(tp, fp, fn)
        if m == 'FPR':
            metrics_result[m] = calculate_fpr(tn, fp)
        if m == 'mean_delay':
            metrics_result[m] = calculate_mean_delay(total_distance, tp)
        if m == 'mean_detection_delay':
            metrics_result[m] = calculate_mean_delay(total_detection_distance, tp)
    return metrics_result


def calculate_metrics_dataset(filepath, filename, metrics, dataset_config, save_input_for_calculation=False):
    input_filename = os.path.join(filepath, filename)
    print(f'*****************************************************************')
    print(f'Calculating metrics for file {input_filename}...')
    print(f'*****************************************************************')
    df = pd.read_excel(input_filename, index_col=0)
    complete_results = df.T.to_dict()
    metrics_results = {}
    for logname in complete_results.keys():
        if logname not in dataset_config.lognames:
            print(f'Logname {logname} not configured for the dataset. IGNORING...')
            continue
        metrics_results[logname] = {}
        regexp = r'(\d.*).xes'
        if match := re.search(regexp, logname):
            logsize = match.group(1)
        else:
            print(f'Problem getting the logsize. File {input_filename} NOT PROCESSED!')
            return

        change_points = {}
        detected_at = {}
        for key in complete_results[logname].keys():
            # get list of trace ids from excel and convert to a list of integers
            trace_ids_list = complete_results[logname][key][1:-1].split(",")
            trace_ids_list = convert_list_to_int(trace_ids_list)

            # insert into change points or detected points
            if change_points_key in key:
                configuration = key[len(change_points_key):]
                change_points[configuration] = trace_ids_list
            elif detected_at_key in key:
                configuration = key[len(detected_at_key):]
                detected_at[configuration] = trace_ids_list

        for configuration in change_points.keys():
            # get the actual change points
            # check first in the exceptions
            if logname in dataset_config.exceptions_in_actual_change_points.keys():
                real_change_points = dataset_config.exceptions_in_actual_change_points[logname]['actual_change_points']
                instances = dataset_config.exceptions_in_actual_change_points[logname]['number_of_instances']
            else:
                # if it is not an exception, get the real change points by the logsize
                real_change_points = dataset_config.actual_change_points[logsize]
                instances = dataset_config.number_of_instances[logsize]

            # get the detected at information if available and convert to a list of integers
            if len(detected_at) > 0:
                metrics = calculate_metrics_new(metrics, change_points[configuration], real_change_points,
                                                instances, detected_at[configuration])
            else:
                metrics = calculate_metrics_new(metrics, change_points[configuration], real_change_points,
                                                instances)
            # add the calculated metrics to the dictionary
            if save_input_for_calculation:
                metrics_results[logname][f'Detected drifts {configuration}'] = change_points[configuration]
                if len(detected_at) > 0:
                    metrics_results[logname][f'Detected at {configuration}'] = detected_at[configuration]
                metrics_results[logname][f'Real drifts {configuration}'] = real_change_points
            # print(f'-----------------------------------------------------------------')
            # print(f'Scenario: {key} - {scenario} - {delta}')
            # print(f'Real change points = {actual_change_points[scenario]}')
            # print(f'Error tolerance = {error_tolerance[scenario]}')
            # print(f'Detected change points = {detected_drifts}')
            for m in metrics:
                metrics_results[logname][f'{m} {configuration}'] = metrics[m]
                # print(f'{m} {scenario_configuration} = {metrics[m]}')
            # print(f'-----------------------------------------------------------------')
    df = pd.DataFrame(metrics_results).T
    out_filename = filename[:-(len('.xlsx'))]
    out_filename = f'metrics_{out_filename}.xlsx'
    out_complete_filename = os.path.join(filepath, out_filename)
    print(f'*****************************************************************')
    print(f'Metrics for file {input_filename} calculated')
    print(f'Saving results at file {out_complete_filename}...')
    df.to_excel(out_complete_filename)
    print(f'*****************************************************************')


def convert_list_to_int(string_list):
    number_of_itens = len(string_list)
    integer_list = []
    if number_of_itens > 0 and string_list[0] != '':  # to avoid error in case of list with ''
        integer_map = map(int, string_list.copy())
        integer_list = list(integer_map)
    return integer_list
