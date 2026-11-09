"""Run integration test and write output to file."""
import subprocess, sys, pathlib

out = pathlib.Path(__file__).parent / "_integration_results.txt"
p   = subprocess.run(
    [sys.executable, "run_integration_test.py"],
    capture_output=True, text=True,
    cwd=str(pathlib.Path(__file__).parent),
)
combined = p.stdout + p.stderr
out.write_text(combined, encoding="utf-8")
lines = combined.strip().splitlines()
# Print last 60 lines (summary + failures)
for line in lines[-60:]:
    print(line)
print("Exit:", p.returncode)
