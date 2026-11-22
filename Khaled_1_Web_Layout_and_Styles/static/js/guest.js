// Guest site: mobile menu toggle and the play button of the home video. No inline scripts (CSP friendly).
(() => {
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".g-burger");
    if (b) {
      const open = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", String(open));
      document.getElementById(b.getAttribute("aria-controls")).classList.toggle("open", open);
    }
    const p = e.target.closest("[data-play]");
    if (p) {
      const v = document.getElementById(p.dataset.play);
      if (v) { v.controls = true; v.play(); p.hidden = true; }
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const b = document.querySelector('.g-burger[aria-expanded="true"]');
    if (b) { b.click(); b.focus(); }
  });
})();

// Pricing: the institution-type menu and the VAT toggle swap prices in place.
// Without JavaScript the same links reload the page with ?type=…&vat=1 and the server renders the prices.
(() => {
  const sec = document.querySelector("[data-pricing]");
  if (!sec) return;
  const data = JSON.parse(document.getElementById("g-price-data").textContent);
  const btn = sec.querySelector(".g-pick-btn"), menu = document.getElementById("g-pick-menu");
  const vatBtn = sec.querySelector(".g-vat-btn"), vatNote = sec.querySelector("[data-vat-note]");
  const label = sec.querySelector("[data-type-label]");
  const state = { type: (menu.querySelector('[aria-current="true"]') || menu.querySelector("a")).dataset.type,
                  vat: vatBtn.getAttribute("aria-pressed") === "true" };

  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function render() {
    const rows = data[state.type];
    sec.querySelectorAll(".g-plan").forEach((card, i) => {
      const price = card.querySelector(".g-plan-price"), go = card.querySelector(".g-plan-go");
      if (rows) {
        price.innerHTML = `<b>${esc(state.vat ? rows[i].inc : rows[i].ex)}</b><span>${esc(sec.dataset.month)}</span>`;
        go.href = go.dataset.goPrice; go.textContent = go.dataset.labelPrice;
      } else {
        price.innerHTML = `<b class="g-plan-quote">${esc(sec.dataset.quote)}</b>`;
        go.href = go.dataset.goContact; go.textContent = go.dataset.labelContact;
      }
    });
    menu.querySelectorAll("a").forEach((a) => {
      const on = a.dataset.type === state.type;
      on ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current");
      if (on) label.textContent = a.textContent;
      a.href = `?type=${a.dataset.type}${state.vat ? "&vat=1" : ""}#pricing`;
    });
    vatBtn.setAttribute("aria-pressed", String(state.vat));
    vatBtn.textContent = state.vat ? vatBtn.dataset.on : vatBtn.dataset.off;
    vatBtn.href = `?type=${state.type}${state.vat ? "" : "&vat=1"}#pricing`;
    vatNote.textContent = state.vat ? vatNote.dataset.on : vatNote.dataset.off;
  }
  function openMenu(open) {
    btn.setAttribute("aria-expanded", String(open));
    menu.hidden = !open;
    if (open) (menu.querySelector('[aria-current="true"]') || menu.querySelector("a")).focus();
  }
  btn.addEventListener("click", () => openMenu(menu.hidden));
  menu.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-type]");
    if (!a) return;
    e.preventDefault(); state.type = a.dataset.type; render(); openMenu(false); btn.focus();
  });
  menu.addEventListener("keydown", (e) => {
    const items = [...menu.querySelectorAll("a")], i = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    if (e.key === "Escape") { openMenu(false); btn.focus(); }
  });
  document.addEventListener("click", (e) => { if (!menu.hidden && !e.target.closest(".g-pick")) openMenu(false); });
  vatBtn.addEventListener("click", (e) => { e.preventDefault(); state.vat = !state.vat; render(); });
  vatBtn.addEventListener("keydown", (e) => { if (e.key === " ") { e.preventDefault(); vatBtn.click(); } });
})();

