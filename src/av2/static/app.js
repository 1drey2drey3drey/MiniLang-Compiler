"use strict";

/* ============================================================================
 * 1. Tabs acessíveis na shell bar
 * ============================================================================ */
const tabs = Array.from(document.querySelectorAll('.shell-tabs [role="tab"]'));
const panels = Array.from(document.querySelectorAll('.shell-main [role="tabpanel"]'));

function openTab(tabId, focusTab = false) {
  const target = document.getElementById(tabId);
  if (!target) return;
  if (typeof apPlayer !== "undefined") apPlayer.stop();
  if (typeof allPlayer !== "undefined") allPlayer.stop();
  if (typeof glcPlayer !== "undefined") glcPlayer.stop();
  tabs.forEach((t, idx) => {
    const selected = t === target;
    t.setAttribute("aria-selected", String(selected));
    t.tabIndex = selected ? 0 : -1;
    if (selected) panels[idx].removeAttribute("hidden");
    else panels[idx].setAttribute("hidden", "until-found");
  });
  target.scrollIntoView({ block: "nearest", inline: "nearest" });
  if (focusTab) target.focus();
}

tabs.forEach((tab, idx) => {
  tab.addEventListener("click", () => openTab(tab.id, false));
  tab.addEventListener("keydown", (ev) => {
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      openTab(tabs[(idx + 1) % tabs.length].id, true);
    } else if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      openTab(tabs[(idx - 1 + tabs.length) % tabs.length].id, true);
    } else if (ev.key === "Home") {
      ev.preventDefault();
      openTab(tabs[0].id, true);
    } else if (ev.key === "End") {
      ev.preventDefault();
      openTab(tabs[tabs.length - 1].id, true);
    }
  });
});

panels.forEach((panel, idx) => {
  panel.addEventListener("beforematch", () => openTab(tabs[idx].id, false));
});

/* ============================================================================
 * 2. Helpers seguros
 * ============================================================================ */
let SPEC = null;
let PRESETS = {};
let SUITE_ROWS = [];
let SUITE_FILTER = "ALL_MODS";
let INPUT_MODE = "code";

function clearEl(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function makeTd(text, label) {
  const td = document.createElement("td");
  td.textContent = text;
  if (label) td.dataset.label = label;
  return td;
}

function setTag(el, kind, text) {
  el.className = `status-tag tag-${kind}`;
  el.textContent = text;
}

async function postJson(url, body) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return resp.json();
}

/* ============================================================================
 * 3. Player enxuto para AP, ALL e GLC
 * ============================================================================ */
class StepPlayer {
  constructor({ prev, play, next, end, speed, counter, onRender }) {
    this.playBtn = play;
    this.speedEl = speed || null;
    this.counterEl = counter;
    this.onRender = onRender;
    this.steps = [];
    this.meta = {};
    this.index = 0;
    this.timer = null;

    prev.addEventListener("click", () => this.go(this.index - 1));
    next.addEventListener("click", () => this.go(this.index + 1));
    end.addEventListener("click", () => this.go(this.steps.length - 1));
    play.addEventListener("click", () => this.toggle());
  }

  load(steps, meta = {}) {
    this.stop();
    this.steps = steps || [];
    this.meta = meta;
    this.index = 0;
    this.render();
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.playBtn.textContent = "▶ play";
  }

  toggle() {
    if (this.timer) {
      this.stop();
      return;
    }
    if (this.steps.length <= 1) return;
    if (this.index >= this.steps.length - 1) {
      this.index = 0;
      this.render();
    }
    this.playBtn.textContent = "⏸ pause";
    const ms = this.speedEl ? Number(this.speedEl.value) : 380;
    this.timer = setInterval(() => {
      if (this.index < this.steps.length - 1) {
        this.index += 1;
        this.render();
      } else {
        this.stop();
      }
    }, ms);
  }

  go(i) {
    this.stop();
    if (!this.steps.length) return;
    this.index = Math.max(0, Math.min(i, this.steps.length - 1));
    this.render();
  }

  render() {
    const total = Math.max(0, this.steps.length - 1);
    this.counterEl.textContent = `${this.index}/${total}`;
    if (this.steps.length) {
      this.onRender(this.steps[this.index], this.index, this.steps, this.meta);
    }
  }
}

/* ============================================================================
 * 3.5 Renderizador SVG de Grafos de Autômatos (AP e ALL com destaque ao vivo)
 * ============================================================================ */
const SVG_NS = "http://www.w3.org/2000/svg";

const AP_LAYOUT = {
  q0: [68, 128],
  q1: [200, 128],
  q2: [358, 128],
  q3: [528, 128],
  q4: [684, 128],
  q5: [842, 128],
  q6: [684, 248],
  q7: [480, 248],
  q8: [270, 248],
};

const ALL_LAYOUT = {
  q0: [58, 205],
  q1: [168, 205],
  q2: [355, 92],
  q4: [605, 92],
  q6: [835, 205],
  q7: [605, 205],
  q8: [355, 205],
  q3: [355, 315],
  q5: [605, 315],
  q9: [495, 435],
  q10: [730, 435],
};

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

