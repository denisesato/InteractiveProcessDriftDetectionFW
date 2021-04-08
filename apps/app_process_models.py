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
import dash_core_components as dcc
import dash_html_components as html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State

from app import app
from components.apply_window import WindowUnity, WindowType, WindowInitialIndex
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

        dcc.Input(id='input-window-size', type='number', value='0', min=0),
        html.Button(id='submit-button-state', n_clicks=0, children='Mine models'),
        html.Div(id='window-size', style={'display': 'none'}),

        dcc.RadioItems(id='initial-index-type',
                       options=[
                           {'label': 'Trace index', 'value': WindowInitialIndex.TRACE_INDEX},
                           {'label': 'Trace concept name', 'value': WindowInitialIndex.TRACE_CONCEPT_NAME},
                       ],
                       value=WindowInitialIndex.TRACE_INDEX,
                       labelStyle={'display': 'inline-block'}
                       ),

        html.Div(dcc.Link('Back to file management', href='/apps/app_manage_files')),

        html.Hr(),
        html.Div(id='div-status-mining', children=''),
        html.Div(id='div-status-similarity', children=''),

        html.Hr(),
        html.Div(id='div-similarity-metrics-value', children=''),
        html.Div(id='div-differences'),
        html.Hr(),

        dcc.Checklist(
            id='check-to-evaluation-options',
            options=[
                {'label': 'Evaluate results', 'value': 'on'},
            ],
        ),

        html.Div(id='element-to-hide', children=[
            dcc.Input(id='input-real-drifts', type='text', placeholder='Fill with real drifts'),
            html.Button(id='submit-evaluation', n_clicks=0, children='Evaluate'),
            html.Div(id='div-fscore'),

        ], style={'display': 'none'}),


    ], className="three columns"),

    html.Div([
        html.Div([
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
            n_intervals=0,
        )]),
])


@app.callback(
    Output(component_id='element-to-hide', component_property='style'),
    [Input(component_id='check-to-evaluation-options', component_property='value')])
def show_hide_element(visibility_state):
    if visibility_state is not None and len(visibility_state) > 0 and visibility_state[0] == 'on':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


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
def run_framework(n_clicks, input_window_size, window_type, window_unity, file):
    int_input_size = 0
    if input_window_size is not None:
        int_input_size = int(input_window_size)
    if file != '' and int_input_size > 0:
        window_count = framework.run(file, window_type, window_unity, int_input_size)
        print(f'Setting window-size value {input_window_size}')
        return input_window_size, window_count
    print(f'Setting window-size value 0')
    return 0, 0


@app.callback([Output('graph-with-slider', 'dot_source'),
               Output('div-similarity-metrics-value', 'children')],
              Input('window-slider', 'value'),
              State('hidden-filename', 'children'))
def update_figure(window_value, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = ''
    div_similarity = []
    if 'window-slider' in changed_id and window_value != 0:
        process_map = framework.get_model(file, window_value)
        if framework.get_metrics_status() == ProcessingStatus.IDLE:
            metrics = framework.get_metrics_manager().get_metrics_info(window_value)
            for metric in metrics:
                div_similarity.append(html.Div(f'{metric.metric_name}: {metric.value}'))
                if len(metric.diff_added) > 0:
                    div_similarity.append(html.Div(f'{metric.metric_name}: Added: {metric.diff_added}'))
                if len(metric.diff_removed) > 0:
                    div_similarity.append(html.Div(f'{metric.metric_name}: Removed: {metric.diff_removed}'))
    return process_map, html.Div(div_similarity)


@app.callback([Output('div-status-similarity', 'children'),
               Output('div-status-mining', 'children'),
               Output('window-slider', 'marks')],
              Input('check-similarity-finished', 'n_intervals'),
              State('window-slider', 'marks'),
              State('initial-index-type', 'value'))
def update_metrics(n, marks, initial_index_type):
    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT MINING THE MODELS
    ###################################################################
    div_status_mining = framework.check_status_mining()

    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT THE METRIC'S CALCULATION
    ###################################################################
    div_similarity_status, windows, windows_with_drifts = framework.check_status_similarity_metrics()
    for w in range(1, framework.get_windows() + 1):
        initial_indexes = []
        if initial_index_type == WindowInitialIndex.TRACE_INDEX:
            initial_indexes = framework.get_initial_trace_indexes()
        elif initial_index_type == WindowInitialIndex.TRACE_CONCEPT_NAME:
            initial_indexes = framework.get_initial_trace_concept_names()
        else:
            print(f'Incorrect initial index type [{initial_index_type}]')
        label = str(w) + '|' + str(initial_indexes[(w - 1)])
        if windows_with_drifts and w in windows_with_drifts:
            marks[str(w)] = {'label': label, 'style': {'color': '#f50'}}
        else:
            marks[str(w)] = {'label': label}

    return div_similarity_status, div_status_mining, marks


@app.callback(Output('div-fscore', 'children'),
              [Input('submit-evaluation', 'n_clicks')],
              [State('input-real-drifts', 'value'),
              State('window-size', 'children')])
def evaluate(n_clicks, real_drifts, win_size):
    if n_clicks and real_drifts and real_drifts != '':
        f_score = ""
        if framework.get_status_framework() == ProcessingStatus.NOT_STARTED:
            return f'It is not possible to evaluate yet because framework was not started.'
        if framework.get_status_framework() == ProcessingStatus.RUNNING:
            return f'It is not possible to evaluate yet because framework is still running.'
        if framework.get_status_framework() != ProcessingStatus.NOT_STARTED and \
                framework.get_status_framework() == ProcessingStatus.IDLE and real_drifts:
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
            f_score = framework.evaluate(window_candidates, list_real_drifts, win_size)
            print(f'IPDD f-score: {f_score}')
        return f'F-score: {f_score}'
    return ''