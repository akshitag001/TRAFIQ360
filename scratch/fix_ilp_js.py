#!/usr/bin/env python3
"""Fix the corrupt ILP JS fetch block in index.html"""
import os

html_path = r'c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Identify the corrupt block precisely - look for the marker text
OLD_START = "            fetch('/api/optimize', {\n                method: 'POST',\n                headers: {'Content-Type': 'application/json'},\n                        <td>${dep.junction}</td>"
OLD_END = "        }"

# Find start and end positions
start_pos = content.find(OLD_START)
if start_pos == -1:
    print("FAIL: Old block start not found")
    # Debug: find the fetch call
    idx = content.find("fetch('/api/optimize'")
    if idx >= 0:
        print(f"fetch found at {idx}:")
        print(repr(content[idx:idx+400]))
    else:
        print("No fetch('/api/optimize' found at all")
    exit(1)

# Find the closing "        }" after the start
end_pos = content.find("\n        }", start_pos) 
if end_pos == -1:
    print("FAIL: Old block end not found")
    exit(1)

# Include the closing brace
end_pos = end_pos + len("\n        }")
old_block = content[start_pos:end_pos]
print(f"Found old block ({len(old_block)} chars):")
print(repr(old_block[:200]))

# Build new block
new_block = (
    "            fetch('/api/optimize', {\n"
    "                method: 'POST',\n"
    "                headers: {'Content-Type': 'application/json'},\n"
    "                body: JSON.stringify(payload)\n"
    "            })\n"
    "            .then(function(res) { return res.json(); })\n"
    "            .then(function(data) {\n"
    "                if (data.status === 'infeasible') {\n"
    "                    banner.style.display = 'block';\n"
    "                    var m = data.coverage_warning ? data.coverage_warning.match(/(\\d+)/) : null;\n"
    "                    document.getElementById('res-min-required').textContent = m ? m[1] : '?';\n"
    "                    tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:var(--red);padding:10px;\">No feasible allocation — add more officers.</td></tr>';\n"
    "                    coverageMeter.style.display = 'none';\n"
    "                    document.getElementById('res-coverage').textContent = 'N/A';\n"
    "                    clearILPJunctionMarkers();\n"
    "                    return;\n"
    "                }\n"
    "                banner.style.display = 'none';\n"
    "                var deps = data.junction_deployments || [];\n"
    "                if (deps.length === 0) {\n"
    "                    tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:var(--text-muted);padding:10px;\">No junctions found for this corridor.</td></tr>';\n"
    "                } else {\n"
    "                    var pcFn = function(p) {\n"
    "                        if (p === 'HIGH')   return '<span class=\"chip chip-red\">HIGH</span>';\n"
    "                        if (p === 'MEDIUM') return '<span class=\"chip chip-amber\">MEDIUM</span>';\n"
    "                        return '<span class=\"chip chip-green\">LOW</span>';\n"
    "                    };\n"
    "                    tbody.innerHTML = deps.map(function(d) {\n"
    "                        return '<tr>' +\n"
    "                            '<td style=\"font-weight:600;\">' + d.junction_name + '</td>' +\n"
    "                            '<td style=\"text-align:center;\">\U0001f46e ' + d.officers + '</td>' +\n"
    "                            '<td style=\"text-align:center;\">\U0001f6a7 ' + d.barricades + '</td>' +\n"
    "                            '<td>' + pcFn(d.priority) + '</td>' +\n"
    "                        '</tr>';\n"
    "                    }).join('');\n"
    "                }\n"
    "                var covered = deps.filter(function(d) { return d.officers >= 1; }).length;\n"
    "                var total = deps.length;\n"
    "                var pct = total > 0 ? Math.round((covered / total) * 100) : 0;\n"
    "                coverageMeter.style.display = 'block';\n"
    "                document.getElementById('res-coverage-label').textContent = covered + ' of ' + total + ' junctions at minimum coverage';\n"
    "                document.getElementById('res-coverage-fill').style.width = pct + '%';\n"
    "                var objVal = typeof data.objective_value === 'number' ? data.objective_value.toFixed(1) : '\u2014';\n"
    "                document.getElementById('res-coverage').textContent = objVal;\n"
    "                updateILPJunctionMarkers(deps);\n"
    "            })\n"
    "            .catch(function(err) {\n"
    "                console.error('ILP optimize error:', err);\n"
    "                tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:var(--red);padding:10px;\">Solver error.</td></tr>';\n"
    "            });\n"
    "        }\n"
    "\n"
    "        function clearILPJunctionMarkers() {\n"
    "            Object.values(ilpJunctionMarkers).forEach(function(m) { if (map) map.removeLayer(m); });\n"
    "            ilpJunctionMarkers = {};\n"
    "        }\n"
    "\n"
    "        function updateILPJunctionMarkers(deployments) {\n"
    "            if (!map) return;\n"
    "            clearILPJunctionMarkers();\n"
    "            var priorityColor = { HIGH: '#b91c1c', MEDIUM: '#b45309', LOW: '#15803d' };\n"
    "            deployments.forEach(function(d) {\n"
    "                if (!d.lat || !d.lon) return;\n"
    "                var color  = priorityColor[d.priority] || '#64748b';\n"
    "                var radius = Math.min(22, 6 + d.officers * 3);\n"
    "                var m = L.circleMarker([d.lat, d.lon], {\n"
    "                    radius: radius, color: color, fillColor: color, fillOpacity: 0.25, weight: 2.5\n"
    "                }).addTo(map);\n"
    "                m.bindTooltip(\n"
    "                    '<strong>' + d.junction_name + '</strong><br>' +\n"
    "                    '\U0001f46e Officers: ' + d.officers + '<br>' +\n"
    "                    '\U0001f6a7 Barricades: ' + d.barricades + '<br>' +\n"
    "                    'Priority: <strong>' + d.priority + '</strong>',\n"
    "                    { direction: 'top' }\n"
    "                );\n"
    "                ilpJunctionMarkers[d.junction_name] = m;\n"
    "            });\n"
    "        }\n"
    "\n"
    "        function drawAlternateGridLines(coords, secondaryImpact) {\n"
    "            diversionPolylines.forEach(function(p) { map.removeLayer(p); });\n"
    "            diversionPolylines = [];\n"
    "            var flowClass = 'animated-flow';\n"
    "            var flowColor = '#d97706';\n"
    "            if (secondaryImpact >= 7.0) { flowClass = 'animated-flow-congested'; flowColor = '#b91c1c'; }\n"
    "            else if (secondaryImpact < 4.0) { flowClass = 'animated-flow-fast'; flowColor = '#15803d'; }\n"
    "            var p = L.polyline(coords, {\n"
    "                color: flowColor, weight: 4, opacity: 0.85, className: flowClass\n"
    "            }).addTo(map);\n"
    "            diversionPolylines.push(p);\n"
    "        }"
)

new_content = content[:start_pos] + new_block + content[end_pos:]
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f"SUCCESS: Replaced {len(old_block)} chars with {len(new_block)} chars")
print("File saved successfully")
