"""
Dining Philosophers (4 philosophers, 4 forks) using SEMAPHORES.

Philosopher i uses fork i (left) and fork (i+1)%4 (right).
  fork[i] : Semaphore(1)  -> one philosopher per fork (mutual exclusion)
  room    : Semaphore(3)  -> at most 3 philosophers may try to pick forks at once.
            With 4 philosophers and 4 forks this breaks the circular wait, so
            deadlock cannot happen. (room limits who COMPETES, not who eats.)

Run:  python dining_philosophers/dp_semaphore.py [--meals 3 --seed 1 --no-open]
      python dining_philosophers/dp_semaphore.py --no-room    # demo: deadlock (may hang until timeout)
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
forks = [threading.Semaphore(1) for _ in range(N)]
eating = [False] * N
meals_eaten = [0] * N
overlap_violations = 0
meta = threading.Lock()                     # only for the checking counters


def philosopher(i, meals, rnd, room, grab_delay):
    global overlap_violations
    me = f"P{i}"
    left, right = i, (i + 1) % N
    for _ in range(meals):
        rec.state(me, "thinking", "thinking")
        time.sleep(rnd.uniform(0.1, 0.4))

        rec.state(me, "hungry", "wants to eat")
        room.acquire()                                       # enter the room (max 3 inside)

        forks[left].acquire()
        rec.fork(f"F{left}", me, "picked up left fork")
        rec.state(me, "acquiring", f"holds F{left}, wants F{right}")
        time.sleep(grab_delay)                               # makes the dangerous interleaving likely
        forks[right].acquire()
        rec.fork(f"F{right}", me, "picked up right fork")

        with meta:                                           # check: no neighbour is eating
            if eating[(i - 1) % N] or eating[(i + 1) % N]:
                overlap_violations += 1
            eating[i] = True
        rec.state(me, "eating", f"has F{left} and F{right}")
        time.sleep(rnd.uniform(0.1, 0.3))
        with meta:
            eating[i] = False
            meals_eaten[i] += 1

        rec.state(me, "releasing", "putting both forks down")
        rec.fork(f"F{left}", None, "put down")
        forks[left].release()
        rec.fork(f"F{right}", None, "put down")
        forks[right].release()
        room.release()                                       # leave the room
    rec.state(me, "thinking", "finished all meals")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meals", type=int, default=3)
    ap.add_argument("--seed", type=int, default=random.randrange(10**6))
    ap.add_argument("--no-room", action="store_true", help="remove the room semaphore (deadlock demo)")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds before declaring deadlock")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    room = threading.Semaphore(N if a.no_room else N - 1)
    grab_delay = 0.15
    ths = [threading.Thread(target=philosopher, args=(i, a.meals, random.Random(a.seed + i), room, grab_delay),
                            daemon=True) for i in range(N)]
    for t in ths: t.start()
    deadline = time.time() + a.timeout
    for t in ths:
        t.join(max(0, deadline - time.time()))
    deadlock = any(t.is_alive() for t in ths)

    summary = {"seed": a.seed, "room_limit": N if a.no_room else N - 1,
               "meals_each_expected": a.meals, "meals_eaten": list(meals_eaten),
               "neighbour_overlap_violations": overlap_violations, "deadlock": deadlock}
    print_summary("DINING PHILOSOPHERS | SEMAPHORE", summary)
    if deadlock:
        print("DEADLOCK: every philosopher is holding one fork and waiting for the next.")
    generate_html(ROOT / "generated_html" / "dining_philosophers_semaphore.html",
                  title="Dining Philosophers - 4 philosophers (Semaphore)", subtitle="semaphore-based",
                  kind="dp", threads=[f"P{i}" for i in range(N)], forks=[f"F{i}" for i in range(N)],
                  initial="thinking", legend=["thinking", "hungry", "acquiring", "eating", "releasing"],
                  events=rec.events, summary=summary, open_browser=not a.no_open)


if __name__ == "__main__":
    main()
