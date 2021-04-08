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

from pm4py.objects.conversion.log import converter as log_converter
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app
from components.ippd_fw import InteractiveProcessDriftDetectionFW

framework = InteractiveProcessDriftDetectionFW()

layout = [
        html.Div([
            html.Div(
                dcc.Link('Analyze process drift', id='link-analyze', href='/apps/app_process_models')
            ),
            html.Div(
                dcc.Link('Back to file management', href='/apps/app_manage_files')
            ),
            html.H3('Event data preview:'),
            html.Div(id='preview-event-data'),
        ])
    ]


def show_file(filename):
    max_lines = 50
    try:
        if '.csv' in filename:
            # Assume que é um arquivo CSV
            df = pd.read_csv(filename, ';', nrows=max_lines)
        elif '.xls' in filename:
            # Assume que é um arquivo excel
            df = pd.read_excel(filename, nrows=max_lines)
        elif '.xes' in filename:
            # Assume que é um arquivo XES
            variant = xes_importer.Variants.ITERPARSE
            parameters = {variant.value.Parameters.MAX_TRACES: max_lines,
                          variant.value.Parameters.TIMESTAMP_SORT: True}
            log = xes_importer.apply(filename, variant=variant, parameters=parameters)

            df = log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)
    except Exception as e:
        print(e)
        return html.Div([
            f'Error when processing file: {filename}.'
        ])

    return html.Div([
        html.H5(filename),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line
    ])


@app.callback([Output('link-analyze', 'href'),
               Output('preview-event-data', 'children')],
              [Input('hidden-filename', 'children')])
def display_page(file):
    if file:
        filename = os.path.join(framework.get_input_path(), file)
        return f'/apps/app_process_models?filename={file}', show_file(filename)
