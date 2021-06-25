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
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State

from app import app
from components.apply_window import WindowUnity, WindowType, WindowInitialIndex
from components.ippd_fw import IPDDProcessingStatus
from components.ippd_fw import InteractiveProcessDriftDetectionFW

framework = InteractiveProcessDriftDetectionFW()

# main layout of the page
layout = [
    dbc.Row([
        dbc.Col([
            html.H3('Analyzing Process Drifts', className='text-primary mt-2'),
            html.H6('Insert the parameters and click on Analyze Process Drifts to start. '
                    'Then, you can visualize the process models over time by clicking on the window and evaluate the '
                    'results calculating the F-score.')
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Container([
                dbc.Row([
                    dbc.Col([html.H5('Parameter configuration')]),
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Span('Read the log as'),
                        dcc.Dropdown(id='window-type',
                                     options=[{'label': item.value, 'value': item.name}
                                              for item in WindowType],
                                     )
                    ], width=12),
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Span('Split sub-logs based on'),
                        dcc.Dropdown(id='window-unity',
                                     options=[],
                                     disabled=True
                                     ),
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Span('Window size'),
                        dbc.Input(id='input-window-size', type='number', min=1,
                                  placeholder='Size', disabled=True),
                        html.Div(id='window-size', children='', style={'display': 'none'}),
                        html.Span('Similarity metrics', style={'display': 'none'}),
                        dcc.Checklist(id='metrics',
                                      options=[{'label': item.value, 'value': item.value}
                                               for item in framework.get_implemented_metrics()],
                                      value=[item.value for item in framework.get_default_metrics()],
                                      labelStyle=dict(display='block'),
                                      style={'display': 'none'}
                                      ),
                        dbc.Button(children=['Analyze Process Drifts'],
                                   id='mine_models_btn', n_clicks=0, disabled=True,
                                   className='btn btn-primary btn-block mt-2')
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Hr(),
                        html.H5('Status'),
                        html.Div(id='div-status-mining', children='Not started'),
                        html.Div(id='div-status-similarity', children=''),
                        html.Hr(),
                    ], width=12)
                ]),

            ], style={'backgroundColor': 'rgba(211,211,211,0.5)'}),

            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.Div(id='evaluation-div', children=[
                            html.H5('Evaluate results'),
                            html.Span('Real drifts: '),
                            dbc.Input(id='input-real-drifts', type='text',
                                      placeholder='Fill with real drifts separated by space', ),
                            dbc.Button(id='submit-evaluation',
                                       n_clicks=0, children='Evaluate',
                                       className='btn btn-primary btn-block mt-2'),
                            html.P(id='div-fscore', className='mt-2'),
                            html.Span('    ')
                        ], style={'display': 'none'})
                    ])
                ])
            ], style={'backgroundColor': 'rgba(211,211,211,0.5)'}, className='mt-2')
        ], width=3, style={'height': '80vh'}),

        dbc.Col([
            # dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H5('Similarity Information'),
                ])
            ], style={'backgroundColor': 'rgba(232, 236, 241, 1)'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id='div-similarity-metrics-value', children=''),
                    html.Div(id='div-differences', children=''),
                    html.Hr()
                ])
            ], style={'backgroundColor': 'rgba(232, 236, 241, 1)'}),
            # ]),

            dbc.Row([
                dbc.Col([
                    dcc.RadioItems(id='initial-index-type',
                                   options=[{'label': item.value, 'value': item.name}
                                            for item in WindowInitialIndex],
                                   value=WindowInitialIndex.TRACE_INDEX.name,
                                   )
                ], width={"size": 6, "offset": 3})
            ], style={'display': 'none'}),

            dbc.Row([
                dbc.Col([
                    dcc.Slider(
                        id='window-slider',
                        step=None,
                        included=False,
                        min=0,
                        max=0,
                        value=0,
                        marks={})
                ])
            ], className='mt-2'),

            dbc.Row(dash_interactive_graphviz.DashInteractiveGraphviz(id="graph-with-slider", dot_source='')),

            dbc.Row([
                dbc.Col([
                    html.Div(id='current-final-window', style={'display': 'none'}),
                    html.Div(id='status-ipdd', style={'display': 'none'}),
                    html.Div(id='diff', style={'display': 'none'}),

                    dcc.Interval(
                        id='check-similarity-finished',
                        interval=1 * 1000,  # in milliseconds
                        n_intervals=0,
                        disabled=True)
                ])
            ]),

        ], id='models-col', width=9, style={'height': '100vh', 'display': 'none'})
    ], className='mt-2')
]