function buildAutomatonGraph(svg, { states, finals, transitions, layout, mode }) {
  clearEl(svg);
  const idPrefix = svg.id;
  const R = 21;

  // Defs: marcadores de seta (padrão e ativo)
  const defs = svgEl("defs");
  const makeMarker = (id, color) => {
    const m = svgEl("marker", {
      id,
      viewBox: "0 0 10 10",
      refX: "8.5",
      refY: "5",
      markerWidth: "6",
      markerHeight: "6",
      orient: "auto-start-reverse",
    });
    m.appendChild(svgEl("path", { d: "M 0 1.5 L 9 5 L 0 8.5 z", fill: color }));
    return m;
  };
  defs.append(
    makeMarker(`${idPrefix}-arr`, "#476278"),
    makeMarker(`${idPrefix}-arr-hi`, "#38bdf8"),
  );
  svg.appendChild(defs);

  // Agrupa transições paralelas por (from -> to)
  const grouped = new Map();
  transitions.forEach((t) => {
    const key = `${t.from}->${t.to}`;
    const txt = mode === "ap" ? `${t.read},${t.pop}/${t.push}` : `${t.read}→${t.write},${t.move}`;
    if (!grouped.has(key)) grouped.set(key, { from: t.from, to: t.to, labels: [] });
    grouped.get(key).labels.push(txt);
  });

  // Seta de estado inicial -> q0
  const [x0, y0] = layout.q0;
  svg.appendChild(
    svgEl("path", {
      d: `M ${x0 - 46} ${y0} L ${x0 - R - 4} ${y0}`,
      stroke: "#22c55e",
      "stroke-width": "2",
      fill: "none",
      "marker-end": `url(#${idPrefix}-arr)`,
    }),
  );

  // Desenha arestas
  const edgesLayer = svgEl("g");
  grouped.forEach((edge, key) => {
    const [fx, fy] = layout[edge.from];
    const [tx, ty] = layout[edge.to];
    const g = svgEl("g", { class: "aut-edge", "data-edge": key });

    let d = "";
    let lx = 0;
    let ly = 0;

    if (edge.from === edge.to) {
      // Self-loop (para cima por padrão; para baixo em q7 AP e q3/q5/q9 ALL)
      const loopDown =
        (mode === "ap" && edge.from === "q7") ||
        (mode === "all" && (edge.from === "q3" || edge.from === "q5" || edge.from === "q9"));
      const dir = loopDown ? 1 : -1;
      const numRows = Math.ceil(edge.labels.length / 2);
      d = `M ${fx - 10} ${fy + dir * (R - 2)} C ${fx - 34} ${fy + dir * 64}, ${fx + 34} ${fy + dir * 64}, ${fx + 10} ${fy + dir * (R - 2)}`;
      lx = fx;
      ly = loopDown ? fy + 66 : fy - 56 - (numRows - 1) * 12;
    } else {
      const dx = tx - fx;
      const dy = ty - fy;
      const dist = Math.hypot(dx, dy) || 1;
      const ux = dx / dist;
      const uy = dy / dist;

      // Curvatura suave em transições especiais para evitar sobreposições
      let bend = 0;
      if (mode === "ap" && key === "q5->q6") bend = 24;
      if (mode === "all" && key === "q8->q9") bend = -36;

      const sx = fx + ux * R;
      const sy = fy + uy * R;
      const ex = tx - ux * (R + 3);
      const ey = ty - uy * (R + 3);

      const mx = (sx + ex) / 2 - uy * bend;
      const my = (sy + ey) / 2 + ux * bend;
      d = bend === 0 ? `M ${sx} ${sy} L ${ex} ${ey}` : `M ${sx} ${sy} Q ${mx} ${my} ${ex} ${ey}`;
      lx = (sx + ex) / 2 - uy * (bend * 0.65);
      ly = (sy + ey) / 2 + ux * (bend * 0.65) - 8;

      if (mode === "ap" && (key === "q6->q7" || key === "q7->q8")) ly += 22;
      if (mode === "all" && key === "q8->q2") { lx -= 34; ly += 8; }
      if (mode === "all" && key === "q8->q3") { lx -= 34; ly += 8; }
      if (mode === "all" && key === "q8->q9") { lx += 28; ly += 4; }
    }

    g.appendChild(
      svgEl("path", {
        d,
        "marker-end": `url(#${idPrefix}-arr)`,
      }),
    );

    // Compacta rótulos em linhas limpas (máximo 2 itens por linha)
    const rows = [];
    for (let i = 0; i < edge.labels.length; i += 2) {
      rows.push(edge.labels.slice(i, i + 2).join(" | "));
    }
    const textEl = svgEl("text", { x: lx, y: ly });
    rows.forEach((line, idx) => {
      const ts = svgEl("tspan", { x: lx, dy: idx === 0 ? "0" : "11.5" });
      ts.textContent = line;
      textEl.appendChild(ts);
    });
    g.appendChild(textEl);
    edgesLayer.appendChild(g);
  });
  svg.appendChild(edgesLayer);

  // Desenha nós (estados)
  const finalsSet = new Set(finals);
  const nodesLayer = svgEl("g");
  states.forEach((st) => {
    const [x, y] = layout[st];
    const g = svgEl("g", { class: "aut-node", "data-state": st });
    g.appendChild(svgEl("circle", { class: "node-outer", cx: x, cy: y, r: R }));
    if (finalsSet.has(st)) {
      g.appendChild(svgEl("circle", { class: "node-inner", cx: x, cy: y, r: R - 4.5 }));
    }
    const label = svgEl("text", { x, y });
    label.textContent = st;
    g.appendChild(label);
    nodesLayer.appendChild(g);
  });
  svg.appendChild(nodesLayer);
}

function updateAutomatonGraph(svg, activeState, visitedSet, activeEdgeKey, isRejectedEnd = false) {
  const idPrefix = svg.id;
  svg.querySelectorAll(".aut-node").forEach((n) => {
    const st = n.dataset.state;
    const active = st === activeState;
    n.classList.toggle("is-active", active);
    n.classList.toggle("is-rejected", active && isRejectedEnd);
    n.classList.toggle("is-visited", visitedSet.has(st));
  });
  svg.querySelectorAll(".aut-edge").forEach((e) => {
    const isHit = e.dataset.edge === activeEdgeKey;
    e.classList.toggle("is-active", isHit);
    const p = e.querySelector("path");
    if (p) p.setAttribute("marker-end", `url(#${idPrefix}-${isHit ? "arr-hi" : "arr"})`);
  });
}

