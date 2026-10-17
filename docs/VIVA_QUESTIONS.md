# Viva Questions and Answers

Tip: answer in your own words. Open the code while practising so every answer is tied to a real line.

## A. General / technology
**1. What technology did you use?**
Python 3 with the standard `threading` module (Thread, Semaphore, Lock, Condition). The animation is plain HTML + CSS + JavaScript, with SVG for the table. No external libraries.

**2. Why Python threads and not processes?**
The problem is about threads sharing memory and needing coordination. Threads share variables directly, which is exactly where race conditions appear. (Python's GIL does not remove races, because a thread can be switched out between "read value" and "write value".)

**3. What is a race condition? Did you show one?**
The result depends on thread timing. In `SharedResource.write()` I split the update into read, sleep, write. With no locking, 3 writers x 5 writes gave a final value of 5 instead of 15 (lost updates).

**4. What is a critical section?**
The code that touches shared data. Here: `res.read()` and `res.write()` in the Readers-Writers programs, and the eating step in the philosophers programs.

**5. What does your program output?**
A summary in the terminal (final value, violations, meals eaten, deadlock yes/no) and an HTML file in `generated_html/` that opens in the browser.

## B. HTML connection
**6. How is the HTML connected to the code?**
Threads call `rec.state()` / `rec.fork()` whenever something changes (class `TraceRecorder` in `common/trace_html.py`). After the threads finish, `generate_html()` puts the event list into an HTML template as JSON. JavaScript in the page replays the events.

**7. Is the animation real or pre-made?**
Real. It is a replay of the events from that run. Different run, different page. `--seed` repeats the same random delays.

**8. How does the browser open automatically?**
`webbrowser.open(path.as_uri())` at the end of `generate_html()`. `--no-open` disables it.

**9. How does the JavaScript work?**
`snap(k)` rebuilds the state after k events by applying events 1..k. The Start/Pause/Step/Reset buttons and slider only change k. `render()` then redraws the stage, log highlight and timeline cursor.

**10. Why is the event recorder protected by a lock?**
Several threads add events at once; the lock stops two threads corrupting the list or getting the same event number.

**11. Why do you log inside the critical section, before releasing?**
So the log order matches the real order. If a thread released first and logged later, another thread's "writing" could appear before this thread's "idle".

**12. Can the HTML run without Python?**
Yes, once generated it is a standalone file (data embedded). It cannot create new runs by itself.

## C. Readers-Writers
**13. State the problem.**
Many readers may read together; a writer needs exclusive access; no reader may read while a writer writes.

**14. Explain the semaphores.**
`rw_mutex`: owns the data (writer alone, or first reader for the whole reader group). `mutex`: protects `read_count`. `turnstile`: lets threads through in arrival order.

**15. Who releases `rw_mutex` in the reader case?**
The last reader (when `read_count` becomes 0).

**16. What is starvation here? How did you avoid it?**
In the basic solution, constant new readers keep `read_count` > 0 so a writer waits forever. The turnstile makes later readers queue behind a waiting writer.

**17. How do you know mutual exclusion worked?**
`SharedResource` counts overlaps (writer with anyone). Result: 0 violations, final value = writers x ops (6/6). Max concurrent readers was 3 or 4, proving readers do share.

**18. Monitor version: how does it work?**
`ReadWriteMonitor` holds the state and one `Condition`. `start_read/start_write` wait in a loop until their ticket is served and the conditions allow entry; `end_*` update state and `notify_all()`.

**19. Why `while` and not `if` around `wait()`?**
After waking, the state may have changed (another thread got in first), so the condition must be re-checked.

**20. What does `wait()` do exactly?**
Releases the monitor lock, puts the thread to sleep, and re-acquires the lock when notified.

**21. Why `notify_all()` and not `notify()`?**
Different threads wait for different conditions (readers vs writers, tickets). Waking one might wake the wrong one, so wake all and let each re-check.

**22. What are tickets for?**
Fairness: threads enter in arrival order, so a writer cannot be overtaken by later readers.

**23. Difference between your semaphore and monitor versions?**
Same behaviour, different tool. Semaphores: low-level, rules spread over several semaphores. Monitor: data + lock + conditions in one class.

**24. Is there any busy waiting?**
No. Blocked threads sleep on `acquire()` or `wait()`.

## D. Dining Philosophers
**25. Describe the setup.**
4 philosophers, 4 forks. Philosopher i uses fork i (left) and (i+1)%4 (right).

**26. How can deadlock happen?**
All four pick up their left fork and wait for the right one: circular wait, nobody can proceed.

**27. How does `room = 3` prevent it?**
Only 3 can compete for 4 forks, so at least one fork is free and one philosopher can get both, eat and release. No circular wait.

**28. Can three philosophers eat together?**
No. `room` limits who competes, not who eats. Max 2 eat at once, and they are non-neighbours (P0+P2 or P1+P3).

**29. Did you prove it prevents deadlock?**
Experiment: with `--no-room`, 5 of 6 seeds deadlocked within 6 s. With room=3 every run finished. Runs alone are not proof; the proof is the circular-wait argument.

**30. Why the sleep between picking the first and second fork?**
It makes the bad interleaving likely so the deadlock demo works reliably.

**31. Can starvation still occur in the semaphore version?**
In theory yes: Python does not guarantee FIFO wake-up for semaphores. In practice all meals finished.

**32. Monitor version: why no deadlock?**
A philosopher takes both forks in one atomic step or none, so there is no hold-and-wait (one of the four deadlock conditions).

**33. List the four deadlock conditions.**
Mutual exclusion, hold and wait, no pre-emption, circular wait. Semaphore version breaks circular wait; monitor version breaks hold and wait.

**34. How does the monitor avoid starvation?**
A philosopher may eat only if neither neighbour is eating and no neighbour has been hungry longer (ticket order). So the longest-waiting philosopher is never overtaken.

**35. How are fork owners shown in the animation?**
Each pickup/putdown calls `rec.fork(...)`; JavaScript tracks owner per fork and draws a line from the fork to its owner.

## E. Concept / comparison
**36. Semaphore vs monitor?**
Semaphore: integer with wait/signal, flexible, easy to misuse. Monitor: encapsulated shared data, mutual exclusion automatic, conditions via wait/notify.

**37. Mutex vs binary semaphore?**
A mutex has an owner (only the locker unlocks). A binary semaphore can be released by another thread; it is a signalling tool.

**38. Why is there no monitor keyword in Python?**
Python does not have one; a class + `Condition` gives the same behaviour.

**39. What would you change to scale to 5 philosophers?**
Change `N` to 5 (and room to N-1). The monitor logic works unchanged.

**40. What did you do with AI?**
Be honest and specific: what you asked for, what you ran and tested, what you understood and changed.

## F. Likely "show me" requests
- Run `python run_all.py` and explain each page as it opens.
- Run dp_semaphore with `--no-room --timeout 10` and show the deadlock.
- Change `--readers 6 --writers 3` and explain the new output.
- Point at the line where the HTML file is written (`generate_html`) and where the event is recorded (`rec.state`).
