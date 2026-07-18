/* crouch15 trainer frontend — vanilla JS, one server round-trip per decision. */
"use strict";

const $ = (id) => document.getElementById(id);
const SUITS = ["♥", "♦", "♣", "♠"]; // 0=hearts 1=diamonds 2=clubs 3=spades
const RANK_NAMES = { 1: "A", 11: "J", 12: "Q", 13: "K" };

let state = null;      // last server state
let lastBet = null;    // for one-key rebet
let quizOnDemand = false;

/* ---------------- api ---------------- */

async function api(path, body) {
  const opts = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const resp = await fetch(path, opts);
  const data = await resp.json();
  if (!resp.ok) {
    toast(data.error || `error ${resp.status}`, "err");
    return null;
  }
  return data;
}

async function refresh(data) {
  if (data === undefined) data = await api("/api/state");
  if (data === null) return;
  state = data;
  render();
  (data.feedback || []).forEach(showFeedback);
}

/* ---------------- rendering ---------------- */

function show(screen) {
  for (const id of ["start-screen", "play-screen", "stats-screen"])
    $(id).classList.toggle("hidden", id !== screen);
}

function render() {
  if (!state || state.phase === "none") { show("start-screen"); return; }
  if (state.phase === "over") { show("start-screen"); return; }
  show("play-screen");

  $("hud-round").innerHTML = `round <b>${state.round_no}</b>`;
  $("hud-shoe").innerHTML = `shoe <b>${state.shoe_no}</b>`;
  $("depth-fill").style.width =
    `${Math.round(100 * state.cards_dealt / state.cards_total)}%`;
  const net = state.net;
  $("hud-net").innerHTML =
    `net <b class="${net >= 0 ? "pos" : "neg"}">${money(net)}</b>`;
  let errors = 0, decisions = 0;
  for (const k in state.session_stats || {}) {
    errors += state.session_stats[k].errors;
    decisions += state.session_stats[k].attempts;
  }
  $("hud-errors").innerHTML = `errors <b class="${errors ? "neg" : "pos"}">${errors}</b>/${decisions}`;

  renderTable();
  renderControls();
  renderQuiz();
}

function cardEl(card) {
  const div = document.createElement("div");
  if (card === null) { div.className = "card back"; return div; }
  const [rank, suit] = card;
  div.className = "card" + (suit <= 1 ? " red" : "");
  const name = RANK_NAMES[rank] || String(rank);
  div.innerHTML = `<span class="pip">${name}</span><span class="suit">${SUITS[suit]}</span>`;
  return div;
}

function renderTable() {
  const table = state.table;
  const dealerBox = $("dealer-cards");
  const handsBox = $("hands-area");
  dealerBox.textContent = "";
  handsBox.textContent = "";
  $("dealer-total").textContent = "";
  const msg = $("message");
  msg.classList.add("hidden");

  if (!table) return;
  for (const card of table.dealer) dealerBox.appendChild(cardEl(card));
  if (table.dealer_total !== null && table.dealer_total !== undefined)
    $("dealer-total").textContent =
      table.dealer_total > 21 ? `${table.dealer_total} bust` : table.dealer_total;

  table.hands.forEach((hand) => {
    const div = document.createElement("div");
    div.className = "hand" + (hand.active ? " active" : "");
    const cards = document.createElement("div");
    cards.className = "cards";
    hand.cards.forEach((c) => cards.appendChild(cardEl(c)));
    div.appendChild(cards);
    const meta = document.createElement("div");
    meta.className = "hand-meta";
    const total = hand.total > 21 ? `${hand.total} bust` : `${hand.soft ? "soft " : ""}${hand.total}`;
    let html = `<span>${total}</span><span>${money(hand.bet)}</span>`;
    if (hand.outcome)
      html += `<span class="outcome-${hand.outcome}">${hand.outcome}` +
              ` ${money(hand.profit, true)}</span>`;
    meta.innerHTML = html;
    div.appendChild(meta);
    handsBox.appendChild(div);
  });

  if (table.settled) {
    const p = table.settled.profit;
    let text = `round ${money(p, true)}`;
    if (table.settled.player_natural) text = `blackjack! ${money(p, true)}`;
    if (table.settled.insurance_profit)
      text += ` (insurance ${money(table.settled.insurance_profit, true)})`;
    msg.textContent = text;
    msg.classList.remove("hidden");
  }
}