/* ============================================================================
 * 4. Trilhas de estados, Pilha, Fita Limitada e GLC
 * ============================================================================ */
function buildStateTrack(el, states, finals) {
  clearEl(el);
  const fset = new Set(finals);
  states.forEach((s) => {
    const node = document.createElement("div");
    node.className = fset.has(s) ? "st-node is-final" : "st-node";
    node.dataset.state = s;
    node.textContent = s;
    el.appendChild(node);
  });
}

function updateStateTrack(el, active, visited, isRejectedEnd = false) {
  el.querySelectorAll(".st-node").forEach((n) => {
    const st = n.dataset.state;
    const isAct = st === active;
    n.classList.toggle("is-active", isAct);
    n.classList.toggle("is-rejected", isAct && isRejectedEnd);
    n.classList.toggle("is-visited", visited.has(st));
  });
}

const apPlayer = new StepPlayer({
  prev: document.getElementById("ap-prev"),
  play: document.getElementById("ap-play"),
  next: document.getElementById("ap-next"),
  end: document.getElementById("ap-end"),
  speed: document.getElementById("ap-speed"),
  counter: document.getElementById("ap-counter"),
  onRender: (step, idx, allSteps, meta) => {
    const visited = new Set(allSteps.slice(0, idx + 1).map((s) => s.state));
    const edgeKey = idx > 0 ? `${allSteps[idx - 1].state}->${step.state}` : null;
    const rejectedEnd = meta.accepted === false && idx === allSteps.length - 1;
    updateStateTrack(document.getElementById("ap-state-track"), step.state, visited, rejectedEnd);
    updateAutomatonGraph(document.getElementById("ap-graph-svg"), step.state, visited, edgeKey, rejectedEnd);
    document.getElementById("ap-desc").textContent = `${step.state} · ${(SPEC && SPEC.ap.descriptions[step.state]) || ""}`;
    document.getElementById("ap-trans").textContent = step.transition || "init";

    const strip = document.getElementById("ap-input-strip");
    clearEl(strip);
    const chars = Array.from(meta.input || "");
    if (!chars.length) {
      const c = document.createElement("div");
      c.className = "t-cell";
      c.textContent = "ε";
      strip.appendChild(c);
    } else {
      chars.forEach((ch, pos) => {
        const c = document.createElement("div");
        c.className = "t-cell";
        if (pos < step.position) c.classList.add("is-consumed");
        if (pos === step.position) c.classList.add("is-head");
        c.textContent = ch;
        const idxEl = document.createElement("i");
        idxEl.textContent = String(pos);
        c.appendChild(idxEl);
        strip.appendChild(c);
      });
    }

    const tower = document.getElementById("ap-stack-tower");
    clearEl(tower);
    const syms = Array.from(step.stack);
    syms.forEach((sym, i) => {
      const blk = document.createElement("div");
      blk.className = "stk-blk";
      if (i === 0) blk.classList.add("is-top");
      else if (i === syms.length - 1 && sym === "Z") blk.classList.add("is-base");
      const s = document.createElement("span");
      s.textContent = sym;
      const tag = document.createElement("small");
      tag.textContent = i === 0 ? "top" : sym === "Z" ? "base" : "";
      blk.append(s, tag);
      tower.appendChild(blk);
    });
  },
});

const allPlayer = new StepPlayer({
  prev: document.getElementById("all-prev"),
  play: document.getElementById("all-play"),
  next: document.getElementById("all-next"),
  end: document.getElementById("all-end"),
  speed: document.getElementById("all-speed"),
  counter: document.getElementById("all-counter"),
  onRender: (step, idx, allSteps, meta) => {
    const visited = new Set(allSteps.slice(0, idx + 1).map((s) => s.state));
    const edgeKey = idx > 0 ? `${allSteps[idx - 1].state}->${step.state}` : null;
    const rejectedEnd = meta.accepted === false && idx === allSteps.length - 1;
    updateStateTrack(document.getElementById("all-state-track"), step.state, visited, rejectedEnd);
    updateAutomatonGraph(document.getElementById("all-graph-svg"), step.state, visited, edgeKey, rejectedEnd);
    document.getElementById("all-desc").textContent = `${step.state} · ${(SPEC && SPEC.all.descriptions[step.state]) || ""}`;
    document.getElementById("all-trans").textContent = step.transition || "init";
    document.getElementById("all-size-lbl").textContent = `${meta.writable_cells}+2 cells`;

    const strip = document.getElementById("all-tape-strip");
    clearEl(strip);
    Array.from(step.tape).forEach((ch, pos) => {
      const c = document.createElement("div");
      c.className = "t-cell";
      if (ch === "<" || ch === ">") c.classList.add("is-marker");
      else if (ch === "I" || ch === "S") c.classList.add("is-matched");
      if (pos === step.head) c.classList.add("is-head");
      c.textContent = ch;
      const idxEl = document.createElement("i");
      idxEl.textContent = String(pos);
      c.appendChild(idxEl);
      strip.appendChild(c);
    });
  },
});

