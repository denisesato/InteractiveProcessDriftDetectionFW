import subprocess
import os


def all_experiments():
    folder = '"C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/LogsProducao/Artificiais"'
    log_name = [
        'PerdaDesempenho0-Manut0-Data.xes',
        'PerdaDesempenho1-Manut0-Data.xes',
        'PerdaDesempenho1-Manut1-Data.xes',
        'LogArtificial01P300C10A.xes',
        'LogArtificial01P300C100A.xes',
        'LogArtificial01P300C1000A.xes',
        'LogArtificial1P350C10A.xes',
        'LogArtificial1P350C100A.xes',
        'LogArtificial1P350C1000A.xes',
        'LogArtificial5P400C10A.xes',
        'LogArtificial5P400C100A.xes',
        'LogArtificial5P400C1000A.xes'
    ]
    for log in log_name:
        file = os.path.join(folder, log)
        deltas = [0.002, 0.05, 0.1, 0.3, 1]
        for delta in deltas:
            print(f'Executando experimento para o log {file} adaptativo com delta {delta} ...')
            subprocess.run(f"ipdd_cli.py -a a -l {file} -d {delta}", shell=True)


def selected_experiments():
    folder = '"C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/LogsProducao/Artificiais/SelecionadosArtigo"'
    log_name = [
        'ST.xes',
        'DR.xes',
        'DR_MS.xes',
        'Log_Paper_Lathe1.xes',
        'Log_Paper_Lathe2.xes',
        'Log_Paper_Lathe3.xes'
    ]
    change_points = [
        [],
        [349],
        [25, 99, 147, 214],
        [506, 1026, 1487, 1805],
        [506, 1026, 1487, 1805],
        [448, 897, 1346, 1795, 1892, 2381, 2498]
    ]
    for log, cps in zip(log_name, change_points):
        file = os.path.join(folder, log)
        deltas = [0.002, 0.05, 0.1, 0.3, 1]
        for delta in deltas:
            print(f'Executando experimento para o log {file} adaptativo SOJOURN TIME com delta {delta} ...')
            str_changepoints = ""
            if len(cps) == 0:
                str_changepoints = '0'
            else:
                for change_point in cps:
                    str_changepoints = f'{str_changepoints} {change_point}'
            subprocess.run(f"ipdd_cli.py -a a -l {file} -d {delta} -rd {str_changepoints}", shell=True)

    # temperature experiment
    log = 'Log_Paper_Lathe4.xes'
    cps = [448, 897, 1346, 1795, 1892, 2381, 2498]
    file = os.path.join(folder, log)
    deltas = [0.002, 0.05, 0.1, 0.3, 1]
    for delta in deltas:
        print(f'Executando experimento para o log {file} adaptativo TEMPERATURA com delta {delta} ...')
        str_changepoints = ""
        for change_point in cps:
            str_changepoints = f'{str_changepoints} {change_point}'
        subprocess.run(f"ipdd_cli.py -a a -l {file} -at OTHER -atname Temperatura -d {delta} -rd {str_changepoints}",
                       shell=True)


if __name__ == '__main__':
    selected_experiments()
