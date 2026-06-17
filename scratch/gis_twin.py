import networkx as nx
import numpy as np
import folium
import os
import json


# Define the junctions with coordinates from the dataset
JUNCTIONS = {
    "MekhriCircle": (13.014602, 77.583981),
    "AyyappaTempleJunc": (12.923716, 77.618662),
    "SatteliteBusStandJunc": (12.954126, 77.543464),
    "YeshwanthpuraCircle": (13.017761, 77.556973),
    "YelhankaCircle": (13.094322, 77.595927),
    "toll gate mysore road": (12.957494, 77.551884),
    "SilkBoardJunc": (12.917013, 77.622874),
    "JalahalliCross(SM Circle)": (13.040089, 77.518302),
    "Nagavara-ORR Junction": (13.039600, 77.624190),
    "K R Circle": (12.976696, 77.586048),
    "KIMCO Junction": (12.951140, 77.538003),
    "HesaraghattaJunction": (13.045216, 77.507432),
    "Devasandra(k r puram)": (13.009463, 77.696157),
    "VeerannapalyaJunction(BEL,HO)": (13.041578, 77.613660),
    "TownhallJunction": (12.963982, 77.584377),
    "KoramangalaWaterTankJunc": (12.927340, 77.620973),
    "GokuldasImagesJunc": (13.030656, 77.536423),
    "HebbalFlyoverJunc": (13.042259, 77.590922),
    "BagalurCrossJunc": (13.122026, 77.610863),
    "BigBazaarJunction(OldMadrasRd)": (12.991387, 77.657421),
    "Bommanahalli": (12.906964, 77.628165),
    "PoliceCornerJunc": (12.968715, 77.587036),
    "BEL Circle": (13.044357, 77.555854),
    "SantheCircle": (13.097470, 77.598195),
    "KhodaysCircle(DV UrsCircle)": (12.980188, 77.571559),
    "RajeshwariJunc": (12.936725, 77.519071),
    "LeprosyhospitalJunc": (12.975538, 77.564240),
    "GoruguntepalyaJunc": (13.029652, 77.540355),
    "SRS Peenya Junc": (13.034509, 77.529849),
    "CMP GateJunc": (12.957914, 77.605855)
}

# Define corridors connecting junctions (Geospatial edges)
CORRIDOR_EDGES = [
    # Tumkur Road Corridor
    ("HesaraghattaJunction", "JalahalliCross(SM Circle)", "Tumkur Road"),
    ("JalahalliCross(SM Circle)", "SRS Peenya Junc", "Tumkur Road"),
    ("SRS Peenya Junc", "GoruguntepalyaJunc", "Tumkur Road"),
    ("GoruguntepalyaJunc", "YeshwanthpuraCircle", "Tumkur Road"),
    
    # Outer Ring Road (ORR) North & East
    ("YeshwanthpuraCircle", "BEL Circle", "ORR North 1"),
    ("BEL Circle", "HebbalFlyoverJunc", "ORR North 1"),
    ("HebbalFlyoverJunc", "VeerannapalyaJunction(BEL,HO)", "ORR North 2"),
    ("VeerannapalyaJunction(BEL,HO)", "Nagavara-ORR Junction", "ORR North 2"),
    ("Nagavara-ORR Junction", "Devasandra(k r puram)", "ORR East 1"),
    ("Devasandra(k r puram)", "BigBazaarJunction(OldMadrasRd)", "ORR East 1"),
    ("BigBazaarJunction(OldMadrasRd)", "AyyappaTempleJunc", "ORR East 2"),
    ("AyyappaTempleJunc", "SilkBoardJunc", "ORR East 2"),
    
    # Bellary Road Corridor (Airport Road)
    ("YelhankaCircle", "SantheCircle", "Bellary Road 2"),
    ("SantheCircle", "BagalurCrossJunc", "Bellary Road 2"),
    ("BagalurCrossJunc", "HebbalFlyoverJunc", "Bellary Road 1"),
    ("HebbalFlyoverJunc", "MekhriCircle", "Bellary Road 1"),
    ("MekhriCircle", "KhodaysCircle(DV UrsCircle)", "Bellary Road 1"),
    
    # Mysore Road Corridor
    ("RajeshwariJunc", "KIMCO Junction", "Mysore Road"),
    ("KIMCO Junction", "SatteliteBusStandJunc", "Mysore Road"),
    ("SatteliteBusStandJunc", "toll gate mysore road", "Mysore Road"),
    ("toll gate mysore road", "TownhallJunction", "Mysore Road"),
    
    # Central Business District (CBD) Corridors
    ("KhodaysCircle(DV UrsCircle)", "K R Circle", "CBD 1"),
    ("K R Circle", "TownhallJunction", "CBD 1"),
    ("TownhallJunction", "PoliceCornerJunc", "CBD 2"),
    ("PoliceCornerJunc", "LeprosyhospitalJunc", "CBD 2"),
    ("LeprosyhospitalJunc", "CMP GateJunc", "CBD 2"),
    
    # Hosur Road Corridor
    ("CMP GateJunc", "KoramangalaWaterTankJunc", "Hosur Road"),
    ("KoramangalaWaterTankJunc", "SilkBoardJunc", "Hosur Road"),
    ("SilkBoardJunc", "Bommanahalli", "Hosur Road"),
    
    # Interconnecting roads
    ("GokuldasImagesJunc", "YeshwanthpuraCircle", "West of Chord Road"),
    ("GokuldasImagesJunc", "KIMCO Junction", "West of Chord Road"),
]

