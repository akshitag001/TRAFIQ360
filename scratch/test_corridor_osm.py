import sys
import os
import networkx as nx

# Add project root to path
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360")
from scratch.gis_twin import G_osm, JUNCTION_OSM_MAP, CORRIDOR_EDGES, JUNCTIONS

if G_osm is None:
    print("Error: G_osm is None. Make sure bengaluru_net.graphml exists.")
    sys.exit(1)

print("G_osm loaded. Number of nodes:", G_osm.number_of_nodes())

success_count = 0
fallback_count = 0

for u, v, name in CORRIDOR_EDGES:
    osm_u = JUNCTION_OSM_MAP.get(u)
    osm_v = JUNCTION_OSM_MAP.get(v)
    
    if osm_u is None or osm_v is None:
        print(f"Junction not mapped: {u} or {v}")
        fallback_count += 1
        continue
        
    coords = None
    # Try u -> v
    try:
        path = nx.shortest_path(G_osm, osm_u, osm_v, weight='length')
        coords = [[G_osm.nodes[n]['y'], G_osm.nodes[n]['x']] for n in path]
    except Exception as e:
        # Try v -> u
        try:
            path = nx.shortest_path(G_osm, osm_v, osm_u, weight='length')
            coords = [[G_osm.nodes[n]['y'], G_osm.nodes[n]['x']] for n in path]
            # Reverse coords to match u -> v orientation
            coords.reverse()
        except Exception as e2:
            pass
            
    if coords:
        print(f"Successfully mapped {name} ({u} -> {v}) with {len(coords)} OSM points.")
        success_count += 1
    else:
        print(f"Failed to map {name} ({u} -> {v}). Using straight line fallback.")
        fallback_count += 1

print(f"\nSummary: Successfully mapped {success_count}/{len(CORRIDOR_EDGES)} corridors.")
