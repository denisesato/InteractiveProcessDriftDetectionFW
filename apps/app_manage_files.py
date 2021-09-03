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
import base64
import os
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app, get_user_id
from app import framework

# configuring a navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("About IPDD", href="/")),
    ],
    brand="IPDD Framework - Manage Event Logs",
    color="primary",
    dark=True,
)

div_instructions = html.H5('Start by loading and selecting the event log (XES format) to be analyzed.')

load_files_div = html.Div([
    html.P(
        'Here you can load the event logs for analyzing process drifts. If the log is already '
        'loaded, just click on its name to continue.'),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drop your files here or ',
            html.A('Select a File', className='link-primary')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '0px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    )])

alert_error = dbc.Alert(
    "The event log must be a XES file.",
    id="alert-error",
    dismissable=True,
    color="danger"
)

show_files_div = html.Div([
    html.H4('Loaded event logs.'),
    html.H5('Select the file you want to analyze:'),
    html.Div(id='div-alerts', children=[]),
    html.Div(id='list-files'),
], className='mt-2')

main_card = [
    dbc.CardBody(
        [
            div_instructions,
            load_files_div,
            show_files_div
        ]),
]

def get_layout():
    # main layout of the page
    layout = [
        dbc.Row([
            dbc.Col(navbar, width=12)
        ]),
        dbc.Row([
            dbc.Col(main_card, className='mt-2', width=12)
        ]),
    ]

    return layout


def save_file(content, filename):
    if '.xes' in filename:
        user = get_user_id()

        # Save the loaded file in the input path
        uploaded_file = os.path.join(framework.get_input_path(user_id=user),
                                     f'{filename}')
        print(f'Saving event log in the input data directory: {uploaded_file}')

        data = content.encode("utf8").split(b";base64,")[1]
        with open(uploaded_file, "wb") as fp:
            fp.write(base64.decodebytes(data))
            return True
    else:
        print(f'Event log must be a XES file: {filename}')
        return False


def list_uploaded_files():
    user = get_user_id()
    files = []
    for filename in os.listdir(framework.get_input_path(user_id=user)):
        path = os.path.join(framework.get_input_path(user_id=user), filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def show_file_link(filename):
    location = f'/apps/app_preview_file?filename={filename}'
    return dcc.Link(filename, href=location)


@app.callback([Output('list-files', 'children'),
               Output('div-alerts', 'children')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(content, name):
    status = None
    if content is not None:
        if not save_file(content, name):
            status = alert_error

    files = list_uploaded_files()
    if len(files) == 0:
        return [html.Li("No event logs loaded yet!")], status
    else:
        return [html.Li(show_file_link(filename)) for filename in files], status
