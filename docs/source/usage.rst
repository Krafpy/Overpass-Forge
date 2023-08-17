
.. _usage:

Usage
=====

Vocabulary
----------

The Overpass API works by selecting *elements* from the OSM database and organising them into *sets*,
on which further filtering and combinations can be done. A *statement* is a partcular
operation which collects, filters or combines statements or sets or apply operations
on sets.

Statements may or may not return a set and are represented by the generic ``Statement`` class.
The ``Set`` class represents a query statement that returns a set, and can be treated as the
resulting set of the statement.


Elements filtering
------------------

Query nodes, ways, relations and areas with specific filters:

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

To query any elements (nodes, ways and relations), use the base ``Elements`` class:

.. code-block:: python

    elements = Elements(name="Foo")

.. code-block:: text

    nwr["name"="Foo"];


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

It is also possible to use addition and substraction operators to create unions and differences:

.. code-block:: python

    union = Nodes(name="Foo") + Ways(name="Foo") + Relations(name="Foo")
    print(build(union))

    diff = Nodes(bounding_box=(50.6,7.0,50.8,7.3)) - Nodes(name="Foo")
    print(build(diff))

.. code-block:: text

    (node["name"="Foo"]; way["name"="Foo"]; rel["name"="Foo"];);
    (node(50.6,7.0,50.8,7.3); - node["name"="Foo"];);

Since unions and differences are sets, it is possible to further apply filters on them:

.. code-block:: python

    union = Nodes(name="Foo") + Ways(name="Foo")
    union = union.where(amenity="cinema")

.. code-block:: text

    (node["name"="Foo"]; way["name"="Foo"];)->.set_0;
    nwr.set_0["amenity"="cinema"];

Intersections are built via a specific ``Intersect`` filter, and can be called from a query
statement:

.. code-block:: python

    union = Nodes(name="Foo") + Ways(name="Foo")
    nodes = Nodes().intersection(union).within((50.6,7.0,50.8,7.3))
    print(build(nodes))

.. code-block:: text

    (node["name"="Foo"]; way["name"="Foo"];)->.set_0;
    node.set_0(50.6,7.0,50.8,7.3);

Or can be constructed using the multiplication operator:

.. code-block:: python

    itsc1 = Nodes(name="Foo") * Nodes(amenity="cinema")
    print(build(itsc1))

    itsc2 = Nodes(name="Foo") * Ways(name="Foo")
    print(build(itsc2))

.. code-block:: text

    node["name"="Foo"]["amenity"="cinema"];

    way["name"="Foo"]->.set_0;
    node["name"="Foo"].set_0;


Recursed down and up sets
-------------------------

It is possible to retrieve all related elements to the elements of a given set by
*recursing* over it. Recursing *up* returns the set of elements
which contain elements from the input set. Recusring *down* returns the elements that
are part of the input set's elements. Recursing down or up *relations* also includes
indirectly related elements.
For more details, check the official
`Overpass QL <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#Recurse_up_(%3C)>`_
documentation.

.. code-block:: python

    a = Nodes(name="Foo", label="a")
    union = a + a.recursed_down()
    union.out()
    print(build(union))

.. code-block:: text

    node["name"="Foo"]->.a;
    (.a; .a >;);
    out;

Labelled sets
-------------

Each statement can receive a ``label`` argument. This label will be used as the name of
variable (if no conflict) in which the result set of the statement (if any *and* required
at compile time) will be stored.

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

The ``{:out_var}`` placheolders is a special placheolder indicating where to insert
the name of the output variable of this statement (if it needs one).