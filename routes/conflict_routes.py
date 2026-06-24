from flask import Blueprint, request, jsonify
from core.model_loader import get_state
from gis_twin import CORRIDOR_EDGES
from optimizer import optimize_resources

conflict_bp = Blueprint('conflict', __name__)

def get_zone(corridor):
    c = corridor.lower()
    if 'bellary' in c or 'north' in c: return 'North'
    if 'hosur' in c or 'silk board' in c or 'bommanahalli' in c: return 'South'
    if 'mg road' in c or 'cbd' in c or 'cubbon' in c or 'hal' in c: return 'Central'
    if 'tumkur' in c or 'nayandahalli' in c or 'west' in c: return 'West'
    if 'kr puram' in c or 'whitefield' in c or 'east' in c: return 'East'
    return 'General'

def get_corridor_nodes(corridor_name):
    nodes = set()
    for u, v, name in CORRIDOR_EDGES:
        if name == corridor_name:
            nodes.add(u)
            nodes.add(v)
    return nodes

@conflict_bp.route('/api/conflicts', methods=['GET'])
def check_active_conflicts():
    try:
        state = get_state()
        active_incidents = state['active_incidents']
        G = state['global_graph']
        warnings = []
        
        # 1. Time & Corridor overlap conflicts
        corridor_active = {}
        for inc in active_incidents:
            corr = inc['corridor']
            if corr != 'Unknown' and corr != 'Non-corridor':
                if corr in corridor_active:
                    corridor_active[corr].append(inc['id'])
                else:
                    corridor_active[corr] = [inc['id']]
                    
        for corr, ids in corridor_active.items():
            if len(ids) > 1:
                warnings.append(f"⚠️ Corridor conflict: Multiple active incidents {', '.join(ids)} on '{corr}' corridor.")
                
        # 2. Adjacent junction bottlenecks
        if G:
            for i in range(len(active_incidents)):
                for j in range(i+1, len(active_incidents)):
                    node1 = active_incidents[i]['junction']
                    node2 = active_incidents[j]['junction']
                    if node1 != 'Unknown' and node2 != 'Unknown':
                        if G.has_edge(node1, node2) or G.has_edge(node2, node1):
                            warnings.append(f"⚠️ Junction bottleneck: Active incidents {active_incidents[i]['id']} ({node1}) and {active_incidents[j]['id']} ({node2}) are directly adjacent.")
                        
        # 3. Resource capacity shortfalls
        if active_incidents:
            res_opt = optimize_resources(active_incidents, 30, 50)
            target_officers = sum(round(inc.get('impact_score', 0) * 1.5) for inc in active_incidents)
            if target_officers > 30:
                warnings.append(f"🚨 Resource deficit: Required {target_officers} officers to cover all active safety margins, but only 30 are available.")
                
        return jsonify({
            'success': True,
            'warnings': warnings
        })
    except Exception as e:
        print(f"[ERROR] /api/conflicts failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@conflict_bp.route('/api/detect-conflicts', methods=['POST'])
def detect_conflicts():
    try:
        data = request.json or {}
        events = data.get('events', [])
        
        conflicts = []
        severity_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
        joint_opt_recommended = False
        
        # 1. Global RESOURCE_CONFLICT check
        total_officers_needed = 0
        available_officers = 20 # default
        
        if events:
            available_officers = int(events[0].get('available_officers', 20))
            
        for ev in events:
            impact = float(ev.get('impact_score', 5.0))
            total_officers_needed += int(max(1, round(impact * 1.5)))
            
        if total_officers_needed > available_officers:
            conflicts.append({
                "type": "RESOURCE_CONFLICT",
                "severity": "CRITICAL",
                "events": [ev.get('id', 'Unknown') for ev in events],
                "message": f"Combined officer requirement ({total_officers_needed}) exceeds availability ({available_officers})",
                "fix": "Request mutual aid from adjacent zones"
            })
            severity_summary["CRITICAL"] += 1
            joint_opt_recommended = True

        # Check pairwise conflicts
        n = len(events)
        for i in range(n):
            for j in range(i + 1, n):
                ev1, ev2 = events[i], events[j]
                c1, c2 = ev1.get('corridor', ''), ev2.get('corridor', '')
                h1, h2 = int(ev1.get('hour', 0)), int(ev2.get('hour', 0))
                imp1, imp2 = float(ev1.get('impact_score', 0)), float(ev2.get('impact_score', 0))
                z1, z2 = ev1.get('zone') or get_zone(c1), ev2.get('zone') or get_zone(c2)
                
                # CORRIDOR_CONFLICT — midnight-wraparound-safe hour diff
                hour_diff = min(abs(h1 - h2), 24 - abs(h1 - h2))
                if c1 == c2 and hour_diff <= 4:
                    sev = "HIGH" if imp1 >= 6 and imp2 >= 6 else "MEDIUM"
                    conflicts.append({
                        "type": "CORRIDOR_CONFLICT",
                        "severity": sev,
                        "events": [ev1.get('id'), ev2.get('id')],
                        "message": f"Two events on {c1} within {hour_diff}h — officer pool conflict",
                        "fix": "Run joint ILP optimization with combined officer pool"
                    })
                    severity_summary[sev] += 1
                    joint_opt_recommended = True
                
                # CASCADE_RISK
                if c1 != c2:
                    nodes1 = get_corridor_nodes(c1)
                    nodes2 = get_corridor_nodes(c2)
                    if nodes1.intersection(nodes2):
                        conflicts.append({
                            "type": "CASCADE_RISK",
                            "severity": "MEDIUM",
                            "events": [ev1.get('id'), ev2.get('id')],
                            "message": f"Adjacent corridors blocked ({c1} and {c2}) — cascade congestion likely",
                            "fix": "Activate secondary diversion loops immediately"
                        })
                        severity_summary["MEDIUM"] += 1
                        
                # ZONE_CONFLICT
                if z1 == z2 and z1 != 'General':
                    # only if they overlap somewhat in time, let's say within 6 hours
                    if abs(h1 - h2) <= 6:
                        conflicts.append({
                            "type": "ZONE_CONFLICT",
                            "severity": "MEDIUM",
                            "events": [ev1.get('id'), ev2.get('id')],
                            "message": f"Multiple events in zone {z1} — DCP coordination required",
                            "fix": "Alert Zone Commander"
                        })
                        severity_summary["MEDIUM"] += 1

        return jsonify({
            "success": True,
            "conflicts": conflicts,
            "severity_summary": severity_summary,
            "joint_optimization_recommended": joint_opt_recommended
        })
    except Exception as e:
        print(f"[ERROR] /api/detect-conflicts failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