# Haversine distance calculator helper
def haversine_distance(coord1, coord2):
    R = 6371.0 # Earth's radius in km
    lat1, lon1 = np.radians(coord1[0]), np.radians(coord1[1])
    lat2, lon2 = np.radians(coord2[0]), np.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def build_network():
    G = nx.DiGraph()
    # Add nodes
    for name, coords in JUNCTIONS.items():
        G.add_node(name, lat=coords[0], lon=coords[1])
    
    # Add bidirectional edges
    for u, v, corridor in CORRIDOR_EDGES:
        dist = haversine_distance(JUNCTIONS[u], JUNCTIONS[v])
        G.add_edge(u, v, weight=dist, corridor=corridor, capacity=100.0, current_flow=20.0)
        G.add_edge(v, u, weight=dist, corridor=corridor, capacity=100.0, current_flow=20.0)
    
    return G

# Initialize High-level Graph
G = build_network()

# ── Load OSM driving graph (lazy loaded in background) ──
import threading
G_osm = None
G_osm_loading = False
JUNCTION_OSM_MAP = {}
CORRIDOR_GEOMETRIES = {}

def _bg_load_osm():
    global G_osm, G_osm_loading, JUNCTION_OSM_MAP, CORRIDOR_GEOMETRIES
    try:
        import osmnx as ox
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        osm_path = os.path.join(data_dir, "bengaluru_graph.graphml")
        if not os.path.exists(osm_path):
            osm_path = os.path.join(base_dir, "bengaluru_net.graphml")
            
        junction_map_path = os.path.join(data_dir, "junction_osm_map.json")
        corridor_geom_path = os.path.join(data_dir, "corridor_geometries.json")
        
        if os.path.exists(junction_map_path) and os.path.exists(corridor_geom_path):
            try:
                print("Loading cached OSM routing data...", flush=True)
                with open(junction_map_path, "r") as f:
                    cached_map = json.load(f)
                    for k, v in cached_map.items():
                        JUNCTION_OSM_MAP[k] = int(v)
                with open(corridor_geom_path, "r") as f:
                    cached_geom = json.load(f)
                    for k, val in cached_geom.items():
                        parts = k.split("|||")
                        if len(parts) == 2:
                            u, v = parts[0], parts[1]
                            CORRIDOR_GEOMETRIES[(u, v)] = val
                # Still load the OSM graph for routing and dynamic shortest paths
                if os.path.exists(osm_path):
                    print("Lazy loading OpenStreetMap Digital Twin graph in background...", flush=True)
                    G_osm = ox.load_graphml(osm_path)
                    print("OSM Graph loaded successfully in background from cache path.", flush=True)
                return
            except Exception as e:
                print(f"Error loading cached OSM files, falling back to full calculation: {e}", flush=True)
                
        if os.path.exists(osm_path):
            try:
                print("Lazy loading OpenStreetMap Digital Twin graph in background...", flush=True)
                G_osm = ox.load_graphml(osm_path)
                print("OSM Graph loaded successfully. Mapping junctions to nearest OSM nodes in background...", flush=True)
                for junc_name, coords in JUNCTIONS.items():
                    node_id = ox.nearest_nodes(G_osm, X=coords[1], Y=coords[0])
                    JUNCTION_OSM_MAP[junc_name] = int(node_id)
                print("Junction-OSM node mapping complete.", flush=True)
                
                # Save mapping to cache
                os.makedirs(data_dir, exist_ok=True)
                with open(junction_map_path, "w") as f:
                    json.dump(JUNCTION_OSM_MAP, f)
                
                print("Pre-caching detailed OSM geometry for base corridors in background...", flush=True)
                geom_to_save = {}
                for u, v, name in CORRIDOR_EDGES:
                    osm_u = JUNCTION_OSM_MAP.get(u)
                    osm_v = JUNCTION_OSM_MAP.get(v)
                    coords = None
                    if osm_u is not None and osm_v is not None:
                        try:
                            path = nx.shortest_path(G_osm, osm_u, osm_v, weight='length')
                            coords = [[G_osm.nodes[n]['y'], G_osm.nodes[n]['x']] for n in path]
                        except Exception:
                            try:
                                path = nx.shortest_path(G_osm, osm_v, osm_u, weight='length')
                                coords = [[G_osm.nodes[n]['y'], G_osm.nodes[n]['x']] for n in path]
                            except Exception:
                                pass
                    if coords:
                        CORRIDOR_GEOMETRIES[(u, v)] = coords
                        CORRIDOR_GEOMETRIES[(v, u)] = coords
                        geom_to_save[f"{u}|||{v}"] = coords
                        geom_to_save[f"{v}|||{u}"] = coords
                
                with open(corridor_geom_path, "w") as f:
                    json.dump(geom_to_save, f)
                print("Base corridor OSM geometries cached and saved.", flush=True)
            except Exception as e:
                print(f"Error loading/processing OSM graphml in background: {e}", flush=True)
                G_osm = None
    finally:
        G_osm_loading = False

