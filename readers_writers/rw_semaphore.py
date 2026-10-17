"""
Readers-Writers problem using SEMAPHORES.

Semaphores used (all start at 1):
  rw_mutex : whoever holds it owns the shared data. A writer takes it alone;
             the FIRST reader takes it for the whole group of readers.
  mutex    : protects the counter read_count (how many readers are inside).
  turnstile: readers and writers pass through it one at a time, in arrival order.
             This stops a stream of readers from starving a waiting writer.

Run:  python readers_writers/rw_semaphore.py [--readers 4 --writers 2 --ops 3 --seed 1 --no-open]
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

rw_mutex = threading.Semaphore(1)
mutex = threading.Semaphore(1)
turnstile = threading.Semaphore(1)
read_count = 0


def reader(name, ops, rnd):
    global read_count
    for _ in range(ops):
        time.sleep(rnd.uniform(0.05, 0.25))                 # idle / thinking
        rec.state(name, "waiting", "wants to read")
        turnstile.acquire()                                 # wait for my turn in line
        mutex.acquire()
        read_count += 1
        if read_count == 1:
            rw_mutex.acquire()                              # first reader locks out writers
        mutex.release()
        turnstile.release()                                 # next thread in line may go

        rec.state(name, "reading", f"active readers={read_count}")
        value = res.read(rnd.uniform(0.1, 0.25))            # ---- critical section ----

        mutex.acquire()
        read_count -= 1
        rec.state(name, "idle", f"read value {value}; active readers={read_count}")
        if read_count == 0:
            rw_mutex.release()                              # last reader lets writers in
        mutex.release()
    rec.state(name, "done", "finished all reads")


def writer(name, ops, rnd):
    for _ in range(ops):
        time.sleep(rnd.uniform(0.05, 0.25))
        rec.state(name, "waiting", "wants to write")
        turnstile.acquire()
        rw_mutex.acquire()                                  # need exclusive access
        turnstile.release()

        rec.state(name, "writing", "exclusive access")
        new_value = res.write(rnd.uniform(0.1, 0.25))       # ---- critical section ----
        rec.state(name, "idle", f"wrote value {new_value}")
        rw_mutex.release()
    rec.state(name, "done", "finished all writes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readers", type=int, default=4)
    ap.add_argument("--writers", type=int, default=2)
    ap.add_argument("--ops", type=int, default=3, help="operations per thread")
    ap.add_argument("--seed", type=int, default=random.randrange(10**6))
    ap.add_argument("--no-open", action="store_true", help="do not open the browser")
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
    print_summary("READERS-WRITERS | SEMAPHORE", summary)
    generate_html(ROOT / "generated_html" / "readers_writers_semaphore.html",
                  title="Readers-Writers (Semaphore)", subtitle="semaphore-based",
                  kind="rw", threads=names, forks=[], initial="idle",
                  legend=["waiting", "reading", "writing", "idle", "done"],
                  events=rec.events, summary=summary, open_browser=not a.no_open)


if __name__ == "__main__":
    main()
