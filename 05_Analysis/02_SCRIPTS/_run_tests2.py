"""Run test_pipeline.py, write summary to file."""
import subprocess, sys, pathlib

out_path = pathlib.Path(__file__).parent / "_test_results.txt"

p = subprocess.run(
    [sys.executable, "test_pipeline.py"],
    capture_output=True, text=True,
    cwd=str(pathlib.Path(__file__).parent)
)
combined = p.stdout + p.stderr
lines = combined.strip().splitlines()
# Write full output
out_path.write_text(combined, encoding="utf-8")
# Also print summary (last 25 lines)
for line in lines[-25:]:
    print(line)
print("Exit:", p.returncode)
