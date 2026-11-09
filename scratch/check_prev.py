import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
lines = open(r'C:\Users\ahmad\.gemini\antigravity-ide\brain\fc70b344-d995-4c5f-9898-53a8e67da71e\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8').readlines()
for l in lines[352:]:
    obj = json.loads(l)
    tc = obj.get('tool_calls')
    if tc:
        for c in tc:
            print(f"Step {obj.get('step_index')}: {c.get('name')} -> {list(c.get('args', {}).keys())}")
            if c.get('name') in ['replace_file_content', 'write_to_file']:
                print(f"   Target: {c['args'].get('TargetFile')}")
            elif c.get('name') == 'run_command':
                print(f"   Cmd: {c['args'].get('CommandLine')[:100]}")
            elif c.get('name') == 'view_file':
                print(f"   View: {c['args'].get('AbsolutePath')}")
