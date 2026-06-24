from flask import Blueprint, request, jsonify
from datetime import datetime
import pandas as pd
import numpy as np
from core.model_loader import get_state

incident_bp = Blueprint('incident', __name__)

@incident_bp.route('/api/incidents', methods=['GET', 'POST'])
def handle_incidents():
    try:
        state = get_state()
        active_incidents = state['active_incidents']
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'incidents': active_incidents
            })
        else:
            # Create a new active incident
            data = request.json or {}
            cause = data.get('event_cause', 'vehicle_breakdown')
            corr = data.get('corridor', 'Unknown')
            zone = data.get('zone', 'Unknown')
            junc = data.get('junction', 'Unknown')
            etype = data.get('event_type', 'unplanned')
            priority = data.get('priority', 'Low')
            
            now = datetime.now()
            hour = now.hour
            dow = now.weekday()
            
            cause_means = state['cause_means']
            encoders = state['encoders']
            models = state['models']
            impact_explainer = state['impact_explainer']
            
            # Calculate predicted impact
            hist_sev = cause_means.get(cause, 3.5)
            input_data = pd.DataFrame([{
                'event_cause': cause, 'corridor': corr, 'zone': zone, 'junction': junc,
                'hour': hour, 'dow': dow, 'event_type': etype, 'priority': priority,
                'historical_severity': hist_sev
            }])
            
            try:
                for col, le in encoders.items():
                    val = input_data[col].iloc[0]
                    if val not in le.classes_:
                        input_data[col] = int(le.transform([le.classes_[0]])[0])
                    else:
                        input_data[col] = int(le.transform([val])[0])
                    input_data[col] = input_data[col].astype(int)
                
                # Ensure all remaining columns are numeric
                for col in input_data.columns:
                    if input_data[col].dtype == 'object':
                        input_data[col] = pd.to_numeric(input_data[col], errors='coerce')
                
                imp_score = float(models['impact'].predict(input_data)[0])
                log_dur = float(models['duration'].predict(input_data)[0])
                expected_dur = float(np.expm1(log_dur))
                closure_prob = float(models['closure'].predict_proba(input_data)[0][1])
                
                imp_score = min(10.0, max(1.0, round(imp_score, 1)))
                expected_dur = max(10, int(round(expected_dur)))
                closure_prob = round(closure_prob, 2)
                
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
                    
            except Exception as e:
                ml_load_error = state.get('ml_load_error')
                if ml_load_error:
                    return jsonify({'success': False, 'error': f"Failed to predict new incident: {e}. ROOT CAUSE: {ml_load_error}"})
                return jsonify({'success': False, 'error': f"Failed to predict new incident: {e}"})
                
            incident = {
                'id': f"INC{len(active_incidents) + 1:04d}",
                'event_cause': cause,
                'corridor': corr,
                'zone': zone,
                'junction': junc,
                'event_type': etype,
                'priority': priority,
                'start_datetime': now.strftime("%Y-%m-%d %H:%M:%S"),
                'hour': hour,
                'dow': dow,
                'impact_score': imp_score,
                'closure_probability': closure_prob,
                'expected_duration_min': expected_dur,
                'status': 'active',
                'shap_drivers': shap_drivers
            }
            
            active_incidents.append(incident)
            return jsonify({
                'success': True,
                'incident': incident
            })
    except Exception as e:
        print(f"[ERROR] /api/incidents failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@incident_bp.route('/api/incidents/<inc_id>', methods=['DELETE'])
def resolve_incident(inc_id):
    try:
        state = get_state()
        active_incidents = state['active_incidents']
        
        idx = next((i for i, inc in enumerate(active_incidents) if inc['id'] == inc_id), None)
        if idx is not None:
            inc = active_incidents.pop(idx)
            return jsonify({'success': True, 'message': f'Incident {inc_id} resolved.'})
        return jsonify({'success': False, 'error': 'Incident not found'}), 404
    except Exception as e:
        print(f"[ERROR] /api/incidents/<inc_id> failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
