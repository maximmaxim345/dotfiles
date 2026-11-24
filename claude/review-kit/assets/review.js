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
const blank = () => ({ comments: [], picks: {}, notes: {}, resolved: [], nextId: 1, drafts: {}, body: null });
const page = Object.assign(blank(), load(PAGE, {}));
const ui = { open: null, expand: {}, view: {}, tray: false, mark: null, slots: {}, unfold: {} };
const API = location.protocol.startsWith('http') && /^\/review\/[\w-]+$/.test(location.pathname) ? '/api' + location.pathname : '';
const board = { on: false, send: false, rev: 0, scroll: 0, replies: {}, sent: { comments: [], picks: {}, notes: {} }, header: '' };
const queue = [];
const noteTimers = {};
const R = KIT.review || null;
const DRAFTS = R ? R.drafts : [];
const BASE = Object.fromEntries(DRAFTS.map(d => [d.id, d]));
const STATUS = { post: 'To post', lower: 'Lower priority', dismissed: 'Dismissed' };
const draftTimers = {};
const draft = id => ({ ...BASE[id], ...(page.drafts[id] || {}) });
const bodyText = () => page.body ?? R.body;
const AUTHORS = [...new Set(Object.values(KIT.hunks).flatMap(h => h.authors || []))];
// Browser storage keeps the narrative text each edit started from, so a rebuild that rewrote a draft or the body wins, as on the board.
if (R) {
  const bases = page.bases || {};
  for (const id of Object.keys(page.drafts)) if (!BASE[id] || bases[id] !== BASE[id].text) delete page.drafts[id];
  if (page.bodyBase !== R.body) page.body = null;
  Object.assign(page, { bases: Object.fromEntries(DRAFTS.map(d => [d.id, d.text])), bodyBase: R.body });
}
let pumping = null;

async function call(path, body) {
  const ident = { page: KIT.key, ...(KIT.review ? { version: KIT.review.version } : {}) };
  const init = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...ident, ...body }) } : { cache: 'no-store' };
  const r = await fetch(API + path, init);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(data.error || `the board answered ${r.status}`), { status: r.status });
  return data;
}

// Text typed but not yet saved on the board wins over the state the board sends back.
function adopt(data) {
  const before = { comments: page.comments, drafts: page.drafts };
  const typed = Object.keys(draftTimers).filter(k => k !== 'body').map(id => [id, page.drafts[id].text]);
  const body = 'body' in draftTimers ? page.body : undefined;
  Object.assign(page, blank(), data.state);
  Object.assign(board, { rev: data.rev, scroll: data.scroll, replies: data.replies, sent: data.sent, send: data.send, header: data.header });
  const typing = document.activeElement;
  if (typing && typing.matches('.call textarea.note')) page.notes[typing.closest('.call').dataset.call] = typing.value;
  if (typing && typing.matches('textarea.dtext')) typed.push([typing.closest('[data-draft]').dataset.draft, typing.value]);
  for (const [id, text] of typed) page.drafts[id] = { ...page.drafts[id], text };
  if (typing && typing.id === 'rbody') page.body = typing.value;
  else if (body !== undefined) page.body = body;
  return before;
}

function apply(op) {
  if (op.op === 'add') page.comments.push({ id: page.nextId++, hunk: op.hunk, key: op.key, label: op.label, text: op.text, at: new Date().toISOString(), ...(op.parent ? { parent: op.parent } : {}) });
  if (op.op === 'remove') page.comments = page.comments.filter(c => c.id !== op.id);
  if (op.op === 'pick') page.picks[op.call] = op.value;
  if (op.op === 'note') page.notes[op.call] = op.value;
  if (op.op === 'draft') page.drafts[op.id] = { ...page.drafts[op.id], ...Object.fromEntries(['text', 'status', 'reason'].filter(k => k in op).map(k => [k, op[k]])) };
  if (op.op === 'body') page.body = op.value;
  if (op.op === 'resolve') page.resolved = [...page.resolved.filter(x => x !== op.id), ...(op.on ? [op.id] : [])];
  if (op.op === 'clear') { page.comments = page.comments.filter(isSent); page.picks = {}; page.notes = {}; }
}

