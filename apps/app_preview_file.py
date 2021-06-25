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

import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app
from components.ippd_fw import InteractiveProcessDriftDetectionFW

framework = InteractiveProcessDriftDetectionFW()

# main layout of the page
layout = [
    dbc.Row(
        dbc.Col(html.H3('Preview Selected File'), className='text-primary mt-2')
    ),

    dbc.Row(
        dbc.Col([html.H5(['If the file is ok click on ',
                          dbc.CardLink(children='Process Drift Analysis', id='link-analyze', href='#')])
                 ], className='mt-2')),

    dbc.Row(
        dbc.Col([
            dbc.Spinner(html.Div(id='preview-event-data', className='mt-2'))
        ])
    )
]


def show_file(complete_filename, filename):
    try:
        framework.import_log(complete_filename, filename)
    except Exception as e:
        print(e)
        return html.Div([
            f'Error when processing file: {complete_filename}.'
        ])

    return html.Div([
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


@app.callback([Output('link-analyze', 'href'),
               Output('preview-event-data', 'children')],
              [Input('hidden-filename', 'children')])
def display_page(file):
    if file:
        filename = os.path.join(framework.get_input_path(), file)
        return f'/apps/app_process_models?filename={file}', show_file(filename, file)
