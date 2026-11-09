import glob
import json
import os

files = glob.glob('C:/Users/ahmad/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl')
files.sort(key=os.path.getmtime)

for f in files:
    mtime = os.path.getmtime(f)
    print("=== File:", f)
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            if '"type":"USER_INPUT"' in line:
                try:
                    obj = json.loads(line)
                    content = obj.get('content', '')
                    print("  USER:", content[:300].strip().replace('\n', ' '))
                except Exception as e:
                    print("  Error:", e)
