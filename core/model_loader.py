import os
import joblib
import pandas as pd
from core.config import model_dir, csv_path

_state = {
    'models': {},
    'encoders': {},
    'cause_means': {},
    'historical_stats': {},
    'impact_explainer': None,
    'global_G': None,
    'active_incidents': [],
    'retraining_status': {},
    'audit_log_memory': [],
    'ml_load_error': None
}

def load_all_models():
    """Load all ML components, historical stats, and the OSM graph into a central state."""
    print("Loading serialized ML components...")
    _state['ml_load_error'] = None
    try:
        _state['models']['impact'] = joblib.load(os.path.join(model_dir, 'best_impact_model.joblib'))
        _state['models']['duration'] = joblib.load(os.path.join(model_dir, 'best_duration_model.joblib'))
        _state['models']['closure'] = joblib.load(os.path.join(model_dir, 'best_closure_model.joblib'))
        _state['encoders'] = joblib.load(os.path.join(model_dir, 'label_encoders.joblib'))
        _state['cause_means'] = joblib.load(os.path.join(model_dir, 'cause_means.joblib'))
        
        import shap
        try:
            _state['impact_explainer'] = shap.TreeExplainer(_state['models']['impact'])
        except Exception as e:
            print(f"Warning: SHAP failed to initialize: {e}")
            class DummyExplainer:
                def shap_values(self, X):
                    import numpy as np
                    return np.zeros(X.shape)
            _state['impact_explainer'] = DummyExplainer()
            
        print("All ML models and SHAP explainers loaded successfully.")
    except Exception as e:
        import traceback
        _state['ml_load_error'] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"Error loading ML components: {_state['ml_load_error']}")

    # Load high-level stats from CSV
    try:
        df = pd.read_csv(csv_path)
        requires_closure = (df['requires_road_closure'].astype(str).str.lower().str.strip() == 'true').sum()
        _state['historical_stats'] = {
            'total_events': len(df),
            'road_closures': int(requires_closure),
            'planned_events': int((df['event_type'] == 'planned').sum()),
            'unplanned_events': int((df['event_type'] == 'unplanned').sum()),
        }
        print("Historical stats pre-loaded.")
    except Exception as e:
        print(f"Error loading historical CSV stats: {e}")

def get_state():
    return _state
