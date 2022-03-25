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
import base64
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import dash_interactive_graphviz
from dash.dependencies import Input, Output, State
from app import app, get_user_id, framework, dash
from components.adaptive.attributes import Activity
from components.parameters import WindowUnityFixed, ReadLogAs, AttributeAdaptive, Approach
from components.ippd_fw import IPDDProcessingStatus, IPDDParametersFixed, IPDDParametersAdaptive

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
        dbc.CardHeader(['Evaluation metrics']),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Span('Real drifts: '), width=2),
                dbc.Col(dbc.Input(id='input-real-drifts', type='text',
                                  placeholder='Fill with real drifts separated by space'), width=4),
                dbc.Col(dbc.Button(id='submit-evaluation',
                                   n_clicks=0, children='Evaluate',
                                   className='btn btn-secondary'), width=2)
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

modal_extended_adaptive_options = [
    dbc.Button("+", id="extended_adaptive_options", n_clicks=0, outline=True),
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("ADWIN parameters")),
            dbc.ModalBody(
                dbc.FormFloating(
                    [
                        dbc.Input(id='input-delta', type='number', value=0.002),
                        dbc.Label('Delta'),
                    ]
                )),
            dbc.ModalFooter(
                dbc.Button(
                    "Close", id="close", className="ms-auto", n_clicks=0
                )
            ),
        ],
        id="modal",
        size="sm",
        is_open=False,
    ),
]

parameters_panel = [
    dbc.CardHeader([
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Show/Hide Parameters",
                        id="button-parameters",
                        className='btn btn-secondary'
                    ), width=8
                ),

                dbc.Col([
                    dbc.Button("Evaluate results", id="button-evaluation", className="btn btn-light",
                               style={'display': 'none'}),
                ], width=2),

                dbc.Col([
                    dbc.Button("How to analyze", id="popover-bottom-target", className="btn btn-light"),
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
                    dbc.Label('Approach', width='auto'),
                    dcc.Dropdown(id='approach',
                                 options=[{'label': item.value, 'value': item.name}
                                          for item in Approach],
                                 ),
                ]),
                dbc.Col([
                    dbc.Label('Read the log as', width='auto'),
                    dcc.Dropdown(id='window-type',
                                 options=[{'label': item.value, 'value': item.name}
                                          for item in ReadLogAs],
                                 disabled=True),
                ]),
                dbc.Col([
                    dbc.Label('Attribute', width='auto'),
                    dcc.Dropdown(id='attribute',
                                 options=[{'label': item.value, 'value': item.name}
                                          for item in AttributeAdaptive],
                                 disabled=True),
                ], id='col-attribute', style={'display': 'None'}),
                dbc.Col([
                    dbc.Label('Split sub-logs based on', width='auto'),
                    dcc.Dropdown(id='window-unity',
                                 options=[],
                                 disabled=True,
                                 ),
                ], id='col-window-unity', style={'display': 'none'}),
                dbc.Col([
                    dbc.Label('Window size', width='auto'),
                    dbc.Input(id='input-window-size', type='number', min=1,
                              placeholder='Size', disabled=True, value=30),
                    html.Div(id='window-size', style={'display': 'none'}),
                ], id='col-window-size', style={'display': 'none'}),
                dbc.Col(
                    modal_extended_adaptive_options,
                    id='col-extended_adaptive_options', align="end", width='auto', style={'display': 'none'}),
                dbc.Col([
                    dbc.Button(children=['Analyze Process Drifts'],
                               id='mine_models_btn', n_clicks=0, disabled=True,
                               className='btn btn-secondary')
                ], align="end", width='auto')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label('Similarity metrics for control-flow', width='auto'),
                    dbc.Checklist(id='metrics',
                                  options=[{'label': item.value, 'value': item.value}
                                           for item in framework.get_implemented_metrics()],
                                  value=[item.value for item in framework.get_default_metrics()],
                                  inline=True),
                ]),
            ], style={'display': 'block'})
        ]),
        id='collapse-parameters', is_open=True
    )
]

