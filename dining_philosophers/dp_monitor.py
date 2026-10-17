"""
Dining Philosophers (4 philosophers, 4 forks) using a MONITOR.

TableMonitor owns: each philosopher's state, a hunger ticket, the owner of each
fork, and ONE Condition variable. A philosopher picks up BOTH forks in one
atomic step inside the monitor, or none -> no hold-and-wait -> no deadlock.
A philosopher may eat only if neither neighbour is eating AND no neighbour has
been hungry for longer (oldest-hungry-first -> no starvation).

Run:  python dining_philosophers/dp_monitor.py [--meals 3 --seed 1 --no-open]
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

N = 4
rec = TraceRecorder()


class TableMonitor:
    def __init__(self):
        self.cond = threading.Condition()
        self.state = ["thinking"] * N
        self.ticket = [None] * N                 # hunger ticket (smaller = hungry longer)
        self.next_ticket = 0
        self.owner = [None] * N                  # owner[f] = philosopher index or None
        self.conflicts = 0                       # times someone tried to take an owned fork
        self.meals = [0] * N

    def _can_eat(self, i):
        for j in ((i - 1) % N, (i + 1) % N):
            if self.state[j] == "eating":
                return False
            if self.state[j] == "hungry" and self.ticket[j] < self.ticket[i]:
                return False                     # neighbour has waited longer -> let them go first
        return True

    def pickup(self, i):
        me = f"P{i}"
        left, right = i, (i + 1) % N
        with self.cond:
            self.state[i] = "hungry"
            self.ticket[i] = self.next_ticket
            self.next_ticket += 1
            rec.state(me, "hungry", "wants to eat")
            while not self._can_eat(i):
                self.cond.wait()                 # sleep; re-check the condition when woken
            rec.state(me, "acquiring", "taking both forks atomically")
            for f in (left, right):
                if self.owner[f] is not None:
                    self.conflicts += 1
                self.owner[f] = i
                rec.fork(f"F{f}", me, "picked up")
            self.state[i] = "eating"
            self.ticket[i] = None
            rec.state(me, "eating", f"has F{left} and F{right}")

    def putdown(self, i):
        me = f"P{i}"
        with self.cond:
            rec.state(me, "releasing", "putting forks down")
            for f in (i, (i + 1) % N):
                self.owner[f] = None
                rec.fork(f"F{f}", None, "put down")
            self.state[i] = "thinking"
            self.meals[i] += 1
            rec.state(me, "thinking", "back to thinking")
            self.cond.notify_all()               # neighbours may now be able to eat


table = TableMonitor()


def philosopher(i, meals, rnd):
    for _ in range(meals):
        time.sleep(rnd.uniform(0.1, 0.4))        # thinking
        table.pickup(i)
        time.sleep(rnd.uniform(0.1, 0.3))        # eating
        table.putdown(i)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meals", type=int, default=3)
    ap.add_argument("--seed", type=int, default=random.randrange(10**6))
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    for i in range(N):
        rec.state(f"P{i}", "thinking", "starts thinking")
    ths = [threading.Thread(target=philosopher, args=(i, a.meals, random.Random(a.seed + i)), daemon=True)
           for i in range(N)]
    for t in ths: t.start()
    deadline = time.time() + a.timeout
    for t in ths:
        t.join(max(0, deadline - time.time()))
    deadlock = any(t.is_alive() for t in ths)

    summary = {"seed": a.seed, "meals_each_expected": a.meals, "meals_eaten": list(table.meals),
               "fork_conflict_violations": table.conflicts, "deadlock": deadlock}
    print_summary("DINING PHILOSOPHERS | MONITOR", summary)
    generate_html(ROOT / "generated_html" / "dining_philosophers_monitor.html",
                  title="Dining Philosophers - 4 philosophers (Monitor)", subtitle="monitor-based",
                  kind="dp", threads=[f"P{i}" for i in range(N)], forks=[f"F{i}" for i in range(N)],
                  initial="thinking", legend=["thinking", "hungry", "acquiring", "eating", "releasing"],
                  events=rec.events, summary=summary, open_browser=not a.no_open)


if __name__ == "__main__":
    main()