@app.callback([Output('window-unity', 'disabled'),
               Output('input-window-size', 'disabled'),
               Output('mine_models_btn', 'disabled'),
               Output('window-unity', 'options')],
              [Input('window-type', 'value'),
               Input('window-unity', 'value'),
               Input('input-window-size', 'value')]
              )
def type_selected(type_value, unity_value, winsize):
    if type_value:
        options = []
        for item in WindowUnity:
            if item == WindowUnity.UNITY:
                if type_value == WindowType.TRACE.name:
                    options.append({'label': 'Traces', 'value': item.name})
                elif type_value == WindowType.EVENT.name:
                    options.append({'label': 'Events', 'value': item.name})
            else:
                options.append({'label': item.value, 'value': item.name})
    else:
        options = [{'label': item.value, 'value': item.name}
                   for item in WindowUnity]

    if not type_value:
        return True, True, True, options
    elif not unity_value:
        print(f'User selected window-type: {type_value}')
        return False, True, True, options
    elif not winsize or winsize <= 0:
        print(f'User selected window-unity: {unity_value}')
        return False, False, True, options
    else:
        return False, False, False, options


@app.callback(Output('check-similarity-finished', 'disabled'),
              [Input('status-ipdd', 'children'),
               Input('window-size', 'children'),])
# used to start or stop the interval component for checking similarity calculation
def check_status_ipdd(status, window_size):
    print(f'check_status_ipdd window-size {window_size}')
    # to avoid first call
    ctx = dash.callback_context
    # when the callback is started not by interval
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'window-size.children':
        status = framework.get_status_framework()

    if status == IPDDProcessingStatus.RUNNING:
        return False
    elif status == IPDDProcessingStatus.NOT_STARTED or status == IPDDProcessingStatus.IDLE:
        return True


@app.callback([Output('models-col', 'style'),
               Output('window-slider', 'min'),
               Output('window-slider', 'max'),
               Output('window-slider', 'value')],
              Input('current-final-window', 'children'),
              State('window-slider', 'min'),
              State('window-slider', 'max'),
              State('models-col', 'style'),
              State('window-size', 'children'), )
# this callback is triggered when mining have finished
def update_slider(current_final_window, min, max, models_col_style, window_size):
    print(f'update_slider: current_final_window {current_final_window} - window_size {window_size}')
    if current_final_window and current_final_window > 0 and window_size and window_size != 0:
        app.logger.info(f'Atualiza window-slider min: 1, max: {current_final_window - 1}, value: 0')
        return {'height': '100vh', 'display': 'block'}, min, current_final_window - 1, 0
    else:
        return {'height': '100vh', 'display': 'none'}, min, max, -1


@app.callback(Output('window-size', 'children'),
              [Input('mine_models_btn', 'n_clicks')],
              [State('input-window-size', 'value'),
               State('window-type', 'value'),
               State('window-unity', 'value'),
               State('hidden-filename', 'children'),
               State('metrics', 'value')])
def run_framework(n_clicks, input_window_size, window_type, window_unity, file, metrics):
    if n_clicks > 0:
        int_input_size = 0
        if input_window_size is not None:
            int_input_size = int(input_window_size)
        if file != '' and int_input_size > 0:
            print(f'Running IPDD')
            framework.run(file, window_type, window_unity, int_input_size, metrics)
        print(f'Setting window-size value {input_window_size}')
        return input_window_size
    else:
        print(f'Setting window-size value with initial value 0')
        return 0


@app.callback([Output('graph-with-slider', 'dot_source'),
               Output('div-similarity-metrics-value', 'children')],
              Input('window-slider', 'value'),
              State('hidden-filename', 'children'))
