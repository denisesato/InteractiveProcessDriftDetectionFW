import subprocess
import os


def trace_by_trace_without_update_model():
    folder = '"C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1"'
    change_patterns = [
        'cb',
        # 'cd',
        # 'cf',
        # 'cm',
        # 'cp',
        # 'IOR',
        # 'IRO',
        # 'lp',
        # 'OIR',
        # 'ORI',
        # 'pl',
        # 'pm',
        # 're',
        # 'RIO',
        # 'ROI',
        # 'rp',
        # 'sw'
    ]
    sizes = [
        '2.5k',
        # '5k',
        # '7.5k',
        # '10k'
    ]
    deltas = [
        0.002
    ]
    winsizes = [
        100
    ]

    for cp in change_patterns:
        for s in sizes:
            for w in winsizes:
                for d in deltas:
                    log = f'{cp}{s}.xes'
                    filename = os.path.join(folder, log)
                    print(f'Adaptive IPDD control-flow Trace by Trace {filename} - window {w} delta {d}')
                    subprocess.run(f"ipdd_cli.py -l {filename} -w {w} -a a -p cf -cfa t -d {d} --no_update_model", shell=True)


if __name__ == '__main__':
    trace_by_trace_without_update_model()