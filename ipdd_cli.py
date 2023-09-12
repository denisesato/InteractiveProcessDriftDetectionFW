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

from components.adaptive.detectors import ConceptDriftDetector, SelectDetector
from components.parameters import ReadLogAs, WindowUnityFixed, Approach, AttributeAdaptive, AdaptivePerspective, \
    ControlflowAdaptiveApproach
from components.dfg_definitions import Metric
from components.ippd_fw import InteractiveProcessDriftDetectionFW, IPDDParametersFixed, IPDDParametersAdaptive, \
    IPDDParametersAdaptiveControlflow


def main():
    pathname = os.path.dirname(os.path.abspath(__file__))
    print(f'Pathname of script: {pathname}')

    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)

    parser = argparse.ArgumentParser(description='IPDD FW command line')

    # General options
    parser.add_argument('--approach', '-a', help='Approach: f - fixed window or a - adaptive window', default='f')
    parser.add_argument('--event_log', '-l', required=True,
                        help='Event log: path and name of the event log using XES format')
    parser.add_argument('--real_drifts', '-rd', type=int, nargs='+',
                        help='Real drifts: list of trace indexes of the real drifts (separated by a '
                             'space), used for evaluation. If no real drift exists, then fill with 0.')
    parser.add_argument('--metrics', '-mt', nargs='+',
                        help=f'Similarity Metrics: list of similarity metrics that IPDD should '
                             f'calculate. Possible options: {[m.name for m in framework.get_implemented_metrics()]}',
                        default=['NODES', 'EDGES'])

    # Parameter for fixed or adaptive IPDD for control-flow drifts
    parser.add_argument('--win_size', '-ws', type=int, default=30,
                        help='Window size: numeric value indicating the total of window unities for each window')

    # Options for the adaptive approaches
    parser.add_argument('--delta', '-dt', help='Delta parameter - ADWIN change detector', type=float,
                        default=0.002)
    parser.add_argument('--perspective', '-p', help='Define the process model perspective to analyze '
                                                    'td - time/data perspectives or cf - control-flow perspective',
                        default='cf')

    # Options for adaptive approach for time/data perspectives
    parser.add_argument('--attribute', '-at', help='Attribute for the change detector: st - sojourn time activity '
                                                   'ot - other attribute; in this case specify attribute_name parameter',
                        default='st')
    parser.add_argument('--attribute_name', '-atname', help='Attribute name')
    parser.add_argument('--activities', '-activities', nargs='+',
                        help='Activities considered for getting the defined attribute', default=[])

    # Options for adaptive approach for the control-flow perspective
    parser.add_argument('--adaptive_controlflow_approach', '-cfa', help='Choose the approach for Adaptive IPDD for '
                                                                        'control-flow drifts '
                                                                        't - trace by trace or w - windowing',
                        default='t')
    parser.add_argument('--save_sublogs', '-sub',
                        help='Option for exporting the sub-logs derived between the detected change points',
                        type=bool, default=False)
    parser.add_argument('--no_update_model',
                        help='Option for update process model after detecting a change point',
                        action='store_true')

    args = parser.parse_args()
    approach = ''
    perspective = ''
    if args.approach == 'f':
        approach = Approach.FIXED.name
    elif args.approach == 'a':
        approach = Approach.ADAPTIVE.name
        if args.perspective == 'td':
            perspective = AdaptivePerspective.TIME_DATA.name
        elif args.perspective == 'cf':
            perspective = AdaptivePerspective.CONTROL_FLOW.name
        else:
            print(f'You must define --perspective when using approach ADAPTIVE')
            return

    attribute = ''
    attribute_name = ''
    win_size = 0
    if approach == Approach.FIXED.name:
        win_size = args.win_size
    elif approach == Approach.ADAPTIVE.name:
        if perspective == AdaptivePerspective.TIME_DATA.name:
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
        elif perspective == AdaptivePerspective.CONTROL_FLOW.name:
            win_size = args.win_size
            if args.adaptive_controlflow_approach == 't':
                adaptive_controlflow_approach = ControlflowAdaptiveApproach.TRACE.name
            elif args.adaptive_controlflow_approach == 'w':
                adaptive_controlflow_approach = ControlflowAdaptiveApproach.WINDOW.name

    event_log = args.event_log
    real_drifts = args.real_drifts
    if real_drifts and len(real_drifts) == 1 and real_drifts[0] == 0:  # no real drift present in the log
        real_drifts = []

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
    detector_class = None
    if approach == Approach.FIXED.name:
        print(f'Window size: {win_size}')
    elif approach == Approach.ADAPTIVE.name:
        detector_class = SelectDetector.get_detector_instance(ConceptDriftDetector.ADWIN.name,
                                                              parameters={'delta': args.delta})
        print(f'Delta - ADWIN detector: {args.delta}')
        if perspective == AdaptivePerspective.TIME_DATA.name:
            print(f'Attribute: {attribute}')
            if attribute == AttributeAdaptive.OTHER.name:
                print(f'Attribute name: {attribute_name}')
                if len(activities) > 0:
                    print(f'Filtered activities: {activities}')
        elif perspective == AdaptivePerspective.CONTROL_FLOW.name:
            print(f'Window size: {win_size}')
            print(f'Adaptive control-flow approach: {adaptive_controlflow_approach}')
            print(f'Export sublogs: {args.save_sublogs}')
            print(f'Update process models: {args.no_update_model}')

    print(f'Metrics: {[m.value for m in metrics]}')
    print(f'Event log: {event_log}')

    if real_drifts is not None:
        print(f'Real drifts: {real_drifts}')
    print('----------------------------------------------')

    print(f'Starting analyzing process drifts ...')
    parameters = None
    if approach == Approach.FIXED.name:
        parameters = IPDDParametersFixed(event_log, approach, ReadLogAs.TRACE.name, metrics,
                                         WindowUnityFixed.UNITY.name, win_size)
    elif approach == Approach.ADAPTIVE.name:
        if perspective == AdaptivePerspective.TIME_DATA.name:
            parameters = IPDDParametersAdaptive(event_log,
                                                approach,
                                                perspective,
                                                ReadLogAs.TRACE.name,
                                                metrics,
                                                detector_class,
                                                attribute,
                                                attribute_name,
                                                activities)
        elif perspective == AdaptivePerspective.CONTROL_FLOW.name:
            parameters = IPDDParametersAdaptiveControlflow(event_log,
                                                           approach,
                                                           perspective,
                                                           ReadLogAs.TRACE.name,
                                                           win_size,
                                                           metrics,
                                                           adaptive_controlflow_approach,
                                                           detector_class,
                                                           save_sublogs=args.save_sublogs,
                                                           update_model=not args.no_update_model)
    framework.run_script(parameters)

    running = framework.get_status_running()
    while running:
        print(f'Waiting for IPDD finishes ... Status running: {running}')
        time.sleep(2)  # in seconds
        running = framework.get_status_running()
    print(f'IPDD finished drift analysis')

    detected_drifts = None
    total_of_itens = framework.get_number_of_items()
    if approach == Approach.FIXED.name:
        windows, detected_drifts = framework.get_windows_with_drifts()
        print(f'IPDD detect control-flow drift in windows {windows} - traces {detected_drifts}')
    elif approach == Approach.ADAPTIVE.name:
        if perspective == AdaptivePerspective.TIME_DATA.name:
            detected_drifts = {}
            # get the activities that report a drift using the change detector
            for activity in framework.get_activities_with_drifts():
                indexes = framework.initial_indexes[activity]
                detected_drifts[activity] = list(indexes.keys())[1:]
                print(
                    f'IPDD detect drifts for attribute {attribute}-{attribute_name} in activity {activity} in indexes {detected_drifts}')
                # get information about control-flow metrics
                windows, traces = framework.get_windows_with_drifts(activity)
                if len(traces) > 0:
                    print(
                        f'IPDD detect control-flow drift for activity {activity} in windows {windows} - traces {traces}')
        elif perspective == AdaptivePerspective.CONTROL_FLOW.name:
            detected_drifts = framework.get_initial_trace_indexes()
            # remove the index 0
            detected_drifts = detected_drifts[1:]
            print(
                f'Adaptive IPDD detect control-flow drifts in traces {detected_drifts}')
            # get information about control-flow metrics
            windows, traces = framework.get_windows_with_drifts()
            print(
                f'Similarity metrics confirm the drifts in  {traces}')
        else:
            print(f'Perspective not identified: {perspective}')
    else:
        print(f'Approach not identified: {approach}')

    if approach == Approach.FIXED.name:
        if args.real_drifts is not None:
            f_score = framework.evaluate(real_drifts, detected_drifts, total_of_itens)
            print(f'IPDD F-score: {f_score}')
    elif approach == Approach.ADAPTIVE.name:
        if args.real_drifts is not None:
            # if len(detected_drifts) > 0:
            print(f'********* IPDD evaluation metrics results *********')
            for activity in framework.get_all_activities():
                if activity in detected_drifts:
                    framework.evaluate(real_drifts, detected_drifts[activity], total_of_itens,
                                       activity)
                else:
                    # if IPDD do not detect any drift in the activity
                    framework.evaluate(real_drifts, [], total_of_itens, activity)
            # else:
            #     print(f'********* IPDD did not detect any drift. No F-score results *********')
    else:
        print(f'Approach not identified: {approach}')


