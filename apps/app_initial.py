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
import uuid

import dash_bootstrap_components as dbc
import dash_html_components as html
from flask import session

# configuring a navbar
from app import framework

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Start IPDD", href="/apps/app_manage_files")),
    ],
    brand="IPDD Framework - Interactive Process Drift Detection Framework",
    color="primary",
    dark=True,
)

info_ipdd = [
    dbc.CardBody(
        [
            html.H5("The Interactive Process Drift Detection (IPDD) Framework is a tool for process drift visual "
                    "analysis.", className="card-text"),
            html.H5(dbc.CardLink(children='Start IPDD here', href="/apps/app_manage_files"), className="card-text mt-3"),
            html.H5("A process drift, also named concept drift, indicates the process changed while being "
                    "analyzed (Process Mining Manifesto, 2011). ", className="card-text mt-4"),
            html.H5("IPDD allows the detection of process drifts in the control-flow perspective of the process by "
                    "applying similarity metrics between process models mined over time. ",
                    className="card-text mt-3"),

            html.H5(['Source code available at: ',
                     dbc.CardLink(children='https://github.com/denisesato/InteractiveProcessDriftDetectionFW',
                                  id='link-github',
                                  href='https://github.com/denisesato/InteractiveProcessDriftDetectionFW')],
                    className="card-text mt-4"),

            # html.Hr(),
            # html.H4("Academic Publications", className="card-subtitle mt-4"),
            # html.H6("More details about the "
            #         "framework architecture and the current implementation are available in the related publications.",
            #         className="card-text mt-3"),
            #
            # dbc.CardLink("External link", href="https://google.com", className="card-text mt-2"),

        ]
    )
]


def get_layout():
    if not session.get('user'):
        print(f'Creating user session...')
        session['user'] = str(uuid.uuid4())

    # main layout of the page
    layout = [
        dbc.Row([
            dbc.Col(navbar, width=12)
        ]),
        dbc.Row([
            dbc.Col(info_ipdd, className='mt-2', width=12)
        ], justify="around"),
    ]

    return layout
