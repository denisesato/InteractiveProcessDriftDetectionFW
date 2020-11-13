import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State

from app import app
from components.apply_window import WindowUnity, WindowType, AnalyzeDrift, ModelAnalyzes


class ProcessingStatus:
    NOT_STARTED = 'NOT_STARTED'
    IDLE = 'IDLE'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'
    TIMEOUT = 'TIMEOUT'


class Control:
    def __init__(self):
        self.metrics_status = ProcessingStatus.NOT_STARTED
        self.mining_status = ProcessingStatus.NOT_STARTED
        self.metrics_manager = None

    def finish_mining_calculation(self):
        self.mining_status = ProcessingStatus.FINISHED

    def start_mining_calculation(self):
        self.mining_status = ProcessingStatus.STARTED

    def reset_mining_calculation(self):
        self.mining_status = ProcessingStatus.IDLE

    def get_mining_status(self):
        return self.mining_status

    def finish_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.FINISHED

    def start_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.STARTED

    def reset_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.IDLE

    def time_out_metrics_calculation(self):
        self.metrics_status = ProcessingStatus.TIMEOUT

    def get_metrics_status(self):
        return self.metrics_status

    def set_metrics_manager(self, metrics_manager):
        self.metrics_manager = metrics_manager

    def get_metrics_manager(self):
        return self.metrics_manager


control = Control()

layout = html.Div([
    html.Div([
        html.P(children='Set the windowing strategy parameters'),

        dcc.RadioItems(id='window-type',
                       options=[
                           {'label': 'Stream of Traces', 'value': WindowType.TRACE},
                           # {'label': 'Event Stream', 'value': WindowType.EVENT},
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
        html.Div(id='div-status-mining'),
        html.Div(id='div-status-similarity'),

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
        print(f'Usuário selecionou janela {window_type}-{window_unity} de tamanho {input_window_size} - arquivo {file}')
        control.start_metrics_calculation()
        control.start_mining_calculation()
        models = AnalyzeDrift(window_type, window_unity, int(input_window_size), file, control)
        window_count = models.generate_models()
        control.finish_mining_calculation()
        print(f'Retornando final-window [{window_count}]')
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
    div_status = ''
    div_similarity = ''
    div_differences = ''
    if 'window-slider' in changed_id and window_value != 0:
        process_map = ModelAnalyzes.get_model(file, window_value)
        if control.get_metrics_status() == ProcessingStatus.IDLE:
            metrics = control.get_metrics_manager().get_metrics_info(window_value)
            for metric in metrics:
                div_similarity += f'Similarity metric [{metric.name}]: {metric.value}'
                if len(metric.diff) > 0:
                    div_differences += f'Differences: {metric.diff} '
    return process_map, div_similarity, div_differences


@app.callback([Output('div-status-similarity', 'children'),
               Output('div-status-mining', 'children'),
               Output('window-slider', 'marks')],
              Input('check-similarity-finished', 'n_intervals'),
              [State('div-status-similarity', 'children'),
               State('div-status-mining', 'children'),
               State('final-window', 'children'),
               State('window-slider', 'marks')])
def update_metrics(n, div_similarity_status, div_status_mining, final_window, marks):
    ###################################################################
    # ATUALIZA INTERFACE EM RELAÇÃO A MINERAÇÃO DE PROCESSOS
    ###################################################################
    if control.get_mining_status() == ProcessingStatus.FINISHED:
        control.reset_mining_calculation()
        div_status_mining = f'Finished to mine the process models.'
    elif control.get_mining_status() == ProcessingStatus.STARTED:
        div_status_mining = f'Mining process models...'

    ###################################################################
    # ATUALIZA INTERFACE EM RELAÇÃO AO CÁLCULO DE MÉTRICAS
    ###################################################################

    # verifica se o cálculo de métricas terminou normalmente ou por timeout
    # e também verifica se a mineração de processos já atualizou o final-window
    # para evitar que as marcas do slider fiquem sem marcações (final-window = 0)
    if (control.get_metrics_status() == ProcessingStatus.FINISHED or control.get_metrics_status() == ProcessingStatus.TIMEOUT) \
            and final_window:
        if control.get_metrics_status() == ProcessingStatus.FINISHED:
            div_similarity_status = f'Similarity metrics calculated.'
        elif control.get_metrics_status() == ProcessingStatus.TIMEOUT:
            div_similarity_status = f'TIMEOUT in the similarity metrics calculation. Some metrics will not be presented...'
        windows = control.get_metrics_manager().get_window_candidates()
        for w in range(1, final_window + 1):
            if w in windows:
                marks[str(w)] = {'label': str(w), 'style': {'color': '#f50'}}
            else:
                marks[str(w)] = {'label': str(w)}
        control.reset_metrics_calculation()
    elif control.get_metrics_status() == ProcessingStatus.STARTED:
        div_similarity_status = 'Calculating similarity metrics...'
        marks = {str(w): str(w) for w in range(1, final_window + 1)}

    return div_similarity_status, div_status_mining, marks
