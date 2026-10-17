const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell,
        WidthType, ShadingType, AlignmentType, LevelFormat, BorderStyle, PageBreak, Footer, PageNumber } = require("docx");

const term = JSON.parse(fs.readFileSync("terminal.json", "utf8"));
const F = "Calibri";
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 300 }, ...o, children: [new TextRun({ text: t, font: F, size: 22 })] });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 140 }, children: [new TextRun({ text: t, font: F, bold: true, size: 30, color: "1F3864" })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 }, children: [new TextRun({ text: t, font: F, bold: true, size: 25, color: "2E5597" })] });
const B = t => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: t, font: F, size: 22 })] });
const C = t => new Paragraph({ spacing: { after: 0 }, shading: { type: ShadingType.CLEAR, fill: "F2F2F2" }, children: [new TextRun({ text: t, font: "Consolas", size: 18 })] });
const cap = t => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: t, font: F, italics: true, size: 20 })] });
const center = (t, size, bold = false, after = 120) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children: [new TextRun({ text: t, font: F, size, bold })] });
const img = f => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: 540, height: 470 }, altText: { title: f, description: f, name: f } })] });
const termBlock = name => term[name].split("\n").filter(Boolean).map(l => C(l.length > 110 ? l.slice(0, 110) + "..." : l));

const bd = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function table(widths, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({ children: r.map((c, ci) => new TableCell({
      borders, width: { size: widths[ci], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      shading: ri === 0 ? { type: ShadingType.CLEAR, fill: "D9E2F3" } : undefined,
      children: [new Paragraph({ children: [new TextRun({ text: c, font: F, size: 20, bold: ri === 0 || ci === 0 })] })] })) })) });
}

