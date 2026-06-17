import re

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# find all api strings starting with /api/
# look for /api/ followed by word characters, hyphens, slashes, or variables
matches = re.findall(r'[\'`"]/api/[^\'`" ]+[\'`"]', content)
print("Thorough API Endpoints in index.html:")
for m in sorted(list(set(matches))):
    print(m)
