
.. _usage:

Usage
=====

Vocabulary
----------

The Overpass API works by selecting elements from the OSM database and organising them into *sets*,
on which further filtering and combinations can be done. A *statement* is a partcular
operation which collects, filters or combines data and stores the result in a set.

In the following, we use the terms *statements* and *sets* interchangeably. The first
being used more when referring to the *operation* itself, while the second when referring to
the result of that operation.

Statements are separated in two categories: *query statements* and *block statements*.
Query statements collect and filter data from the database while block statements combine
sets. Block statements inherit from the ``BlockStatement`` base class while query statements
inherit from the ``QueryStatement`` base class. The latter implements specific filtering
methods.


Elements filtering
------------------

Query nodes, ways relations and areas with specific filters:

.. code-block:: python

    nodes = Nodes(
        bounding_box=(50.6,7.0,50.8,7.3), name="Foo", amenity="cinema")
    print(build(nodes))

Outputed compiled query:

.. code-block:: text

    node(50.6,7.0,50.8,7.3)["name"="Foo"]["amenity"="cinema"];

The constructors of a query statement can receive various predefined filters,
and an arbitrary number of tag equality filters.
It is also possible to chain specific filters. Each chaining returns a *new* set
which is intersected with the set the filter is applied on. This allows
to reuse any intermediate set in later statements.
During compilation, chained intersections are merged into a single element selection:

.. code-block:: python

    nodes = Nodes()
    nodes = nodes.within((50.6,7.0,50.8,7.3))
    nodes = nodes.where(name="Foo")
    nodes = nodes.around(100.0, lats=[50.7], lons=[7.2])

.. code-block:: text

    node(50.6,7.0,50.8,7.3)["name"="Foo"](around:100.0,50.7,7.2);

This is not always possible however, for example if a filter requires an input set,
the statement computing that set is executed before and its result is stored in a variable.
For example:

.. code-block:: python

    city = Nodes(name="Paris", place="city")
    nodes = Nodes().around(10000., city).where(amenity="cinema")

.. code-block:: text

    node["name"="Paris"]["place"="city"]->.set_0;
    node(around.set_0:10000.0)["amenity"="cinema"];

To add an arbitrary number of filters, use the ``filter`` method, which takes a list
of ``Filter`` instances as arguments:

.. code-block:: python

    paris = Areas(name="Paris")
    nodes = Nodes().filter(
        Area(paris), Key("amenity"), Changed(datetime(2017, 11, 19)))

.. code-block:: text

    area["name"="Paris"]->.set_0;
    node(area.set_0)["amenity"](changed:"2017-11-19T00:00:00Z");

Available filters are listed in the :ref:`API Reference <api-reference-filters>`.


Unions, differences and intersections
-------------------------------------

The ``Union`` and ``Difference`` statements allow to build a union of any number of sets
and a difference between two sets.

.. code-block:: python

    union = Union(
        Nodes(name="Foo"), Ways(name="Foo"), Relations(name="Foo"))
    print(build(union))

    diff = Difference(
        Nodes(bounding_box=(50.6,7.0,50.8,7.3)), Nodes(name="Foo"))
    print(build(diff))

.. code-block:: text

    (node["name"="Foo"]; way["name"="Foo"]; rel["name"="Foo"];);
    (node(50.6,7.0,50.8,7.3); - node["name"="Foo"];);

It is also possible to use addition and substraction to create unions and differences.
Note however that a union of more than two elements using that set creates nested
unions:

.. code-block:: python

    union = Nodes(name="Foo") + Ways(name="Foo") + Relations(name="Foo")
    print(build(union))

    diff = Nodes(bounding_box=(50.6,7.0,50.8,7.3)) - Nodes(name="Foo")
    print(build(diff))

.. code-block:: text

    ((node["name"="Foo"]; way["name"="Foo"];); rel["name"="Foo"];);
    (node(50.6,7.0,50.8,7.3); - node["name"="Foo"];);

Intersections are a specific ``Intersection`` filter. It can also be called from a query
statement:

.. code-block:: python

    union = Nodes(name="Foo") + Ways(name="Foo")
    nodes = Nodes().intersection(union).within((50.6,7.0,50.8,7.3))
    print(build(nodes))

.. code-block:: text

    (node["name"="Foo"]; way["name"="Foo"];)->.set_0;
    node.set_0(50.6,7.0,50.8,7.3);


Labelled sets
-------------

Each statement can receive a ``label`` argument. This label will be used as the name of
variable (if no conflict) in which the result of the statement will be stored.

.. code-block:: python

    city = Areas(name="London", label="london")
    bars = Nodes(name="bar", within=city)

.. code-block:: text

    area["name"="London"]->.london; 
    node(area.london)["name"="bar"];


Raw statements
--------------

It is possible define custom Overpass QL strings as statements via a ``RawStatement``.
Raw statements allow to treat a string as a part of a larger query which depends or
is depended by other statements using placeholders.

.. code-block:: python

    area = Areas(name="Berlin")
    raw = RawStatement("node(area.{a})[!opening_hours]->.{:out_var};", a=area)
    raw.out()

.. code-block:: text

    area["name"="Berlin"]->.set_0;
    node(area.set_0)[!opening_hours]->._;
    out;