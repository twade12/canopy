// CANOPY Vision — local wiring-diagram copilot front-end (vanilla JS).
const api = {
  async get(path) { const r = await fetch(path); if (!r.ok) throw await err(r); return r.json(); },
  async send(path, method, body) {
    const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) throw await err(r); return r.json();
  },
  async upload(path, file) {
    const fd = new FormData(); fd.append('file', file);
    const r = await fetch(path, { method: 'POST', body: fd });
    if (!r.ok) throw await err(r); return r.json();
  },
};
async function err(r) { let d; try { d = (await r.json()).detail; } catch { d = r.statusText; } return new Error(d || ('HTTP ' + r.status)); }

const state = { vehicles: [], current: null, page: 0, pageTotal: 1 };

// minimal, safe markdown -> html
function md(t) {
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const lines = esc(t).split('\n'); let html = '', inList = false;
  for (let line of lines) {
    if (/^\s*[-*]\s+/.test(line)) { if (!inList) { html += '<ul>'; inList = true; } html += '<li>' + line.replace(/^\s*[-*]\s+/, '') + '</li>'; continue; }
    if (inList) { html += '</ul>'; inList = false; }
    if (/^###\s+/.test(line)) html += '<h3>' + line.replace(/^###\s+/, '') + '</h3>';
    else if (/^##\s+/.test(line)) html += '<h2>' + line.replace(/^##\s+/, '') + '</h2>';
    else if (/^#\s+/.test(line)) html += '<h1>' + line.replace(/^#\s+/, '') + '</h1>';
    else if (line.trim() === '') html += '<br>';
    else html += '<p style="margin:4px 0">' + line + '</p>';
  }
  if (inList) html += '</ul>';
  return html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
}

const el = id => document.getElementById(id);

const ui = {
  async init() {
    this.checkHealth();
    await this.loadVehicles();
    this.setupDropzone();
  },

  async checkHealth() {
    try {
      const h = await api.get('/api/health');
      el('statusDot').className = 'dot ' + (h.model_ready ? 'ok' : 'bad');
      el('statusText').textContent = h.model_ready ? h.model : (h.models.length ? `${h.model} not pulled` : 'Ollama offline');
    } catch { el('statusDot').className = 'dot bad'; el('statusText').textContent = 'Ollama offline'; }
  },

  async loadVehicles() {
    state.vehicles = await api.get('/api/vehicles');
    const list = el('vehicleList');
    list.innerHTML = state.vehicles.map(v => `
      <div class="vehicle-item ${state.current && state.current.id === v.id ? 'active' : ''}" onclick="ui.select(${v.id})">
        <div class="name">${esc(v.label || [v.year, v.make, v.model].filter(Boolean).join(' ') || 'Unnamed vehicle')}</div>
        <div class="meta">${esc(v.vin || 'no VIN')}</div>
      </div>`).join('') || '<p class="muted">No vehicles yet.</p>';
  },

  async newVehicle() {
    const v = await api.send('/api/vehicles', 'POST', { label: 'New vehicle' });
    await this.loadVehicles(); this.select(v.id);
  },

  async select(id) {
    state.current = await api.get('/api/vehicles/' + id);
    state.page = 0;
    el('emptyState').classList.add('hidden');
    el('workspace').classList.remove('hidden');
    el('planCard').classList.add('hidden');
    el('pinDetail').classList.add('hidden');
    this.render();
    await this.loadVehicles();
  },

  render() {
    const v = state.current;
    el('vehTitle').textContent = v.label || [v.year, v.make, v.model].filter(Boolean).join(' ') || 'Vehicle';
    el('vin').value = v.vin || ''; el('year').value = v.year || ''; el('make').value = v.make || ''; el('model').value = v.model || '';
    this.renderDiagram(); this.renderPinouts(v.pinouts); this.renderMemories(v.memories); this.renderMessages(v.messages);
  },

  renderDiagram() {
    const d = (state.current.diagrams || [])[0];
    const ok = !!d;
    el('extractBtn').disabled = !ok; el('extractAllBtn').disabled = !ok; el('canPlanBtn').disabled = !ok;
    state.pageTotal = ok ? (d.pages || 1) : 1;
    state.diagramId = ok ? d.id : null;
    const nav = el('pageNav');
    if (ok && state.pageTotal > 1) {
      nav.classList.remove('hidden');
      el('pageTotal').textContent = state.pageTotal;
      el('pageNum').max = state.pageTotal;
      el('pageNum').value = state.page + 1;
    } else { nav.classList.add('hidden'); }
    el('diagramPreview').innerHTML = ok
      ? `<img src="/api/diagram/${d.id}/image?page=${state.page}&t=${Date.now()}" alt="diagram page ${state.page + 1}">`
      : '';
  },

  pageStep(delta) { this.gotoPage(state.page + delta); },
  gotoPage(n) {
    n = Math.max(0, Math.min(state.pageTotal - 1, parseInt(n) || 0));
    state.page = n; this.renderDiagram();
  },

  sigClass(s) {
    s = (s || '').toLowerCase();
    if (/can[\s-]?(h|hi|high|l|lo|low|\+|-)|^can/.test(s)) return 'can';
    if (/pwr|power|vpwr|kappwr|b\+|\+12|batt|kl30|kl15|ign/.test(s)) return 'pwr';
    if (/gnd|ground|pwrgnd|sigrtn|return/.test(s)) return 'gnd';
    return '';
  },

  renderPinouts(pins) {
    state.current.pinouts = pins || [];
    const conns = [...new Set((pins || []).map(p => p.connector || ''))];
    el('connectorName').textContent = conns.filter(Boolean).length ? '· ' + conns.filter(Boolean).join(', ') : '';
    if (!pins || !pins.length) { el('pinoutTable').innerHTML = '<p class="muted">No pinout yet. Navigate to a connector page and click “Extract this page”.</p>'; return; }
    let html = '';
    for (const conn of conns) {
      const group = pins.filter(p => (p.connector || '') === conn);
      if (conns.length > 1 || conn) html += `<div class="conn-group">${esc(conn || 'Connector')}</div>`;
      html += `<table><thead><tr><th>Pin</th><th>Signal</th><th>Function</th><th>Color</th></tr></thead><tbody>${
        group.map((p, i) => {
          const sc = this.sigClass(p.signal);
          const idx = pins.indexOf(p);
          return `<tr class="pin-row" data-i="${idx}" onclick="ui.showPin(${idx})">
            <td class="pin-num ${sc}">${esc(p.pin)}</td>
            <td class="${sc === 'can' ? 'signal-can' : sc === 'pwr' ? 'signal-pwr' : sc === 'gnd' ? 'signal-gnd' : ''}">${esc(p.signal)}</td>
            <td class="muted">${esc(p.function || '')}</td>
            <td>${esc(p.wire_color || '')}</td></tr>`;
        }).join('')
      }</tbody></table>`;
    }
    el('pinoutTable').innerHTML = html;
  },

  showPin(idx) {
    const p = state.current.pinouts[idx]; if (!p) return;
    document.querySelectorAll('.pin-row').forEach(r => r.classList.toggle('sel', r.dataset.i == idx));
    const row = (label, val) => val ? `<div>${label}</div><div><b>${esc(val)}</b></div>` : '';
    el('pinDetail').innerHTML = `
      <span class="pd-close" onclick="el('pinDetail').classList.add('hidden')">✕</span>
      <div class="pd-pin">Pin ${esc(p.pin)}</div>
      <div class="pd-sig">${esc(p.signal || '(no label)')}</div>
      <div class="pd-func">${esc(p.function || 'No plain-language function recorded.')}</div>
      <div class="pd-grid">
        ${row('Connector', p.connector)}
        ${row('Circuit', p.circuit)}
        ${row('Wire color', p.wire_color)}
        ${row('Connects to', p.connects_to)}
        ${row('Diagram page', p.page != null ? (p.page + 1) : '')}
        ${row('Notes', p.notes)}
      </div>`;
    el('pinDetail').classList.remove('hidden');
  },

  renderMemories(mems) {
    el('memList').innerHTML = (mems || []).map(m => `
      <div class="memory"><span class="kind">${esc(m.kind)}</span><div style="flex:1">${esc(m.content)}</div>
      <button class="ghost danger" onclick="ui.delMemory(${m.id})">✕</button></div>`).join('') || '<p class="muted">No memories saved.</p>';
  },

  renderMessages(msgs) {
    const box = el('messages');
    box.innerHTML = (msgs || []).map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('');
    box.scrollTop = box.scrollHeight;
  },

  async saveVehicle() {
    state.current = await api.send('/api/vehicles/' + state.current.id, 'PATCH', {
      vin: el('vin').value, year: el('year').value, make: el('make').value, model: el('model').value,
    });
    await this.select(state.current.id);
  },

  async deleteVehicle() {
    if (!confirm('Delete this vehicle and its diagrams/memories?')) return;
    await api.send('/api/vehicles/' + state.current.id, 'DELETE');
    state.current = null; el('workspace').classList.add('hidden'); el('emptyState').classList.remove('hidden');
    await this.loadVehicles();
  },

  setupDropzone() {
    const dz = el('dropzone'), fi = el('fileInput');
    dz.onclick = () => fi.click();
    fi.onchange = () => fi.files[0] && this.uploadFile(fi.files[0]);
    ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => {
      e.preventDefault(); dz.classList.toggle('drag', ev === 'dragover');
      if (ev === 'drop' && e.dataTransfer.files[0]) this.uploadFile(e.dataTransfer.files[0]);
    }));
  },

  async uploadFile(file) {
    if (!state.current) return;
    el('dropzone').innerHTML = '<span class="spinner"></span> uploading…';
    try {
      await api.upload(`/api/vehicles/${state.current.id}/diagram`, file);
      await this.select(state.current.id);
    } catch (e) { alert('Upload failed: ' + e.message); }
    el('dropzone').innerHTML = '<strong>Drop</strong> an image or PDF here, or click to choose.<br><span class="muted">PNG · JPG · PDF</span>';
  },

  async withBusy(btn, label, fn) {
    const old = btn.innerHTML; btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> ${label}`;
    try { return await fn(); } catch (e) { alert(e.message); } finally { btn.disabled = false; btn.innerHTML = old; }
  },

  async extract(allPages) {
    const btn = allPages ? el('extractAllBtn') : el('extractBtn');
    await this.withBusy(btn, allPages ? `scanning ${state.pageTotal} pages…` : 'reading page…', async () => {
      const r = await api.send(`/api/vehicles/${state.current.id}/extract`, 'POST', { page: state.page, all_pages: !!allPages });
      this.renderPinouts(r.pinouts);
    });
  },

  async identify() {
    await this.withBusy(el('identifyBtn'), 'identifying…', async () => {
      const v = await api.send(`/api/vehicles/${state.current.id}/identify`, 'POST', { page: state.page });
      Object.assign(state.current, v);
      el('vin').value = v.vin || ''; el('year').value = v.year || ''; el('make').value = v.make || ''; el('model').value = v.model || '';
      el('vehTitle').textContent = v.label || [v.year, v.make, v.model].filter(Boolean).join(' ') || 'Vehicle';
      this.loadVehicles();
    });
  },

  async canPlan() {
    await this.withBusy(el('canPlanBtn'), 'planning…', async () => {
      const r = await api.send(`/api/vehicles/${state.current.id}/can-plan`, 'POST', { page: state.page });
      el('planCard').classList.remove('hidden');
      el('planOutput').innerHTML = md(r.plan);
    });
  },

  ask(q) { el('chatInput').value = q; this.send(); },

  async send() {
    const input = el('chatInput'); const q = input.value.trim();
    if (!q || !state.current) return;
    input.value = '';
    const box = el('messages');
    box.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(q)}</div></div>`);
    box.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="pending"><span class="spinner"></span> thinking…</div>`);
    box.scrollTop = box.scrollHeight;
    try {
      const r = await api.send(`/api/vehicles/${state.current.id}/chat`, 'POST', { message: q, save_memories: el('saveMem').checked, page: state.page });
      el('pending').remove();
      box.insertAdjacentHTML('beforeend', `<div class="msg assistant"><div class="md">${md(r.reply)}</div></div>`);
      box.scrollTop = box.scrollHeight;
      if (r.saved_memories && r.saved_memories.length) { state.current = await api.get('/api/vehicles/' + state.current.id); this.renderMemories(state.current.memories); }
    } catch (e) { el('pending').innerHTML = '<span class="warn">' + esc(e.message) + '</span>'; }
  },

  async addMemory() {
    const i = el('memInput'); if (!i.value.trim()) return;
    await api.send(`/api/vehicles/${state.current.id}/memories`, 'POST', { content: i.value.trim() });
    i.value = ''; state.current = await api.get('/api/vehicles/' + state.current.id); this.renderMemories(state.current.memories);
  },

  async delMemory(id) {
    await api.send('/api/memories/' + id, 'DELETE');
    state.current = await api.get('/api/vehicles/' + state.current.id); this.renderMemories(state.current.memories);
  },
};

function esc(s) { return (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
ui.init();