// On the board each change goes to the server in order, and a comment shows once the server gave it its id.
function edit(op) {
  if (!board.on || op.op !== 'add') apply(op);
  if (!board.on) { save(PAGE, page); return Promise.resolve(); }
  return new Promise((resolve, reject) => { queue.push({ op, resolve, reject }); pump(); });
}

function pump() {
  if (!pumping) pumping = drain().finally(() => { pumping = null; });
  return pumping;
}

async function drain() {
  while (queue.length && board.on) {
    const item = queue[0];
    try {
      const data = await call('/edit', item.op);
      queue.shift();
      item.resolve();
      if (!queue.length) refresh(adopt(data));
    } catch (e) {
      if (e.status === 409) { stale(); return; }
      if (e.status >= 400 && e.status < 500) { queue.shift(); item.reject(e); board.rev = -1; continue; }
      $('#status').textContent = `Not saved on the board yet, trying again: ${e.message}`;
      queue.filter(x => x.op.op === 'add').forEach(x => x.reject(e));
      queue.splice(0, queue.length, ...queue.filter(x => x.op.op !== 'add'));
      return;
    }
  }
}

const current = data => data.key === KIT.key && (!R || data.version === R.version);

function stale() {
  board.on = false;
  board.stale = true;
  queue.splice(0).forEach(x => x.reject(new Error('this page was rebuilt')));
  updateBar();
}

function saveNote(call) {
  clearTimeout(noteTimers[call]);
  delete noteTimers[call];
  const card = $$('.call[data-call]').find(c => c.dataset.call === call);
  edit({ op: 'note', call, value: $('textarea.note', card).value }).catch(() => {});
}

function saveDraftText(id) {
  clearTimeout(draftTimers[id]);
  delete draftTimers[id];
  const op = id === 'body' ? { op: 'body', value: page.body } : { op: 'draft', id, text: page.drafts[id].text };
  edit(op).catch(() => {});
}

const saveNotes = () => { Object.keys(noteTimers).forEach(saveNote); Object.keys(draftTimers).forEach(saveDraftText); };

async function settle() {
  saveNotes();
  await pump();
  if (queue.length) throw new Error('the board has not saved the last change yet');
}

async function poll() {
  if (!board.on || document.hidden) return;
  if (queue.length || pumping) { pump(); return; }
  try {
    const data = await call('/state');
    if (!current(data)) stale();
    else if (data.rev > board.rev && !queue.length && !pumping) refresh(adopt(data));
  } catch (e) {}
}

// An open comment box keeps its hunk as it is, so typed text survives a reply landing nearby.
function refresh(before) {
  const hosts = new Set([...before.comments, ...page.comments].map(c => c.hunk));
  for (const d of DRAFTS) if (JSON.stringify(before.drafts[d.id]) !== JSON.stringify(page.drafts[d.id])) hosts.add(d.hunk);
  const open = ui.open || {};
  const typing = document.activeElement;
  $$('.hunk[data-rendered]').forEach(el => { if (hosts.has(el.dataset.hunk) && el.dataset.hunk !== open.hunk && !el.contains(typing)) renderHunk(el); });
  renderReview();
  $$('.cm[data-fb]').forEach(cm => { if (open.key !== 'F' + cm.dataset.fb) renderReplies(cm); });
  updateCards();
  updateBar();
}

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

const isSent = c => board.sent.comments.includes(c.id);
const sentTag = c => isSent(c) ? ' <span class="tag">Sent</span>' : '';

function box(open) {
  const title = open.parent ? 'Reply' : open.key[0] === 'F' ? 'Reply to the author' : 'Comment on ' + esc(open.label);
  return `<div class="cbox"><div class="cmeta">${title}</div><textarea aria-label="Comment">${esc(open.draft || '')}</textarea><div class="row"><button class="btn primary" data-save>Save comment</button><button class="btn" data-cancel>Cancel</button></div></div>`;
}

function mine(c) {
  const who = c.parent || c.key[0] === 'F' ? 'Your reply' : 'Your comment on ' + esc(c.label);
  const remove = isSent(c) ? '' : `<button class="linkbtn" data-del="${c.id}">Remove</button>`;
  return `<div class="cmt"><div class="cmeta">${who}${sentTag(c)}</div><div class="txt">${esc(c.text)}</div>${remove}</div>`;
}

