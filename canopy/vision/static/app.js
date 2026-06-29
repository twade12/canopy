// CANOPY Vision — drag-and-dock workspace + local AI wiring-diagram copilot.

const ICON = {
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>', plus: '<path d="M12 5v14M5 12h14"/>',
  diagram: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>',
  pinout: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
  plan: '<path d="M4 6h16M4 12h16M4 18h10"/><circle cx="20" cy="18" r="1.5"/>',
  chat: '<path d="M4 5h16v11H8l-4 4z"/>', memory: '<path d="M6 3h12a1 1 0 011 1v17l-7-4-7 4V4a1 1 0 011-1z"/>',
  record: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9h6M7 13h10"/>',
  api: '<path d="M8 3H5v18h3M16 3h3v18h-3M9 12h6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19"/>',
  moon: '<path d="M21 12.8A8 8 0 1111 3a6 6 0 0010 9.8z"/>',
  reset: '<path d="M3 12a9 9 0 0115-6.6L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 01-15 6.6L3 16"/><path d="M3 21v-5h5"/>',
  leaf: '<path d="M5 19C5 10 11 4 20 4c0 9-6 15-15 15z"/><path d="M5 19C9 15 13 12 18 10"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>', prev: '<path d="M15 6l-6 6 6 6"/>', next: '<path d="M9 6l6 6-6 6"/>',
  logout: '<path d="M14 7V5a2 2 0 00-2-2H6a2 2 0 00-2 2v14a2 2 0 002 2h6a2 2 0 002-2v-2M10 12h11M18 9l3 3-3 3"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5M5 20h14"/>', search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
  bolt: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>', warn: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
  edit: '<path d="M4 20h4L18 10l-4-4L4 16z"/><path d="M13 5l4 4"/>', trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
  annotations: '<rect x="3" y="4" width="13" height="13" rx="2"/><circle cx="7" cy="8" r="1.4"/><path d="M3.5 14l3.5-3.5 3 3"/><path d="M14 9l5-5 2.2 2.2-5 5-2.7.5z"/>',
  arrow: '<path d="M5 19L19 5M19 5h-7M19 5v7"/>',
  expand: '<path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/>', compress: '<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>',
  book: '<path d="M5 4h11a2 2 0 012 2v14H7a2 2 0 00-2 2z"/><path d="M9 4v14"/>',
  guide: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
  check: '<path d="M5 12l4 4L19 6"/>',
  cab: '<path d="M3 4h18v16H3z"/><path d="M7 4v16M11 4v16M15 4v16M19 4v16"/>',
  gauge: '<path d="M4 19a8 8 0 1116 0"/><path d="M12 19l5-5"/>', scope: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M5 13h2l2-4 2 7 2-5h4"/>', siggen: '<path d="M3 12c3-7 5-7 7 0s4 7 7 0"/>',
  catalog: '<rect x="3" y="4" width="7" height="7" rx="1"/><rect x="14" y="4" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  cockpit: '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="5" rx="1"/><rect x="13" y="10" width="8" height="11" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/>',
  gear: '<circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.6 1.6 0 00.32 1.77l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.6 1.6 0 00-1.77-.32 1.6 1.6 0 00-.97 1.47V21a2 2 0 01-4 0v-.1A1.6 1.6 0 008.9 19.4a1.6 1.6 0 00-1.77.32l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.6 1.6 0 00.32-1.77 1.6 1.6 0 00-1.47-.97H3a2 2 0 010-4h.1A1.6 1.6 0 004.6 8.9a1.6 1.6 0 00-.32-1.77l-.06-.06a2 2 0 112.83-2.83l.06.06a1.6 1.6 0 001.77.32H9a1.6 1.6 0 00.97-1.47V3a2 2 0 014 0v.1a1.6 1.6 0 00.97 1.47 1.6 1.6 0 001.77-.32l.06-.06a2 2 0 112.83 2.83l-.06.06a1.6 1.6 0 00-.32 1.77V9a1.6 1.6 0 001.47.97H21a2 2 0 010 4h-.1a1.6 1.6 0 00-1.47.97z"/>',
  zin: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4M11 8v6M8 11h6"/>', zout: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4M8 11h6"/>', tag: '<path d="M3 7l8-4 8 4v10l-8 4-8-4z"/>',
  assistant: '<path d="M12 3l1.7 4L18 8.7l-4.3 1.6L12 15l-1.7-4.7L6 8.7 10.3 7z"/><circle cx="18" cy="18" r="2.4"/>',
  bench: '<rect x="3" y="8" width="18" height="9" rx="2"/><path d="M7 8V5M17 8V5M8 13h8"/>', link: '<path d="M9 15l6-6M8 8H6a4 4 0 000 8h2M16 16h2a4 4 0 000-8h-2"/>',
  triage: '<path d="M21 4a4 4 0 01-5.6 5.6L7 18l-2-2 8.4-8.4A4 4 0 0119 2l-3 3 1.5 1.5L21 4z"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="1"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/>',
  phone: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
};
const svg = (n, cls = 'icon') => `<svg class="${cls}" viewBox="0 0 24 24">${ICON[n] || ''}</svg>`;
// Sage's animated leaf — shown whenever Sage (the AI) is working.
const leaf = (cls = '') => `<svg class="sage-leaf ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20C4 11 10 4 20 4c0 10-7 16-16 16z" fill="currentColor"/><path d="M18.5 5.5C12 9 7.5 14 5 20" fill="none" stroke="#fff" stroke-width="1.3" opacity=".55" stroke-linecap="round"/></svg>`;
const VIEWS = [
  { key: 'diagram', label: 'Diagram', icon: 'diagram' }, { key: 'pinout', label: 'Pinout', icon: 'pinout' },
  { key: 'plan', label: 'Wiring Plan', icon: 'plan' }, { key: 'chat', label: 'Chat', icon: 'chat' },
  { key: 'guided', label: 'Guided', icon: 'guide' },
  { key: 'triage', label: 'Triage', icon: 'triage' }, { key: 'pcb', label: 'PCB', icon: 'chip' },
  { key: 'annotations', label: 'Annotations', icon: 'annotations' },
  { key: 'memories', label: 'Memories', icon: 'memory' }, { key: 'record', label: 'Record', icon: 'record' },
  { key: 'profile', label: 'Profile', icon: 'cab' }, { key: 'wiki', label: 'Wiki', icon: 'record' },
  { key: 'assistant', label: 'Sage', icon: 'leaf' }, { key: 'bench', label: 'Bench', icon: 'bench' },
  { key: 'research', label: 'Research', icon: 'search' }, { key: 'api', label: 'API', icon: 'api' },
  { key: 'cockpit', label: 'Cockpit', icon: 'cockpit' },
  { key: 'knowledge', label: 'Knowledge', icon: 'book' }, { key: 'products', label: 'Products', icon: 'catalog' },
  { key: 'dmm', label: 'DMM', icon: 'gauge' }, { key: 'scope', label: 'Scope', icon: 'scope' },
  { key: 'siggen', label: 'Signal Gen', icon: 'siggen' },
];
const GLOBAL_VIEWS = new Set(['cockpit', 'api', 'assistant', 'bench', 'research', 'knowledge', 'products', 'dmm', 'scope', 'siggen']);  // usable without a project
const GUIDED_PHASES = [
  { key: 'intake', label: 'Intake' }, { key: 'sealed', label: 'Sealed checks' },
  { key: 'powerup', label: 'Power-up' }, { key: 'inspect', label: 'Open & inspect' },
  { key: 'board', label: 'Board checks' }, { key: 'rootcause', label: 'Root cause' },
  { key: 'document', label: 'Document' },
];
const meta = k => VIEWS.find(v => v.key === k) || { label: k, icon: 'diagram' };

const api = {
  _cache: new Map(),  // url -> { t, data } for cacheable GETs (cget)
  async get(p) { const r = await fetch(p); if (!r.ok) throw await err(r); return r.json(); },
  // cacheable GET: serves a fresh-enough cached copy instantly, else fetches. Writes invalidate.
  async cget(p, ttl = 20000) {
    const hit = this._cache.get(p);
    if (hit && Date.now() - hit.t < ttl) return structuredClone(hit.data);
    const data = await this.get(p);
    this._cache.set(p, { t: Date.now(), data });
    return structuredClone(data);
  },
  _bust(p) { if (p) for (const k of this._cache.keys()) { if (k === p || k.startsWith(p)) this._cache.delete(k); } },
  async send(p, m, b) { const r = await fetch(p, { method: m, headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw await err(r); this._cache.clear(); return r.json(); },
  async upload(p, f) { const fd = new FormData(); fd.append('file', f); const r = await fetch(p, { method: 'POST', body: fd }); if (!r.ok) throw await err(r); this._cache.clear(); return r.json(); },
};
async function err(r) { let d; try { d = (await r.json()).detail; } catch { d = r.statusText; } return new Error(d || ('HTTP ' + r.status)); }
const el = id => document.getElementById(id);
const esc = s => (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const state = { records: [], current: null, page: 0, pageTotal: 1, diagramId: null, selectedPin: null,
  plan: '', zoom: 1, apiRef: null, gid: 1, drag: null,
  theme: localStorage.getItem('canopy-theme') || 'light', sidebar: true, dock: null };

// ---------- markdown ----------
// Local models often emit inline LaTeX ($\mu$F, $\geq$, $>0.5\Omega$); convert the common
// electronics symbols to plain Unicode so they render instead of showing raw markup.
const TEX_MAP = { '\\mu': 'µ', '\\Omega': 'Ω', '\\omega': 'ω', '\\ohm': 'Ω', '\\geq': '≥',
  '\\leq': '≤', '\\neq': '≠', '\\times': '×', '\\cdot': '·', '\\pm': '±', '\\mp': '∓',
  '\\approx': '≈', '\\sim': '~', '\\degree': '°', '\\circ': '°', '\\Delta': 'Δ', '\\delta': 'δ',
  '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\lambda': 'λ', '\\pi': 'π', '\\tau': 'τ',
  '\\infty': '∞', '\\rightarrow': '→', '\\to': '→', '\\leftarrow': '←', '\\,': ' ', '\\;': ' ' };
const SUP = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻' };
const SUB = { '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉' };
function texConv(inner) {
  let x = inner.replace(/\\(?:text|mathrm|mathbf|rm)\{([^}]*)\}/g, '$1');
  for (const k in TEX_MAP) x = x.split(k).join(TEX_MAP[k]);
  x = x.replace(/\^\{?(-?\d+)\}?/g, (_, d) => [...d].map(ch => SUP[ch] || ch).join(''));
  x = x.replace(/_\{?(\d+)\}?/g, (_, d) => [...d].map(ch => SUB[ch] || ch).join(''));
  return x.replace(/\\[a-zA-Z]+/g, '').replace(/[{}]/g, '').trim();
}
function deTex(s) {
  return s.replace(/\$([^$\n]+?)\$/g, (_, i) => texConv(i)).replace(/\\\(([\s\S]*?)\\\)/g, (_, i) => texConv(i));
}
function md(t) {
  let s = esc(t).replace(/```([\s\S]*?)```/g, (_, c) => `<pre><code>${c.trim()}</code></pre>`);
  s = deTex(s);
  const lines = s.split('\n'); let out = '', list = null, tbl = [];
  const close = () => { if (list) { out += `</${list}>`; list = null; } };
  const flushTbl = () => { if (!tbl.length) return;
    const rows = tbl.map(r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
    const sep = rows[1] && rows[1].every(c => /^:?-+:?$/.test(c));
    const head = sep ? rows[0] : null; const body = sep ? rows.slice(2) : rows;
    out += '<table>' + (head ? '<thead><tr>' + head.map(c => `<th>${c}</th>`).join('') + '</tr></thead>' : '') +
      '<tbody>' + body.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
    tbl = []; };
  for (const ln of lines) {
    if (/^\s*\|.*\|\s*$/.test(ln)) { close(); tbl.push(ln); continue; }
    flushTbl();
    if (/^\s*[-*]\s+/.test(ln)) { if (list !== 'ul') { close(); out += '<ul>'; list = 'ul'; } out += '<li>' + ln.replace(/^\s*[-*]\s+/, '') + '</li>'; continue; }
    if (/^\s*\d+\.\s+/.test(ln)) { if (list !== 'ol') { close(); out += '<ol>'; list = 'ol'; } out += '<li>' + ln.replace(/^\s*\d+\.\s+/, '') + '</li>'; continue; }
    close();
    const hm = ln.match(/^\s*(#{1,6})\s+(.*)$/);  // ATX headers h1-h6 (#### was dropped before)
    if (hm) { const lvl = hm[1].length; out += `<h${lvl}>${hm[2].replace(/\s+#+\s*$/, '')}</h${lvl}>`; }
    else if (ln.trim()) out += '<p>' + ln + '</p>';
  }
  flushTbl(); close();
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
  out = out.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, url) =>
    `<img class="md-img" src="${url}" alt="${esc(alt)}" loading="lazy" title="Click to expand" onclick="ui.lightbox('${url}')">`);
  return out.replace(/\b([Pp]in|[Tt]erminal)\s*#?\s*(\d{1,3})\b/g, (m, w, n) => pinIndex()[n]
    ? `<span class="pinref" data-pin="${n}" onmouseenter="ui.pinTip(event,'${n}')" onmouseleave="ui.hideTip()" onclick="ui.gotoPinPage('${n}')">${m}</span>` : m);
}
function pinIndex() { const i = {}; for (const p of (state.current?.pinouts || [])) if (p.pin && !(p.pin in i)) i[p.pin] = p; return i; }
// engineering-format a meter reading
function fmtMeas(v, unit) {
  const a = Math.abs(v);
  if (unit === 'Ω') { if (a >= 1e6) return [(v / 1e6).toFixed(3), 'MΩ']; if (a >= 1e3) return [(v / 1e3).toFixed(3), 'kΩ']; return [v.toFixed(2), 'Ω']; }
  if (unit === 'Hz') { if (a >= 1e3) return [(v / 1e3).toFixed(3), 'kHz']; return [v.toFixed(1), 'Hz']; }
  if (unit === 'mA') return [v.toFixed(3), 'mA'];
  if (unit === 'V') { if (a < 1 && a > 0) return [(v * 1000).toFixed(1), 'mV']; return [v.toFixed(3), 'V']; }
  return [String(v), unit];
}
// Harness ribbon: module connector (left) -> colored wires -> CAB universal header (right).
const ROLE_COLOR = { power: '#ef4444', ignition: '#ef4444', accessory: '#ef4444', ground: '#555',
  can_h: '#0e8aa6', can_l: '#0e8aa6', can_fd_h: '#0e8aa6', can_fd_l: '#0e8aa6',
  lin: '#8b5cf6', kline: '#8b5cf6', sensor_ref: '#0f9d6b', sensor_signal: '#0f9d6b',
  sensor_return: '#0f9d6b', output: '#f59e0b', switch: '#6366f1', unknown: '#9ca3af' };
function harnessSvg(harness, connector) {
  if (!harness.length) return '<div class="muted" style="font-size:12px;padding:10px">No pins mapped yet — extract the pinout first.</div>';
  const rowH = 26, top = 46, W = 820, bx1 = 150, bx2 = W - 150, dotL = bx1 + 9, dotR = bx2 - 9;
  const H = top + harness.length * rowH + 16;
  const rows = harness.map((h, i) => {
    const y = top + i * rowH + rowH / 2;
    const col = ROLE_COLOR[h.role] || ROLE_COLOR.unknown;
    const cardShort = h.card ? h.card.split('-')[1] : '';
    const lbl = `${h.module_pin} ${h.signal || ''}`.trim();
    const rlbl = `${h.header_pin}${cardShort ? ' · ' + cardShort + ' ' + (h.channel || '') : ''}`;
    return `<path d="M ${dotL} ${y} C ${dotL + 70} ${y}, ${dotR - 70} ${y}, ${dotR} ${y}" stroke="${col}" stroke-width="2.4" fill="none"/>
      <circle cx="${dotL}" cy="${y}" r="3.5" fill="${col}"/><circle cx="${dotR}" cy="${y}" r="3.5" fill="${col}"/>
      <text x="${bx1 - 12}" y="${y + 3.5}" text-anchor="end" class="hs-pin">${esc(lbl.slice(0, 30))}</text>
      <text x="${bx2 + 12}" y="${y + 3.5}" text-anchor="start" class="hs-hdr" fill="${col}">${esc(rlbl)}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${W} ${H}" class="harness-svg" preserveAspectRatio="xMidYMin meet">
    <rect x="${bx1}" y="${top - 14}" width="18" height="${H - top}" rx="5" class="hs-conn"/>
    <rect x="${bx2 - 18}" y="${top - 14}" width="18" height="${H - top}" rx="5" class="hs-conn"/>
    <text x="${bx1 + 9}" y="${top - 22}" text-anchor="middle" class="hs-title">MODULE ${esc(connector || '')}</text>
    <text x="${bx2 - 9}" y="${top - 22}" text-anchor="middle" class="hs-title">CAB HEADER</text>
    ${rows}</svg>`;
}
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
      { t: 'g', id: g(), tabs: ['triage', 'pcb', 'chat', 'plan', 'annotations', 'memories', 'api'], active: 'triage' }] }] }; }
