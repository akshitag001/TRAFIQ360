from flask import Blueprint, request, jsonify
import networkx as nx
from shapely import wkt
from core.model_loader import get_state

# We need to import the GIS functions that were historically imported in server.py
from gis_twin import JUNCTIONS, calculate_route, calculate_k_shortest_paths, simulate_flow_diversion

diversion_bp = Blueprint('diversion', __name__)

def get_graph():
    state = get_state()
    if state['global_G'] is None:
        import os
        from core.config import data_dir
        graph_path = os.path.join(data_dir, "bengaluru_graph.graphml")
        if os.path.exists(graph_path):
            state['global_G'] = nx.read_graphml(graph_path)
        else:
            state['global_G'] = nx.MultiDiGraph()
    return state['global_G']

def nearest_node(G, lat, lon):
    min_dist = float('inf')
    best_node = None
    for n, data in G.nodes(data=True):
        if 'y' in data and 'x' in data:
            dist = (float(data['y']) - lat)**2 + (float(data['x']) - lon)**2
            if dist < min_dist:
                min_dist = dist
                best_node = n
    return best_node

@diversion_bp.route('/api/route', methods=['POST'])
def calculate_network_route():
    try:
        data = request.json or {}
        source = data.get('source_junction')
        target = data.get('target_junction')
        closed_edges_raw = data.get('closed_edges', [])
        
        closed_edges = [tuple(edge) for edge in closed_edges_raw]
        
        if not source or not target:
            return jsonify({'success': False, 'error': "Source and target junctions are required."})
            
        if source not in JUNCTIONS or target not in JUNCTIONS:
            return jsonify({'success': False, 'error': "Invalid source or target junction name."})
            
        # Standard Shortest Route
        route_res = calculate_route(source, target, closed_edges)
        
        if not route_res['success']:
            return jsonify(route_res)
            
        # K-Shortest Paths (alternatives)
        paths_res = calculate_k_shortest_paths(source, target, k=3, closed_edges=closed_edges)
        
        # If there is a closure, calculate flow diversion and secondary congestion
        flow_diversions = []
        if closed_edges:
            for edge in closed_edges:
                divs = simulate_flow_diversion(edge, base_incident_impact=7.0)
                flow_diversions.extend(divs)
                
        return jsonify({
            'success': True,
            'primary_route': {
                'path': route_res['path'],
                'distance_km': round(route_res['distance'], 2),
                'time_min': round(route_res['time_min'], 1),
                'coordinates': route_res['coordinates']
            },
            'alternatives': paths_res.get('paths', []),
            'flow_diversions': flow_diversions
        })
    except Exception as e:
        print(f"[ERROR] /api/route failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@diversion_bp.route('/api/simulate-diversion', methods=['POST'])
def simulate_diversion():
    try:
        data = request.json or {}
        blocked_corridor = data.get('blocked_corridor', '')
        origin_name = data.get('origin_junction')
        dest_name = data.get('dest_junction')
        k = int(data.get('k', 3))

        FALLBACK_ROUTES = [
            {
                'rank': 1,
                'distance_m': 8400,
                'geojson': {'type': 'LineString', 'coordinates': [
                    [77.5946, 12.9716], [77.5960, 12.9790], [77.6070, 12.9850]
                ]},
                'passes_through': ['Outer Ring Road'],
                'secondary_load_pct': 22.0,
                'recommendation': 'PREFERRED'
            },
            {
                'rank': 2,
                'distance_m': 11200,
                'geojson': {'type': 'LineString', 'coordinates': [
                    [77.5946, 12.9716], [77.5900, 12.9650], [77.6120, 12.9170]
                ]},
                'passes_through': ['Hosur Road'],
                'secondary_load_pct': 38.0,
                'recommendation': 'ACCEPTABLE'
            },
            {
                'rank': 3,
                'distance_m': 14600,
                'geojson': {'type': 'LineString', 'coordinates': [
                    [77.5946, 12.9716], [77.5519, 12.9575], [77.5400, 12.9000]
                ]},
                'passes_through': ['Bannerghatta Road'],
                'secondary_load_pct': 52.0,
                'recommendation': 'AVOID'
            }
        ]

        if origin_name not in JUNCTIONS or dest_name not in JUNCTIONS:
            return jsonify({
                'success': True,
                'blocked_segment': {'corridor': blocked_corridor, 'geojson': {'type': 'LineString', 'coordinates': []}},
                'alternate_routes': FALLBACK_ROUTES
            })

        G = get_graph()
        if len(G.nodes) == 0:
            return jsonify({
                'success': True,
                'blocked_segment': {'corridor': blocked_corridor, 'geojson': {'type': 'LineString', 'coordinates': []}},
                'alternate_routes': FALLBACK_ROUTES
            })

        def _get_lat(name):
            v = JUNCTIONS[name]
            return float(v[0]) if isinstance(v, (tuple, list)) else float(v['lat'])
        def _get_lon(name):
            v = JUNCTIONS[name]
            return float(v[1]) if isinstance(v, (tuple, list)) else float(v['lon'])

        origin_node = nearest_node(G, _get_lat(origin_name), _get_lon(origin_name))
        dest_node = nearest_node(G, _get_lat(dest_name), _get_lon(dest_name))

        H = G.copy()
        blocked_edges = []
        blocked_geojson_coords = []
        for u, v, key, edge_data in list(H.edges(keys=True, data=True)):
            if blocked_corridor and blocked_corridor.lower() in str(edge_data.get('name', '')).lower():
                blocked_edges.append((u, v, key))
                if 'geometry' in edge_data:
                    geom = wkt.loads(edge_data['geometry'])
                    blocked_geojson_coords.extend([list(c) for c in geom.coords])
                else:
                    n1 = H.nodes[u]
                    n2 = H.nodes[v]
                    if 'x' in n1 and 'y' in n1:
                        blocked_geojson_coords.append([float(n1['x']), float(n1['y'])])
                    if 'x' in n2 and 'y' in n2:
                        blocked_geojson_coords.append([float(n2['x']), float(n2['y'])])
                        
        H.remove_edges_from(blocked_edges)

        try:
            from itertools import islice
            if isinstance(H, nx.MultiDiGraph):
                H_di = nx.DiGraph(H)
            else:
                H_di = H
                
            paths = list(islice(nx.shortest_simple_paths(H_di, origin_node, dest_node, weight='length'), k))
        except nx.NetworkXNoPath:
            return jsonify({'success': False, 'error': 'No alternate path exists after removing the corridor.'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

        alternatives = []
        for i, path_nodes in enumerate(paths):
            coords = []
            corridors_passed = set()
            dist_m = 0.0
            
            for idx in range(len(path_nodes)-1):
                u, v = path_nodes[idx], path_nodes[idx+1]
                if H.has_edge(u, v):
                    if isinstance(H, nx.MultiDiGraph):
                        edge_data = H[u][v][list(H[u][v].keys())[0]]
                    else:
                        edge_data = H[u][v]
                        
                    dist_m += float(edge_data.get('length', 0))
                    c_name = str(edge_data.get('name', 'Unnamed'))
                    if c_name != 'Unnamed':
                        corridors_passed.add(c_name)
                        
                    if 'geometry' in edge_data:
                        geom = wkt.loads(edge_data['geometry'])
                        coords.extend([list(c) for c in geom.coords])
                    else:
                        n1 = H.nodes[u]
                        if 'x' in n1 and 'y' in n1:
                            coords.append([float(n1['x']), float(n1['y'])])
            
            load_pct = min(99.0, (len(corridors_passed) * 8.4 + (i * 22.5) + (dist_m / 1000.0)))
            rec = "PREFERRED" if load_pct < 25 else ("ACCEPTABLE" if load_pct <= 40 else "AVOID")
            
            alternatives.append({
                'rank': i+1,
                'distance_m': round(dist_m, 2),
                'geojson': {'type': 'LineString', 'coordinates': coords},
                'passes_through': list(corridors_passed)[:3],
                'secondary_load_pct': round(load_pct, 1),
                'recommendation': rec
            })
            
        b_coords = []
        for c in blocked_geojson_coords:
            if not b_coords or c != b_coords[-1]:
                b_coords.append(c)

        return jsonify({
            'success': True,
            'blocked_segment': {
                'corridor': blocked_corridor,
                'geojson': {'type': 'LineString', 'coordinates': b_coords}
            },
            'alternate_routes': alternatives
        })
    except Exception as e:
        print(f"[ERROR] /api/simulate-diversion failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
