import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State

from app import app
from components.apply_window import WindowUnity, WindowType
from components.ippd_fw import ProcessingStatus
from components.ippd_fw import InteractiveProcessDriftDetectionFW

framework = InteractiveProcessDriftDetectionFW()

layout = html.Div([
    html.Div([
        html.P(children='Set the windowing strategy parameters'),

        dcc.RadioItems(id='window-type',
                       options=[
                           {'label': 'Stream of Traces', 'value': WindowType.TRACE},
                           {'label': 'Event Stream', 'value': WindowType.EVENT},
                       ],
                       value=WindowType.TRACE,
                       labelStyle={'display': 'inline-block'}
                       ),

        dcc.RadioItems(id='window-unity',
                       options=[
                           {'label': 'Unity', 'value': WindowUnity.UNITY},
                           {'label': 'Hours', 'value': WindowUnity.HOUR},
                           {'label': 'Days', 'value': WindowUnity.DAY}
                       ],
                       value=WindowUnity.UNITY,
                       labelStyle={'display': 'inline-block'}
                       ),

        dcc.Input(id='input-window-size', type='number', value='0'),
        html.Button(id='submit-button-state', n_clicks=0, children='Mine models'),
        html.Div(id='window-size', style={'display': 'none'}),

        html.Div(dcc.Link('Back to file management', href='/apps/app_manage_files')),

        html.Hr(),
        html.Div(id='div-status-mining', children=''),
        html.Div(id='div-status-similarity', children=''),

        html.Hr(),
        html.Div(id='div-similarity-metrics-value'),
        html.Div(id='div-differences'),
    ], className="three columns"),

    html.Div([html.Div([
        dcc.Slider(
            id='window-slider',
            step=None,
            included=False,
            marks={0: {'label': '0'}}
        ),
    ]),

        html.Div([
            dash_interactive_graphviz.DashInteractiveGraphviz(
                id="graph-with-slider", dot_source=''),
        ]),
    ], className="nine columns"),

    html.Div([
        html.Div(id='final-window', style={'display': 'none'}),
        html.Div(id='diff'),

        dcc.Interval(
            id='check-similarity-finished',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        )]),
])


@app.callback([Output('window-slider', 'min'),
               Output('window-slider', 'max'),
               Output('window-slider', 'value')],
              [Input('final-window', 'children')])
def update_slider(final_window):
    if not final_window:
        app.logger.error('Final-window ainda não definida')
        app.logger.info(f'Atualiza window-slider min: 0, max: 0, value: 0')
        return 0, 0, 0

    app.logger.info(f'Atualiza window-slider min: 1, max: {final_window}, value: 1')
    return 1, final_window, 1


@app.callback([Output('window-size', 'children'),
               Output('final-window', 'children')],
              [Input('submit-button-state', 'n_clicks')],
              [State('input-window-size', 'value'),
               State('window-type', 'value'),
               State('window-unity', 'value'),
               State('hidden-filename', 'children')])
def update_output(n_clicks, input_window_size, window_type, window_unity, file):
    if file != '' and input_window_size != '0':
        window_count = framework.run(file, window_type, window_unity, int(input_window_size))
        return input_window_size, window_count
    return 0, 0


@app.callback([Output('graph-with-slider', 'dot_source'),
               Output('div-similarity-metrics-value', 'children'),
               Output('div-differences', 'children')],
              Input('window-slider', 'value'),
              State('hidden-filename', 'children'))
def update_figure(window_value, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = """
        digraph  {
          node[style="filled"]
          a ->b->d
          a->c->d
        }
        """
    div_similarity = ''
    div_differences = ''
    if 'window-slider' in changed_id and window_value != 0:
        process_map = framework.get_model(file, window_value)
        if framework.get_metrics_status() == ProcessingStatus.IDLE:
            metrics = framework.get_metrics_manager().get_metrics_info(window_value)
            for metric in metrics:
                div_similarity += f'Similarity metric [{metric.name}]: {metric.value}'
                if len(metric.diff) > 0:
                    div_differences += f'Differences [{metric.name}]: {metric.diff}'
    return process_map, div_similarity, div_differences


@app.callback([Output('div-status-similarity', 'children'),
               Output('div-status-mining', 'children'),
               Output('window-slider', 'marks')],
              Input('check-similarity-finished', 'n_intervals'),
              State('window-slider', 'marks'))
def update_metrics(n, marks):
    ###################################################################
    # ATUALIZA INTERFACE EM RELAÇÃO A MINERAÇÃO DE PROCESSOS
    ###################################################################
    div_status_mining = framework.check_status_mining()

    ###################################################################
    # ATUALIZA INTERFACE EM RELAÇÃO AO CÁLCULO DE MÉTRICAS
    ###################################################################
    div_similarity_status, windows, windows_with_drifts = framework.check_status_similarity_metrics()
    for w in range(1, framework.get_windows() + 1):
        label = str(w) + '|' + str(framework.get_initial_indexes()[(w-1)])
        if windows_with_drifts and w in windows_with_drifts:
            marks[str(w)] = {'label': label, 'style': {'color': '#f50'}}
        else:
            marks[str(w)] = {'label': label}

    return div_similarity_status, div_status_mining, marks
