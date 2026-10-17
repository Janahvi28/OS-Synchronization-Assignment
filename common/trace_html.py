"""
common/trace_html.py
--------------------
Shared helper used by ALL four programs.

1. TraceRecorder  - threads call .state() / .fork() whenever something changes.
                    Every call is stored as one event (number, time, who, what).
2. generate_html  - after the threads finish, the recorded events are written into
                    a single .html file as JSON. A small JavaScript player inside
                    that file replays the events step by step (animation).

So the animation is NOT hand-drawn: it is a replay of what the Python threads
really did in that run.
"""
import json
import threading
import time
import webbrowser
from pathlib import Path


class TraceRecorder:
    def __init__(self):
        self._events = []
        self._lock = threading.Lock()      # protects only the list below
        self._t0 = time.perf_counter()

    def _add(self, **kw):
        with self._lock:
            kw["n"] = len(self._events) + 1
            kw["t"] = round(time.perf_counter() - self._t0, 3)
            self._events.append(kw)

    def state(self, thread, state, msg):
        """Thread `thread` moved to `state` (e.g. R1 -> reading)."""
        self._add(kind="state", thread=thread, state=state,
                  msg=f"{thread} -> {state} ({msg})")

    def fork(self, fork, owner, msg):
        """Fork ownership changed. owner = 'P1' or None (free)."""
        who = owner if owner else "free"
        self._add(kind="fork", fork=fork, owner=owner,
                  msg=f"Fork {fork} -> {who} ({msg})")

    @property
    def events(self):
        return list(self._events)


