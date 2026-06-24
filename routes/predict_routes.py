from flask import Blueprint, request, jsonify
from core.model_loader import get_state
import pandas as pd
import numpy as np
import os
import json
from core.config import registry_path, active_txt_path, model_dir

predict_bp = Blueprint('predict', __name__)

def _load_registry() -> list:
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            return json.load(f)
    return []

@predict_bp.route('/api/predict', methods=['POST'])
def predict_incident():
    try:
        data = request.json or {}
        
        # Extract inputs
        cause = data.get('event_cause', 'vehicle_breakdown')
        corr = data.get('corridor', 'Unknown')
        zone = data.get('zone', 'Unknown')
        junc = data.get('junction', 'Unknown')
        hour = int(data.get('hour', 12))
        dow = int(data.get('dow', 0))
        etype = data.get('event_type', 'unplanned')
        priority = data.get('priority', 'Low')
        
        state = get_state()
        cause_means = state['cause_means']
        encoders = state['encoders']
        models = state['models']
        impact_explainer = state['impact_explainer']
        
        # Calculate historical severity
        hist_sev = cause_means.get(cause, 3.5)
        
        # Prepare input DataFrame for encoders & models
        input_data = pd.DataFrame([{
            'event_cause': cause,
            'corridor': corr,
            'zone': zone,
            'junction': junc,
            'hour': hour,
            'dow': dow,
            'event_type': etype,
            'priority': priority,
            'historical_severity': hist_sev
        }])
        
        # Encode variables
        for col, le in encoders.items():
            val = input_data[col].iloc[0]
            if val not in le.classes_:
                input_data[col] = le.transform([le.classes_[0]])
            else:
                input_data[col] = le.transform([val])
            
        # Predict Impact Score
        impact_score = float(models['impact'].predict(input_data)[0])
        # Predict Duration (trained on log scale)
        log_dur = float(models['duration'].predict(input_data)[0])
        expected_dur = float(np.expm1(log_dur))
        # Predict Closure Probability
        closure_prob = float(models['closure'].predict_proba(input_data)[0][1])
        
        # Calculate SHAP for impact model
        shap_vals = impact_explainer.shap_values(input_data)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]
        shap_vals = shap_vals[0]
        
        feature_names = input_data.columns.tolist()
        top_drivers_raw = sorted(zip(feature_names, shap_vals.tolist()), key=lambda x: abs(x[1]), reverse=True)[:3]
        
        shap_drivers = []
        for feat, val in top_drivers_raw:
            direction = "up" if val > 0 else "down"
            display_feat = feat.replace('_', ' ').title()
            shap_drivers.append({"feature": display_feat, "value": abs(val), "direction": direction})
        
        # Round values for display
        impact_score = min(10.0, max(1.0, round(impact_score, 1)))
        expected_dur = max(10, int(round(expected_dur)))
        closure_prob = round(closure_prob, 2)
        
        return jsonify({
            'success': True,
            'prediction': {
                'impact_score': impact_score,
                'closure_probability': closure_prob,
                'expected_duration_min': expected_dur,
                'historical_severity': round(hist_sev, 2),
                'shap_drivers': shap_drivers
            }
        })
    except Exception as e:
        print(f"[ERROR] /api/predict failed: {str(e)}")
        return jsonify({'success': False, 'error': f"Prediction model execution failed: {e}", 'detail': str(e)}), 500


@predict_bp.route('/api/model-versions', methods=['GET'])
def get_model_versions():
    try:
        reg = _load_registry()
        return jsonify({"success": True, "versions": reg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@predict_bp.route('/api/active-model', methods=['GET'])
def get_active_model():
    try:
        reg = _load_registry()
        active = next((v for v in reg if v.get("is_active")), None)
        if active:
            dur_mins = active.get('rmse_duration', 0)
            dur_hours = dur_mins / 60.0
            active['duration_rmse_display'] = f"{dur_hours:.1f} hours"
            active['duration_rmse_note'] = "Avg prediction error on event duration"
            return jsonify({"success": True, "active": active})
        return jsonify({"success": False, "message": "No active model found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@predict_bp.route('/api/rollback-model', methods=['POST'])
def rollback_model():
    try:
        data = request.json or {}
        target_version = data.get("version")
        if not target_version:
            return jsonify({"success": False, "message": "Version required"}), 400
            
        import shutil
        imp_src = os.path.join(model_dir, f'xgb_imp_{target_version}.pkl')
        dur_src = os.path.join(model_dir, f'xgb_dur_{target_version}.pkl')
        cls_src = os.path.join(model_dir, f'lgb_cls_{target_version}.pkl')
        
        if not (os.path.exists(imp_src) and os.path.exists(dur_src) and os.path.exists(cls_src)):
            return jsonify({"success": False, "message": f"Physical model files for {target_version} not found"}), 404
            
        shutil.copy(imp_src, os.path.join(model_dir, 'best_impact_model.joblib'))
        shutil.copy(dur_src, os.path.join(model_dir, 'best_duration_model.joblib'))
        shutil.copy(cls_src, os.path.join(model_dir, 'best_closure_model.joblib'))
        
        with open(active_txt_path, "w") as f:
            f.write(target_version)
            
        reg = _load_registry()
        for v in reg:
            v["is_active"] = (v["version"] == target_version)
        with open(registry_path, "w") as f:
            json.dump(reg, f, indent=2)
            
        from core.model_loader import load_all_models
        load_all_models()
        
        from routes.audit_routes import log_audit
        log_audit("Admin", "Model Rollback", "ML Engine", {"version": target_version})
        
        return jsonify({"success": True, "message": f"Successfully rolled back to {target_version}"})
    except Exception as e:
        print(f"[ERROR] /api/rollback-model failed: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
