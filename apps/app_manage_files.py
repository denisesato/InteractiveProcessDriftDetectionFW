import base64
import os

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
from components.info import Info

layout = html.Div([
    html.H3('Carregue o arquivo contendo os dados de eventos:'),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Solte seu arquivo aqui ou ',
            html.A('Selecione um arquivo')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Div(id='list-files'),
])


def save_file(content, filename):
    # Salva arquivo carregado
    uploaded_file = os.path.join(Info.get_data_input_path(),
                                 f'{filename}')
    print(f'Salvando arquivo: {uploaded_file}')

    data = content.encode("utf8").split(b";base64,")[1]
    with open(uploaded_file, "wb") as fp:
        fp.write(base64.decodebytes(data))


def list_uploaded_files():
    files = []
    for filename in os.listdir(Info.get_data_input_path()):
        path = os.path.join(Info.get_data_input_path(), filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def show_file_link(filename):
    location = f'/apps/app_preview_file?filename={filename}'
    return dcc.Link(filename, href=location)


@app.callback(Output('list-files', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(content, name):
    if content is not None:
        save_file(content, name)

    files = list_uploaded_files()
    if len(files) == 0:
        return [html.Li("Sem arquivos carregados!")]
    else:
        return [html.Li(show_file_link(filename)) for filename in files]