function thread(c, open) {
  const resolved = page.resolved.includes(c.id);
  if (resolved && !ui.unfold[c.id]) {
    return `<div class="cmt done"><div class="cmeta">Resolved, ${esc(c.label)}</div><div class="txt one">${esc(c.text)}</div><button class="linkbtn" data-unfold="${c.id}">Show</button></div>`;
  }
  const items = [
    ...page.comments.filter(x => x.parent === c.id).map(x => [Date.parse(x.at) || 0, mine(x)]),
    ...(board.replies[c.id] || []).map(r => [Date.parse(r.at) || 0, `<div class="cmt reply"><div class="cmeta">Author</div><div class="txt">${esc(r.text)}</div></div>`]),
  ].sort((a, b) => a[0] - b[0]);
  let out = `<div class="thread">${mine(c)}${items.map(i => i[1]).join('')}`;
  if (open && open.parent === c.id) out += box(open);
  else if (board.on && isSent(c)) {
    out += `<div class="tacts"><button class="linkbtn" data-follow="${c.id}">Reply</button><button class="linkbtn" data-resolve="${c.id}">${resolved ? 'Unresolve' : 'Resolve'}</button>`
      + (resolved ? `<button class="linkbtn" data-unfold="${c.id}">Hide</button>` : '') + '</div>';
  }
  return out + '</div>';
}

function commentsHtml(match, open) {
  let out = page.comments.filter(c => !c.parent && match(c)).map(c => thread(c, open)).join('');
  if (open && !open.parent) out += box(open);
  return out;
}

function rowComments(hid, key, at) {
  const open = ui.open && ui.open.hunk === hid && ui.open.key === key ? ui.open : null;
  return (at ? draftsAt(hid, at) : '') + commentsHtml(c => c.hunk === hid && c.key === key, open);
}

// `at` holds the old and the new line numbers a row or a word block shows.
function draftsAt(hid, at) {
  return DRAFTS.filter(d => d.hunk === hid && at[d.side === 'LEFT' ? 0 : 1].includes(d.line)).map(d => draftBox(d.id, 'diff')).join('');
}

const rowsFor = text => Math.min(14, Math.max(2, text.split('\n').reduce((n, l) => n + 1 + Math.floor(l.length / 90), 0)));

function draftBox(id, place) {
  const d = draft(id), b = BASE[id];
  const where = d.where ? `<code>${esc(d.where)}</code>` : '<span class="muted">no line</span>';
  const tag = `<span class="tag ${d.status === 'post' ? 'accent' : ''}">${STATUS[d.status]}</span>`;
  if (place === 'diff' && d.status !== 'post' && !ui.unfold['d:' + id]) {
    return `<div class="draft fold" data-draft="${esc(id)}">${tag}<span class="one">${esc(d.text)}</span><button class="linkbtn" data-dfold>Show</button></div>`;
  }
  const seg = Object.keys(STATUS).map(s => `<button data-dstatus="${s}" aria-pressed="${d.status === s}">${s === 'lower' ? 'Lower' : STATUS[s]}</button>`).join('');
  const edited = d.text !== b.text ? '<span class="tag">Edited</span>' : '';
  const fold = place === 'diff' && d.status !== 'post' ? '<button class="linkbtn" data-dfold>Hide</button>' : '';
  const jump = place === 'list' && d.hunk ? `<a class="golink" href="#hunk-${d.hunk}" data-lines="${d.line}-${d.line}">Show its line</a>` : '';
  const reason = d.status === 'dismissed' && d.reason ? `<p class="dreason"><span class="lbl">Reason.</span> ${d.reason === b.reason ? b.reasonHtml : esc(d.reason)}</p>` : '';
  const off = d.status === 'post' && !d.inDiff
    ? '<div class="warnbox">GitHub takes inline comments only on lines of the PR\'s diff, and this one is not. <button class="linkbtn" data-dmove>Move into the review body</button></div>' : '';
  const proof = b.proof ? `<div class="proof"><div class="cmeta">Proof, private, never posted</div>${b.proofHtml}</div>` : '';
  return `<div class="draft s-${d.status}" data-draft="${esc(id)}"${place === 'list' ? ` id="draft-${esc(id)}"` : ''}><div class="dh">${tag}${where}${edited}`
    + `<span class="seg" role="group" aria-label="Status">${seg}</span>${fold}</div>`
    + `<div class="dgrid${proof ? ' two' : ''}"><textarea class="dtext" aria-label="Draft text" rows="${rowsFor(d.text)}">${esc(d.text)}</textarea>${proof}</div>${reason}${off}${jump}</div>`;
}

