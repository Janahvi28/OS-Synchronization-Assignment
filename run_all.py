"""Run all four programs one after another. Each one opens its own HTML animation."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent
for script in ["readers_writers/rw_semaphore.py", "readers_writers/rw_monitor.py",
               "dining_philosophers/dp_semaphore.py", "dining_philosophers/dp_monitor.py"]:
    print("\n=== Running", script, "===")
    subprocess.run([sys.executable, str(root / script)], check=False)
