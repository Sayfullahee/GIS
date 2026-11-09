import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding="utf-8")

url = "http://localhost:8000/openapi.json"
req = urllib.request.urlopen(url)
data = json.loads(req.read().decode("utf-8"))

print(f"Title: {data['info']['title']}")
print(f"Version: {data['info']['version']}")
print(f"Total Paths: {len(data['paths'])}")
print(f"Total Tags: {len(data.get('tags', []))}\n")

for path, methods in data["paths"].items():
    for method, spec in methods.items():
        tags = spec.get("tags", ["Untagged"])
        summary = spec.get("summary", "No summary")
        print(f"[{method.upper():4}] {path:35} | {tags[0]} | {summary}")
