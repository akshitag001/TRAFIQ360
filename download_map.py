import osmnx as ox
import os

print("OSM boundary configuration...")
# Bounding box coordinates: (left, bottom, right, top) i.e. (west, south, east, north)
# Bbox centered on Bengaluru
west = 77.50
south = 12.90
east = 77.70
north = 13.10

output_path = r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\bengaluru_net.graphml"

print(f"Downloading driving road network from OpenStreetMap (BBox: left={west}, bottom={south}, right={east}, top={north})...")
try:
    # Use osmnx to download the drive graph
    G_osm = ox.graph_from_bbox(bbox=(west, south, east, north), network_type='drive')
    print("Download completed successfully. Saving to GraphML...")
    ox.save_graphml(G_osm, filepath=output_path)
    print(f"Graph successfully serialized to {output_path}")
except Exception as e:
    print(f"Error downloading OSM network graph: {e}")