def ensure_osm_loaded():
    global G_osm, G_osm_loading
    if G_osm is not None or G_osm_loading:
        return
    G_osm_loading = True
    t = threading.Thread(target=_bg_load_osm, daemon=True)
    t.start()

def get_corridies_with_geometries():
    ensure_osm_loaded()
    res = []
    for u, v, name in CORRIDOR_EDGES:
        coords = CORRIDOR_GEOMETRIES.get((u, v)) or CORRIDOR_GEOMETRIES.get((v, u))
        if not coords:
            coords = [list(JUNCTIONS[u]), list(JUNCTIONS[v])]
        res.append({
            'source': u,
            'target': v,
            'name': name,
            'coordinates': coords
        })
    return res


def calculate_route(source, target, closed_edges=[]):
    """
    Calculate primary shortest route, following street centerlines if OSM is available.
    """
    ensure_osm_loaded()
    if G_osm is not None and source in JUNCTION_OSM_MAP and target in JUNCTION_OSM_MAP:
        G_temp = G_osm.copy()
        
        # Block closed corridors on OSM network
        for u, v in closed_edges:
            if u in JUNCTION_OSM_MAP and v in JUNCTION_OSM_MAP:
                osm_u = JUNCTION_OSM_MAP[u]
                osm_v = JUNCTION_OSM_MAP[v]
                try:
                    # Find edges connecting them on standard path and remove them
                    block_path = nx.shortest_path(G_osm, osm_u, osm_v, weight='length')
                    for i in range(len(block_path)-1):
                        u_n = block_path[i]
                        v_n = block_path[i+1]
                        if G_temp.has_edge(u_n, v_n):
                            G_temp.remove_edge(u_n, v_n)
                        if G_temp.has_edge(v_n, u_n):
                            G_temp.remove_edge(v_n, u_n)
                except Exception as e:
                    pass
                    
        try:
            osm_src = JUNCTION_OSM_MAP[source]
            osm_dest = JUNCTION_OSM_MAP[target]
            path_nodes = nx.shortest_path(G_temp, osm_src, osm_dest, weight='length')
            dist_m = nx.path_weight(G_temp, path_nodes, weight='length')
            dist_km = dist_m / 1000.0
            
            # Extract actual road centerline coordinates
            coords = [[G_temp.nodes[n]['y'], G_temp.nodes[n]['x']] for n in path_nodes]
            # Speed assumption: 30 km/h
            travel_time = dist_km / (30.0 / 60.0)
            
            return {
                'success': True,
                'path': [source] + [f"Node_{n}" for n in path_nodes[1:-1]] + [target],
                'distance': dist_km,
                'time_min': travel_time,
                'coordinates': coords
            }
        except nx.NetworkXNoPath:
            # Fall back to high-level graph
            pass

    # FALLBACK: Dijkstra on the high-level network graph G
    G_temp = G.copy()
    for u, v in closed_edges:
        if G_temp.has_edge(u, v): G_temp.remove_edge(u, v)
        if G_temp.has_edge(v, u): G_temp.remove_edge(v, u)
            
    try:
        path = nx.dijkstra_path(G_temp, source, target, weight='weight')
        dist = nx.dijkstra_path_length(G_temp, source, target, weight='weight')
        coords = [JUNCTIONS[node] for node in path]
        travel_time = dist / (30.0 / 60.0)
        return {
            'success': True,
            'path': path,
            'distance': dist,
            'time_min': travel_time,
            'coordinates': coords
        }
    except nx.NetworkXNoPath:
        return {
            'success': False,
            'error': f"No route found between {source} and {target}."
        }