// Dock layout is per-tab (sessionStorage) so multiple CANOPY tabs don't clobber each other;
// localStorage holds the last layout only as a seed for newly opened tabs.
function saveDock() { try { const s = JSON.stringify(state.dock); sessionStorage.setItem('canopy-dock', s); localStorage.setItem('canopy-dock', s); } catch {} }
function loadDock() { try { const raw = sessionStorage.getItem('canopy-dock') || localStorage.getItem('canopy-dock'); const d = JSON.parse(raw); if (d && d.t) { let mx = 0; (function walk(n){ if (n.t === 'g') mx = Math.max(mx, n.id); else n.kids.forEach(walk); })(d); state.gid = mx + 1; return d; } } catch {} return defaultDock(); }
function setTitle() { document.title = state.current ? `${state.current.label || [state.current.year, state.current.make, state.current.model].filter(Boolean).join(' ') || 'Untitled'} · CANOPY` : 'CANOPY · Vision'; }
function pcbZoomFor(id) { try { return (JSON.parse(localStorage.getItem('canopy-pcbzoom')) || {})[id] || 1; } catch { return 1; } }
function savePcbZoom(id, z) { try { const m = JSON.parse(localStorage.getItem('canopy-pcbzoom')) || {}; m[id] = z; localStorage.setItem('canopy-pcbzoom', JSON.stringify(m)); } catch {} }
const parentOf = (node, t) => { if (node.t !== 's') return null; for (let i = 0; i < node.kids.length; i++) { if (node.kids[i] === t) return { parent: node, idx: i }; const r = parentOf(node.kids[i], t); if (r) return r; } return null; };
const groupOfView = (node, v) => node.t === 'g' ? (node.tabs.includes(v) ? node : null) : node.kids.reduce((a, k) => a || groupOfView(k, v), null);
const firstGroup = n => n.t === 'g' ? n : firstGroup(n.kids[0]);
function findGroupById(n, id) { if (n.t === 'g') return n.id === id ? n : null; for (const k of n.kids) { const f = findGroupById(k, id); if (f) return f; } return null; }
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
// Reveal a view with minimal churn: only rebuild the whole dock when the view doesn't exist yet.
// If it already exists, just activate its group (or do nothing if already active) so unrelated
// panels — e.g. the Triage transcript and its scroll position — are left untouched.
function ensureView(v) {
  const g = groupOfView(state.dock, v);
  if (!g) { const fg = firstGroup(state.dock); fg.tabs.push(v); fg.active = v; saveDock(); renderDock(); }
  else if (g.active !== v) { g.active = v; saveDock(); rerenderGroup(g); }
}

function computeZone(r, x, y) { const fx = (x - r.left) / r.width, fy = (y - r.top) / r.height, m = Math.min(fx, 1 - fx, fy, 1 - fy);
  if (m > 0.22) return 'center'; return m === fx ? 'left' : m === 1 - fx ? 'right' : m === fy ? 'top' : 'bottom'; }
function showZone(z, side) { const b = { left: ['0', '0', '50%', '100%'], right: ['50%', '0', '50%', '100%'], top: ['0', '0', '100%', '50%'], bottom: ['0', '50%', '100%', '50%'], center: ['8%', '8%', '84%', '84%'] }[side];
  z.style.display = 'block'; z.style.left = b[0]; z.style.top = b[1]; z.style.width = b[2]; z.style.height = b[3]; }

function renderDock() { const ws = el('workspace'); ws.innerHTML = '';
  if (state.maxGroup != null) { const node = findGroupById(state.dock, state.maxGroup);
    if (node) { const g = renderGroup(node); g.classList.add('maximized'); ws.appendChild(g); return; }
    state.maxGroup = null; }
  ws.appendChild(renderNode(state.dock)); }
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
  if (hidden.length) { const add = document.createElement('div'); add.className = 'tab tab-icon'; add.innerHTML = svg('plus'); add.title = 'Add a panel'; add.onclick = e => addMenu(e, group, hidden); strip.appendChild(add); }
  const maxed = state.maxGroup === group.id;
  const mx = document.createElement('div'); mx.className = 'tab tab-icon'; mx.style.marginLeft = 'auto';
  mx.title = maxed ? 'Restore panel' : 'Maximize panel'; mx.innerHTML = svg(maxed ? 'compress' : 'expand');
  mx.onclick = () => { state.maxGroup = maxed ? null : group.id; renderDock(); }; strip.appendChild(mx);
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
  show(label, cancelable) { const t = el('aiToast'); t.innerHTML = `<div class="tt-head">${leaf()} <span>${esc(label)}</span>${cancelable ? '<button class="tt-stop" onclick="ui.cancelStream()">Stop</button>' : ''}</div><div class="tt-body" id="toastBody"></div>`; t.classList.remove('hidden'); if (this._t) clearTimeout(this._t); },
  body(text) { const b = el('toastBody'); if (b) b.textContent = text; },
  append(text) { const b = el('toastBody'); if (b) b.textContent = (b.textContent + text).slice(-600); },
  label(text) { const h = el('aiToast').querySelector('.tt-head span'); if (h) h.textContent = text; },
  done(label) { const t = el('aiToast'); const h = t.querySelector('.tt-head'); if (h) h.innerHTML = `${svg('bolt')} <span>${esc(label || 'Done')}</span>`; this.hide(2200); },
  hide(delay = 0) { if (this._t) clearTimeout(this._t); this._t = setTimeout(() => el('aiToast').classList.add('hidden'), delay); },
};

// ---------- modal ----------
function showModal(node) { closeModal(); const bd = document.createElement('div'); bd.className = 'modal-backdrop'; bd.id = 'modalBackdrop'; bd.appendChild(node); bd.addEventListener('mousedown', e => { if (e.target === bd) closeModal(); }); document.body.appendChild(bd); return bd; }
function closeModal() { const b = el('modalBackdrop'); if (b) b.remove(); }

// freehand / arrow / box annotation overlay for the lightbox (markup for the wiki)
const anno = {
  tool: 'pen', color: '#ef4444', strokes: [], cur: null, canvas: null, ctx: null, img: null,
  init(canvas, img) {
    this.canvas = canvas; this.img = img; this.strokes = []; this.cur = null;
    const w = img.clientWidth, h = img.clientHeight; canvas.width = w; canvas.height = h;
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px'; this.ctx = canvas.getContext('2d');
    const pt = e => { const r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
    canvas.onpointerdown = e => { canvas.setPointerCapture(e.pointerId); this.cur = { tool: this.tool, color: this.color, pts: [pt(e)] }; };
    canvas.onpointermove = e => { if (!this.cur) return; const p = pt(e); if (this.cur.tool === 'pen') this.cur.pts.push(p); else this.cur.pts[1] = p; this.redraw(); };
    canvas.onpointerup = () => { if (this.cur && this.cur.pts.length > 1) this.strokes.push(this.cur); this.cur = null; this.redraw(); };
    this.redraw();
  },
  setTool(t, btn) { this.tool = t; document.querySelectorAll('.lb-tools .tool').forEach(b => b.classList.toggle('active', b === btn)); },
  setColor(c) { this.color = c; document.querySelectorAll('.lb-sw').forEach(s => s.classList.toggle('active', s.dataset.c === c)); },
  undo() { this.strokes.pop(); this.redraw(); },
  clear() { this.strokes = []; this.redraw(); },
  _draw(ctx, s, W, H, scale) {
    ctx.strokeStyle = s.color; ctx.fillStyle = s.color; ctx.lineWidth = Math.max(2, 3 * scale); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const P = s.pts.map(([x, y]) => [x * W, y * H]);
    if (s.tool === 'pen') { ctx.beginPath(); P.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
    else if (s.tool === 'box') { const [a, b] = P; ctx.strokeRect(a[0], a[1], b[0] - a[0], b[1] - a[1]); }
    else if (s.tool === 'arrow') { const [a, b] = P; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0]); const hl = Math.max(10, 16 * scale);
      ctx.beginPath(); ctx.moveTo(b[0], b[1]); ctx.lineTo(b[0] - hl * Math.cos(ang - 0.4), b[1] - hl * Math.sin(ang - 0.4));
      ctx.lineTo(b[0] - hl * Math.cos(ang + 0.4), b[1] - hl * Math.sin(ang + 0.4)); ctx.closePath(); ctx.fill(); }
  },
  redraw() { const { ctx, canvas } = this; if (!ctx) return; ctx.clearRect(0, 0, canvas.width, canvas.height);
    const all = this.cur ? [...this.strokes, this.cur] : this.strokes;
    all.forEach(s => this._draw(ctx, s, canvas.width, canvas.height, 1)); },
  async save() {
    if (!this.img || !state.current) return; const st = el('lbStatus'); if (st) st.textContent = 'Saving…';
    const W = this.img.naturalWidth, H = this.img.naturalHeight;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const ctx = cv.getContext('2d');
    ctx.drawImage(this.img, 0, 0, W, H); const scale = W / this.canvas.width;
    this.strokes.forEach(s => this._draw(ctx, s, W, H, scale));
    try { const note = (el('lbCap') || {}).value || '';
      const r = await api.send(`/api/vehicles/${state.current.id}/annotation`, 'POST', { image: cv.toDataURL('image/png'), note: note.trim() });
      if (st) st.textContent = 'Saved to the Annotations tab'; aiToast.done('Annotation saved');
      const cap = el('lbSaveCap'); if (cap) cap.setAttribute('onclick', `ui.saveCaption(${r.id})`);
      ensureView('annotations');  // collect it into the Annotations gallery (visible when the lightbox closes)
    } catch (e) { if (st) st.textContent = ''; alert(e.message); }
  },
};

function viewIn(c) { c.classList.remove('view-in'); void c.offsetWidth; c.classList.add('view-in'); }
function renderViewInto(view, c) {
  if (!c) return;
  const globals = { cockpit: ui.viewCockpit, api: ui.viewApi, assistant: ui.viewAssistant, bench: ui.viewBench, research: ui.viewResearch, knowledge: ui.viewKnowledge, products: ui.viewProducts, dmm: ui.viewDmm, scope: ui.viewScope, siggen: ui.viewSiggen };
  if (globals[view]) { globals[view].call(ui, c); viewIn(c); return; }
  if (!state.current) { c.innerHTML = '<div class="empty">Select or create a project on the left.</div>'; viewIn(c); return; }
  ({ diagram: ui.viewDiagram, pinout: ui.viewPinout, plan: ui.viewPlan, chat: ui.viewChat, triage: ui.viewTriage, pcb: ui.viewPcb, memories: ui.viewMemories, annotations: ui.viewAnnotations, record: ui.viewRecord, wiki: ui.viewWiki, guided: ui.viewGuided, profile: ui.viewProfile })[view].call(ui, c);
  viewIn(c);
}

