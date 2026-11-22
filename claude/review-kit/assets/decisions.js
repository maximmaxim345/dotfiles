(() => {
const KIT = JSON.parse(document.getElementById('kit-data').textContent);
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const KEY = 'review-kit:decisions:' + KIT.key;
let state = { picks: {}, notes: {} };
try { state = Object.assign(state, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) {}
const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const cards = () => $$('.dec[data-call]');
const chosen = card => state.picks[card.dataset.call] || card.dataset.pick;

function answer() {
  const changed = cards().filter(c => chosen(c) !== c.dataset.pick).map(c => c.dataset.call + chosen(c));
  const notes = cards().filter(c => (state.notes[c.dataset.call] || '').trim()).map(c => `${c.dataset.call}: ${state.notes[c.dataset.call].trim()}`);
  return [changed.length ? changed.join(', ') : 'go', ...notes].join('\n\n');
}

function update() {
  for (const card of cards()) {
    card.classList.toggle('changed', chosen(card) !== card.dataset.pick);
    $$('.opt', card).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.opt === chosen(card))));
  }
  const st = $('#status');
  st.classList.remove('ok');
  st.textContent = `Answer: ${answer().split('\n')[0]}`;
}

document.addEventListener('click', async e => {
  const t = e.target.closest('button');
  if (!t) return;
  if (t.dataset.opt) { state.picks[t.closest('.dec').dataset.call] = t.dataset.opt; persist(); update(); return; }
  if (t.id !== 'copy') return;
  const text = answer();
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (err) {}
  if (!ok) {
    const tray = $('#tray');
    tray.hidden = false;
    tray.innerHTML = '<p class="small">Copying was blocked. Select the text below and copy it.</p><textarea readonly></textarea>';
    const ta = $('textarea', tray); ta.value = text; ta.focus(); ta.select();
    return;
  }
  $('#status').textContent = 'Copied. Paste it into the chat.';
  $('#status').classList.add('ok');
});

document.addEventListener('input', e => {
  const card = e.target.closest('.dec');
  if (!card || !e.target.matches('textarea.note')) return;
  state.notes[card.dataset.call] = e.target.value; persist(); update();
});

for (const card of cards()) $('textarea.note', card).value = state.notes[card.dataset.call] || '';
update();
})();
