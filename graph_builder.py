import osmnx as ox
import os
import json
import networkx as nx
import json

def build_graph():
    print("Downloading OSM network for Bengaluru...")
    # 1. Download graph
    G = ox.graph_from_place("Bengaluru, India", network_type="drive", retain_all=False, simplify=True)
    
    # 2. Filter to keep only specific highway types
    keep_types = ["motorway", "trunk", "primary", "secondary", "tertiary"]
    
    # We need to filter edges based on highway type. 
    # Highway can be a string or a list of strings if multiple tags exist
    edges_to_remove = []
    for u, v, k, data in G.edges(keys=True, data=True):
        hw = data.get('highway', '')
        if isinstance(hw, list):
            if not any(t in keep_types for t in hw):
                edges_to_remove.append((u, v, k))
        else:
            if hw not in keep_types:
                edges_to_remove.append((u, v, k))
                
    G.remove_edges_from(edges_to_remove)
    
    # Clean up isolated nodes
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    
    # 3. Save graphml
    os.makedirs('data', exist_ok=True)
    ox.save_graphml(G, filepath="data/bengaluru_graph.graphml")
    print("Saved bengaluru_graph.graphml")
    
    # 4. Export as GeoJSON
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    # The edges GeoDataFrame contains the geometries
    gdf_edges = gdf_edges.reset_index()
    # We only need the geometry and maybe some properties
    # GeoJSON doesn't handle lists well, so convert lists to strings
    for col in gdf_edges.columns:
        if col != 'geometry':
            gdf_edges[col] = gdf_edges[col].apply(lambda x: str(x) if isinstance(x, list) else x)
            
    gdf_edges.to_file("data/road_network.geojson", driver="GeoJSON")
    print("Saved road_network.geojson")
    
    # 5. Extract top 20 junctions by degree
    degrees = dict(G.degree())
    # Sort nodes by degree
    top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:20]
    
    junctions = []
    for node_id, degree in top_nodes:
        lat = G.nodes[node_id].get('y')
        lon = G.nodes[node_id].get('x')
        # name might not be available on nodes, but we'll try to find a meaningful name
        name = f"Junction {node_id}"
        if 'name' in G.nodes[node_id]:
            name = G.nodes[node_id]['name']
            
        junctions.append({
            "node_id": node_id,
            "lat": lat,
            "lon": lon,
            "name": name,
            "degree": degree
        })
        
    with open("data/key_junctions.json", "w") as f:
        json.dump(junctions, f, indent=2)
    print("Saved key_junctions.json")

if __name__ == "__main__":
    build_graph()