// ================= UI =================
const ui = {
  async init() {
    document.documentElement.dataset.theme = state.theme;
    el('sidebarToggle').innerHTML = svg('menu'); el('themeToggle').innerHTML = svg(state.theme === 'dark' ? 'sun' : 'moon');
    el('resetBtn').innerHTML = svg('reset'); el('apiBtn').innerHTML = svg('api'); el('newRecBtn').innerHTML = svg('plus'); el('searchIcon').innerHTML = svg('search');
    el('assistantBtn').innerHTML = svg('leaf'); el('benchBtn').innerHTML = svg('bench'); el('researchBtn').innerHTML = svg('search'); el('logoutBtn').innerHTML = svg('logout');
    const kbtn = el('knowledgeBtn'); if (kbtn) kbtn.innerHTML = svg('book');
    const pbtn = el('productsBtn'); if (pbtn) pbtn.innerHTML = svg('catalog');
    const ckb = el('cockpitBtn'); if (ckb) ckb.innerHTML = svg('cockpit');
    const adb = el('adminBtn'); if (adb) adb.innerHTML = svg('gear');
    ['dmm:gauge', 'scope:scope', 'siggen:siggen'].forEach(p => { const [id, ic] = p.split(':'); const b = el(id + 'Btn'); if (b) b.innerHTML = svg(ic); });
    api.get('/api/auth/status').then(s => {
      const u = s.user || {}; state.user = u; state.team = s.team || null;
      if (s.auth) el('logoutBtn').classList.remove('hidden');
      const b = el('userBadge');
      if (b && s.auth) { b.classList.remove('hidden');
        const t = s.team;
        b.title = `${u.username}${u.role === 'admin' ? ' · Admin' : ' · Member'}${t ? ' · Team: ' + t.name : ''}`;
        b.innerHTML = `${t ? `<span class="ub-team" style="--tc:${esc(t.color)}" title="Team: ${esc(t.name)}"><i></i><b>${esc(t.name)}</b></span>` : ''}<span class="ub-name">${esc(u.username || '')}</span><span class="ub-role ${esc(u.role)}">${u.role === 'admin' ? 'Admin' : 'Member'}</span>`; }
      const adb = el('adminBtn'); if (adb && u.role === 'admin') adb.classList.remove('hidden');  // admin console is admin-only
    }).catch(() => {});
    el('fileInput').onchange = e => e.target.files[0] && this.uploadFile(e.target.files[0]);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && state.streamCtrl) this.cancelStream(); });
    state.dock = loadDock();
    this.checkHealth(); await this.loadRecords();
    let want = null; try { want = parseInt(sessionStorage.getItem('canopy-project'), 10); } catch {}
    const pick = state.records.find(r => r.id === want) || state.records[0];
    if (pick) await this.select(pick.id); else { setTitle(); renderDock(); }
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
  async loadRecords() { state.records = await api.cget('/api/vehicles'); this.renderRecords(); },
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
  newRecord() { this.startWizard(); },  // guided onboarding instead of a blank project
  async select(id) { state.current = await api.cget('/api/vehicles/' + id); state.page = 0; state.selectedPin = null; state.plan = ''; state.zoom = 1; state.triageMsgs = null; state.triageImage = null; state.pcbImage = null; state.pcbComponents = null; state.pcbSel = null; state.pcbZoom = pcbZoomFor(id); state.pcbEdit = null; state.pcbPhotos = null; state.pcbPhotoId = null; state.pcbEditMode = false; state.wikiMd = null; state.guidedLog = null; state.guidedStep = null; state.guidedPhase = 'intake'; state.guidedSymptom = ''; state.guidedThinking = null; state.profileYaml = null; state.profileObj = null; state.profileSaved = false; state.measurements = null;
    try { sessionStorage.setItem('canopy-project', id); } catch {} setTitle(); this.renderRecords(); renderDock(); },

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
    c.innerHTML = `<div id="productBanner"></div><h3 class="sec">Project details</h3>
      <label class="field"><span>Label</span><input id="f_label" value="${esc(v.label || '')}" placeholder="e.g. 2016 F-250 PCM"></label>
      <div class="row"><label class="field" style="flex:2"><span>VIN</span><input id="f_vin" value="${esc(v.vin || '')}"></label><label class="field"><span>Year</span><input id="f_year" value="${esc(v.year || '')}"></label></div>
      <div class="row"><label class="field" style="flex:1"><span>Make</span><input id="f_make" value="${esc(v.make || '')}"></label><label class="field" style="flex:1"><span>Model</span><input id="f_model" value="${esc(v.model || '')}"></label></div>
      <div class="row" style="margin-bottom:14px"><button class="primary" onclick="ui.saveVehicle()">Save</button><button onclick="ui.identify()">Identify from diagram</button><button onclick="ui.openView('annotations')">${svg('annotations')} Annotations</button><button onclick="ui.promoteProduct()">${svg('catalog')} Promote to Product</button><button class="ghost danger" onclick="ui.deleteVehicle()">Delete</button></div>`;
    this.loadProductMatch();
    c.innerHTML += `
      <h3 class="sec">Tags</h3><div class="tags" style="margin-bottom:10px">${(v.tags || []).map(t => `<span class="tagchip rm" onclick="ui.removeTag('${esc(t).replace(/'/g, "")}')">${esc(t)} ✕</span>`).join('') || '<span class="muted">No tags.</span>'}</div>
      <div class="chat-input"><input id="tagIn" placeholder="Add a tag (e.g. Duramax)" onkeydown="if(event.key==='Enter')ui.addTag()"><button onclick="ui.addTag()">${svg('tag')} Add</button><button onclick="ui.extractTags()" id="tagAiBtn">${svg('bolt')} AI tags</button></div>`; },

  // ---------- NPI cockpit (every project's pipeline readiness) ----------
  ckCard(p) {
    const STAGES = [['identity', 'ID'], ['diagram', 'Diagram'], ['pinout', 'Pinout'], ['pcb', 'PCB'], ['findings', 'Findings'], ['profile', 'Profile'], ['product', 'Product']];
    const title = esc([p.year, p.make, p.model].filter(Boolean).join(' ') || p.label || 'Untitled');
    const team = p.team ? `<div class="ck-teamrow"><span class="ck-team" style="--tcol:${esc(p.team.color)}"><i></i>${esc(p.team.name)}</span></div>` : '';
    return `<div class="ck-card${p.team ? ' owned' : ''}"${p.team ? ` style="--tcol:${esc(p.team.color)}"` : ''} onclick="ui.cockpitOpen(${p.id})">
      <div class="ck-top"><div class="ck-title">${title}</div>${p.units ? `<span class="units-badge" title="units serviced">${p.units}</span>` : ''}</div>
      ${team}<div class="ck-bar"><span style="width:${p.progress}%"></span></div>
      <div class="ck-stages">${STAGES.map(([k, lbl]) => `<span class="ck-st ${p.stages[k] ? 'on' : ''}" title="${lbl}">${p.stages[k] ? svg('check') : ''}<i>${lbl}</i></span>`).join('')}</div>
      <div class="ck-next">${p.next ? `Next: <b>${esc(p.next)}</b>` : '<span class="ck-ready">' + svg('check') + ' ready to list</span>'}</div></div>`;
  },
  viewCockpit(c) {
    if (state.cockpit == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadCockpit(); return; }
    const q = (state.cockpitQ || '').toLowerCase();
    let rows = state.cockpit.filter(p => !q || [p.label, p.make, p.model, p.year, ...(p.tags || [])].join(' ').toLowerCase().includes(q));
    rows = rows.slice().sort((a, b) => b.progress - a.progress);
    const card = p => this.ckCard(p);
    c.innerHTML = `<div class="ck-col">
      <div class="ck-head"><h3 class="sec" style="margin:0">NPI Cockpit</h3>
        <input id="ckQ" placeholder="Search modules…" value="${esc(state.cockpitQ || '')}" oninput="ui.cockpitSearch(this.value)" style="max-width:240px">
        <button class="primary" onclick="ui.startWizard()">${svg('plus')} New module (guided)</button>
        <button class="iconbtn" title="Refresh" onclick="ui.loadCockpit(true)">${svg('reset')}</button>
        <span class="muted" style="font-size:11px">${rows.length} module(s)</span></div>
      ${rows.length ? `<div class="ck-grid">${rows.map(card).join('')}</div>` : '<div class="empty">No modules yet. Click <b>New module (guided)</b> to onboard one.</div>'}</div>`;
  },
  async loadCockpit(force) { if (force) state.cockpit = null; try { state.cockpit = await api.get('/api/cockpit'); } catch { state.cockpit = []; } rerenderView('cockpit'); },
  cockpitSearch(v) { state.cockpitQ = v; const g = document.querySelector('.ck-grid'); if (!g) { rerenderView('cockpit'); return; }
    const q = v.toLowerCase(); const rows = state.cockpit.filter(p => !q || [p.label, p.make, p.model, p.year, ...(p.tags || [])].join(' ').toLowerCase().includes(q)).sort((a, b) => b.progress - a.progress);
    g.innerHTML = rows.map(p => this.ckCard(p)).join('') || '<div class="empty">No matches.</div>';
  },
  async cockpitOpen(id) { await this.select(id); ensureView('record'); },

  // ---------- guided onboarding wizard (TurboTax-style new-module flow) ----------
  startWizard() {
    state.wizard = { step: 0, vid: null, identity: { label: '', make: '', model: '', year: '' },
      diagram: false, pinouts: 0, components: 0, pcbImage: null, symptom: '', match: null };
    let ov = el('wizard');
    if (!ov) { ov = document.createElement('div'); ov.id = 'wizard'; document.body.appendChild(ov); }
    this.renderWizard();
  },
  wizardClose() { const ov = el('wizard'); if (ov) ov.remove(); this.loadRecords(); state.cockpit = null; },
  renderWizard() {
    const ov = el('wizard'); if (!ov) return; const w = state.wizard;
    const STEPS = [
      { key: 'identify', title: 'Identify the module', skip: false },
      { key: 'diagram', title: 'Wiring diagram', skip: true },
      { key: 'pcb', title: 'Board photo', skip: true },
      { key: 'symptom', title: 'Customer symptom', skip: true },
      { key: 'review', title: 'Review & open', skip: false },
    ];
    const s = STEPS[w.step]; let body = '';
    if (w.busy) body = `<div class="wiz-busy">${leaf('big')}<div>${esc(w.busy)}</div></div>`;
    else
    if (s.key === 'identify') body = `<div class="wiz-grid">
        <label class="field"><span>Label</span><input id="wizLabel" value="${esc(w.identity.label)}" placeholder="e.g. 2016 F-250 PCM"></label>
        <div class="row"><label class="field" style="flex:1"><span>Year</span><input id="wizYear" value="${esc(w.identity.year)}"></label><label class="field" style="flex:2"><span>Make</span><input id="wizMake" value="${esc(w.identity.make)}"></label><label class="field" style="flex:2"><span>Model</span><input id="wizModel" value="${esc(w.identity.model)}"></label></div>
        ${w.match ? `<div class="prod-banner">${svg('catalog')} We've serviced this — <b>${esc([w.match.year, w.match.make, w.match.model].filter(Boolean).join(' '))}</b> · ${w.match.units} unit(s). The saved profile &amp; wiki will be reused.</div>` : ''}</div>`;
    else if (s.key === 'diagram') body = `<div class="wiz-drop">${w.diagram ? `<div class="wiz-ok">${svg('check')} Diagram added${w.pinouts ? ` · ${w.pinouts} pins extracted` : ''}</div>` : `<button onclick="ui.wizDiagramPick()">${svg('upload')} Upload wiring diagram</button>`}
        ${w.diagram && !w.pinouts ? `<button class="primary" onclick="ui.wizExtract()">${svg('bolt')} Extract pinout</button>` : ''}</div>`;
    else if (s.key === 'pcb') body = `<div class="wiz-drop">${w.pcbImage ? `<img src="${w.pcbImage}" class="wiz-thumb">` : ''}
        <button onclick="ui.wizPcbPick()">${svg('chip')} ${w.components ? 'Replace board photo' : 'Upload board photo'}</button>
        ${w.components ? `<div class="wiz-ok">${svg('check')} ${w.components} components identified</div>` : ''}</div>`;
    else if (s.key === 'symptom') body = `<textarea id="wizSymptom" class="wiz-symptom" placeholder="e.g. No communication / no-start; intermittent after warm-up…">${esc(w.symptom)}</textarea>`;
    else body = `<div class="wiz-review">
        <div class="wr-row"><span>Module</span><b>${esc([w.identity.year, w.identity.make, w.identity.model].filter(Boolean).join(' ') || w.identity.label || '—')}</b></div>
        <div class="wr-row"><span>Wiring diagram</span><b>${w.diagram ? `added · ${w.pinouts} pins` : 'skipped'}</b></div>
        <div class="wr-row"><span>Board photo</span><b>${w.components ? `${w.components} components` : 'skipped'}</b></div>
        <div class="wr-row"><span>Symptom</span><b>${esc(w.symptom || 'not stated')}</b></div>
        ${w.match ? `<div class="prod-banner">${svg('catalog')} Matches an existing product (${w.match.units} units serviced).</div>` : ''}</div>`;
    ov.innerHTML = `<div class="wiz">
      <div class="wiz-head"><span class="wordmark">CANOPY</span><span class="wiz-sub">New module onboarding</span><button class="iconbtn" style="margin-left:auto" title="Close" onclick="ui.wizardClose()">${svg('close')}</button></div>
      <div class="wiz-stepper">${STEPS.map((x, i) => `<div class="wiz-pip ${i === w.step ? 'cur' : (i < w.step ? 'done' : '')}"><span>${i < w.step ? svg('check') : i + 1}</span>${x.title.split(' ')[0]}</div>`).join('')}</div>
      <h2 class="wiz-title">${s.title}</h2>
      <div class="wiz-body">${body}</div>
      <div class="wiz-assist">${svg('leaf')}<span><b>Sage</b> · ${this.wizAssist(s.key)}</span></div>
      <div class="wiz-nav"><button onclick="ui.wizardBack()" ${w.step === 0 || w.busy ? 'disabled' : ''}>Back</button><div class="spacer"></div>${s.skip ? `<button class="ghost" onclick="ui.wizardNext(true)" ${w.busy ? 'disabled' : ''}>Skip</button>` : ''}<button class="primary" onclick="ui.wizardNext()" ${w.busy ? 'disabled' : ''}>${w.step === STEPS.length - 1 ? 'Open workspace' : 'Next'}</button></div>
    </div>`;
  },
  wizAssist(key) {  // Sage's live, data-aware prompts
    const w = state.wizard;
    if (key === 'identify') return w.match ? `I've serviced this one before — <b>${esc([w.match.year, w.match.make, w.match.model].filter(Boolean).join(' '))}</b>, ${w.match.units} unit(s). I'll reuse the saved CAB profile &amp; wiki, so this'll be quick.` : "Snap the label or type the make / model / year — I'll check whether we've serviced this module before.";
    if (key === 'diagram') { if (w.summary) { const s = w.summary; const bits = [s.can && 'a CAN bus', s.power && 'power', s.ground && 'ground'].filter(Boolean);
      return `Read <b>${s.pins} pins</b>${bits.length ? ' — I can see ' + bits.join(', ') : ''}.${w.tags && w.tags.length ? ` Tagged it: ${w.tags.slice(0, 6).map(esc).join(', ')}.` : ''} Next, photograph the board.`; }
      return "Drop the wiring diagram (image or PDF) — I'll read the connector pinout and tag the module automatically. No diagram yet? Skip it."; }
    if (key === 'pcb') return w.components ? `Boxed <b>${w.components} components</b> — I'll flag the usual failure points when we triage; you can correct any of them later.` : "Photograph the top of the board and I'll identify the components and read their part markings.";
    if (key === 'symptom') return "What's the customer's complaint? Even a short note focuses the triage and goes into the repair record.";
    return `Everything's collected${w.summary ? ` — ${w.summary.pins} pins` : ''}${w.components ? `, ${w.components} components` : ''}${w.tags && w.tags.length ? ', tags' : ''} and your symptom. Open the workspace and we'll triage and build the wiki.`;
  },
  wizardBack() { if (state.wizard.step > 0) { state.wizard.step--; this.renderWizard(); } },
  async wizardNext(skip) {
    const w = state.wizard;
    if (w.step === 0) {  // create/update the project, check for a known product
      const g = id => (el(id) || {}).value || '';
      w.identity = { label: g('wizLabel'), make: g('wizMake'), model: g('wizModel'), year: g('wizYear') };
      try {
        if (!w.vid) { const v = await api.send('/api/vehicles', 'POST', w.identity); w.vid = v.id; }
        else await api.send('/api/vehicles/' + w.vid, 'PATCH', w.identity);
        const m = await api.get(`/api/vehicles/${w.vid}/product-match`); w.match = m.match;
      } catch (e) { alert(e.message); return; }
    } else if (w.step === 3 && !skip) {  // save symptom into the record
      const t = (el('wizSymptom') || {}).value.trim();
      if (t) { w.symptom = t; try { await api.send(`/api/vehicles/${w.vid}/memories`, 'POST', { content: 'Customer symptom: ' + t, kind: 'case' }); } catch {} }
    } else if (w.step === 4) { return this.wizardFinish(); }
    w.step++; this.renderWizard();
  },
  wizDiagramPick() { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*,application/pdf';
    inp.onchange = async e => { const f = e.target.files[0]; if (!f) return; const w = state.wizard;
      w.busy = 'Uploading the wiring diagram…'; this.renderWizard();
      try { await api.upload(`/api/vehicles/${w.vid}/diagram`, f); w.diagram = true; w.busy = null; this.renderWizard(); this.wizExtract(); }
      catch (er) { w.busy = null; this.renderWizard(); alert(er.message); } };
    inp.click();
  },
  async wizExtract() { const w = state.wizard;
    w.busy = 'Reading the connector pinout…'; this.renderWizard();
    try {
      const r = await api.send(`/api/vehicles/${w.vid}/extract`, 'POST', { all_pages: true });
      const pins = r.pinouts || []; w.pinouts = pins.length;
      const txt = pins.map(p => `${p.signal || ''} ${p.function || ''}`).join(' ').toLowerCase();
      w.summary = { pins: pins.length, can: /\bcan\b|can[\s_-]?h|can[\s_-]?l/.test(txt),
        power: /b\+|kl30|kl15|vbat|batt|\bpower\b|\bign/.test(txt), ground: /gnd|ground|return/.test(txt) };
      w.busy = 'Pulling useful tags from the diagram…'; this.renderWizard();
      try { const t = await api.send(`/api/vehicles/${w.vid}/extract-tags`, 'POST', { all_pages: true }); w.tags = t.tags || []; } catch {}
    } catch (e) { alert(e.message); }
    w.busy = null; this.renderWizard();
  },
  wizPcbPick() { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
    inp.onchange = e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader();
      r.onload = async () => { const w = state.wizard; w.pcbImage = r.result; w.busy = 'Analyzing the board — boxing &amp; identifying components…'; this.renderWizard();
        try { const res = await api.send(`/api/vehicles/${w.vid}/pcb`, 'POST', { image: r.result }); w.components = (res.components || []).length; }
        catch (er) { alert(er.message); }
        w.busy = null; this.renderWizard(); };
      r.readAsDataURL(f); };
    inp.click();
  },
  async wizardFinish() { const vid = state.wizard.vid; this.wizardClose(); if (vid) { await this.select(vid); ensureView('record'); ensureView('wiki'); } },

  // ---------- product library (reusable SKUs: profile + wiki + BOM + cases) ----------
  async loadProductMatch() {
    const b = el('productBanner'); if (!b || !state.current) return;
    try { const r = await api.get(`/api/vehicles/${state.current.id}/product-match`); const m = r.match;
      b.innerHTML = m ? `<div class="prod-banner">${svg('catalog')} Known product — <b>${esc([m.year, m.make, m.model, m.module_class].filter(Boolean).join(' '))}</b> · ${m.units} unit(s) serviced · <a href="#" onclick="ui.openProduct(${m.id});return false">open in Products</a></div>` : '';
    } catch { b.innerHTML = ''; }
  },
  async promoteProduct() {
    if (!state.current) return; aiToast.show('Promoting to Product library…');
    try { const p = await api.send(`/api/vehicles/${state.current.id}/promote`, 'POST');
      state.products = null; aiToast.done(`Product saved — ${p.units} unit(s) serviced`); this.loadProductMatch();
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  viewProducts(c) {
    if (state.products == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadProducts(); return; }
    c.innerHTML = `<div class="prod-col"><div class="row" style="margin-bottom:10px;align-items:center"><h3 class="sec" style="margin:0">Product library</h3><span class="muted" style="margin-left:auto;font-size:11px">${state.products.length} product(s) — the SKUs you service</span></div>
      ${state.products.length ? `<div class="prod-grid">${state.products.map(p => `<div class="prod-card"><div class="pc-title">${esc([p.year, p.make, p.model].filter(Boolean).join(' ') || p.label || 'Module')}</div>
        <div class="pc-sub">${esc(p.module_class || '')}${p.part_number ? ' · ' + esc(p.part_number) : ''}</div>
        <div class="pc-units"><span class="units-badge">${p.units}</span> unit(s) serviced</div>
        <div class="row" style="margin-top:auto;padding-top:8px"><button onclick="ui.openProduct(${p.id})">Open</button><button class="primary" style="flex:1" onclick="ui.productListing(${p.id})">${svg('record')} Listing</button><button class="iconbtn danger" title="Remove" onclick="ui.deleteProduct(${p.id})">${svg('trash')}</button></div></div>`).join('')}</div>`
        : '<div class="empty">No products yet. Open a project, confirm its <b>Profile</b> and <b>Wiki</b>, then click <b>Promote to Product</b> on its Record tab. The first unit of a module mints a reusable product; later units match it instantly.</div>'}</div>`;
  },
  async loadProducts() { try { state.products = await api.get('/api/products'); } catch { state.products = []; } rerenderView('products'); },
  async openProduct(id) {
    try { const p = await api.get('/api/product/' + id);
      const m = document.createElement('div'); m.className = 'modal'; m.style.width = 'min(820px,95vw)';
      m.innerHTML = `<div class="m-head">${svg('catalog')} ${esc([p.year, p.make, p.model].filter(Boolean).join(' ') || p.label || 'Product')}</div>
        <div class="m-sub">${esc(p.module_class || '')}${p.part_number ? ' · P/N ' + esc(p.part_number) : ''} · ${p.units} unit(s) serviced</div>
        <div class="m-body md" style="max-height:64vh;overflow:auto">${md(p.wiki || '_No wiki captured for this product yet._')}</div>
        <div class="m-foot"><button class="primary" onclick="ui.productListing(${p.id})">${svg('record')} Generate listing</button><button onclick="closeModal()">Close</button></div>`;
      showModal(m);
    } catch (e) { alert(e.message); }
  },
  async productListing(id) {
    aiToast.show('Writing product listing…', true);
    try { const r = await api.send('/api/product/' + id + '/listing', 'POST'); state.lastListing = r.listing; aiToast.done('Listing ready');
      const m = document.createElement('div'); m.className = 'modal'; m.style.width = 'min(760px,94vw)';
      m.innerHTML = `<div class="m-head">${svg('record')} Product listing</div><div class="m-body md" style="max-height:68vh;overflow:auto">${md(r.listing)}</div><div class="m-foot"><button onclick="ui.copyListing()">Copy Markdown</button><button class="primary" onclick="closeModal()">Close</button></div>`;
      showModal(m);
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  copyListing() { if (state.lastListing) navigator.clipboard?.writeText(state.lastListing); aiToast.show('Copied'); aiToast.hide(1200); },
  async deleteProduct(id) { if (!confirm('Remove this product from the library?')) return;
    try { await api.send('/api/product/' + id, 'DELETE'); state.products = (state.products || []).filter(p => p.id !== id); rerenderView('products'); } catch (e) { alert(e.message); }
  },

  // ---------- api docs ----------
  async viewApi(c) { if (!state.apiRef) { c.innerHTML = '<p class="muted">Loading API reference…</p>'; try { state.apiRef = await api.get('/api/reference'); } catch { c.innerHTML = '<p class="warn">Could not load reference.</p>'; return; } }
    const ref = state.apiRef;
    c.innerHTML = `<h3 class="sec">REST API</h3><p class="muted">All endpoints are local. Interactive Swagger: <a href="${ref.swagger}" target="_blank">${ref.swagger}</a> · OpenAPI: <a href="${ref.openapi}" target="_blank">${ref.openapi}</a> (import into Postman).</p>
      ${ref.groups.map(gr => `<div class="api-group"><h4>${esc(gr.group)}</h4>${gr.endpoints.map(e => `<div class="api-ep"><div><span class="m">${esc(e.method)}</span> <span class="p">${esc(e.path)}</span></div><div class="u">${esc(e.use)}</div>${e.example ? `<pre>${esc(e.example)}</pre>` : ''}</div>`).join('')}</div>`).join('')}`; },

  // ---------- project CRUD from sidebar ----------
  async renameRecord(id) { const v = state.records.find(r => r.id === id); const name = prompt('Project name', v ? (v.label || '') : ''); if (name == null) return; await api.send('/api/vehicles/' + id, 'PATCH', { label: name.trim() }); if (state.current && state.current.id === id) { state.current.label = name.trim(); setTitle(); } await this.loadRecords(); if (state.current && state.current.id === id) rerenderView('record'); },
  async deleteRecord(id) { if (!confirm('Delete this project and its diagrams/memories?')) return; await api.send('/api/vehicles/' + id, 'DELETE'); if (state.current && state.current.id === id) { state.current = null; try { sessionStorage.removeItem('canopy-project'); } catch {} setTitle(); renderDock(); } await this.loadRecords(); },
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
        <div class="muted" style="margin-top:6px">Pick a SocketCAN device (a CANable / USB-to-CAN adapter or vcan0), or 'virtual' for a dry run.</div></div>
      <div class="bench-section"><h4>${svg('cab')} Restbus simulation <span id="rbState" class="muted" style="font-weight:400;font-size:11px"></span></h4>
        <div class="muted" style="margin-bottom:6px">Load a platform DBC, then broadcast the absent ECUs' periodic frames (ignition, NM, speed…) so the module wakes up as if installed.</div>
        <div class="row"><input id="rbFile" type="file" accept=".dbc" style="flex:1"><button onclick="ui.benchDbcUpload()">Load DBC</button><button class="primary" onclick="ui.benchRestbusStart()">Start</button><button onclick="ui.benchRestbusStop()">Stop</button></div>
        <div id="rbMsgs" class="rb-msgs" style="margin-top:8px"></div></div>
      <div class="bench-section"><h4>Probe ECU</h4>
        <div class="row"><input id="bReq" value="0x7E0" style="width:90px" title="request id"><input id="bRsp" value="0x7E8" style="width:90px" title="response id"><button class="primary" onclick="ui.benchPing()">Ping &amp; confirm connectivity</button></div>
        <div id="bPingOut" class="kvp" style="margin-top:9px"></div></div>
      <div class="bench-section"><h4>Diagnostic trouble codes (UDS 0x19)</h4>
        <div class="row"><input id="bDReq" value="0x7E0" style="width:90px"><input id="bDRsp" value="0x7E8" style="width:90px"><button class="primary" onclick="ui.benchReadDtcs()">Read DTCs</button></div>
        <div id="bDtcOut" style="margin-top:8px"></div></div>
      <div class="bench-section"><h4>UDS request (read data / actuator output control)</h4>
        <div class="muted" style="margin-bottom:6px">Hex payload — e.g. <code>22F190</code> read VIN · <code>1902FF</code> read DTCs · <code>2F&lt;did&gt;03&lt;state&gt;</code> output control.</div>
        <div class="row"><input id="bUReq" value="0x7E0" style="width:90px"><input id="bURsp" value="0x7E8" style="width:90px"><input id="bUPayload" placeholder="22F190" style="flex:1"><button onclick="ui.benchUds()">Send UDS</button></div>
        <div id="bUdsOut" class="muted" style="margin-top:8px"></div>${hints}</div>
      <div class="bench-section"><h4>Send raw frame</h4>
        <div class="row"><input id="bFid" placeholder="123" style="width:90px"><input id="bFdata" placeholder="DE AD BE EF" style="flex:1"><button onclick="ui.benchSend()">Send</button></div></div>
      <div class="bench-section"><h4>Live traffic</h4><div class="frame-log" id="bFrames"><span class="muted">Connect to see frames.</span></div></div>`;
    this.benchLoadInterfaces(); this.benchRefreshStatus(); this.benchRestbusRefresh();
  },
  async benchDbcUpload() {
    const f = el('rbFile') && el('rbFile').files[0]; if (!f) { alert('Choose a .dbc file first.'); return; }
    aiToast.show('Loading DBC…');
    try { const r = await api.upload('/api/can/dbc', f); this.renderRestbus(r); aiToast.done('DBC loaded: ' + r.dbc); }
    catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  async benchRestbusRefresh() { try { this.renderRestbus(await api.get('/api/can/restbus')); } catch {} },
  renderRestbus(r) {
    const st = el('rbState'), box = el('rbMsgs');
    if (st) st.textContent = (r && r.loaded) ? `${r.dbc} · ${r.count ? 'broadcasting ' + r.count + ' frame(s)' : 'idle'}` : '';
    if (box) box.innerHTML = (r && r.messages || []).map(m => `<div class="rb-m ${m.running ? 'on' : ''}"><span class="fid">${esc(m.id)}</span> ${esc(m.name)} <span class="muted">${m.cycle_ms ? m.cycle_ms + 'ms' : 'no cycle'}</span>${m.running ? '<span class="ok-badge yes" style="margin-left:auto">TX</span>' : ''}</div>`).join('');
  },
  async benchRestbusStart() { try { this.renderRestbus(await api.send('/api/can/restbus/start', 'POST', { messages: [] })); aiToast.show('Restbus broadcasting'); aiToast.hide(1400); } catch (e) { alert(e.message); } },
  async benchRestbusStop() { try { this.renderRestbus(await api.send('/api/can/restbus/stop', 'POST')); } catch (e) { alert(e.message); } },
  async benchReadDtcs() {
    const out = el('bDtcOut'); out.innerHTML = '<span class="spinner"></span> reading…';
    try { const r = await api.send('/api/can/dtcs', 'POST', { request_id: el('bDReq').value, response_id: el('bDRsp').value });
      if (!r.ok) { out.innerHTML = `<span class="warn">${esc(r.error || 'no response')}</span>`; return; }
      out.innerHTML = r.dtcs.length ? `<div class="dtc-list">${r.dtcs.map(d => `<span class="dtc ${d.confirmed ? 'conf' : ''}" title="status ${d.status} · ftb ${d.ftb}">${esc(d.code)}</span>`).join('')}</div>` : '<span class="ok-badge yes">No stored DTCs</span>';
    } catch (e) { out.innerHTML = `<span class="warn">${esc(e.message)}</span>`; }
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
  benchPoll() { state.benchTimer = setInterval(async () => { const log = el('bFrames'); if (!log) { clearInterval(state.benchTimer); state.benchTimer = null; return; } try { const r = await api.get('/api/can/frames?since=' + (state.benchSince || 0)); for (const f of r.frames) { state.benchSince = f.seq; const dec = f.decoded ? ` <span class="fdec">${esc(f.decoded.name)}: ${esc(Object.entries(f.decoded.signals).map(([k, v]) => k + '=' + v).join(' '))}</span>` : ''; log.insertAdjacentHTML('afterbegin', `<div class="fr"><span class="fid">${f.id}</span>${f.ext ? 'x' : ''} ${f.data}${dec}</div>`); } while (log.children.length > 200) log.lastChild.remove(); } catch {} }, 1000); },
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

  // ---------- bench instruments: DMM / Oscilloscope / Signal Generator ----------
  viewDmm(c) {
    const modes = [['vdc', 'V⏜', 'DC volts'], ['vac', 'V∿', 'AC volts'], ['adc', 'A⏜', 'DC current'], ['aac', 'A∿', 'AC current'], ['resistance', 'Ω', 'resistance'], ['continuity', '•))', 'continuity'], ['frequency', 'Hz', 'frequency']];
    const m = state.dmmMode || 'vdc';
    this.instrEnsure('dmm');
    c.innerHTML = `<div class="instr dmm">
      <div class="instr-head">${svg('gauge')} Digital Multimeter ${this.instrSourceBar()}</div>
      <div class="dmm-modes">${modes.map(([k, sym, lbl]) => `<button class="${k === m ? 'primary' : ''}" title="${lbl}" onclick="ui.dmmMode('${k}')">${sym}</button>`).join('')}</div>
      <div class="dmm-screen"><div class="dmm-val" id="dmmVal">--</div><div class="dmm-unit" id="dmmUnit"></div><div class="dmm-extra" id="dmmExtra"></div></div>
      ${this.measPanel('dmm')}
      <div class="muted" style="font-size:11px;margin-top:10px">Simulated by default — the <b>Signal Generator</b> drives these readings. Connect a USB DMM (Source) for live hardware.</div></div>`;
    this.dmmStart(); this.loadMeasurements();
  },
  dmmMode(k) { state.dmmMode = k; rerenderView('dmm'); },
  dmmStart() {
    if (state.dmmTimer) clearInterval(state.dmmTimer);
    const tick = async () => {
      const v = el('dmmVal'); if (!v) { clearInterval(state.dmmTimer); state.dmmTimer = null; return; }
      try { const r = await api.get('/api/instr/dmm?mode=' + (state.dmmMode || 'vdc')); state.dmmLast = r;
        if (r.mode === 'continuity') { v.textContent = r.continuity ? 'CONT' : 'OPEN'; v.className = 'dmm-val' + (r.continuity ? ' beep' : ''); el('dmmUnit').textContent = ''; el('dmmExtra').textContent = r.value + ' Ω'; }
        else { const [val, unit] = fmtMeas(r.value, r.unit); v.textContent = val; v.className = 'dmm-val'; el('dmmUnit').textContent = unit; el('dmmExtra').textContent = r.overload ? 'OL' : ''; }
      } catch {}
    };
    tick(); state.dmmTimer = setInterval(tick, 300);
  },
  viewScope(c) {
    this.instrEnsure('scope');
    const tb = state.scopeTb || 5e-4, vdiv = state.scopeVdiv || 0.5, run = state.scopeRun !== false;
    const tg = state.scopeTrig || (state.scopeTrig = { level: 0, edge: 'rising', mode: 'auto', coupling: 'dc' });
    const tbs = [['10µs', 1e-5], ['50µs', 5e-5], ['0.1ms', 1e-4], ['0.5ms', 5e-4], ['1ms', 1e-3], ['5ms', 5e-3], ['10ms', 1e-2]];
    const vds = [0.05, 0.1, 0.2, 0.5, 1, 2];
    c.innerHTML = `<div class="instr scope">
      <div class="instr-head">${svg('scope')} Oscilloscope <span class="muted" id="scopeRead" style="font-weight:400;font-size:11px"></span>${this.instrSourceBar()}</div>
      <div class="scope-screen"><canvas id="scopeCanvas"></canvas></div>
      <div class="scope-ctl">
        <label>Time/div <select onchange="ui.scopeSet('tb',this.value)">${tbs.map(([l, val]) => `<option value="${val}" ${val === tb ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
        <label>V/div <select onchange="ui.scopeSet('vdiv',this.value)">${vds.map(val => `<option value="${val}" ${val === vdiv ? 'selected' : ''}>${val} V</option>`).join('')}</select></label>
        <label>Coupling <select onchange="ui.scopeSet('coupling',this.value)">${['dc', 'ac'].map(x => `<option value="${x}" ${tg.coupling === x ? 'selected' : ''}>${x.toUpperCase()}</option>`).join('')}</select></label>
        <button class="${run ? 'danger' : 'primary'}" onclick="ui.scopeSet('run',${run ? 0 : 1})">${run ? 'Stop' : 'Run'}</button>
        <button onclick="ui.captureScope()" style="margin-left:auto">${svg('record')} Capture</button></div>
      ${this.measPanel('scope')}
      <div class="scope-ctl trig">
        <span class="trig-lbl">Trigger</span>
        <label>Level <div class="sg-in" style="width:120px"><input type="number" step="0.1" value="${tg.level}" onchange="ui.scopeSet('trigLevel',this.value)"><span>V</span></div></label>
        <div class="seg">${['rising', 'falling'].map(x => `<button class="${tg.edge === x ? 'primary' : ''}" onclick="ui.scopeSet('trigEdge','${x}')">${x === 'rising' ? '↑' : '↓'}</button>`).join('')}</div>
        <div class="seg">${['auto', 'normal', 'single'].map(x => `<button class="${tg.mode === x ? 'primary' : ''}" onclick="ui.scopeSet('trigMode','${x}')">${x}</button>`).join('')}</div>
      </div></div>`;
    this.scopeConnect(); this.loadMeasurements();
  },
  scopeSet(k, v) {
    const tg = state.scopeTrig;
    if (k === 'tb') state.scopeTb = parseFloat(v);
    else if (k === 'vdiv') state.scopeVdiv = parseFloat(v);
    else if (k === 'run') state.scopeRun = !!+v;
    else if (k === 'coupling') tg.coupling = v;
    else if (k === 'trigLevel') tg.level = parseFloat(v) || 0;
    else if (k === 'trigEdge') tg.edge = v;
    else if (k === 'trigMode') { tg.mode = v; if (v === 'single') state.scopeRun = true; }
    rerenderView('scope');
  },
  scopeConnect() {
    if (state.scopeES) { state.scopeES.close(); state.scopeES = null; }
    if (state.scopeRun === false) { this.scopeDraw(null); return; }
    const tg = state.scopeTrig || { level: 0, edge: 'rising', mode: 'auto', coupling: 'dc' };
    const url = `/api/instr/scope/stream?timebase=${state.scopeTb || 5e-4}&samples=500&trig_level=${tg.level}&trig_edge=${tg.edge}&coupling=${tg.coupling}`;
    const es = new EventSource(url); state.scopeES = es;
    es.onmessage = e => {
      const cv = el('scopeCanvas'); if (!cv) { es.close(); state.scopeES = null; return; }
      let fr; try { fr = JSON.parse(e.data); } catch { return; }
      if (tg.mode === 'normal' && !fr.trig) return;       // wait for a trigger
      this.scopeDraw(fr);
      if (tg.mode === 'single' && fr.trig) { es.close(); state.scopeES = null; state.scopeRun = false; rerenderView('scope'); }
    };
  },
  scopeDraw(frame) {
    const cv = el('scopeCanvas'); if (!cv) return; const wrap = cv.parentElement; const dpr = devicePixelRatio || 1;
    const W = wrap.clientWidth, H = wrap.clientHeight; if (!W || !H) return;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px';
    if (frame) state.scopeLastFrame = frame;
    const x = cv.getContext('2d'); x.scale(dpr, dpr); x.clearRect(0, 0, W, H);
    const cols = 10, rows = 8;
    x.strokeStyle = 'rgba(110,230,170,.13)'; x.lineWidth = 1;
    for (let i = 0; i <= cols; i++) { const px = i / cols * W; x.beginPath(); x.moveTo(px, 0); x.lineTo(px, H); x.stroke(); }
    for (let i = 0; i <= rows; i++) { const py = i / rows * H; x.beginPath(); x.moveTo(0, py); x.lineTo(W, py); x.stroke(); }
    x.strokeStyle = 'rgba(110,230,170,.3)'; x.beginPath(); x.moveTo(0, H / 2); x.lineTo(W, H / 2); x.moveTo(W / 2, 0); x.lineTo(W / 2, H); x.stroke();
    const vdiv = state.scopeVdiv || 0.5, divH = H / rows;
    // trigger level line + marker
    const tg = state.scopeTrig;
    if (tg && frame) { const ty = H / 2 - (frame.trig_level != null ? frame.trig_level : tg.level) / vdiv * divH;
      if (ty > 2 && ty < H - 2) { x.strokeStyle = 'rgba(245,213,52,.7)'; x.setLineDash([5, 4]); x.lineWidth = 1; x.beginPath(); x.moveTo(0, ty); x.lineTo(W, ty); x.stroke(); x.setLineDash([]);
        x.fillStyle = 'rgba(245,213,52,.9)'; x.beginPath(); x.moveTo(W - 1, ty); x.lineTo(W - 9, ty - 5); x.lineTo(W - 9, ty + 5); x.fill(); } }
    if (!frame || !frame.ch1) return;
    const n = frame.ch1.length;
    x.strokeStyle = '#34f5a0'; x.lineWidth = 2; x.shadowColor = '#34f5a0'; x.shadowBlur = 9; x.beginPath();
    for (let i = 0; i < n; i++) { const px = i / (n - 1) * W; const py = H / 2 - frame.ch1[i] / vdiv * divH; i ? x.lineTo(px, py) : x.moveTo(px, py); }
    x.stroke(); x.shadowBlur = 0;
    const rd = el('scopeRead'); if (rd) rd.textContent = `${(frame.span * 1000).toFixed(2)} ms · ${vdiv} V/div · trig ${frame.trig ? 'OK' : '...'}`;
  },
  async viewSiggen(c) {
    if (!state.siggen) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.siggenLoad(); return; }
    const s = state.siggen, waves = ['sine', 'square', 'triangle', 'sawtooth', 'dc'];
    this.instrEnsure('siggen');
    c.innerHTML = `<div class="instr siggen">
      <div class="instr-head">${svg('siggen')} Signal Generator ${this.instrSourceBar()}</div>
      <div class="scope-screen sg-prev"><canvas id="sgPrev"></canvas></div>
      <div class="sg-waves">${waves.map(w => `<button class="${w === s.waveform ? 'primary' : ''}" onclick="ui.siggenSet({waveform:'${w}'})">${w}</button>`).join('')}</div>
      <div class="sg-row"><label>Frequency<div class="sg-in"><input id="sgFreq" type="number" value="${s.freq_hz}" onchange="ui.siggenSet({freq_hz:+this.value})"><span>Hz</span></div></label>
        <label>Amplitude<div class="sg-in"><input type="number" step="0.1" value="${s.amp_vpp}" onchange="ui.siggenSet({amp_vpp:+this.value})"><span>Vpp</span></div></label></div>
      <div class="sg-row"><label>Offset<div class="sg-in"><input type="number" step="0.1" value="${s.offset_v}" onchange="ui.siggenSet({offset_v:+this.value})"><span>V</span></div></label>
        <label>Duty<div class="sg-in"><input type="number" step="0.05" min="0.05" max="0.95" value="${s.duty}" onchange="ui.siggenSet({duty:+this.value})" ${s.waveform === 'square' ? '' : 'disabled'}><span></span></div></label></div>
      <button class="${s.enabled ? 'danger' : 'primary'}" style="width:100%;margin-top:10px" onclick="ui.siggenSet({enabled:${s.enabled ? 'false' : 'true'}})">${s.enabled ? 'Output ON — click to disable' : 'Output OFF — click to enable'}</button>
      <div class="muted" style="font-size:11px;margin-top:6px">Open the <b>Oscilloscope</b> to see this signal render live.</div></div>`;
    this.siggenPreview();
  },
  async siggenLoad() { try { state.siggen = await api.get('/api/instr/siggen'); } catch { state.siggen = { waveform: 'sine', freq_hz: 1000, amp_vpp: 2, offset_v: 0, duty: 0.5, enabled: true }; } rerenderView('siggen'); },
  async siggenSet(patch) { try { state.siggen = await api.send('/api/instr/siggen', 'POST', patch); rerenderView('siggen'); } catch (e) { alert(e.message); } },
  siggenPreview() {
    const cv = el('sgPrev'); if (!cv || !state.siggen) return; const wrap = cv.parentElement; const dpr = devicePixelRatio || 1;
    const W = wrap.clientWidth, H = wrap.clientHeight; if (!W || !H) return;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px';
    const x = cv.getContext('2d'); x.scale(dpr, dpr); x.clearRect(0, 0, W, H);
    x.strokeStyle = 'rgba(110,230,170,.18)'; x.beginPath(); x.moveTo(0, H / 2); x.lineTo(W, H / 2); x.stroke();
    const s = state.siggen, cycles = 3, scale = Math.max(1, s.amp_vpp / 2 + Math.abs(s.offset_v) + 0.4);
    x.strokeStyle = '#34d399'; x.lineWidth = 2; x.shadowColor = '#34d399'; x.shadowBlur = 7; x.beginPath();
    for (let i = 0; i <= W; i++) { const frac = (i / W * cycles) % 1; let v;
      if (s.waveform === 'sine') v = Math.sin(2 * Math.PI * frac); else if (s.waveform === 'square') v = frac < s.duty ? 1 : -1; else if (s.waveform === 'triangle') v = frac < 0.5 ? 4 * frac - 1 : 3 - 4 * frac; else if (s.waveform === 'sawtooth') v = 2 * frac - 1; else v = 0;
      const vv = s.enabled ? (s.offset_v + (s.amp_vpp / 2) * v) : 0; const py = H / 2 - vv / scale * (H / 2 - 8);
      i ? x.lineTo(i, py) : x.moveTo(i, py); }
    x.stroke(); x.shadowBlur = 0;
  },
  // shared instrument source (Simulated <-> real USB device)
  instrSourceBar() {
    const s = state.instrStatus || { mock: true };
    return `<span class="instr-source"><span class="src-badge ${s.mock ? '' : 'live'}">${s.mock ? 'simulated' : 'LIVE'}</span>
      <select id="instrPort" title="Measurement source" onchange="ui.instrConnect(this.value)">
        <option value="">Simulated bench</option>
        ${(state.instrPorts || []).map(p => `<option value="${esc(p.device)}" ${state.instrPort === p.device ? 'selected' : ''}>${esc(p.device)}${p.desc ? ' · ' + esc(p.desc) : ''}</option>`).join('')}
      </select><button class="iconbtn" title="Rescan USB ports" onclick="ui.instrPorts()">${svg('reset')}</button></span>`;
  },
  async instrEnsure(view) {
    if (state.instrPorts !== undefined) return;
    state.instrPorts = [];
    try { state.instrPorts = (await api.get('/api/instr/ports')).ports || []; } catch {}
    try { state.instrStatus = await api.get('/api/instr/status'); } catch {}
    rerenderView(view);
  },
  async instrConnect(port) {
    try { state.instrStatus = await api.send('/api/instr/connect', 'POST', { port: port || '' }); state.instrPort = port || '';
      aiToast.show(port ? ('Connected to ' + port) : 'Simulated bench'); aiToast.hide(1500);
      ['dmm', 'scope', 'siggen'].forEach(v => rerenderView(v));
    } catch (e) { alert(e.message); }
  },
  async instrPorts() { state.instrPorts = undefined; await this.instrEnsure('scope'); ['dmm', 'siggen'].forEach(v => rerenderView(v)); },
  // record DMM readings / scope captures into the selected project (for audit + wiki)
  measPanel(kind) {
    if (!state.current) return `<div class="muted" style="font-size:11px;margin-top:10px">Select a project on the left to record ${kind === 'dmm' ? 'readings' : 'captures'} into its wiki.</div>`;
    const rows = (state.measurements || []).filter(m => m.kind === kind).slice(0, 6);
    const recBtn = kind === 'dmm'
      ? `<button class="primary" onclick="ui.recordDmm()">${svg('record')} Record reading → ${esc(state.current.label || 'project')}</button>` : '';
    return `<div class="instr-rec">${recBtn}<span class="muted" style="font-size:11px">Saved to <b>${esc(state.current.label || 'project')}</b></span></div>
      <div class="meas-list">${rows.map(m => `<div class="meas-row">${kind === 'scope' ? svg('scope') : ''}<b>${esc(m.label || m.mode)}</b>${m.value != null ? ` <span class="meas-v">${esc(String(m.value))} ${esc(m.unit || '')}</span>` : ''}<span class="muted" style="font-size:10.5px">${esc((m.created_at || '').slice(11, 19))}</span><button class="iconbtn" title="Delete" onclick="ui.deleteMeas(${m.id})">${svg('trash')}</button></div>`).join('') || '<span class="muted" style="font-size:11px">No recordings yet.</span>'}</div>`;
  },
  async loadMeasurements() {
    if (!state.current || state.measurements !== null) return;
    state.measurements = [];
    try { state.measurements = await api.get(`/api/vehicles/${state.current.id}/measurements`); } catch {}
    ['dmm', 'scope'].forEach(v => rerenderView(v));
  },
  async recordDmm() {
    if (!state.current) { alert('Select a project first.'); return; }
    const r = state.dmmLast; if (!r) { alert('No reading yet.'); return; }
    const label = prompt('Label this reading (e.g. "battery rest voltage", "R12 across pins"):', r.mode);
    if (label == null) return;
    try { const m = await api.send(`/api/vehicles/${state.current.id}/measurement`, 'POST', { kind: 'dmm', label, mode: r.mode, value: r.value, unit: r.unit });
      state.measurements = [m, ...(state.measurements || [])]; rerenderView('dmm'); aiToast.done('Reading recorded'); }
    catch (e) { alert(e.message); }
  },
  async captureScope() {
    if (!state.current) { alert('Select a project first.'); return; }
    const cv = el('scopeCanvas'); if (!cv) return;
    const label = prompt('Label this capture (e.g. "injector 1 drive", "5V ref ripple"):', 'scope capture');
    if (label == null) return;
    const fr = state.scopeLastFrame;
    try { const m = await api.send(`/api/vehicles/${state.current.id}/measurement`, 'POST', { kind: 'scope', label, mode: 'CH1', data: fr ? { dt: fr.dt, span: fr.span, ch1: fr.ch1 } : null, image: cv.toDataURL('image/png') });
      state.measurements = [m, ...(state.measurements || [])]; rerenderView('scope'); aiToast.done('Capture saved to project'); }
    catch (e) { alert(e.message); }
  },
  async deleteMeas(id) {
    try { await api.send('/api/measurement/' + id, 'DELETE'); state.measurements = (state.measurements || []).filter(m => m.id !== id); ['dmm', 'scope'].forEach(v => rerenderView(v)); } catch (e) { alert(e.message); }
  },

  // ---------- guided repair triage ----------
  viewTriage(c) {
    // Render messages INLINE (not via getElementById afterward) so moving/redocking tabs —
    // which rebuilds the tree detached before attaching — never loses the transcript.
    const msgs = state.triageMsgs;
    const body = msgs == null
      ? '<div class="empty"><span class="spinner"></span></div>'
      : (msgs.map(m => `<div class="msg ${m.role}"><div class="md">${md(m.content)}</div></div>`).join('')
         || '<div class="empty">Start a guided triage — describe the symptom or attach a board photo.</div>');
    c.innerHTML = `<div class="chat"><div class="chips">
        <span class="chip" onclick="ui.fillTriage('The symptom is: ')">Describe symptom</span>
        <span class="chip" onclick="ui.attachTriagePhoto()">${svg('upload')} Attach photo</span>
        <span class="chip" onclick="ui.phoneModal()">${svg('phone')} Pair phone</span>
        <span class="chip" onclick="ui.askTriage('Analyze the attached PCB photo: identify the components and what to check on each, and which tool to use.')">Analyze PCB</span>
        <span class="chip" onclick="ui.askTriage('Which serial/diagnostic protocols does this module use, and which OBD-II pins are relevant?')">Protocols / OBD-II</span>
        <span class="chip" onclick="ui.triageReport()">Generate report</span></div>
      <div class="messages" id="tMsgs">${body}</div>
      <div id="tAttach" class="muted" style="font-size:11.5px;min-height:16px"></div>
      <div class="chat-input"><textarea id="tIn" placeholder="Describe what you see / measured; ask for the next step…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();ui.sendTriage();}"></textarea>
        <button class="iconbtn" title="Attach photo" onclick="ui.attachTriagePhoto()">${svg('upload')}</button><button class="primary" onclick="ui.sendTriage()">Send</button></div>
      <div class="muted" style="margin-top:5px;font-size:11px">Guided diagnosis using this project's pinout + accumulated knowledge. Attach photos of the board, scope, or meter.</div></div>`;
    if (msgs == null) this.loadTriage();
    else { const b = c.querySelector('#tMsgs'); if (b) b.scrollTop = b.scrollHeight; }
    if (state.triageImage) { const a = c.querySelector('#tAttach'); if (a) a.textContent = 'photo attached — sends with your next message'; }
  },
  async loadTriage() { try { state.triageMsgs = await api.get(`/api/vehicles/${state.current.id}/triage/messages`); } catch { state.triageMsgs = []; } rerenderView('triage'); },
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
    // Keep the photo in the message content so it survives tab moves; the server re-embeds it
    // as a saved-attachment URL on reload. Strip image markdown from history sent to the model.
    const userContent = q + (img ? `\n\n![photo](${img})` : '');
    box.insertAdjacentHTML('beforeend', `<div class="msg user"><div class="md">${md(userContent)}</div></div>`);
    const aId = 't' + Date.now(); box.insertAdjacentHTML('beforeend', `<div class="msg assistant" id="${aId}"><div class="thinking"><span class="spinner"></span> thinking…</div><div class="md cursor-blink" id="${aId}-md"></div></div>`); box.scrollTop = box.scrollHeight;
    const history = (state.triageMsgs || []).slice(-8).map(m => ({ role: m.role, content: m.content.replace(/!\[[^\]]*\]\([^)]*\)/g, '[photo]') }));
    state.triageMsgs = [...(state.triageMsgs || []), { role: 'user', content: userContent }]; let full = '';
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
    if (state.pcbComponents == null) {  // not loaded yet — fetch the saved analysis
      c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadPcb(); return;
    }
    if (!state.pcbComponents.length || !state.pcbImage) {
      c.innerHTML = `<div id="pcbDz" class="dropzone">${svg('chip')}<div style="margin-top:8px"><strong>Drop a PCB photo</strong> (the ECU/module board), or click.</div><div class="muted" style="margin-top:4px">CANOPY boxes the components it recognizes and tells you what to check on each.</div></div>
        <div class="row" style="margin-top:10px;justify-content:center"><button onclick="ui.phoneModal()">${svg('phone')} Pair phone to snap a photo</button></div>`;
      const dz = c.querySelector('#pcbDz'); if (dz) { dz.onclick = () => this.pcbPick();
        ['dragover', 'dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.toggle('drag', ev === 'dragover'); if (ev === 'drop' && e.dataTransfer.files[0]) this.pcbUpload(e.dataTransfer.files[0]); })); }
      return;
    }
    const comps = state.pcbComponents; const edit = !!state.pcbEditMode;
    const nm = p => esc(p.user_label || p.label);
    const sel = state.pcbSel != null ? comps[state.pcbSel] : null;
    const handles = ['nw', 'ne', 'sw', 'se'].map(h => `<span class="handle ${h}"></span>`).join('');
    const boxes = comps.map((p, i) => { const [x0, y0, x1, y1] = p.box; const on = i === state.pcbSel;
      return `<div class="pcb-box ${on ? 'sel' : 'dim'}${edit ? ' editing' : ''}" data-idx="${i}" style="left:${x0 * 100}%;top:${y0 * 100}%;width:${(x1 - x0) * 100}%;height:${(y1 - y0) * 100}%" onclick="ui.selectPcb(${i})">${(on || edit) ? `<span class="lbl">${nm(p)}</span>` : ''}${edit ? handles + `<span class="pcb-del" title="Delete box" onpointerdown="event.stopPropagation()" onclick="event.stopPropagation();ui.pcbDeleteComponent(${p.id})">${svg('close')}</span>` : ''}</div>`; }).join('');
    const z = state.pcbZoom || 1;
    const photos = state.pcbPhotos || [];
    const strip = photos.length > 1 ? `<div class="pcb-photos">${photos.map((ph, i) => `<div class="pcb-thumb ${ph.id === state.pcbPhotoId ? 'sel' : ''}" title="${esc(ph.note || 'board photo')} — ${ph.count} parts" onclick="ui.pcbSelectPhoto(${ph.id})"><img src="/api/attachment/${ph.id}/image" loading="lazy"><span class="pt-n">${photos.length - i}</span></div>`).join('')}</div>` : '';
    let detail;
    if (!sel) detail = `<div class="pcb-detail muted" style="font-size:12px">Select a component to see its function, what to check, correct the AI, and send it to Triage.${edit ? ' In edit mode you can drag/resize boxes or add a new one.' : ''}</div>`;
    else if (state.pcbEdit === sel.id) detail = `<div class="pcb-detail"><div class="muted" style="font-size:11px;margin-bottom:4px">Correct the AI — your record for diagnosis &amp; replacement</div>
        <input id="pcEdLabel" placeholder="Component name" value="${esc(sel.user_label || sel.label)}">
        <input id="pcEdPart" placeholder="Part number / spec (e.g. TJA1050, 28F400)" value="${esc(sel.part || '')}" style="margin-top:6px">
        <textarea id="pcEdNote" placeholder="Spec, correction, or observation for the record…" style="margin-top:6px;min-height:54px">${esc(sel.user_note || '')}</textarea>
        <div class="row" style="margin-top:6px"><button class="primary" onclick="ui.pcbSaveEdit(${sel.id})">Save</button><button onclick="ui.pcbEditToggle(null)">Cancel</button><button class="danger" style="margin-left:auto" onclick="ui.pcbDeleteComponent(${sel.id})">${svg('trash')} Delete</button></div></div>`;
    else detail = `<div class="pcb-detail"><div style="display:flex;align-items:center;gap:8px"><b style="font-size:14px">${nm(sel)}</b>${sel.user_label ? '<span class="tagchip" title="corrected by tech">edited</span>' : ''}${sel.part ? `<span class="tagchip">${esc(sel.part)}</span>` : ''}${sel.confidence ? `<span style="margin-left:auto;color:var(--muted);font-size:11px">conf ${Math.round(sel.confidence * 100)}%</span>` : ''}</div>
        <div style="margin:6px 0;font-size:13px">${esc(sel.function)}</div><div class="warn" style="color:var(--cyan)">Check: ${esc(sel.check)}</div>
        ${sel.user_note ? `<div style="margin-top:6px;font-size:12.5px"><b>Note:</b> ${esc(sel.user_note)}</div>` : ''}
        <div class="row" style="margin-top:8px"><button onclick="ui.pcbEditToggle(${sel.id})">${svg('edit')} Edit / correct</button><button class="primary" style="flex:1" onclick="ui.pcbToTriage(${state.pcbSel})">${svg('triage')} Send to Triage</button></div></div>`;
    c.innerHTML = `<div class="pcb-col">
      <div class="row" style="margin-bottom:8px"><button onclick="ui.pcbPick()">${svg('upload')} New photo</button><button onclick="ui.phoneModal()">${svg('phone')} Pair phone</button>
        <button class="${edit ? 'primary' : ''}" onclick="ui.pcbToggleEditMode()">${svg('edit')} ${edit ? 'Done editing' : 'Edit boxes'}</button>
        ${edit ? `<button onclick="ui.pcbAddBox()">${svg('plus')} Add box</button>` : ''}
        <button onclick="ui.exportPcb()">${svg('chip')} Save PNG</button>
        <div class="zoomctl"><button class="iconbtn" onclick="ui.pcbZoom(-1)">${svg('zout')}</button><span id="pcbZlbl">${Math.round(z * 100)}%</span><button class="iconbtn" onclick="ui.pcbZoom(1)">${svg('zin')}</button><button class="iconbtn" title="Fit height" onclick="ui.pcbZoom(0)">${svg('reset')}</button></div></div>
      ${strip}
      <div class="pcb-layout">
        <div class="pcb-stage"><div class="pcb-wrap" id="pcbWrap" style="height:${z * 100}%"><img src="${state.pcbImage}" alt="PCB"><div style="position:absolute;inset:0">${boxes}</div></div></div>
        <div class="pcb-side">
          <div class="muted" style="font-size:11px;margin-bottom:6px">${comps.length} component${comps.length === 1 ? '' : 's'}${edit ? ' — drag a box to move, corners to resize' : ' — click one to highlight it'}</div>
          <div class="pcb-list">${comps.map((p, i) => `<div class="pcb-item ${i === state.pcbSel ? 'sel' : ''}" onclick="ui.selectPcb(${i})"><div class="pi-top"><span class="pi-label">${nm(p)}${p.user_label ? ' ·' : ''}</span>${p.confidence ? `<span class="pi-conf">${Math.round(p.confidence * 100)}%</span>` : ''}</div><div class="pi-detail">${esc(p.check)}</div></div>`).join('') || '<div class="muted" style="font-size:12px">No components yet — Add box, or analyze a new photo.</div>'}</div>
          ${detail}
        </div>
      </div></div>`;
    if (edit) this.pcbBindEdit();
  },
  async loadPcb() {
    try { const r = await api.get(`/api/vehicles/${state.current.id}/pcb-components`);
      state.pcbPhotos = r.photos || [];
      if (r.attachment_id) { state.pcbPhotoId = r.attachment_id; state.pcbComponents = r.components || [];
        if (!state.pcbImage) state.pcbImage = `/api/attachment/${r.attachment_id}/image`;
      } else state.pcbComponents = [];
    } catch { state.pcbComponents = []; state.pcbPhotos = []; }
    rerenderView('pcb');
  },
  async pcbSelectPhoto(attId) {
    if (attId === state.pcbPhotoId) return;
    state.pcbPhotoId = attId; state.pcbImage = `/api/attachment/${attId}/image`; state.pcbSel = null; state.pcbEdit = null;
    try { const r = await api.get(`/api/vehicles/${state.current.id}/pcb-components?attachment_id=${attId}`); state.pcbComponents = r.components || []; if (r.photos) state.pcbPhotos = r.photos; }
    catch { state.pcbComponents = []; }
    rerenderView('pcb');
  },
  pcbToggleEditMode() { state.pcbEditMode = !state.pcbEditMode; state.pcbEdit = null; rerenderView('pcb'); },
  pcbBindEdit() {
    const wrap = el('pcbWrap'); if (!wrap) return;
    wrap.querySelectorAll('.pcb-box.editing').forEach(boxEl => {
      const comp = state.pcbComponents[+boxEl.dataset.idx]; if (!comp) return;
      const startDrag = (e, mode) => { e.preventDefault(); e.stopPropagation();
        const rect = wrap.getBoundingClientRect(); const sx = e.clientX, sy = e.clientY; const sb = comp.box.slice();
        const cl = v => Math.max(0, Math.min(1, v));
        const move = ev => { const dx = (ev.clientX - sx) / rect.width, dy = (ev.clientY - sy) / rect.height;
          let [x0, y0, x1, y1] = sb;
          if (mode === 'move') { x0 += dx; x1 += dx; y0 += dy; y1 += dy; }
          else { if (mode.includes('w')) x0 += dx; if (mode.includes('e')) x1 += dx; if (mode.includes('n')) y0 += dy; if (mode.includes('s')) y1 += dy; }
          comp.box = [cl(Math.min(x0, x1)), cl(Math.min(y0, y1)), cl(Math.max(x0, x1)), cl(Math.max(y0, y1))];
          boxEl.style.left = comp.box[0] * 100 + '%'; boxEl.style.top = comp.box[1] * 100 + '%';
          boxEl.style.width = (comp.box[2] - comp.box[0]) * 100 + '%'; boxEl.style.height = (comp.box[3] - comp.box[1]) * 100 + '%';
          state.pcbDragged = true; };
        const up = () => { document.removeEventListener('pointermove', move); document.removeEventListener('pointerup', up);
          if (state.pcbDragged) api.send(`/api/pcb-component/${comp.id}`, 'PATCH', { box: comp.box }).catch(() => {}); };
        document.addEventListener('pointermove', move); document.addEventListener('pointerup', up);
      };
      boxEl.onpointerdown = e => { if (!e.target.classList.contains('handle')) startDrag(e, 'move'); };
      boxEl.querySelectorAll('.handle').forEach(h => { const mode = ['nw', 'ne', 'sw', 'se'].find(x => h.classList.contains(x)); h.onpointerdown = e => startDrag(e, mode); });
    });
  },
  async pcbAddBox() {
    const label = (prompt('New component — what is it? (name)') || '').trim(); if (!label) return;
    const part = (prompt('Part number / marking (optional)') || '').trim();
    aiToast.show('Identifying component…', true);
    try { const comp = await api.send(`/api/vehicles/${state.current.id}/pcb-component`, 'POST',
        { attachment_id: state.pcbPhotoId, label, part, box: [0.42, 0.42, 0.58, 0.58], identify: true });
      state.pcbComponents.push(comp); state.pcbSel = state.pcbComponents.length - 1; state.pcbEditMode = true;
      const ph = (state.pcbPhotos || []).find(p => p.id === state.pcbPhotoId); if (ph) ph.count++;
      aiToast.done('Added — drag it onto the part'); rerenderView('pcb');
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  async pcbDeleteComponent(id) {
    if (!confirm('Delete this component box?')) return;
    try { await api.send(`/api/pcb-component/${id}`, 'DELETE');
      state.pcbComponents = state.pcbComponents.filter(c => c.id !== id); state.pcbSel = null; state.pcbEdit = null;
      const ph = (state.pcbPhotos || []).find(p => p.id === state.pcbPhotoId); if (ph && ph.count > 0) ph.count--;
      rerenderView('pcb'); aiToast.done('Deleted');
    } catch (e) { alert(e.message); }
  },
  pcbEditToggle(id) { state.pcbEdit = id; rerenderView('pcb'); },
  async pcbSaveEdit(id) {
    const body = { user_label: el('pcEdLabel').value.trim(), part: el('pcEdPart').value.trim(), user_note: el('pcEdNote').value.trim() };
    try { const upd = await api.send(`/api/pcb-component/${id}`, 'PATCH', body);
      const i = state.pcbComponents.findIndex(c => c.id === id); if (i >= 0) state.pcbComponents[i] = upd;
      state.pcbEdit = null; rerenderView('pcb'); aiToast.done('Correction saved');
    } catch (e) { alert(e.message); }
  },
  async exportPcb() {
    if (!state.pcbImage) return; aiToast.show('Rendering annotated image…');
    try {
      const img = new Image(); img.src = state.pcbImage; await img.decode();
      const cv = document.createElement('canvas'); cv.width = img.naturalWidth; cv.height = img.naturalHeight;
      const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0);
      const lw = Math.max(2, cv.width / 450); const fs = Math.max(13, cv.width / 75); ctx.font = `bold ${fs}px sans-serif`; ctx.textBaseline = 'bottom';
      (state.pcbComponents || []).forEach((p, i) => { const [x0, y0, x1, y1] = p.box; const x = x0 * cv.width, y = y0 * cv.height, w = (x1 - x0) * cv.width, h = (y1 - y0) * cv.height;
        const on = i === state.pcbSel; ctx.lineWidth = on ? lw * 1.6 : lw; ctx.strokeStyle = on ? '#ef4444' : 'rgba(239,68,68,.9)';
        ctx.strokeRect(x, y, w, h); const nm = p.user_label || p.label; const tw = ctx.measureText(nm).width; ctx.fillStyle = '#ef4444'; ctx.fillRect(x, y - fs - 4, tw + 10, fs + 4); ctx.fillStyle = '#fff'; ctx.fillText(nm, x + 5, y - 2); });
      const a = document.createElement('a'); a.href = cv.toDataURL('image/png'); a.download = `${(state.current.label || 'pcb').replace(/[^\w.-]/g, '_')}_annotated.png`; a.click();
      aiToast.done('Saved annotated PNG');
    } catch (e) { aiToast.done('Error'); alert(e.message); }
  },
  pcbPick() { if (!state.pcbFileInput) { const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*'; inp.onchange = e => { if (e.target.files[0]) this.pcbUpload(e.target.files[0]); }; state.pcbFileInput = inp; } state.pcbFileInput.value = ''; state.pcbFileInput.click(); },
  async pcbUpload(file) {
    const r = new FileReader(); r.onload = async () => { state.pcbImage = r.result; state.pcbSel = null; state.pcbEdit = null; state.pcbEditMode = false;
      await this.busy(null, 'analyzing board…', async () => { aiToast.show('Analyzing PCB…');
        const res = await api.send(`/api/vehicles/${state.current.id}/pcb`, 'POST', { image: r.result });
        state.pcbComponents = res.components || []; state.pcbPhotoId = res.attachment_id;
        try { state.pcbPhotos = await api.get(`/api/vehicles/${state.current.id}/pcb-photos`); } catch {}
        rerenderView('pcb'); aiToast.done(`${state.pcbComponents.length} components`); });
    }; r.readAsDataURL(file);
  },
  async lightbox(src) {
    const m = document.createElement('div'); m.className = 'modal lightbox';
    const att = (src.match(/\/api\/attachment\/(\d+)\/image/) || [])[1];
    const sw = c => `<span class="lb-sw" style="background:${c}" onclick="anno.setColor('${c}')" data-c="${c}"></span>`;
    m.innerHTML = `<div class="lb-tools">
        <button class="tool active" data-tool="pen" onclick="anno.setTool('pen',this)">${svg('edit')} Draw</button>
        <button class="tool" data-tool="arrow" onclick="anno.setTool('arrow',this)">${svg('arrow')} Arrow</button>
        <button class="tool" data-tool="box" onclick="anno.setTool('box',this)">${svg('chip')} Box</button>
        <span style="margin:0 4px">${sw('#ef4444')}${sw('#f59e0b')}${sw('#0f9d6b')}${sw('#0e8aa6')}${sw('#ffffff')}</span>
        <button onclick="anno.undo()">Undo</button><button onclick="anno.clear()">Clear</button>
        <button class="primary" style="margin-left:auto" onclick="anno.save()">${svg('record')} Save annotated</button></div>
      <div class="lb-img"><div class="lb-canvaswrap"><img id="lbImg" src="${src}" alt=""><canvas id="lbCanvas"></canvas></div></div>
      <div class="lb-cap"><input id="lbCap" placeholder="Add a caption / annotation for the wiki…">
        <button class="primary" id="lbSaveCap" onclick="ui.saveCaption(${att || 'null'})">Save caption</button></div>
      <div class="m-foot"><span class="m-status" id="lbStatus"></span><button onclick="closeModal()">Close</button></div>`;
    showModal(m);
    const img = el('lbImg'); const done = () => anno.init(el('lbCanvas'), img);
    if (img.complete) done(); else img.onload = done;
    if (att) { try { const a = await api.get(`/api/attachment/${att}`); const i = el('lbCap'); if (i) i.value = a.note || ''; } catch {} }
  },
  async saveCaption(att) {
    const i = el('lbCap'); if (!i) return; const btn = el('lbSaveCap');
    if (att == null) { alert('Save the annotated image first (creates a record to caption).'); return; }
    if (btn) btn.textContent = 'Saving…';
    try { await api.send(`/api/attachment/${att}`, 'PATCH', { note: i.value.trim() }); if (btn) btn.textContent = 'Saved'; aiToast.done('Caption saved'); rerenderView('annotations'); }
    catch (e) { if (btn) btn.textContent = 'Save caption'; alert(e.message); }
  },

  // ---------- annotated photos gallery (markup that flows into the wiki) ----------
  viewAnnotations(c) {
    c.innerHTML = `<div class="row" style="margin-bottom:10px;align-items:baseline">
        <h3 class="sec" style="margin:0">Annotated photos</h3>
        <span class="muted" style="font-size:11px">Open any image (diagram or board), click to expand, mark it with <b>Draw / Arrow / Box</b>, add a caption and <b>Save annotated</b> — they collect here and flow into the Wiki.</span></div>
      <div id="annoGal" class="anno-gal"><div class="empty"><span class="spinner"></span></div></div>`;
    this.loadAnnotations();
  },
  async loadAnnotations() {
    const gal = el('annoGal'); if (!gal || !state.current) return;
    let list = [];
    try { list = await api.get(`/api/vehicles/${state.current.id}/attachments`); } catch { list = []; }
    const annos = (list || []).filter(a => a.kind === 'annotation');
    if (!annos.length) { gal.innerHTML = '<div class="empty">No annotated photos yet. Open a diagram or board image, click to expand, then use <b>Draw / Arrow / Box</b> and <b>Save annotated</b>.</div>'; return; }
    gal.innerHTML = annos.map(a => `<div class="anno-card">
        <img src="/api/attachment/${a.id}/image" loading="lazy" title="Click to view / re-annotate" onclick="ui.lightbox('/api/attachment/${a.id}/image')">
        <div class="anno-cap"><input id="annoCap-${a.id}" value="${esc(a.note || '')}" placeholder="Add a caption for the wiki…" onkeydown="if(event.key==='Enter')ui.annoCaption(${a.id})" onblur="ui.annoCaption(${a.id}, true)"></div>
        <div class="anno-act"><button class="ghost" onclick="ui.lightbox('/api/attachment/${a.id}/image')">${svg('edit')} View</button><button class="ghost danger" onclick="ui.annoDelete(${a.id})">${svg('trash')} Delete</button></div>
      </div>`).join('');
  },
  async annoCaption(id, quiet) {
    const i = el('annoCap-' + id); if (!i) return;
    try { await api.send(`/api/attachment/${id}`, 'PATCH', { note: i.value.trim() }); if (!quiet) aiToast.done('Caption saved'); }
    catch (e) { if (!quiet) alert(e.message); }
  },
  async annoDelete(id) {
    if (!confirm('Delete this annotated photo? It will also disappear from the wiki.')) return;
    try { await api.send(`/api/attachment/${id}`, 'DELETE'); this.loadAnnotations(); }
    catch (e) { alert(e.message); }
  },
  selectPcb(i) { if (state.pcbDragged) { state.pcbDragged = false; return; }  // ignore click after a box drag
    state.pcbSel = state.pcbSel === i ? null : i; rerenderView('pcb'); },
  pcbZoom(dir) { state.pcbZoom = dir === 0 ? 1 : Math.max(0.5, Math.min(5, (state.pcbZoom || 1) + dir * 0.25));
    if (state.current) savePcbZoom(state.current.id, state.pcbZoom);
    const w = document.querySelector('.pcb-wrap'); if (w) w.style.height = (state.pcbZoom * 100) + '%';
    const l = el('pcbZlbl'); if (l) l.textContent = Math.round(state.pcbZoom * 100) + '%'; },
  pcbToTriage(i) { state.triageImage = state.pcbImage; ensureView('triage'); const sel = i != null ? state.pcbComponents[i] : null;
    const txt = sel ? `About the ${sel.user_label || sel.label} on this board: ` : 'Here is the ECU board photo. The symptom is: ';
    const inp = el('tIn'); if (inp) { inp.value = txt; inp.focus(); } const a = el('tAttach'); if (a) a.textContent = 'board photo attached — sends with your next message'; },

  // ---------- project wiki (compiled, shareable) ----------
  viewWiki(c) {
    if (state.wikiMd == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadWiki(); return; }
    c.innerHTML = `<div class="wiki-col">
      <div class="row" style="margin-bottom:10px"><button onclick="ui.loadWiki(true)">${svg('reset')} Refresh</button><button onclick="ui.wikiCopy()">${svg('record')} Copy Markdown</button><button onclick="ui.wikiPrint()">Print / PDF</button>
        <span class="muted" style="margin-left:auto;align-self:center;font-size:11px">Compiled from this project's pinout, components, annotations &amp; notes</span></div>
      <div class="wiki-doc md" id="wikiDoc">${md(state.wikiMd)}</div></div>`;
  },
  async loadWiki(force) { if (force) { state.wikiMd = null; rerenderView('wiki'); }
    try { const r = await api.get(`/api/vehicles/${state.current.id}/wiki`); state.wikiMd = r.markdown || '_Nothing compiled yet._'; }
    catch { state.wikiMd = '_Could not load the wiki._'; } rerenderView('wiki'); },
  wikiCopy() { if (state.wikiMd) { navigator.clipboard?.writeText(state.wikiMd); aiToast.show('Wiki Markdown copied'); aiToast.hide(1200); } },
  wikiPrint() { if (!state.wikiMd) return; const w = window.open('', '_blank'); if (!w) return;
    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(state.current.label || 'CANOPY wiki')}</title>
      <style>body{font-family:system-ui,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;line-height:1.55;color:#111}img{max-width:100%;border:1px solid #ddd;border-radius:6px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px 8px;font-size:13px;text-align:left}h1,h2{border-bottom:1px solid #eee;padding-bottom:4px}code{background:#f3f3f3;padding:1px 4px;border-radius:4px}</style></head>
      <body>${md(state.wikiMd)}</body></html>`); w.document.close(); setTimeout(() => w.print(), 350); },

  // ---------- guided walkthrough (physics-first, step by step) ----------
  viewGuided(c) {
    if (state.guidedLog == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadGuided(); return; }
    const phases = GUIDED_PHASES; const cur = state.guidedPhase;
    const curIdx = phases.findIndex(p => p.key === cur);
    const ladder = phases.map((p, i) => `<div class="gp ${p.key === cur ? 'cur' : (i < curIdx ? 'done' : '')}" onclick="ui.guidedSetPhase('${p.key}')"><span class="gp-n">${i < curIdx ? svg('check') : i + 1}</span>${p.label}</div>`).join('<span class="gp-sep"></span>');
    const s = state.guidedStep;
    let stepCard;
    if (state.guidedThinking != null) stepCard = `<div class="g-step"><div class="g-title">${svg('guide')} Thinking through the next step…</div><div class="g-think" id="gThink">${esc(state.guidedThinking) || '<span class="spinner"></span>'}</div></div>`;
    else if (s && s.done) stepCard = `<div class="g-step done"><div class="g-title">${svg('check')} Diagnosis concluded</div>
        <div class="g-row"><b>Root cause:</b> ${esc(s.root_cause)}</div><div class="g-row"><b>Repair &amp; re-verify:</b> ${esc(s.repair)}</div>
        <div class="row" style="margin-top:8px"><button class="primary" onclick="ui.guidedCompile()">${svg('record')} Compile wiki</button></div></div>`;
    else if (s) stepCard = `<div class="g-step"><div class="g-title">${esc(s.title)} ${s.tool && s.tool !== 'none' ? `<span class="tagchip">${esc(s.tool)}</span>` : ''}</div>
        ${s.why ? `<div class="g-row"><b>Why:</b> ${esc(s.why)}</div>` : ''}
        ${s.how ? `<div class="g-row"><b>How:</b> ${esc(s.how)}</div>` : ''}
        ${s.expected ? `<div class="g-row"><b>Expected:</b> ${esc(s.expected)}</div>` : ''}
        ${s.record ? `<div class="g-row"><b>Record:</b> ${esc(s.record)}</div>` : ''}
        ${s.safety ? `<div class="g-row warn" style="color:var(--cyan)">${svg('warn')} ${esc(s.safety)}</div>` : ''}
        <input id="gResult" placeholder="What did you measure / observe?" style="margin-top:8px">
        <div class="row" style="margin-top:6px"><button class="ok" onclick="ui.guidedRecord('pass')">Pass</button><button class="danger" onclick="ui.guidedRecord('fail')">Fail / issue</button><button onclick="ui.guidedRecord('note')">Note</button><button class="ghost" style="margin-left:auto" onclick="ui.guidedNext()">Skip / re-suggest</button></div></div>`;
    else stepCard = `<div class="g-step muted"><div class="g-row">Ready when you are. Describe the customer symptom below, then get the first recommended step for <b>${esc(phases[curIdx] ? phases[curIdx].label : cur)}</b>.</div>
        <button class="primary" style="margin-top:8px" onclick="ui.guidedNext()">${svg('guide')} Suggest next step</button></div>`;
    c.innerHTML = `<div class="guided-col">
      <div class="g-ladder">${ladder}</div>
      <div class="g-sym"><textarea id="gSymptom" placeholder="Customer symptom (e.g. no-start, no comms, intermittent…)" oninput="state.guidedSymptom=this.value">${esc(state.guidedSymptom || '')}</textarea><button onclick="ui.guidedRecordSymptom()">Record symptom</button></div>
      ${stepCard}
      <div class="g-log"><div class="muted" style="font-size:11px;margin:10px 0 4px">Walkthrough log${state.guidedLog.length ? ` (${state.guidedLog.length})` : ''}</div>
        ${state.guidedLog.map(m => `<div class="g-le">${esc(m.content)}</div>`).join('') || '<div class="muted" style="font-size:12px">No steps yet.</div>'}</div>
    </div>`;
  },
  async loadGuided() {
    try { state.guidedLog = await api.get(`/api/vehicles/${state.current.id}/guided/log`); }
    catch { state.guidedLog = []; }
    if (!state.guidedSymptom) { const sy = (state.guidedLog || []).find(m => / Symptom /.test(m.content) || m.content.includes('[intake] Symptom')); if (sy) state.guidedSymptom = sy.content.split('→').pop().replace(/^[^:]*:/, '').trim(); }
    rerenderView('guided');
  },
  guidedSetPhase(key) { state.guidedPhase = key; state.guidedStep = null; rerenderView('guided'); },
  async guidedRecordSymptom() {
    const v = (el('gSymptom') || {}).value || ''; if (!v.trim()) return; state.guidedSymptom = v.trim();
    try { await api.send(`/api/vehicles/${state.current.id}/guided/step`, 'POST', { phase: 'intake', title: 'Symptom', result: v.trim(), status: 'note' });
      state.guidedLog = await api.get(`/api/vehicles/${state.current.id}/guided/log`); aiToast.done('Symptom recorded'); rerenderView('guided'); } catch (e) { alert(e.message); }
  },
  async guidedNext() {
    const symptom = state.guidedSymptom || (el('gSymptom') || {}).value || '';
    state.guidedStep = null; state.guidedThinking = '';  // show the live "thinking" panel
    aiToast.show('Thinking through the next step…', true); rerenderView('guided');
    await this.stream(`/api/vehicles/${state.current.id}/guided/next/stream`, { phase: state.guidedPhase, symptom },
      tok => { state.guidedThinking += tok; aiToast.append(tok);
        const e = el('gThink'); if (e) { e.textContent = state.guidedThinking.slice(-1600); e.scrollTop = e.scrollHeight; } },
      data => { state.guidedThinking = null;
        if (data && data.title !== undefined) { state.guidedStep = data; aiToast.done('Next step ready'); }
        else aiToast.done('Done');
        rerenderView('guided'); },
      e => { state.guidedThinking = null; aiToast.done('Error'); rerenderView('guided'); alert(e); });
  },
  async guidedRecord(status) {
    const s = state.guidedStep; if (!s) return; const result = (el('gResult') || {}).value || '';
    try { await api.send(`/api/vehicles/${state.current.id}/guided/step`, 'POST', { phase: state.guidedPhase, title: s.title, result, status });
      if (s.phase_complete && s.next_phase) state.guidedPhase = s.next_phase;
      state.guidedStep = null;
      state.guidedLog = await api.get(`/api/vehicles/${state.current.id}/guided/log`);
      rerenderView('guided'); this.guidedNext();  // auto-advance to the next recommendation
    } catch (e) { alert(e.message); }
  },
  guidedCompile() { ensureView('wiki'); this.loadWiki(true); },

  // ---------- CAB module profile (diagram/PCB -> confirmed test profile) ----------
  viewProfile(c) {
    if (state.profileYaml == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadProfile(); return; }
    const p = state.profileObj;
    const cards = (p && p.active_cards) || [];
    const harness = (p && p.harness_map) || [];
    const roleClass = r => ({ can_h: 'can', can_l: 'can', can_fd_h: 'can', can_fd_l: 'can', lin: 'can', power: 'pwr', ignition: 'pwr', accessory: 'pwr', ground: 'gnd' }[r] || '');
    c.innerHTML = `<div class="prof-col">
      <div class="row" style="margin-bottom:8px"><button onclick="ui.profileRegenerate()">${svg('reset')} Regenerate from diagram/PCB</button><button class="primary" onclick="ui.profileSave()">${svg('check')} Save / confirm</button><button onclick="ui.profileDownload()">${svg('upload')} Download .yaml</button>
        <span class="tagchip ${state.profileSaved ? 'ok' : ''}" style="margin-left:auto;align-self:center">${state.profileSaved ? 'confirmed' : 'draft — review before energizing'}</span></div>
      <div class="warn" style="color:var(--cyan);font-size:12px;margin-bottom:8px">${svg('warn')} CONFIRM BEFORE ENERGIZE: verify power, ground, and CAN pins against the wiring diagram before CAB closes any relay.</div>
      ${p ? `<div class="prof-summary"><b>${esc(p.identity.module_class)}</b> · ${esc([p.identity.year, p.identity.make, p.identity.model].filter(Boolean).join(' ') || p.identity.label)} · connector ${esc(p.connector || '—')}
        <div class="prof-cards">${cards.map(cd => `<span class="tagchip" title="CAB card">${esc(cd)}</span>`).join('')}</div></div>
        <div class="prof-legend">${[['power/ign', '#ef4444'], ['ground', '#555'], ['CAN', '#0e8aa6'], ['LIN', '#8b5cf6'], ['sensor', '#0f9d6b'], ['output', '#f59e0b'], ['switch', '#6366f1']].map(([t, col]) => `<span class="lg"><i style="background:${col}"></i>${t}</span>`).join('')}</div>
        <div class="prof-wire">${harnessSvg(harness, p.connector)}</div>
        <div class="prof-harness"><table><thead><tr><th>Pin</th><th>Signal</th><th>Role</th><th>Header</th><th>CAB card</th><th>Ch</th></tr></thead><tbody>
        ${harness.map(h => `<tr><td>${esc(h.module_pin)}</td><td>${esc(h.signal)}</td><td><span class="pin ${roleClass(h.role)}">${esc(h.role)}</span></td><td>${esc(h.header_pin)}</td><td>${esc(h.card || '—')}</td><td>${esc(h.channel)}</td></tr>`).join('')}
        </tbody></table></div>` : '<div class="warn">Could not parse the profile YAML — fix it below.</div>'}
      <div class="muted" style="font-size:11px;margin:10px 0 4px">Profile YAML (source of truth — edit and Save). This is the CAB test profile.</div>
      <textarea id="profYaml" class="prof-yaml" spellcheck="false">${esc(state.profileYaml)}</textarea>
    </div>`;
  },
  async loadProfile() {
    try { const r = await api.get(`/api/vehicles/${state.current.id}/profile`); state.profileYaml = r.yaml || ''; state.profileObj = r.profile; state.profileSaved = !!r.saved; }
    catch (e) { state.profileYaml = '# could not load profile\n'; state.profileObj = null; }
    rerenderView('profile');
  },
  async profileRegenerate() {
    if (state.profileSaved && !confirm('Regenerate a fresh draft from the current pinout/PCB? Your saved profile stays until you Save the new one.')) return;
    try { const r = await api.send(`/api/vehicles/${state.current.id}/profile/generate`, 'POST'); state.profileYaml = r.yaml; state.profileObj = r.profile; state.profileSaved = false; rerenderView('profile'); aiToast.done('Draft regenerated'); }
    catch (e) { alert(e.message); }
  },
  async profileSave() {
    const yaml = (el('profYaml') || {}).value || state.profileYaml;
    try { await api.send(`/api/vehicles/${state.current.id}/profile`, 'PUT', { yaml }); state.profileYaml = yaml; state.profileSaved = true;
      const r = await api.get(`/api/vehicles/${state.current.id}/profile`); state.profileObj = r.profile; rerenderView('profile'); aiToast.done('Profile confirmed'); }
    catch (e) { alert(e.message); }
  },
  profileDownload() {
    const yaml = (el('profYaml') || {}).value || state.profileYaml;
    const a = document.createElement('a'); a.href = 'data:text/yaml;charset=utf-8,' + encodeURIComponent(yaml);
    a.download = `${(state.current.label || 'module').replace(/[^\w.-]/g, '_')}.profile.yaml`; a.click();
  },

  // ---------- house knowledge base browser ----------
  viewKnowledge(c) {
    if (state.kbList == null) { c.innerHTML = '<div class="empty"><span class="spinner"></span></div>'; this.loadKb(); return; }
    c.innerHTML = `<div class="kb-col">
      <div class="kb-search">${svg('search')}<input id="kbQ" placeholder="Search the troubleshooting knowledge base…" value="${esc(state.kbQuery || '')}" oninput="ui.kbSearch(this.value)"><span class="muted" style="font-size:11px;white-space:nowrap">${state.kbList.length} articles · used automatically in triage</span></div>
      <div class="kb-wrap">
        <div class="kb-list" id="kbList">${this._kbItems()}</div>
        <div class="kb-doc md" id="kbDoc">${state.kbBody ? md(state.kbBody) : '<div class="muted" style="padding:14px">Select an article. This is the CANOPY house knowledge base — the AI already consults it during triage; here you can read and search it yourself.</div>'}</div>
      </div></div>`;
  },
  _kbItems() {
    const q = (state.kbQuery || '').toLowerCase();
    const items = (state.kbList || []).filter(a => !q || (a.title + ' ' + a.tags.join(' ')).toLowerCase().includes(q));
    return items.map(a => `<div class="kb-item ${a.slug === state.kbSlug ? 'sel' : ''}" onclick="ui.kbOpen('${a.slug}')"><div class="kb-title">${esc(a.title)}</div><div class="kb-tags">${a.tags.slice(0, 5).map(t => `<span class="tagchip">${esc(t)}</span>`).join('')}</div></div>`).join('') || '<div class="muted" style="padding:8px">No matches.</div>';
  },
  async loadKb() { try { state.kbList = await api.cget('/api/knowledge', 6e5); } catch { state.kbList = []; } rerenderView('knowledge'); },
  kbSearch(v) { state.kbQuery = v; const l = el('kbList'); if (l) l.innerHTML = this._kbItems(); },
  async kbOpen(slug) { state.kbSlug = slug;
    try { const a = await api.cget('/api/knowledge/' + slug, 6e5); state.kbBody = `# ${a.title}\n\n${a.body}`; }
    catch { state.kbBody = '_Could not load this article._'; }
    rerenderView('knowledge');
  },

  // ---------- phone pairing ----------
  phoneModal() {
    if (!state.current) return; const id = state.current.id;
    const m = document.createElement('div'); m.className = 'modal'; m.style.width = 'min(520px,94vw)';
    m.innerHTML = `<div class="m-head">${svg('phone')} Pair a phone</div><div class="m-sub">Scan with your phone's camera (same Wi-Fi / VPN). Photos appear below within ~1-2s — tap <b>PCB</b> to analyze the board or <b>Triage</b> to attach to the conversation.</div>
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
      } catch {} }, 1200);
  },
  async fetchDataUrl(url) { const r = await fetch(url); const b = await r.blob(); return new Promise(res => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(b); }); },
  async phoneUse(attId, target) {
    const dataUrl = await this.fetchDataUrl(`/api/attachment/${attId}/image`); closeModal();
    if (target === 'pcb') { state.pcbImage = dataUrl; state.pcbSel = null; state.pcbZoom = 1; ensureView('pcb'); aiToast.show('Analyzing PCB…');
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
  async saveVehicle() { const g = id => el(id) ? el(id).value : undefined; await api.send('/api/vehicles/' + state.current.id, 'PATCH', { label: g('f_label'), vin: g('f_vin'), year: g('f_year'), make: g('f_make'), model: g('f_model') }); state.current = await api.get('/api/vehicles/' + state.current.id); setTitle(); this.loadRecords(); rerenderView('record'); },
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
// click ripple on any button (CSS gives buttons position:relative; overflow:hidden)
document.addEventListener('pointerdown', e => {
  const btn = e.target.closest('button'); if (!btn || btn.disabled) return;
  const r = btn.getBoundingClientRect(), d = Math.max(r.width, r.height);
  const sp = document.createElement('span'); sp.className = 'ripple';
  sp.style.width = sp.style.height = d + 'px';
  sp.style.left = (e.clientX - r.left - d / 2) + 'px'; sp.style.top = (e.clientY - r.top - d / 2) + 'px';
  btn.appendChild(sp); setTimeout(() => sp.remove(), 580);
});
ui.init();