def calculate_k_shortest_paths(source, target, k=3, closed_edges=[]):
    """
    Calculate top K shortest paths using OSM geometries if available.
    """
    ensure_osm_loaded()
    if G_osm is not None and source in JUNCTION_OSM_MAP and target in JUNCTION_OSM_MAP:
        G_temp = G_osm.copy()
        
        # Block closed corridors on OSM network
        for u, v in closed_edges:
            if u in JUNCTION_OSM_MAP and v in JUNCTION_OSM_MAP:
                osm_u = JUNCTION_OSM_MAP[u]
                osm_v = JUNCTION_OSM_MAP[v]
                try:
                    block_path = nx.shortest_path(G_osm, osm_u, osm_v, weight='length')
                    for i in range(len(block_path)-1):
                        u_n = block_path[i]
                        v_n = block_path[i+1]
                        if G_temp.has_edge(u_n, v_n): G_temp.remove_edge(u_n, v_n)
                        if G_temp.has_edge(v_n, u_n): G_temp.remove_edge(v_n, u_n)
                except Exception as e:
                    pass
                    
        try:
            osm_src = JUNCTION_OSM_MAP[source]
            osm_dest = JUNCTION_OSM_MAP[target]
            
            # Convert G_temp (MultiDiGraph) to DiGraph for nx.shortest_simple_paths
            G_simple = nx.DiGraph()
            for u_node, v_node, key, data in G_temp.edges(keys=True, data=True):
                w = data.get('length', 1.0)
                if G_simple.has_edge(u_node, v_node):
                    if w < G_simple[u_node][v_node]['length']:
                        G_simple[u_node][v_node]['length'] = w
                else:
                    G_simple.add_edge(u_node, v_node, length=w)
            
            generator = nx.shortest_simple_paths(G_simple, osm_src, osm_dest, weight='length')
            paths = []
            for i, path in enumerate(generator):
                if i >= k:
                    break
                dist_m = nx.path_weight(G_simple, path, weight='length')
                dist_km = dist_m / 1000.0
                travel_time = dist_km / (30.0 / 60.0)
                paths.append({
                    'path': [source] + [f"Node_{n}" for n in path[1:-1]] + [target],
                    'distance': dist_km,
                    'time_min': travel_time,
                    'coordinates': [[G_temp.nodes[n]['y'], G_temp.nodes[n]['x']] for n in path]
                })
            return {'success': True, 'paths': paths}
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

    # Fallback to high-level graph
    G_temp = G.copy()
    for u, v in closed_edges:
        if G_temp.has_edge(u, v): G_temp.remove_edge(u, v)
        if G_temp.has_edge(v, u): G_temp.remove_edge(v, u)
            
    try:
        generator = nx.shortest_simple_paths(G_temp, source, target, weight='weight')
        paths = []
        for i, path in enumerate(generator):
            if i >= k:
                break
            dist = nx.path_weight(G_temp, path, weight='weight')
            travel_time = dist / (30.0 / 60.0)
            paths.append({
                'path': path,
                'distance': dist,
                'time_min': travel_time,
                'coordinates': [JUNCTIONS[node] for node in path]
            })
        return {'success': True, 'paths': paths}
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {'success': False, 'error': f"No route found between {source} and {target}."}

