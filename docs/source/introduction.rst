Introduction
============

Overpass Forge is a library aiming at simplifying the automated generation of queries
for the `OpenStreetMap's Overpass API <https://wiki.openstreetmap.org/wiki/Overpass_API>`_
in Python. It offers object-oriented mappings to
`Overpass QL <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL>`_
statements and sets to represent queries, which are then compiled
into the corresponding Overpass QL string.


Installation
------------

Requires **Python 3.10+**. Install via ``pip``:

.. code-block:: console

    (.venv) $ pip install overpassforge


Example
-------

Manipulate query statements as if manipulating the corresponding query result sets.
Introduction of variables and management of dependencies and execution order will
be automatically handled. See the :ref:`api-reference` for the list of all features.

The following code generates the query that finds both cinema nodes and ways in Bonn,
which are at most 100m away from a bus stop node:

.. code-block:: python

    from overpassforge import Areas, Nodes, Ways, build, beautify

    bus_stops = Nodes(within=Areas(name="Bonn"), highway="bus_stop")
    ways = Ways(around=(bus_stops, 100.0)).where(amenity="cinema")
    nodes = Nodes(around=(bus_stops, 100.0)).where(amenity="cinema")
    result = ways + nodes
    result.out("meta")

    query = build(result)
    print(beautify(query))

Output:

.. code-block:: text

    area["name"="Bonn"]->.set_0;
    node(area.set_0)["highway"="bus_stop"]->.set_1;
    (
        way(around.set_1:100.0)["amenity"="cinema"];
        node(around.set_1:100.0)["amenity"="cinema"];
    );
    out meta;