# ---------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
 :root{--bg:#0f172a;--panel:#1e293b;--line:#334155;--txt:#e2e8f0;--mut:#94a3b8;--acc:#22d3ee}
 *{box-sizing:border-box}
 body{font-family:"Trebuchet MS",Verdana,sans-serif;background:linear-gradient(160deg,#0b1020,#1a1f3a);color:var(--txt);margin:0;min-height:100vh}
 .wrap{max-width:1150px;margin:0 auto;padding:18px}
 header{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;margin-bottom:12px;border-bottom:2px solid var(--acc);padding-bottom:8px}
 h1{margin:0;font-size:24px;letter-spacing:.5px} .sub{color:var(--mut);font-size:13px}
 .badge{background:var(--acc);color:#06222b;font-weight:700;border-radius:20px;padding:3px 12px;font-size:12px}
 .panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:14px}
 .panel h3{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:1.5px;color:var(--acc)}
 .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
 button{width:42px;height:38px;border:none;border-radius:50%;background:var(--acc);color:#06222b;font-size:17px;font-weight:700;cursor:pointer}
 button:hover{filter:brightness(1.15)} #slider{flex:1;min-width:180px;accent-color:var(--acc)} .controls label{font-size:12px;color:var(--mut)}
 .grid{display:grid;grid-template-columns:1.35fr 1fr;gap:14px} @media(max-width:850px){.grid{grid-template-columns:1fr}}
 #log{height:250px;overflow-y:auto;font:12px Consolas,monospace}
 #log div{padding:3px 6px;border-left:3px solid transparent;color:var(--mut)} #log div.cur{background:#0e3a47;border-color:var(--acc);color:#fff}
 .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:10px}
 .stat{background:#0f172a;border-radius:10px;padding:8px;text-align:center} .stat b{display:block;font-size:22px;color:var(--acc)} .stat span{font-size:11px;color:var(--mut)}
 .zones{display:grid;grid-template-columns:1fr 1.2fr 1fr;gap:10px}
 .zone{min-height:210px;border:2px dashed var(--line);border-radius:12px;padding:8px;text-align:center}
 .zone h4{margin:0 0 8px;font-size:12px;color:var(--mut);letter-spacing:1px}
 .zone.vault{border-color:var(--acc)} .zone.vault.w{border-color:#f43f5e;background:#3b1020} .zone.vault.r{background:#0e2f3a}
 .chip{display:inline-block;margin:3px;padding:7px 11px;border-radius:9px;font-weight:700;font-size:14px;color:#0b1020;transition:all .3s}
 .vtxt{font-size:13px;margin-bottom:8px;color:#fff}
 .lane{display:flex;align-items:center;margin:6px 0;font-size:12px}
 .lane span.nm{width:32px;color:var(--mut)} .lane .bar{position:relative;flex:1;height:16px;background:#0f172a;border-radius:8px;overflow:hidden}
 .seg{position:absolute;top:0;height:16px}
 .cursor{position:absolute;top:0;width:2px;height:16px;background:#fff;z-index:2}
 .leg{margin-top:8px;font-size:12px;color:var(--mut)} .leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin:0 4px 0 14px}
 pre{margin:0;font-size:12px;color:#cbd5e1;white-space:pre-wrap}
</style></head><body><div class="wrap">
<header><div><h1>__TITLE__</h1><div class="sub" id="sub"></div></div><span class="badge">Replay of a real run</span></header>
<div class="panel controls">
 <button id="bPlay" title="play/pause">&#10074;&#10074;</button><button id="bStep" title="step">&#9197;</button><button id="bReset" title="reset">&#10226;</button>
 <label>Speed <input type="range" id="speed" min="1" max="20" value="5"></label>
 <input type="range" id="slider" min="0" value="0"><span id="cnt"></span>
</div>
<div class="grid">
 <div class="panel"><h3>Live view</h3><div class="stats" id="stats"></div><div id="stage"></div></div>
 <div class="panel"><h3>Event log</h3><div id="log"></div></div>
</div>
<div class="panel"><h3>Timeline (event order)</h3><div id="tl"></div><div class="leg" id="leg"></div></div>
<div class="panel"><h3>Run summary</h3><pre id="sum"></pre></div>
</div>
<script>
const D = __DATA__;
const COL = {idle:"#64748b",waiting:"#fbbf24",reading:"#22d3ee",writing:"#f43f5e",done:"#475569",
             thinking:"#818cf8",hungry:"#fbbf24",acquiring:"#fb923c",eating:"#34d399",releasing:"#e879f9"};
const ev = D.events, N = ev.length;
let k = 0, playing = true, timer = null;
const $ = id => document.getElementById(id);
$("sub").textContent = D.subtitle + "  |  " + D.threads.length + " threads  |  " + N + " recorded events";
$("sum").textContent = JSON.stringify(D.summary, null, 2);
$("slider").max = N;

// Rebuild the world after k events (replay events 0..k-1)
function snap(k){
  const st = {}, fk = {}, c = {writes:0, reads:0, meals:{}};
  D.threads.forEach(t => {st[t] = D.initial; c.meals[t] = 0;});
  D.forks.forEach(f => fk[f] = null);
  for (let i = 0; i < k; i++){
    const e = ev[i];
    if (e.kind === "state"){
      const prev = st[e.thread];
      if (prev==="writing" && e.state==="idle") c.writes++;
      if (prev==="reading" && e.state==="idle") c.reads++;
      if (prev==="eating" && e.state==="releasing") c.meals[e.thread]++;
      st[e.thread] = e.state;
    } else fk[e.fork] = e.owner;
  }
  return {st, fk, c};
}
const stat = (n,l) => `<div class="stat"><b>${n}</b><span>${l}</span></div>`;
const chip = (t,s) => `<span class="chip" style="background:${COL[s]}">${t}</span>`;

function stageRW(st, c){
  const by = f => D.threads.filter(t => f(st[t]));
  const wait = by(s=>s==="waiting"), rd = by(s=>s==="reading"), wr = by(s=>s==="writing"), out = by(s=>s==="idle"||s==="done");
  let vcls = "zone vault", msg = "resource is FREE";
  if (wr.length){vcls += " w"; msg = "exclusive WRITE by " + wr[0];}
  else if (rd.length){vcls += " r"; msg = rd.length + " reader(s) sharing";}
  $("stats").innerHTML = stat(rd.length,"readers inside")+stat(wr.length,"writers inside")+stat(wait.length,"waiting")+stat(c.reads,"reads done")+stat(c.writes,"writes done");
  return `<div class="zones">
    <div class="zone"><h4>WAITING ROOM</h4>${wait.map(t=>chip(t,"waiting")).join("")}</div>
    <div class="${vcls}"><h4>SHARED RESOURCE</h4><div class="vtxt">${msg}</div>${rd.map(t=>chip(t,"reading")).join("")}${wr.map(t=>chip(t,"writing")).join("")}</div>
    <div class="zone"><h4>OUTSIDE</h4>${out.map(t=>chip(t,st[t])).join("")}</div></div>`;
}

function stageDP(st, fk, c){
  const cx=230, cy=210, R=150, n=D.threads.length;
  const ang = i => (-90 + i*360/n) * Math.PI/180;
  const used = D.forks.filter(f=>fk[f]).length;
  $("stats").innerHTML = stat(used+"/"+D.forks.length,"forks in use")+D.threads.map(t=>stat(c.meals[t],t+" meals")).join("");
  let s = `<svg viewBox="0 0 460 420" width="100%"><circle cx="${cx}" cy="${cy}" r="88" fill="#3b2a1a" stroke="#a16207" stroke-width="4"/>`;
  const fpos = {};
  D.forks.forEach((f,i) => { const a = ang(i)+Math.PI/n; fpos[f] = [cx+62*Math.cos(a), cy+62*Math.sin(a)]; });
  D.threads.forEach((p,i) => {
    const x = cx+R*Math.cos(ang(i)), y = cy+R*Math.sin(ang(i));
    D.forks.forEach(f => { if (fk[f]===p) s += `<line x1="${x}" y1="${y}" x2="${fpos[f][0]}" y2="${fpos[f][1]}" stroke="${COL[st[p]]}" stroke-width="3" stroke-dasharray="2 5" stroke-linecap="round"/>`; });
    s += `<rect x="${x-36}" y="${y-30}" width="72" height="60" rx="16" fill="${COL[st[p]]}"/>`+
         `<text x="${x}" y="${y-3}" text-anchor="middle" font-weight="700" font-size="16" fill="#0b1020">${p}</text>`+
         `<text x="${x}" y="${y+16}" text-anchor="middle" font-size="11" fill="#0b1020">${st[p]}</text>`;
  });
  D.forks.forEach(f => {
    const [x,y]=fpos[f], o=fk[f];
    s += `<polygon points="${x},${y-14} ${x+14},${y} ${x},${y+14} ${x-14},${y}" fill="${o?'#34d399':'#0f172a'}" stroke="#e2e8f0" stroke-width="1.5"/>`+
         `<text x="${x}" y="${y+4}" text-anchor="middle" font-size="10" font-weight="700" fill="${o?'#0b1020':'#e2e8f0'}">${f}</text>`+
         `<text x="${x}" y="${y+27}" text-anchor="middle" font-size="9" fill="#cbd5e1">${o||'free'}</text>`;
  });
  return s + "</svg>";
}

function buildTimeline(){
  let h="";
  D.threads.forEach(t => {
    const pts=[[0,D.initial]];
    ev.forEach((e,i)=>{ if(e.kind==="state"&&e.thread===t) pts.push([i+1,e.state]); });
    h += `<div class="lane"><span class="nm">${t}</span><div class="bar">`;
    pts.forEach((p,j)=>{ const end = j+1<pts.length?pts[j+1][0]:N;
      h += `<div class="seg" style="left:${p[0]/N*100}%;width:${(end-p[0])/N*100}%;background:${COL[p[1]]}" title="${p[1]}"></div>`; });
    h += `<div class="cursor"></div></div></div>`;
  });
  $("tl").innerHTML = h;
  $("leg").innerHTML = D.legend.map(s => `<i style="background:${COL[s]}"></i>${s}`).join("");
  $("log").innerHTML = ev.map((e,i)=>`<div id="e${i}">[${e.t.toFixed(3)}s] #${e.n} ${e.msg}</div>`).join("");
}

function render(){
  const {st,fk,c} = snap(k);
  $("stage").innerHTML = D.kind==="rw" ? stageRW(st,c) : stageDP(st,fk,c);
  $("slider").value = k; $("cnt").textContent = k+" / "+N;
  document.querySelectorAll(".cursor").forEach(x => x.style.left = (k/N*100)+"%");
  document.querySelectorAll("#log .cur").forEach(d => d.classList.remove("cur"));
  if (k>0){ const d=$("e"+(k-1)); d.classList.add("cur"); d.scrollIntoView({block:"nearest"}); }
}
function tick(){ if(k<N){k++;render();} else stop(); }
function play(){ playing=true; $("bPlay").innerHTML="&#10074;&#10074;"; clearInterval(timer); timer=setInterval(tick,1000/$("speed").value); }
function stop(){ playing=false; $("bPlay").innerHTML="&#9654;"; clearInterval(timer); }
$("bPlay").onclick = () => { if(playing) stop(); else { if(k>=N) k=0; play(); } };
$("bStep").onclick = () => { stop(); tick(); };
$("bReset").onclick = () => { stop(); k=0; render(); };
$("speed").oninput = () => { if(playing) play(); };
$("slider").oninput = e => { k=+e.target.value; render(); };
buildTimeline(); render(); play();
</script></body></html>
"""


def print_summary(title, summary):
    """Pretty terminal report (instead of dumping a raw dict)."""
    width = 62
    print("+" + "-" * width + "+")
    print("| " + title.center(width - 2) + " |")
    print("+" + "-" * width + "+")
    for key, val in summary.items():
        print("| " + f"{key.replace('_', ' '):<32}: {str(val):<{width - 36}}" + " |")
    print("+" + "-" * width + "+")


def generate_html(path, *, title, subtitle, kind, threads, forks, initial, legend,
                  events, summary, open_browser=True):
    """Write the replay page. kind is 'rw' (readers-writers) or 'dp' (dining philosophers)."""
    data = dict(subtitle=subtitle, kind=kind, threads=threads, forks=forks, initial=initial,
                legend=legend, events=events, summary=summary)
    page = HTML.replace("__TITLE__", title).replace("__DATA__", json.dumps(data))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(f"HTML simulation written to: {path.resolve()}")
    if open_browser:
        webbrowser.open(path.resolve().as_uri())     # this is what "jumps" into the browser
    return path
