# OS Synchronization Assignment

Four Python programs that solve two classic synchronization problems in two ways each.
Every program records what its threads do and then **generates an HTML page that replays the run as an animation** (it opens in your browser automatically).

| Problem | Semaphore version | Monitor version |
|---|---|---|
| Readers-Writers | `readers_writers/rw_semaphore.py` | `readers_writers/rw_monitor.py` |
| Dining Philosophers (4) | `dining_philosophers/dp_semaphore.py` | `dining_philosophers/dp_monitor.py` |

## Requirements
Python 3.8+ only. No external libraries.

## How to run
```bash
python readers_writers/rw_semaphore.py
python readers_writers/rw_monitor.py
python dining_philosophers/dp_semaphore.py
python dining_philosophers/dp_monitor.py
python run_all.py            # runs all four
```
Useful options: `--seed 42` (repeat the same random delays), `--no-open` (don't open browser),
`--readers 4 --writers 2 --ops 3` (readers-writers), `--meals 3` (philosophers).
Deadlock demo: `python dining_philosophers/dp_semaphore.py --no-room --timeout 10`

The HTML files are written to `generated_html/`.

## How the HTML is connected to the code
1. Threads call `rec.state(...)` / `rec.fork(...)` (in `common/trace_html.py`) each time something changes.
2. After all threads finish, `generate_html()` writes the recorded events into one `.html` file as JSON.
3. JavaScript inside that file replays the events (Start / Pause / Step / Reset / speed / slider).

## Folder layout
```
common/            trace_html.py (recorder + HTML generator), shared_resource.py (violation detector)
readers_writers/   rw_semaphore.py, rw_monitor.py
dining_philosophers/ dp_semaphore.py, dp_monitor.py
generated_html/    output pages
docs/              report, screenshots, viva questions
```
