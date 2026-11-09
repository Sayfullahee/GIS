import json

for brain, name in [
    ('c0eb9926-20fd-4793-97b0-25f648749b9e', 'c0eb'),
    ('c44a729b-177a-4edb-8aca-411057894fa5', 'c44a'),
    ('14aa444e-c9e7-4b39-af58-e078ce6866c4', '14aa')
]:
    path = f'C:/Users/ahmad/.gemini/antigravity-ide/brain/{brain}/.system_generated/logs/transcript.jsonl'
    lines = open(path, encoding='utf-8').readlines()
    print(f'=== {name} ({len(lines)} lines) ===')
    for i, l in enumerate(lines):
        d = json.loads(l)
        t = d.get('type')
        if t == 'USER_INPUT':
            print(f'Line {i} USER: {d.get("content", "")[:200]}')
        elif t == 'PLANNER_RESPONSE' and d.get('thinking'):
            th = d.get('thinking', '').strip().replace('\n', ' ')
            if len(th) > 150: th = th[:150] + '...'
            print(f'Line {i} THINK: {th}')
            tc = d.get('tool_calls')
            if tc:
                for c in tc:
                    print(f'       TOOL: {c.get("name")} args={list(c.get("args", {}).keys())}')
