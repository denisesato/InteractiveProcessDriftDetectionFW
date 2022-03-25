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
from dash import dash_table
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output
from app import app, get_user_id, framework

# configuring a navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Process Drift Analysis", id='drift-analysis-link')),
        dbc.NavItem(dbc.NavLink("Manage Files", href="/apps/app_manage_files")),
        dbc.NavItem(dbc.NavLink("About IPDD", href="/")),
    ],
    brand="IPDD Framework - Preview Selected File",
    color="primary",
    dark=True,
)

main_panel = html.Div([
        html.H5(['If the file is ok click on ',
                 dbc.CardLink(children='Process Drift Analysis', id='link-analyze', href='#')],
                className='mt-2'),
        dbc.Spinner(html.Div(id='preview-event-data', className='mt-3'))
    ])


def get_layout():
    # main layout of the page
    layout = [
        dbc.Row([
            dbc.Col(navbar, width=12)
        ]),
        dbc.Row([
            dbc.Col(main_panel, className='mt-2', width=12)
        ])
    ]

    return layout


def show_file(complete_filename, filename):
    try:
        print(f'Importing event log: {complete_filename}')
        framework.import_log(complete_filename, filename)
    except Exception as e:
        print(e)
        return html.Div([
            f'Error when processing file: {complete_filename}.'
        ])

    div_file_info = html.Div([
        html.H5(f'First {framework.MAX_TRACES} traces of the file: {filename}'),
        html.H5(f'Total of cases: {framework.current_log.total_of_cases} and Median case duration: '
                f'{round(framework.current_log.median_case_duration_in_hours, 2)} hrs'),
        dash_table.DataTable(
            data=framework.current_log.first_traces.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in framework.current_log.first_traces.columns],
            style_cell={'textAlign': 'left'},
            style_as_list_view=True,
            sort_action="native",
            sort_mode='multi',
            page_action="native",
            page_current=0,
            page_size=20,
        ),
    ])
    return div_file_info


@app.callback([Output('link-analyze', 'href'),
               Output('preview-event-data', 'children'),
               Output('drift-analysis-link', 'href')],
              [Input('hidden-filename', 'children')])
def display_page(file):
    if file:
        user = get_user_id()
        filename = os.path.join(framework.get_input_path(user_id=user), file)
        return f'/apps/app_process_models?filename={file}', show_file(filename, file), \
               f'/apps/app_process_models?filename={file}'
