import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from optimizer import optimize_resources

test_incidents = [
    {'id': 'INC0001', 'junction': 'MekhriCircle', 'impact_score': 10.0, 'closure_probability': 0.1, 'duration_min': 120},
    {'id': 'INC0002', 'junction': 'MekhriCircle', 'impact_score': 10.0, 'closure_probability': 0.1, 'duration_min': 120},
    {'id': 'INC0003', 'junction': 'AyyappaTempleJunc', 'impact_score': 10.0, 'closure_probability': 0.1, 'duration_min': 120},
    {'id': 'INC0004', 'junction': 'YeshwanthpuraCircle', 'impact_score': 8.7, 'closure_probability': 0.1, 'duration_min': 120}
]

res = optimize_resources(test_incidents, total_available_officers=5, total_available_barricades=60)
print("Optimization Results:")
print("Status:", res['status'])
print("Success:", res['success'])
print("Total Allocated Officers:", res['total_officers_allocated'])
print("Overall Safety Coverage:", res['overall_safety_coverage'])
print("Deployments:")
for dep in res['deployments']:
    print(f" - {dep['incident_id']} at {dep['junction']}: {dep['officers_allocated']} / {dep['target_officers']}")