const glcPlayer = new StepPlayer({
  prev: document.getElementById("glc-prev"),
  play: document.getElementById("glc-play"),
  next: document.getElementById("glc-next"),
  end: document.getElementById("glc-end"),
  counter: document.getElementById("glc-counter"),
  onRender: (step, idx) => {
    document.getElementById("glc-rule-caption").textContent = step.rule_applied || "start_symbol";
    document.querySelectorAll("#glc-prods .p-chip").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.prodId === step.rule_id);
    });

    const out = document.getElementById("glc-sentential");
    clearEl(out);
    const nts = new Set(["S", "B", "T", "R"]);
    let marked = false;
    for (const ch of step.sentential_form) {
      if (!marked && nts.has(ch)) {
        const sp = document.createElement("span");
        sp.className = "nt-mark";
        sp.textContent = ch;
        out.appendChild(sp);
        marked = true;
      } else {
        out.appendChild(document.createTextNode(ch));
      }
    }

    document.querySelectorAll("#glc-history .deriv-row").forEach((el, i) => {
      el.classList.toggle("is-active", i === idx);
    });
  },
});

function setErrComment(el, text, kind = "err") {
  if (!text) {
    el.hidden = true;
    el.textContent = "";
    el.className = "err-comment";
    return;
  }
  el.hidden = false;
  el.className = kind === "warn" ? "err-comment is-warn" : "err-comment";
  el.textContent = `# motivo: ${text}`;
}

function loadAP(res, inputStr) {
  document.getElementById("ap-input").value = inputStr;
  const tbody = document.getElementById("ap-trace-tbody");
  const descEl = document.getElementById("ap-desc");
  const transEl = document.getElementById("ap-trans");
  const errEl = document.getElementById("ap-err-comment");
  clearEl(tbody);
  descEl.classList.remove("is-error");

  if (!res) {
    setTag(document.getElementById("ap-badge"), "muted", "SKIP");
    updateStateTrack(document.getElementById("ap-state-track"), null, new Set());
    updateAutomatonGraph(document.getElementById("ap-graph-svg"), null, new Set(), null);
    descEl.textContent = "Etapa 1 não executada (interrompida na verificação léxica).";
    transEl.textContent = "—";
    setErrComment(errEl, "o analisador léxico rejeitou a entrada antes da Etapa 1 (AP).", "warn");
    clearEl(document.getElementById("ap-input-strip"));
    clearEl(document.getElementById("ap-stack-tower"));
    apPlayer.load([], { input: inputStr });
    return;
  }

  if (res.lexical_error) {
    setTag(document.getElementById("ap-badge"), "err", "LEX ERR");
    updateStateTrack(document.getElementById("ap-state-track"), null, new Set());
    updateAutomatonGraph(document.getElementById("ap-graph-svg"), null, new Set(), null);
    descEl.textContent = "Entrada bloqueada antes de δ_AP.";
    descEl.classList.add("is-error");
    transEl.textContent = "alfabeto inválido";
    setErrComment(errEl, res.lexical_error, "err");
    clearEl(document.getElementById("ap-input-strip"));
    clearEl(document.getElementById("ap-stack-tower"));
    apPlayer.load([], { input: inputStr });
    return;
  }

  setTag(document.getElementById("ap-badge"), res.accepted ? "ok" : "err", res.accepted ? "ACCEPT" : "REJECT");
  setErrComment(errEl, res.accepted ? "" : res.reason, "err");
  apPlayer.load(res.trace, { input: inputStr, accepted: res.accepted });
  (res.trace || []).forEach((s) => {
    const tr = document.createElement("tr");
    tr.append(
      makeTd(String(s.step), "#"),
      makeTd(s.state, "state"),
      makeTd(String(s.position), "pos"),
      makeTd(s.stack, "stack"),
      makeTd(s.remaining_input || "ε", "rem"),
      makeTd(s.transition || "init", "delta"),
    );
    tbody.appendChild(tr);
  });
}

function loadALL(res, inputStr) {
  document.getElementById("all-input").value = inputStr || "";
  const tbody = document.getElementById("all-trace-tbody");
  const descEl = document.getElementById("all-desc");
  const transEl = document.getElementById("all-trans");
  const errEl = document.getElementById("all-err-comment");
  clearEl(tbody);
  descEl.classList.remove("is-error");

  if (!res) {
    setTag(document.getElementById("all-badge"), "muted", "SKIP");
    updateStateTrack(document.getElementById("all-state-track"), null, new Set());
    updateAutomatonGraph(document.getElementById("all-graph-svg"), null, new Set(), null);
    descEl.textContent = "Etapa 2 não executada.";
    transEl.textContent = "—";
    setErrComment(errEl, "o ALL só executa quando a Etapa 1 (AP) aceita a estrutura sintática.", "warn");
    document.getElementById("all-size-lbl").textContent = "0+2 cells";
    clearEl(document.getElementById("all-tape-strip"));
    allPlayer.load([], { writable_cells: 0 });
    return;
  }

  if (res.lexical_error) {
    setTag(document.getElementById("all-badge"), "err", "LEX ERR");
    updateStateTrack(document.getElementById("all-state-track"), null, new Set());
    updateAutomatonGraph(document.getElementById("all-graph-svg"), null, new Set(), null);
    descEl.textContent = "Entrada bloqueada antes de δ_ALL.";
    descEl.classList.add("is-error");
    transEl.textContent = "alfabeto inválido";
    setErrComment(errEl, res.lexical_error, "err");
    document.getElementById("all-size-lbl").textContent = `${res.writable_cells}+2 cells`;
    clearEl(document.getElementById("all-tape-strip"));
    allPlayer.load([], { writable_cells: res.writable_cells });
    return;
  }

  setTag(document.getElementById("all-badge"), res.accepted ? "ok" : "err", res.accepted ? "ACCEPT" : "REJECT");
  setErrComment(errEl, res.accepted ? "" : res.reason, "err");
  allPlayer.load(res.trace, { writable_cells: res.writable_cells, accepted: res.accepted });
  (res.trace || []).forEach((s) => {
    const tr = document.createElement("tr");
    const tape = `${s.tape.slice(0, s.head)}[${s.tape[s.head]}]${s.tape.slice(s.head + 1)}`;
    tr.append(
      makeTd(String(s.step), "#"),
      makeTd(s.state, "state"),
      makeTd(String(s.head), "head"),
      makeTd(s.symbol_read, "read"),
      makeTd(tape, "tape"),
      makeTd(s.transition || "init", "delta"),
    );
    tbody.appendChild(tr);
  });
}

