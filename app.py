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
import dash_uploader as du
from flask import session
from components.ippd_fw import InteractiveProcessDriftDetectionFW
import uuid

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                suppress_callback_exceptions=True)

framework = InteractiveProcessDriftDetectionFW(model_type='dfg')
app.title = 'IPDD Framework'
# configure the upload folder
du.configure_upload(app, framework.get_input_path())
server = app.server
app.server.secret_key = b'e\x19\xf5\xcaZ\x89\xff\xf4\xbf\x15\x14S.\x931\xbd'


def get_user_id():
    # recover the user from session
    user = 'unknown'
    if not session.get('user'):
        print(f'Creating user session...')
        session['user'] = str(uuid.uuid4())
    elif session.get('user'):
        user = session['user']
        # print(f'Get user from session {user}')
    return user
