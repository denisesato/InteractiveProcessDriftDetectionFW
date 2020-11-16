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

    args = parser.parse_args()
    if args.win_type == 't':
        win_type = WindowType.TRACE
    elif args.win_type == 'e':
        win_type = WindowType.EVENT

    if args.win_unity == 'u':
        win_unity = WindowUnity.UNITY
    elif args.win_unity == 'h':
        win_unity = WindowUnity.HOUR
    elif args.win_unity == 'd':
        win_unity = WindowUnity.DAY

    win_size = args.win_size
    event_log = args.event_log

    print('----------------------------------------------')
    print('Configuration:')
    print('----------------------------------------------')
    print(f'Window type: {win_type}')
    print(f'Window unity: {win_unity}')
    print(f'Window size: {win_size}')
    print(f'Event log: {event_log}')
    print('----------------------------------------------')

    framework = InteractiveProcessDriftDetectionFW(pathname=pathname)
    window_count = framework.run(event_log, win_type, win_unity, win_size)
    print(f'Mined [{window_count}] process models')

    while framework.get_status_running():
        print('Waiting for IPDD finish similarity metrics...')
        time.sleep(1000)

    return


if __name__ == '__main__':
    main()