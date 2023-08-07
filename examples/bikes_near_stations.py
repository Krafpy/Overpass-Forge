import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from overpass_builder import Areas, Nodes, beautify, build

# Find all bike rental stations in San Francisco within 50 meters of a railway station

sf = Areas(name="San Francisco")
bike_rental = Nodes(within=sf).where(amenity="bicycle_rental")
stations = Nodes(around=(bike_rental, 50)).where(railway="station")
filtered = Nodes(around=(stations, 50)).where(amenity="bicycle_rental")
result = stations + filtered
result.out("meta")

query = build(result)
print(beautify(query))