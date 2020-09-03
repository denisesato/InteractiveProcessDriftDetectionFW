import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from apps import app_manage_files, app_generate_process_models, app_preview_file

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Div(id='hidden-filename', hidden=True),
])


@app.callback([Output('page-content', 'children'), Output('hidden-filename', 'children')],
              [Input('url', 'pathname')],
              [State('url', 'search')])
def display_page(pathname, search):
    filename = ''
    if search:
        filename = search.lstrip('?filename=')

    if pathname == '/':
        return app_manage_files.layout, filename
    elif pathname == '/apps/app_generate_process_models':
        return app_generate_process_models.layout, filename
    elif pathname == '/apps/app_preview_file':
        return app_preview_file.layout, filename
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)