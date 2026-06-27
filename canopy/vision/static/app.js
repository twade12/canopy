// CANOPY Vision — drag-and-dock workspace + local AI wiring-diagram copilot.

const ICON = {
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>', plus: '<path d="M12 5v14M5 12h14"/>',
  diagram: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
  pinout: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
  plan: '<path d="M4 6h16M4 12h16M4 18h10"/><circle cx="20" cy="18" r="1.5"/>',
  chat: '<path d="M4 5h16v11H8l-4 4z"/>', memory: '<path d="M9 3a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 006 0V6a3 3 0 00-3-3z"/>',
  record: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9h6M7 13h10"/>',
  api: '<path d="M8 3H5v18h3M16 3h3v18h-3M9 12h6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19"/>',
  moon: '<path d="M21 12.8A8 8 0 1111 3a6 6 0 0010 9.8z"/>', reset: '<path d="M4 4v6h6M20 20v-6h-6"/><path d="M20 8a8 8 0 00-14-3M4 16a8 8 0 0014 3"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>', prev: '<path d="M15 6l-6 6 6 6"/>', next: '<path d="M9 6l6 6-6 6"/>',
  logout: '<path d="M14 7V5a2 2 0 00-2-2H6a2 2 0 00-2 2v14a2 2 0 002 2h6a2 2 0 002-2v-2M10 12h11M18 9l3 3-3 3"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5M5 20h14"/>', search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
  bolt: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>', warn: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
  edit: '<path d="M4 20h4L18 10l-4-4L4 16z"/><path d="M13 5l4 4"/>', trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
  zin: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4M11 8v6M8 11h6"/>', zout: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4M8 11h6"/>', tag: '<path d="M3 7l8-4 8 4v10l-8 4-8-4z"/>',
  assistant: '<path d="M12 3l1.7 4L18 8.7l-4.3 1.6L12 15l-1.7-4.7L6 8.7 10.3 7z"/><circle cx="18" cy="18" r="2.4"/>',
  bench: '<rect x="3" y="8" width="18" height="9" rx="2"/><path d="M7 8V5M17 8V5M8 13h8"/>', link: '<path d="M9 15l6-6M8 8H6a4 4 0 000 8h2M16 16h2a4 4 0 000-8h-2"/>',
  triage: '<path d="M21 4a4 4 0 01-5.6 5.6L7 18l-2-2 8.4-8.4A4 4 0 0119 2l-3 3 1.5 1.5L21 4z"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="1"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/>',
  phone: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
};
const svg = (n, cls = 'icon') => `<svg class="${cls}" viewBox="0 0 24 24">${ICON[n] || ''}</svg>`;
const VIEWS = [
  { key: 'diagram', label: 'Diagram', icon: 'diagram' }, { key: 'pinout', label: 'Pinout', icon: 'pinout' },
  { key: 'plan', label: 'Wiring Plan', icon: 'plan' }, { key: 'chat', label: 'Chat', icon: 'chat' },
  { key: 'triage', label: 'Triage', icon: 'triage' }, { key: 'pcb', label: 'PCB', icon: 'chip' },
  { key: 'memories', label: 'Memories', icon: 'memory' }, { key: 'record', label: 'Record', icon: 'record' },
  { key: 'assistant', label: 'Assistant', icon: 'assistant' }, { key: 'bench', label: 'Bench', icon: 'bench' },
  { key: 'research', label: 'Research', icon: 'search' }, { key: 'api', label: 'API', icon: 'api' },
];
const GLOBAL_VIEWS = new Set(['api', 'assistant', 'bench', 'research']);  // usable without a project
const meta = k => VIEWS.find(v => v.key === k) || { label: k, icon: 'diagram' };

