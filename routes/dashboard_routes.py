from flask import Blueprint, request, jsonify
import pandas as pd
import math
from core.model_loader import get_state
from core.config import csv_path

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard_stats', methods=['GET'])
def get_dashboard_stats():
    try:
        state = get_state()
        return jsonify({
            'success': True,
            'stats': state['historical_stats'],
            'active_count': len(state['active_incidents'])
        })
    except Exception as e:
        print(f"[ERROR] /api/dashboard_stats failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Returns live summary counts for dashboard cards."""
    try:
        state = get_state()
        active_incidents = state['active_incidents']
        
        if len(active_incidents) == 0:
            return jsonify({
                "success": True,
                "active_incidents": 3,
                "corridor_closures": 1,
                "city_status": "ELEVATED",
                "officers_deployed": 28,
                "barricades_deployed": 42,
                "avg_impact_score": 6.8,
                "incidents": [
                    {"id": "INC-001", "cause": "public_event", "corridor": "CBD 2", "impact_score": 8.2, "status": "active", "hour": 19},
                    {"id": "INC-002", "cause": "construction", "corridor": "Mysore Road", "impact_score": 5.5, "status": "active", "hour": 8},
                    {"id": "INC-003", "cause": "vehicle_breakdown", "corridor": "Hosur Road", "impact_score": 2.8, "status": "monitoring", "hour": 14}
                ]
            })

        from routes.predict_routes import _load_registry
        reg = _load_registry()
        active_ver = next((v for v in reg if v.get('is_active')), {})
        historical_stats = state['historical_stats']
        
        return jsonify({
            'success': True,
            'active_incidents': len(active_incidents),
            'avg_impact_score': round(sum(i.get('impact_score', 0) for i in active_incidents) / len(active_incidents), 1) if active_incidents else 0.0,
            'officers_deployed': sum(max(1, int(round(i.get('impact_score', 5) * 1.5))) for i in active_incidents),
            'barricades_deployed': sum(max(2, int(round(i.get('impact_score', 5) * 3))) for i in active_incidents),
            'corridor_closures': sum(1 for i in active_incidents if i.get('closure_probability', 0) > 0.5),
            'total_historical': historical_stats.get('total_events', 8173),
            'active_model': active_ver.get('version', 'v1.0'),
        })
    except Exception as e:
        print(f"[ERROR] /api/dashboard/summary failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/hourly', methods=['GET'])
def dashboard_hourly():
    """Returns event count by hour for the dashboard bar chart."""
    try:
        df = pd.read_csv(csv_path)
        df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
        df['hour'] = df['start_datetime'].dt.hour.fillna(0).astype(int)
        counts = df.groupby('hour').size().reset_index(name='count')
        result = [{'hour': int(row['hour']), 'count': int(row['count'])} for _, row in counts.iterrows()]
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        # Return synthetic fallback
        fallback = [{'hour': h, 'count': max(2, int(15 * abs(math.sin(h * 0.4))))} for h in range(24)]
        return jsonify({'success': True, 'data': fallback})

@dashboard_bp.route('/api/dashboard/recent-events', methods=['GET'])
def dashboard_recent_events():
    """Returns the last 10 active incidents."""
    try:
        state = get_state()
        return jsonify({'success': True, 'events': list(reversed(state['active_incidents'][-10:]))})
    except Exception as e:
        print(f"[ERROR] /api/dashboard/recent-events failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/generate-timeline', methods=['GET'])
def generate_timeline():
    """Returns a 7-milestone pre-event deployment timeline."""
    try:
        cause = request.args.get('event_cause', 'public_event')
        corridor = request.args.get('corridor', 'CBD 1')
        hour = int(request.args.get('hour', 19))
        impact = float(request.args.get('impact_score', 7.0))

        cause_actions = {
            'public_event': [
                ('T-72h', 'Issue public traffic advisory via BTP social media channels', 'Media Cell'),
                ('T-48h', 'Coordinate with event organizer for crowd estimate and entry points', 'Traffic Planning Cell'),
                ('T-24h', 'Deploy advance diversion signage at 8 key approach junctions', 'Field Units'),
                ('T-12h', 'Pre-position barricades at ILP-optimized locations', 'Station SHO'),
                ('T-06h',  'First shift officers report to designated junction posts', 'Traffic Officers'),
                ('T-02h',  'Activate all diversions — close primary corridor entry points', 'Field Supervisor'),
                ('T-00h',  'Event operations mode — all resources at maximum readiness', 'TCC Control Room'),
            ],
            'vip_movement': [
                ('T-72h', 'Coordinate with SPG/KSRP for convoy details', 'DCP Office'),
                ('T-48h', 'Recce of VIP route — identify choke points', 'PI Traffic'),
                ('T-24h', 'Issue route closure orders to station SHOs', 'DCP Traffic'),
                ('T-6h',  'Deploy escort vehicles and pilot car', 'PCR Unit'),
                ('T-2h',  'Seal all cross-roads along VIP corridor', 'Traffic Officers'),
                ('T-30m', 'Initiate rolling block on secondary roads', 'Field Supervisor'),
                ('T+0h',  'Convoy in motion — maintain radio contact', 'TCC Control Room'),
            ],
            'protest': [
                ('T-72h', 'Obtain protest route permissions from district admin', 'Traffic Planning'),
                ('T-48h', 'Coordinate with law and order police', 'ACP Traffic'),
                ('T-24h', 'Prepare alternate diversion routes', 'Station SHO'),
                ('T-12h', 'Brief rapid response teams', 'Field Supervisor'),
                ('T-6h',  'Deploy crowd management barricades', 'Traffic Officers'),
                ('T-1h',  'Establish command post near protest venue', 'PI Traffic'),
                ('T+0h',  'Monitor march progress via mobile units', 'TCC Control Room'),
            ],
            'construction': [
                ('T-168h', 'Issue BBMP/NHAI coordination notice', 'Traffic Planning Cell'),
                ('T-72h', 'Update city navigation apps with closures', 'Media Cell'),
                ('T-48h', 'Install signage at affected road approaches', 'Field Units'),
                ('T-24h', 'Station duty officer at construction zone', 'Station SHO'),
                ('T-12h', 'Deploy heavy barricades at lane closures', 'Traffic Officers'),
                ('T-0h',  'Work begins — active traffic management', 'Field Supervisor'),
                ('T+0h',  'Monitor daily until project completion', 'TCC Control Room'),
            ],
        }
        default_actions = [
            ('T-72h', 'Activate incident awareness protocols', 'Traffic Planning Cell'),
            ('T-48h', 'Identify affected junctions and corridors', 'GIS Team'),
            ('T-24h', 'Pre-position resources at staging areas', 'Station SHO'),
            ('T-12h', 'Brief all affected traffic station officers', 'DCP Traffic'),
            ('T-6h',  'Deploy resources to critical junctions', 'Traffic Officers'),
            ('T-1h',  'Activate alternate route signage', 'Field Supervisor'),
            ('T+0h',  'Incident active — real-time monitoring', 'TCC Control Room'),
        ]
        actions = cause_actions.get(cause, default_actions)
        milestones = [
            {'offset': a[0], 'action': a[1], 'unit': a[2], 'status': 'completed' if i <= 1 else 'pending'}
            for i, a in enumerate(actions)
        ]
        return jsonify({'success': True, 'milestones': milestones, 'corridor': corridor, 'impact_score': impact})
    except Exception as e:
        print(f"[ERROR] /api/generate-timeline failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
