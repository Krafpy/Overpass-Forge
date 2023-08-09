# Overpass Forge: a query builder for the Overpass query language

[![PyPI latest version](https://img.shields.io/pypi/v/overpassforge)](https://pypi.org/project/overpassforge/)
![License](https://img.shields.io/github/license/Krafpy/Overpass-Forge)
[![Documentation status](https://readthedocs.org/projects/overpassforge/badge/?version=latest)](https://overpassforge.readthedocs.io/en/latest/?badge=latest)
![CI tests](https://github.com/Krafpy/Overpass-Forge/actions/workflows/ci.yml/badge.svg)

An object-oriented model to build Overpass queries in Python. Primarly intended
to generate complex queries in Python.

## Install

Requires **Python 3.10 or higher**. Install with:

```cmd
pip install overpassforge
```

## Example

```python
from overpassforge import Areas, Nodes, Ways, build, beautify

# Find both cinema nodes and ways in Bonn, which
# are at most 100m away from bus stop nodes

bus_stops = Nodes(within=Areas(name="Bonn"), highway="bus_stop")
ways = Ways(around=(bus_stops, 100.0)).where(amenity="cinema")
nodes = Nodes(around=(bus_stops, 100.0)).where(amenity="cinema")
result = ways + nodes
result.out("meta")

query = build(result)
print(beautify(query))
```

Output:

```text
area["name"="Bonn"]->.set_0;
node(area.set_0)["highway"="bus_stop"]->.set_1;
(
  way(around.set_1:100.0)["amenity"="cinema"];
  node(around.set_1:100.0)["amenity"="cinema"];
);
out meta;
```

## Features

List of currently implemented features, based on the [Overpass QL wiki](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL).

- Settings: all except augmented-difference between dates (*adiff*)
- Block statements
  - [x] union, difference, intersection
  - [ ] For-each loop (*foreach*)
  - [ ] Block statements *if, for, complete, retro, compare*
- Standalone statements
  - [x] out
  - [x] Item (implicit)
  - [ ] Recurse up (<) and down (>)
  - [ ] Recurse up relations (<<) and down (>>)
  - [ ] Query for areas (is_in)
  - [ ] Statements *timeline*, *local*, *convert*, *make*
  - [x] The Query Statement (*node, way, rel, area* **only**)
  - [ ] The Query Filter
- Filters
  - [x] By tag (*has-kv*)
  - [x] Bounding box
  - [ ] Recurse (*n, w, r, bn, bw, br*)
  - [ ] Recurse (way_cnt, way_link)
  - [x] By input set (*.setname*)
  - [x] By element id
  - [x] Relative to other elements (*around*)
  - [x] By polygon (*poly*)
  - [x] *newer*
  - [x] By date of change (*changed*)
  - [x] By user (*user, uid*)
  - [x] By area (*area*)
  - [x] Area pivot (*pivot*)
  - [ ] Conditional query filter (*if:*)

## Contributing

### Setup the development environment

#### Windows

```cmd
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

#### Linux

```cmd
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Unit tests

Run all the tests with:

```cmd
python -m pytest ./tests
```