const kids = [
  // ---------- title page ----------
  center("NMAM INSTITUTE OF TECHNOLOGY, NITTE", 28, true, 60),
  center("Department of Information Science and Engineering", 24, false, 600),
  center("OPERATING SYSTEMS - PROGRAMMING ASSIGNMENT", 30, true, 200),
  center("Process Synchronization: Readers-Writers and Dining Philosophers", 26, false, 100),
  center("Semaphore and Monitor solutions in Python with auto-generated HTML animations", 22, false, 600),
  table([2800, 6226], [
    ["Student name", "[YOUR NAME]"], ["USN", "[YOUR USN]"], ["Course", "Operating Systems"],
    ["Submitted to", "[FACULTY NAME], [DESIGNATION]"],
    ["GitHub repository", "[PASTE YOUR GITHUB LINK HERE]"]]),
  new Paragraph({ children: [new PageBreak()] }),

  // ---------- 1 ----------
  H1("1. Aim and Problem Statement"),
  P("When several threads use the same data at the same time, the result can depend on which thread the scheduler happens to run first. This is called a race condition. Process synchronization is the set of techniques that make sure only the allowed threads enter the part of the code that touches shared data."),
  P("This assignment solves two classic synchronization problems, each in two different ways, which gives four programs:"),
  B("Readers-Writers problem using semaphores (rw_semaphore.py)"),
  B("Readers-Writers problem using a monitor (rw_monitor.py)"),
  B("Dining Philosophers problem, four philosophers and four forks, using semaphores (dp_semaphore.py)"),
  B("Dining Philosophers problem, four philosophers and four forks, using a monitor (dp_monitor.py)"),
  P("A further requirement is that running each program must open an HTML page that animates what happened. Instead of drawing a fixed animation, every program records its own events while it runs, and the page replays that record. The animation is therefore a picture of the real execution."),

  H1("2. Technology Used"),
  table([2600, 6426], [
    ["Item", "Purpose"],
    ["Python 3 (threading module)", "Threads, Semaphore, Lock and Condition. No external library is needed."],
    ["TraceRecorder class", "Collects events (number, time, thread, new state, message) in a list protected by a small lock."],
    ["SharedResource class", "A shared integer that counts rule violations, used to check mutual exclusion."],
    ["HTML, CSS, JavaScript", "One self-contained page per run. Python writes the events into the page as JSON; JavaScript replays them."],
    ["SVG (inside the page)", "Draws the round table, philosophers and forks in the Dining Philosophers animation."],
    ["Git and GitHub", "Version control and submission of the source code."]]),
  P(" "),
  H2("Project structure"),
  C("common/trace_html.py        recorder + HTML generator (shared by all four)"),
  C("common/shared_resource.py   shared value with violation detection"),
  C("readers_writers/            rw_semaphore.py, rw_monitor.py"),
  C("dining_philosophers/        dp_semaphore.py, dp_monitor.py"),
  C("generated_html/             the four animation pages are written here"),
  P(" "),
  P("Both versions of a problem use the same recorder, the same HTML generator and, for Readers-Writers, the same shared resource. So the only difference between the two versions is the synchronization mechanism, which keeps the comparison fair."),

  // ---------- 3 ----------
  H1("3. How the HTML Animation Is Connected to the Code"),
  P("The connection happens in three steps."),
  B("Recording: whenever a thread changes state (for example waiting to reading), it calls rec.state(...). In the philosopher programs a fork change calls rec.fork(...). Each call adds one event with a sequence number and a time stamp."),
  B("Generating: when all threads have finished, generate_html() converts the event list to JSON and inserts it into an HTML template. The file is saved in generated_html/ and opened with Python's webbrowser module, which is why the page appears by itself."),
  B("Replaying: the JavaScript in the page rebuilds the state of the system after event k by applying events 1 to k in order. The Start, Pause, Step and Reset buttons, the speed control and the slider only change k, and the drawing is refreshed from the rebuilt state."),
  P("The page contains the animated stage, the event log, a timeline with one coloured lane per thread, and the run summary printed by the program. Because threads are scheduled differently on every run, each run produces a different page. The --seed option fixes the random delays so a run can be repeated."),

  // ---------- 4 ----------
  H1("4. Readers-Writers using Semaphores"),
  P("Many readers may read the shared value together, but a writer must be alone. The program uses three binary semaphores, all starting at 1:"),
  B("rw_mutex: whoever holds it owns the data. A writer takes it for itself. The first reader takes it on behalf of all readers, and the last reader gives it back."),
  B("mutex: protects the counter read_count, which says how many readers are inside."),
  B("turnstile: every reader and writer passes through it in arrival order before asking for rw_mutex."),
  H2("Why the turnstile is needed"),
  P("Without it, a steady stream of new readers keeps read_count above zero and a waiting writer may never get rw_mutex (writer starvation). With the turnstile, a writer that is waiting for rw_mutex is still holding the turnstile, so later readers queue behind it. Threads are served roughly in arrival order."),
  H2("Checking correctness"),
  P("A write in SharedResource is split into three steps: read the value, sleep for a short random time, write value + 1. If two writers ever overlap, one update is lost. The class also counts every overlap between a writer and any other thread. At the end the program prints the final value, the expected value (writers x operations) and the number of violations."),

  H1("5. Readers-Writers using a Monitor"),
  P("Python has no monitor keyword, so the monitor is a class (ReadWriteMonitor) that keeps the shared state and one threading.Condition. Every method runs inside the condition's lock, so only one thread executes monitor code at a time. The four methods are start_read, end_read, start_write and end_write."),
  P("The state is: active_readers, writer_active, next_ticket and now_serving. An arriving thread takes a ticket. A reader may enter when its ticket is being served and no writer is active. A writer may enter when its ticket is being served, no writer is active and active_readers is zero. If the condition is false the thread calls wait(), which releases the lock and sleeps."),
  P("The condition is tested in a while loop, not an if. After waking up, another thread may have changed the state, so the thread must check again. The tickets give the same fairness as the turnstile: nobody can overtake a waiting writer."),
  P("Compared to the semaphore version, all the entry and exit rules are in one class and there are no separate counters and semaphores to keep in step."),

  // ---------- 6 ----------
  H1("6. Dining Philosophers (4) using Semaphores"),
  P("Four philosophers sit around a table with four forks. Philosopher i needs fork i (left) and fork (i+1) mod 4 (right). Each fork is a semaphore initialised to 1. A fifth semaphore, room, is initialised to 3."),
  P("Deadlock happens if all four philosophers pick up their left fork and then wait for the right one. Each holds one fork and waits for a fork held by the neighbour, which is a circular wait. Because only three philosophers can be in the room at once, at least one fork is always free and one of the three can get both forks, eat and release them. So the circular wait can never form."),
  P("room limits how many philosophers compete for forks, not how many eat. With four forks at most two philosophers can eat at the same time, and they must not be neighbours (P0 and P2, or P1 and P3)."),
  P("A short sleep is added between taking the first and second fork. It makes the dangerous timing very likely, so the deadlock test in Section 9 shows up quickly. Starvation is not completely ruled out here, because Python does not promise that waiting threads are woken in first-come order."),

  H1("7. Dining Philosophers (4) using a Monitor"),
  P("TableMonitor keeps the state of each philosopher (thinking, hungry or eating), a hunger ticket, the owner of each fork and one condition variable. A philosopher calls pickup(i). The monitor marks him hungry, gives him a ticket and makes him wait until two things are true: neither neighbour is eating, and no neighbour has been hungry for longer. When both are true he takes both forks in a single step."),
  P("Since a philosopher takes either both forks or none, nobody ever holds one fork while waiting for another. Hold-and-wait is one of the four conditions for deadlock, so deadlock is impossible. The oldest-hungry-first rule also prevents starvation, because a hungry philosopher can only be delayed by neighbours who are already eating or who waited longer, and both of those finish in finite time. putdown(i) frees the two forks, sets the state to thinking and calls notify_all()."),
  P("The monitor knows who owns every fork, so it reports ownership directly to the recorder, and that is what the animation draws."),

  // ---------- 8 ----------
  H1("8. How to Run"),
  C("python readers_writers/rw_semaphore.py"),
  C("python readers_writers/rw_monitor.py"),
  C("python dining_philosophers/dp_semaphore.py"),
  C("python dining_philosophers/dp_monitor.py"),
  P(" "),
  P("Each command prints a summary and then opens its HTML page. Options: --seed N, --no-open, --readers/--writers/--ops, --meals. All four can be started with python run_all.py."),

  // ---------- 9 ----------
  H1("9. Testing and Results"),
  H2("Race condition (no synchronization)"),
  P("Three writer threads each made five writes with no locking at all. The expected final value is 15. In three runs the final value was 5 every time, and the violation counter showed 13, 14 and 14. Most increments were lost, which shows why synchronization is needed."),
  H2("Mutual exclusion with synchronization"),
  P("With the default settings (4 readers, 2 writers, 3 operations each) both Readers-Writers programs finished with 0 violations and a final value of 6 out of 6. Up to 3 readers (semaphore run) and 4 readers (monitor run) were inside together, which confirms that readers really do share the resource. In Dining Philosophers, all four philosophers ate all three meals with 0 neighbour overlaps (semaphore) and 0 fork conflicts (monitor)."),
  H2("Deadlock test"),
  P("To confirm that room is what prevents deadlock, the semaphore program was run with room set to 4 (the --no-room option) and a 6-second limit, using six different seeds. It deadlocked in 5 of the 6 runs, with every philosopher holding one fork. The same program with room = 3 finished in every run I tried. A few successful runs can never prove that a program is deadlock-free, so the real argument is the reasoning given in Section 6."),
  H2("Starvation"),
  P("Starvation was handled by the turnstile (semaphore Readers-Writers), by tickets (monitor Readers-Writers) and by the oldest-hungry-first rule (monitor philosophers). The semaphore philosophers program is the one case without a strict guarantee, because the order in which Python wakes waiting threads is not specified. In all my runs every philosopher finished all meals."),

  H1("10. Semaphore versus Monitor"),
  table([1800, 3600, 3626], [
    ["Point", "Semaphore", "Monitor"],
    ["Structure", "Separate semaphores plus code spread over the threads", "Data, lock and conditions together in one class"],
    ["Waiting", "Thread blocks on acquire()", "Thread waits on a condition and re-checks it"],
    ["Risk of mistakes", "A misplaced acquire/release can break the program silently", "Rules are in one place, easier to check"],
    ["Level", "Low level and flexible", "Higher level"],
    ["Fairness here", "Needed an extra turnstile; none for philosophers", "Tickets and oldest-hungry-first were simple to add"],
    ["Cost", "Easy to write quickly", "Every wake-up must re-check its condition"]]),
  P(" "),
  P("Conclusion: semaphores are simple and map directly to the textbook algorithms, but the programmer must place every wait and signal correctly. A monitor puts the shared data and the rules together, so correctness and fairness are easier to reason about, at the price of re-checking conditions after every wake-up."),

  // ---------- 11 ----------
  new Paragraph({ children: [new PageBreak()] }),
  H1("11. Screenshots of the Generated Animations and Terminal Output"),
  P("The screenshots below were captured part-way through a replay. Replace them with screenshots from your own run if you prefer."),
];
const shots = [["readers_writers_semaphore", "Readers-Writers (Semaphore)", "rw_semaphore.py"],
               ["readers_writers_monitor", "Readers-Writers (Monitor)", "rw_monitor.py"],
               ["dining_philosophers_semaphore", "Dining Philosophers (Semaphore)", "dp_semaphore.py"],
               ["dining_philosophers_monitor", "Dining Philosophers (Monitor)", "dp_monitor.py"]];
