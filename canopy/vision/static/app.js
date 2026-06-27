// CANOPY Vision — local wiring-diagram copilot (VS Code-style tabbed/split UI).

const ICON = {
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  split: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>',
  diagram: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
  vehicle: '<path d="M5 13l1.5-4.5A2 2 0 018.4 7h7.2a2 2 0 011.9 1.5L19 13M5 13h14v4H5z"/><circle cx="7.5" cy="17" r="1.2"/><circle cx="16.5" cy="17" r="1.2"/>',
  pinout: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
  plan: '<path d="M4 6h16M4 12h16M4 18h10"/><circle cx="20" cy="18" r="1.5"/>',
  chat: '<path d="M4 5h16v11H8l-4 4z"/>',
  memory: '<path d="M9 3a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 006 0V6a3 3 0 00-3-3z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/>',
  moon: '<path d="M21 12.8A8 8 0 1111 3a6 6 0 0010 9.8z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  prev: '<path d="M15 6l-6 6 6 6"/>', next: '<path d="M9 6l6 6-6 6"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5M5 20h14"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
  bolt: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  warn: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
};
const svg = (name, cls = 'icon') => `<svg class="${cls}" viewBox="0 0 24 24">${ICON[name] || ''}</svg>`;

const VIEWS = [
  { key: 'diagram', label: 'Diagram', icon: 'diagram' },
  { key: 'pinout', label: 'Pinout', icon: 'pinout' },
  { key: 'plan', label: 'Wiring Plan', icon: 'plan' },
  { key: 'chat', label: 'Chat', icon: 'chat' },
  { key: 'memories', label: 'Memories', icon: 'memory' },
  { key: 'vehicle', label: 'Record', icon: 'vehicle' },
];
const SLOTS = { left: 'slot-left', rightTop: 'slot-rightTop', rightBottom: 'slot-rightBottom' };

