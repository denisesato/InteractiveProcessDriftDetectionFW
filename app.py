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
import dash
import dash_bootstrap_components as dbc
from flask import session

from components.ippd_fw import InteractiveProcessDriftDetectionFW

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                suppress_callback_exceptions=True)

app.title = 'IPDD Framework'
server = app.server
server.secret_key = b'e\x19\xf5\xcaZ\x89\xff\xf4\xbf\x15\x14S.\x931\xbd'
framework = InteractiveProcessDriftDetectionFW(model_type='dfg')


def get_user_id():
    # recover the user from session
    user = 'unknown'
    if session.get('user'):
        user = session['user']
    return user