function renderReview() {
  const host = $('#rv');
  if (!host) return;
  if (!$('#rbody')) host.innerHTML = '<div class="card rvbody"><div class="cmeta">Review body <span class="tag" id="rbody-edited" hidden>Edited</span></div><textarea id="rbody" aria-label="Review body"></textarea></div><div id="rv-lists"></div>';
  const area = $('#rbody');
  if (area !== document.activeElement) { area.value = bodyText(); area.rows = rowsFor(area.value) + 1; }
  $('#rbody-edited').hidden = bodyText() === R.body;
  const lists = $('#rv-lists');
  if (lists.contains(document.activeElement) && document.activeElement.matches('textarea')) { ui.reviewStale = true; return; }
  ui.reviewStale = false;
  const by = s => DRAFTS.filter(d => draft(d.id).status === s);
  const post = by('post');
  const link = d => d.hunk ? `<a href="#hunk-${d.hunk}" data-lines="${d.line}-${d.line}">${esc(d.where)}</a>` : `<a href="#draft-${esc(d.id)}">${esc(d.where || 'no line')}</a>`;
  let html = `<h3>To post <span class="count">${post.length}</span></h3>`;
  html += post.length ? '<ul class="dsum">' + post.map(d => `<li>${link(d)} <span class="muted">${esc(draft(d.id).text.slice(0, 90))}</span></li>`).join('') + '</ul>' : '<p class="muted small">No draft is marked To post.</p>';
  const loose = post.filter(d => !d.hunk);
  if (loose.length) html += `<h3>Not at a line of this page <span class="count">${loose.length}</span></h3>` + loose.map(d => draftBox(d.id, 'list')).join('');
  for (const s of ['lower', 'dismissed']) {
    const list = by(s);
    html += `<details class="group skim dlist" data-list="${s}"${ui.lists && ui.lists[s] ? ' open' : ''}><summary><b>${STATUS[s]}</b><span class="count">${list.length}</span><span class="go">Show</span></summary>`
      + (list.map(d => draftBox(d.id, 'list')).join('') || '<p class="muted small">None.</p>') + '</details>';
  }
  lists.innerHTML = html;
}

function setDraft(id, change) {
  saveNotes();
  edit({ op: 'draft', id, ...change }).catch(() => {});
  const el = BASE[id].hunk && document.getElementById('hunk-' + BASE[id].hunk);
  if (el && el.dataset.rendered) renderHunk(el);
  renderReview();
  updateBar();
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

// With wrap off, each side of a split diff has its own scroller. Comments sit between the scrolling parts.
function renderPairs(id, rows) {
  let out = '', part = [];
  const flush = () => {
    if (part.length) out += `<div class="pair">${scroller(`<table class="d">${sideRows(part, 'l')}</table>`)}${scroller(`<table class="d">${sideRows(part, 'r')}</table>`)}</div>`;
    part = [];
  };
  for (const r of rows) {
    part.push(r);
    const cm = rowComments(id, keyOf(r), [[r.o], [r.n]]);
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
    const cm = rowComments(id, key, [[r.o], [r.n]]);
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
      html += `<div class="wb ctx cl" data-key="R${b.n}">${wordLines([[b.s, 'same']])}${b.e ? EOL : ''}</div>` + rowComments(id, 'R' + b.n, [[b.o], [b.n]]);
      continue;
    }
    let body = wordLines(mergedDiff(b.R.map(x => x.s).join('\n'), b.A.map(x => x.s).join('\n')));
    if (b.R.some(x => x.e)) body += `<div class="wl"><del>${EOL}</del></div>`;
    if (b.A.some(x => x.e)) body += `<div class="wl"><ins>${EOL}</ins></div>`;
    const key = b.A.length ? 'R' + b.A[0].n : 'L' + b.R[0].o;
    const span = b.A.length > 1 ? `${key}-${b.A[b.A.length - 1].n}` : key;
    html += `<div class="wb cl" data-key="${key}" data-span="${span}">${body}</div>` + rowComments(id, key, [b.R.map(x => x.o), b.A.map(x => x.n)]);
  }
  return html + '<p class="legend">Struck words are removed, marked words are added. Switch to Lines for line numbers.</p></div>';
}

