from flask import Blueprint, request, jsonify
import pulp
import math
import os
import json
from core.config import data_dir
from core.model_loader import get_state

from gis_twin import CORRIDOR_EDGES, JUNCTIONS

optimize_bp = Blueprint('optimize', __name__)

@optimize_bp.route('/api/optimize', methods=['POST'])
def run_resource_optimization():
    try:
        data = request.json or {}
        event_cause = data.get('event_cause', '')
        corridor = data.get('corridor', '')
        impact_score = float(data.get('impact_score', 0))
        closure_probability = float(data.get('closure_probability', 0))
        available_officers = int(data.get('available_officers', 20))
        available_barricades = int(data.get('available_barricades', 100))

        # Identify affected junctions based on the corridor
        affected_junc_names = set()
        for u, v, corr_name in CORRIDOR_EDGES:
            if corr_name == corridor:
                affected_junc_names.add(u)
                affected_junc_names.add(v)
                
        # Load junction metadata
        key_junc_path = os.path.join(data_dir, "key_junctions.json")
        junc_meta = {}
        if os.path.exists(key_junc_path):
            try:
                with open(key_junc_path, 'r') as f:
                    for j in json.load(f):
                        junc_meta[j['name']] = j
            except Exception:
                pass
                
        affected_junctions = []
        for name in affected_junc_names:
            if name in junc_meta:
                affected_junctions.append(junc_meta[name])
            elif name in JUNCTIONS:
                # Fallback
                affected_junctions.append({
                    "name": name,
                    "lat": JUNCTIONS[name][0],
                    "lon": JUNCTIONS[name][1],
                    "degree": 3 # Default degree
                })
                
        if not affected_junctions:
            return jsonify({
                'status': 'infeasible',
                'total_officers': 0,
                'total_barricades': 0,
                'junction_deployments': [],
                'objective_value': 0,
                'coverage_warning': f"No junctions found for corridor {corridor}"
            })

        prob = pulp.LpProblem("Live_Optimization", pulp.LpMinimize)
        
        officers = pulp.LpVariable.dicts("Officers", [j['name'] for j in affected_junctions], lowBound=0, cat='Integer')
        barricades = pulp.LpVariable.dicts("Barricades", [j['name'] for j in affected_junctions], lowBound=0, cat='Integer')
        
        # Objective
        prob += pulp.lpSum([officers[j['name']] for j in affected_junctions]) + 0.5 * pulp.lpSum([barricades[j['name']] for j in affected_junctions])
        
        # Constraints
        prob += pulp.lpSum([officers[j['name']] for j in affected_junctions]) <= available_officers
        prob += pulp.lpSum([barricades[j['name']] for j in affected_junctions]) <= available_barricades
        
        min_off_total = 0
        for j in affected_junctions:
            j_name = j['name']
            j_load = j.get('degree', 3)
            # min_coverage constraint based on load and impact
            min_cov = max(1, math.ceil(j_load * impact_score * 0.1))
            
            prob += officers[j_name] >= min_cov
            min_off_total += min_cov
            
            # barricade constraint
            if closure_probability > 0.6:
                prob += barricades[j_name] >= 2
            elif closure_probability > 0.3:
                prob += barricades[j_name] >= 1
            else:
                prob += barricades[j_name] >= 0
                
            if impact_score >= 7:
                prob += officers[j_name] >= 2
                
        # Solve with 3-second time limit so it never hangs
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=3))
        
        status = pulp.LpStatus[prob.status]
        
        if status != 'Optimal':
            # Proportional fallback — never return empty deployments
            n_junc = len(affected_junctions)
            off_each = max(1, available_officers // n_junc) if n_junc > 0 else 1
            bar_each = max(0, available_barricades // n_junc) if n_junc > 0 else 0
            fallback_deployments = []
            for j in affected_junctions:
                fallback_deployments.append({
                    'junction_name': j['name'],
                    'lat': j.get('lat', 12.9716),
                    'lon': j.get('lon', 77.5946),
                    'officers': off_each,
                    'barricades': bar_each,
                    'priority': 'MEDIUM'
                })
            return jsonify({
                'status': 'proportional_fallback',
                'total_officers': off_each * n_junc,
                'total_barricades': bar_each * n_junc,
                'junction_deployments': fallback_deployments,
                'objective_value': 0,
                'coverage_warning': f"Insufficient officers — minimum {min_off_total} required, proportional allocation applied"
            })
            
        deployments = []
        tot_off = 0
        tot_bar = 0
        for j in affected_junctions:
            j_name = j['name']
            off = int(officers[j_name].varValue)
            bar = int(barricades[j_name].varValue)
            tot_off += off
            tot_bar += bar
            
            priority = "LOW"
            if off >= 4:
                priority = "HIGH"
            elif off >= 2:
                priority = "MEDIUM"
                
            deployments.append({
                "junction_name": j_name,
                "lat": j['lat'],
                "lon": j['lon'],
                "officers": off,
                "barricades": bar,
                "priority": priority
            })
            
        return jsonify({
            'status': 'optimal',
            'total_officers': tot_off,
            'total_barricades': tot_bar,
            'junction_deployments': deployments,
            'objective_value': pulp.value(prob.objective),
            'coverage_warning': None
        })
    except Exception as e:
        print(f"[ERROR] /api/optimize failed: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
