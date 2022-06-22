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
        # 'Log_Paper_Lathe3.xes',
    ]
    change_points = [
        [],
        [349],  # trace marcado no nome do log
        [0, 26, 100, 148, 215],  # trace inicial e traces após a parada para manutenção
        [205, 858, 1246, 1555, 2006],  # traces marcados como QuedaDesempenho - TRUE
        [426, 706, 1043, 1731, 2279],  # traces marcados como QuedaDesempenho - TRUE
        # [499, 1250, 2000]  # traces marcados como QuedaDesempenho - TRUE
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
    # classificado pelo Edson
    # 1076    up
    # 1629    down
    # 2315    up
    # 3038    down
    # 3311    up
    # 4451    down
    # 4486    up
    # 5400    down
    # 6095    up
    # 6577    down
    # 7969    up
    # 8683    down
    cps = [1075, 2314, 3310, 4485, 6094, 7968]
    file = os.path.join(folder, log)
    deltas = [0.002, 0.05, 0.1, 0.3, 1]
    for delta in deltas:
        print(f'Executando experimento para o log {file} adaptativo TEMPERATURA com delta {delta} ...')
        str_changepoints = ""
        for change_point in cps:
            str_changepoints = f'{str_changepoints} {change_point}'
        subprocess.run(f"ipdd_cli.py -a a -l {file} -at OTHER -atname Temperatura -d {delta} -rd {str_changepoints}",
                       shell=True)


def one_experiment_for_testing():
    folder = '"C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/LogsProducao/Artificiais/SelecionadosArtigo"'
    log_name = [
        'DR_MS.xes',
    ]
    change_points = [
        [0, 26, 100, 148, 215],  # trace inicial e traces após a parada para manutenção
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


if __name__ == '__main__':
    selected_experiments()
    # one_experiment_for_testing()