function renderPr(el) {
  let html = '<div class="hhead"><span class="fname">PR title and description</span><span class="acts"><button class="linkbtn" data-hc>Comment</button></span></div>';
  html += rowComments('pr', 'H') + '<div class="words prd">';
  html += `<div class="wb cl prt" data-key="T"><div class="wl">${esc(KIT.pr.title)}</div></div>` + rowComments('pr', 'T');
  KIT.pr.body.split('\n').forEach((line, i) => {
    html += `<div class="wb cl" data-key="B${i + 1}"><div class="wl" style="--i:${hang(line)}">${esc(line) || '&nbsp;'}</div></div>` + rowComments('pr', 'B' + (i + 1));
  });
  $('.hbody', el).innerHTML = html + '</div>';
  el.dataset.rendered = '1';
  const ta = $('.cbox textarea', el);
  if (ta) ta.focus({ preventScroll: true });
}

function renderHunk(el) {
  if (el.dataset.hunk === 'pr') { renderPr(el); return; }
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
  if (R && KIT.multiAuthor) for (const a of h.authors) html += `<span class="tag au au${AUTHORS.indexOf(a) % 4}">${esc(a)}</span>`;
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
  for (const pairs of $$('.pairs', el)) {
    const tables = $$('.dscroll > table', pairs);
    tables.forEach(t => { t.style.minWidth = ''; });
    const width = Math.max(...tables.map(t => t.offsetWidth));
    tables.forEach(t => { t.style.minWidth = width + 'px'; });
  }
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
  renderReview();
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

const noted = () => $$('.call[data-call]').filter(c => (page.notes[c.dataset.call] || '').trim());

function updateCards() {
  for (const card of $$('.call[data-call]')) {
    const chosen = page.picks[card.dataset.call] || card.dataset.pick;
    card.classList.toggle('changed', chosen !== card.dataset.pick);
    $$('.opt', card).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.opt === chosen)));
    const note = $('textarea.note', card);
    if (note && note !== document.activeElement) note.value = page.notes[card.dataset.call] || '';
  }
}

const chosen = card => page.picks[card.dataset.call] || card.dataset.pick;
const noteOf = card => (page.notes[card.dataset.call] || '').trim();

// On the board the answer holds only what the thread has not had yet, and each comment carries its [id] for the reply.
function answer() {
  const cards = $$('.call[data-call]');
  const fresh = board.on;
  const picks = cards.filter(c => chosen(c) !== ((fresh && board.sent.picks[c.dataset.call]) || c.dataset.pick));
  const notes = cards.filter(c => noteOf(c) && noteOf(c) !== (fresh ? board.sent.notes[c.dataset.call] || '' : ''));
  const comments = page.comments.filter(c => !(fresh && isSent(c)));
  const line = c => !fresh ? `${c.label}: ${c.text}` : c.parent ? `[${c.parent}] Reply on ${c.label}: ${c.text}` : `[${c.id}] ${c.label}: ${c.text}`;
  const parts = [
    ...(picks.length ? [picks.map(c => c.dataset.call + chosen(c)).join(', ')] : []),
    ...notes.map(c => `Decide ${c.dataset.call}: ${noteOf(c)}`),
    ...comments.map(line),
  ];
  const lead = R ? [reviewSummary(!fresh)] : [];
  return { text: [...lead, ...(parts.length ? parts : ['go'])].join('\n\n') + '\n', picks, notes, comments };
}

function reviewCounts() {
  const n = { post: 0, lower: 0, dismissed: 0, edited: 0 };
  for (const b of DRAFTS) { const d = draft(b.id); n[d.status]++; if (d.text !== b.text || d.status !== b.status) n.edited++; }
  n.body = bodyText() !== R.body;
  return n;
}