def update_figure(window_value, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = ''
    div_similarity = []
    if 'window-slider' in changed_id and window_value >= 0:
        window_value += 1  # because slider starts on 0 but windows on 1
        process_map = framework.get_model(file, window_value)
        if framework.get_metrics_status() == IPDDProcessingStatus.IDLE:
            metrics = framework.get_metrics_manager().get_metrics_info(window_value)
            for metric in metrics:
                div_similarity.append(html.Span(f'{metric.metric_name}: '))
                div_similarity.append(html.Span("{:.2f}".format(metric.value), className='font-weight-bold'))

                for additional_info in metric.get_additional_info():
                    strType, strList = additional_info.get_status_info()
                    div_similarity.append(html.Div([
                        html.Span(f'{strType}', className='font-italic'),
                        html.Span(f'{strList}', className='font-weight-bold')
                    ]))
    return process_map, html.Div(div_similarity)


@app.callback([Output('div-status-similarity', 'children'),
               Output('div-status-mining', 'children'),
               Output('window-slider', 'marks'),
               Output('evaluation-div', 'style'),
               Output('current-final-window', 'children'),
               Output('status-ipdd', 'children'),
               Output('mine_models_btn', 'children')],
              Input('check-similarity-finished', 'n_intervals'),
              State('window-slider', 'marks'),
              State('initial-index-type', 'value'),
              State('current-final-window', 'children'))
def update_status_and_drifts(n, marks, initial_index_type, current_final_window):
    print(f'update_status_and_drifts - current_final_window {current_final_window}')
    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT MINING THE MODELS
    ###################################################################
    div_status_mining = framework.get_status_mining_text()

    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT THE METRIC'S CALCULATION
    ###################################################################
    div_similarity_status, windows, windows_with_drifts = framework.get_status_similarity_metrics_text()
    marks = {}
    for w in range(0, framework.get_windows()):
        # The change of the trace initial information stops working after
        # stopping interval component when IPDD finishs running
        # TODO remove or fix the code below
        initial_indexes = []
        if initial_index_type == WindowInitialIndex.TRACE_INDEX.name:
            initial_indexes = framework.get_initial_trace_indexes()
        elif initial_index_type == WindowInitialIndex.TRACE_CONCEPT_NAME.name:
            initial_indexes = framework.get_initial_trace_concept_names()
        else:
            print(f'Incorrect initial index type [{initial_index_type}]')
        label = str(w + 1) + '|' + str(initial_indexes[(w)])
        if windows_with_drifts and (w + 1) in windows_with_drifts:
            marks[w] = {'label': label, 'style': {'color': '#f50'}}
        else:
            marks[w] = {'label': label}

    ipdd_status = framework.get_status_framework()
    total_of_windows = framework.total_of_windows

    # display or not the evaluation container
    display_evaluation = {'display': 'none'}
    if ipdd_status == IPDDProcessingStatus.FINISHED or ipdd_status == IPDDProcessingStatus.IDLE:
        display_evaluation = {'display': 'block'}

    # display or not the spinner (loading behavior of button)
    children_button = ["Analyze Process Drifts"]
    if ipdd_status == IPDDProcessingStatus.RUNNING:
        children_button = [dbc.Spinner(size="sm"), " Analyzing Process Drifts..."]

    print(f'update_status_and_drifts - returning as current_final_window {total_of_windows}')
    return div_similarity_status, div_status_mining, marks, display_evaluation, total_of_windows, \
           ipdd_status, children_button


@app.callback(Output('div-fscore', 'children'),
              [Input('submit-evaluation', 'n_clicks')],
              [State('input-real-drifts', 'value'),
               State('window-size', 'children')])
def evaluate(n_clicks, real_drifts, window_size):
    if n_clicks and real_drifts and real_drifts != '':
        f_score = ""
        if framework.get_status_framework() == IPDDProcessingStatus.NOT_STARTED:
            return f'It is not possible to evaluate yet because framework was not started.'
        if framework.get_status_framework() == IPDDProcessingStatus.RUNNING:
            return f'It is not possible to evaluate yet because framework is still running.'
        if framework.get_status_framework() != IPDDProcessingStatus.NOT_STARTED and \
                framework.get_status_framework() == IPDDProcessingStatus.IDLE and real_drifts:
            drifts = real_drifts.split(" ")
            list_real_drifts = []
            for item in drifts:
                if item != '':
                    try:
                        item_int = int(item)
                    except ValueError:
                        print(f'Input values must be integer - ignoring [{item}]')
                    list_real_drifts.append(item_int)
            print(f'Real drifts {list_real_drifts}')
            window_candidates = framework.get_windows_candidates()
            f_score = framework.evaluate(window_candidates, list_real_drifts, window_size)
            print(f'IPDD f-score: {f_score}')
        return f'F-score: {f_score}'
    return ''
