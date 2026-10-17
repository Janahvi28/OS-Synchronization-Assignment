"""
Readers-Writers problem using a MONITOR.

Python has no 'monitor' keyword, so a monitor is built as a class that owns
  - the shared state (active_readers, writer_active, ticket counters)
  - ONE threading.Condition (= a lock + wait()/notify_all())
and every public method runs inside that lock.

Fairness: each arriving thread takes a ticket and may only enter when its ticket
is being served, so a waiting writer cannot be overtaken by later readers.

Run:  python readers_writers/rw_monitor.py [--readers 4 --writers 2 --ops 3 --seed 1 --no-open]
"""
import argparse
import random
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.trace_html import TraceRecorder, generate_html, print_summary      # noqa: E402
from common.shared_resource import SharedResource               # noqa: E402

rec = TraceRecorder()
res = SharedResource()


class ReadWriteMonitor:
    def __init__(self):
        self.cond = threading.Condition()       # the monitor lock + condition variable
        self.active_readers = 0
        self.writer_active = False
        self.next_ticket = 0                    # ticket given to the next arrival
        self.now_serving = 0                    # ticket allowed to enter now

    def start_read(self, name):
        with self.cond:                         # enter monitor
            rec.state(name, "waiting", "wants to read")
            my = self.next_ticket
            self.next_ticket += 1
            while not (my == self.now_serving and not self.writer_active):
                self.cond.wait()                # releases lock, sleeps; re-check on wake-up
            self.now_serving += 1               # let the next ticket (maybe another reader) in
            self.active_readers += 1
            rec.state(name, "reading", f"active readers={self.active_readers}")
            self.cond.notify_all()

    def end_read(self, name, value):
        with self.cond:
            self.active_readers -= 1
            rec.state(name, "idle", f"read value {value}; active readers={self.active_readers}")
            if self.active_readers == 0:
                self.cond.notify_all()          # a waiting writer may proceed

    def start_write(self, name):
        with self.cond:
            rec.state(name, "waiting", "wants to write")
            my = self.next_ticket
            self.next_ticket += 1
            while not (my == self.now_serving and not self.writer_active and self.active_readers == 0):
                self.cond.wait()
            self.now_serving += 1
            self.writer_active = True
            rec.state(name, "writing", "exclusive access")

    def end_write(self, name, value):
        with self.cond:
            self.writer_active = False
            rec.state(name, "idle", f"wrote value {value}")
            self.cond.notify_all()


monitor = ReadWriteMonitor()


def reader(name, ops, rnd):
    for _ in range(ops):
        time.sleep(rnd.uniform(0.05, 0.25))
        monitor.start_read(name)
        value = res.read(rnd.uniform(0.1, 0.25))            # ---- critical section ----
        monitor.end_read(name, value)
    rec.state(name, "done", "finished all reads")


def writer(name, ops, rnd):
    for _ in range(ops):
        time.sleep(rnd.uniform(0.05, 0.25))
        monitor.start_write(name)
        value = res.write(rnd.uniform(0.1, 0.25))           # ---- critical section ----
        monitor.end_write(name, value)
    rec.state(name, "done", "finished all writes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readers", type=int, default=4)
    ap.add_argument("--writers", type=int, default=2)
    ap.add_argument("--ops", type=int, default=3)
    ap.add_argument("--seed", type=int, default=random.randrange(10**6))
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    names, threads = [], []
    for i in range(1, a.readers + 1):
        names.append(f"R{i}")
        threads.append(threading.Thread(target=reader, args=(f"R{i}", a.ops, random.Random(a.seed + i))))
    for i in range(1, a.writers + 1):
        names.append(f"W{i}")
        threads.append(threading.Thread(target=writer, args=(f"W{i}", a.ops, random.Random(a.seed + 100 + i))))

    for t in threads: t.start()
    for t in threads: t.join()

    summary = {"seed": a.seed, "readers": a.readers, "writers": a.writers,
               "final_value": res.value, "expected_value": a.writers * a.ops,
               "mutual_exclusion_violations": res.violations,
               "max_concurrent_readers": res.max_readers,
               "lost_updates": a.writers * a.ops - res.value}
    print_summary("READERS-WRITERS | MONITOR", summary)
    generate_html(ROOT / "generated_html" / "readers_writers_monitor.html",
                  title="Readers-Writers (Monitor)", subtitle="monitor-based",
                  kind="rw", threads=names, forks=[], initial="idle",
                  legend=["waiting", "reading", "writing", "idle", "done"],
                  events=rec.events, summary=summary, open_browser=not a.no_open)


if __name__ == "__main__":
    main()
