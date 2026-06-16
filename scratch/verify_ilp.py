content = open('index.html', encoding='utf-8').read()
checks = [
    ('Infeasible banner HTML', 'res-infeasible-banner'),
    ('Coverage meter HTML', 'res-coverage-meter'),
    ('Coverage fill bar', 'res-coverage-fill'),
    ('Coverage label', 'res-coverage-label'),
    ('Min required span', 'res-min-required'),
    ('Officer slider 1-50', 'min="1" max="50"'),
    ('Barricade slider', 'res-bar-slider'),
    ('initResourceSliders fn', 'function initResourceSliders'),
    ('initResourceSliders called', 'initResourceSliders();'),
    ('runILPOptimize fn', 'function runILPOptimize'),
    ('recalcResourceOptimization fn', 'function recalcResourceOptimization'),
    ('clearILPJunctionMarkers fn', 'function clearILPJunctionMarkers'),
    ('updateILPJunctionMarkers fn', 'function updateILPJunctionMarkers'),
    ('drawAlternateGridLines fn', 'function drawAlternateGridLines'),
    ('fetch with body payload', 'body: JSON.stringify(payload)'),
    ('Infeasible check in JS', "data.status === 'infeasible'"),
    ('4-col table', 'colspan="4"'),
    ('Table header Junction', '<th>Junction</th>'),
    ('Table header Officers', '<th>Officers</th>'),
    ('Table header Barricades', '<th>Barricades</th>'),
    ('Table header Priority', '<th>Priority</th>'),
    ('Debounce 300ms', 'setTimeout(runILPOptimize, 300)'),
    ('Map marker fillOpacity', 'fillOpacity: 0.25'),
    ('Map marker weight 2.5', 'weight: 2.5'),
]
all_ok = True
for label, token in checks:
    found = token in content
    status = 'OK' if found else 'MISSING'
    if not found:
        all_ok = False
    print(f'  [{status}] {label}')
print()
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')