// On the board the thread reads the drafts with `review-page export`, so the answer only counts them.
function reviewSummary(full) {
  const n = reviewCounts();
  const changed = [n.edited ? `${n.edited} draft${n.edited === 1 ? '' : 's'}` : '', n.body ? 'the review body' : ''].filter(Boolean);
  const line = `Drafts: ${n.post} to post, ${n.lower} lower priority, ${n.dismissed} dismissed.` + (changed.length ? ` Changed on the page: ${changed.join(' and ')}.` : '');
  if (!full) return line;
  const items = DRAFTS.map(b => {
    const d = draft(b.id);
    return `[${d.status}] ${d.where || 'no line'} (${b.id}): ${d.text}` + (d.status === 'dismissed' && d.reason ? `\nReason: ${d.reason}` : '');
  });
  return [line, `Review body:\n${bodyText()}`, ...items].join('\n\n');
}

function updateBar() {
  const a = answer(), n = a.comments.length, p = a.picks.length, m = a.notes.length;
  const rc = R ? reviewCounts() : null;
  const any = n || p || m || (rc && (rc.edited || rc.body));
  const st = $('#status');
  st.classList.remove('ok');
  st.textContent = board.stale ? 'This page was rebuilt. Reload it to see the new one.'
    : (rc ? `${rc.post} to post, ` : '') + `${n} ${board.on ? 'unsent ' : ''}comment${n === 1 ? '' : 's'}` + ($('.call') ? `, ${p} changed pick${p === 1 ? '' : 's'}, ${m} note${m === 1 ? '' : 's'}` : '');
  $('#copy').textContent = any ? 'Copy for chat' : 'Copy go';
  const send = $('#send');
  send.hidden = !(board.on && board.send);
  send.textContent = any ? 'Send to thread' : 'Send go';
  $('#copy').classList.toggle('primary', send.hidden);
  renderTray();
}

function sentBody(a) {
  const cards = $$('.call[data-call]');
  return {
    text: a.text,
    comments: a.comments.map(c => c.id),
    picks: Object.fromEntries(cards.map(c => [c.dataset.call, chosen(c)])),
    notes: Object.fromEntries(cards.map(c => [c.dataset.call, noteOf(c)])),
  };
}

async function sendAnswer() {
  const btn = $('#send'), st = $('#status');
  btn.disabled = true;
  st.classList.remove('ok');
  st.textContent = 'Sending...';
  try {
    await settle();
    refresh(adopt(await call('/send', sentBody(answer()))));
    st.textContent = 'Sent to the thread.';
    st.classList.add('ok');
  } catch (e) {
    st.textContent = `Not sent: ${e.message}. Copy for chat still works.`;
  }
  btn.disabled = false;
}

function renderTray(fallbackText) {
  const tray = $('#tray');
  tray.hidden = !ui.tray && !fallbackText;
  if (tray.hidden) return;
  let html = '<h3>Your comments <button class="linkbtn" data-tray-close>Close</button></h3>';
  if (fallbackText) {
    html += '<p class="small">Copying was blocked. Select the text below and copy it.</p><textarea readonly></textarea>';
  } else if (!page.comments.length && !changedPicks().length && !noted().length) {
    html += '<p class="small muted">Nothing yet, so Copy go puts "go" on the clipboard. Tap a line in the diff to comment on it, or pick a different option on a card.</p>';
  } else {
    html += '<ul>';
    for (const card of changedPicks()) html += `<li><div class="cmeta">Decide ${card.dataset.call}</div>${esc(page.picks[card.dataset.call])} instead of the pick ${esc(card.dataset.pick)}</li>`;
    for (const card of noted()) html += `<li><div class="cmeta">Note on decide ${card.dataset.call}</div>${esc(page.notes[card.dataset.call].trim())}</li>`;
    for (const c of page.comments) {
      const remove = isSent(c) ? '' : ` <button class="linkbtn" data-del="${c.id}">Remove</button>`;
      html += `<li><div class="cmeta">${esc(c.label)}${c.parent ? ', reply' : ''}${sentTag(c)}</div>${esc(c.text)}${remove}</li>`;
    }
    html += '</ul><button class="btn" data-clear>Clear all</button>';
  }
  tray.innerHTML = html;
  if (fallbackText) { const ta = $('textarea', tray); ta.value = fallbackText; ta.focus(); ta.select(); }
}