models_card = [
    dbc.Row([
        dbc.Col([
            dbc.CardImg(id='activity_plot', top=True),
            dbc.Card(
                dbc.CardBody([
                    html.Div([
                        html.H6('Activity', id='activity_title', className='card-title'),
                        dcc.Dropdown(id='activity', value='', clearable=False),
                        html.Hr(id='activity_hr'),
                    ], id='activity_div'),
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
    Output("modal", "is_open"),
    [Input("extended_adaptive_options", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
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


@app.callback([Output('col-window-unity', 'style'),
               Output('col-window-size', 'style'),  # next attribute for fixed approach
               Output('col-attribute', 'style'),  # next attribute for adaptive approach
               Output('col-extended_adaptive_options', 'style'), # extended attributes for adaptive approach
               Output('window-type', 'disabled'),
               Output('window-type', 'value')],  # read the log as
              Input('approach', 'value'),
              State('window-type', 'value'))
def approach_selected(approach_value, read_log_as_value):
    show = {'display': 'block'}
    hide = {'display': 'none'}
    # print(f'Chamou {approach_value} {window_unity_style} {window_size_style}')
    if approach_value:
        if approach_value == Approach.FIXED.name:
            return show, show, hide, hide, False, read_log_as_value
        elif approach_value == Approach.ADAPTIVE.name:
            return hide, hide, show, show, False, read_log_as_value
        elif approach_value == '':
            return hide, hide, hide, hide, True, ''
        else:
            print(f'Invalid approach type in app_process_models.approach_selected: {approach_value}')
            return hide, hide, hide, hide, True, read_log_as_value
    else:  # first call
        return hide, hide, hide, hide, True, read_log_as_value


@app.callback([Output('window-unity', 'disabled'),
               Output('input-window-size', 'disabled'),
               Output('window-unity', 'options'),
               Output('attribute', 'disabled'),
               Output('mine_models_btn', 'disabled')],
              [Input('window-type', 'value'),
               Input('window-unity', 'value'),
               Input('input-window-size', 'value'),
               Input('attribute', 'value')],
              State('approach', 'value')
              )
def type_and_options_selected(read_log_as, unity_value, winsize, attribute, approach):
    enable_mine_button = False
    enable_window_unity = False
    enable_window_size = False
    enable_attribute = False
    options = []

    # check if the mine button should be enabled
    if read_log_as:
        if approach and approach == Approach.ADAPTIVE.name:
            # check if the attribute should be enabled
            if read_log_as:
                enable_attribute = True

                # check if the user fill attribute to enable mine button
                if attribute:
                    enable_mine_button = True
        elif approach and approach == Approach.FIXED.name:
            # if the user have selected FIXED window and type, fill the options for window unity
            if approach and approach == Approach.FIXED.name and read_log_as:
                for item in WindowUnityFixed:
                    if item == WindowUnityFixed.UNITY:
                        if read_log_as == ReadLogAs.TRACE.name:
                            options.append({'label': 'Traces', 'value': item.name})
                        elif read_log_as == ReadLogAs.EVENT.name:
                            options.append({'label': 'Events', 'value': item.name})
                    else:
                        options.append({'label': item.value, 'value': item.name})
                enable_window_unity = True
            # check if the window size input should be enabled
            if unity_value:
                enable_window_size = True

                # check if the user fill the window size to enable mine button
                if winsize and winsize > 0:
                    enable_mine_button = True
    return not enable_window_unity, not enable_window_size, options, not enable_attribute, not enable_mine_button,


@app.callback([Output('check-ipdd-finished', 'disabled'),
               Output('button-parameters', 'n_clicks'),
               Output('models-col', 'style')],
              [Input('status-ipdd', 'children'),
               Input('window-size', 'children')],
              [State('check-ipdd-finished', 'disabled'),
               State('button-parameters', 'n_clicks'),
               State('models-col', 'style')])
# used to start or stop the interval component for checking similarity calculation
def check_status_ipdd(status, window_size, interval_disabled, button_clicks, models_col_style):
    ctx = dash.callback_context
    # print(f'check_status_ipdd {ctx.triggered} {status} {window_size}')

    # when the user starts a new process drift analysis
    if ctx.triggered[0]['prop_id'] == 'window-size.children' and window_size > 0:
        if status == IPDDProcessingStatus.NOT_STARTED or status == IPDDProcessingStatus.IDLE:
            # starts the interval and hide the parameters panel
            return False, 1, {'display': 'none'}
        else:
            # IPDD is still running
            return interval_disabled, button_clicks, models_col_style
    # interval check
    elif window_size > 0:
        # print(f'interval check: status {status}')
        if status == IPDDProcessingStatus.RUNNING:
            return interval_disabled, button_clicks, models_col_style
        if status == IPDDProcessingStatus.IDLE:
            return True, 0, {'display': 'block'}
    # user selected a new event log
    else:
        if status == IPDDProcessingStatus.IDLE:
            framework.restart_status()
            return False, 0, {'display': 'none'}
        return True, 0, {'display': 'none'}


@app.callback(Output('window-size', 'children'),
              [Input('mine_models_btn', 'n_clicks')],
              [State('approach', 'value'),
               State('input-window-size', 'value'),
               State('window-type', 'value'),
               State('window-unity', 'value'),
               State('attribute', 'value'),
               State('hidden-filename', 'children'),
               State('metrics', 'value'),
               State('input-delta', 'value')])
def run_framework(n_clicks, approach, input_window_size, window_type, window_unity, attribute, file, metrics,
                  deltaAdwin):
    if n_clicks > 0:
        int_input_size = 0
        if input_window_size is not None:
            int_input_size = int(input_window_size)
        if file != '' and int_input_size > 0:
            print(f'Running IPDD')
            user = get_user_id()
            if approach == Approach.FIXED.name:
                parameters = IPDDParametersFixed(file, approach, window_type, metrics, window_unity, int_input_size)
                framework.run(parameters, user_id=user)
            elif approach == Approach.ADAPTIVE.name:
                if deltaAdwin:
                    parameters = IPDDParametersAdaptive(file, approach, window_type, metrics, attribute, deltaAdwin)
                else:
                    parameters = IPDDParametersAdaptive(file, approach, window_type, metrics, attribute)
                framework.run(parameters, user_id=user)
            else:
                print(f'Incorrect approach {approach}')
        print(f'Setting window-size value {input_window_size}, indicating IPDD starts the analysis')
        return input_window_size
    else:
        print(f'Setting window-size value with initial value 0, indicating IPDD is IDLE')
        return 0


@app.callback([Output('current-model', 'dot_source'),
               Output('div-similarity-metrics-value', 'children')],
              Input('window-slider', 'value'),
              State('activity', 'value'),
              State('hidden-filename', 'children'))
def update_figure(window_value, activity, file):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    process_map = ''
    div_similarity = []
    if 'window-slider' in changed_id and window_value >= 0:
        window_value += 1  # because slider starts on 0 but windows on 1
        process_map = framework.get_model(file, window_value, get_user_id(), activity)
        if window_value > 1:
            previous_process_map = framework.get_model(file, window_value - 1, get_user_id(), activity)
        if framework.get_total_of_windows(
                activity) > 1:  # if there is only one window the metrics manager is not initialized
            if framework.get_metrics_status() == IPDDProcessingStatus.IDLE:
                metrics = framework.get_metrics_manager(activity).get_metrics_info(window_value)
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


@app.callback([Output('window-slider', 'marks'),
               Output('window-slider', 'max'),
               Output('window-slider', 'value'),
               Output('activity_plot', 'src')],
              Input('activity', 'value'),
              State('attribute', 'value'),
              State('approach', 'value'))
def update_slider_and_plot(activity, attribute, approach):
    marks = {}
    max_slider = 0
    selected = -1
    plot = ''
    if approach:
        initial_indexes = None
        if approach == Approach.FIXED.name:
            initial_indexes = framework.get_initial_trace_indexes()
            last_window = framework.get_total_of_windows()
        elif approach == Approach.ADAPTIVE.name:
            initial_indexes = framework.get_initial_trace_indexes(activity)
            last_window = framework.get_total_of_windows(activity)
        else:
            print(f'Approach not identified {approach} in app_process_models.update_slider_and_plot')
        # print(f'update_slider - activity {activity} - last_window {last_window} - indexes {initial_indexes}')
        windows_with_drifts = ()
        if initial_indexes:
            selected = 0
            # get the number of windows generated and the windows reported as containing drifts
            if approach == Approach.FIXED.name:
                total_of_windows = framework.get_total_of_windows()
                if total_of_windows > 1:
                    windows_with_drifts, traces = framework.get_drifts_info()
            elif approach == Approach.ADAPTIVE.name:
                total_of_windows = framework.get_total_of_windows(activity)
                if total_of_windows > 1:
                    windows_with_drifts, traces = framework.get_drifts_info(activity)
            else:
                print(f'Approach not identified {approach} in app_process_models.update_slider_and_plot')

            max_slider = total_of_windows - 1
            for w in range(0, last_window):
                label = str(w + 1) + '|' + str(initial_indexes[w])
                marks[w] = {'label': label}
                if windows_with_drifts and ((w + 1) in windows_with_drifts):
                    marks[w] = {'label': label, 'style': {'color': '#f50'}}
                else:
                    marks[w] = {'label': label}
            if approach == Approach.ADAPTIVE.name and activity and activity != '' and \
                    activity != Activity.ALL.value and attribute:
                plot_filename = framework.get_activity_plot_src(get_user_id(), activity, attribute)
                # print(f'Trying to show plot {plot_filename}')
                encoded_image = base64.b64encode(open(plot_filename, 'rb').read())
                plot = 'data:image/png;base64,{}'.format(encoded_image.decode())
    return marks, max_slider, selected, plot


@app.callback([Output('div-status-similarity', 'children'),
               Output('div-status-mining', 'children'),
               Output('evaluation-card', 'style'),
               Output('button-evaluation', 'style'),
               Output('status-ipdd', 'children'),
               Output('div-status', 'children'),
               Output('activity', 'options'),
               Output('activity', 'value'),
               Output('activity_div', 'style')],
              Input('check-ipdd-finished', 'n_intervals'),
              State('div-status', 'children'),
              State('activity', 'value'),
              State('approach', 'value'))
def update_status_and_drifts(n, div_status, activity, approach):
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
    # div_similarity_status, windows, windows_with_drifts = framework.get_status_similarity_metrics_text()
    div_similarity_status = framework.get_status_similarity_metrics_text()

    # display or not
    display_evaluation = {'display': 'none'}
    style_activity = {'display': 'none'}
    activities = []
    first_activity = ''
    if ipdd_status == IPDDProcessingStatus.FINISHED or ipdd_status == IPDDProcessingStatus.IDLE:
        display_evaluation = {'display': 'block'}

        if framework.get_approach() and framework.get_approach() == Approach.ADAPTIVE.name:
            activities = [{'label': item, 'value': item} for item in framework.get_activities_with_drifts()]
            if len(activities) == 0:  # no drift is detected
                first_activity = Activity.ALL.value
            else:
                style_activity = {'display': 'block'}
                first_activity = framework.get_first_activity()
                print(f'Activities with drifts {activities} - selected activity {first_activity}')

    return div_similarity_status, div_status_mining, display_evaluation, display_evaluation, ipdd_status, \
           div_status, activities, first_activity, style_activity


@app.callback(Output('div-fscore', 'children'),
              [Input('submit-evaluation', 'n_clicks')],
              [State('input-real-drifts', 'value'),
               State('window-size', 'children'),
               State('activity', 'value')])
def evaluate(n_clicks, real_drifts, window_size, activity):
    if n_clicks and real_drifts and real_drifts != '':
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
            windows, traces = framework.get_drifts_info(activity)
            metrics_summary = framework.evaluate(list_real_drifts, traces, window_size, framework.get_number_of_items())
            metric = []
            for metric_name in metrics_summary.keys():
                metric_print = f'{metric_name}: {"{:.2f}".format(metrics_summary[metric_name])}'
                print(f'IPDD evaluated: {metric_print}')
                metric.append(html.H5(metric_print))
        return metric
    return ''
