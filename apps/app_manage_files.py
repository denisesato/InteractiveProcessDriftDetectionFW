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
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Output
from app import du, get_user_id, framework

# configuring a navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("About IPDD", href="/")),
    ],
    brand="IPDD - Manage Event Logs",
    color="primary",
    dark=True,
)


def get_layout():
    div_instructions = html.H5('Start by loading and selecting the event log (XES format) to be analyzed.')

    load_files_div = html.Div([
        html.P(
            'Here you can load the event logs for analyzing process drifts. If the log is already '
            'loaded, just click on its name to continue.'),

        du.Upload(id='dash-uploader',
                  max_file_size=1800,  # 1800 Mb
                  filetypes=['xes', 'xes.gz'],
                  upload_id=get_user_id()),
    ])

    show_files_div = html.Div([
        html.H4('Loaded event logs.'),
        html.H5('Select the file you want to analyze:'),
        html.Div(id='div-alerts', children=[]),
        html.Div(id='list-files', children=return_li_files()),
    ], className='mt-2')

    # main layout of the page
    layout = [
        dbc.Row([
            dbc.Col(navbar, width=12)
        ]),
        dbc.Row([
            dbc.Col(
                dbc.CardBody(
                    [
                        div_instructions,
                        load_files_div,
                        show_files_div
                    ]), className='mt-2', width=12),
        ]),
    ]

    return layout


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


def return_li_files():
    files = list_uploaded_files()
    if len(files) == 0:
        return [html.Li("No event logs loaded yet!")]
    else:
        return [html.Li(show_file_link(filename)) for filename in files]


@du.callback(
    output=Output('list-files', 'children'),
    id='dash-uploader',
)
def update_files_list(filename):
    print(f'User uploaded file {filename}')
    return return_li_files()