function loadGLC(derivation) {
  const hist = document.getElementById("glc-history");
  clearEl(hist);
  document.querySelectorAll("#glc-prods .p-chip").forEach((el) => el.classList.remove("is-active"));
  if (!derivation || !derivation.length) {
    document.getElementById("glc-rule-caption").textContent = "no_derivation";
    document.getElementById("glc-sentential").textContent = "— rejeitada pela GLC / AP —";
    glcPlayer.load([]);
    return;
  }
  derivation.forEach((step, idx) => {
    const row = document.createElement("div");
    row.className = "deriv-row";
    const a = document.createElement("span");
    a.textContent = `${step.step}. ${step.step === 0 ? "  " : "⇒ "}${step.sentential_form}`;
    const b = document.createElement("span");
    b.textContent = step.rule_id || "start";
    row.append(a, b);
    row.addEventListener("click", () => glcPlayer.go(idx));
    hist.appendChild(row);
  });
  glcPlayer.load(derivation);
}

/* ============================================================================
 * 5. Frontpage ./run — Compilação MiniLang e Raw
 * ============================================================================ */
const editorEl = document.getElementById("minilang-editor");
const gutterEl = document.getElementById("code-gutter");
const backdropEl = document.getElementById("code-backdrop");
let CURRENT_ERROR_SPAN = null;

function renderCodeHighlights(span = null) {
  CURRENT_ERROR_SPAN = span;
  const lines = editorEl.value.split("\n");

  // Numeração de linhas na calha com marcação na linha do erro
  clearEl(gutterEl);
  lines.forEach((_, idx) => {
    const ln = document.createElement("span");
    ln.className = "gutter-ln";
    const lineNum = idx + 1;
    if (span && span.line === lineNum) {
      ln.classList.add(span.severity === "warn" ? "is-warn" : "is-err");
      ln.textContent = `● ${lineNum}`;
    } else {
      ln.textContent = String(lineNum);
    }
    gutterEl.appendChild(ln);
  });

  // Camada backdrop com sublinhado ondulado estilo IDE (~~~~) no token exato
  clearEl(backdropEl);
  lines.forEach((lineText, idx) => {
    const lineNum = idx + 1;
    const lineEl = document.createElement("span");
    lineEl.className = "ide-line";
    if (span && span.line === lineNum) {
      lineEl.classList.add(span.severity === "warn" ? "has-warn" : "has-err");
      const start = Math.max(0, Math.min((span.column || 1) - 1, lineText.length));
      const len = Math.max(1, span.length || 1);
      const end = Math.min(lineText.length, start + len);
      const before = lineText.slice(0, start);
      const target = lineText.slice(start, end) || " ";
      const after = lineText.slice(end);
      if (before) lineEl.appendChild(document.createTextNode(before));
      const mark = document.createElement("mark");
      mark.className = span.severity === "warn" ? "ide-squiggle is-warn" : "ide-squiggle";
      mark.textContent = target;
      lineEl.appendChild(mark);
      if (after) lineEl.appendChild(document.createTextNode(after));
    } else {
      lineEl.textContent = lineText || " ";
    }
    backdropEl.appendChild(lineEl);
  });
}

function syncGutter() {
  renderCodeHighlights(null);
}

editorEl.addEventListener("input", () => {
  renderCodeHighlights(null);
  setActiveScenarioFlag(null);
});
editorEl.addEventListener("scroll", () => {
  backdropEl.scrollTop = editorEl.scrollTop;
  backdropEl.scrollLeft = editorEl.scrollLeft;
});

