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
import os

from components.parameters import Paths, AdaptivePerspective, ControlflowAdaptiveApproach
from run_UTFPR_analysis import UTFPRConfigurationControlflow


def generate_path_controlflow_adaptive_trace():
    user = 'script'
    perspective = AdaptivePerspective.CONTROL_FLOW.name
    approach = ControlflowAdaptiveApproach.TRACE.name
    for log in UTFPRConfigurationControlflow.lognames:
        for winsize in UTFPRConfigurationControlflow.windows:
            for delta in UTFPRConfigurationControlflow.deltas:
                folder_params = f'{perspective}_{approach}_win{winsize}_delta{delta}'
                path = os.path(Paths.DATA_PATH,
                               Paths.OUTPUT_PATH,
                               user,
                               Paths.ADAPTIVE_PATH,
                               log,
                               folder_params,
                               Paths.MODELS_PATH)
                