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
    parser.add_argument('--approach', '-a', help='Approach: f - fixed window or a - adaptive window', default='a')
    parser.add_argument('--read_as', '-wt', help='Read the log as: t - stream of traces or e - event stream', default='t')
    parser.add_argument('--event_log', '-l', required=True,
                        help='Event log: path and name of the event log using XES format')
    parser.add_argument('--real_drifts', '-rd', type=int, nargs='+',
                        help='Real drifts: list of trace indexes from actual drifts (separated by a space), used for '
                             'evaluation')
    parser.add_argument('--metrics', '-mt', nargs='+',
                        help=f'Similarity Metrics: list of similarity metrics that IPDD should '
                             f'calculate. Possible options: {[m.name for m in framework.get_implemented_metrics()]}',
                        default=['NODES'])
    # options for fixed approach
    parser.add_argument('--win_unity', '-wu',
                        help='Window unity: u - amount of traces or events, h - hours, or d - days', default='u')
    parser.add_argument('--win_size', '-wz', type=int, default=30,
                        help='Window size: numeric value indicating the total of window unities for each window')
    # options for adaptive approach
    parser.add_argument('--attribute', '-at', help='Attribute for the change detector: st - sojourn time activity',
                        default='st')
    parser.add_argument('--delta', '-dt', help='Delta parameter - ADWIN cganhe detector', type=float,
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

    event_log = args.event_log
    real_drifts = args.real_drifts

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
        print(f'Delta - ADWIN detector: {args.delta}')
    print(f'Metrics: {[m.value for m in metrics]}')
    print(f'Event log: {event_log}')

    if args.real_drifts is not None:
        print(f'Real drifts: {real_drifts}')
    print('----------------------------------------------')

    print(f'Starting analyzing process drifts ...')
    if approach == Approach.FIXED.name:
        parameters = IPDDParametersFixed(event_log, approach, win_type, metrics, win_unity, win_size)
        framework.run(parameters, user_id='script')
    elif approach == Approach.ADAPTIVE.name:
        parameters = IPDDParametersAdaptive(event_log, approach, win_type, metrics, attribute, args.delta)
        framework.run(parameters, user_id='script')

    running = framework.get_status_running()
    while running:
        print(f'Waiting for IPDD finishes ... Status running: {running}')
        time.sleep(2)  # in seconds
        running = framework.get_status_running()
    print(f'IPDD finished drift analysis')

    if approach == Approach.FIXED.name:
        window_candidates = framework.get_windows_candidates()
        print(f'IPDD detect drift in windows {window_candidates}')
    elif approach == Approach.ADAPTIVE.name:
        for activity in framework.get_activities():
            indexes = framework.initial_indexes[activity]
            if len(indexes) > 0:
                print(f'IPDD detect sojourn time drift for activity {activity} in indexes {indexes}')
            window_candidates = framework.get_windows_candidates(activity)
            if len(window_candidates) > 0:
                print(f'IPDD detect control-flow drift for activity {activity} in windows {window_candidates}')

    if args.real_drifts is not None:
        f_score = framework.evaluate(window_candidates, real_drifts, win_size)
        print(f'IPDD f-score: {f_score}')


if __name__ == '__main__':
    main()