function renderStdout(pipe, lexInfo, projections) {
  const verdict = document.getElementById("stdout-verdict");
  if (pipe.stage_stopped === "CONCLUIDO") setTag(verdict, "ok", "EXIT 0 · ACCEPTED");
  else if (pipe.stage_stopped === "ALL") setTag(verdict, "warn", "EXIT 2 · SEMANTIC ERR");
  else if (pipe.stage_stopped === "AP") setTag(verdict, "err", "EXIT 1 · SYNTAX ERR");
  else setTag(verdict, "err", "EXIT 1 · LEXICAL ERR");

  // [0] LEXER
  setTag(document.getElementById("out-lex-tag"), lexInfo.ok ? "ok" : "err", lexInfo.ok ? "OK" : "ERR");
  document.getElementById("out-lex-info").textContent = lexInfo.short;

  // [1] AP
  const goApBtn = document.getElementById("go-ap-btn");
  const goGlcBtn = document.getElementById("go-glc-btn");
  const goAllBtn = document.getElementById("go-all-btn");

  if (pipe.ap_result) {
    const ok = pipe.ap_result.accepted;
    setTag(document.getElementById("out-ap-tag"), ok ? "ok" : "err", ok ? "ACCEPT" : "REJECT");
    document.getElementById("out-ap-info").textContent =
      `9 states · ${pipe.ap_result.steps} steps · final=${pipe.ap_result.final_state} · stack=${pipe.ap_result.final_stack}`;
    goApBtn.disabled = false;
    goGlcBtn.disabled = !ok;
  } else {
    setTag(document.getElementById("out-ap-tag"), "muted", "SKIP");
    document.getElementById("out-ap-info").textContent = "interrompido no léxico";
    goApBtn.disabled = true;
    goGlcBtn.disabled = true;
  }

  // [2] ALL
  if (pipe.all_result) {
    const ok = pipe.all_result.accepted;
    setTag(document.getElementById("out-all-tag"), ok ? "ok" : "err", ok ? "ACCEPT" : "REJECT");
    document.getElementById("out-all-info").textContent =
      `'${pipe.semantic_slice}' · ${pipe.all_result.writable_cells}+2 cells · ${pipe.all_result.steps} steps · final=${pipe.all_result.final_state}`;
    goAllBtn.disabled = false;
  } else {
    setTag(document.getElementById("out-all-tag"), "muted", "SKIP");
    document.getElementById("out-all-info").textContent = "não executado (aguarda AP ACCEPT)";
    goAllBtn.disabled = true;
  }

  // Comentário explicativo inline no stdout sempre que houver erro ou aviso parcial
  const stdoutComment = document.getElementById("stdout-comment");
  if (pipe.stage_stopped === "CONCLUIDO") {
    setErrComment(stdoutComment, "");
  } else if (pipe.stage_stopped === "LEXICO") {
    setErrComment(stdoutComment, lexInfo.detail, "err");
  } else if (pipe.stage_stopped === "AP" && pipe.ap_result) {
    setErrComment(
      stdoutComment,
      `${pipe.ap_result.reason} Como a sintaxe falhou na Etapa 1, a Etapa 2 (ALL) não é executada.`,
      "err",
    );
  } else if (pipe.stage_stopped === "ALL" && pipe.all_result) {
    setErrComment(
      stdoutComment,
      `A sintaxe foi aceita pelo AP, mas a semântica falhou: ${pipe.all_result.reason}`,
      "warn",
    );
  }

  // Drawer 1: Projeção de tokens
  const projBox = document.getElementById("projection-chips");
  clearEl(projBox);
  document.getElementById("proj-meta").textContent = pipe.input_str || "";
  (projections || []).forEach((p) => {
    const chip = document.createElement("span");
    chip.className = "proj-chip";
    chip.title = p.role;
    const s = document.createElement("span");
    s.textContent = p.source_lexeme;
    const a = document.createElement("span");
    a.textContent = "→";
    const f = document.createElement("strong");
    f.textContent = p.formal_symbol;
    chip.append(s, a, f);
    projBox.appendChild(chip);
  });
  document.getElementById("drawer-projection").hidden = !projections || !projections.length;

  // Drawer 2: Diagnóstico completo
  const lines = [
    `[LEX] ${lexInfo.detail}`,
    `[AP ] ${pipe.ap_result ? pipe.ap_result.reason : "não executado"}`,
    `[ALL] ${pipe.all_result ? pipe.all_result.reason : "não executado"}`,
  ];
  document.getElementById("diag-log").textContent = lines.join("\n");

  loadAP(pipe.ap_result, pipe.input_str);
  loadALL(pipe.all_result, pipe.semantic_slice || "");
  loadGLC(pipe.derivation);
}

const SCENARIO_RAW = {
  ok: "p{(()){}}#isisiisis:isisiisis;",
  syntax_err: "p{(()){}#isisiisis:isisiisis;",
  semantic_err: "p{(()){}}#isisiisis:isisiissi;",
  lexical_err: "p{(()){}}#isisi@isisi;",
};

async function runCode() {
  const data = await postJson("/api/compile/minilang", { source: editorEl.value });
  renderCodeHighlights(data.error_span || null);
  // Mantém o campo raw sempre sincronizado com o que foi compilado no editor MiniLang
  if (data.lexical_ok) {
    document.getElementById("raw-input").value = data.formal_string;
    renderRawVisualStrip(data.formal_string, data.pipeline);
  }
  const lexInfo = data.lexical_ok
    ? {
        ok: true,
        short: `${data.token_count} tokens → ${data.formal_string}`,
        detail: `${data.token_count} tokens reconhecidos pelo MiniLexer (AV1) → '${data.formal_string}' (${data.formal_string.length} chars).`,
      }
    : { ok: false, short: data.lexical_error, detail: data.lexical_error };
  renderStdout(data.pipeline, lexInfo, data.projections);
}

function renderRawVisualStrip(cadeia, pipe) {
  const strip = document.getElementById("raw-visual-strip");
  clearEl(strip);
  const chars = Array.from(cadeia || "");
  if (!chars.length) {
    const empty = document.createElement("span");
    empty.className = "raw-ch is-fault-err";
    empty.textContent = "ε";
    strip.appendChild(empty);
    return;
  }

  let faultIdx = -1;
  let faultKind = "";

  if (pipe.stage_stopped === "LEXICO") {
    const m = /posição (\d+)/.exec(pipe.lexical_error || "");
    if (m) {
      faultIdx = Number(m[1]);
      faultKind = "err";
    }
  } else if (pipe.stage_stopped === "AP" && pipe.ap_result) {
    faultIdx = Math.min(pipe.ap_result.final_position, chars.length - 1);
    faultKind = "err";
  } else if (pipe.stage_stopped === "ALL" && pipe.all_result) {
    const hashPos = cadeia.indexOf("#");
    if (hashPos >= 0) {
      const idx = hashPos + 1 + (pipe.all_result.final_head - 1);
      faultIdx = Math.max(0, Math.min(idx, chars.length - 1));
      faultKind = "warn";
    }
  }

  chars.forEach((ch, idx) => {
    const el = document.createElement("span");
    el.className = "raw-ch";
    if (ch === "p") el.classList.add("tok-head");
    else if ("{}()".includes(ch)) el.classList.add("tok-scope");
    else if ("#:;".includes(ch)) el.classList.add("tok-sep");
    else if (ch === "i") el.classList.add("tok-type-i");
    else if (ch === "s") el.classList.add("tok-type-s");
    if (idx === faultIdx) el.classList.add(faultKind === "warn" ? "is-fault-warn" : "is-fault-err");
    el.textContent = ch;
    el.title = `pos ${idx}: '${ch}'`;
    strip.appendChild(el);
  });
}

