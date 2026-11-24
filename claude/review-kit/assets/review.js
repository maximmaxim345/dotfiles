(() => {
const KIT = JSON.parse(document.getElementById('kit-data').textContent);
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const escLine = s => esc(s).replace(/\r/g, '<span class="cr" title="carriage return">\u240d</span>');
const EOL = '<span class="eol">No newline at end of file</span>';

const TOK_CODE = /\s+|[A-Za-z0-9_]+|[^\sA-Za-z0-9_]/g;
const TOK_WORDS = /\n|[^\S\n]+|[\p{L}\p{N}_'’]+|[^\s\p{L}\p{N}_]/gu;
const STEP = 20;
const LCS_LIMIT = 4e6;

function load(key, fallback) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
}

const PREFS = 'review-kit:prefs';
const PAGE = 'review-kit:page:' + KIT.key;
const prefs = Object.assign({ wrap: false, layout: 'auto', order: 'reading' }, load(PREFS, {}));
const page = Object.assign({ comments: [], picks: {}, nextId: 1 }, load(PAGE, {}));
const ui = { open: null, expand: {}, view: {}, tray: false, mark: null, slots: {} };
const persist = () => save(PAGE, page);

function lcsPairs(a, b, eq) {
  let p = 0;
  while (p < a.length && p < b.length && eq(a[p], b[p])) p++;
  let s = 0;
  while (s < a.length - p && s < b.length - p && eq(a[a.length - 1 - s], b[b.length - 1 - s])) s++;
  const out = [];
  for (let i = 0; i < p; i++) out.push([i, i]);
  const A = a.slice(p, a.length - s), B = b.slice(p, b.length - s);
  const n = A.length, m = B.length;
  if (n && m && n * m <= LCS_LIMIT) {
    const dp = [];
    for (let i = 0; i <= n; i++) dp.push(new Int32Array(m + 1));
    for (let i = n - 1; i >= 0; i--)
      for (let j = m - 1; j >= 0; j--)
        dp[i][j] = eq(A[i], B[j]) ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (eq(A[i], B[j])) { out.push([i + p, j + p]); i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
      else j++;
    }
  }
  for (let k = s; k > 0; k--) out.push([a.length - k, b.length - k]);
  return out;
}

function segs(toks, changed) {
  for (let i = 1; i < toks.length - 1; i++)
    if (!changed[i] && !toks[i].trim() && changed[i - 1] && changed[i + 1]) changed[i] = true;
  const out = [];
  toks.forEach((t, i) => {
    const last = out[out.length - 1];
    if (last && last[1] === changed[i]) last[0] += t; else out.push([t, changed[i]]);
  });
  return out;
}

function wordDiff(a, b) {
  const ta = a.match(TOK_CODE) || [], tb = b.match(TOK_CODE) || [];
  const pairs = lcsPairs(ta, tb, (x, y) => x === y);
  const ca = ta.map(() => true), cb = tb.map(() => true);
  let same = 0;
  for (const [i, j] of pairs) { ca[i] = false; cb[j] = false; if (ta[i].trim()) same += ta[i].length; }
  const tot = (a.replace(/\s/g, '').length + b.replace(/\s/g, '').length) / 2 || 1;
  return { a: segs(ta, ca), b: segs(tb, cb), sim: same / tot };
}

function mergedDiff(a, b) {
  const ta = a.match(TOK_WORDS) || [], tb = b.match(TOK_WORDS) || [];
  const pairs = lcsPairs(ta, tb, (x, y) => x === y);
  const out = [];
  let i = 0, j = 0;
  const push = (t, k) => { const l = out[out.length - 1]; if (l && l[1] === k) l[0] += t; else out.push([t, k]); };
  for (const [pi, pj] of pairs) {
    while (i < pi) push(ta[i++], 'del');
    while (j < pj) push(tb[j++], 'add');
    push(ta[i], 'same'); i++; j++;
  }
  while (i < ta.length) push(ta[i++], 'del');
  while (j < tb.length) push(tb[j++], 'add');
  return out;
}

function colored(s, toks, from = 0, to = s.length) {
  if (!toks || !toks.length) return escLine(s.slice(from, to));
  let out = '', at = 0;
  for (let i = 0; i < toks.length && at < to; i += 2) {
    const a = Math.max(at, from), b = Math.min(at + toks[i], to);
    if (a < b) { const t = escLine(s.slice(a, b)); out += toks[i + 1] ? `<span class="t-${toks[i + 1]}">${t}</span>` : t; }
    at += toks[i];
  }
  return out;
}

function renderSegs(sg, cls, s, toks) {
  let at = 0;
  return sg.map(([t, c]) => {
    const html = colored(s, toks, at, at + t.length);
    at += t.length;
    return c ? `<span class="${cls}">${html}</span>` : html;
  }).join('');
}

function blocks(h) {
  let o = h.oldStart, n = h.newStart, cur = null;
  const out = [], eol = new Set(h.noNewline);
  h.lines.forEach(([t, s], i) => {
    const e = eol.has(i), k = h.hl && h.hl[i];
    if (t === ' ') { cur = null; out.push({ ctx: true, o: o++, n: n++, s, e, k }); return; }
    if (!cur) { cur = { ctx: false, R: [], A: [] }; out.push(cur); }
    if (t === '-') cur.R.push({ o: o++, s, e, k }); else cur.A.push({ n: n++, s, e, k });
  });
  return out;
}

function align(R, A) {
  const pairs = lcsPairs(R, A, (x, y) => x.s.trim() !== '' && x.s.trim() === y.s.trim());
  const ops = [];
  let i = 0, j = 0;
  for (const [pi, pj] of pairs) {
    ops.push({ R: R.slice(i, pi), A: A.slice(j, pj) });
    ops.push({ R: [R[pi]], A: [A[pj]] });
    i = pi + 1; j = pj + 1;
  }
  ops.push({ R: R.slice(i), A: A.slice(j) });
  return ops.filter(op => op.R.length || op.A.length);
}

function changeRows(b) {
  const rows = [];
  for (const op of align(b.R, b.A)) {
    const k = Math.max(op.R.length, op.A.length);
    for (let i = 0; i < k; i++) {
      const r = op.R[i], a = op.A[i];
      let l = r ? colored(r.s, r.k) : null, rr = a ? colored(a.s, a.k) : null;
      if (r && a) {
        const w = wordDiff(r.s, a.s);
        if (w.sim >= 0.4) { l = renderSegs(w.a, 'dw', r.s, r.k); rr = renderSegs(w.b, 'aw', a.s, a.k); }
      }
      if (r && r.e) l += EOL;
      if (a && a.e) rr += EOL;
      rows.push({ t: 'chg', o: r ? r.o : null, n: a ? a.n : null, l, r: rr });
    }
  }
  return rows;
}

function toUnified(rows) {
  const out = [];
  let dels = [], adds = [];
  const flush = () => { out.push(...dels, ...adds); dels = []; adds = []; };
  for (const r of rows) {
    if (r.t !== 'chg') { flush(); out.push({ t: r.t, o: r.o, n: r.n, c: r.r }); continue; }
    if (r.l !== null) dels.push({ t: 'del', o: r.o, n: null, c: r.l });
    if (r.r !== null) adds.push({ t: 'add', o: null, n: r.n, c: r.r });
  }
  flush();
  return out;
}

function windowRows(w, from, to) {
  const rows = [];
  for (let i = from; i < to; i++) {
    const s = colored(w.lines[i], w.hl && w.hl[i]);
    rows.push({ t: 'ctx', o: w.old + i, n: w.new + i, l: s, r: s });
  }
  return rows;
}

function isSplit() {
  return prefs.layout === 'split' || (prefs.layout === 'auto' && window.innerWidth >= 900);
}

const keyOf = r => (r.n != null ? 'R' + r.n : 'L' + r.o);
const labelOf = (h, key) => key[0] === 'R' ? `${h.path}:${key.slice(1)}` : `${h.path}:${key.slice(1)} (removed line)`;

function rangeOf(h) {
  if (!h.lines.length) return '';
  if (h.newCount) return h.newCount > 1 ? `${h.newStart}-${h.newStart + h.newCount - 1}` : `${h.newStart}`;
  return `removed at old ${h.oldStart}-${h.oldStart + h.oldCount - 1}`;
}

function commentsHtml(match, open) {
  let out = '';
  for (const c of page.comments.filter(match)) {
    out += `<div class="cmt"><div class="cmeta">${c.key[0] === 'F' ? 'Your reply' : 'Your comment on ' + esc(c.label)}</div><div class="txt">${esc(c.text)}</div><button class="linkbtn" data-del="${c.id}">Remove</button></div>`;
  }
  if (open) {
    out += `<div class="cbox"><div class="cmeta">${open.key[0] === 'F' ? 'Reply to the author' : 'Comment on ' + esc(open.label)}</div><textarea aria-label="Comment"></textarea><div class="row"><button class="btn primary" data-save>Save comment</button><button class="btn" data-cancel>Cancel</button></div></div>`;
  }
  return out;
}

function rowComments(hid, key) {
  const open = ui.open && ui.open.hunk === hid && ui.open.key === key ? ui.open : null;
  return commentsHtml(c => c.hunk === hid && c.key === key, open);
}

function cell(html) {
  if (html == null) return '';
  if (!prefs.wrap) return html;
  const lead = html.match(/^(?:<[^>]*>|[ \t])*/)[0];
  const n = lead.replace(/<[^>]*>/g, '').replace(/\t/g, '    ').length;
  return `<div class="hi" style="--i:${n}">${lead.replace(/(<[^>]*>)|[ \t]/g, (_, tag) => tag || '')}${html.slice(lead.length)}</div>`;
}

function expandRow(id, dir, w, shown, bare) {
  const embedded = w.lines.length - shown;
  const hidden = embedded + w.more;
  if (!hidden) return '';
  const where = dir === 'up' ? 'above' : 'below';
  const btn = embedded
    ? `<button class="linkbtn" data-expand="${id}:${dir}">Show ${Math.min(STEP, embedded)} more lines ${where}</button>`
    : '';
  const rest = embedded ? `${hidden} unchanged lines ${where}` : `${hidden} more unchanged lines ${where} are not included in this page`;
  const inner = `${btn}<span class="small muted">${rest}</span>`;
  return bare ? `<div class="exp">${inner}</div>` : `<tr class="exp"><td colspan="4">${inner}</td></tr>`;
}

const scroller = table => `<div class="sx"><div class="dscroll">${table}</div></div>`;

function sideRows(rows, side) {
  return rows.map(r => {
    const html = side === 'l' ? r.l : r.r;
    const cls = r.t === 'chg' ? (html === null ? 'empty' : side === 'l' ? 'del' : 'add') : '';
    return `<tr class="cl" data-key="${keyOf(r)}"><td class="ln ${cls}">${(side === 'l' ? r.o : r.n) ?? ''}</td><td class="c ${cls}">${html === null ? '&nbsp;' : html}</td></tr>`;
  }).join('');
}

// With wrap off, each side of a split diff scrolls on its own. Comments sit between the scrolling parts.
function renderPairs(id, rows) {
  let out = '', part = [];
  const flush = () => {
    if (part.length) out += `<div class="pair">${scroller(`<table class="d">${sideRows(part, 'l')}</table>`)}${scroller(`<table class="d">${sideRows(part, 'r')}</table>`)}</div>`;
    part = [];
  };
  for (const r of rows) {
    part.push(r);
    const cm = rowComments(id, keyOf(r));
    if (cm) { flush(); out += `<div class="pcm">${cm}</div>`; }
  }
  flush();
  return out;
}

function renderTable(id, h) {
  const split = isSplit() && h.lines.some(([t]) => t === '-');
  const ex = ui.expand[id] || { up: 0, down: 0 };
  let rows = [];
  const up = h.above ? Math.min(ex.up, h.above.lines.length) : 0;
  const down = h.below ? Math.min(ex.down, h.below.lines.length) : 0;
  if (h.above) rows.push(...windowRows(h.above, h.above.lines.length - up, h.above.lines.length));
  for (const b of blocks(h)) {
    if (b.ctx) { const s = colored(b.s, b.k) + (b.e ? EOL : ''); rows.push({ t: 'ctx', o: b.o, n: b.n, l: s, r: s }); }
    else rows.push(...changeRows(b));
  }
  if (h.below) rows.push(...windowRows(h.below, 0, down));
  if (split && !prefs.wrap) {
    return '<div class="pairs">' + (h.above ? expandRow(id, 'up', h.above, up, true) : '') + renderPairs(id, rows)
      + (h.below ? expandRow(id, 'down', h.below, down, true) : '') + '</div>';
  }
  if (!split) rows = toUnified(rows);
  let t = split ? '<table class="d split"><colgroup><col class="lnc"><col><col class="lnc"><col></colgroup>' : '<table class="d">';
  if (h.above) t += expandRow(id, 'up', h.above, up);
  for (const r of rows) {
    const key = keyOf(r);
    if (split) {
      const lc = r.t === 'chg' ? (r.l === null ? 'empty' : 'del') : '';
      const rc = r.t === 'chg' ? (r.r === null ? 'empty' : 'add') : '';
      t += `<tr class="cl" data-key="${key}"><td class="ln ${lc}">${r.o ?? ''}</td><td class="c split-l ${lc}">${cell(r.l)}</td><td class="ln ${rc}">${r.n ?? ''}</td><td class="c ${rc}">${cell(r.r)}</td></tr>`;
    } else {
      const c = r.t === 'del' ? 'del' : r.t === 'add' ? 'add' : '';
      const p = r.t === 'del' ? '-' : r.t === 'add' ? '+' : '';
      t += `<tr class="cl" data-key="${key}"><td class="ln ${c}">${r.o ?? ''}</td><td class="ln ${c}">${r.n ?? ''}</td><td class="p ${c}">${p}</td><td class="c ${c}">${cell(r.c)}</td></tr>`;
    }
    const cm = rowComments(id, key);
    if (cm) t += `<tr class="crow"><td colspan="4"><div>${cm}</div></td></tr>`;
  }
  if (h.below) t += expandRow(id, 'down', h.below, down);
  return scroller(t + '</table>');
}

function hang(raw) {
  const m = raw.match(/^([ \t]*)([-*+] |\d+[.)] |> )?/);
  return m[1].replace(/\t/g, '    ').length + (m[2] ? m[2].length : 0);
}

// Each source line gets a hanging indent, so a wrapped list item lines up under its text.
function wordLines(parts) {
  const lines = [{ html: '', raw: '' }];
  for (const [t, k] of parts) {
    t.split('\n').forEach((piece, i) => {
      if (i) lines.push({ html: '', raw: '' });
      if (!piece) return;
      const line = lines[lines.length - 1];
      line.raw += piece;
      line.html += k === 'same' ? escLine(piece) : k === 'del' ? `<del>${escLine(piece)}</del>` : `<ins>${escLine(piece)}</ins>`;
    });
  }
  return lines.map(l => `<div class="wl" style="--i:${hang(l.raw)}">${l.html || '&nbsp;'}</div>`).join('');
}

function renderWords(id, h) {
  let html = '<div class="words">';
  for (const b of blocks(h)) {
    if (b.ctx) {
      if (!b.s.trim()) continue;
      html += `<div class="wb ctx cl" data-key="R${b.n}">${wordLines([[b.s, 'same']])}${b.e ? EOL : ''}</div>` + rowComments(id, 'R' + b.n);
      continue;
    }
    let body = wordLines(mergedDiff(b.R.map(x => x.s).join('\n'), b.A.map(x => x.s).join('\n')));
    if (b.R.some(x => x.e)) body += `<div class="wl"><del>${EOL}</del></div>`;
    if (b.A.some(x => x.e)) body += `<div class="wl"><ins>${EOL}</ins></div>`;
    const key = b.A.length ? 'R' + b.A[0].n : 'L' + b.R[0].o;
    const span = b.A.length > 1 ? `${key}-${b.A[b.A.length - 1].n}` : key;
    html += `<div class="wb cl" data-key="${key}" data-span="${span}">${body}</div>` + rowComments(id, key);
  }
  return html + '<p class="legend">Struck words are removed, marked words are added. Switch to Lines for line numbers.</p></div>';
}

function renderHunk(el) {
  const id = el.dataset.hunk, h = KIT.hunks[id];
  const body = $('.hbody', el);
  const prose = h.prose && h.lines.length;
  const view = prose ? (ui.view[id] || 'words') : 'lines';
  let html = `<div class="hhead"><span class="fname">${esc(h.path)}</span><span class="rng">${rangeOf(h)}</span>`;
  if (h.header) html += `<span class="fn">${esc(h.header)}</span>`;
  if (KIT.commits.length > 1) {
    for (const sha of h.commits) {
      const subject = SUBJECTS[sha];
      html += subject ? `<span class="sha" title="${esc(subject)}">${sha}</span>` : `<span class="sha">${esc(sha)}</span>`;
    }
  }
  html += '<span class="sxhint" hidden>Long lines, scroll sideways</span><span class="acts">';
  if (prose) html += `<span class="seg" role="group" aria-label="View"><button data-view="${id}:words" aria-pressed="${view === 'words'}">Words</button><button data-view="${id}:lines" aria-pressed="${view === 'lines'}">Lines</button></span>`;
  html += '<button class="linkbtn" data-hc>Comment</button></span></div>';
  if (h.note) html += `<div class="fnote">${esc(h.note)}</div>`;
  html += rowComments(id, 'H');
  if (h.lines.length) html += view === 'words' ? renderWords(id, h) : renderTable(id, h);
  body.innerHTML = html;
  el.dataset.rendered = '1';
  edges(el);
  if (ui.mark && ui.mark.id === id) markLines(el);
  const ta = $('.cbox textarea', body);
  if (ta) ta.focus({ preventScroll: true });
}

function edges(el) {
  let any = false;
  for (const s of $$('.dscroll', el)) {
    const more = s.scrollLeft + s.clientWidth < s.scrollWidth - 1;
    s.parentElement.classList.toggle('more', more);
    any = any || s.scrollWidth > s.clientWidth + 1;
  }
  const hint = $('.sxhint', el);
  if (hint) hint.hidden = !any;
}

function keyLines(node) {
  const key = node.dataset.key;
  if (!key || key[0] !== 'R') return null;
  const first = +key.slice(1);
  const span = node.dataset.span;
  return [first, span ? +span.split('-')[1] : first];
}

function markLines(el) {
  const { first, last } = ui.mark;
  const hits = $$('[data-key]', el).filter(n => {
    const r = keyLines(n);
    return r && r[0] <= last && first <= r[1];
  });
  hits.forEach(n => n.classList.add('mark'));
  return hits;
}

function jump(id, first, last) {
  const el = document.getElementById('hunk-' + id), h = KIT.hunks[id];
  if (!el) return;
  ui.mark = { id, first, last };
  const ex = ui.expand[id] = ui.expand[id] || { up: 0, down: 0 };
  const top = h.newCount ? h.newStart : h.newStart + 1;
  if (h.above && first < top) ex.up = Math.max(ex.up, Math.ceil((top - first) / STEP) * STEP);
  if (h.below && last >= h.below.new) ex.down = Math.max(ex.down, Math.ceil((last - h.below.new + 1) / STEP) * STEP);
  for (let d = el.closest('details'); d; d = d.parentElement.closest('details')) d.open = true;
  $$('.mark').forEach(n => n.classList.remove('mark'));
  renderHunk(el);
  let hits = $$('.mark', el);
  if (!hits.length && ui.view[id] !== 'lines' && h.prose) { ui.view[id] = 'lines'; renderHunk(el); hits = $$('.mark', el); }
  $$('.hunk[data-hunk]').forEach(x => { if (!x.dataset.rendered && visible(x)) renderHunk(x); });
  (hits[0] || el).scrollIntoView({ behavior: 'smooth', block: hits.length ? 'center' : 'start' });
}

function visible(el) {
  for (let d = el.closest('details'); d; d = d.parentElement.closest('details')) if (!d.open) return false;
  return true;
}

function renderAll() {
  document.body.classList.toggle('nowrap', !prefs.wrap);
  $$('.hunk[data-hunk]').forEach(el => { if (visible(el)) renderHunk(el); else delete el.dataset.rendered; });
  $$('.cm[data-fb]').forEach(renderReplies);
  $$('[data-layout]').forEach(b => b.setAttribute('aria-pressed', String(prefs.layout === b.dataset.layout)));
  $('#wrap').checked = prefs.wrap;
  updateCards();
  updateBar();
}

function renderReplies(cm) {
  const id = cm.dataset.fb;
  const key = 'F' + id;
  const open = ui.open && ui.open.key === key ? ui.open : null;
  $('.replies', cm).innerHTML = commentsHtml(c => c.key === key, open);
  const ta = $('.cbox textarea', cm);
  if (ta) ta.focus({ preventScroll: true });
}

function changedPicks() {
  return $$('.call[data-call]').filter(c => page.picks[c.dataset.call] && page.picks[c.dataset.call] !== c.dataset.pick);
}

function updateCards() {
  for (const card of $$('.call[data-call]')) {
    const chosen = page.picks[card.dataset.call] || card.dataset.pick;
    card.classList.toggle('changed', chosen !== card.dataset.pick);
    $$('.opt', card).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.opt === chosen)));
  }
}

