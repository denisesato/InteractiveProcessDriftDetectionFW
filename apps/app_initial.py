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
import dash_bootstrap_components as dbc
from dash import html

# configuring a navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Start IPDD", href="/apps/app_manage_files")),
    ],
    brand="IPDD - Interactive Process Drift Detection Framework",
    color="primary",
    dark=True,
)

info_ipdd = [
    dbc.CardBody(
        [
            html.H5("The Interactive Process Drift Detection (IPDD) Framework is a tool for process drift detection and"
                    " analysis.", className="card-text"),
            html.H5(dbc.CardLink(children='Click to start the Interactive Process Drift Detection',
                                 href="/apps/app_manage_files"), className="card-text mt-3"),
            # html.H5("A process drift, also named concept drift, indicates the process changed while being "
            #         "analyzed (Process Mining Manifesto, 2011). ", className="card-text mt-4"),
            # html.H5("IPDD allows the detection of process drifts in the control-flow perspective of the process by "
            #         "applying similarity metrics between process models mined over time. ",
            #         className="card-text mt-3"),

            html.Hr(),
            html.H4("Academic Publications", className="card-subtitle mt-4"),
            html.H6("More details about the "
                    "IPDD framework architecture and the current implementation are available in the related "
                    "publications:",
                    className="card-text mt-3"),

            html.P(dbc.CardLink("Interactive Process Drift Detection Framework - ICAISC 2021",
                                href="https://link.springer.com/chapter/10.1007/978-3-030-87897-9_18",
                                target="_blank")),
            html.P(dbc.CardLink("Interactive Process Drift Detection: A Framework for Visual Analysis of Process "
                                "Drifts (Extended Abstract) - ICPM 2021",
                                href="https://icpmconference.org/2021/wp-content/uploads/sites/5/2021/10/L"
                                     "-Interactive-Process-Drift-Detection-A-Framework-for-Visual-Analysis-of-Process"
                                     "-Drifts.pdf", target="_blank")),
            html.H6("More details about concept drift in process mining are available in the survey: ",
                    className="card-text mt-3"),

            html.P(dbc.CardLink("A Survey on Concept Drift in Process Mining - ACM Computing Surveys 2022",
                                href="https://dl.acm.org/doi/10.1145/3472752?sid=SCITRUS",
                                target="_blank")),

            html.H5(['Source code available at: ',
                     dbc.CardLink(children='https://github.com/denisesato/InteractiveProcessDriftDetectionFW',
                                  id='link-github',
                                  href='https://github.com/denisesato/InteractiveProcessDriftDetectionFW')],
                    className="card-text mt-4"),
        ]
    )
]


def get_layout():
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
