from flask import Blueprint, request, jsonify
from core.config import btp_xlsx_path
from btp_event_service import get_btp_events, save_btp_import
from routes.audit_routes import log_audit

btp_bp = Blueprint('btp', __name__)

@btp_bp.route('/api/btp/events', methods=['GET'])
def btp_events():
    try:
        events = get_btp_events(use_live=True)
        return jsonify({'success': True, 'events': events, 'count': len(events)})
    except Exception as e:
        print(f"[ERROR] /api/btp/events failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@btp_bp.route('/api/btp/import', methods=['POST'])
def btp_import():
    try:
        data = request.get_json(force=True)
        if not data or 'event' not in data:
            return jsonify({'success': False, 'error': 'Missing event data.'}), 400
        event = data['event']
        user_role = data.get('user_role', 'Operator')
        
        save_btp_import(event, btp_xlsx_path)
        log_audit(user_role, 'btp_import', 'planner', {'event_id': event.get('event_id', ''), 'event_name': event.get('event_name', '')})
        return jsonify({'success': True, 'message': 'BTP event imported successfully.', 'event': event})
    except Exception as e:
        print(f"[ERROR] /api/btp/import failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