function copyText() {
  const picks = changedPicks().map(c => c.dataset.call + page.picks[c.dataset.call]);
  if (!picks.length && !page.comments.length) return 'go\n';
  const parts = picks.length ? [picks.join(', ')] : [];
  for (const c of page.comments) parts.push(`${c.label}: ${c.text}`);
  return parts.join('\n\n') + '\n';
}

function updateBar() {
  const n = page.comments.length, p = changedPicks().length;
  const st = $('#status');
  st.classList.remove('ok');
  st.textContent = `${n} comment${n === 1 ? '' : 's'}` + ($('.call') ? `, ${p} changed pick${p === 1 ? '' : 's'}` : '');
  $('#copy').textContent = n || p ? 'Copy for chat' : 'Copy go';
  renderTray();
}

function renderTray(fallbackText) {
  const tray = $('#tray');
  tray.hidden = !ui.tray && !fallbackText;
  if (tray.hidden) return;
  let html = '<h3>Your comments <button class="linkbtn" data-tray-close>Close</button></h3>';
  if (fallbackText) {
    html += '<p class="small">Copying was blocked. Select the text below and copy it.</p><textarea readonly></textarea>';
  } else if (!page.comments.length && !changedPicks().length) {
    html += '<p class="small muted">Nothing yet, so Copy go puts "go" on the clipboard. Tap a line in the diff to comment on it, or pick a different option on a card.</p>';
  } else {
    html += '<ul>';
    for (const card of changedPicks()) html += `<li><div class="cmeta">Decide ${card.dataset.call}</div>${esc(page.picks[card.dataset.call])} instead of the pick ${esc(card.dataset.pick)}</li>`;
    for (const c of page.comments) html += `<li><div class="cmeta">${esc(c.label)}</div>${esc(c.text)} <button class="linkbtn" data-del="${c.id}">Remove</button></li>`;
    html += '</ul><button class="btn" data-clear>Clear all</button>';
  }
  tray.innerHTML = html;
  if (fallbackText) { const ta = $('textarea', tray); ta.value = fallbackText; ta.focus(); ta.select(); }
}

