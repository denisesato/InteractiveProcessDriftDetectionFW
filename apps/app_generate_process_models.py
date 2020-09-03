import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State
from app import app

from apply_window import WindowUnity, WindowType, generate_models, get_model

layout = html.Div([
    html.Div([
        html.H3(children='Selecione como realizar o janelamento'),

        dcc.RadioItems(id='window-type',
                       options=[
                           {'label': 'Stream de Traces', 'value': WindowType.TRACE},
                           {'label': 'Stream de Eventos', 'value': WindowType.EVENT},
                       ],
                       value=WindowType.TRACE,
                       labelStyle={'display': 'inline-block'}
                       ),

        dcc.RadioItems(id='window-unity',
                       options=[
                           {'label': 'Unidade', 'value': WindowUnity.UNITY},
                           {'label': 'Horas', 'value': WindowUnity.HOUR},
                           {'label': 'Dias', 'value': WindowUnity.DAY}
                       ],
                       value=WindowUnity.UNITY,
                       labelStyle={'display': 'inline-block'}
                       ),

        dcc.Input(id='input-window-size', type='number', value='0'),
        html.Button(id='submit-button-state', n_clicks=0, children='Gerar processos'),
        html.Div(id='window-size', style={'display': 'none'})
    ]),

    html.Div([
        dcc.Slider(
            id='window-slider',
            min=1,
            step=None
        ),
    ]),

    html.Div([
        dash_interactive_graphviz.DashInteractiveGraphviz(
            id="graph-with-slider"),
    ]),

    html.Div(id='final-window', style={'display': 'none'})
])


@app.callback([Output('window-slider', 'max'),
               Output('window-slider', 'marks'),
               Output('window-slider', 'value')],
              [Input('final-window', 'children')])
def update_slider(value):
    if not value:
        value = 0
    else:
        print('Problema na geração dos modelos, não foi possível obter final-window')

    print(f'Atualiza slider {value}')
    mark = {str(w): str(w) for w in range(1, value)}

    return value, mark, 1

@app.callback([Output('window-size', 'children'),
               Output('final-window', 'children')],
              [Input('submit-button-state', 'n_clicks')],
              [State('input-window-size', 'value'),
               State('window-type', 'value'),
               State('window-unity', 'value'),
               State('hidden-filename', 'children')])
def update_output(n_clicks, input_window_size, window_type, window_unity, file):
    if file and input_window_size != '0':
        print(f'Usuário selecionou janela por {window_type}-{window_unity} de tamanho {input_window_size} - arquivo {file}')
        window_count = generate_models(window_type, window_unity, int(input_window_size), file)

        return input_window_size, window_count
    return 0, 0


@app.callback(Output('graph-with-slider', 'dot_source'),
              [Input('window-slider', 'value'),
               Input('final-window', 'children')],
               [State('hidden-filename', 'children')])
def update_figure(window_value, window_size, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = """digraph  {
          node[style="filled"]
        }
        """
    if 'final-window' in changed_id:
        process_map = get_model(1, file)
    elif 'window-slider' in changed_id:
        process_map = get_model(window_value, file)
    return str(process_map)



