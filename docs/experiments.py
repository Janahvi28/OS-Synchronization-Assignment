"""Two small experiments used in the report (Section: Testing)."""
import random, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.shared_resource import SharedResource

print("Experiment 1: 3 writers x 5 writes, NO synchronization")
for seed in range(1, 4):
    r = SharedResource(); rnd = random.Random(seed)
    def w():
        for _ in range(5): r.write(rnd.uniform(0.02, 0.06))
    ts = [threading.Thread(target=w) for _ in range(3)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print(f"  seed {seed}: final value {r.value} (expected 15), violations {r.violations}")

print("Experiment 2: semaphore philosophers WITHOUT room (timeout 6 s), 6 seeds")
dead = 0
for seed in range(1, 7):
    out = subprocess.run([sys.executable, "dining_philosophers/dp_semaphore.py", "--no-open", "--no-room",
                          "--seed", str(seed), "--timeout", "6"], capture_output=True, text=True).stdout
    d = "'deadlock': True" in out; dead += d
    print(f"  seed {seed}: {'DEADLOCK' if d else 'finished'}")
print(f"  deadlocked in {dead} of 6 runs")
