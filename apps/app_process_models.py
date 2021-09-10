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
from app import app, get_user_id
from app import framework
from components.apply_window import WindowUnity, WindowType, WindowInitialIndex
from components.ippd_fw import IPDDProcessingStatus

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Manage Files", href="/apps/app_manage_files")),
        dbc.NavItem(dbc.NavLink("About IPDD", href="/")),
    ],
    brand="IPDD Framework - Analyzing Process Drifts",
    color="primary",
    dark=True,
)

evaluation_card = html.Div([
    dbc.Collapse([
        dbc.CardHeader(['Calculate F-score metric']),
        # html.Hr(),
        # html.H6(['Calculate F-score metric']),
        # html.Hr(),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Span('Real drifts: '), width=2),
                dbc.Col(dbc.Input(id='input-real-drifts', type='text',
                                  placeholder='Fill with real drifts separated by space'), width=4),
                dbc.Col(dbc.Button(id='submit-evaluation',
                                   n_clicks=0, children='Evaluate',
                                   className='btn btn-primary', block=True), width=2)
            ]),
            dbc.Row([
                dbc.Col(html.H4(id='div-fscore', className='mt-2')),
            ])
        ])
    ], id='collapse-evaluation', is_open=False)
], id='evaluation-card', className='mt-1', style={'display': 'none'})

status_panel = [
    html.Div([html.H5('Status: ', style={'display': 'inline'})], id='div-status',
             style={'display': 'inline'}),
    html.Div(id='div-status-mining', children='Not started',
             style={'display': 'inline'}),
    html.Div(id='div-status-similarity', children='', style={'display': 'inline'})
]

parameters_panel = [
    dbc.CardHeader([
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Show/Hide Parameters",
                        # color="link",
                        id="button-parameters",
                    ), width=8
                ),

                dbc.Col([
                    dbc.Button("Evaluate results", id="button-evaluation", color="link", block=True,
                               style={'display': 'none'}),
                ], width=2),

                dbc.Col([
                    dbc.Button("How to analyze", id="popover-bottom-target", color="link", block=True),
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Analyzing Process Drifts using IPDD Framework"),
                            dbc.PopoverBody(
                                'Insert the parameters and click on Analyze Process Drifts to start. '
                                'IPDD will show the process models over time and you can navigate between the '
                                'models by clicking on the window. IPDD shows the similarity metrics calculated '
                                'between the current model and the previous one. '
                                'You can also evaluate the detected drifts using the F-score metric, which is '
                                'calculate using the the actual drifts informed by the user. '),
                        ],
                        id="popover",
                        target="popover-bottom-target",  # needs to be the same as dbc.Button id
                        placement="bottom",
                        is_open=False,
                    )], width=2)
            ]),
    ], className='mt-1'),

    dbc.Collapse(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Span('Read the log as'),
                    dcc.Dropdown(id='window-type',
                                 options=[{'label': item.value, 'value': item.name}
                                          for item in WindowType],
                                 ),
                ]),
                dbc.Col([
                    html.Span('Split sub-logs based on'),
                    dcc.Dropdown(id='window-unity',
                                 options=[],
                                 disabled=True,
                                 ),
                ]),
                dbc.Col([
                    html.Span('Window size'),
                    dbc.Input(id='input-window-size', type='number', min=1,
                              placeholder='Size', disabled=True),
                    html.Div(id='window-size', style={'display': 'none'}),
                ]),
                dbc.Col([
                    dbc.Button(children=['Analyze Process Drifts'],
                               id='mine_models_btn', n_clicks=0, disabled=True,
                               className='btn btn-primary', block=True, style={"margin-top": "1.4rem"})
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    html.Span('Similarity metrics'),
                    dcc.Checklist(id='metrics',
                                  options=[{'label': item.value, 'value': item.value}
                                           for item in framework.get_implemented_metrics()],
                                  value=[item.value for item in framework.get_default_metrics()],
                                  ),
                ]),
            ], style={'display': 'none'})
        ]),
        id='collapse-parameters', is_open=True
    )
]

models_card = [
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H6('Similarity Information', className='card-title'),
                    html.Div(id='div-similarity-metrics-value', children=''),
                    html.Div(id='div-differences', children=''),
                ]),
                style={'backgroundColor': 'rgba(232, 236, 241, 1)'}, className='mt-1'
            )
        ], width=3),

        dbc.Col([
            dcc.Slider(
                id='window-slider',
                step=None,
                included=False,
                min=0,
                max=0,
                value=0,
                marks={}),

            dash_interactive_graphviz.DashInteractiveGraphviz(id="current-model", dot_source=''),
        ], width=9, style={'height': '75vh'})
    ], className='mt-1'),

    dbc.Row([
        dbc.Col([
            html.Div(id='status-ipdd', style={'display': 'none'}),
            html.Div(id='diff', style={'display': 'none'}),

            dcc.Interval(
                id='check-ipdd-finished',
                interval=1 * 1000,  # in milliseconds
                n_intervals=0,
                disabled=True)
        ])
    ]),
]


def get_layout():
    # main layout of the page
    layout = [
        dbc.Row([
            dbc.Col(navbar)
        ]),

        dbc.Row(
            dbc.Col(parameters_panel, width=12)
        ),

        dbc.Row(
            dbc.Col(evaluation_card, width=12)
        ),

        dbc.Row(
            dbc.Col(status_panel, className='mt-2')
        ),

        dbc.Row(
            dbc.Col(models_card, id='models-col', width=12, style={'display': 'none'})
        )
    ]
    return layout


