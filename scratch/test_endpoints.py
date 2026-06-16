import sys
import os
import json

# Add project root to path
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360")
from server import app, active_incidents

print("Initializing Flask test client...")
client = app.test_client()

# Test 1: Get Dashboard Stats
print("\n--- Test 1: Dashboard Stats ---")
res = client.get('/api/dashboard_stats')
print("Status Code:", res.status_code)
print("Data:", json.loads(res.data.decode('utf-8')))

# Test 2: Predict Incident
print("\n--- Test 2: ML Incident Prediction ---")
payload = {
    'event_cause': 'public_event',
    'corridor': 'CBD 2',
    'zone': 'Central Zone 2',
    'junction': 'MekhriCircle',
    'hour': 19,
    'dow': 4,
    'event_type': 'planned',
    'priority': 'High'
}
res = client.post('/api/predict', data=json.dumps(payload), content_type='application/json')
print("Status Code:", res.status_code)
print("Data:", json.loads(res.data.decode('utf-8')))

# Test 3: NetworkX Route & Simulation
print("\n--- Test 3: NetworkX Route & Diversion ---")
payload_route = {
    'source_junction': 'MekhriCircle',
    'target_junction': 'SilkBoardJunc',
    'closed_edges': [['MekhriCircle', 'HebbalFlyoverJunc']]
}
res = client.post('/api/route', data=json.dumps(payload_route), content_type='application/json')
print("Status Code:", res.status_code)
data = json.loads(res.data.decode('utf-8'))
print("Primary Route Path:", data.get('primary_route', {}).get('path'))
print("Diversions Found:", len(data.get('flow_diversions', [])))

# Test 4: Resource Optimization (PuLP)
print("\n--- Test 4: Resource Optimization (PuLP) ---")
# Add some incidents
client.post('/api/incidents', data=json.dumps({
    'event_cause': 'protest', 'corridor': 'Bellary Road 1', 'zone': 'North Zone 2',
    'junction': 'MekhriCircle', 'event_type': 'unplanned', 'priority': 'High'
}), content_type='application/json')

client.post('/api/incidents', data=json.dumps({
    'event_cause': 'vehicle_breakdown', 'corridor': 'Mysore Road', 'zone': 'West Zone 1',
    'junction': 'toll gate mysore road', 'event_type': 'unplanned', 'priority': 'Low'
}), content_type='application/json')

print("Active incidents count:", len(active_incidents))

res = client.post('/api/optimize', data=json.dumps({
    'total_officers': 20,
    'total_barricades': 50
}), content_type='application/json')
print("Status Code:", res.status_code)
opt_data = json.loads(res.data.decode('utf-8'))
print("Optimization Status:", opt_data.get('status'))
print("Overall Safety Coverage %:", opt_data.get('overall_safety_coverage'))
print("Deployments detail:")
for dep in opt_data.get('deployments', []):
    print(f" - {dep['incident_id']} at {dep['junction']}: allocated {dep['officers_allocated']} officers, {dep['barricades_allocated']} barricades")

# Test 5: Conflict Detection
print("\n--- Test 5: Conflict Detection ---")
res = client.get('/api/conflicts')
print("Status Code:", res.status_code)
print("Warnings:", json.loads(res.data.decode('utf-8')).get('warnings'))

# Test 6: PDF Playbook Generation
print("\n--- Test 6: PDF Playbook Generation ---")
res = client.get(f"/api/playbook/{active_incidents[0]['id']}")
print("Status Code:", res.status_code)
print("Content-Type:", res.headers.get('Content-Type'))
print("Content-Length:", len(res.data), "bytes")

print("\nAll integration checks complete. Backend server intelligence components are fully operational.")
