"""
    This file is part of Interactive Process Drift (IPDD) Framework.
    IPDD is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    IPDD is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with IPDD. If not, see <https://www.gnu.org/licenses/>.
"""
import argparse
import os
import time

from components.parameters import ReadLogAs, WindowUnityFixed, Approach, AttributeAdaptive
from components.dfg_definitions import Metric
from components.ippd_fw import InteractiveProcessDriftDetectionFW, IPDDParametersFixed, IPDDParametersAdaptive


def main():
    pathname = os.path.dirname(os.path.abspath(__file__))
    print(f'Pathname of script: {pathname}')

    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)

    parser = argparse.ArgumentParser(description='IPDD FW command line')
    parser.add_argument('--approach', '-a', help='Approach: f - fixed window or a - adaptive window', default='f')
    parser.add_argument('--read_as', '-wt', help='Read the log as: t - stream of traces or e - event stream',
                        default='t')
    parser.add_argument('--event_log', '-l', required=True,
                        help='Event log: path and name of the event log using XES format')
    parser.add_argument('--real_drifts', '-rd', type=int, nargs='+',
                        help='Real drifts: list of trace indexes (starting from 1) of the real drifts (separated by a '
                             'space), used for evaluation. If no real drift exists, then fill with 0.')
    parser.add_argument('--error_tolerance', '-et', type=int,
                        help='Error tolerance: the interval os tolerance considered when evaluating the F-score metric',
                        default=100)
    parser.add_argument('--metrics', '-mt', nargs='+',
                        help=f'Similarity Metrics: list of similarity metrics that IPDD should '
                             f'calculate. Possible options: {[m.name for m in framework.get_implemented_metrics()]}',
                        default=['NODES', 'EDGES'])
    # options for fixed approach
    parser.add_argument('--win_unity', '-wu',
                        help='Window unity: u - amount of traces or events, h - hours, or d - days', default='u')
    parser.add_argument('--win_size', '-ws', type=int, default=30,
                        help='Window size: numeric value indicating the total of window unities for each window')
    # options for adaptive approach
    parser.add_argument('--attribute', '-at', help='Attribute for the change detector: st - sojourn time activity '
                                                   'ot - other attribute; in this case specify attribute_name parameter',
                        default='st')
    parser.add_argument('--attribute_name', '-atname', help='Attribute name')
    parser.add_argument('--activities', '-activities', nargs='+',
                        help='Activities considered for getting the defined attribute', default=[])
    parser.add_argument('--delta', '-dt', help='Delta parameter - ADWIN change detector', type=float,
                        default=0.002)

    args = parser.parse_args()
    approach = ''
    if args.approach == 'f':
        approach = Approach.FIXED.name
    elif args.approach == 'a':
        approach = Approach.ADAPTIVE.name

    if args.read_as == 't':
        win_type = ReadLogAs.TRACE.name
    elif args.read_as == 'e':
        win_type = ReadLogAs.EVENT.name

    win_unity = ''
    attribute = ''
    attribute_name = ''
    win_size = 0
    if approach == Approach.FIXED.name:
        if args.win_unity == 'u':
            win_unity = WindowUnityFixed.UNITY.name
        elif args.win_unity == 'h':
            win_unity = WindowUnityFixed.HOUR.name
        elif args.win_unity == 'd':
            win_unity = WindowUnityFixed.DAY.name
        win_size = args.win_size
    elif approach == Approach.ADAPTIVE.name:
        if args.attribute == 'st':
            attribute = AttributeAdaptive.SOJOURN_TIME.name
        else:
            attribute = AttributeAdaptive.OTHER.name
            if args.attribute_name != '':
                attribute_name = args.attribute_name
            else:
                print(f'You must define --attribute_name when using attribute OTHER')
                return
        activities = args.activities

    event_log = args.event_log
    real_drifts = args.real_drifts
    if real_drifts and len(real_drifts) == 1 and real_drifts[0] == 0:  # no real drift present in the log
        real_drifts = []
    error_tolerance = args.error_tolerance

    # get enum from metrics
    metrics = []
    for m in args.metrics:
        for implemented_metric in Metric:
            if m == implemented_metric.name:
                metrics.append(implemented_metric)

    print('----------------------------------------------')
    print('Configuration:')
    print('----------------------------------------------')
    print(f'Approach: {approach}')
    print(f'Read log as: {win_type}')
    if approach == Approach.FIXED.name:
        print(f'Window unity: {win_unity}')
        print(f'Window size: {win_size}')
    elif approach == Approach.ADAPTIVE.name:
        print(f'Attribute: {attribute}')
        if attribute == AttributeAdaptive.OTHER.name:
            print(f'Attribute name: {attribute_name}')
            if len(activities) > 0:
                print(f'Filtered activities: {activities}')
        print(f'Delta - ADWIN detector: {args.delta}')
    print(f'Metrics: {[m.value for m in metrics]}')
    print(f'Event log: {event_log}')

    if real_drifts is not None:
        print(f'Real drifts: {real_drifts}')
        print(f'Error tolerance: {error_tolerance}')
    print('----------------------------------------------')

    print(f'Starting analyzing process drifts ...')
    if approach == Approach.FIXED.name:
        parameters = IPDDParametersFixed(event_log, approach, win_type, metrics, win_unity, win_size)
        framework.run(parameters, user_id='script')
    elif approach == Approach.ADAPTIVE.name:
        parameters = IPDDParametersAdaptive(event_log, approach, win_type, metrics, attribute, attribute_name,
                                            activities, args.delta)
        framework.run(parameters, user_id='script')

    running = framework.get_status_running()
    while running:
        print(f'Waiting for IPDD finishes ... Status running: {running}')
        time.sleep(2)  # in seconds
        running = framework.get_status_running()
    print(f'IPDD finished drift analysis')

    detected_drifts = None
    total_of_itens = framework.get_number_of_items()
    if approach == Approach.FIXED.name:
        windows, detected_drifts = framework.get_drifts_info()
        print(f'IPDD detect control-flow drift in windows {windows} - traces {detected_drifts}')
    elif approach == Approach.ADAPTIVE.name:
        detected_drifts = {}
        # get the activities that report a drift using the change detector
        for activity in framework.get_activities_with_drifts():
            indexes = framework.initial_indexes[activity]
            detected_drifts[activity] = list(indexes.keys())[1:]
            print(f'IPDD detect drifts for attribute {attribute}-{attribute_name} in activity {activity} in indexes {detected_drifts}')
            # get information about control-flow metrics
            windows, traces = framework.get_drifts_info(activity)
            if len(traces) > 0:
                print(f'IPDD detect control-flow drift for activity {activity} in windows {windows} - traces {traces}')
    else:
        print(f'Approach not identified: {approach}')

    if approach == Approach.FIXED.name:
        if args.real_drifts is not None:
            f_score = framework.evaluate(real_drifts, detected_drifts, error_tolerance, total_of_itens)
            print(f'IPDD F-score: {f_score}')
    elif approach == Approach.ADAPTIVE.name:
        if args.real_drifts is not None:
            # if len(detected_drifts) > 0:
            print(f'********* IPDD evaluation metrics results *********')
            for activity in framework.get_all_activities():
                if activity in detected_drifts.keys():
                    framework.evaluate(real_drifts, detected_drifts[activity], error_tolerance, total_of_itens, activity)
                else:
                    # if IPDD do not detect any drift in the activity
                    framework.evaluate(real_drifts, [], error_tolerance, total_of_itens, activity)
            # else:
            #     print(f'********* IPDD did not detect any drift. No F-score results *********')
    else:
        print(f'Approach not identified: {approach}')


if __name__ == '__main__':
    main()
