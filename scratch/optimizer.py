import pulp
import numpy as np
import json

def optimize_resources(active_incidents, total_available_officers=50, total_available_barricades=100):
    """
    Solves an Integer Linear Programming (ILP) model to allocate resources to active incidents.
    
    active_incidents: list of dicts: [
        {'id': 'FKID123', 'junction': 'MekhriCircle', 'impact_score': 6.5, 'closure_probability': 0.72},
        ...
    ]
    total_available_officers: budget of officers
    total_available_barricades: budget of barricades
    """
    prob = pulp.LpProblem("Manpower_Barricading_Optimization", pulp.LpMinimize)
    
    # Indices
    incident_ids = [inc['id'] for inc in active_incidents]
    
    # Decision Variables
    # Number of officers allocated to each incident
    officers_vars = pulp.LpVariable.dicts("Officers", incident_ids, lowBound=0, cat='Integer')
    # Number of barricades allocated to each incident
    barricades_vars = pulp.LpVariable.dicts("Barricades", incident_ids, lowBound=0, cat='Integer')
    
    # Slack variables for under-deployment (safety requirement deficits)
    officer_deficit = pulp.LpVariable.dicts("Off_Deficit", incident_ids, lowBound=0, cat='Continuous')
    barricade_deficit = pulp.LpVariable.dicts("Bar_Deficit", incident_ids, lowBound=0, cat='Continuous')
    
    # Calculate safety coverage targets for each incident based on impact score & closure probability
    officer_targets = {}
    barricade_targets = {}
    impact_scores = {}
    
    for inc in active_incidents:
        inc_id = inc['id']
        score = inc['impact_score']
        p_close = inc['closure_probability']
        impact_scores[inc_id] = score
        
        # Officer targets: round(score * 1.5), min 1 officer
        officer_targets[inc_id] = max(1, int(round(score * 1.5)))
        # Barricade targets: round(p_close * 6) if p_close >= 0.3, else 0
        barricade_targets[inc_id] = int(round(p_close * 6)) if p_close >= 0.3 else 0
        
    # Objective function components:
    # 1. Cost of resource deployment (we want to minimize unnecessary resource usage)
    # 2. High penalty for under-deployment (deficit) scaled by incident impact score
    # Penalty cost = sum( impact_score * (10.0 * officer_deficit + 5.0 * barricade_deficit) )
    
    deployment_cost = pulp.lpSum([officers_vars[i] + 0.5 * barricades_vars[i] for i in incident_ids])
    penalty_cost = pulp.lpSum([
        impact_scores[i] * (15.0 * officer_deficit[i] + 8.0 * barricade_deficit[i])
        for i in incident_ids
    ])
    
    prob += deployment_cost + penalty_cost, "Total_Deployment_and_Safety_Cost"
    
    # Calculate minimum floor requirements
    min_officers_required = 0
    min_barricades_required = 0
    for i in incident_ids:
        if impact_scores[i] >= 7.0:
            min_officers_required += 2
            if barricade_targets[i] > 0:
                min_barricades_required += 2
        elif impact_scores[i] >= 5.0:
            min_officers_required += 1

    enforce_min_floors = (min_officers_required <= total_available_officers)
    enforce_min_barricades = (min_barricades_required <= total_available_barricades)

    # Constraints
    # 1. Total resource capacities
    prob += pulp.lpSum([officers_vars[i] for i in incident_ids]) <= total_available_officers, "Max_Available_Officers"
    prob += pulp.lpSum([barricades_vars[i] for i in incident_ids]) <= total_available_barricades, "Max_Available_Barricades"
    
    # 2. Deficit definition constraints (soft requirements)
    for i in incident_ids:
        # Deficit_i >= Target_i - Deployed_i
        prob += officer_deficit[i] >= officer_targets[i] - officers_vars[i], f"Officer_Deficit_Def_{i}"
        prob += barricade_deficit[i] >= barricade_targets[i] - barricades_vars[i], f"Barricade_Deficit_Def_{i}"
        
        # Min safety floors (enforced only if mathematically feasible to prevent solver infeasibility)
        if enforce_min_floors:
            if impact_scores[i] >= 7.0:
                prob += officers_vars[i] >= 2, f"Min_Officers_High_Impact_{i}"
            elif impact_scores[i] >= 5.0:
                prob += officers_vars[i] >= 1, f"Min_Officers_Med_Impact_{i}"
                
        if enforce_min_barricades:
            if impact_scores[i] >= 7.0 and barricade_targets[i] > 0:
                prob += barricades_vars[i] >= 2, f"Min_Barricades_High_Impact_{i}"
            
    # Solve
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    # Check if the optimization succeeded; if not (e.g. solver error or infeasibility), use a heuristic fallback
    solver_success = (pulp.LpStatus[status] == "Optimal")
    
    if not solver_success:
        # Fallback heuristic: Proportional allocation mapping (guarantees positive values and respects budget)
        total_target_off = sum(officer_targets.values())
        off_ratio = total_available_officers / total_target_off if total_target_off > 0 else 0
        
        total_target_bar = sum(barricade_targets.values())
        bar_ratio = total_available_barricades / total_target_bar if total_target_bar > 0 else 0
        
        allocated_off_sum = 0
        allocated_bar_sum = 0
        
        for inc_id in incident_ids:
            off_val = int(np.floor(officer_targets[inc_id] * off_ratio))
            bar_val = int(np.floor(barricade_targets[inc_id] * bar_ratio))
            
            officers_vars[inc_id].varValue = off_val
            barricades_vars[inc_id].varValue = bar_val
            
            allocated_off_sum += off_val
            allocated_bar_sum += bar_val
            
        # Distribute remaining leftovers to highest impact hotspots
        sorted_incidents = sorted(active_incidents, key=lambda x: x['impact_score'], reverse=True)
        remaining_off = total_available_officers - allocated_off_sum
        for inc in sorted_incidents:
            if remaining_off <= 0:
                break
            officers_vars[inc['id']].varValue += 1
            remaining_off -= 1
            
        remaining_bar = total_available_barricades - allocated_bar_sum
        for inc in sorted_incidents:
            if remaining_bar <= 0:
                break
            barricades_vars[inc['id']].varValue += 1
            remaining_bar -= 1
    
    # Format outputs
    deployments = []
    total_officers_deployed = 0
    total_barricades_deployed = 0
    total_residual_risk = 0.0
    
    for inc in active_incidents:
        inc_id = inc['id']
        off_dep = int(officers_vars[inc_id].varValue)
        bar_dep = int(barricades_vars[inc_id].varValue)
        
        total_officers_deployed += off_dep
        total_barricades_deployed += bar_dep
        
        target_off = officer_targets[inc_id]
        off_cov = min(1.0, off_dep / target_off) if target_off > 0 else 1.0
        residual = inc['impact_score'] * (1.0 - off_cov)
        total_residual_risk += residual
        
        # Create a simple shift schedule (e.g. split into 8h shifts based on incident duration)
        # For long events, suggest rotation
        shift_duration = 8 # 8 hours
        total_shifts = max(1, int(np.ceil(inc.get('duration_min', 60.0) / 480.0)))
        
        deployments.append({
            'incident_id': inc_id,
            'junction': inc['junction'],
            'impact_score': inc['impact_score'],
            'officers_allocated': off_dep,
            'barricades_allocated': bar_dep,
            'target_officers': target_off,
            'target_barricades': barricade_targets[inc_id],
            'coverage_pct': round(off_cov * 100, 1),
            'residual_impact': round(residual, 1),
            'shifts_required': total_shifts,
            'suggested_rotation': f"{off_dep} officers per shift across {total_shifts} shifts" if total_shifts > 1 else "Single shift deployment"
        })
        
    avg_residual = total_residual_risk / len(active_incidents) if active_incidents else 0.0
    
    return {
        'status': pulp.LpStatus[status],
        'success': pulp.LpStatus[status] == "Optimal",
        'total_officers_allocated': total_officers_deployed,
        'total_barricades_allocated': total_barricades_deployed,
        'officers_available': total_available_officers,
        'barricades_available': total_available_barricades,
        'overall_safety_coverage': round((1.0 - (total_residual_risk / sum(impact_scores.values()))) * 100, 1) if sum(impact_scores.values()) > 0 else 100.0,
        'average_residual_impact': round(avg_residual, 2),
        'deployments': deployments
    }

if __name__ == "__main__":
    # Test cases
    test_incidents = [
        {'id': 'INC01', 'junction': 'MekhriCircle', 'impact_score': 8.5, 'closure_probability': 0.85, 'duration_min': 240},
        {'id': 'INC02', 'junction': 'SilkBoardJunc', 'impact_score': 6.2, 'closure_probability': 0.45, 'duration_min': 120},
        {'id': 'INC03', 'junction': 'TownhallJunction', 'impact_score': 4.1, 'closure_probability': 0.10, 'duration_min': 45},
        {'id': 'INC04', 'junction': 'HebbalFlyoverJunc', 'impact_score': 7.8, 'closure_probability': 0.90, 'duration_min': 360}
    ]
    
    # Resource surplus
    res_surplus = optimize_resources(test_incidents, 30, 50)
    print("Surplus optimization results:")
    print("Total allocated officers:", res_surplus['total_officers_allocated'])
    print("Safety coverage %:", res_surplus['overall_safety_coverage'])
    
    # Resource deficit
    res_deficit = optimize_resources(test_incidents, 5, 10)
    print("\nDeficit optimization results:")
    print("Total allocated officers:", res_deficit['total_officers_allocated'])
    print("Safety coverage %:", res_deficit['overall_safety_coverage'])
