import csv

with open('00_Project_Control/PROCESSING_STATUS.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    incomplete = [row for row in reader if row.get('Status') != 'COMPLETE']
    print(f'Total incomplete rows: {len(incomplete)}')
    for r in incomplete:
        print(f"ID: {r.get('Identifier')}, Type: {r.get('Type')}, Name: {r.get('Name')}, Status: {r.get('Status')}, Notes: {r.get('Notes', '')[:60]}")
