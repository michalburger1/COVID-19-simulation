#!/usr/bin/env python3
from plotly import offline
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import plotly.graph_objs as go
import sys
import yaml
from collections import namedtuple

Country = namedtuple('Country', ['name', 'formula', 'case_count'])
Formula = namedtuple('Formula', ['lambd', 'text'])

parser = argparse.ArgumentParser(description='COVID-19 power law visualization')
parser.add_argument('data', metavar='data', type=str, help=f"YAML file with data")
parser.add_argument('country', metavar='country', type=str, help=f"Country")
args = parser.parse_args()


def TG_formula(TG, A):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{6.23} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}")
    return Formula(lambda t: (A / TG) * ((t / TG)**6.23) / np.exp(t / TG), text)


countries = [
    Country('Slovakia', Formula(lambda t: 10 * t**1.21, r'$10 \cdot t^{1.2}$'), 10),
    Country('Italy', TG_formula(7.8, 4417), 200),
    Country('Spain', TG_formula(6.4, 3665), 2500),
    Country('Germany', TG_formula(6.7, 3773), 2500)
]
# Country('Italy', 0.48 * x ** 3.35, r'$0.5382 \cdot t^{3.37}$')]
country = next(c for c in countries if c.name == args.country)

with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        # active = [point['positive'] for point in data]
        active = [point['positive'] - point['recovered'] - point['dead'] for point in data]
        dead = [point['dead'] for point in data]
        recovered = [point['recovered'] for point in data]
        date_list = [point['date'] for point in data]
    except yaml.YAMLError as exc:
        raise exc

cumulative_active = list(filter(lambda x: x >= country.case_count, itertools.accumulate(active)))
date_list = date_list[len(active) - len(cumulative_active):]
x = np.arange(1, len(cumulative_active) + 50)
y_power_law = country.formula.lambd(x)

last_date = datetime.strptime(date_list[-1], '%Y-%m-%d')
date_list += [(last_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(1, 51)]

layout = go.Layout(title=f"Active cases in {country.name}",
                   xaxis=dict(type='log',
                              autorange=True,
                              title=r'$\text{Days since the 200}^\mathrm{th}\text{ case}$'),
                   yaxis=dict(type='log', autorange=True, title='COVID-19 active cases'),
                   hovermode='x',
                   font={'size': 20})
figure = go.Figure(layout=layout)
figure.add_trace(
    go.Scatter(x=x,
               y=cumulative_active,
               text=date_list,
               mode='lines+markers',
               name=f"Active cases",
               line={'width': 3},
               marker={'size': 8}))

figure.add_trace(
    go.Scatter(
        x=x,
        y=y_power_law,
        text=date_list,
        mode='lines',
        name=country.formula.text,
        line={
            'dash': 'dash',
            'width': 3
        },
    ))

# offline.plot(figure, filename='graph.html')
figure.show()