const api = {
  async get(p) { const r = await fetch(p); if (!r.ok) throw await err(r); return r.json(); },
  async send(p, m, b) { const r = await fetch(p, { method: m, headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw await err(r); return r.json(); },
  async upload(p, f) { const fd = new FormData(); fd.append('file', f); const r = await fetch(p, { method: 'POST', body: fd }); if (!r.ok) throw await err(r); return r.json(); },
};
async function err(r) { let d; try { d = (await r.json()).detail; } catch { d = r.statusText; } return new Error(d || ('HTTP ' + r.status)); }
const el = id => document.getElementById(id);
const esc = s => (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const state = { records: [], current: null, page: 0, pageTotal: 1, diagramId: null, selectedPin: null,
  plan: '', zoom: 1, apiRef: null, gid: 1, drag: null,
  theme: localStorage.getItem('canopy-theme') || 'light', sidebar: true, dock: null };

// ---------- markdown ----------
function md(t) {
  let s = esc(t).replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c.trim()}</code></pre>`);
  const lines = s.split('\n'); let out = '', list = null; const close = () => { if (list) { out += `</${list}>`; list = null; } };
  for (const ln of lines) {
    if (/^\s*[-*]\s+/.test(ln)) { if (list !== 'ul') { close(); out += '<ul>'; list = 'ul'; } out += '<li>' + ln.replace(/^\s*[-*]\s+/, '') + '</li>'; continue; }
    if (/^\s*\d+\.\s+/.test(ln)) { if (list !== 'ol') { close(); out += '<ol>'; list = 'ol'; } out += '<li>' + ln.replace(/^\s*\d+\.\s+/, '') + '</li>'; continue; }
    close();
    if (/^###\s+/.test(ln)) out += '<h3>' + ln.replace(/^###\s+/, '') + '</h3>';
    else if (/^##\s+/.test(ln)) out += '<h2>' + ln.replace(/^##\s+/, '') + '</h2>';
    else if (/^#\s+/.test(ln)) out += '<h1>' + ln.replace(/^#\s+/, '') + '</h1>';
    else if (ln.trim()) out += '<p>' + ln + '</p>';
  }
  close();
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
  return out.replace(/\b([Pp]in|[Tt]erminal)\s*#?\s*(\d{1,3})\b/g, (m, w, n) => pinIndex()[n]
    ? `<span class="pinref" data-pin="${n}" onmouseenter="ui.pinTip(event,'${n}')" onmouseleave="ui.hideTip()" onclick="ui.gotoPinPage('${n}')">${m}</span>` : m);
}
function pinIndex() { const i = {}; for (const p of (state.current?.pinouts || [])) if (p.pin && !(p.pin in i)) i[p.pin] = p; return i; }
function sigClass(s) { s = (s || '').toLowerCase();
  if (/can[\s-]?(h|hi|high|l|lo|low|\+|-)|^can\b/.test(s)) return 'can';
  if (/pwr|power|vpwr|kappwr|b\+|\+12|batt|kl30|kl15|ign|vbpwr/.test(s)) return 'pwr';
  if (/gnd|ground|pwrgnd|sigrtn|return/.test(s)) return 'gnd'; return ''; }

// ================= DOCK ENGINE =================
function defaultDock() { state.gid = 1; const g = () => state.gid++;
  return { t: 's', dir: 'row', sizes: [58, 42], kids: [
    { t: 'g', id: g(), tabs: ['diagram'], active: 'diagram' },
    { t: 's', dir: 'col', sizes: [58, 42], kids: [
      { t: 'g', id: g(), tabs: ['pinout', 'record'], active: 'pinout' },
      { t: 'g', id: g(), tabs: ['triage', 'pcb', 'chat', 'plan', 'memories', 'api'], active: 'triage' }] }] }; }
function saveDock() { try { localStorage.setItem('canopy-dock', JSON.stringify(state.dock)); } catch {} }
function loadDock() { try { const d = JSON.parse(localStorage.getItem('canopy-dock')); if (d && d.t) { let mx = 0; (function walk(n){ if (n.t === 'g') mx = Math.max(mx, n.id); else n.kids.forEach(walk); })(d); state.gid = mx + 1; return d; } } catch {} return defaultDock(); }
const parentOf = (node, t) => { if (node.t !== 's') return null; for (let i = 0; i < node.kids.length; i++) { if (node.kids[i] === t) return { parent: node, idx: i }; const r = parentOf(node.kids[i], t); if (r) return r; } return null; };
const groupOfView = (node, v) => node.t === 'g' ? (node.tabs.includes(v) ? node : null) : node.kids.reduce((a, k) => a || groupOfView(k, v), null);
const firstGroup = n => n.t === 'g' ? n : firstGroup(n.kids[0]);
const placedViews = (n, s = new Set()) => { if (n.t === 'g') n.tabs.forEach(t => s.add(t)); else n.kids.forEach(k => placedViews(k, s)); return s; };

function removeViewFromGroup(v) { const g = groupOfView(state.dock, v); if (!g) return; g.tabs.splice(g.tabs.indexOf(v), 1); if (g.active === v) g.active = g.tabs[g.tabs.length - 1] || null; if (!g.tabs.length) removeGroup(g); }
function removeGroup(g) { if (g === state.dock) return; const { parent, idx } = parentOf(state.dock, g); parent.kids.splice(idx, 1); parent.sizes.splice(idx, 1); if (parent.kids.length === 1) collapse(parent); }
function collapse(split) { const only = split.kids[0]; if (split === state.dock) state.dock = only; else { const p = parentOf(state.dock, split); p.parent.kids[p.idx] = only; } }
function splitWith(target, v, side) {
  const ng = { t: 'g', id: state.gid++, tabs: [v], active: v };
  const dir = (side === 'left' || side === 'right') ? 'row' : 'col', before = (side === 'left' || side === 'top');
  const info = parentOf(state.dock, target);
  if (info && info.parent.dir === dir) { const at = before ? info.idx : info.idx + 1; info.parent.kids.splice(at, 0, ng); info.parent.sizes.splice(at, 0, 100); }
  else { const ns = { t: 's', dir, sizes: [100, 100], kids: before ? [ng, target] : [target, ng] }; if (target === state.dock) state.dock = ns; else { const p = parentOf(state.dock, target); p.parent.kids[p.idx] = ns; } }
}
function ensureView(v) { if (!groupOfView(state.dock, v)) { const g = firstGroup(state.dock); g.tabs.push(v); g.active = v; } else groupOfView(state.dock, v).active = v; saveDock(); renderDock(); }

function computeZone(r, x, y) { const fx = (x - r.left) / r.width, fy = (y - r.top) / r.height, m = Math.min(fx, 1 - fx, fy, 1 - fy);
  if (m > 0.22) return 'center'; return m === fx ? 'left' : m === 1 - fx ? 'right' : m === fy ? 'top' : 'bottom'; }
function showZone(z, side) { const b = { left: ['0', '0', '50%', '100%'], right: ['50%', '0', '50%', '100%'], top: ['0', '0', '100%', '50%'], bottom: ['0', '50%', '100%', '50%'], center: ['8%', '8%', '84%', '84%'] }[side];
  z.style.display = 'block'; z.style.left = b[0]; z.style.top = b[1]; z.style.width = b[2]; z.style.height = b[3]; }

function renderDock() { const ws = el('workspace'); ws.innerHTML = ''; ws.appendChild(renderNode(state.dock)); }
function renderNode(node) {
  if (node.t === 'g') return renderGroup(node);
  const box = document.createElement('div'); box.className = 'split ' + node.dir;
  const kidEls = [];
  node.kids.forEach((kid, i) => {
    if (i > 0) { const rz = document.createElement('div'); rz.className = 'resizer'; box.appendChild(rz); }
    const k = renderNode(kid); k.style.flex = `${node.sizes[i]} 1 0`;
    if (node.dir === 'row') k.style.height = '100%'; else k.style.width = '100%';
    box.appendChild(k); kidEls.push(k);
  });
  let ri = 0;
  [...box.children].forEach(ch => { if (ch.classList.contains('resizer')) { attachResizer(ch, node, ri, kidEls[ri], kidEls[ri + 1]); ri++; } });
  return box;
}
function attachResizer(rz, split, i, a, b) {
  rz.onmousedown = e => { e.preventDefault(); const horiz = split.dir === 'row'; const start = horiz ? e.clientX : e.clientY;
    const aS = horiz ? a.offsetWidth : a.offsetHeight, bS = horiz ? b.offsetWidth : b.offsetHeight;
    document.body.style.userSelect = 'none'; document.body.style.cursor = horiz ? 'col-resize' : 'row-resize';
    const mv = ev => { const d = (horiz ? ev.clientX : ev.clientY) - start; const na = aS + d, nb = bS - d; if (na < 80 || nb < 80) return; split.sizes[i] = na; split.sizes[i + 1] = nb; a.style.flex = `${na} 1 0`; b.style.flex = `${nb} 1 0`; };
    const up = () => { document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); document.body.style.userSelect = ''; document.body.style.cursor = ''; saveDock(); };
    document.addEventListener('mousemove', mv); document.addEventListener('mouseup', up); };
}
function renderGroup(group) {
  const g = document.createElement('div'); g.className = 'group'; g.dataset.gid = group.id;
  const body = document.createElement('div'); body.className = 'panel-content'; body.style.position = 'relative';
  const ov = document.createElement('div'); ov.className = 'dropzone-edge'; const zone = document.createElement('div'); zone.className = 'zone'; ov.appendChild(zone); body.appendChild(ov);
  const content = document.createElement('div'); content.className = 'pc-content'; body.appendChild(content);
  g.ondragover = e => { if (!state.drag) return; e.preventDefault(); showZone(zone, computeZone(g.getBoundingClientRect(), e.clientX, e.clientY)); };
  g.ondragleave = e => { if (!g.contains(e.relatedTarget)) zone.style.display = 'none'; };
  g.ondrop = e => { if (!state.drag) return; e.preventDefault(); const side = computeZone(g.getBoundingClientRect(), e.clientX, e.clientY); zone.style.display = 'none'; ui.handleDrop(group, state.drag.view, side); };
  g.appendChild(buildTabstrip(group)); g.appendChild(body);
  renderViewInto(group.active, content);
  return g;
}
function buildTabstrip(group) {
  const strip = document.createElement('div'); strip.className = 'tabstrip';
  group.tabs.forEach(v => { const tab = document.createElement('div'); tab.className = 'tab' + (v === group.active ? ' active' : ''); tab.draggable = true;
    tab.innerHTML = `${svg(meta(v).icon)} ${meta(v).label} <span class="x">${svg('close')}</span>`;
    tab.onclick = e => { if (e.target.closest('.x')) { removeViewFromGroup(v); saveDock(); renderDock(); } else { group.active = v; saveDock(); rerenderGroup(group); } };
    tab.ondragstart = e => { state.drag = { view: v }; tab.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; };
    tab.ondragend = () => { tab.classList.remove('dragging'); state.drag = null; }; strip.appendChild(tab); });
  const hidden = VIEWS.filter(v => !placedViews(state.dock).has(v.key));
  if (hidden.length) { const add = document.createElement('div'); add.className = 'tab'; add.innerHTML = svg('plus'); add.title = 'Add a panel'; add.onclick = e => addMenu(e, group, hidden); strip.appendChild(add); }
  return strip;
}
function addMenu(e, group, hidden) { e.stopPropagation(); const m = document.createElement('div'); m.className = 'addmenu';
  m.style.cssText = `position:fixed;left:${e.clientX}px;top:${e.clientY}px;background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:5px;box-shadow:var(--shadow);z-index:1000`;
  hidden.forEach(v => { const it = document.createElement('div'); it.style.cssText = 'padding:6px 12px;cursor:pointer;font-size:13px;border-radius:6px;display:flex;gap:7px;align-items:center'; it.innerHTML = svg(v.icon) + ' ' + v.label; it.onmouseenter = () => it.style.background = 'var(--panel-2)'; it.onmouseleave = () => it.style.background = ''; it.onclick = () => { group.tabs.push(v.key); group.active = v.key; saveDock(); renderDock(); m.remove(); }; m.appendChild(it); });
  document.body.appendChild(m);
  const r = m.getBoundingClientRect(); m.style.left = Math.max(6, Math.min(e.clientX, innerWidth - r.width - 8)) + 'px'; m.style.top = Math.max(6, Math.min(e.clientY, innerHeight - r.height - 8)) + 'px';
  setTimeout(() => document.addEventListener('click', () => m.remove(), { once: true }), 0);
}
function rerenderGroup(group) {
  // Update tab bar + content IN PLACE — never replace the .group element, or we'd lose its
  // inline flex sizing and the resizers' element references (which broke layout/resize).
  const gEl = document.querySelector(`.group[data-gid="${group.id}"]`); if (!gEl) { renderDock(); return; }
  gEl.querySelector('.tabstrip').replaceWith(buildTabstrip(group));
  renderViewInto(group.active, gEl.querySelector('.pc-content'));
}
function rerenderView(v) { const g = groupOfView(state.dock, v); if (g && g.active === v) { const c = document.querySelector(`.group[data-gid="${g.id}"] .pc-content`); if (c) renderViewInto(v, c); } }
function contentOf(v) { const g = groupOfView(state.dock, v); return g ? document.querySelector(`.group[data-gid="${g.id}"] .pc-content`) : null; }

// ---------- AI activity toast ----------
const aiToast = {
  show(label, cancelable) { const t = el('aiToast'); t.innerHTML = `<div class="tt-head">${svg('assistant')} <span>${esc(label)}</span>${cancelable ? '<button class="tt-stop" onclick="ui.cancelStream()">Stop</button>' : ''}</div><div class="tt-body" id="toastBody"></div>`; t.classList.remove('hidden'); if (this._t) clearTimeout(this._t); },
  body(text) { const b = el('toastBody'); if (b) b.textContent = text; },
  append(text) { const b = el('toastBody'); if (b) b.textContent = (b.textContent + text).slice(-600); },
  label(text) { const h = el('aiToast').querySelector('.tt-head span'); if (h) h.textContent = text; },
  done(label) { const t = el('aiToast'); const h = t.querySelector('.tt-head'); if (h) h.innerHTML = `${svg('bolt')} <span>${esc(label || 'Done')}</span>`; this.hide(2200); },
  hide(delay = 0) { if (this._t) clearTimeout(this._t); this._t = setTimeout(() => el('aiToast').classList.add('hidden'), delay); },
};

// ---------- modal ----------
function showModal(node) { closeModal(); const bd = document.createElement('div'); bd.className = 'modal-backdrop'; bd.id = 'modalBackdrop'; bd.appendChild(node); bd.addEventListener('mousedown', e => { if (e.target === bd) closeModal(); }); document.body.appendChild(bd); return bd; }
function closeModal() { const b = el('modalBackdrop'); if (b) b.remove(); }

function renderViewInto(view, c) {
  if (!c) return;
  const globals = { api: ui.viewApi, assistant: ui.viewAssistant, bench: ui.viewBench, research: ui.viewResearch };
  if (globals[view]) return globals[view].call(ui, c);
  if (!state.current) { c.innerHTML = '<div class="empty">Select or create a project on the left.</div>'; return; }
  ({ diagram: ui.viewDiagram, pinout: ui.viewPinout, plan: ui.viewPlan, chat: ui.viewChat, triage: ui.viewTriage, pcb: ui.viewPcb, memories: ui.viewMemories, record: ui.viewRecord })[view].call(ui, c);
}

// ================= UI =================
const ui = {
  async init() {
    document.documentElement.dataset.theme = state.theme;
    el('sidebarToggle').innerHTML = svg('menu'); el('themeToggle').innerHTML = svg(state.theme === 'dark' ? 'sun' : 'moon');
    el('resetBtn').innerHTML = svg('reset'); el('apiBtn').innerHTML = svg('api'); el('newRecBtn').innerHTML = svg('plus'); el('searchIcon').innerHTML = svg('search');
    el('assistantBtn').innerHTML = svg('assistant'); el('benchBtn').innerHTML = svg('bench'); el('researchBtn').innerHTML = svg('search'); el('logoutBtn').innerHTML = svg('logout');
    api.get('/api/auth/status').then(s => { if (s.auth) el('logoutBtn').classList.remove('hidden'); }).catch(() => {});
    el('fileInput').onchange = e => e.target.files[0] && this.uploadFile(e.target.files[0]);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && state.streamCtrl) this.cancelStream(); });
    state.dock = loadDock();
    this.checkHealth(); await this.loadRecords();
    if (state.records.length) await this.select(state.records[0].id); else renderDock();
  },
  async checkHealth() { try { const h = await api.get('/api/health'); el('statusDot').className = 'dot ' + (h.model_ready ? 'ok' : 'bad'); el('statusText').textContent = h.model_ready ? h.model : (h.models.length ? h.model + ' (not pulled)' : 'Ollama offline'); } catch { el('statusDot').className = 'dot bad'; el('statusText').textContent = 'Ollama offline'; } },

  toggleSidebar() { state.sidebar = !state.sidebar; el('sidebar').classList.toggle('collapsed', !state.sidebar); },
  toggleTheme() { state.theme = state.theme === 'dark' ? 'light' : 'dark'; document.documentElement.dataset.theme = state.theme; localStorage.setItem('canopy-theme', state.theme); el('themeToggle').innerHTML = svg(state.theme === 'dark' ? 'sun' : 'moon'); },
  async logout() { try { await api.send('/api/logout', 'POST'); } catch {} location.href = '/login'; },
  resetLayout() { state.dock = defaultDock(); saveDock(); renderDock(); },
  openView(v) { ensureView(v); },
  handleDrop(group, v, side) { const from = groupOfView(state.dock, v);
    if (side === 'center') { if (from !== group) { removeViewFromGroup(v); group.tabs.push(v); } group.active = v; }
    else { if (from === group && from.tabs.length === 1) { state.drag = null; return; } removeViewFromGroup(v); splitWith(group, v, side); }
    state.drag = null; saveDock(); renderDock(); },

  // ---------- records / projects ----------
  async loadRecords() { state.records = await api.get('/api/vehicles'); this.renderRecords(); },
  renderRecords() {
    const q = (el('projSearch')?.value || '').toLowerCase(), sort = el('projSort')?.value || 'recent', grp = el('projGroup')?.value || 'none';
    let recs = state.records.filter(v => { const hay = [v.label, v.vin, v.make, v.model, v.year, ...(v.tags || [])].join(' ').toLowerCase(); return !q || hay.includes(q); });
    recs = recs.slice().sort((a, b) => sort === 'title' ? (a.label || '').localeCompare(b.label || '') : (b.created_at || '').localeCompare(a.created_at || ''));
    const card = v => `<div class="rec-item ${state.current && state.current.id === v.id ? 'active' : ''}" onclick="ui.select(${v.id})">
      <div class="rec-actions"><button class="iconbtn" title="Rename" onclick="event.stopPropagation();ui.renameRecord(${v.id})">${svg('edit')}</button><button class="iconbtn danger" title="Delete" onclick="event.stopPropagation();ui.deleteRecord(${v.id})">${svg('trash')}</button></div>
      <div class="name">${esc(v.label || [v.year, v.make, v.model].filter(Boolean).join(' ') || 'Untitled')}</div>
      ${(v.tags || []).length ? `<div class="tags">${v.tags.slice(0, 6).map(t => `<span class="tagchip">${esc(t)}</span>`).join('')}</div>` : ''}</div>`;
    let html = '';
    if (grp === 'none') html = recs.map(card).join('');
    else { const groups = {}; recs.forEach(v => { const key = (v[grp] || (v.tags || []).find(Boolean) || '—'); (groups[key] = groups[key] || []).push(v); });
      html = Object.keys(groups).sort().map(k => `<div class="group-label">${esc(k)}</div>` + groups[k].map(card).join('')).join(''); }
    el('recordList').innerHTML = html || '<p class="muted" style="padding:8px">No projects. Create one with +.</p>';
  },
  async newRecord() { const v = await api.send('/api/vehicles', 'POST', { label: 'New project' }); await this.loadRecords(); this.select(v.id); },
  async select(id) { state.current = await api.get('/api/vehicles/' + id); state.page = 0; state.selectedPin = null; state.plan = ''; state.zoom = 1; state.triageMsgs = null; state.triageImage = null; state.pcbImage = null; state.pcbComponents = null; state.pcbSel = null; this.renderRecords(); renderDock(); },

  // ---------- diagram ----------
  viewDiagram(c) {
    const d = (state.current.diagrams || [])[0]; state.diagramId = d ? d.id : null; state.pageTotal = d ? (d.pages || 1) : 1;
    if (!d) { c.innerHTML = `<div id="dz" class="dropzone">${svg('upload')}<div style="margin-top:8px"><strong>Drop</strong> a wiring diagram (image or PDF), or click.</div></div>`; }
    else { const nav = state.pageTotal > 1 ? `<div class="pagenav"><button class="iconbtn" onclick="ui.pageStep(-1)">${svg('prev')}</button>
      <input type="number" min="1" max="${state.pageTotal}" value="${state.page + 1}" onchange="ui.gotoPage(this.value-1)"> / ${state.pageTotal}<button class="iconbtn" onclick="ui.pageStep(1)">${svg('next')}</button></div>` : '';
      c.innerHTML = `<div class="diag-toolbar"><button class="primary" onclick="ui.extract(false)" id="exBtn">${svg('bolt')} Extract page</button>
        <button onclick="ui.extract(true)" id="exAllBtn">All pages</button><button onclick="ui.identify()" id="idBtn">Identify</button>${nav}
        <div class="zoomctl"><button class="iconbtn" onclick="ui.zoom(-1)">${svg('zout')}</button><span id="zlbl">${Math.round(state.zoom * 100)}%</span><button class="iconbtn" onclick="ui.zoom(1)">${svg('zin')}</button><button class="iconbtn" title="Fit" onclick="ui.zoom(0)">${svg('reset')}</button></div></div>
        <div class="diag-scroll"><img id="diagImg" src="/api/diagram/${d.id}/image?page=${state.page}&t=${Date.now()}" style="width:${state.zoom * 100}%"></div>`; }
    const dz = c.querySelector('#dz'); if (dz) { dz.onclick = () => el('fileInput').click(); ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.toggle('drag', ev === 'dragover'); if (ev === 'drop' && e.dataTransfer.files[0]) this.uploadFile(e.dataTransfer.files[0]); })); }
  },
  zoom(dir) { state.zoom = dir === 0 ? 1 : Math.max(0.25, Math.min(5, state.zoom + dir * 0.25)); const img = el('diagImg'); if (img) img.style.width = (state.zoom * 100) + '%'; const z = el('zlbl'); if (z) z.textContent = Math.round(state.zoom * 100) + '%'; },
  pageStep(d) { this.gotoPage(state.page + d); },
  gotoPage(n) { state.page = Math.max(0, Math.min(state.pageTotal - 1, parseInt(n) || 0)); rerenderView('diagram'); },

  // ---------- pinout ----------
  viewPinout(c) {
    const pins = state.current.pinouts || []; let detail = '';
    if (state.selectedPin != null && pins[state.selectedPin]) { const p = pins[state.selectedPin]; const r = (l, v) => v ? `<div>${l}</div><div><b>${esc(v)}</b></div>` : '';
      detail = `<div class="pin-detail"><div class="pd-top"><span class="pd-pin">Pin ${esc(p.pin)}</span><span class="pd-sig">${esc(p.signal || '')}</span><span class="pd-close" onclick="ui.selectPin(null)">${svg('close')}</span></div>
        <div class="pd-func">${esc(p.function || 'No function recorded.')}</div><div class="pd-grid">${r('Connector', p.connector)}${r('Circuit', p.circuit)}${r('Wire', p.wire_color)}${r('Connects to', p.connects_to)}${r('Page', p.page != null ? p.page + 1 : '')}</div></div>`; }
    if (!pins.length) { c.innerHTML = `<div class="pin-sticky">${detail || ''}<input placeholder="Filter pins…" disabled></div><p class="muted">No pinout yet. On the Diagram, go to a connector page and click “Extract page”.</p>`; return; }
    const conns = [...new Set(pins.map(p => p.connector || ''))];
    let body = '';
    for (const conn of conns) { const g = pins.filter(p => (p.connector || '') === conn);
      body += `<div class="conn-group">${esc(conn || 'Connector')} · ${g.length}</div><table><tbody>${g.map(p => { const i = pins.indexOf(p), sc = sigClass(p.signal); const b = sc ? `<span class="badge ${sc}">${sc.toUpperCase()}</span> ` : '';
        return `<tr class="pin-row ${i === state.selectedPin ? 'sel' : ''}" onclick="ui.selectPin(${i})"><td style="width:42px"><b>${esc(p.pin)}</b></td><td>${b}${esc(p.signal)}</td><td class="muted">${esc(p.function || '')}</td></tr>`; }).join('')}</tbody></table>`; }
    c.innerHTML = `<div class="pin-sticky">${detail}<input placeholder="Filter pins…" oninput="ui.filterPins(this.value)"></div><div id="pinBody">${body}</div>`;
  },
  filterPins(q) { q = (q || '').toLowerCase(); document.querySelectorAll('#pinBody tr.pin-row').forEach(tr => tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none'); },
  selectPin(idx) { state.selectedPin = idx; if (idx != null) { const p = state.current.pinouts[idx]; if (p && p.page != null) { state.page = p.page; ensureView('diagram'); } } rerenderView('pinout'); rerenderView('diagram'); },
  gotoPinPage(n) { const p = pinIndex()[n]; if (p && p.page != null) { state.page = p.page; ensureView('diagram'); rerenderView('diagram'); } this.hideTip(); },
  pinTip(ev, n) { const p = pinIndex()[n]; if (!p) return; const t = el('tooltip'); t.innerHTML = `<div><span class="tt-pin">Pin ${esc(p.pin)}</span> <span class="tt-sig">${esc(p.signal || '')}</span></div><div class="tt-row">${esc(p.function || '')}</div>${p.connector ? `<div class="tt-row">${esc(p.connector)}${p.page != null ? ' · page ' + (p.page + 1) : ''} · click to open</div>` : ''}`; t.style.display = 'block'; t.style.left = Math.min(ev.clientX + 14, innerWidth - 300) + 'px'; t.style.top = (ev.clientY + 16) + 'px'; },
  hideTip() { el('tooltip').style.display = 'none'; },

  // ---------- plan ----------
  viewPlan(c) { c.innerHTML = `<div class="row" style="margin-bottom:10px"><button class="primary" onclick="ui.canPlan()" id="planBtn">${svg('bolt')} Generate CAN wiring plan</button></div>
    ${state.plan ? `<div class="md">${md(state.plan)}</div><p class="warn">${svg('warn')} Verify power &amp; ground pins by hand and set the PSU current limit before energizing.</p>` : '<p class="muted">Generates a bench connection plan from the extracted pinout. Pin numbers are hover-able.</p>'}`; },

  // ---------- chat ----------
  viewChat(c) { const msgs = state.current.messages || [];
    c.innerHTML = `<div class="chat"><div class="chips">
      <span class="chip" onclick="ui.ask('How do I wire this module to communicate over CAN?')">Wire for CAN</span>
      <span class="chip" onclick="ui.ask('How can I simulate a test on the A/C clutch relay in this vehicle?')">Simulate A/C clutch relay</span>
      <span class="chip" onclick="ui.ask('Which pins are power, ground, CAN-H and CAN-L?')">Power/GND/CAN pins</span></div>
      <div class="messages" id="msgs">${msgs.map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('')}</div>
      <div class="chat-input"><textarea id="chatIn" placeholder="Ask about this diagram…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();ui.send();}"></textarea><button class="primary" onclick="ui.send()">Send</button></div>
      <label class="toggle"><input type="checkbox" id="autoMem" checked> Auto-save new, salient facts to memory</label></div>`;
    const m = el('msgs'); if (m) m.scrollTop = m.scrollHeight; },

  // ---------- memories ----------
  viewMemories(c) { const mems = state.current.memories || [];
    c.innerHTML = `<div class="chat-input" style="margin-bottom:12px"><input id="memIn" placeholder="Add a fact to remember…"><button onclick="ui.addMemory()">Save</button></div>
      ${mems.map(m => `<div class="memory"><span class="kind ${m.kind === 'auto' ? 'auto' : ''}">${esc(m.kind)}</span><div style="flex:1">${esc(m.content)}</div><button class="iconbtn danger" onclick="ui.delMemory(${m.id})">${svg('close')}</button></div>`).join('') || '<p class="muted">No memories yet — saved manually or auto-distilled from chat (semantically de-duplicated).</p>'}`; },

  // ---------- record + tags ----------
  viewRecord(c) { const v = state.current;
    c.innerHTML = `<h3 class="sec">Project details</h3>
      <label class="field"><span>Label</span><input id="f_label" value="${esc(v.label || '')}" placeholder="e.g. 2016 F-250 PCM"></label>
      <div class="row"><label class="field" style="flex:2"><span>VIN</span><input id="f_vin" value="${esc(v.vin || '')}"></label><label class="field"><span>Year</span><input id="f_year" value="${esc(v.year || '')}"></label></div>
      <div class="row"><label class="field" style="flex:1"><span>Make</span><input id="f_make" value="${esc(v.make || '')}"></label><label class="field" style="flex:1"><span>Model</span><input id="f_model" value="${esc(v.model || '')}"></label></div>
      <div class="row" style="margin-bottom:14px"><button class="primary" onclick="ui.saveVehicle()">Save</button><button onclick="ui.identify()">Identify from diagram</button><button class="ghost danger" onclick="ui.deleteVehicle()">Delete</button></div>
      <h3 class="sec">Tags</h3><div class="tags" style="margin-bottom:10px">${(v.tags || []).map(t => `<span class="tagchip rm" onclick="ui.removeTag('${esc(t).replace(/'/g, "")}')">${esc(t)} ✕</span>`).join('') || '<span class="muted">No tags.</span>'}</div>
      <div class="chat-input"><input id="tagIn" placeholder="Add a tag (e.g. Duramax)" onkeydown="if(event.key==='Enter')ui.addTag()"><button onclick="ui.addTag()">${svg('tag')} Add</button><button onclick="ui.extractTags()" id="tagAiBtn">${svg('bolt')} AI tags</button></div>`; },

  // ---------- api docs ----------
  async viewApi(c) { if (!state.apiRef) { c.innerHTML = '<p class="muted">Loading API reference…</p>'; try { state.apiRef = await api.get('/api/reference'); } catch { c.innerHTML = '<p class="warn">Could not load reference.</p>'; return; } }
    const ref = state.apiRef;
    c.innerHTML = `<h3 class="sec">REST API</h3><p class="muted">All endpoints are local. Interactive Swagger: <a href="${ref.swagger}" target="_blank">${ref.swagger}</a> · OpenAPI: <a href="${ref.openapi}" target="_blank">${ref.openapi}</a> (import into Postman).</p>
      ${ref.groups.map(gr => `<div class="api-group"><h4>${esc(gr.group)}</h4>${gr.endpoints.map(e => `<div class="api-ep"><div><span class="m">${esc(e.method)}</span> <span class="p">${esc(e.path)}</span></div><div class="u">${esc(e.use)}</div>${e.example ? `<pre>${esc(e.example)}</pre>` : ''}</div>`).join('')}</div>`).join('')}`; },

  // ---------- project CRUD from sidebar ----------
  async renameRecord(id) { const v = state.records.find(r => r.id === id); const name = prompt('Project name', v ? (v.label || '') : ''); if (name == null) return; await api.send('/api/vehicles/' + id, 'PATCH', { label: name.trim() }); if (state.current && state.current.id === id) state.current.label = name.trim(); await this.loadRecords(); if (state.current && state.current.id === id) rerenderView('record'); },
  async deleteRecord(id) { if (!confirm('Delete this project and its diagrams/memories?')) return; await api.send('/api/vehicles/' + id, 'DELETE'); if (state.current && state.current.id === id) { state.current = null; renderDock(); } await this.loadRecords(); },
  cancelModal() { closeModal(); },

  // ---------- actions ----------
  async uploadFile(file) {
    if (!state.current) return;
    try { await api.upload(`/api/vehicles/${state.current.id}/diagram`, file); } catch (e) { alert('Upload failed: ' + e.message); return; }
    state.current = await api.get('/api/vehicles/' + state.current.id); state.page = 0; ensureView('diagram'); renderDock();
    this.analyzeAndConfirm();
  },
  async analyzeAndConfirm() {
    const m = document.createElement('div'); m.className = 'modal';
    m.innerHTML = `<div class="m-head">${svg('bolt')} Analyze wiring diagram</div><div class="m-sub">Reading the diagram to identify this project…</div><div class="m-body" id="mBody"><div class="thinking" style="padding:18px 0"><span class="spinner"></span> analyzing…</div></div>`;
    showModal(m);
    let s; try { s = await api.send(`/api/vehicles/${state.current.id}/suggest`, 'POST', { page: 0 }); }
    catch (e) { const b = el('mBody'); if (b) b.innerHTML = `<p class="warn">${svg('warn')} ${esc(e.message)}</p>`; m.insertAdjacentHTML('beforeend', `<div class="m-foot"><button class="primary" onclick="closeModal()">Close</button></div>`); return; }
    el('mBody').innerHTML = `
      <label class="field"><span>Project name</span><input id="mLabel" value="${esc(s.label || '')}"></label>
      <div class="row"><label class="field" style="flex:2"><span>VIN</span><input id="mVin" value="${esc(s.vin || '')}"></label><label class="field"><span>Year</span><input id="mYear" value="${esc(s.year || '')}"></label></div>
      <div class="row"><label class="field" style="flex:1"><span>Make</span><input id="mMake" value="${esc(s.make || '')}"></label><label class="field" style="flex:1"><span>Model</span><input id="mModel" value="${esc(s.model || '')}"></label></div>
      <div class="row"><label class="field" style="flex:1"><span>Module type</span><input id="mModule" value="${esc(s.module_type || '')}"></label><label class="field" style="flex:1"><span>Engine / spec</span><input id="mEngine" value="${esc(s.engine || '')}"></label></div>
      <label class="field"><span>Tags (comma-separated)</span><input id="mTags" value="${esc((s.tags || []).join(', '))}"></label>
      <div class="opts"><span class="muted">After confirming, automatically:</span>
        <label><input type="checkbox" id="optPin" checked> Extract pinout from <select id="optPinScope" style="width:auto;display:inline-block">${state.pageTotal > 1 ? '<option value="page">current page</option><option value="all">all ' + state.pageTotal + ' pages</option>' : '<option value="page">the diagram</option>'}</select></label>
        <label><input type="checkbox" id="optPlan"> Generate CAN wiring plan</label>
        <label><input type="checkbox" id="optMem" checked> Extract memories</label></div>`;
    m.insertAdjacentHTML('beforeend', `<div class="m-foot"><span class="m-status" id="mStatus"></span><button class="ghost" onclick="ui.cancelModal()">Cancel</button><button class="primary" id="mGo" onclick="ui.runPipeline()">Confirm &amp; extract</button></div>`);
  },
  async runPipeline() {
    const id = state.current.id, g = x => el(x) ? el(x).value.trim() : '';
    const status = el('mStatus'), go = el('mGo'); if (go) go.disabled = true;
    const set = t => { if (status) status.innerHTML = `<span class="spinner"></span> ${esc(t)}`; aiToast.show(t); };
    try {
      set('saving details…');
      await api.send('/api/vehicles/' + id, 'PATCH', { label: g('mLabel'), vin: g('mVin'), year: g('mYear'), make: g('mMake'), model: g('mModel') });
      const tags = g('mTags').split(',').map(t => t.trim()).filter(Boolean); const mod = g('mModule'); if (mod && !tags.some(t => t.toLowerCase() === mod.toLowerCase())) tags.push(mod);
      for (const t of tags) await api.send(`/api/vehicles/${id}/tags`, 'POST', { tag: t });
      if (el('optPin') && el('optPin').checked) { const all = el('optPinScope').value === 'all'; set(all ? `extracting pinout (all ${state.pageTotal} pages)…` : 'extracting pinout…'); await api.send(`/api/vehicles/${id}/extract`, 'POST', { page: state.page, all_pages: all }); }
      if (el('optPlan') && el('optPlan').checked) { set('generating wiring plan…'); const r = await api.send(`/api/vehicles/${id}/can-plan`, 'POST', { page: state.page }); state.plan = r.plan; }
      if (el('optMem') && el('optMem').checked) { set('extracting memories…'); await api.send(`/api/vehicles/${id}/extract-memories`, 'POST', { page: state.page }); }
      aiToast.done('Project ready'); closeModal(); state.current = await api.get('/api/vehicles/' + id); await this.loadRecords(); renderDock();
    } catch (e) { aiToast.done('Error'); if (status) status.innerHTML = `<span class="warn">${esc(e.message)}</span>`; if (go) go.disabled = false; }
  },

  // ---------- global assistant ----------
  viewAssistant(c) {
    const msgs = state.assistantMsgs || [];
    c.innerHTML = `<div class="chat"><div class="chips">
        <span class="chip" onclick="ui.askAssistant('How do I confirm CAN connectivity to an ECU on the bench?')">Confirm CAN connectivity</span>
        <span class="chip" onclick="ui.askAssistant('How can I verify the A/C clutch relay output from an ECM over CAN?')">Test A/C clutch relay</span>
        <span class="chip" onclick="ui.askAssistant('Compare the CAN bus pins across the vehicles I have analyzed.')">Compare CAN pins</span></div>
      <div class="messages" id="aMsgs">${msgs.map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('') || '<div class="empty">Ask anything. I draw on the accumulated knowledge from every project you have analyzed.</div>'}</div>
      <div class="chat-input"><textarea id="aIn" placeholder="Ask across all projects…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();ui.sendAssistant();}"></textarea><button class="primary" onclick="ui.sendAssistant()">Send</button></div></div>`;
    const m = el('aMsgs'); if (m) m.scrollTop = m.scrollHeight;
  },
  askAssistant(q) { ensureView('assistant'); const i = el('aIn'); if (i) i.value = q; this.sendAssistant(q); },
  async sendAssistant(forced) {
    const input = el('aIn'); const q = (forced || (input ? input.value : '')).trim(); if (!q) return; if (input) input.value = '';
    state.assistantMsgs = state.assistantMsgs || [];
    const box = el('aMsgs'); if (box && box.querySelector('.empty')) box.innerHTML = '';
    box.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(q)}</div></div>`);
    const aId = 'as' + Date.now(); box.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="${aId}"><div class="thinking"><span class="spinner"></span> thinking…</div><div class="md cursor-blink" id="${aId}-md"></div></div>`); box.scrollTop = box.scrollHeight;
    const history = state.assistantMsgs.slice(-8); state.assistantMsgs.push({ role: 'user', content: q }); let full = '';
    aiToast.show('Assistant thinking…', true);
    await this.stream('/api/assistant/chat/stream', { message: q, history },
      tok => { full += tok; aiToast.append(tok); const t = el(aId)?.querySelector('.thinking'); if (t) t.remove(); const m = el(aId + '-md'); if (m) { m.innerHTML = md(full); const b = el('aMsgs'); if (b) b.scrollTop = b.scrollHeight; } },
      () => { aiToast.done('Answered'); const m = el(aId + '-md'); if (m) m.classList.remove('cursor-blink'); state.assistantMsgs.push({ role: 'assistant', content: full }); },
      e => { aiToast.done('Error'); const x = el(aId); if (x) x.innerHTML = `<span class="warn">${esc(e)}</span>`; });
  },

  // ---------- CAN bench ----------
  viewBench(c) {
    const acts = (state.current?.pinouts || []).filter(p => /relay|ctrl|control|sol|actuat|accr|output/i.test(p.signal || p.function || ''));
    const hints = acts.length ? `<div class="muted" style="margin-top:8px">Actuator-like pins on <b>${esc(state.current.label || 'this project')}</b>: ${acts.slice(0, 8).map(p => `<span class="tagchip">pin ${esc(p.pin)} ${esc(p.signal)}</span>`).join(' ')}<br>Commanding these needs the ECU's specific UDS routine/output-control id (service 0x2F/0x31).</div>` : '';
    c.innerHTML = `
      <div class="bench-status" id="benchStatus"><span class="dot"></span> checking…</div>
      <div class="bench-section"><h4>${svg('link')} Connection</h4>
        <div class="row"><select id="bIface" style="flex:1"></select><input id="bChannel" placeholder="can0" value="vcan0" style="width:110px"><input id="bBitrate" value="500000" style="width:95px" title="bitrate">
          <button class="primary" id="bConnectBtn" onclick="ui.benchConnect()">Connect</button><button onclick="ui.benchDisconnect()">Disconnect</button></div>
        <div class="muted" style="margin-top:6px">Pick a SocketCAN device (USB-to-CAN adapter or vcan0), or 'virtual' for a dry run.</div></div>
      <div class="bench-section"><h4>Probe ECU</h4>
        <div class="row"><input id="bReq" value="0x7E0" style="width:90px" title="request id"><input id="bRsp" value="0x7E8" style="width:90px" title="response id"><button class="primary" onclick="ui.benchPing()">Ping &amp; confirm connectivity</button></div>
        <div id="bPingOut" class="kvp" style="margin-top:9px"></div></div>
      <div class="bench-section"><h4>UDS request (read data / actuator output control)</h4>
        <div class="muted" style="margin-bottom:6px">Hex payload — e.g. <code>22F190</code> read VIN · <code>1902FF</code> read DTCs · <code>2F&lt;did&gt;03&lt;state&gt;</code> output control.</div>
        <div class="row"><input id="bUReq" value="0x7E0" style="width:90px"><input id="bURsp" value="0x7E8" style="width:90px"><input id="bUPayload" placeholder="22F190" style="flex:1"><button onclick="ui.benchUds()">Send UDS</button></div>
        <div id="bUdsOut" class="muted" style="margin-top:8px"></div>${hints}</div>
      <div class="bench-section"><h4>Send raw frame</h4>
        <div class="row"><input id="bFid" placeholder="123" style="width:90px"><input id="bFdata" placeholder="DE AD BE EF" style="flex:1"><button onclick="ui.benchSend()">Send</button></div></div>
      <div class="bench-section"><h4>Live traffic</h4><div class="frame-log" id="bFrames"><span class="muted">Connect to see frames.</span></div></div>`;
    this.benchLoadInterfaces(); this.benchRefreshStatus();
  },
  async benchLoadInterfaces() {
    try { const list = await api.get('/api/can/interfaces'); const sel = el('bIface'); if (!sel) return;
      sel.innerHTML = list.map(i => `<option value="${i.interface}|${i.channel}">${esc(i.channel)} (${esc(i.interface)}${i.state ? ' · ' + esc(i.state) : ''})</option>`).join(''); } catch {}
  },
  async benchRefreshStatus() {
    let s; try { s = await api.get('/api/can/status'); } catch { return; }
    const el2 = el('benchStatus'); if (!el2) return;
    el2.innerHTML = s.connected ? `<span class="dot ok"></span> Connected to <b>${esc(s.channel)}</b> · ${s.frames} frames` : `<span class="dot"></span> Not connected`;
    if (s.connected && !state.benchTimer) this.benchPoll(); if (!s.connected && state.benchTimer) { clearInterval(state.benchTimer); state.benchTimer = null; }
  },
  async benchConnect() {
    const v = (el('bIface').value || 'socketcan|vcan0').split('|');
    await this.busy('bConnectBtn', 'connecting…', async () => {
      await api.send('/api/can/connect', 'POST', { interface: v[0], channel: el('bChannel').value || v[1], bitrate: parseInt(el('bBitrate').value) || 500000 });
      state.benchSince = 0; this.benchRefreshStatus();
    });
  },
  async benchDisconnect() { await api.send('/api/can/disconnect', 'POST'); if (state.benchTimer) { clearInterval(state.benchTimer); state.benchTimer = null; } this.benchRefreshStatus(); },
  benchPoll() { state.benchTimer = setInterval(async () => { const log = el('bFrames'); if (!log) { clearInterval(state.benchTimer); state.benchTimer = null; return; } try { const r = await api.get('/api/can/frames?since=' + (state.benchSince || 0)); for (const f of r.frames) { state.benchSince = f.seq; log.insertAdjacentHTML('afterbegin', `<div class="fr"><span class="fid">${f.id}</span>${f.ext ? 'x' : ''} ${f.data}</div>`); } while (log.children.length > 200) log.lastChild.remove(); } catch {} }, 1000); },
  async benchPing() {
    const out = el('bPingOut'); out.innerHTML = '<span class="spinner"></span> probing…'; aiToast.show('Pinging ECU…');
    try { const r = await api.send('/api/can/ping', 'POST', { request_id: el('bReq').value, response_id: el('bRsp').value });
      aiToast.done(r.connected ? 'ECU responding' : 'No response');
      out.innerHTML = `<div>Connectivity</div><div><span class="ok-badge ${r.connected ? 'yes' : 'no'}">${r.connected ? 'CONNECTED' : 'NO RESPONSE'}</span></div>` +
        (r.vin ? `<div>VIN</div><div><b>${esc(r.vin)}</b></div>` : '') + (r.dtc_count != null ? `<div>Stored DTCs</div><div><b>${r.dtc_count}</b></div>` : '');
    } catch (e) { aiToast.done('Error'); out.innerHTML = `<span class="warn">${esc(e.message)}</span>`; }
  },
  async benchUds() {
    const out = el('bUdsOut'); out.innerHTML = '<span class="spinner"></span> sending…';
    try { const r = await api.send('/api/can/uds', 'POST', { request_id: el('bUReq').value, response_id: el('bURsp').value, payload: el('bUPayload').value });
      out.innerHTML = r.ok ? `<span class="ok-badge yes">OK</span> response: <code>${esc(r.response)}</code>` : `<span class="ok-badge no">${r.nrc ? 'NRC ' + r.nrc : 'FAIL'}</span> ${esc(r.error || r.response || '')}`;
    } catch (e) { out.innerHTML = `<span class="warn">${esc(e.message)}</span>`; }
  },
  async benchSend() {
    try { await api.send('/api/can/send', 'POST', { id: el('bFid').value, data: el('bFdata').value }); } catch (e) { alert(e.message); }
  },

  // ---------- guided repair triage ----------
  viewTriage(c) {
    c.innerHTML = `<div class="chat"><div class="chips">
        <span class="chip" onclick="ui.fillTriage('The symptom is: ')">Describe symptom</span>
        <span class="chip" onclick="ui.attachTriagePhoto()">${svg('upload')} Attach photo</span>
        <span class="chip" onclick="ui.phoneModal()">${svg('phone')} Pair phone</span>
        <span class="chip" onclick="ui.askTriage('Analyze the attached PCB photo: identify the components and what to check on each, and which tool to use.')">Analyze PCB</span>
        <span class="chip" onclick="ui.askTriage('Which serial/diagnostic protocols does this module use, and which OBD-II pins are relevant?')">Protocols / OBD-II</span>
        <span class="chip" onclick="ui.triageReport()">Generate report</span></div>
      <div class="messages" id="tMsgs"><div class="empty"><span class="spinner"></span></div></div>
      <div id="tAttach" class="muted" style="font-size:11.5px;min-height:16px"></div>
      <div class="chat-input"><textarea id="tIn" placeholder="Describe what you see / measured; ask for the next step…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();ui.sendTriage();}"></textarea>
        <button class="iconbtn" title="Attach photo" onclick="ui.attachTriagePhoto()">${svg('upload')}</button><button class="primary" onclick="ui.sendTriage()">Send</button></div>
      <div class="muted" style="margin-top:5px;font-size:11px">Guided diagnosis using this project's pinout + accumulated knowledge. Attach photos of the board, scope, or meter.</div></div>`;
    if (state.triageMsgs == null) this.loadTriage(); else this.renderTriageMsgs();
    if (state.triageImage) { const a = el('tAttach'); if (a) a.textContent = 'photo attached — sends with your next message'; }
  },
  async loadTriage() { try { state.triageMsgs = await api.get(`/api/vehicles/${state.current.id}/triage/messages`); } catch { state.triageMsgs = []; } this.renderTriageMsgs(); },
  renderTriageMsgs() { const box = el('tMsgs'); if (!box) return; const msgs = state.triageMsgs || []; box.innerHTML = msgs.map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('') || '<div class="empty">Start a guided triage — describe the symptom or attach a board photo.</div>'; box.scrollTop = box.scrollHeight; },
  fillTriage(q) { ensureView('triage'); const i = el('tIn'); if (i) { i.value = q; i.focus(); } },
  askTriage(q) { ensureView('triage'); this.sendTriage(q); },
  attachTriagePhoto() {
    if (!state.triageFileInput) { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
      inp.onchange = e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => { state.triageImage = r.result; const a = el('tAttach'); if (a) a.textContent = 'photo attached — sends with your next message'; }; r.readAsDataURL(f); };
      state.triageFileInput = inp; }
    state.triageFileInput.value = ''; state.triageFileInput.click();
  },
  async sendTriage(forced) {
    const input = el('tIn'); const q = (forced || (input ? input.value : '')).trim(); if (!q || !state.current) return; if (input) input.value = '';
    const box = el('tMsgs'); if (box && box.querySelector('.empty')) box.innerHTML = '';
    const img = state.triageImage; state.triageImage = null; const a = el('tAttach'); if (a) a.textContent = '';
    box.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(q)}</div>${img ? `<img src="${img}" style="max-width:170px;border-radius:8px;margin-top:6px;display:block">` : ''}</div>`);
    const aId = 't' + Date.now(); box.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="${aId}"><div class="thinking"><span class="spinner"></span> thinking…</div><div class="md cursor-blink" id="${aId}-md"></div></div>`); box.scrollTop = box.scrollHeight;
    const history = (state.triageMsgs || []).slice(-8); state.triageMsgs = [...(state.triageMsgs || []), { role: 'user', content: q }]; let full = '';
    aiToast.show('Triaging…', true);
    await this.stream(`/api/vehicles/${state.current.id}/triage/stream`, { message: q, image: img || '', history },
      tok => { full += tok; aiToast.append(tok); const t = el(aId)?.querySelector('.thinking'); if (t) t.remove(); const m = el(aId + '-md'); if (m) { m.innerHTML = md(full); const b = el('tMsgs'); if (b) b.scrollTop = b.scrollHeight; } },
      () => { aiToast.done('Done'); const m = el(aId + '-md'); if (m) m.classList.remove('cursor-blink'); state.triageMsgs.push({ role: 'assistant', content: full }); },
      e => { aiToast.done('Error'); const x = el(aId); if (x) x.innerHTML = `<span class="warn">${esc(e)}</span>`; });
  },
  async triageReport() {
    if (!state.current) return; aiToast.show('Writing report…');
    try { const r = await api.send(`/api/vehicles/${state.current.id}/report`, 'POST'); state.lastReport = r.report; aiToast.done('Report ready');
      const m = document.createElement('div'); m.className = 'modal'; m.style.width = 'min(760px,94vw)';
      m.innerHTML = `<div class="m-head">${svg('record')} Repair report</div><div class="m-body md" style="max-height:68vh;overflow:auto">${md(r.report)}</div><div class="m-foot"><button onclick="ui.copyReport()">Copy Markdown</button><button class="primary" onclick="closeModal()">Close</button></div>`;
      showModal(m);
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  copyReport() { if (state.lastReport) navigator.clipboard?.writeText(state.lastReport); aiToast.show('Copied'); aiToast.hide(1200); },

  // ---------- PCB photo analysis (boxed components) ----------
  viewPcb(c) {
    if (!state.pcbComponents) {
      c.innerHTML = `<div id="pcbDz" class="dropzone">${svg('chip')}<div style="margin-top:8px"><strong>Drop a PCB photo</strong> (the ECU/module board), or click.</div><div class="muted" style="margin-top:4px">CANOPY boxes the components it recognizes and tells you what to check on each.</div></div>
        <div class="row" style="margin-top:10px;justify-content:center"><button onclick="ui.phoneModal()">${svg('phone')} Pair phone to snap a photo</button></div>`;
      const dz = c.querySelector('#pcbDz'); if (dz) { dz.onclick = () => this.pcbPick();
        ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.toggle('drag', ev === 'dragover'); if (ev === 'drop' && e.dataTransfer.files[0]) this.pcbUpload(e.dataTransfer.files[0]); })); }
      return;
    }
    const comps = state.pcbComponents;
    const sel = state.pcbSel != null ? comps[state.pcbSel] : null;
    const boxes = comps.map((p, i) => { const [x0, y0, x1, y1] = p.box; const on = i === state.pcbSel;
      return `<div class="pcb-box ${on ? 'sel' : 'dim'}" style="left:${x0 * 100}%;top:${y0 * 100}%;width:${(x1 - x0) * 100}%;height:${(y1 - y0) * 100}%" onclick="ui.selectPcb(${i})">${on ? `<span class="lbl">${esc(p.label)}</span>` : ''}</div>`; }).join('');
    c.innerHTML = `<div class="pcb-col">
      <div class="row" style="margin-bottom:8px"><button onclick="ui.pcbPick()">${svg('upload')} New photo</button><button onclick="ui.phoneModal()">${svg('phone')} Pair phone</button><button onclick="ui.exportPcb()">${svg('chip')} Save annotated PNG</button></div>
      <div class="pcb-layout">
        <div class="pcb-stage"><div class="pcb-wrap"><img src="${state.pcbImage}" alt="PCB"><div style="position:absolute;inset:0">${boxes}</div></div></div>
        <div class="pcb-side">
          <div class="muted" style="font-size:11px;margin-bottom:6px">${comps.length} components — click one to highlight it on the board</div>
          <div class="pcb-list">${comps.map((p, i) => `<div class="pcb-item ${i === state.pcbSel ? 'sel' : ''}" onclick="ui.selectPcb(${i})"><div class="pi-top"><span class="pi-label">${esc(p.label)}</span><span class="pi-conf">${Math.round(p.confidence * 100)}%</span></div><div class="pi-detail">${esc(p.check)}</div></div>`).join('')}</div>
          ${sel ? `<div class="pcb-detail"><div style="display:flex;align-items:center;gap:8px"><b style="font-size:14px">${esc(sel.label)}</b>${sel.part ? `<span class="tagchip">${esc(sel.part)}</span>` : ''}<span style="margin-left:auto;color:var(--muted);font-size:11px">conf ${Math.round(sel.confidence * 100)}%</span></div>
            <div style="margin:6px 0;font-size:13px">${esc(sel.function)}</div><div class="warn" style="color:var(--cyan)">Check: ${esc(sel.check)}</div>
            <button class="primary" style="margin-top:8px;width:100%" onclick="ui.pcbToTriage(${state.pcbSel})">${svg('triage')} Send to Triage</button></div>` : '<div class="pcb-detail muted" style="font-size:12px">Select a component to see its function, what to check, and send it to Triage.</div>'}
        </div>
      </div></div>`;
  },
  async exportPcb() {
    if (!state.pcbImage) return; aiToast.show('Rendering annotated image…');
    try {
      const img = new Image(); img.src = state.pcbImage; await img.decode();
      const cv = document.createElement('canvas'); cv.width = img.naturalWidth; cv.height = img.naturalHeight;
      const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0);
      const lw = Math.max(2, cv.width / 450); const fs = Math.max(13, cv.width / 75); ctx.font = `bold ${fs}px sans-serif`; ctx.textBaseline = 'bottom';
      (state.pcbComponents || []).forEach((p, i) => { const [x0, y0, x1, y1] = p.box; const x = x0 * cv.width, y = y0 * cv.height, w = (x1 - x0) * cv.width, h = (y1 - y0) * cv.height;
        const on = i === state.pcbSel; ctx.lineWidth = on ? lw * 1.6 : lw; ctx.strokeStyle = on ? '#0f9d6b' : '#0e8aa6';
        ctx.strokeRect(x, y, w, h); const tw = ctx.measureText(p.label).width; ctx.fillStyle = on ? '#0f9d6b' : '#0e8aa6'; ctx.fillRect(x, y - fs - 4, tw + 10, fs + 4); ctx.fillStyle = '#fff'; ctx.fillText(p.label, x + 5, y - 2); });
      const a = document.createElement('a'); a.href = cv.toDataURL('image/png'); a.download = `${(state.current.label || 'pcb').replace(/[^\w.-]/g, '_')}_annotated.png`; a.click();
      aiToast.done('Saved annotated PNG');
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  pcbPick() { if (!state.pcbFileInput) { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*'; inp.onchange = e => { if (e.target.files[0]) this.pcbUpload(e.target.files[0]); }; state.pcbFileInput = inp; } state.pcbFileInput.value = ''; state.pcbFileInput.click(); },
  async pcbUpload(file) {
    const r = new FileReader(); r.onload = async () => { state.pcbImage = r.result; state.pcbSel = null;
      await this.busy(null, 'analyzing board…', async () => { aiToast.show('Analyzing PCB…');
        const res = await api.send(`/api/vehicles/${state.current.id}/pcb`, 'POST', { image: r.result });
        state.pcbComponents = res.components || []; rerenderView('pcb'); aiToast.done(`${state.pcbComponents.length} components`); });
    }; r.readAsDataURL(file);
  },
  selectPcb(i) { state.pcbSel = state.pcbSel === i ? null : i; rerenderView('pcb'); },
  pcbToTriage(i) { state.triageImage = state.pcbImage; ensureView('triage'); const sel = i != null ? state.pcbComponents[i] : null;
    const txt = sel ? `About the ${sel.label} on this board: ` : 'Here is the ECU board photo. The symptom is: ';
    const inp = el('tIn'); if (inp) { inp.value = txt; inp.focus(); } const a = el('tAttach'); if (a) a.textContent = 'board photo attached — sends with your next message'; },

  // ---------- phone pairing ----------
  phoneModal() {
    if (!state.current) return; const id = state.current.id;
    const m = document.createElement('div'); m.className = 'modal'; m.style.width = 'min(520px,94vw)';
    m.innerHTML = `<div class="m-head">${svg('phone')} Pair a phone</div><div class="m-sub">Scan with your phone's camera (same Wi-Fi / VPN). Photos you take appear here and can go straight into PCB analysis or Triage.</div>
      <div class="m-body" style="text-align:center"><img src="/api/vehicles/${id}/pair/qr?t=${Date.now()}" style="width:210px;height:210px;border-radius:10px;border:1px solid var(--border)">
        <div class="muted" id="phoneUrl" style="font-size:11px;margin-top:6px;word-break:break-all"></div>
        <div id="phoneGal" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:14px"></div></div>
      <div class="m-foot"><button class="primary" onclick="closeModal()">Done</button></div>`;
    showModal(m);
    api.get(`/api/vehicles/${id}/pair`).then(d => { const u = el('phoneUrl'); if (u) u.textContent = d.url; }).catch(() => {});
    state.phoneSeen = new Set();
    const t = setInterval(async () => { const gal = el('phoneGal'); if (!gal) { clearInterval(t); return; }
      try { const list = await api.get(`/api/vehicles/${id}/attachments`);
        for (const a of list.slice().reverse()) { if (a.kind !== 'phone' || state.phoneSeen.has(a.id)) continue; state.phoneSeen.add(a.id);
          gal.insertAdjacentHTML('afterbegin', `<div><img src="/api/attachment/${a.id}/image" style="width:100%;border-radius:8px;border:1px solid var(--border)"><div class="row" style="gap:4px;margin-top:3px;justify-content:center"><button class="ghost" style="font-size:10px;padding:3px 7px" onclick="ui.phoneUse(${a.id},'pcb')">PCB</button><button class="ghost" style="font-size:10px;padding:3px 7px" onclick="ui.phoneUse(${a.id},'triage')">Triage</button></div></div>`); }
      } catch {} }, 2000);
  },
  async fetchDataUrl(url) { const r = await fetch(url); const b = await r.blob(); return new Promise(res => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(b); }); },
  async phoneUse(attId, target) {
    const dataUrl = await this.fetchDataUrl(`/api/attachment/${attId}/image`); closeModal();
    if (target === 'pcb') { state.pcbImage = dataUrl; state.pcbSel = null; ensureView('pcb'); aiToast.show('Analyzing PCB…');
      try { const res = await api.send(`/api/vehicles/${state.current.id}/pcb`, 'POST', { image: dataUrl }); state.pcbComponents = res.components || []; rerenderView('pcb'); aiToast.done(`${state.pcbComponents.length} components`); }
      catch (e) { aiToast.done('Error'); alert(e.message); }
    } else { state.triageImage = dataUrl; ensureView('triage'); const i = el('tIn'); if (i) { i.value = 'Here is a photo of the board: '; i.focus(); } const a = el('tAttach'); if (a) a.textContent = 'phone photo attached — sends with your next message'; }
  },

  // ---------- deep research ----------
  viewResearch(c) {
    const v = state.current;
    const seed = v ? [v.year, v.make, v.model, v.tags && v.tags.includes('PCM') ? 'PCM' : ''].filter(Boolean).join(' ') + ' connector pinout' : '';
    c.innerHTML = `
      <div class="row" style="margin-bottom:10px"><input id="resQ" value="${esc(seed)}" placeholder="e.g. 2007 Silverado TCM connector harness pinout photo" style="flex:1" onkeydown="if(event.key==='Enter')ui.doResearch()"><button class="primary" id="resBtn" onclick="ui.doResearch()">${svg('search')} Search</button></div>
      <div class="muted" style="margin-bottom:10px">Finds connector/harness photos, physical pin layouts, OBD-II pinouts and protocol references with sourced links you can triage.${v ? ' Results can be saved to <b>' + esc(v.label || 'this project') + '</b> as references.' : ''}</div>
      <div id="resOut"></div>`;
  },
  async doResearch() {
    const q = el('resQ').value.trim(); if (!q) return; const out = el('resOut');
    await this.busy('resBtn', 'researching…', async () => {
      const r = await api.send('/api/research', 'POST', { query: q });
      if (r.configured === false) { out.innerHTML = `<div class="bench-section"><b>Deep research not configured.</b><div class="muted" style="margin-top:6px">${esc(r.hint)}</div></div>`; return; }
      if (r.error) { out.innerHTML = `<p class="warn">${esc(r.error)}</p>`; return; }
      const imgs = (r.images || []).filter(i => i.thumbnail).slice(0, 8);
      out.innerHTML =
        (r.summary ? `<div class="bench-section"><h4>Synthesis (provider: ${esc(r.provider)})</h4><div class="md">${md(r.summary)}</div></div>` : '') +
        (imgs.length ? `<div class="bench-section"><h4>Images</h4><div style="display:flex;gap:8px;flex-wrap:wrap">${imgs.map(i => `<a href="${esc(i.source || i.image)}" target="_blank" title="${esc(i.title)}"><img src="${esc(i.thumbnail)}" style="height:84px;border-radius:8px;border:1px solid var(--border)"></a>`).join('')}</div></div>` : '') +
        `<div class="bench-section"><h4>Sources</h4>${(r.results || []).map((s, i) => `<div class="api-ep"><div><b>[${i + 1}]</b> <a href="${esc(s.url)}" target="_blank">${esc(s.title || s.url)}</a></div><div class="u">${esc(s.snippet || '')}</div>${state.current ? `<button class="ghost" style="margin-top:4px" onclick="ui.saveReference('${esc((s.title || '').replace(/'/g, ''))}','${esc(s.url)}')">Save as reference</button>` : ''}</div>`).join('') || '<p class="muted">No results.</p>'}</div>`;
    });
  },
  async saveReference(title, url) {
    if (!state.current) return;
    await api.send(`/api/vehicles/${state.current.id}/memories`, 'POST', { content: `${title} — ${url}`, kind: 'reference' });
    aiToast.show('Saved reference'); aiToast.hide(1600);
  },
  async busy(id, label, fn) { const b = el(id); const old = b ? b.innerHTML : ''; if (b) { b.disabled = true; b.innerHTML = `<span class="spinner"></span> ${label}`; } aiToast.show(label); try { const r = await fn(); aiToast.done(); return r; } catch (e) { aiToast.done('Error'); alert(e.message); } finally { if (b) { b.disabled = false; b.innerHTML = old; } } },
  async extract(all) { await this.busy(all ? 'exAllBtn' : 'exBtn', all ? `scanning ${state.pageTotal}…` : 'reading…', async () => { const r = await api.send(`/api/vehicles/${state.current.id}/extract`, 'POST', { page: state.page, all_pages: !!all }); state.current.pinouts = r.pinouts; ensureView('pinout'); rerenderView('pinout'); }); },
  async identify() { await this.busy('idBtn', 'identifying…', async () => { const v = await api.send(`/api/vehicles/${state.current.id}/identify`, 'POST', { page: state.page }); Object.assign(state.current, v); this.loadRecords(); rerenderView('record'); }); },
  async canPlan() { await this.busy('planBtn', 'planning…', async () => { const r = await api.send(`/api/vehicles/${state.current.id}/can-plan`, 'POST', { page: state.page }); state.plan = r.plan; rerenderView('plan'); }); },
  async saveVehicle() { const g = id => el(id) ? el(id).value : undefined; await api.send('/api/vehicles/' + state.current.id, 'PATCH', { label: g('f_label'), vin: g('f_vin'), year: g('f_year'), make: g('f_make'), model: g('f_model') }); state.current = await api.get('/api/vehicles/' + state.current.id); this.loadRecords(); rerenderView('record'); },
  async deleteVehicle() { if (!confirm('Delete this project?')) return; await api.send('/api/vehicles/' + state.current.id, 'DELETE'); state.current = null; await this.loadRecords(); renderDock(); },
  async addTag() { const i = el('tagIn'); if (!i || !i.value.trim()) return; state.current.tags = await api.send(`/api/vehicles/${state.current.id}/tags`, 'POST', { tag: i.value.trim() }); this.loadRecords(); rerenderView('record'); },
  async removeTag(t) { state.current.tags = await api.send(`/api/vehicles/${state.current.id}/tags/${encodeURIComponent(t)}`, 'DELETE'); this.loadRecords(); rerenderView('record'); },
  async extractTags() { await this.busy('tagAiBtn', 'tagging…', async () => { const r = await api.send(`/api/vehicles/${state.current.id}/extract-tags`, 'POST', { page: state.page }); state.current.tags = r.tags; this.loadRecords(); rerenderView('record'); }); },
  async addMemory() { const i = el('memIn'); if (!i || !i.value.trim()) return; await api.send(`/api/vehicles/${state.current.id}/memories`, 'POST', { content: i.value.trim() }); await this.refreshMemories(); },
  async delMemory(id) { await api.send('/api/memories/' + id, 'DELETE'); await this.refreshMemories(); },
  async refreshMemories() { state.current.memories = await api.get(`/api/vehicles/${state.current.id}/memories`); rerenderView('memories'); },

  // ---------- chat streaming ----------
  ask(q) { ensureView('chat'); const i = el('chatIn'); if (i) i.value = q; this.send(q); },
  async send(forced) { const input = el('chatIn'); const q = (forced || (input ? input.value : '')).trim(); if (!q || !state.current) return; if (input) input.value = '';
    const auto = el('autoMem') ? el('autoMem').checked : true; if (!el('msgs')) ensureView('chat'); const msgs = el('msgs');
    msgs.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(q)}</div></div>`);
    const aId = 'a' + Date.now(); msgs.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="${aId}"><div class="thinking"><span class="spinner"></span> thinking…</div><div class="md cursor-blink" id="${aId}-md"></div></div>`); msgs.scrollTop = msgs.scrollHeight;
    state.current.messages = [...(state.current.messages || []), { role: 'user', content: q }]; let full = '';
    aiToast.show('Thinking…', true);
    try { await this.stream(`/api/vehicles/${state.current.id}/chat/stream`, { message: q, save_memories: auto, page: state.page },
      tok => { full += tok; aiToast.append(tok); const t = el(aId)?.querySelector('.thinking'); if (t) t.remove(); const m = el(aId + '-md'); if (m) { m.innerHTML = md(full); const b = el('msgs'); if (b) b.scrollTop = b.scrollHeight; } },
      done => { aiToast.done('Answered'); const m = el(aId + '-md'); if (m) m.classList.remove('cursor-blink'); state.current.messages.push({ role: 'assistant', content: full }); if (done.saved_memories && done.saved_memories.length) { aiToast.show(`Saved ${done.saved_memories.length} memory(ies)`); aiToast.hide(2200); this.refreshMemories(); } },
      e => { aiToast.done('Error'); const x = el(aId); if (x) x.innerHTML = `<span class="warn">${esc(e)}</span>`; }); }
    catch (e) { aiToast.done('Error'); const x = el(aId); if (x) x.innerHTML = `<span class="warn">${esc(e.message)}</span>`; } },
  async stream(url, body, onTok, onDone, onErr) {
    const ctrl = new AbortController(); state.streamCtrl = ctrl; let finished = false;
    try {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: ctrl.signal });
      if (!r.ok) { onErr((await r.json().catch(() => ({}))).detail || 'request failed'); return; }
      const reader = r.body.getReader(), dec = new TextDecoder(); let buf = '';
      while (true) { const { value, done } = await reader.read(); if (done) break; buf += dec.decode(value, { stream: true }); const evs = buf.split('\n\n'); buf = evs.pop();
        for (const ev of evs) { const ml = ev.match(/event: (\w+)/), dl = ev.match(/data: (.*)/s); if (!ml || !dl) continue; let data; try { data = JSON.parse(dl[1]); } catch { data = dl[1]; }
          if (ml[1] === 'token') onTok(data); else if (ml[1] === 'done') { finished = true; onDone(data); } else if (ml[1] === 'error') onErr(data); } }
      if (!finished) onDone({});
    } catch (e) { if (e.name === 'AbortError') onDone({ aborted: true }); else onErr(e.message || 'stream error'); }
    finally { state.streamCtrl = null; }
  },
  cancelStream() { if (state.streamCtrl) { state.streamCtrl.abort(); aiToast.done('Stopped'); } },
};
ui.init();