async function copy() {
  const text = copyText();
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) {}
  if (!ok) {
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    ta.remove();
  }
  if (!ok) { renderTray(text); return; }
  const st = $('#status');
  st.textContent = 'Copied. Paste it into the chat.';
  st.classList.add('ok');
}

function rerender(el) {
  if (!el) return;
  if (el.matches('.cm')) renderReplies(el); else renderHunk(el);
}

function reveal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  for (let d = el.closest('details'); d; d = d.parentElement.closest('details')) d.open = true;
  $$('.hunk[data-hunk]').forEach(h => { if (!h.dataset.rendered && visible(h)) renderHunk(h); });
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.addEventListener('click', e => {
  const t = e.target.closest('button, a, tr.cl, .wb.cl');
  if (!t) return;
  const d = t.dataset;
  const host = t.closest('.hunk[data-hunk], .cm[data-fb]');
  if (t.matches('a[href^="#"]')) {
    const id = t.getAttribute('href').slice(1);
    if (!document.getElementById(id)) return;
    e.preventDefault();
    if (d.lines && id.startsWith('hunk-')) { const [a, b] = d.lines.split('-').map(Number); jump(id.slice(5), a, b); }
    else reveal(id);
    history.replaceState(null, '', '#' + id);
    return;
  }
  if (d.layout) { prefs.layout = d.layout; save(PREFS, prefs); renderAll(); return; }
  if (d.order) { prefs.order = d.order; save(PREFS, prefs); applyOrder(); return; }
  if (d.view) { const [id, v] = d.view.split(':'); ui.view[id] = v; renderHunk(host); return; }
  if (d.expand) { const [id, dir] = d.expand.split(':'); const ex = ui.expand[id] = ui.expand[id] || { up: 0, down: 0 }; ex[dir] += STEP; renderHunk(host); return; }
  if (d.hc !== undefined) {
    const h = KIT.hunks[host.dataset.hunk];
    const prev = ui.open && document.querySelector(`[data-hunk="${ui.open.hunk}"]`);
    ui.open = { hunk: host.dataset.hunk, key: 'H', label: `${h.path}${rangeOf(h) ? ':' + rangeOf(h) : ''} (whole hunk)` };
    if (prev && prev !== host) renderHunk(prev);
    renderHunk(host); return;
  }
  if (d.reply) {
    const cm = t.closest('.cm');
    ui.open = { hunk: null, key: 'F' + d.reply, label: `Reply to your comment${cm.dataset.where ? ' on ' + cm.dataset.where : ''}` };
    renderReplies(cm); return;
  }
  if (d.save !== undefined) {
    const text = $('.cbox textarea', host).value.trim();
    if (text && ui.open) { page.comments.push({ id: page.nextId++, hunk: ui.open.hunk, key: ui.open.key, label: ui.open.label, text }); persist(); }
    ui.open = null; rerender(host); updateBar(); return;
  }
  if (d.cancel !== undefined) { ui.open = null; rerender(host); return; }
  if (d.del) { page.comments = page.comments.filter(c => c.id !== +d.del); persist(); renderAll(); return; }
  if (d.clear !== undefined) { if (confirm('Remove all comments on this page?')) { page.comments = []; page.picks = {}; persist(); renderAll(); } return; }
  if (d.opt) { const card = t.closest('.call'); page.picks[card.dataset.call] = d.opt; persist(); updateCards(); updateBar(); return; }
  if (d.trayClose !== undefined) { ui.tray = false; $('#tray').hidden = true; return; }
  if (t.id === 'show') { ui.tray = !ui.tray; renderTray(); return; }
  if (t.id === 'copy') { copy(); return; }
  if (t.matches('tr.cl, .wb.cl')) {
    if (String(window.getSelection())) return;
    const h = KIT.hunks[host.dataset.hunk];
    const key = t.dataset.key;
    const span = t.dataset.span;
    const label = span && span !== key ? `${h.path}:${span.slice(1)}` : labelOf(h, key);
    const prev = ui.open && ui.open.hunk && ui.open.hunk !== host.dataset.hunk && document.querySelector(`[data-hunk="${ui.open.hunk}"]`);
    ui.open = { hunk: host.dataset.hunk, key, label };
    if (prev) renderHunk(prev);
    renderHunk(host);
  }
});

