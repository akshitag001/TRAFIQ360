from flask import Blueprint, request, jsonify
import sys
import os
import uuid
import threading
from core.config import base_dir
from core.model_loader import get_state, load_all_models
from routes.audit_routes import log_audit
from routes.feedback_routes import _feedback_xlsx_read
from routes.predict_routes import _load_registry

retrain_bp = Blueprint('retrain', __name__)

@retrain_bp.route('/api/retrain', methods=['POST'])
def trigger_retrain():
    try:
        data = request.get_json(force=True) or {}
        user_role = data.get('user_role', 'Admin')
        job_id = str(uuid.uuid4())[:8]
        
        state = get_state()
        state['retraining_status'][job_id] = {'status': 'running', 'progress': 0, 'message': 'Starting...', 'result': None}

        def _progress(pct, msg):
            state['retraining_status'][job_id]['progress'] = pct
            state['retraining_status'][job_id]['message'] = msg

        def _run():
            try:
                sys.path.insert(0, os.path.join(base_dir, 'scratch'))
                from retrain_pipeline import retrain
                result = retrain(progress_callback=_progress)
                state['retraining_status'][job_id]['status'] = 'done'
                state['retraining_status'][job_id]['result'] = result
                load_all_models()
                log_audit(user_role, 'retrain_trigger', 'learning', result)
            except Exception as e:
                state['retraining_status'][job_id]['status'] = 'error'
                state['retraining_status'][job_id]['message'] = str(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return jsonify({'success': True, 'job_id': job_id, 'message': 'Retraining started in background.'})
    except Exception as e:
        print(f"[ERROR] /api/retrain failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retrain_bp.route('/api/retrain/status/<job_id>', methods=['GET'])
def retrain_status(job_id):
    try:
        state = get_state()
        if job_id not in state['retraining_status']:
            return jsonify({'success': False, 'error': 'Job not found.'}), 404
        return jsonify({'success': True, **state['retraining_status'][job_id]})
    except Exception as e:
        print(f"[ERROR] /api/retrain/status failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retrain_bp.route('/api/models/versions', methods=['GET'])
def model_versions():
    try:
        reg = _load_registry()
        versions = reg if isinstance(reg, list) else reg.get('versions', [])
        return jsonify({'success': True, 'versions': versions})
    except Exception as e:
        print(f"[ERROR] /api/models/versions failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retrain_bp.route('/api/training/queue', methods=['GET'])
def training_queue():
    try:
        records = _feedback_xlsx_read()
        pending = [r for r in records if str(r.get('approval_status', '')).lower() == 'pending']
        approved = [r for r in records if str(r.get('approval_status', '')).lower() == 'approved']
        rejected = [r for r in records if str(r.get('approval_status', '')).lower() == 'rejected']
        return jsonify({'success': True, 'pending': len(pending), 'approved': len(approved), 'rejected': len(rejected), 'total': len(records)})
    except Exception as e:
        print(f"[ERROR] /api/training/queue failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
