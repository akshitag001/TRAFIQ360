import re
import os

with open('server.py', encoding='utf-8') as f:
    content = f.read()

# Find any strings containing extensions
matches = re.findall(r'[\'"][^\'"]+\.(?:json|csv|txt|xlsx|pkl|joblib|graphml|geojson)[\'"]', content)
print("File Paths/Extensions in server.py:")
for m in sorted(list(set(matches))):
    print(m)