def simulate_flow_diversion(closed_edge, base_incident_impact=7.0):
    ensure_osm_loaded()
    u, v = closed_edge
    alternatives = []
    
    # Identify adjacent edges or find alternative paths from u to v
    res = calculate_k_shortest_paths(u, v, k=3, closed_edges=[closed_edge])
    if res['success']:
        diverted_load = base_incident_impact * 8.0 # e.g. 56 units of flow
        flow_shares = [0.6, 0.3, 0.1]
        
        for idx, path_info in enumerate(res['paths']):
            if idx >= len(flow_shares):
                break
            share = flow_shares[idx]
            path_nodes = path_info['path']
            flow_added = diverted_load * share
            
            # Map nodes to corridor names
            corridors_traversed = []
            for i in range(len(path_nodes)-1):
                n1, n2 = path_nodes[i], path_nodes[i+1]
                if not n1.startswith("Node_") and not n2.startswith("Node_"):
                    edge_data = G.get_edge_data(n1, n2)
                    corr_name = edge_data['corridor'] if edge_data else "Alternate Road"
                    corridors_traversed.append(corr_name)
            
            if not corridors_traversed:
                corridors_traversed = ["Alternate Bypass Road"]
                
            alternatives.append({
                'rank': idx + 1,
                'path': path_nodes,
                'corridors': list(set(corridors_traversed)),
                'flow_added': flow_added,
                'distance': path_info['distance'],
                'base_time': path_info['time_min'],
                'congested_time': path_info['time_min'] * (1.0 + 0.15 * (flow_added / 35.0)**2),
                'secondary_impact': min(10.0, 3.0 + (flow_added / 10.0)),
                'coordinates': path_info['coordinates']
            })
            
    return alternatives

def generate_digital_twin_map(output_path, active_incidents=[]):
    ensure_osm_loaded()
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=12, tiles="Cartodb Positron")
    
    # Draw corridors
    for u, v, corridor in CORRIDOR_EDGES:
        coords = CORRIDOR_GEOMETRIES.get((u, v)) or CORRIDOR_GEOMETRIES.get((v, u))
        if not coords:
            coords = [list(JUNCTIONS[u]), list(JUNCTIONS[v])]
        folium.PolyLine(
            locations=coords,
            weight=4,
            color="#2d3748",
            opacity=0.6,
            tooltip=f"Corridor: {corridor} (Connecting {u} and {v})"
        ).add_to(m)
        
    incident_nodes = {inc['node']: inc for inc in active_incidents}
    
    for name, coords in JUNCTIONS.items():
        color = "#2b6cb0"
        radius = 6
        popup_html = f"<strong>Junction:</strong> {name}<br><strong>Latitude:</strong> {coords[0]}<br><strong>Longitude:</strong> {coords[1]}"
        
        if name in incident_nodes:
            inc = incident_nodes[name]
            impact = inc['impact']
            color = "#e53e3e" if impact >= 7.0 else "#dd6b20" if impact >= 5.0 else "#38a169"
            radius = 12
            popup_html += f"<br><br>🚨 <strong>ACTIVE INCIDENT</strong><br>Cause: {inc['cause']}<br>Impact: {impact}/10"
            
            folium.CircleMarker(
                location=coords,
                radius=radius * 2,
                color=color,
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.15,
            ).add_to(m)
            
        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
        
    m.save(output_path)
    print(f"Digital Twin Map saved to {output_path}")

# Self-test if executed
if __name__ == "__main__":
    route = calculate_route("MekhriCircle", "SilkBoardJunc")
    print("Standard Route distance:", route['distance'], "km")
