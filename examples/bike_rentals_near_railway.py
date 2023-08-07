from overpassforge import Areas, Nodes, beautify, build

sf = Areas(name="San Francisco")
bike_rental = Nodes(within=sf).where(amenity="bicycle_rental")
stations = Nodes(around=(bike_rental, 50)).where(railway="station")
filtered = Nodes(around=(stations, 50)).where(amenity="bicycle_rental")
result = stations + filtered
result.out("meta")

query = build(result)
print(beautify(query))