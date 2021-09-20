import subprocess
import os

if __name__ == '__main__':
    folder = 'C:/Users/denis/OneDrive/Documents/Doutorado/Artigos_Desenvolvidos/Artigo_Ruschel_Manutencao/Logs'
    log_name = 'PerdaDesempenho1-Manut0-Data.xes'
    file = os.path.join(folder, log_name)
    min_w = 30
    total_of_cases = 250
    max_w = total_of_cases / 2
    for w in range(min_w, int(max_w)+1, 1):
        # print(f'Window {w} - condição {total_of_cases % w}')
        # if total_of_cases % w == 0:
        #     print(f'Executando experimento para o log {file} com janela {w} ...')
        #     subprocess.run(f"ipdd_cli.py -wz {w} -l {file} -mt SOJOURN_TIME", shell=True)
        print(f'Executando experimento para o log {file} com janela {w} ...')
        subprocess.run(f"ipdd_cli.py -wz {w} -l {file} -mt SOJOURN_TIME", shell=True)