import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State
from json_tricks import dumps, loads

from app import app
from components.apply_window import WindowUnity, WindowType, AnalyzeDrift, ModelAnalyzes
from components.compare.compare_dfg import RecoverMetrics


class MetricsStatus:
    NOT_STARTED = 'NOT_STARTED'
    IDLE = 'IDLE'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'


class ControlMetrics:
    def __init__(self):
        self.metrics_status = MetricsStatus.NOT_STARTED
        self.metrics_manager = None

    def finish_metrics_calculation(self):
        self.metrics_status = MetricsStatus.FINISHED

    def start_metrics_calculation(self):
        self.metrics_status = MetricsStatus.STARTED

    def reset_metrics_calculation(self):
        self.metrics_status = MetricsStatus.IDLE

    def get_metrics_status(self):
        return self.metrics_status

    def set_metrics_manager(self, metrics_manager):
        self.metrics_manager = metrics_manager

    def get_metrics_manager(self):
        return self.metrics_manager


control = ControlMetrics()


layout = html.Div([
    html.Div([
        html.H3(children='Selecione como realizar o janelamento'),

        dcc.Link('Voltar ao gerenciamento de arquivos', href='/apps/app_manage_files'),

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
        html.Div(id='window-size', style={'display': 'none'}),

        html.Div(id='div-status-models'),
        html.Div(id='div-status-similarity'),
        html.Div(id='div-similarity-metrics'),
    ]),

    html.Div([html.Div([
                dcc.Slider(
                    id='window-slider',
                    min=0,
                    step=None,
                    included=False
                ),
            ]),

            html.Div([
                dash_interactive_graphviz.DashInteractiveGraphviz(
                    id="graph-with-slider", dot_source=''),
            ]),
    ]),


    html.Div(id='final-window', style={'display': 'none'}),
    html.Div(id='diff'),

    dcc.Interval(
                id='check-similarity-finished',
                interval=1*1000, # in milliseconds
                n_intervals=0
            )
])


@app.callback([Output('window-slider', 'min'),
               Output('window-slider', 'max'),
               Output('window-slider', 'value')],
              [Input('final-window', 'children')])
def update_slider(final_window):
    if not final_window:
        app.logger.error('Final-window ainda não definida')
        return 0, 0, 0

    app.logger.info(f'Atualiza slider {final_window}')
    return 1, final_window, 1


@app.callback([Output('window-size', 'children'),
               Output('final-window', 'children')],
              [Input('submit-button-state', 'n_clicks')],
              [State('input-window-size', 'value'),
               State('window-type', 'value'),
               State('window-unity', 'value'),
               State('hidden-filename', 'children')])
def update_output(n_clicks, input_window_size, window_type, window_unity, file):
    if file and input_window_size != '0':
        print(f'Usuário selecionou janela {window_type}-{window_unity} de tamanho {input_window_size} - arquivo {file}')
        control.start_metrics_calculation()
        models = AnalyzeDrift(window_type, window_unity, int(input_window_size), file, control)
        window_count = models.generate_models()

        return input_window_size, window_count
    return 0, 0


@app.callback([Output('graph-with-slider', 'dot_source'),
               Output('div-status-models', 'children'),
               Output('div-similarity-metrics', 'children')],
              [Input('window-slider', 'value'),
               Input('final-window', 'children')],
               [State('hidden-filename', 'children')])
def update_figure(window_value, window_size, file):
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
    if 'final-window' in changed_id:
        div_status = 'Escolha uma opção de janelamento para gerar os modelos de processo'
    elif 'window-slider' in changed_id and window_value != 0:
        process_map = ModelAnalyzes.get_model(file, window_value)
        div_status = f'Modelos de processo gerados para a opção escolhida.'
        if control.get_metrics_status() == MetricsStatus.IDLE:
            metrics = control.get_metrics_manager().get_metrics_info(window_value)
            for metric in metrics:
                div_similarity += f'** Métrica [{metric.name}]: {metric.value} '
                if len(metric.diff) > 0:
                    div_similarity += f'- Diferenças: {metric.diff} '
    return process_map, div_status, div_similarity


@app.callback([Output('div-status-similarity', 'children'),
               Output('window-slider', 'marks')],
              Input('check-similarity-finished', 'n_intervals'),
              [State('div-status-similarity', 'children'),
               State('hidden-filename', 'children'),
               State('final-window', 'children'),
               State('window-slider', 'marks')])
def update_metrics(n, value, file, final_window, mark):
    if control.get_metrics_status() == MetricsStatus.FINISHED:
        div = f'Cálculo de métricas finalizado.'
        windows = control.get_metrics_manager().get_window_candidates()
        for w in range(1, final_window + 1):
            if w in windows:
                mark[str(w)] = {'label': str(w), 'style': {'color': '#f50'}}
            else:
                mark[str(w)] = {'label': str(w)}
        control.reset_metrics_calculation()
    elif control.get_metrics_status() == MetricsStatus.STARTED:
        div = 'Cálculo de métricas em andamento...'
        mark = {str(w): str(w) for w in range(1, final_window + 1)}
    else:
        div = value

    if mark is None:
        mark = {0: {'label': '0'}}

    return div, mark
