"""Run test_pipeline.py and capture only summary."""
import subprocess, sys

p = subprocess.run(
    [sys.executable, "test_pipeline.py"],
    capture_output=True, text=True
)
output = p.stdout + p.stderr
# Print last 40 lines (summary section)
lines = output.strip().splitlines()
for line in lines[-40:]:
    print(line)
print("\nExit code:", p.returncode)