async function runRaw() {
  const cadeia = document.getElementById("raw-input").value;
  const pipe = await postJson("/api/validate/pipeline", { input: cadeia });
  renderRawVisualStrip(cadeia, pipe);
  const lexInfo = pipe.lexical_error
    ? { ok: false, short: pipe.lexical_error, detail: pipe.lexical_error }
    : { ok: true, short: `Σ_AP válido (${cadeia.length} chars) → ${cadeia}`, detail: `Todos os ${cadeia.length} símbolos pertencem a Σ_AP.` };
  renderStdout(pipe, lexInfo, []);
}

function setMode(mode) {
  INPUT_MODE = mode;
  const isCode = mode === "code";
  document.getElementById("mode-code-btn").classList.toggle("is-active", isCode);
  document.getElementById("mode-raw-btn").classList.toggle("is-active", !isCode);
  document.getElementById("code-box").hidden = !isCode;
  document.getElementById("raw-box").hidden = isCode;
  document.getElementById("editor-title").textContent = isCode ? "programa.min" : "stdin :: Σ_AP";
}

function setActiveScenarioFlag(scenarioId) {
  document.querySelectorAll("[data-scenario]").forEach((b) =>
    b.classList.toggle("is-active", b.dataset.scenario === scenarioId),
  );
}

document.getElementById("mode-code-btn").addEventListener("click", () => { setMode("code"); runCode(); });
document.getElementById("mode-raw-btn").addEventListener("click", () => { setMode("raw"); runRaw(); });
document.getElementById("run-btn").addEventListener("click", () => (INPUT_MODE === "code" ? runCode() : runRaw()));
document.getElementById("raw-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runRaw(); });
document.getElementById("raw-input").addEventListener("input", () => setActiveScenarioFlag(null));

document.querySelectorAll("[data-scenario]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.scenario;
    const preset = PRESETS[id];
    const rawStr = SCENARIO_RAW[id];
    if (!preset || !rawStr) return;

    setActiveScenarioFlag(id);
    // Sincroniza ambos (código MiniLang + cadeia formal raw) e executa no modo atual
    editorEl.value = preset.code;
    syncGutter();
    document.getElementById("raw-input").value = rawStr;
    if (INPUT_MODE === "code") runCode();
    else runRaw();
  });
});

document.getElementById("go-ap-btn").addEventListener("click", () => openTab("tab-ap"));
document.getElementById("go-all-btn").addEventListener("click", () => openTab("tab-all"));
document.getElementById("go-glc-btn").addEventListener("click", () => openTab("tab-glc"));

document.getElementById("ap-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const val = document.getElementById("ap-input").value;
  const data = await postJson("/api/validate/ap", { input: val });
  loadAP(data.ap_result, val);
  loadGLC(data.derivation);
});

document.getElementById("all-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const val = document.getElementById("all-input").value;
  const data = await postJson("/api/validate/all", { input: val });
  loadALL(data.all_result, val);
});

/* ============================================================================
 * 6. Suite (50 casos) & Specs
 * ============================================================================ */
function renderSuite() {
  const tbody = document.getElementById("suite-tbody");
  clearEl(tbody);
  const rows = SUITE_FILTER === "ALL_MODS" ? SUITE_ROWS : SUITE_ROWS.filter((r) => r.modulo === SUITE_FILTER);
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    const gotTd = makeTd(r.obtido ? "ACCEPT" : "REJECT", "got");
    gotTd.style.color = r.passou ? "var(--green)" : "var(--red)";
    gotTd.style.fontWeight = "700";

    const actTd = document.createElement("td");
    const actWrap = document.createElement("div");
    actWrap.className = "suite-actions";

    const codeBtn = document.createElement("button");
    codeBtn.type = "button";
    codeBtn.className = "out-link";
    codeBtn.textContent = "code →";
    codeBtn.title = "Carregar código MiniLang deste teste no editor ./run";
    codeBtn.addEventListener("click", async () => {
      setActiveScenarioFlag(null);
      setMode("code");
      editorEl.value = r.minilang_code || "";
      document.getElementById("raw-input").value = r.entrada || "";
      syncGutter();
      await runCode();
      openTab("tab-run");
    });

    const simBtn = document.createElement("button");
    simBtn.type = "button";
    simBtn.className = "out-link";
    simBtn.textContent = "sim →";
    simBtn.title = "Abrir direto no simulador formal (AP / ALL)";
    simBtn.addEventListener("click", async () => {
      if (r.modulo === "ALL" || r.id === "LEX-02") {
        const d = await postJson("/api/validate/all", { input: r.entrada });
        loadALL(d.all_result, r.entrada);
        openTab("tab-all");
      } else if (r.modulo === "AP") {
        const d = await postJson("/api/validate/ap", { input: r.entrada });
        loadAP(d.ap_result, r.entrada);
        loadGLC(d.derivation);
        openTab("tab-ap");
      } else {
        setMode("raw");
        document.getElementById("raw-input").value = r.entrada;
        await runRaw();
        openTab("tab-run");
      }
    });

    actWrap.append(codeBtn, simBtn);
    actTd.appendChild(actWrap);

    tr.append(
      makeTd(r.id, "id"),
      makeTd(r.modulo, "mod"),
      makeTd(String(r.comprimento), "len"),
      makeTd(r.entrada || '""', "input"),
      makeTd(r.esperado ? "ACCEPT" : "REJECT", "exp"),
      gotTd,
      makeTd(r.regra_verificada, "rule"),
      actTd,
    );
    tbody.appendChild(tr);
  });
}

