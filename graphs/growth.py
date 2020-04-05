#!/usr/bin/env python3
from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum
from flask import Flask, render_template
from plotly import offline
from plotly.graph_objs import Figure, Layout, Scatter
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import numpy as np
import os
import sys
import yaml

Country = namedtuple('Country', ['name', 'formula', 'case_count'])
Formula = namedtuple('Formula', ['lambd', 'text', 'maximal_day', 'second_ip_day'])
EXPONENT = 6.23

parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
parser.add_argument('data', metavar='data', type=str, help=f"Directory with YAML files")
parser.add_argument('country', metavar='country', type=str, help=f"Country name or 'ALL'")
args = parser.parse_args()


class GraphType(Enum):
    Normal = 1
    SemiLog = 2
    Log = 3


def TG_formula(TG, A):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{6.23} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}")
    # Second inflection point day
    second_ip_day = math.ceil(TG * (EXPONENT + math.sqrt(EXPONENT)))
    return Formula(lambda t: (A / TG) * ((t / TG)**6.23) / np.exp(t / TG), text, EXPONENT * TG,
                   second_ip_day)


countries = [
    Country('Slovakia', Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$', 60, 60), 10),
    Country('Italy', TG_formula(7.8, 4417), 200),
    # Country('Italy', Formula(lambda t: 0.5382 * t**3.37, r'$0.5382 \cdot t^{3.37}$'), 200),
    Country('Spain', TG_formula(6.4, 3665), 200),
    Country('Germany', TG_formula(6.7, 3773), 200),
    Country('USA', TG_formula(10.2, 72329), 200),
    Country('UK', TG_formula(7.2, 2719), 200),
    Country('France', TG_formula(6.5, 1961), 200),
    Country('Iran', TG_formula(8.7, 2569), 200)
]


class CountryData:
    def __init__(self, path, country_basic):
        self.name = country_basic.name
        self.formula = country_basic.formula
        self.path = os.path.join(path, f'data-{self.name}.yaml')
        with open(self.path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                positive = np.array([point['positive'] for point in data])
                self.dead = np.array([point['dead'] for point in data])
                self.recovered = np.array([point['recovered'] for point in data])
                self.active = positive - self.recovered - self.dead
                self.date_list = [point['date'] for point in data]
            except yaml.YAMLError as exc:
                raise exc

        self.cumulative_active = np.array(
            list(filter(lambda x: x >= country_basic.case_count, np.add.accumulate(self.active))))
        self.date_list = self.date_list[len(self.active) - len(self.cumulative_active):]
        self.x = np.arange(1, self.formula.second_ip_day)
        self.y = country_basic.formula.lambd(self.x)
        self.maximal_date = self.y.argmax()

        self.last_date = datetime.strptime(self.date_list[-1], '%Y-%m-%d')
        self.date_list += [(self.last_date + timedelta(days=d)).strftime('%Y-%m-%d')
                           for d in range(1,
                                          len(self.x) - len(self.date_list) + 1)]
        self.x = self.x[:len(self.date_list)]

    def create_country_figure(self, graph_type=GraphType.Normal):

        maximal_height = max(self.y[self.maximal_date], self.cumulative_active.max())
        shapes = [
            dict(type="line",
                 x0=self.maximal_date,
                 y0=self.y[0],
                 x1=self.maximal_date,
                 y1=maximal_height,
                 line=dict(width=2, dash='dot'))
        ]

        try:
            prediction_date = self.date_list.index('2020-03-29')
            shapes.append(
                dict(type="line",
                     x0=prediction_date,
                     y0=self.y[0],
                     x1=prediction_date,
                     y1=maximal_height,
                     line=dict(width=2, dash='dot')))
        except ValueError:
            pass

        layout = Layout(title=f"Active cases in {self.name}",
                        xaxis=dict(
                            autorange=True,
                            title=r'$\text{Days since the 200}^\mathrm{th}\text{ case}$',
                            type='category',
                            categoryorder='category ascending',
                        ),
                        yaxis=dict(autorange=True, title='COVID-19 active cases', tickformat='.0f'),
                        height=700,
                        shapes=shapes,
                        hovermode='x',
                        font={'size': 15},
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        x = self.x if graph_type != GraphType.Normal else self.date_list
        figure = Figure(layout=layout)
        figure.add_trace(
            Scatter(
                x=x,
                y=self.y,
                text=self.date_list,
                mode='lines',
                name=self.formula.text,
                line={
                    'dash': 'dash',
                    'width': 3,
                    'color': 'rgb(31, 119, 180)',
                },
            ))

        figure.add_trace(
            Scatter(x=x,
                    y=self.cumulative_active,
                    mode='lines+markers',
                    name=f"Active cases",
                    line={
                        'width': 3,
                        'color': 'rgb(239, 85, 59)',
                    },
                    marker={'size': 8}))

        if graph_type == GraphType.Normal:
            figure.update_yaxes(type="linear")
        elif graph_type == GraphType.SemiLog:
            figure.update_xaxes(type="linear")
            figure.update_yaxes(type="log")
        elif graph_type == GraphType.Log:
            figure.update_xaxes(type="log")
            figure.update_yaxes(type="log")
        return figure


def create_dashboard(countries_data, server, graph_type=GraphType.Normal):
    app = dash.Dash(external_scripts=[
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
    ], server=server)
    app.title = 'COVID-19 predictions'
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True

    graphs = [
        dcc.Graph(id=country_data.name, figure=country_data.create_country_figure(graph_type))
        for country_data in countries_data
    ]

    app.layout = html.Div(children=[
        html.H1(children='COVID-19 predictions of Boďová and Kollár'),
        html.Ul([
            html.Li('Black dotted lines: prediction date and maximal date'),
            html.Li('Blue dashed dotted lines: prediction of total active cases'),
            html.Li('Red lines: real total active cases'),
        ])
    ] + graphs)
    return app


if args.country != "ALL":
    country = next(c for c in countries if c.name == args.country)
    country_data = CountryData(args.data, country)
    country_data.create_country_figure().show()
    # offline.plot(country_data.create_country_figure(), filename='graph.html')
else:
    countries_data = [
        CountryData(args.data, country) for country in countries
        if os.path.isfile(os.path.join(args.data, f'data-{country.name}.yaml'))
    ]

    server = Flask(__name__, template_folder='.')
    @server.route("/")
    def home():
        return render_template('index.html')

    @server.route("/covid19-normal")
    def covid19_normal():
        return create_dashboard(countries_data, server, GraphType.Normal).index()

    @server.route("/covid19-semilog")
    def covid19_semilog():
        return create_dashboard(countries_data, server, GraphType.SemiLog).index()

    server.run(host="0.0.0.0", port=8080)
