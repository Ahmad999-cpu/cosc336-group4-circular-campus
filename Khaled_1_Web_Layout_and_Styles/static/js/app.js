/* Circular Campus — shared behaviour for every page.
   No framework: HTMX swaps server-rendered HTML; this file adds the small interactions.
   Everything here is progressive: the pages work without it, only less smoothly. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  // Like $$, but also includes `root` itself when it matches (htmx:load hands us the new element).
  const within = (sel, root) => (root && root.matches && root.matches(sel) ? [root] : []).concat(root ? $$(sel, root) : []);
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CC = (window.CC = window.CC || {});

  /* ---------- toasts ---------- */
  const tickSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>';
  const bangSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" aria-hidden="true"><path d="M12 7v6M12 17h.01"/></svg>';
  CC.toast = function (text, opts) {
    opts = opts || {};
    const box = $("#toasts");
    if (!box) return;
    const el = document.createElement("div");
    el.className = "toast" + (opts.ok ? " ok" : "") + (opts.celebrate ? " celebrate" : "");
    const tick = document.createElement("span");
    tick.className = "tick";
    tick.innerHTML = opts.ok ? tickSvg : bangSvg;
    const span = document.createElement("span");
    span.textContent = text;
    el.append(tick, span);
    if (opts.href && opts.label) {
      const a = document.createElement("a");
      a.href = opts.href; a.textContent = opts.label;
      el.appendChild(a);
    }
    box.appendChild(el);
    while (box.children.length > 3) box.firstChild.remove();
    const ms = opts.ms || (opts.celebrate ? 6500 : 5500);
    el.style.setProperty("--toast-ms", ms + "ms");
    setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 300); }, ms);
    if (opts.celebrate) CC.burst(tick);
  };

  /* A small burst in the brand colours when something is reused: the one celebratory moment. */
  CC.burst = function (from) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !from.animate) return;
    const r = from.getBoundingClientRect();
    const colours = ["#E5323B", "#7EA6CE", "#D6E3F1", "#FFFFFF", "#0E1F3A"];
    for (let i = 0; i < 22; i++) {
      const p = document.createElement("span");
      p.className = "burst";
      p.style.background = colours[i % colours.length];
      p.style.left = r.left + r.width / 2 + "px"; p.style.top = r.top + r.height / 2 + "px";
      document.body.appendChild(p);
      const a = (Math.PI * 2 * i) / 22 + Math.random() * 0.4, d = 60 + Math.random() * 70;
      p.animate([{ transform: "translate(0,0) rotate(0) scale(1)", opacity: 1 },
                 { transform: `translate(${Math.cos(a) * d}px, ${Math.sin(a) * d - 30}px) rotate(${Math.random() * 360}deg) scale(.6)`, opacity: 0 }],
                { duration: 900 + Math.random() * 400, easing: "cubic-bezier(.2,.8,.2,1)" }).onfinish = () => p.remove();
    }
  };
  function flushMessages(root) {
    within("script[data-flash]", root).forEach((s) => {
      try { JSON.parse(s.textContent).forEach((m) => CC.toast(m.text, { ok: m.level === "success", href: m.href, label: m.label, celebrate: m.celebrate })); } catch (e) { /* ignore */ }
      s.remove();
    });
  }

  /* ---------- button ripple ---------- */
  document.addEventListener("pointerdown", (e) => {
    const btn = e.target.closest(".btn");
    if (!btn || btn.disabled || reduced) return;
    const r = btn.getBoundingClientRect(), d = Math.max(r.width, r.height);
    const s = document.createElement("span");
    s.className = "ripple";
    s.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`;
    btn.appendChild(s);
    setTimeout(() => s.remove(), 650);
  });

  /* ---------- disclosures: [data-toggle="<id>"] opens .collapse#id ---------- */
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-toggle]");
    if (!t) return;
    const box = document.getElementById(t.dataset.toggle);
    if (!box) return;
    const open = !box.classList.contains("open");
    box.classList.toggle("open", open);
    $$(`[data-toggle="${t.dataset.toggle}"]`).forEach((b) => b.setAttribute("aria-expanded", open));
    if (open) setTimeout(() => { const f = box.querySelector("textarea, input:not([type=hidden]), select"); if (f) f.focus(); }, 220);
  });

  /* ---------- drawer: HTMX loads content into #drawer, we slide it in ---------- */
  let lastFocus = null;
  CC.openDrawer = function () {
    const d = $("#drawer");
    lastFocus = document.activeElement;
    d.hidden = false;
    requestAnimationFrame(() => requestAnimationFrame(() => { d.classList.add("on"); $("#scrim").classList.add("on"); }));
    setTimeout(() => { const f = d.querySelector("[autofocus], [data-autofocus]") || d.querySelector(".close"); if (f) f.focus(); }, 80);
  };
  CC.closeDrawer = function () {
    const d = $("#drawer");
    if (!d || d.hidden) return;
    d.classList.remove("on"); $("#scrim").classList.remove("on");
    setTimeout(() => { d.hidden = true; d.innerHTML = ""; }, 380);
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  };
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-drawer-close]") || e.target.id === "scrim") CC.closeDrawer();
  });

  /* ---------- notifications popover ---------- */
  document.addEventListener("click", (e) => {
    const bell = e.target.closest("#bell");
    const pop = $("#notes");
    if (!pop) return;
    if (bell) {
      const open = pop.hidden;
      pop.hidden = !open; bell.setAttribute("aria-expanded", String(open));
      return;
    }
    if (!e.target.closest("#notes")) { pop.hidden = true; const b = $("#bell"); if (b) b.setAttribute("aria-expanded", "false"); }
  });

  /* ---------- keyboard: Esc closes, Tab stays inside an open drawer ---------- */
  document.addEventListener("keydown", (e) => {
    const d = $("#drawer");
    if (e.key === "Escape") {
      CC.closeDrawer();
      const pop = $("#notes"); if (pop) pop.hidden = true;
    }
    if (e.key === "Tab" && d && !d.hidden) {
      const f = $$("button, input, select, textarea, a[href]", d).filter((x) => !x.disabled && x.offsetParent !== null);
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  /* ---------- example chips fill a field: <button data-fill="need" data-value="..."> ---------- */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-fill]");
    if (!b) return;
    const f = document.getElementById(b.dataset.fill);
    if (!f) return;
    f.value = b.dataset.value;
    f.focus();
    f.dispatchEvent(new Event("input", { bubbles: true }));
  });

  /* ---------- AI suggestions: <button data-ai-use="field-id" data-value="…" data-mode="append" data-key="tags"> ---------- */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-ai-use]");
    if (!b) return;
    const f = document.getElementById(b.dataset.aiUse);
    if (!f) return;
    if (b.dataset.mode === "append") {
      const have = f.value.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
      const add = b.dataset.value.split(",").map((x) => x.trim()).filter((x) => x && !have.includes(x.toLowerCase()));
      f.value = [f.value.trim(), add.join(", ")].filter(Boolean).join(", ");
      const hidden = document.getElementById("ai-tags");
      if (hidden) hidden.value = [hidden.value, add.join(",")].filter(Boolean).join(",");
    } else {
      f.value = b.dataset.value;
    }
    f.dispatchEvent(new Event("change", { bubbles: true }));
    f.classList.add("ai-filled");
    const used = document.getElementById("ai-used");
    if (used && b.dataset.key && !used.value.split(",").includes(b.dataset.key)) used.value = [used.value, b.dataset.key].filter(Boolean).join(",");
    b.disabled = true;
    b.textContent = document.documentElement.lang === "ar" ? "تم ✓" : "Used ✓";
  });

  /* ---------- range inputs that mirror their value: <input type="range" data-mirror="out-id"> ---------- */
  document.addEventListener("input", (e) => {
    const r = e.target.closest("[data-mirror]");
    if (!r) return;
    const out = document.getElementById(r.dataset.mirror);
    if (out) out.textContent = Number(r.value).toLocaleString(document.documentElement.lang === "ar" ? "ar-AE" : "en");
  });

  /* ---------- switches that show a hidden block: <input type="checkbox" data-show="id"> ---------- */
  document.addEventListener("change", (e) => {
    const t = e.target.closest("[data-show]");
    if (!t) return;
    const box = document.getElementById(t.dataset.show);
    if (box) { box.hidden = !t.checked; if (t.checked) init(box); }
  });

  /* ---------- quantity steppers: <div class="stepper-qty" data-max="4"> ---------- */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-step]");
    if (!b) return;
    const wrap = b.closest(".stepper-qty"), input = wrap.querySelector("input");
    const max = +wrap.dataset.max || 9999, min = +wrap.dataset.min || 1;
    input.value = Math.min(max, Math.max(min, (+input.value || min) + (+b.dataset.step)));
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });

  /* ---------- score rings and counters animate when they appear ---------- */
  function animateRings(root) {
    within(".ring .val[data-to]", root).forEach((c) => {
      if (reduced) { c.style.transition = "none"; }
      requestAnimationFrame(() => requestAnimationFrame(() => { c.style.strokeDashoffset = c.dataset.to; }));
    });
  }
  function countUp(el) {
    const to = +el.dataset.count, fmt = new Intl.NumberFormat(document.documentElement.lang === "ar" ? "ar-AE" : "en-AE");
    if (reduced || !isFinite(to)) { el.textContent = fmt.format(to); return; }
    const start = performance.now(), dur = 900;
    const step = (now) => {
      const p = Math.min(1, (now - start) / dur), k = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt.format(Math.round(to * k));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  const io = "IntersectionObserver" in window ? new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      en.target.classList.add("reveal-in");
      io.unobserve(en.target);
    });
  }, { rootMargin: "0px 0px -40px 0px" }) : null;
  function init(root) {
    root = root || document;
    flushMessages(root);
    animateRings(root);
    within("[data-count]", root).forEach(countUp);
    if (io && !reduced) within("[data-reveal]", root).forEach((el) => { if (el.getBoundingClientRect().top > window.innerHeight) io.observe(el); });
    within("[data-autosubmit]", root).forEach((f) => {
      if (f.dataset.bound) return;
      f.dataset.bound = "1";
      f.addEventListener("change", () => (f.requestSubmit ? f.requestSubmit() : f.submit()));
    });
  }
  CC.init = init;

  /* ---------- HTMX glue ---------- */
  /* ---------- live badges: menu counts and the bell (cc:refresh after an action, and every minute) ---------- */
  CC.refreshBadges = () => {
    if (!document.querySelector("#bell")) return;
    fetch("/badges/", { headers: { "X-Requested-With": "fetch", "X-Background": "1" }, credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d) return;
        Object.entries(d.nav || {}).forEach(([key, n]) => {
          const c = document.querySelector(`[data-nav="${key}"] .count`);
          if (!c) return;
          if (c.textContent !== String(n)) { c.textContent = n; c.classList.remove("bump"); void c.offsetWidth; c.classList.add("bump"); }
          c.hidden = !n;
        });
        const dot = document.querySelector("#bell .dot");
        if (dot) { dot.textContent = d.unread; dot.hidden = !d.unread; }
      })
      .catch(() => {});
  };
  document.body.addEventListener("cc:refresh", CC.refreshBadges);
  setInterval(() => { if (!document.hidden) CC.refreshBadges(); }, 60000);

  /* ---------- a live progress line while any HTMX request is in flight (background refreshes excluded) ---------- */
  let inflight = 0, progressTimer = null;
  const progress = () => document.getElementById("progress");
  document.addEventListener("htmx:beforeRequest", (e) => {
    if ((e.detail.requestConfig && e.detail.requestConfig.headers || {})["X-Background"] === "1") return;
    inflight++;
    clearTimeout(progressTimer);
    progressTimer = setTimeout(() => { const p = progress(); if (p && inflight) p.classList.add("on"); }, 120);  // quick swaps stay calm
  });
  document.addEventListener("htmx:afterRequest", (e) => {
    if ((e.detail.requestConfig && e.detail.requestConfig.headers || {})["X-Background"] === "1") return;
    inflight = Math.max(0, inflight - 1);
    if (!inflight) { clearTimeout(progressTimer); const p = progress(); if (p) p.classList.remove("on"); }
  });

  // htmx:load fires for every piece of new content, including outerHTML swaps whose old target is gone.
  document.addEventListener("htmx:load", (e) => { if (e.detail.elt !== document.body) init(e.detail.elt); });
  document.addEventListener("htmx:afterSwap", (e) => {
    if (e.detail.target.id === "drawer") CC.openDrawer();
  });
  document.addEventListener("htmx:responseError", (e) => {
    const msg = document.documentElement.lang === "ar" ? "تعذّر إكمال الطلب. أعد تحميل الصفحة وحاول مجددًا." : "That didn't go through. Reload the page and try again.";
    CC.toast(msg);
  });
  // Feature 1: "Print label" on the QR page (no inline script, so it keeps working under a strict CSP).
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-print]")) window.print();
  });
  document.addEventListener("cc:toast", (e) => CC.toast(e.detail.text, e.detail));
  document.addEventListener("cc:close-drawer", () => CC.closeDrawer());

  document.addEventListener("DOMContentLoaded", () => init(document));
})();
