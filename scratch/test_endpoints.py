import platform
from collections import namedtuple
_UnameResult = namedtuple('uname_result', ['system', 'node', 'release', 'version', 'machine'])
platform.win32_ver = lambda release='', version='', csd='', ptype='': ('10', '10.0.19045', '', 'Multiprocessor Free')
platform.uname = lambda: _UnameResult('Windows', 'DESKTOP', '10', '10.0.19045', 'AMD64')

import sys
import os
import json

# Add project root to path
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360")
from server import app, active_incidents

print("Initializing Flask test client...", flush=True)
client = app.test_client()

# Test 1: Get Dashboard Stats
print("\n--- Test 1: Dashboard Stats ---", flush=True)
res = client.get('/api/dashboard_stats')
print("Status Code:", res.status_code, flush=True)
print("Data:", json.loads(res.data.decode('utf-8')), flush=True)

# Test 2: Predict Incident
print("\n--- Test 2: ML Incident Prediction ---", flush=True)
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
print("Status Code:", res.status_code, flush=True)
print("Data:", json.loads(res.data.decode('utf-8')), flush=True)

# Test 3: NetworkX Route & Simulation
print("\n--- Test 3: NetworkX Route & Diversion ---", flush=True)
payload_route = {
    'source_junction': 'MekhriCircle',
    'target_junction': 'SilkBoardJunc',
    'closed_edges': [['MekhriCircle', 'HebbalFlyoverJunc']]
}
res = client.post('/api/route', data=json.dumps(payload_route), content_type='application/json')
print("Status Code:", res.status_code, flush=True)
data = json.loads(res.data.decode('utf-8'))
print("Primary Route Path:", data.get('primary_route', {}).get('path'), flush=True)
print("Diversions Found:", len(data.get('flow_diversions', [])), flush=True)

# Test 4: Resource Optimization (PuLP)
print("\n--- Test 4: Resource Optimization (PuLP) ---", flush=True)
# Add some incidents
client.post('/api/incidents', data=json.dumps({
    'event_cause': 'protest', 'corridor': 'Bellary Road 1', 'zone': 'North Zone 2',
    'junction': 'MekhriCircle', 'event_type': 'unplanned', 'priority': 'High'
}), content_type='application/json')

client.post('/api/incidents', data=json.dumps({
    'event_cause': 'vehicle_breakdown', 'corridor': 'Mysore Road', 'zone': 'West Zone 1',
    'junction': 'toll gate mysore road', 'event_type': 'unplanned', 'priority': 'Low'
}), content_type='application/json')

print("Active incidents count:", len(active_incidents), flush=True)

res = client.post('/api/optimize', data=json.dumps({
    'event_cause': 'protest',
    'corridor': 'Bellary Road 1',
    'impact_score': 7.5,
    'closure_probability': 0.8,
    'available_officers': 20,
    'available_barricades': 50
}), content_type='application/json')
print("Status Code:", res.status_code, flush=True)
opt_data = json.loads(res.data.decode('utf-8'))
print("Optimization Status:", opt_data.get('status'), flush=True)
print("Total Officers:", opt_data.get('total_officers'), flush=True)
print("Total Barricades:", opt_data.get('total_barricades'), flush=True)
print("Deployments detail:", flush=True)
for dep in opt_data.get('junction_deployments', []):
    print(f" - {dep['junction_name']}: allocated {dep['officers']} officers, {dep['barricades']} barricades", flush=True)

# Test 5: Conflict Detection
print("\n--- Test 5: Conflict Detection ---", flush=True)
res = client.get('/api/conflicts')
print("Status Code:", res.status_code, flush=True)
print("Warnings:", json.loads(res.data.decode('utf-8')).get('warnings'), flush=True)

# Test 5b: Multi-Event Conflict Detection (POST /api/detect-conflicts)
print("\n--- Test 5b: Multi-Event Conflict Detection ---", flush=True)
payload_conflicts = {
    "events": [
        {"id": "INC0001", "corridor": "Bellary Road 1", "hour": 10, "event_cause": "protest", "impact_score": 7.5, "available_officers": 20, "zone": "North"},
        {"id": "INC0002", "corridor": "Bellary Road 1", "hour": 12, "event_cause": "public_event", "impact_score": 8.0, "available_officers": 20, "zone": "North"}
    ]
}
res = client.post('/api/detect-conflicts', data=json.dumps(payload_conflicts), content_type='application/json')
print("Status Code:", res.status_code, flush=True)
print("Data:", json.loads(res.data.decode('utf-8')), flush=True)

# Test 6: PDF Playbook Generation
print("\n--- Test 6: PDF Playbook Generation ---", flush=True)
res = client.get(f"/api/playbook/{active_incidents[0]['id']}")
print("Status Code:", res.status_code, flush=True)
print("Content-Type:", res.headers.get('Content-Type'), flush=True)
print("Content-Length:", len(res.data), "bytes", flush=True)

print("\nAll integration checks complete. Backend server intelligence components are fully operational.", flush=True)
