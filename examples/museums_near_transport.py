from overpassforge import Areas, Nodes, Ways, Union, Around, beautify, build, Settings

# Find Museums in Paris with nearby transportation within 50 Meters

paris = Areas(name="Paris")
museums = Union(
    Nodes(within=paris, tourism="museum"),
    Ways(within=paris, tourism="museum")
)
around_museums = Around(50.0, museums)
result = Union(
    Nodes(around=around_museums).where(highway="bus_stop"),
    Ways(around=around_museums).where(highway="bus_stop"),
    Nodes(around=around_museums).where(railway="tram_stop"),
    Ways(around=around_museums).where(railway="tram_stop"),
    Nodes(around=around_museums).where(railway="subway_entrance"),
    Ways(around=around_museums).where(railway="subway_entrance")
)
result.out("meta")

query = build(result, Settings(out="json", timeout=10))
print(beautify(query))