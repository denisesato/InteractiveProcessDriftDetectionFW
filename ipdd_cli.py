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

from components.apply_window import WindowType, WindowUnity
from components.ippd_fw import InteractiveProcessDriftDetectionFW


def main():
    pathname = os.path.dirname(os.path.abspath(__file__))
    print(f'Pathname of script: {pathname}')

    parser = argparse.ArgumentParser(description='IPDD FW command line')
    parser.add_argument('--win_type', '-wt', help='Window type: t - stream of traces or e - event stream', default='t')
    parser.add_argument('--win_unity', '-wu',
                        help='Window unity: u - amount of traces or events, h - hours, or d - days', default='u')
    parser.add_argument('--win_size', '-wz', type=int, required=True,
                        help='Window size: numeric value indicating the total of window unities for each window')
    parser.add_argument('--event_log', '-l', required=True,
                        help='Event log: path and name of the event log using XES format')
    parser.add_argument('--real_drifts', '-rd', type=int, nargs='+',
                        help='Real drifts: list of trace indexes from actual drifts (separated by a space), used for '
                             'evaluation')

    args = parser.parse_args()
    if args.win_type == 't':
        win_type = WindowType.TRACE.name
    elif args.win_type == 'e':
        win_type = WindowType.EVENT.name

    if args.win_unity == 'u':
        win_unity = WindowUnity.UNITY.name
    elif args.win_unity == 'h':
        win_unity = WindowUnity.HOUR.name
    elif args.win_unity == 'd':
        win_unity = WindowUnity.DAY.name

    win_size = args.win_size
    event_log = args.event_log
    real_drifts = args.real_drifts

    print('----------------------------------------------')
    print('Configuration:')
    print('----------------------------------------------')
    print(f'Window type: {win_type}')
    print(f'Window unity: {win_unity}')
    print(f'Window size: {win_size}')
    print(f'Event log: {event_log}')
    if args.real_drifts is not None:
        print(f'Real drifts: {real_drifts}')
    print('----------------------------------------------')

    framework = InteractiveProcessDriftDetectionFW(script=True)
    print(f'Starting analyzing process drifts ...')
    framework.run(event_log, win_type, win_unity, win_size)

    running = framework.get_status_running()
    while running:
        print(f'Waiting for IPDD finishes ... Status running: {running}')
        time.sleep(60)  # in seconds
        running = framework.get_status_running()
    print(f'IPDD finished drift analysis')

    window_candidates = framework.get_windows_candidates()
    print(f'IPDD detect drift in windows {window_candidates}')

    if args.real_drifts is not None:
        f_score = framework.evaluate(window_candidates, real_drifts, win_size)
        print(f'IPDD f-score: {f_score}')


if __name__ == '__main__':
    main()