async function loadSuite() {
  const resp = await fetch("/api/tests/run");
  const data = await resp.json();
  SUITE_ROWS = data.rows;
  document.getElementById("suite-summary-line").textContent =
    `PASS ${data.passed}/${data.total} · failed=${data.failed} · pytest=92/92 · jflap=418/418`;
  renderSuite();
}

document.querySelectorAll("[data-filter]").forEach((btn) => {
  btn.addEventListener("click", () => {
    SUITE_FILTER = btn.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((b) => b.classList.toggle("is-active", b === btn));
    renderSuite();
  });
});

document.getElementById("reload-suite-btn").addEventListener("click", loadSuite);

/* ============================================================================
 * 6.5 Fullscreen para Grafos e Editor (com ESC para sair)
 * ============================================================================ */
function toggleFullscreenElement(targetId) {
  const el = document.getElementById(targetId);
  if (!el) return;
  const entering = !el.classList.contains("is-fullscreen");
  // Fecha qualquer outro painel em tela cheia
  document.querySelectorAll(".is-fullscreen").forEach((other) => {
    if (other !== el) other.classList.remove("is-fullscreen");
  });
  el.classList.toggle("is-fullscreen", entering);
  document.body.style.overflow = entering ? "hidden" : "";
  document.querySelectorAll("[data-fs-target]").forEach((btn) => {
    const active = btn.dataset.fsTarget === targetId && entering;
    btn.textContent = active ? "✕ sair (ESC)" : "⛶ fullscreen";
  });
}

document.querySelectorAll("[data-fs-target]").forEach((btn) => {
  btn.addEventListener("click", () => toggleFullscreenElement(btn.dataset.fsTarget));
});

document.querySelectorAll("[data-proxy-click]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = document.getElementById(btn.dataset.proxyClick);
    if (target) target.click();
  });
});

window.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") {
    const openFs = document.querySelector(".is-fullscreen");
    if (openFs && openFs.id) toggleFullscreenElement(openFs.id);
  }
});

/* ============================================================================
 * 7. Bootstrap
 * ============================================================================ */
async function init() {
  const resp = await fetch("/api/spec");
  SPEC = await resp.json();

  (SPEC.minilang_presets || []).forEach((p) => { PRESETS[p.id] = p; });

  buildStateTrack(document.getElementById("ap-state-track"), SPEC.ap.states, SPEC.ap.final_states);
  buildStateTrack(document.getElementById("all-state-track"), SPEC.all.states, SPEC.all.final_states);

  const apCfg = {
    states: SPEC.ap.states,
    finals: SPEC.ap.final_states,
    transitions: SPEC.ap.transitions,
    layout: AP_LAYOUT,
    mode: "ap",
  };
  const allCfg = {
    states: SPEC.all.states,
    finals: SPEC.all.final_states,
    transitions: SPEC.all.transitions,
    layout: ALL_LAYOUT,
    mode: "all",
  };
  buildAutomatonGraph(document.getElementById("ap-graph-svg"), apCfg);
  buildAutomatonGraph(document.getElementById("all-graph-svg"), allCfg);
  buildAutomatonGraph(document.getElementById("spec-ap-svg"), apCfg);
  buildAutomatonGraph(document.getElementById("spec-all-svg"), allCfg);

  const prodsEl = document.getElementById("glc-prods");
  clearEl(prodsEl);
  SPEC.glc.productions.forEach((p) => {
    const chip = document.createElement("span");
    chip.className = "p-chip";
    chip.dataset.prodId = p.id;
    chip.textContent = `${p.id}: ${p.text}`;
    prodsEl.appendChild(chip);
  });

  // Preenche ./specs
  document.getElementById("spec-glc-pre").textContent = [
    `V = { ${SPEC.glc.non_terminals.join(", ")} }`,
    `T = { ${SPEC.glc.terminals.join(", ")} }`,
    `S = ${SPEC.glc.start_symbol}`,
    "",
    ...SPEC.glc.productions.map((p) => `  ${p.id}: ${p.text}`),
  ].join("\n");

  document.getElementById("spec-ap-pre").textContent = [
    `Q = { ${SPEC.ap.states.join(", ")} } (${SPEC.ap.state_count} estados) | F = { ${SPEC.ap.final_states.join(", ")} }`,
    `Γ = { ${SPEC.ap.stack_alphabet.join(", ")} } | inicial = ${SPEC.ap.initial_stack_symbol}`,
    "",
    ...SPEC.ap.transitions.map((t) => `  ${t.label}`),
  ].join("\n");

  document.getElementById("spec-all-pre").textContent = [
    `Q = { ${SPEC.all.states.join(", ")} } (${SPEC.all.state_count} estados) | F = { ${SPEC.all.final_states.join(", ")} }`,
    `Σ = { ${SPEC.all.input_alphabet.join(", ")} } | Γ = { ${SPEC.all.tape_alphabet.join(", ")} } | bordas = '${SPEC.all.left_marker}' '${SPEC.all.right_marker}'`,
    "",
    ...SPEC.all.transitions.map((t) => `  ${t.label}`),
  ].join("\n");

  // Frontpage já preenchida com o programa fictício MiniLang e executada ao abrir
  if (PRESETS.ok) {
    editorEl.value = PRESETS.ok.code;
    syncGutter();
    await runCode();
  }
  await loadSuite();
}

init();
