import os
# import pandas as pd
# from pm4py.objects.log.util import dataframe_utils
# from pm4py.streaming.importer.xes import importer as xes_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter


def analyze_italian_help_desk():
    folder = 'data/input/logs/controlflow/real'
    logname = 'italian_help_desk_company.xes'
    logcsv = 'finale.csv'

    # log_csv = pd.read_csv(os.path.join(folder, logcsv), sep=',')
    # log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
    # log_csv = log_csv.sort_values('Timestamp')

    # import the event log sorted by timestamp
    # import the event log sorted by timestamp
    variant = xes_importer.Variants.ITERPARSE
    parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
    eventlog = xes_importer.apply(os.path.join(folder, logname), variant=variant, parameters=parameters)
    event_data = log_converter.apply(eventlog, variant=log_converter.Variants.TO_EVENT_STREAM)
    drift_ostovar = [8577, 17307]
    case_ids_drifts = []
    for event_id, event in enumerate(event_data):
        if event_id in drift_ostovar:
            case_id = event['case:concept:name']
            case_ids_drifts.append(case_id)
            print(f'{event}')
            print(f'{case_id}')

    # get trace id from event log
    for trace_id, trace in enumerate(eventlog):
        case_id = trace.attributes['concept:name']
        if case_id in case_ids_drifts:
            print(f'{trace_id}: {trace}')


if __name__ == '__main__':
    analyze_italian_help_desk()
