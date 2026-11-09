with open('c:/xampp/htdocs/GIS/00_Project_Control/VERSION_LOG.csv', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
header_count = lines[0].count(',') + 1
bad = []
for i, line in enumerate(lines[1:], 2):
    if line.strip() and (line.count(',') + 1) != header_count:
        bad.append((i, line.count(',') + 1, line[:90]))
if bad:
    for row in bad:
        print(f'  Line {row[0]}: {row[1]} fields — {row[2]}')
else:
    print('All lines have correct field count:', header_count)
print('Last 3 lines:')
for ln in lines[-3:]:
    print(' ', ln[:100])