async function copy() {
  saveNotes();
  const a = answer();
  const text = board.on ? `${board.header}\n\n${a.text}` : a.text;
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
  if (!board.on) return;
  try {
    await settle();
    refresh(adopt(await call('/sent', sentBody(a))));
    st.textContent = 'Copied. Paste it into the chat.';
    st.classList.add('ok');
  } catch (e) {
    st.classList.remove('ok');
    st.textContent = `Copied, but the board did not mark it as sent: ${e.message}`;
  }
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
    const label = h ? `${h.path}${rangeOf(h) ? ':' + rangeOf(h) : ''} (whole hunk)` : 'PR draft';
    ui.open = { hunk: host.dataset.hunk, key: 'H', label };
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
    const open = ui.open;
    const close = () => { if (ui.open === open) ui.open = null; rerender(host); updateBar(); };
    if (!text || !open) { close(); return; }
    t.disabled = true;
    edit({ op: 'add', hunk: open.hunk, key: open.key, label: open.label, text, ...(open.parent ? { parent: open.parent } : {}) }).then(close, err => {
      t.disabled = false;
      $('#status').textContent = `Comment not saved: ${err.message}`;
    });
    return;
  }
  if (d.cancel !== undefined) { ui.open = null; rerender(host); return; }
  if (d.follow) {
    const c = page.comments.find(x => x.id === +d.follow);
    const prev = ui.open && ui.open.hunk && ui.open.hunk !== c.hunk && document.querySelector(`.hunk[data-hunk="${ui.open.hunk}"]`);
    ui.open = { hunk: c.hunk, key: c.key, label: c.label, parent: c.id };
    if (prev) renderHunk(prev);
    rerender(host); return;
  }
  if (d.resolve) {
    const id = +d.resolve;
    ui.unfold[id] = false;
    edit({ op: 'resolve', id, on: !page.resolved.includes(id) }).catch(() => {});
    rerender(host); return;
  }
  if (d.unfold) { ui.unfold[d.unfold] = !ui.unfold[d.unfold]; rerender(host); return; }
  if (d.del) { edit({ op: 'remove', id: +d.del }).catch(() => {}); renderAll(); return; }
  if (d.clear !== undefined) {
    if (confirm('Remove all unsent comments, changed picks and notes on this page?')) {
      edit({ op: 'clear' }).catch(() => {}); renderAll();
    }
    return;
  }
  if (d.dstatus) { setDraft(t.closest('[data-draft]').dataset.draft, { status: d.dstatus }); return; }
  if (d.dfold !== undefined) { const id = t.closest('[data-draft]').dataset.draft; ui.unfold['d:' + id] = !ui.unfold['d:' + id]; renderHunk(host); return; }
  if (d.dmove !== undefined) {
    const id = t.closest('[data-draft]').dataset.draft, x = draft(id);
    page.body = `${bodyText().trimEnd()}\n\n${x.where ? '`' + x.where + '`: ' : ''}${x.text}`.trimStart();
    edit({ op: 'body', value: page.body }).catch(() => {});
    setDraft(id, { status: 'dismissed', reason: 'Moved into the review body.' });
    return;
  }
  if (d.opt) { edit({ op: 'pick', call: t.closest('.call').dataset.call, value: d.opt }).catch(() => {}); updateCards(); updateBar(); return; }
  if (d.trayClose !== undefined) { ui.tray = false; $('#tray').hidden = true; return; }
  if (t.id === 'show') { ui.tray = !ui.tray; renderTray(); return; }
  if (t.id === 'copy') { copy(); return; }
  if (t.id === 'send') { sendAnswer(); return; }
  if (t.matches('tr.cl, .wb.cl')) {
    if (String(window.getSelection())) return;
    const h = KIT.hunks[host.dataset.hunk];
    const key = t.dataset.key;
    const span = t.dataset.span;
    const label = !h ? (key === 'T' ? 'PR title' : `PR description line ${key.slice(1)}`)
      : span && span !== key ? `${h.path}:${span.slice(1)}` : labelOf(h, key);
    const prev = ui.open && ui.open.hunk && ui.open.hunk !== host.dataset.hunk && document.querySelector(`[data-hunk="${ui.open.hunk}"]`);
    ui.open = { hunk: host.dataset.hunk, key, label };
    if (prev) renderHunk(prev);
    renderHunk(host);
  }
});

