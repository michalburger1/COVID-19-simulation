#!/usr/bin/env python3

from setuptools import find_namespace_packages, setup

setup(
    name="covid_graphs",
    version="1.0",
    description="COVID-19 graph plotting",
    install_requires=[
        "click",
        "click_pathlib",
        "dash",
        "Flask",
        "inotify",
        "numpy",
        "pandas",
        "protobuf",
        "plotly",
        "pytest",
        "scipy",
    ],
    dependency_links=[],
    python_requires=">=3.7",
    packages=find_namespace_packages(),
    entry_points={
        "console_scripts": [
            "covid_graphs.run_server = covid_graphs.scripts.server:run_server",
            "covid_graphs.show_country_plot = covid_graphs.country_graph:show_country_plot",
            "covid_graphs.show_heat_map = covid_graphs.heat_map:show_heat_map",
            "covid_graphs.show_scatter_plot = covid_graphs.scatter_plot:show_scatter_plot",
            "covid_graphs.prepare_data = covid_graphs.prepare_data:main"
        ]
    },
    package_data={"": ["*.html"]},
)
