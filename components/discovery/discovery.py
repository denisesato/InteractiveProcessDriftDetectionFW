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

from graphviz import Source


class Discovery:
    def generate_process_model(self, sub_log, models_path, event_data_original_name, w_count, activity=''):
        pass

    def get_process_model(self, models_path, log_name, window, activity):
        map_file = self.model_type_definitions.get_model_filename(log_name, window)
        models_path = self.model_type_definitions.get_models_path(models_path, log_name, activity)

        if os.path.exists(os.path.join(models_path, map_file)):
            gviz = Source.from_file(filename=map_file, directory=models_path)
            return gviz.source

        return """
                digraph  {
                  node[style="filled"]
                  a ->b->d
                  a->c->d
                }
                """