document.addEventListener('input', e => {
  if (e.target.matches('.cbox textarea') && ui.open) ui.open.draft = e.target.value;
  if (e.target.matches('textarea.dtext, #rbody')) {
    const id = e.target.id === 'rbody' ? 'body' : e.target.closest('[data-draft]').dataset.draft;
    if (id === 'body') page.body = e.target.value;
    else {
      page.drafts[id] = { ...page.drafts[id], text: e.target.value };
      $$('[data-draft] textarea.dtext').forEach(x => { if (x !== e.target && x.closest('[data-draft]').dataset.draft === id) x.value = e.target.value; });
    }
    clearTimeout(draftTimers[id]);
    draftTimers[id] = setTimeout(() => saveDraftText(id), 400);
    updateBar();
    return;
  }
  if (!e.target.matches('.call textarea.note')) return;
  const call = e.target.closest('.call').dataset.call;
  page.notes[call] = e.target.value;
  clearTimeout(noteTimers[call]);
  noteTimers[call] = setTimeout(() => saveNote(call), 400);
  updateBar();
});

document.addEventListener('focusout', e => {
  if (!e.target.matches('textarea.dtext, #rbody')) return;
  const id = e.target.id === 'rbody' ? 'body' : e.target.closest('[data-draft]').dataset.draft;
  if (draftTimers[id]) saveDraftText(id);
  if (ui.reviewStale) setTimeout(renderReview);
});

document.addEventListener('change', e => {
  if (e.target.matches('.call textarea.note') && noteTimers[e.target.closest('.call').dataset.call]) saveNote(e.target.closest('.call').dataset.call);
});

document.addEventListener('toggle', e => {
  if (e.target.matches('details[data-list]')) ui.lists = { ...ui.lists, [e.target.dataset.list]: e.target.open };
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
  if (!s.classList || !s.classList.contains('dscroll')) return;
  s.parentElement.classList.toggle('more', s.scrollLeft + s.clientWidth < s.scrollWidth - 1);
  const pairs = s.closest('.pairs');
  if (pairs) for (const o of $$('.dscroll', pairs)) if (o !== s && o.scrollLeft !== s.scrollLeft) o.scrollLeft = s.scrollLeft;
}, true);
// A browser hands a whole touchpad gesture to one scroller, so a diagonal swipe over a diff would move only one axis.
// A movement under a quarter of the other axis is drift and is dropped.
document.addEventListener('wheel', e => {
  if (e.ctrlKey || e.shiftKey || e.deltaMode || !e.deltaX || !e.cancelable) return;
  const s = e.target.closest && e.target.closest('.dscroll');
  if (!s || s.scrollWidth <= s.clientWidth) return;
  const x = Math.abs(e.deltaX), y = Math.abs(e.deltaY);
  e.preventDefault();
  if (x * 4 >= y) s.scrollLeft += e.deltaX;
  if (y * 4 >= x) window.scrollBy(0, e.deltaY);
}, { passive: false });
let wasSplit = isSplit();
window.addEventListener('resize', () => {
  if (isSplit() !== wasSplit) { wasSplit = isSplit(); renderAll(); return; }
  $$('.hunk[data-rendered]').forEach(edges);
});
window.addEventListener('scroll', () => {
  if (!board.on) return;
  clearTimeout(board.scrollTimer);
  board.scrollTimer = setTimeout(() => call('/edit', { op: 'scroll', y: Math.round(window.scrollY) }).catch(() => {}), 800);
}, { passive: true });

(async () => {
  if (API) {
    try {
      const data = await call('/state');
      if (current(data)) {
        adopt(data);
        board.on = true;
      }
      history.scrollRestoration = 'manual';
    } catch (e) {}
  }
  applyOrder();
  renderAll();
  if (location.hash.length > 1) reveal(location.hash.slice(1));
  else if (board.scroll) window.scrollTo(0, board.scroll);
  if (board.on) {
    setInterval(poll, 4000);
    document.addEventListener('visibilitychange', poll);
  }
})();
})();