const api = {
  async get(p) { const r = await fetch(p); if (!r.ok) throw await err(r); return r.json(); },
  async send(p, m, b) { const r = await fetch(p, { method: m, headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw await err(r); return r.json(); },
  async upload(p, f) { const fd = new FormData(); fd.append('file', f); const r = await fetch(p, { method: 'POST', body: fd }); if (!r.ok) throw await err(r); return r.json(); },
};
async function err(r) { let d; try { d = (await r.json()).detail; } catch { d = r.statusText; } return new Error(d || ('HTTP ' + r.status)); }
const el = id => document.getElementById(id);
const esc = s => (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const state = {
  records: [], current: null, page: 0, pageTotal: 1, diagramId: null, selectedPin: null,
  plan: '', layout: { left: 'diagram', rightTop: 'pinout', rightBottom: null },
  sidebar: true, leftOn: true, theme: localStorage.getItem('canopy-theme') || 'light',
};

// ---------- markdown ----------
function md(t) {
  let s = esc(t);
  s = s.replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c.trim()}</code></pre>`);
  const lines = s.split('\n'); let out = '', list = null;
  const closeList = () => { if (list) { out += `</${list}>`; list = null; } };
  for (let ln of lines) {
    if (/^\s*[-*]\s+/.test(ln)) { if (list !== 'ul') { closeList(); out += '<ul>'; list = 'ul'; } out += '<li>' + ln.replace(/^\s*[-*]\s+/, '') + '</li>'; continue; }
    if (/^\s*\d+\.\s+/.test(ln)) { if (list !== 'ol') { closeList(); out += '<ol>'; list = 'ol'; } out += '<li>' + ln.replace(/^\s*\d+\.\s+/, '') + '</li>'; continue; }
    closeList();
    if (/^###\s+/.test(ln)) out += '<h3>' + ln.replace(/^###\s+/, '') + '</h3>';
    else if (/^##\s+/.test(ln)) out += '<h2>' + ln.replace(/^##\s+/, '') + '</h2>';
    else if (/^#\s+/.test(ln)) out += '<h1>' + ln.replace(/^#\s+/, '') + '</h1>';
    else if (ln.trim() === '') out += '';
    else out += '<p>' + ln + '</p>';
  }
  closeList();
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>').replace(/`([^`]+)`/g, '<code>$1</code>');
  return wrapPinRefs(out);
}
function wrapPinRefs(html) {
  return html.replace(/\b([Pp]in|[Tt]erminal)\s*#?\s*(\d{1,3})\b/g,
    (m, w, n) => pinIndex()[n] ? `<span class="pinref" data-pin="${n}" onmouseenter="ui.pinTip(event,'${n}')" onmouseleave="ui.hideTip()" onclick="ui.gotoPinPage('${n}')">${m}</span>` : m);
}
function pinIndex() {
  const idx = {};
  for (const p of (state.current?.pinouts || [])) if (p.pin && !(p.pin in idx)) idx[p.pin] = p;
  return idx;
}
function sigClass(s) {
  s = (s || '').toLowerCase();
  if (/can[\s-]?(h|hi|high|l|lo|low|\+|-)|^can\b/.test(s)) return 'can';
  if (/pwr|power|vpwr|kappwr|b\+|\+12|batt|kl30|kl15|ign|vbpwr/.test(s)) return 'pwr';
  if (/gnd|ground|pwrgnd|sigrtn|return/.test(s)) return 'gnd';
  return '';
}

const ui = {
  async init() {
    document.documentElement.dataset.theme = state.theme;
    el('sidebarToggle').innerHTML = svg('menu');
    el('splitToggle').innerHTML = svg('split');
    el('diagToggle').innerHTML = svg('diagram');
    el('themeToggle').innerHTML = svg(state.theme === 'dark' ? 'sun' : 'moon');
    el('newRecBtn').innerHTML = svg('plus');
    el('fileInput').onchange = e => e.target.files[0] && this.uploadFile(e.target.files[0]);
    this.checkHealth();
    await this.loadRecords();
    if (state.records.length) await this.select(state.records[0].id);
    else this.renderAllSlots();
  },

  async checkHealth() {
    try { const h = await api.get('/api/health');
      el('statusDot').className = 'dot ' + (h.model_ready ? 'ok' : 'bad');
      el('statusText').textContent = h.model_ready ? h.model : (h.models.length ? h.model + ' (not pulled)' : 'Ollama offline');
    } catch { el('statusDot').className = 'dot bad'; el('statusText').textContent = 'Ollama offline'; }
  },

  // ---------- records ----------
  async loadRecords() {
    state.records = await api.get('/api/vehicles');
    el('recordList').innerHTML = state.records.map(v => `
      <div class="rec-item ${state.current && state.current.id === v.id ? 'active' : ''}" onclick="ui.select(${v.id})">
        <div class="name">${esc(v.label || [v.year, v.make, v.model].filter(Boolean).join(' ') || 'Untitled record')}</div>
        <div class="meta">${svg('vehicle')} ${esc(v.vin || 'no VIN')}</div>
      </div>`).join('') || '<p class="muted" style="padding:8px">No records yet. Create one with +.</p>';
  },
  async newRecord() {
    const v = await api.send('/api/vehicles', 'POST', { label: 'New record' });
    await this.loadRecords(); this.select(v.id);
  },
  async select(id) {
    state.current = await api.get('/api/vehicles/' + id);
    state.page = 0; state.selectedPin = null; state.plan = '';
    await this.loadRecords(); this.renderAllSlots();
  },

  // ---------- layout ----------
  toggleSidebar() { state.sidebar = !state.sidebar; el('sidebar').classList.toggle('collapsed', !state.sidebar); },
  toggleSplit() {
    state.layout.rightBottom = state.layout.rightBottom ? null : (state.layout.rightTop === 'chat' ? 'pinout' : 'chat');
    el('slot-rightBottom').classList.toggle('hidden', !state.layout.rightBottom);
    el('splitToggle').classList.toggle('active', !!state.layout.rightBottom);
    this.renderAllSlots();
  },
  toggleDiagram() { state.leftOn = !state.leftOn; el('slot-left').classList.toggle('collapsed', !state.leftOn); el('diagToggle').classList.toggle('active', state.leftOn); },
  toggleTheme() { state.theme = state.theme === 'dark' ? 'light' : 'dark'; document.documentElement.dataset.theme = state.theme; localStorage.setItem('canopy-theme', state.theme); el('themeToggle').innerHTML = svg(state.theme === 'dark' ? 'sun' : 'moon'); },

  setSlotView(slotKey, view) {
    for (const k of Object.keys(SLOTS)) if (k !== slotKey && state.layout[k] === view) state.layout[k] = (slotKey === 'left' ? 'diagram' : VIEWS.find(v => v.key !== view).key);
    state.layout[slotKey] = view; this.renderAllSlots();
  },

  renderAllSlots() { el('diagToggle').classList.toggle('active', state.leftOn); el('splitToggle').classList.toggle('active', !!state.layout.rightBottom); for (const k of Object.keys(SLOTS)) this.renderSlot(k); },
  renderSlot(slotKey) {
    const view = state.layout[slotKey]; const host = el(SLOTS[slotKey]); if (!view) { host.innerHTML = ''; return; }
    const tabs = VIEWS.map(v => `<div class="tab ${v.key === view ? 'active' : ''}" onclick="ui.setSlotView('${slotKey}','${v.key}')">${svg(v.icon)} ${v.label}</div>`).join('');
    host.innerHTML = `<div class="tabstrip">${tabs}</div><div class="panel-content" id="content-${slotKey}"></div>`;
    const c = el('content-' + slotKey);
    if (!state.current) { c.innerHTML = '<div class="empty">Select or create a record on the left to begin.</div>'; return; }
    ({ diagram: this.viewDiagram, pinout: this.viewPinout, plan: this.viewPlan, chat: this.viewChat, memories: this.viewMemories, vehicle: this.viewVehicle })[view].call(this, c);
  },

  // ---------- views ----------
  viewDiagram(c) {
    const d = (state.current.diagrams || [])[0];
    state.diagramId = d ? d.id : null; state.pageTotal = d ? (d.pages || 1) : 1;
    if (!d) {
      c.innerHTML = `<div id="dz" class="dropzone">${svg('upload')}<div style="margin-top:8px"><strong>Drop</strong> a wiring diagram (image or PDF), or click to choose.</div></div>`;
    } else {
      const nav = state.pageTotal > 1 ? `<div class="pagenav"><button class="iconbtn" onclick="ui.pageStep(-1)">${svg('prev')}</button>
        Page <input type="number" min="1" max="${state.pageTotal}" value="${state.page + 1}" onchange="ui.gotoPage(this.value-1)"> / ${state.pageTotal}
        <button class="iconbtn" onclick="ui.pageStep(1)">${svg('next')}</button></div>` : '';
      c.innerHTML = `
        <div class="row" style="margin-bottom:10px">
          <button class="primary" onclick="ui.extract(false)" id="exBtn">${svg('bolt')} Extract this page</button>
          <button onclick="ui.extract(true)" id="exAllBtn">Extract all pages</button>
          <button onclick="ui.identify()" id="idBtn">Identify vehicle</button>
          <button class="ghost" onclick="el('fileInput').click()">${svg('upload')} Replace</button>
        </div>
        ${nav}
        <div class="diagram-wrap"><img src="/api/diagram/${d.id}/image?page=${state.page}&t=${Date.now()}" alt="diagram page ${state.page + 1}"></div>`;
    }
    const dz = el('dz'); if (dz) { dz.onclick = () => el('fileInput').click();
      ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.toggle('drag', ev === 'dragover'); if (ev === 'drop' && e.dataTransfer.files[0]) this.uploadFile(e.dataTransfer.files[0]); })); }
  },

  viewPinout(c) {
    const pins = state.current.pinouts || [];
    let detail = '';
    if (state.selectedPin != null && pins[state.selectedPin]) {
      const p = pins[state.selectedPin]; const r = (l, v) => v ? `<div>${l}</div><div><b>${esc(v)}</b></div>` : '';
      detail = `<div class="pin-detail"><div class="pd-top"><span class="pd-pin">Pin ${esc(p.pin)}</span><span class="pd-sig">${esc(p.signal || '')}</span><span class="pd-close" onclick="ui.selectPin(null)">${svg('close')}</span></div>
        <div class="pd-func">${esc(p.function || 'No plain-language function recorded.')}</div>
        <div class="pd-grid">${r('Connector', p.connector)}${r('Circuit', p.circuit)}${r('Wire color', p.wire_color)}${r('Connects to', p.connects_to)}${r('Page', p.page != null ? p.page + 1 : '')}</div></div>`;
    }
    if (!pins.length) { c.innerHTML = detail + '<p class="muted">No pinout yet. Open the Diagram tab, go to a connector page, and click “Extract this page”.</p>'; return; }
    const conns = [...new Set(pins.map(p => p.connector || ''))];
    let body = '';
    for (const conn of conns) {
      const g = pins.filter(p => (p.connector || '') === conn);
      body += `<div class="conn-group">${esc(conn || 'Connector')} · ${g.length} pins</div><table><tbody>${
        g.map(p => { const i = pins.indexOf(p); const sc = sigClass(p.signal);
          const badge = sc ? `<span class="badge ${sc}">${sc.toUpperCase()}</span> ` : '';
          return `<tr class="pin-row ${i === state.selectedPin ? 'sel' : ''}" onclick="ui.selectPin(${i})"><td style="width:48px"><b>${esc(p.pin)}</b></td><td>${badge}${esc(p.signal)}</td><td class="muted">${esc(p.function || '')}</td></tr>`;
        }).join('')}</tbody></table>`;
    }
    c.innerHTML = detail + `<div class="filter-box"><input placeholder="Filter pins…" oninput="ui.filterPins(this.value)"></div><div id="pinBody">${body}</div>`;
  },
  filterPins(q) {
    q = (q || '').toLowerCase();
    document.querySelectorAll('#pinBody tr.pin-row').forEach(tr => { tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none'; });
  },

  viewPlan(c) {
    c.innerHTML = `<div class="row" style="margin-bottom:10px"><button class="primary" onclick="ui.canPlan()" id="planBtn">${svg('bolt')} Generate CAN wiring plan</button></div>
      ${state.plan ? `<div class="md">${md(state.plan)}</div><p class="warn">${svg('warn')} Verify power &amp; ground pins by hand and set the PSU current limit before energizing.</p>` : '<p class="muted">Generate a step-by-step bench connection plan from the extracted pinout. Pin numbers in the plan are hoverable.</p>'}`;
  },

  viewChat(c) {
    const msgs = state.current.messages || [];
    c.innerHTML = `<div class="chat">
      <div class="chips">
        <span class="chip" onclick="ui.ask('How do I wire this module to communicate over CAN?')">How to wire for CAN?</span>
        <span class="chip" onclick="ui.ask('How can I simulate a test on the A/C clutch relay in this vehicle?')">Simulate A/C clutch relay</span>
        <span class="chip" onclick="ui.ask('Which pins are power, ground, CAN-H and CAN-L?')">Power / GND / CAN pins</span>
      </div>
      <div class="messages" id="msgs">${msgs.map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('')}</div>
      <div class="chat-input"><textarea id="chatIn" placeholder="Ask about this wiring diagram…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();ui.send();}"></textarea><button class="primary" onclick="ui.send()">Send</button></div>
      <label class="toggle"><input type="checkbox" id="autoMem" checked> Auto-save new, salient facts to memory</label></div>`;
    const m = el('msgs'); if (m) m.scrollTop = m.scrollHeight;
  },

  viewMemories(c) {
    const mems = state.current.memories || [];
    c.innerHTML = `<div class="chat-input" style="margin-bottom:12px"><input id="memIn" placeholder="Add a fact to remember…"><button onclick="ui.addMemory()">Save</button></div>
      ${mems.map(m => `<div class="memory"><span class="kind ${m.kind === 'auto' ? 'auto' : ''}">${esc(m.kind)}</span><div style="flex:1">${esc(m.content)}</div><button class="iconbtn danger" onclick="ui.delMemory(${m.id})">${svg('close')}</button></div>`).join('') || '<p class="muted">No memories yet. They are saved manually or auto-distilled from chat.</p>'}`;
  },

  viewVehicle(c) {
    const v = state.current;
    c.innerHTML = `<h3 class="sec">Record details</h3>
      <div class="row"><label class="field" style="flex:1"><span>Label</span><input id="f_label" value="${esc(v.label || '')}" placeholder="e.g. 2016 F-250 PCM"></label></div>
      <div class="row"><label class="field" style="flex:2"><span>VIN</span><input id="f_vin" value="${esc(v.vin || '')}"></label>
        <label class="field"><span>Year</span><input id="f_year" value="${esc(v.year || '')}"></label></div>
      <div class="row"><label class="field" style="flex:1"><span>Make</span><input id="f_make" value="${esc(v.make || '')}"></label>
        <label class="field" style="flex:1"><span>Model</span><input id="f_model" value="${esc(v.model || '')}"></label></div>
      <div class="row"><button class="primary" onclick="ui.saveVehicle()">Save</button><button onclick="ui.identify()">Identify from diagram</button><button class="ghost danger" onclick="ui.deleteVehicle()">Delete record</button></div>`;
  },

  // ---------- diagram actions ----------
  pageStep(d) { this.gotoPage(state.page + d); },
  gotoPage(n) { state.page = Math.max(0, Math.min(state.pageTotal - 1, parseInt(n) || 0)); this.renderSlotsWith('diagram'); },
  renderSlotsWith(view) { for (const k of Object.keys(SLOTS)) if (state.layout[k] === view) this.renderSlot(k); },
  ensureView(view) { if (!Object.values(state.layout).includes(view)) { if (view === 'diagram' && state.leftOn === false) { state.leftOn = true; el('slot-left').classList.remove('collapsed'); } state.layout[view === 'diagram' ? 'left' : 'rightTop'] = view; this.renderAllSlots(); } },

  async uploadFile(file) {
    if (!state.current) return;
    try { await api.upload(`/api/vehicles/${state.current.id}/diagram`, file); await this.select(state.current.id); }
    catch (e) { alert('Upload failed: ' + e.message); }
  },
  async busy(id, label, fn) { const b = el(id); const old = b ? b.innerHTML : ''; if (b) { b.disabled = true; b.innerHTML = `<span class="spinner"></span> ${label}`; } try { return await fn(); } catch (e) { alert(e.message); } finally { if (b) { b.disabled = false; b.innerHTML = old; } } },

  async extract(all) {
    await this.busy(all ? 'exAllBtn' : 'exBtn', all ? `scanning ${state.pageTotal} pages…` : 'reading…', async () => {
      const r = await api.send(`/api/vehicles/${state.current.id}/extract`, 'POST', { page: state.page, all_pages: !!all });
      state.current.pinouts = r.pinouts; this.ensureView('pinout'); this.renderSlotsWith('pinout');
    });
  },
  async identify() {
    await this.busy('idBtn', 'identifying…', async () => {
      const v = await api.send(`/api/vehicles/${state.current.id}/identify`, 'POST', { page: state.page });
      Object.assign(state.current, v); this.loadRecords(); this.renderSlotsWith('vehicle');
    });
  },
  async canPlan() {
    await this.busy('planBtn', 'planning…', async () => {
      const r = await api.send(`/api/vehicles/${state.current.id}/can-plan`, 'POST', { page: state.page });
      state.plan = r.plan; this.renderSlotsWith('plan');
    });
  },

  // ---------- pinout actions ----------
  selectPin(idx) {
    state.selectedPin = idx;
    if (idx != null) { const p = state.current.pinouts[idx]; if (p && p.page != null) { state.page = p.page; this.ensureView('diagram'); this.renderSlotsWith('diagram'); } }
    this.renderSlotsWith('pinout');
  },
  gotoPinPage(n) { const p = pinIndex()[n]; if (p && p.page != null) { state.page = p.page; this.ensureView('diagram'); this.renderSlotsWith('diagram'); } this.hideTip(); },

  // ---------- tooltip ----------
  pinTip(ev, n) {
    const p = pinIndex()[n]; if (!p) return; const t = el('tooltip');
    t.innerHTML = `<div><span class="tt-pin">Pin ${esc(p.pin)}</span> <span class="tt-sig">${esc(p.signal || '')}</span></div>
      <div class="tt-row">${esc(p.function || '')}</div>${p.connector ? `<div class="tt-row">${esc(p.connector)}${p.page != null ? ' · page ' + (p.page + 1) : ''}</div>` : ''}<div class="tt-row">click to open that page</div>`;
    t.style.display = 'block'; const x = Math.min(ev.clientX + 14, window.innerWidth - 300); t.style.left = x + 'px'; t.style.top = (ev.clientY + 16) + 'px';
  },
  hideTip() { el('tooltip').style.display = 'none'; },

  // ---------- vehicle/memories ----------
  async saveVehicle() {
    const g = id => el(id) ? el(id).value : undefined;
    state.current = await api.send('/api/vehicles/' + state.current.id, 'PATCH', { label: g('f_label'), vin: g('f_vin'), year: g('f_year'), make: g('f_make'), model: g('f_model') });
    state.current = await api.get('/api/vehicles/' + state.current.id); this.loadRecords(); this.renderAllSlots();
  },
  async deleteVehicle() {
    if (!confirm('Delete this record and its diagrams/memories?')) return;
    await api.send('/api/vehicles/' + state.current.id, 'DELETE'); state.current = null; await this.loadRecords(); this.renderAllSlots();
  },
  async addMemory() { const i = el('memIn'); if (!i || !i.value.trim()) return; await api.send(`/api/vehicles/${state.current.id}/memories`, 'POST', { content: i.value.trim() }); await this.refreshMemories(); },
  async delMemory(id) { await api.send('/api/memories/' + id, 'DELETE'); await this.refreshMemories(); },
  async refreshMemories() { state.current.memories = await api.get(`/api/vehicles/${state.current.id}/memories`); this.renderSlotsWith('memories'); },

  // ---------- chat (streaming) ----------
  ask(q) { this.ensureView('chat'); const i = el('chatIn'); if (i) i.value = q; this.send(q); },
  async send(forced) {
    const input = el('chatIn'); const q = (forced || (input ? input.value : '')).trim();
    if (!q || !state.current) return; if (input) input.value = '';
    const auto = el('autoMem') ? el('autoMem').checked : true;
    const box = el('msgs'); if (!box) { this.ensureView('chat'); }
    const msgs = el('msgs');
    msgs.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(q)}</div></div>`);
    const aId = 'a' + Date.now();
    msgs.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="${aId}"><div class="thinking"><span class="spinner"></span> thinking…</div><div class="md cursor-blink" id="${aId}-md"></div></div>`);
    msgs.scrollTop = msgs.scrollHeight;
    state.current.messages = [...(state.current.messages || []), { role: 'user', content: q }];
    let full = '';
    try {
      await this.stream(`/api/vehicles/${state.current.id}/chat/stream`, { message: q, save_memories: auto, page: state.page },
        tok => { full += tok; const t = el(aId)?.querySelector('.thinking'); if (t) t.remove(); const m = el(aId + '-md'); if (m) { m.innerHTML = md(full); msgs.scrollTop = msgs.scrollHeight; } },
        done => { const m = el(aId + '-md'); if (m) m.classList.remove('cursor-blink'); state.current.messages.push({ role: 'assistant', content: full }); if (done.saved_memories && done.saved_memories.length) this.refreshMemories(); },
        e => { const el2 = el(aId); if (el2) el2.innerHTML = `<span class="warn">${esc(e)}</span>`; });
    } catch (e) { const el2 = el(aId); if (el2) el2.innerHTML = `<span class="warn">${esc(e.message)}</span>`; }
  },
  async stream(url, body, onTok, onDone, onErr) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { onErr((await r.json().catch(() => ({}))).detail || 'request failed'); return; }
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = '';
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      const events = buf.split('\n\n'); buf = events.pop();
      for (const ev of events) {
        const ml = ev.match(/event: (\w+)/); const dl = ev.match(/data: (.*)/s); if (!ml || !dl) continue;
        const type = ml[1]; let data; try { data = JSON.parse(dl[1]); } catch { data = dl[1]; }
        if (type === 'token') onTok(data); else if (type === 'done') onDone(data); else if (type === 'error') onErr(data);
      }
    }
  },
};
ui.init();
