# Graphs and visualizations related to COVID-19

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for deamon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081).


### Running without Docker
Alternatively, you can run the server locally without Docker. Create a virtual
environment, install the `covid_graphs` package an run the server.
```sh
python3.7 -m venv your/path/to/venv
source your/path/to/venv/bin/activate
pip install -e . # With -e the package will automatically reload with any local changes.
server.py data build/results-poly.pb build/results-exp.pb
```


## Running standalone graphs

For quick development or data examination, running standalone graphs is useful. We're assuming that the programs are run from the root of the repository.

```sh
covid_graphs/covid_graphs/country.py data Spain
scatter_plot.py data/Slovakia.data build/results.pb
covid_graphs/covid_graphs/heat_map.py build/results.pb
```