def run_IPDD_script(parameters, real_drifts=None):
    # getting instance of the IPDD
    framework = InteractiveProcessDriftDetectionFW(script=True)

    if parameters.approach == Approach.FIXED.name:
        win_size = parameters.win_size
    elif parameters.approach == Approach.ADAPTIVE.name:
        if parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            attribute_name = ''
            if parameters.attribute == AttributeAdaptive.OTHER.name:
                if parameters.attribute_name != '':
                    attribute_name = parameters.attribute_name
                else:
                    print(f'You must define --attribute_name when using attribute OTHER')
                    return
            activities = parameters.activities
        elif parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            win_size = parameters.win_size

    event_log = parameters.logname
    if real_drifts and len(real_drifts) == 1 and real_drifts[0] == 0:  # no real drift present in the log
        real_drifts = []

    # get enum from metrics
    metrics = []
    for m in parameters.metrics:
        for implemented_metric in Metric:
            if m == implemented_metric.name:
                metrics.append(implemented_metric)

    print('----------------------------------------------')
    print('Configuration:')
    print('----------------------------------------------')
    print(f'Approach: {parameters.approach}')
    detector_class = None
    if parameters.approach == Approach.FIXED.name:
        print(f'Window size: {win_size}')
    elif parameters.approach == Approach.ADAPTIVE.name:
        # check if the user define a detector, otherwise use the default ADWIN detector
        if hasattr(parameters, "detector_class"):
            detector_class = parameters.detector_class
        else:
            detector_class = SelectDetector.get_selected_detector(ConceptDriftDetector.ADWIN.name)
        print(f'Detector: {detector_class.get_name()}')
        for key in detector_class.parameters.keys():
            print(f'{key}: {detector_class.parameters[key]}')

        if parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            print(f'Attribute: {parameters.attribute}')
            if parameters.attribute == AttributeAdaptive.OTHER.name:
                print(f'Attribute name: {attribute_name}')
                if len(activities) > 0:
                    print(f'Filtered activities: {activities}')
        elif parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            print(f'Window size: {win_size}')
            print(f'Adaptive control-flow approach: {parameters.adaptive_controlflow_approach}')
            print(f'Export sublogs: {parameters.save_sublogs}')
            print(f'Update process models: {parameters.update_model}')

    print(f'Metrics: {[m.value for m in metrics]}')
    print(f'Event log: {event_log}')

    if real_drifts is not None:
        print(f'Real drifts: {real_drifts}')
    print('----------------------------------------------')

    # parameters for customizing information inside the plots
    activities_for_plot = None
    if hasattr(parameters, "activities_for_plot"):
        activities_for_plot = parameters.activities_for_plot

    attribute_name_for_plot = None
    if hasattr(parameters, "attribute_name_for_plot"):
        attribute_name_for_plot = parameters.attribute_name_for_plot

    print(f'Starting analyzing process drifts ...')
    if parameters.approach == Approach.FIXED.name:
        parameters = IPDDParametersFixed(event_log, parameters.approach, ReadLogAs.TRACE.name, metrics,
                                         WindowUnityFixed.UNITY.name, win_size)
    elif parameters.approach == Approach.ADAPTIVE.name:
        if parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            parameters = IPDDParametersAdaptive(logname=event_log,
                                                approach=parameters.approach,
                                                perspective=parameters.perspective,
                                                read_log_as=parameters.read_log_as,
                                                metrics=metrics,
                                                detector_class=detector_class,
                                                attribute=parameters.attribute,
                                                attribute_name=attribute_name,
                                                activities=activities,
                                                activities_for_plot=activities_for_plot,
                                                attribute_name_for_plot=attribute_name_for_plot)
        elif parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            parameters = IPDDParametersAdaptiveControlflow(logname=event_log,
                                                           approach=parameters.approach,
                                                           perspective=parameters.perspective,
                                                           read_log_as=ReadLogAs.TRACE.name,
                                                           win_size=win_size,
                                                           metrics=metrics,
                                                           adaptive_controlflow_approach=parameters.adaptive_controlflow_approach,
                                                           detector_class=detector_class,
                                                           save_sublogs=parameters.save_sublogs,
                                                           update_model=parameters.update_model)
    framework.run_script(parameters)

    running = framework.get_status_running()
    while running:
        print(f'Waiting for IPDD finishes ... Status running: {running}')
        time.sleep(2)  # in seconds
        running = framework.get_status_running()
    print(f'IPDD finished drift analysis')

    detected_drifts = None
    total_of_itens = framework.get_number_of_items()
    if parameters.approach == Approach.FIXED.name:
        windows, detected_drifts = framework.get_windows_with_drifts()
        print(f'IPDD detect control-flow drift in windows {windows} - traces {detected_drifts}')
    elif parameters.approach == Approach.ADAPTIVE.name:
        if parameters.perspective == AdaptivePerspective.TIME_DATA.name:
            detected_drifts = {}
            # get the activities that report a drift using the change detector
            for activity in framework.get_activities_with_drifts():
                if parameters.perspective == AdaptivePerspective.TIME_DATA.name and \
                        parameters.read_log_as == ReadLogAs.EVENT.name:
                    indexes = framework.initial_event_ids[activity]
                    detected_drifts[activity] = list(indexes)[1:]
                else:
                    indexes = framework.initial_indexes[activity]
                    detected_drifts[activity] = list(indexes.keys())[1:]
                print(
                    f'IPDD detect drifts for attribute {parameters.attribute}-{attribute_name} in activity {activity} in indexes {detected_drifts}')
                # get information about control-flow metrics
                windows, traces = framework.get_windows_with_drifts(activity)
                if len(traces) > 0:
                    print(
                        f'IPDD detect control-flow drift for activity {activity} in windows {windows} - traces {traces}')
        elif parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
            detected_drifts = framework.get_initial_trace_indexes()
            # remove the index 0
            detected_drifts = detected_drifts[1:]
            print(
                f'Adaptive IPDD detect control-flow drifts in traces {detected_drifts}')
            # get information about control-flow metrics
            windows, traces = framework.get_windows_with_drifts()
            print(
                f'Similarity metrics confirm the drifts in  {traces}')
        else:
            print(f'Perspective not identified: {parameters.perspective}')
    else:
        print(f'Approach not identified: {parameters.approach}')

    metrics = None
    if parameters.approach == Approach.FIXED.name:
        if real_drifts is not None:
            metrics = framework.evaluate(real_drifts, detected_drifts, total_of_itens)
            print(f'IPDD F-score: {metrics}')
    elif parameters.approach == Approach.ADAPTIVE.name:
        if real_drifts is not None:
            if parameters.perspective == AdaptivePerspective.TIME_DATA.name:
                # if len(detected_drifts) > 0:
                print(f'********* IPDD evaluation metrics results *********')
                metrics = {}
                for activity in framework.get_all_activities():
                    if activity in detected_drifts:
                        metrics[activity] = framework.evaluate(real_drifts, detected_drifts[activity], total_of_itens,
                                                               activity)
                    else:
                        # if IPDD do not detect any drift in the activity
                        metrics[activity] = framework.evaluate(real_drifts, [], total_of_itens, activity)
                # else:
                #     print(f'********* IPDD did not detect any drift. No F-score results *********')
            if parameters.perspective == AdaptivePerspective.CONTROL_FLOW.name:
                metrics = framework.evaluate(real_drifts, detected_drifts, total_of_itens)
    else:
        print(f'Approach not identified: {parameters.approach}')

    if metrics:
        return detected_drifts, metrics
    else:
        return detected_drifts


if __name__ == '__main__':
    main()