@app.callback(
    Output("collapse-evaluation", "is_open"),
    [Input("button-evaluation", "n_clicks")],
    [State("collapse-evaluation", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("collapse-parameters", "is_open"),
    [Input("button-parameters", "n_clicks")],
    [State("collapse-parameters", "is_open"),
     State('status-ipdd', 'children')],
)
def toggle_collapse(n, is_open, status_ipdd):
    if n:
        if not is_open and status_ipdd == IPDDProcessingStatus.RUNNING:
            return is_open
        else:
            return not is_open
    return is_open


@app.callback(
    Output("popover", "is_open"),
    [Input("popover-bottom-target", "n_clicks")],
    [State("popover", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


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


@app.callback([Output('check-ipdd-finished', 'disabled'),
               Output('button-parameters', 'n_clicks'),
               Output('models-col', 'style'),
               Output('window-slider', 'value')],
              [Input('status-ipdd', 'children'),
               Input('window-size', 'children')],
              [State('check-ipdd-finished', 'disabled'),
               State('button-parameters', 'n_clicks'),
               State('models-col', 'style')])
# used to start or stop the interval component for checking similarity calculation
def check_status_ipdd(status, window_size, interval_disabled, button_clicks, models_col_style):
    ctx = dash.callback_context
    print(f'check_status_ipdd {ctx.triggered} {status} {window_size}')

    # when the user starts a new process drift analysis
    if ctx.triggered[0]['prop_id'] == 'window-size.children' and window_size > 0:
        if status == IPDDProcessingStatus.NOT_STARTED or status == IPDDProcessingStatus.IDLE:
            # starts the interval and hide the parameters panel
            return False, 1, {'display': 'none'}, -1
        else:
            # IPDD is still running
            return interval_disabled, button_clicks, models_col_style, -1
    # interval check
    elif window_size > 0:
        if status == IPDDProcessingStatus.RUNNING:
            return interval_disabled, button_clicks, models_col_style, -1
        if status == IPDDProcessingStatus.IDLE:
            return True, 0, {'display': 'block'}, 0
    # user selected a new event log
    else:
        if status == IPDDProcessingStatus.IDLE:
            framework.restart_status()
            return False, 0, {'display': 'none'}, -1
        return True, 0, {'display': 'none'}, -1


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
            user = get_user_id()
            framework.run(file, window_type, window_unity, int_input_size, metrics, user)
        print(f'Setting window-size value {input_window_size}, indicating IPDD starts the analysis')
        return input_window_size
    else:
        print(f'Setting window-size value with initial value 0, indicating IPDD is IDLE')
        return 0


@app.callback([Output('current-model', 'dot_source'),
               Output('div-similarity-metrics-value', 'children')],
              Input('window-slider', 'value'),
              State('hidden-filename', 'children'))
def update_figure(window_value, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = ''
    div_similarity = []
    if 'window-slider' in changed_id and window_value >= 0:
        window_value += 1  # because slider starts on 0 but windows on 1
        process_map = framework.get_model(file, window_value, get_user_id())
        if window_value > 1:
            previous_process_map = framework.get_model(file, window_value - 1, get_user_id())
        if framework.total_of_windows > 1:  # if there is only one window the metrics manager is not initialized
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
               Output('evaluation-card', 'style'),
               Output('button-evaluation', 'style'),
               Output('status-ipdd', 'children'),
               Output('div-status', 'children'),
               Output('window-slider', 'max')],
              Input('check-ipdd-finished', 'n_intervals'),
              State('div-status', 'children'))
def update_status_and_drifts(n, div_status):
    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT MINING THE MODELS
    ###################################################################
    div_status_mining = framework.get_status_mining_text() + "  "
    ipdd_status = framework.get_status_framework()

    # display or not the spinner (loading behavior)
    if ipdd_status == IPDDProcessingStatus.RUNNING:
        if len(div_status) == 1:
            div_status = [dbc.Spinner(size="sm"), " "] + div_status
    elif ipdd_status == IPDDProcessingStatus.FINISHED or ipdd_status == IPDDProcessingStatus.IDLE:
        div_status = [html.H5('Status: ', style={'display': 'inline'})]

    ###################################################################
    # UPDATE THE USER INTERFACE ABOUT THE METRIC'S CALCULATION
    ###################################################################
    div_similarity_status, windows, windows_with_drifts = framework.get_status_similarity_metrics_text()
    marks = {}
    for w in range(0, framework.get_windows()):
        initial_indexes = framework.get_initial_trace_indexes()
        label = str(w + 1) + '|' + str(initial_indexes[w] + 1)
        if windows_with_drifts and (w + 1) in windows_with_drifts:
            marks[w] = {'label': label, 'style': {'color': '#f50'}}
        else:
            marks[w] = {'label': label}

    # display or not
    display_evaluation = {'display': 'none'}
    max_slider = 0
    if ipdd_status == IPDDProcessingStatus.FINISHED or ipdd_status == IPDDProcessingStatus.IDLE:
        display_evaluation = {'display': 'block'}
        # get the number of windows generated
        total_of_windows = framework.total_of_windows
        max_slider = total_of_windows - 1

    return div_similarity_status, div_status_mining, marks, display_evaluation, display_evaluation, ipdd_status, \
           div_status, max_slider


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
            print(f'IPDD f-score: {"{:.2f}".format(f_score)}')
        return f'F-score: {"{:.2f}".format(f_score)}'
    return ''
