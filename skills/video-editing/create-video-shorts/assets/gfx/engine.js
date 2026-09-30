/* World engine for the luxury-tech shorts graphics.
   One bright world of floating white cards + a world camera, driven purely by time (seek-safe).
   CFG is defined by the page before this script loads. */
(function () {
  const W = 1080, H = 1920, RFPS = 240;
  const cfg = window.CFG;
  const anchor = cfg.anchor || (cfg.mode === 'split' ? [540, 470] : [540, 720]);
  const ease = (name) => (name === 'linear' ? (p) => p : gsap.parseEase(name));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const $ = (id) => document.getElementById(id);

  /* ---------- world camera ---------- */
  // moves: [{t, dur, ease, to:{x,y,s}, kind}] ; kind 'whip' => {t, to, via} (0.45 out power3.in, 0.6 in power3.out)
  const moves = (cfg.moves || []).slice().sort((a, b) => a.t - b.t);
  const cam0 = Object.assign({ x: 540, y: 470, s: 1 }, cfg.cam0 || {});
  function camAt(t) {
    let c = { ...cam0 };
    for (const m of moves) {
      if (t <= m.t) break;
      if (m.kind === 'whip') {
        const out = m.out || 0.45, inn = m.in || 0.6;
        const via = m.via || { x: (c.x + m.to.x) / 2, y: (c.y + m.to.y) / 2, s: Math.min(c.s, m.to.s) * 0.92 };
        if (t < m.t + out) { const p = ease('power3.in')((t - m.t) / out); return mix(c, via, p); }
        if (t < m.t + out + inn) { const p = ease('power3.out')((t - m.t - out) / inn); return mix(via, m.to, p); }
        c = { ...c, ...m.to }; continue;
      }
      const p = clamp((t - m.t) / m.dur, 0, 1);
      const e = ease(m.ease || defEase(m.kind))(p);
      if (p < 1) return mix(c, { ...c, ...m.to }, e);
      c = { ...c, ...m.to };
    }
    return c;
  }
  function defEase(kind) { return { step: 'power3.inOut', push: 'power2.inOut', pull: 'power2.inOut', glide: 'sine.inOut' }[kind] || 'power2.inOut'; }
  function mix(a, b, p) {
    // interpolate scale geometrically so zooms feel even
    return { x: lerp(a.x, b.x, p), y: lerp(a.y, b.y, p), s: a.s * Math.pow(b.s / a.s, p) };
  }
  const toScreen = (c, x, y) => [anchor[0] + c.s * (x - c.x), anchor[1] + c.s * (y - c.y)];

  /* ---------- heroes / depth of field ---------- */
  const heroes = (cfg.heroes || []).slice().sort((a, b) => a.t - b.t);
  function heroAt(t) { let h = null, prev = null, since = -9; for (const e of heroes) { if (t >= e.t) { prev = h; h = e.id; since = e.t; } } return { h, prev, since }; }
  function pushAmount(c) { const ref = cfg.pushRef || cam0.s; return clamp((c.s / ref - 1) / 0.45, 0, 1); }

  /* ---------- cards ---------- */
  const cards = cfg.cards || [];
  const cardById = {};
  const world = $('world');
  const RADIUS = { media: (w) => Math.round(w * 0.03), doc: () => 40, tile: () => 72, phone: () => 84, capture: () => 36, logo: () => 0, plain: () => 0 };
  const SHADOW = '0 60px 120px rgba(24,24,32,.16), 0 24px 48px rgba(24,24,32,.10), 0 4px 10px rgba(24,24,32,.06)';
  for (const c of cards) {
    const el = document.createElement('div');
    el.className = 'card ' + (c.kind || 'plain');
    el.id = 'card-' + c.id;
    const r = c.radius != null ? c.radius : (RADIUS[c.kind] || RADIUS.plain)(c.w);
    Object.assign(el.style, { left: c.x - c.w / 2 + 'px', top: c.y - c.h / 2 + 'px', width: c.w + 'px', height: c.h + 'px', borderRadius: r + 'px' });
    if (c.kind !== 'logo' && c.kind !== 'plain') { el.style.background = c.bg || '#fff'; el.style.boxShadow = SHADOW; }
    if (c.clip !== false && c.kind !== 'logo') el.style.overflow = 'hidden';
    if (c.img) {
      const im = document.createElement('img'); im.src = c.img; im.id = 'img-' + c.id; im.className = 'footage';
      if (c.inner) { Object.assign(im.style, { position: 'absolute', left: 0, top: 0, width: c.fw + 'px', height: c.fh + 'px', transformOrigin: '0 0' }); }
      else { Object.assign(im.style, { width: '100%', height: '100%', objectFit: c.fit || 'cover', objectPosition: c.pos || 'center' }); }
      el.appendChild(im);
    }
    if (c.html) { const d = document.createElement('div'); d.className = 'inner'; d.innerHTML = c.html; el.appendChild(d); }
    if (c.overlay) { const o = document.createElement('div'); o.id = 'ov-' + c.id; Object.assign(o.style, { position: 'absolute', left: 0, top: 0, width: c.fw + 'px', height: c.fh + 'px', transformOrigin: '0 0' }); o.innerHTML = c.overlay; el.appendChild(o); }
    world.appendChild(el);
    c.el = el; c.r = r; cardById[c.id] = c;
  }

  /* inner camera for footage inside a card: keyframes [{t,dur,ease,fx,fy,k}] ; fx,fy footage px at card centre, k = css px per footage px */
  function innerAt(c, t) { const s = innerRaw(c, t); const hw = c.w / 2 / s.k, hh = c.h / 2 / s.k;
    return { k: s.k, fx: c.fw > 2 * hw ? clamp(s.fx, hw, c.fw - hw) : c.fw / 2, fy: c.fh > 2 * hh ? clamp(s.fy, hh, c.fh - hh) : c.fh / 2 }; }
  function innerRaw(c, t) {
    const ks = c.inner || [];
    let s = { fx: c.fw / 2, fy: c.fh / 2, k: Math.max(c.w / c.fw, c.h / c.fh) };
    if (c.inner0) s = { ...s, ...c.inner0 };
    for (const m of ks) {
      if (t <= m.t) break;
      const p = clamp((t - m.t) / (m.dur || 0.55), 0, 1), e = ease(m.ease || 'power2.inOut')(p);
      const to = { fx: m.fx != null ? m.fx : s.fx, fy: m.fy != null ? m.fy : s.fy, k: m.k != null ? m.k : s.k };
      if (p < 1) return { fx: lerp(s.fx, to.fx, e), fy: lerp(s.fy, to.fy, e), k: s.k * Math.pow(to.k / s.k, e) };
      s = to;
    }
    return s;
  }

  /* landing animation (dull pop) */
  function landAt(c, t) {
    if (!c.land) return { o: 1, sc: 1, dy: 0 };
    const p = clamp((t - c.land.t) / (c.land.dur || 0.55), 0, 1);
    const e = ease('power3.out')(p);
    return { o: clamp(p * 2.2, 0, 1), sc: lerp(0.92, 1, e), dy: lerp(70, 0, e) };
  }
  function exitAt(c, t) {
    if (!c.exit) return 1;
    return 1 - clamp((t - c.exit.t) / (c.exit.dur || 0.35), 0, 1);
  }

  /* ---------- videos (must be direct root children) ---------- */
  const vids = {};
  document.querySelectorAll('video[data-card]').forEach((v) => { vids[v.dataset.card] = v; });
  const bdVid = document.querySelector('video[data-backdrop]');
  const bdImg = $('bd-img');

  /* ---------- helpers ---------- */
  function mbFilter(el, vx, vy, key, div) {
    div = div || 1;
    const sp = Math.hypot(vx, vy);
    const sig = Math.min(24, 0.29 * sp * 0.75 / 60);
    const f = $('mbg-' + key);
    if (sig < 0.15 || !f) { if (f) f.setAttribute('stdDeviation', '0 0'); return false; }
    const sx = sig * Math.abs(vx) / sp / div, sy = sig * Math.abs(vy) / sp / div;
    f.setAttribute('stdDeviation', sx.toFixed(2) + ' ' + sy.toFixed(2));
    return true;
  }
  function footageScreenXform(c, t, cam, land) {
    // returns {S, Tx, Ty} mapping footage px -> screen, and card screen rect
    const inn = innerAt(c, t);
    const cx = c.x, cy = c.y + land.dy;
    const sc = cam.s * land.sc;
    const [scx, scy] = toScreen(cam, cx, cy);
    const S = sc * inn.k;
    const Tx = scx - S * inn.fx, Ty = scy - S * inn.fy;
    const hw = c.w / 2 * sc, hh = c.h / 2 * sc;
    return { S, Tx, Ty, rect: [scx - hw, scy - hh, scx + hw, scy + hh], rad: c.r * sc, inn };
  }

  /* ---------- typing / reveal ---------- */
  const typings = (cfg.typings || []).map((ty) => ({ ...ty, el: $(ty.el) }));
  const reveals = (cfg.reveals || []).map((r) => ({ ...r, el: $(r.el) }));

  /* ---------- per-frame render ---------- */
  function render(t) {
    const cam = camAt(t), camp = camAt(Math.max(0, t - 1 / RFPS));
    world.style.transform = `translate(${anchor[0] - cam.s * cam.x}px,${anchor[1] - cam.s * cam.y}px) scale(${cam.s})`;
    const { h, prev, since } = heroAt(t);
    const push = pushAmount(cam);
    const heroP = clamp((t - since) / 0.5, 0, 1);
    // world motion blur: screen velocity of the hero centre (or anchor)
    const hc = h && h !== 'none' && cardById[h] ? cardById[h] : null;
    const px = hc ? hc.x : cam.x, py = hc ? hc.y : cam.y;
    const a = toScreen(cam, px, py), b = toScreen(camp, px, py);
    const vx = (a[0] - b[0]) * RFPS, vy = (a[1] - b[1]) * RFPS;
    const moving = mbFilter(null, vx, vy, 'world');
    $('viewport').style.filter = moving ? 'url(#mb-world)' : 'none';

    for (const c of cards) {
      const land = landAt(c, t);
      let blur = 0, op = land.o * exitAt(c, t);
      if (!c.noDof && h === 'none') { blur = 14 * push; op *= 1 - 0.3 * push; }
      else if (!c.noDof && h) {
        if (c.id === h) { blur = 0; }
        else if (c.id === prev) { blur = 9 * heroP; op *= lerp(1, 0.4, heroP); }
        else if (c.group && cardById[h] && cardById[h].group === c.group && c.sharpWithGroup) { blur = 0; }
        else { blur = 14 * push; op *= 1 - 0.3 * push; }
      }
      if (c.forceSharp) blur = 0;
      c.el.style.opacity = op;
      c.el.style.filter = blur > 0.05 ? `blur(${(blur / cam.s).toFixed(2)}px)` : 'none';
      c.el.style.transform = `translateY(${land.dy}px) scale(${land.sc})`;
      // footage inside card
      if (c.inner || vids[c.id]) {
        const X = footageScreenXform(c, t, cam, land);
        const Xp = footageScreenXform(c, Math.max(0, t - 1 / RFPS), camp, landAt(c, Math.max(0, t - 1 / RFPS)));
        // velocity of the footage point at the card centre
        const fx = X.inn.fx, fy = X.inn.fy;
        const ivx = ((X.Tx + X.S * fx) - (Xp.Tx + Xp.S * fx)) * RFPS, ivy = ((X.Ty + X.S * fy) - (Xp.Ty + Xp.S * fy)) * RFPS;
        if (vids[c.id]) {
          const v = vids[c.id];
          const [x0, y0, x1, y1] = X.rect;
          const S = X.S;
          v.style.transform = `translate(${X.Tx}px,${X.Ty}px) scale(${S})`;
          const ins = [(y0 - X.Ty) / S, c.fw - (x1 - X.Tx) / S, c.fh - (y1 - X.Ty) / S, (x0 - X.Tx) / S];
          v.style.clipPath = `inset(${ins[0]}px ${ins[1]}px ${ins[2]}px ${ins[3]}px round ${X.rad / S}px)`;
          v.style.opacity = op;
          const mv = mbFilter(null, ivx, ivy, c.id, S);
          const parts = [];
          if (mv) parts.push(`url(#mb-${c.id})`);
          if (blur > 0.05) parts.push(`blur(${(blur / S).toFixed(2)}px)`);
          v.style.filter = parts.length ? parts.join(' ') : 'none';
        } else {
          const im = $('img-' + c.id);
          const inn = X.inn;
          const ox = c.w / 2 - inn.k * inn.fx, oy = c.h / 2 - inn.k * inn.fy;
          im.style.transform = `translate(${ox}px,${oy}px) scale(${inn.k})`;
          const ovl = $('ov-' + c.id); if (ovl) ovl.style.transform = im.style.transform;
          const mv = mbFilter(null, ivx, ivy, c.id, inn.k * cam.s * land.sc);
          im.style.filter = mv ? `url(#mb-${c.id})` : 'none';
        }
        // capture backdrop follows the footage
        if (c.backdrop) {
          const bd = c.backdrop; // {tIn, tOut}
          let bo = clamp((t - (bd.tIn != null ? bd.tIn : -1)) / 0.35, 0, 1);
          if (bd.tOut != null) bo *= 1 - clamp((t - bd.tOut) / 0.35, 0, 1);
          const E = 1.18; // enlarged clone
          const cxs = anchor[0], cys = anchor[1];
          const S2 = X.S * E, Tx2 = cxs - S2 * X.inn.fx, Ty2 = cys - S2 * X.inn.fy;
          const target = bdVid || bdImg;
          if (target) {
            target.style.transform = `translate(${Tx2}px,${Ty2}px) scale(${S2})`;
            target.style.filter = `blur(${(40 / S2).toFixed(2)}px) saturate(.7) brightness(1.05)`;
            target.style.opacity = bo;
            $('bd-wash').style.opacity = bo * 0.72;
          }
        }
      }
    }
    for (const ty of typings) {
      const n = clamp(Math.floor((t - ty.t0) * (ty.cps || 22)), 0, ty.text.length);
      const blinkOn = (t < ty.t0) || n < ty.text.length || Math.floor((t - ty.t0) * 2.2) % 2 === 0;
      ty.el.innerHTML = escapeHtml(ty.text.slice(0, n)) + (ty.caret === false ? '' : `<span class="caret" style="opacity:${blinkOn ? 1 : 0}"></span>`);
    }
    for (const r of reveals) {
      const p = ease(r.ease || 'power3.out')(clamp((t - r.t) / (r.dur || 0.5), 0, 1));
      if (r.type === 'scaleX') r.el.style.transform = `scaleX(${p})`;
      else if (r.type === 'fade') r.el.style.opacity = p;
      else if (r.type === 'pop') { r.el.style.opacity = clamp(p * 2, 0, 1); r.el.style.transform = `scale(${lerp(0.6, 1, p)})`; }
      else if (r.type === 'fadeout') r.el.style.opacity = 1 - p;
    }
    if (window.CFG_RENDER) window.CFG_RENDER(t, cam);
  }
  function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  const st = { _t: 0 };
  Object.defineProperty(st, 't', { get() { return this._t; }, set(v) { this._t = v; render(v); } });
  const tl = gsap.timeline({ paused: true });
  tl.fromTo(st, { t: 0 }, { t: cfg.dur, duration: cfg.dur, ease: 'none' }, 0);
  window.__timelines[cfg.id] = tl;
  window.__render = render; window.__camAt = camAt;
  render(0);
})();