document.addEventListener('toggle', e => {
  if (e.target.matches('details') && e.target.open) $$('.hunk[data-hunk]', e.target).forEach(h => { if (!h.dataset.rendered && visible(h)) renderHunk(h); });
}, true);

// By commit moves each hunk element under the first commit that touched it, and back again for reading order.
function applyOrder() {
  const reading = $('#reading'), byCommit = $('#bycommit');
  if (!reading || !byCommit) return;
  const want = KIT.commits.length > 1 && prefs.order === 'commit' ? 'commit' : 'reading';
  $$('[data-order]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.order === want)));
  if (want === (byCommit.hidden ? 'reading' : 'commit')) return;
  if (want === 'reading') {
    for (const el of $$('.hunk[data-hunk]', byCommit)) { ui.slots[el.dataset.hunk].replaceWith(el); }
    byCommit.innerHTML = '';
  } else {
    const groups = new Map(KIT.commits.map(([sha, subject]) => [sha, { title: `<span class="sha">${sha}</span> ${esc(subject)}`, read: [], skim: [] }]));
    groups.set('uncommitted', { title: 'Uncommitted changes', read: [], skim: [] });
    groups.set('', { title: 'Not traced to a commit', read: [], skim: [] });
    for (const el of $$('.hunk[data-hunk]', reading)) {
      const h = KIT.hunks[el.dataset.hunk];
      const g = groups.get(h.commits[0] || '');
      const slot = document.createComment('');
      el.before(slot);
      ui.slots[el.dataset.hunk] = slot;
      (h.skim ? g.skim : g.read).push(el);
    }
    for (const g of groups.values()) {
      if (!g.read.length && !g.skim.length) continue;
      const sec = document.createElement('section');
      sec.className = 'group';
      sec.innerHTML = `<h3>${g.title}</h3>`;
      sec.append(...g.read);
      if (g.skim.length) {
        const det = document.createElement('details');
        det.className = 'group skim';
        det.innerHTML = `<summary><b>Marked unimportant</b><span class="count">${g.skim.length} hunk${g.skim.length === 1 ? '' : 's'}</span><span class="go">Show</span></summary>`;
        det.append(...g.skim);
        sec.append(det);
      }
      byCommit.append(sec);
    }
  }
  reading.hidden = want === 'commit';
  byCommit.hidden = want !== 'commit';
  $$('.hunk[data-hunk]').forEach(h => { if (!h.dataset.rendered && visible(h)) renderHunk(h); });
}

const SUBJECTS = Object.fromEntries(KIT.commits);
$('#wrap').addEventListener('change', e => { prefs.wrap = e.target.checked; save(PREFS, prefs); renderAll(); });
document.addEventListener('scroll', e => {
  const s = e.target;
  if (s.classList && s.classList.contains('dscroll')) s.parentElement.classList.toggle('more', s.scrollLeft + s.clientWidth < s.scrollWidth - 1);
}, true);
let wasSplit = isSplit();
window.addEventListener('resize', () => {
  if (isSplit() !== wasSplit) { wasSplit = isSplit(); renderAll(); return; }
  $$('.hunk[data-rendered]').forEach(edges);
});
applyOrder();
renderAll();
if (location.hash.length > 1) reveal(location.hash.slice(1));
})();