function chipAmounts() {
  if (!state || !state.card) return [];
  return [state.card.floor, ...state.card.jumps.map((j) => j[1])];
}

function renderChips() {
  const row = $("chip-row");
  const amounts = chipAmounts();
  const want = amounts.join(",");
  if (row.dataset.amounts === want) return;
  row.dataset.amounts = want;
  row.textContent = "";
  amounts.forEach((amount, i) => {
    const btn = document.createElement("button");
    btn.className = "chip" + (i > 0 ? " jump" : "");
    btn.dataset.bet = amount;
    btn.textContent = `$${amount}`;
    btn.onclick = () => placeBet(amount);
    row.appendChild(btn);
  });
}

function renderControls() {
  const phase = state.phase;
  $("bet-bar").classList.toggle("hidden", phase !== "bet");
  $("action-bar").classList.toggle("hidden", phase !== "action");
  $("insurance-bar").classList.toggle("hidden", phase !== "insurance");

  if (phase === "bet") {
    renderChips();
    const rebet = $("rebet-btn");
    if (lastBet !== null) {
      rebet.classList.remove("hidden");
      rebet.textContent = `Deal ${money(lastBet)} ⏎`;
    } else rebet.classList.add("hidden");
  }
  if (phase === "action") {
    const legal = new Set(state.pending.legal);
    document.querySelectorAll("#action-bar .act").forEach((btn) => {
      btn.disabled = !legal.has(btn.dataset.action);
    });
  }
}

function renderQuiz() {
  const open = state.pending_quiz !== null && state.pending_quiz !== undefined;
  if (open && $("quiz-modal").classList.contains("hidden")) {
    quizOnDemand = false;
    openQuiz({
      shuffle: "Shoe finished — what is the running count?",
      leave: "Walking away — what was the running count?",
      random: "Spot check — what is the running count?",
    }[state.pending_quiz] || "What is the running count?", state.pending_quiz !== "random");
  } else if (!open && !quizOnDemand) {
    closeModals();
  }
}

function openQuiz(reason, allowSkip = true) {
  $("modal-backdrop").classList.remove("hidden");
  $("quiz-modal").classList.remove("hidden");
  $("settings-modal").classList.add("hidden");
  $("summary-modal").classList.add("hidden");
  $("quiz-reason").textContent = reason;
  $("quiz-result").textContent = "";
  $("quiz-result").className = "";
  $("quiz-skip").classList.toggle("hidden", !allowSkip);
  $("quiz-input").value = "";
  $("quiz-input").focus();
}

function closeModals() {
  $("modal-backdrop").classList.add("hidden");
  for (const id of ["quiz-modal", "settings-modal", "summary-modal"])
    $(id).classList.add("hidden");
}

/* ---------------- feedback ---------------- */