shots.forEach(([f, t, s], i) => {
  kids.push(H2(`11.${i + 1} ${t}`), img(`${f}.png`), cap(`Figure ${2 * i + 1}: HTML animation generated by ${s}`),
            ...termBlock(f), cap(`Figure ${2 * i + 2}: terminal output of ${s}`));
});
kids.push(
  H1("12. AI Usage Declaration"),
  P("I used an AI assistant (Claude by Anthropic) to help plan the structure, write and explain the code and draft the report text. I ran all four programs myself, checked the outputs, ran the experiments in Section 9 and went through the code so that I can explain it. [EDIT THIS PARAGRAPH SO IT MATCHES WHAT YOU REALLY DID AND ANY RULES YOUR COLLEGE HAS.]"),
  H1("13. References"),
  P("[1] Python Software Foundation, \"threading - Thread-based parallelism,\" Python 3 documentation, https://docs.python.org/3/library/threading.html"),
  P("[2] A. Silberschatz, P. B. Galvin and G. Gagne, Operating System Concepts, Wiley."),
  P("[3] A. S. Tanenbaum and H. Bos, Modern Operating Systems, Pearson."),
  P("[4] A. B. Downey, The Little Book of Semaphores, Green Tea Press, https://greenteapress.com/wp/semaphores/"),
  P("[5] P. J. Courtois, F. Heymans and D. L. Parnas, \"Concurrent control with readers and writers,\" Communications of the ACM, vol. 14, no. 10, 1971."),
  P("[6] E. W. Dijkstra, \"Hierarchical ordering of sequential processes,\" Acta Informatica, vol. 1, 1971."),
  P("[7] C. A. R. Hoare, \"Monitors: An operating system structuring concept,\" Communications of the ACM, vol. 17, no. 10, 1974."),
  P("[8] E. G. Coffman, M. J. Elphick and A. Shoshani, \"System deadlocks,\" ACM Computing Surveys, vol. 3, no. 2, 1971."),
  H1("14. Academic Integrity Declaration"),
  P("I have run and understood the submitted programs and can explain the synchronization logic and the generated HTML simulation. I have disclosed the AI tool used. I have not submitted another student's work as my own."),
  P("Name: [YOUR NAME]          USN: [YOUR USN]          Signature: ____________          Date: ____________"));

const doc = new Document({
  styles: { default: { document: { run: { font: F, size: 22 } } } },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "OS Programming Assignment | Page ", font: F, size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: F, size: 18 })] })] }) },
    children: kids }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("OS_Assignment_Report.docx", b); console.log("ok"); });
