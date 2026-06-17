import platform
from collections import namedtuple
_UnameResult = namedtuple('uname_result', ['system', 'node', 'release', 'version', 'machine'])
platform.win32_ver = lambda release='', version='', csd='', ptype='': ('10', '10.0.19045', '', 'Multiprocessor Free')
platform.uname = lambda: _UnameResult('Windows', 'DESKTOP', '10', '10.0.19045', 'AMD64')

import joblib
import pandas as pd
import os
import shap

model_dir = "models"
impact_model = joblib.load(os.path.join(model_dir, 'best_impact_model.joblib'))
encoders = joblib.load(os.path.join(model_dir, 'label_encoders.joblib'))

# Mock single input row
input_data = pd.DataFrame([{
    'event_cause': 'public_event',
    'corridor': 'CBD 2',
    'zone': 'Central Zone 2',
    'junction': 'MekhriCircle',
    'hour': 19,
    'dow': 4,
    'event_type': 'planned',
    'priority': 'High',
    'historical_severity': 3.5
}])

for col, le in encoders.items():
    if col in input_data.columns:
        input_data[col] = le.transform([input_data[col].iloc[0]])

print("Running shap TreeExplainer...", flush=True)
explainer = shap.TreeExplainer(impact_model)
print("TreeExplainer constructed. Computing shap_values...", flush=True)
shap_vals = explainer.shap_values(input_data)
print("shap_values computed successfully!", flush=True)
print("shap_vals:", shap_vals, flush=True)
