# Overpass Query Builder

Requires **Python 3.10 or higher**.

## Setup the development environment

### Windows

```cmd
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Linux

```cmd
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Unit tests

Run all the tests with:

```cmd
python -m pytest ./tests
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
