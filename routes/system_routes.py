from flask import Blueprint, request, jsonify, send_file
import os
import pandas as pd
from core.config import data_dir, csv_path, active_txt_path, model_dir, feedback_xlsx_path
from core.model_loader import get_state

from gis_twin import get_corridies_with_geometries

system_bp = Blueprint('system', __name__)

@system_bp.route('/api/corridors', methods=['GET'])
def get_corridors_api():
    try:
        corridors = get_corridies_with_geometries()
        return jsonify({
            'success': True,
            'corridors': corridors
        })
    except Exception as e:
        print(f"[ERROR] /api/corridors failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/road-network', methods=['GET'])
def get_road_network():
    try:
        path = os.path.join(data_dir, "road_network.geojson")
        if os.path.exists(path):
            return send_file(path, mimetype='application/json')
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        print(f"[ERROR] /api/road-network failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/junctions', methods=['GET'])
def get_junctions():
    try:
        path = os.path.join(data_dir, "key_junctions.json")
        if os.path.exists(path):
            return send_file(path, mimetype='application/json')
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        print(f"[ERROR] /api/junctions failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/system-health', methods=['GET'])
def system_health():
    """Returns system health status — model files, data sizes, active version."""
    try:
        def _mb(path):
            try:
                return round(os.path.getsize(path) / 1024 / 1024, 2)
            except Exception:
                return 0.0
        active_ver = 'unknown'
        try:
            with open(active_txt_path) as f:
                active_ver = f.read().strip()
        except Exception:
            pass
            
        from routes.predict_routes import _load_registry
        reg = _load_registry()
        active_entry = next((v for v in reg if v.get('is_active')), {})
        
        return jsonify({
            'success': True,
            'models': {
                'impact_model': os.path.exists(os.path.join(model_dir, 'best_impact_model.joblib')),
                'duration_model': os.path.exists(os.path.join(model_dir, 'best_duration_model.joblib')),
                'closure_model': os.path.exists(os.path.join(model_dir, 'best_closure_model.joblib')),
                'label_encoders': os.path.exists(os.path.join(model_dir, 'label_encoders.joblib')),
            },
            'data': {
                'feedback_xlsx_mb': _mb(feedback_xlsx_path),
                'osm_graph_mb': _mb(os.path.join(data_dir, 'bengaluru_graph.graphml')),
                'road_network_mb': _mb(os.path.join(data_dir, 'road_network.geojson')),
            },
            'active_version': active_ver,
            'model_metrics': {
                'lgb_auc': active_entry.get('lgb_auc', 'N/A'),
                'xgb_auc': active_entry.get('xgb_auc', 'N/A'),
                'rmse_impact': active_entry.get('rmse_impact', 'N/A'),
            },
            'last_trained': active_entry.get('trained_at', 'unknown'),
        })
    except Exception as e:
        print(f"[ERROR] /api/system-health failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/causes', methods=['GET'])
def get_causes_api():
    """Returns unique event causes from dataset."""
    try:
        df = pd.read_csv(csv_path, usecols=['event_cause'])
        causes = sorted(df['event_cause'].dropna().unique().tolist())
        return jsonify({'success': True, 'causes': causes})
    except Exception as e:
        print(f"[ERROR] /api/causes failed: {str(e)}")
        return jsonify({'success': True, 'causes': [
            'public_event', 'vip_movement', 'protest', 'procession',
            'construction', 'accident', 'vehicle_breakdown', 'congestion'
        ]})