// Institution Blueprint preview: switch between the University, School and Hospital templates in place.
(() => {
  const demo = document.querySelector("[data-bp]");
  if (!demo) return;
  demo.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-bp-key]");
    if (!tab) return;
    e.preventDefault();
    const key = tab.dataset.bpKey;
    demo.querySelectorAll("[data-bp-key]").forEach((t) => t.setAttribute("aria-pressed", String(t === tab)));
    demo.querySelectorAll("[data-bp-panel]").forEach((p) => {
      const on = p.dataset.bpPanel === key;
      p.hidden = !on;
      if (on) { p.classList.remove("g-bp-in"); void p.offsetWidth; p.classList.add("g-bp-in"); }
    });
  });
  demo.addEventListener("keydown", (e) => {
    const tab = e.target.closest("[data-bp-key]");
    if (tab && e.key === " ") { e.preventDefault(); tab.click(); }
  });
})();

// Blueprint background tree. Each template's unit tree (read from its preview panel) becomes a line-art tree:
// the trunk ends in the root unit, every unit is a branch with a "fruit". Templates differ in height, spread
// and fruit shape. Switching morphs directly between trees: shared slots move, extra branches grow from (or
// shrink back into) their parent. Purely decorative; hidden on phones; instant for reduced motion.
(() => {
  const svg = document.querySelector("[data-bp-tree]"), demo = document.querySelector("[data-bp]");
  if (!svg || !demo) return;
  const NS = "http://www.w3.org/2000/svg";
  const STYLE = {   // h: trunk height, spread: branch length, angle: branch lift (deg), fruit: shape
    university: { h: .80, spread: .40, angle: 30, fruit: "ringdot" },
    school:     { h: .58, spread: .46, angle: 16, fruit: "solid" },
    hospital:   { h: .70, spread: .34, angle: 42, fruit: "double" },
  };
  const FRUIT = {   // outerFill, innerR (share of r), innerFill
    ringdot: [0, .36, 1], solid: [1, 0, 1], double: [0, .62, 0],
  };

  function read(panel) {               // nested <ul> -> {children:[...]}
    const walk = (ul) => [...ul.children].map((li) => {
      const sub = li.querySelector(":scope > ul");
      return { children: sub ? walk(sub) : [] };
    });
    return walk(panel.querySelector(".g-bp-tree"))[0];
  }

  function layout(key) {
    const st = STYLE[key] || STYLE.university, [of, ir, inf] = FRUIT[st.fruit];
    const root = read(demo.querySelector(`[data-bp-panel="${key}"]`));
    // Lay out in the section's own pixel size so the tree spans the whole width without stretching circles
    const W = svg.clientWidth || 1000, H = svg.clientHeight || 1000, cx = W / 2, unit = Math.min(1, W / 1300);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const base = { x: cx, y: H - 6 }, top = { x: cx, y: H - 6 - st.h * H };
    const segs = [{ x1: base.x, y1: base.y, x2: top.x, y2: top.y }];
    const fruits = [{ x: top.x, y: top.y, r: 46 * unit, of, ir, inf, root: 1 }];
    const kids = root.children, k = kids.length;
    kids.forEach((c, i) => {
      const side = i % 2 ? -1 : 1;
      const t = .28 + .62 * (i + .5) / k;                       // where along the trunk it starts
      const ax = cx, ay = base.y - (base.y - top.y) * t;
      const len = st.spread * W * (1.05 - .4 * (i / Math.max(1, k - 1)));
      const a = (st.angle + 6 * (i % 3)) * Math.PI / 180;
      const fx = ax + side * len * Math.cos(a), fy = ay - len * Math.sin(a);
      segs.push({ x1: ax, y1: ay, x2: fx, y2: fy });
      fruits.push({ x: fx, y: fy, r: 32 * unit, of, ir, inf, root: 0 });
      const g = c.children.length;
      c.children.forEach((_, j) => {
        const b = (st.angle + 10 + (j - (g - 1) / 2) * 34) * Math.PI / 180, l2 = len * .45;
        const gx = fx + side * l2 * Math.cos(b), gy = fy - l2 * Math.sin(b);
        segs.push({ x1: fx, y1: fy, x2: gx, y2: gy });
        fruits.push({ x: gx, y: gy, r: 24 * unit, of, ir, inf, root: 0 });
      });
    });
    return { segs, fruits };
  }

  // Element pools, reused across morphs
  const lines = [], groups = [];
  const lineEl = () => { const l = document.createElementNS(NS, "line"); svg.appendChild(l); lines.push(l); return l; };
  const fruitEl = () => {
    const g = document.createElementNS(NS, "g"), o = document.createElementNS(NS, "circle"), n = document.createElementNS(NS, "circle");
    o.setAttribute("class", "fo"); n.setAttribute("class", "fi"); g.append(o, n); svg.appendChild(g); groups.push(g); return g;
  };

  // A segment shrunk to its start point, a fruit shrunk to nothing at the same place
  const collapseSeg = (s) => ({ x1: s.x1, y1: s.y1, x2: s.x1, y2: s.y1 });
  const collapseFruit = (f, s) => ({ ...f, x: s ? s.x1 : f.x, y: s ? s.y1 : f.y, r: 0 });

  function draw(st) {
    while (lines.length < st.segs.length) lineEl();
    while (groups.length < st.fruits.length) fruitEl();
    lines.forEach((l, i) => {
      const s = st.segs[i];
      if (!s) { l.style.display = "none"; return; }
      l.style.display = "";
      // stop the branch at the fruit's edge so rings stay open, like the logo tree
      const f = st.fruits[i], dx = s.x2 - s.x1, dy = s.y2 - s.y1, d = Math.hypot(dx, dy) || 1, cut = f ? Math.min(f.r, d) : 0;
      l.setAttribute("x1", s.x1); l.setAttribute("y1", s.y1);
      l.setAttribute("x2", s.x2 - dx / d * cut); l.setAttribute("y2", s.y2 - dy / d * cut);
    });
    groups.forEach((g, i) => {
      const f = st.fruits[i];
      if (!f || f.r < .5) { g.style.display = "none"; return; }
      g.style.display = "";
      g.classList.toggle("root", !!f.root);
      const [o, n] = g.children;
      o.setAttribute("cx", f.x); o.setAttribute("cy", f.y); o.setAttribute("r", f.r);
      o.style.fillOpacity = (.04 + .22 * f.of).toFixed(3);
      n.setAttribute("cx", f.x); n.setAttribute("cy", f.y); n.setAttribute("r", Math.max(0, f.r * f.ir));
      n.style.fillOpacity = (.3 * f.inf).toFixed(3);
      n.style.strokeOpacity = f.ir > .05 ? "" : "0";
    });
  }

  const lerp = (a, b, t) => a + (b - a) * t;
  const mix = (A, B, t) => {
    const out = {};
    for (const k in B) out[k] = typeof B[k] === "number" ? lerp(A[k], B[k], t) : B[k];
    return out;
  };
  function blend(from, to, t) {
    const n = Math.max(from.segs.length, to.segs.length), segs = [], fruits = [];
    for (let i = 0; i < n; i++) {
      const a = from.segs[i], b = to.segs[i], fa = from.fruits[i], fb = to.fruits[i];
      if (a && b) { segs.push(mix(a, b, t)); fruits.push(mix(fa, fb, t)); }
      else if (b) { segs.push(mix(collapseSeg(b), b, t)); fruits.push(mix(collapseFruit(fb, b), fb, t)); }
      else if (t < 1) { segs.push(mix(a, collapseSeg(a), t)); fruits.push(mix(fa, collapseFruit(fa, a), t)); }
    }
    return { segs, fruits };
  }

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const ease = (t) => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  let current = layout((demo.querySelector('[data-bp-key][aria-pressed="true"]') || {}).dataset?.bpKey || "university"), frame = 0;
  draw(current);

  function morphTo(key) {
    const target = layout(key);
    cancelAnimationFrame(frame);
    if (reduce.matches) { current = target; draw(current); return; }
    const from = current, start = performance.now(), dur = 1100;
    const step = (now) => {
      const t = Math.min(1, (now - start) / dur);
      current = blend(from, target, ease(t)); draw(current);
      if (t < 1) frame = requestAnimationFrame(step); else current = target;
    };
    frame = requestAnimationFrame(step);
  }
  const activeKey = () => (demo.querySelector('[data-bp-key][aria-pressed="true"]') || {}).dataset?.bpKey || "university";
  demo.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-bp-key]");
    if (tab) morphTo(tab.dataset.bpKey);
  });
  let rt = 0;   // re-fit after a resize
  window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { cancelAnimationFrame(frame); current = layout(activeKey()); draw(current); }, 150); });
})();
