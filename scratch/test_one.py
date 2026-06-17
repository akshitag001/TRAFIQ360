import sys
import os
import json

sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360")
print("Importing server...", flush=True)
from server import app
print("Initializing test client...", flush=True)
client = app.test_client()

print("\n--- Running Test 1: Dashboard Stats ---", flush=True)
res = client.get('/api/dashboard_stats')
print("Status Code:", res.status_code, flush=True)
print("Data:", json.loads(res.data.decode('utf-8')), flush=True)
print("Test 1 success!", flush=True)
