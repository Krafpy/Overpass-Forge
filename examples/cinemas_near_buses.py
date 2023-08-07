import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from overpass_builder import Areas, Nodes, Ways, beautify, build

# Find both cinema nodes and ways in Bonn, which are at most 100m away from bus stop nodes"""

bus_stops = Nodes(within=Areas(name="Bonn"), highway="bus_stop")
ways = Ways(around=(bus_stops, 100.0)).where(amenity="cinema")
nodes = Nodes(around=(bus_stops, 100.0)).where(amenity="cinema")
result = ways + nodes
result.out("meta")

query = build(result)
print(beautify(query))