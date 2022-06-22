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
from ipdd_massive import run_massive_fixed_controlflow, run_massive_adaptive_controlflow_trace_by_trace

if __name__ == '__main__':
    # path = 'D:\Doutorado_Experimentos\datasets\dataset1'
    path = 'C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    logs = [
        'cb2.5k.xes',
        'cd5k.xes'
    ]
    windows = [
        125, 250
    ]
    run_massive_fixed_controlflow(path, logs, windows)

    # path = 'D:\Doutorado_Experimentos\datasets\dataset1'
    path = 'C:/Users/denis/OneDrive/Documents/Doutorado/Bases de Dados/DadosConceptDrift/IPDD_Datasets/dataset1'
    logs = [
        'cb2.5k.xes',
    ]
    windows = [
        75
    ]
    deltas = [
        0.002
    ]
    run_massive_adaptive_controlflow_trace_by_trace(path, logs, windows, deltas)