function money(x, signed = false) {
  const sign = x < 0 ? "−" : signed ? "+" : "";
  return `${sign}$${Math.abs(x).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function toast(text, cls = "err", ms = 3600) {
  let wrap = $("toast-wrap");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "toast-wrap";
    document.body.appendChild(wrap);
  }
  const div = document.createElement("div");
  div.className = `toast ${cls}`;
  div.textContent = text;
  wrap.appendChild(div);
  setTimeout(() => div.remove(), ms);
}

function feed(text, cls) {
  const li = document.createElement("li");
  li.className = cls;
  li.innerHTML = text;
  const list = $("feed-list");
  list.prepend(li);
  while (list.children.length > 200) list.lastChild.remove();
}

function showFeedback(fb) {
  const rc = fb.rc !== undefined ? ` (RC ${signed(fb.rc)})` : "";
  if (fb.kind === "count") return; // shown in the quiz modal
  if (fb.correct === true) {
    feed(`✓ ${fb.kind} ${fb.got}`, "ok");
    return;
  }
  if (fb.correct === false) {
    let text;
    if (fb.kind === "bet") text = `Card says ${fb.expected}${rc} — you bet ${fb.got}`;
    else if (fb.kind === "play")
      text = `Basic strategy: ${fb.expected.toUpperCase()} (${fb.situation}) — you chose ${fb.got}`;
    else if (fb.kind === "insurance")
      text = `Card says ${fb.expected} insurance${rc} — you chose ${fb.got}`;
    else if (fb.kind === "leave")
      text = fb.expected === "leave"
        ? `Card says LEAVE${rc} — you kept playing`
        : `Card says STAY${rc} — you left`;
    else text = `${fb.kind}: expected ${fb.expected}, got ${fb.got}`;
    toast(text, "err");
    feed(`✗ <b>${fb.kind}</b> r${fb.round_no}: ${text}`, "err");
  }
}

function signed(x) { return x >= 0 ? `+${x}` : `−${Math.abs(x)}`; }

/* ---------------- actions ---------------- */

async function placeBet(amount) {
  const data = await api("/api/bet", { amount });
  if (data) { lastBet = amount; await refresh(data); }
}

async function doAction(action) {
  if (state.phase !== "action" || !state.pending.legal.includes(action)) return;
  await refresh(await api("/api/action", { action }));
}

async function doInsurance(take) {
  if (state.phase !== "insurance") return;
  await refresh(await api("/api/insurance", { take }));
}

async function submitQuiz() {
  const raw = $("quiz-input").value.trim();
  if (raw === "") return;
  const data = await api("/api/count", { rc: parseInt(raw, 10), on_demand: quizOnDemand });
  if (!data) return;
  const fb = (data.feedback || []).find((f) => f.kind === "count");
  const out = $("quiz-result");
  if (fb.correct) {
    out.textContent = `✓ correct: RC ${signed(parseInt(fb.expected, 10))}`;
    out.className = "ok";
    feed(`✓ count check: ${fb.got}`, "ok");
  } else {
    out.textContent =
      `✗ true RC ${signed(parseInt(fb.expected, 10))} (you said ${fb.got}, off by ${signed(fb.delta)})`;
    out.className = "err";
    feed(`✗ <b>count</b>: true ${signed(parseInt(fb.expected, 10))}, said ${fb.got}`, "err");
  }
  state = data;
  const wasOnDemand = quizOnDemand;
  setTimeout(() => {
    quizOnDemand = false;
    closeModals();
    if (!wasOnDemand) refresh(); // quiz resolution may have reshuffled
    else render();
  }, 1400);
}

async function endSession() {
  const summary = await api("/api/session/end", {});
  if (!summary) return;
  state = { phase: "none" };
  renderSummary(summary);
  $("modal-backdrop").classList.remove("hidden");
  $("summary-modal").classList.remove("hidden");
}

function renderSummary(s) {
  const acc = (row) => row.attempts
    ? `${(100 * (row.attempts - row.errors) / row.attempts).toFixed(1)}%` : "—";
  let html = `<table><tr><th>decisions</th><th class="num">attempts</th>` +
    `<th class="num">errors</th><th class="num">accuracy</th></tr>`;
  for (const kind in s.by_kind) {
    const row = s.by_kind[kind];
    html += `<tr><td>${kind}</td><td class="num">${row.attempts}</td>` +
      `<td class="num">${row.errors}</td><td class="num">${acc(row)}</td></tr>`;
  }
  html += `</table>`;
  const cc = s.count_checks;
  html += `<p class="dim">count checks: ${cc.n} (${cc.exact} exact` +
    (cc.n ? `, mean |off| ${cc.mean_abs_delta.toFixed(2)}` : "") + `)</p>`;
  html += `<p>rounds <b>${s.rounds}</b> · shoes <b>${s.shoes}</b> · net ` +
    `<b class="${s.net >= 0 ? "pos" : "neg"}">${money(s.net, true)}</b> · ` +
    `${Math.round(s.duration_s / 60)} min · seed ${s.seed}</p>`;
  if (s.errors.length) {
    html += `<h3 style="margin-top:12px">mistakes</h3><table>` +
      `<tr><th>round</th><th>kind</th><th>expected</th><th>got</th></tr>`;
    for (const e of s.errors.slice(0, 30))
      html += `<tr><td class="num">${e.round}</td><td>${e.kind}</td>` +
        `<td>${e.expected}</td><td>${e.got}</td></tr>`;
    html += `</table>`;
  }
  $("summary-body").innerHTML = html;
}

/* ---------------- stats screen ---------------- */

async function showStats() {
  const s = await api("/api/stats");
  if (!s) return;
  show("stats-screen");
  location.hash = "stats";
  const rate = s.decisions ? (100 * s.errors / s.decisions).toFixed(2) + "%" : "—";
  let html = `<div class="tiles">` +
    tile(s.sessions, "sessions") + tile(s.rounds, "rounds") +
    tile(s.decisions, "decisions") + tile(rate, "error rate") +
    tile(money(s.net, true), "net", s.net >= 0 ? "pos" : "neg") +
    tile(money(s.wagered), "wagered") + `</div>`;

  html += `<div class="chart-block"><h3>accuracy by decision type</h3>`;
  for (const row of s.by_kind) {
    const pct = row.attempts ? 100 * (row.attempts - row.errors) / row.attempts : 0;
    html += `<div class="hbar-row"><span>${row.kind}</span>` +
      `<span class="hbar-track"><span class="hbar-fill" style="width:${pct}%"></span></span>` +
      `<span class="hbar-val">${pct.toFixed(1)}% · n=${row.attempts}</span></div>`;
  }
  html += `</div>`;

  if (s.count_deltas.length) {
    const max = Math.max(...s.count_deltas.map((d) => d.n));
    html += `<div class="chart-block"><h3>count-check error distribution</h3>` +
      `<p class="sub">how far off the claimed running count was (0 = exact)</p>` +
      `<div class="vbars-wrap"><div class="vbars">`;
    for (const d of s.count_deltas)
      html += `<div class="vbar${d.delta === 0 ? " zero" : ""}" ` +
        `style="height:${Math.max(4, 100 * d.n / max)}%">` +
        `<span class="lbl">${d.n}</span><span class="x">${signed(d.delta)}</span></div>`;
    html += `</div></div></div>`;
  }

  if (s.play_mistakes.length) {
    html += `<div class="chart-block"><h3>most-missed plays</h3><table>` +
      `<tr><th>situation</th><th>correct</th><th>you chose</th><th class="num">times</th></tr>`;
    for (const m of s.play_mistakes)
      html += `<tr><td>${m.situation}</td><td>${m.expected}</td>` +
        `<td>${m.got}</td><td class="num">${m.n}</td></tr>`;
    html += `</table></div>`;
  }

  if (s.bet_mistakes.length) {
    html += `<div class="chart-block"><h3>bet-sizing mistakes</h3><table>` +
      `<tr><th>card says</th><th>you bet</th><th class="num">times</th></tr>`;
    for (const m of s.bet_mistakes)
      html += `<tr><td>${m.expected}</td><td>${m.got}</td><td class="num">${m.n}</td></tr>`;
    html += `</table></div>`;
  }

  if (s.recent_sessions.length) {
    html += `<div class="chart-block"><h3>recent sessions</h3><table>` +
      `<tr><th>date</th><th class="num">rounds</th><th class="num">net</th>` +
      `<th class="num">errors</th><th class="num">error rate</th></tr>`;
    for (const r of s.recent_sessions) {
      const when = new Date(r.started_at * 1000).toLocaleString();
      const erate = r.decisions ? (100 * r.errors / r.decisions).toFixed(1) + "%" : "—";
      html += `<tr><td>${when}</td><td class="num">${r.rounds}</td>` +
        `<td class="num ${r.net >= 0 ? "pos" : "neg"}">${money(r.net, true)}</td>` +
        `<td class="num">${r.errors}</td><td class="num">${erate}</td></tr>`;
    }
    html += `</table></div>`;
  }
  $("stats-body").innerHTML = html;
}

function tile(v, k, cls = "") {
  return `<div class="tile"><div class="v ${cls}">${v}</div><div class="k">${k}</div></div>`;
}

/* ---------------- wiring ---------------- */

$("start-btn").onclick = async () => {
  const raw = $("seed-input").value.trim();
  const body = raw === "" ? {} : { seed: parseInt(raw, 10) };
  lastBet = null;
  $("feed-list").textContent = "";
  await refresh(await api("/api/session/new", body));
};
$("stats-btn").onclick = showStats;
$("stats-back").onclick = () => {
  location.hash = "";
  state && state.phase !== "none" ? show("play-screen") : show("start-screen");
};

$("custom-bet-btn").onclick = () => {
  const v = parseFloat($("custom-bet").value);
  if (!Number.isNaN(v)) placeBet(v);
};
$("rebet-btn").onclick = () => lastBet !== null && placeBet(lastBet);
$("leave-btn").onclick = async () => refresh(await api("/api/leave", {}));

document.querySelectorAll("#action-bar .act").forEach((btn) => {
  btn.onclick = () => doAction(btn.dataset.action);
});
$("ins-yes").onclick = () => doInsurance(true);
$("ins-no").onclick = () => doInsurance(false);

$("verify-btn").onclick = () => { quizOnDemand = true; openQuiz("Self-check — what is the running count?"); };
$("peek-btn").onclick = async () => {
  const data = await api("/api/peek", {});
  if (data) { toast(`RC ${signed(data.peek_rc)}`, "info", 1800); state = data; render(); }
};
$("quiz-submit").onclick = submitQuiz;
$("quiz-skip").onclick = async () => {
  if (quizOnDemand) { quizOnDemand = false; closeModals(); render(); return; }
  quizOnDemand = false;
  await refresh(await api("/api/quiz/skip", {}));
};
$("quiz-input").addEventListener("keydown", (e) => { if (e.key === "Enter") submitQuiz(); });

$("settings-btn").onclick = () => {
  $("modal-backdrop").classList.remove("hidden");
  $("settings-modal").classList.remove("hidden");
  $("cfg-quiz-shuffle").checked = state.config.quiz_on_shuffle;
  $("cfg-quiz-mean").value = state.config.random_quiz_mean_rounds;
  $("cfg-reveal").checked = state.config.reveal_on_error;
  $("cfg-score-leave").checked = state.config.score_leave;
};
$("settings-close").onclick = async () => {
  await api("/api/config", {
    quiz_on_shuffle: $("cfg-quiz-shuffle").checked,
    random_quiz_mean_rounds: parseInt($("cfg-quiz-mean").value, 10) || 0,
    reveal_on_error: $("cfg-reveal").checked,
    score_leave: $("cfg-score-leave").checked,
  });
  closeModals();
  await refresh();
};
$("end-btn").onclick = endSession;
$("summary-close").onclick = () => { closeModals(); render(); };

document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (!state || state.phase === "none") return;
  if (!$("modal-backdrop").classList.contains("hidden")) return;
  const key = e.key.toLowerCase();
  if (state.phase === "bet" && !state.pending_quiz) {
    const amounts = chipAmounts();
    const idx = "123456789".indexOf(key);
    if (idx >= 0 && idx < amounts.length) placeBet(amounts[idx]);
    else if (key === "enter" && lastBet !== null) placeBet(lastBet);
    else if (key === "l") $("leave-btn").click();
  } else if (state.phase === "action") {
    if (key === "h") doAction("hit");
    else if (key === "s") doAction("stand");
    else if (key === "d") doAction("double");
    else if (key === "p") doAction("split");
  } else if (state.phase === "insurance") {
    if (key === "y") doInsurance(true);
    else if (key === "n") doInsurance(false);
  }
  if (key === "c") $("verify-btn").click();
  else if (key === "k") $("peek-btn").click();
});

refresh().then(() => { if (location.hash === "#stats") showStats(); });
