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
from app import app
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
from app import server  # needed for gunicorn
from apps import app_manage_files, app_process_models, app_preview_file, app_initial

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content'),
            html.Div(id='hidden-filename', hidden=True),
        ], width=12)
    ]),
])


@app.callback([Output('page-content', 'children'), Output('hidden-filename', 'children')],
              [Input('url', 'pathname')],
              [State('url', 'search')])
def display_page(pathname, search):
    filename = ''
    if search:
        filename = search.partition('?filename=')[2]

    if pathname == '/':
        return app_initial.get_layout(), ''
    if pathname == '/apps/app_manage_files':
        return app_manage_files.get_layout(), ''
    elif pathname == '/apps/app_process_models':
        return app_process_models.get_layout(), filename
    elif pathname == '/apps/app_preview_file':
        return app_preview_file.get_layout(), filename
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, threaded=True)
    # app.run_server(debug=True)
