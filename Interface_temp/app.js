// ============================================================
// NEXOR — Application Logic
// ============================================================

// ---- Clock ----
function updateClock() {
  const el = document.getElementById('clock');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleDateString('pt-BR') + ' ' +
      now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
setInterval(updateClock, 1000);
updateClock();

// ---- Toast ----
function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(40px)'; t.style.transition = '.3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

// ---- Modal ----
function openModal(title, body, footer = '') {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = body;
  document.getElementById('modal-footer').innerHTML = footer;
  document.getElementById('modal-overlay').classList.remove('hidden');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}
document.getElementById('modal-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// ---- Navigation ----
const ROUTES = { home: renderHome, operacao: renderOperacao, rolos: renderRolos,
  planejamento: renderPlanejamento, estoque: renderEstoque, cadastros: renderCadastros, configuracoes: renderConfiguracoes };

const PAGE_TITLES = { home: 'Home', operacao: 'Operação', rolos: 'Rolos', planejamento: 'Planejamento',
  estoque: 'Estoque', cadastros: 'Cadastros', configuracoes: 'Configurações' };

function navigate(route) {
  const fn = ROUTES[route];
  if (!fn) return;
  document.querySelectorAll('.nav-item').forEach(a => {
    a.classList.toggle('active', a.dataset.route === route);
  });
  document.getElementById('page-title').textContent = PAGE_TITLES[route] || route;
  document.getElementById('page-subtitle').textContent = '';
  document.getElementById('content').innerHTML = '';
  fn();
  window.location.hash = route;
}

document.querySelectorAll('.nav-item').forEach(a => {
  a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.route); });
});

// ---- Helpers ----
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function fmtDateShort(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function statusBadge(s) {
  const map = {
    ok:           ['badge-green',  'OK'],
    suspicious:   ['badge-yellow', 'Suspeito'],
    fechado:      ['badge-blue',   'Fechado'],
    aberto:       ['badge-yellow', 'Aberto'],
    em_andamento: ['badge-green',  'Em andamento'],
    aguardando:   ['badge-gray',   'Aguardando'],
    cancelado:    ['badge-red',    'Cancelado'],
    disponivel:   ['badge-green',  'Disponível'],
    reservado:    ['badge-yellow', 'Reservado'],
    exportado:    ['badge-purple', 'Exportado'],
    ativo:        ['badge-green',  'Ativo'],
    inativo:      ['badge-gray',   'Inativo'],
  };
  const [cls, label] = map[s] || ['badge-gray', s];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ============================================================
// HOME
// ============================================================
function renderHome() {
  const logs  = DB.get('logs', []);
  const rolls = DB.get('rolls', []);
  const avail = logs.filter(l => l.available);
  const open  = rolls.filter(r => r.status === 'aberto');
  const susp  = logs.filter(l => l.status === 'suspicious' && l.available);
  const last  = rolls.filter(r => r.status === 'fechado').sort((a,b) => new Date(b.date) - new Date(a.date))[0];
  const recent = rolls.slice(-5).reverse();

  const c = document.getElementById('content');
  c.innerHTML = `
    <div class="grid-4 gap-16" style="margin-bottom:24px">
      <div class="card">
        <div class="card-title">Logs Disponíveis</div>
        <div class="card-value color-accent">${avail.length}</div>
        <div class="card-sub">prontos para seleção</div>
      </div>
      <div class="card">
        <div class="card-title">Rolos em Aberto</div>
        <div class="card-value color-yellow">${open.length}</div>
        <div class="card-sub">aguardando fechamento</div>
      </div>
      <div class="card">
        <div class="card-title">Alertas / Suspeitas</div>
        <div class="card-value color-red">${susp.length}</div>
        <div class="card-sub">itens para revisar</div>
      </div>
      <div class="card">
        <div class="card-title">Último Rolo Fechado</div>
        <div class="card-value fw-600" style="font-size:16px;line-height:1.4">${last ? last.code : '—'}</div>
        <div class="card-sub">${last ? fmtDateShort(last.date) : 'nenhum'}</div>
      </div>
    </div>

    <div class="grid-2 gap-16" style="margin-bottom:24px">
      <div>
        <div class="section-header"><span class="section-title">Ações Rápidas</span></div>
        <div class="quick-actions">
          <a class="qa-item" onclick="navigate('operacao')">
            <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
            Novo Fechamento
          </a>
          <a class="qa-item" onclick="navigate('rolos')">
            <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            Consultar Rolos
          </a>
          <a class="qa-item" onclick="navigate('planejamento')">
            <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Planejamento
          </a>
          <a class="qa-item" onclick="navigate('estoque')">
            <svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            Estoque
          </a>
        </div>

        ${susp.length > 0 ? `
        <div class="mt-16">
          <div class="section-header"><span class="section-title">Alertas</span></div>
          <div class="flex flex-col gap-8">
            ${susp.map(l => `
              <div class="alert-item warn">
                <div>
                  <div class="fw-600">${l.filename}</div>
                  <div class="text-sm text-muted">Log suspeito — ${l.machine} • ${fmtDateShort(l.date)}</div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>` : ''}
      </div>

      <div>
        <div class="section-header"><span class="section-title">Atividade Recente</span></div>
        <div class="card" style="padding:0;overflow:hidden">
          <table>
            <thead><tr><th>Rolo</th><th>Tecido</th><th>Status</th><th>Data</th></tr></thead>
            <tbody>
              ${recent.length === 0 ? `<tr><td colspan="4"><div class="empty-state" style="padding:30px"><p>Nenhum rolo registrado</p></div></td></tr>` :
                recent.map(r => `
                  <tr style="cursor:pointer" onclick="navigate('rolos')">
                    <td class="fw-600">${r.code}</td>
                    <td>${r.fabric}</td>
                    <td>${statusBadge(r.status)}</td>
                    <td class="text-muted text-sm">${fmtDateShort(r.date)}</td>
                  </tr>
                `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// ============================================================
// OPERAÇÃO
// ============================================================
let selectedLogs = new Set();

function renderOperacao() {
  selectedLogs = new Set();
  const logs  = DB.get('logs', []).filter(l => l.available);

  const c = document.getElementById('content');
  c.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 300px;gap:20px;align-items:start">
      <div>
        <div class="section-header">
          <div>
            <div class="section-title">Inbox de Logs</div>
            <div class="section-sub">${logs.length} logs disponíveis para seleção</div>
          </div>
          <div class="flex gap-8">
            <button class="btn-secondary btn-sm" onclick="selectAllLogs()">Selecionar Todos</button>
            <button class="btn-secondary btn-sm" onclick="clearLogs()">Limpar</button>
          </div>
        </div>

        <div class="filter-bar">
          <div class="search-bar" style="flex:1">
            <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" placeholder="Buscar log..." oninput="filterLogList(this.value)" />
          </div>
          <select onchange="filterLogStatus(this.value)">
            <option value="">Todos os status</option>
            <option value="ok">OK</option>
            <option value="suspicious">Suspeito</option>
          </select>
        </div>

        <div class="log-list" id="log-list">
          ${logs.length === 0 ? `
            <div class="empty-state">
              <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <p>Nenhum log disponível</p>
            </div>` :
          logs.map(l => renderLogItem(l)).join('')}
        </div>
      </div>

      <div id="op-summary-panel">
        ${renderOpSummary()}
      </div>
    </div>
  `;
}

function renderLogItem(l) {
  const sel = selectedLogs.has(l.id);
  return `
    <div class="log-item ${sel ? 'selected' : ''} ${l.status === 'suspicious' ? 'suspicious' : ''}" 
         id="log-item-${l.id}" onclick="toggleLog(${l.id})">
      <input class="log-check" type="checkbox" ${sel ? 'checked' : ''} onclick="event.stopPropagation();toggleLog(${l.id})" />
      <div style="flex:1">
        <div class="flex items-center gap-8 log-name">
          ${l.filename}
          ${l.status === 'suspicious' ? '<span class="badge badge-yellow">Suspeito</span>' : ''}
        </div>
        <div class="log-details mt-8">
          <span>🧵 ${l.fabric}</span>
          <span>⚙️ ${l.machine}</span>
          <span>👤 ${l.operator}</span>
          <span>📏 ${l.meters}m</span>
          <span>📋 ${l.jobs} jobs</span>
          <span>📅 ${fmtDateShort(l.date)}</span>
        </div>
      </div>
    </div>`;
}

function toggleLog(id) {
  if (selectedLogs.has(id)) selectedLogs.delete(id);
  else selectedLogs.add(id);
  const logs = DB.get('logs', []).filter(l => l.available);
  const item = logs.find(l => l.id === id);
  const el = document.getElementById('log-item-' + id);
  if (el && item) { el.outerHTML = renderLogItem(item); }
  document.getElementById('op-summary-panel').innerHTML = renderOpSummary();
}

function selectAllLogs() {
  const logs = DB.get('logs', []).filter(l => l.available);
  logs.forEach(l => selectedLogs.add(l.id));
  renderOperacao();
}
function clearLogs() { selectedLogs.clear(); renderOperacao(); }

function filterLogList(q) {
  const logs = DB.get('logs', []).filter(l => l.available);
  const filtered = logs.filter(l => l.filename.toLowerCase().includes(q.toLowerCase()) || l.fabric.toLowerCase().includes(q.toLowerCase()));
  document.getElementById('log-list').innerHTML = filtered.map(l => renderLogItem(l)).join('') ||
    `<div class="empty-state"><p>Nenhum resultado encontrado</p></div>`;
}
function filterLogStatus(s) {
  const logs = DB.get('logs', []).filter(l => l.available && (!s || l.status === s));
  document.getElementById('log-list').innerHTML = logs.map(l => renderLogItem(l)).join('') ||
    `<div class="empty-state"><p>Nenhum resultado encontrado</p></div>`;
}

function renderOpSummary() {
  const logs = DB.get('logs', []).filter(l => selectedLogs.has(l.id));
  const totalM = logs.reduce((s,l) => s + l.meters, 0);
  const totalJ = logs.reduce((s,l) => s + l.jobs, 0);
  const susp   = logs.filter(l => l.status === 'suspicious').length;
  return `
    <div class="summary-panel">
      <div class="section-title" style="margin-bottom:16px">Resumo do Rolo</div>
      <div class="summary-row"><span class="label">Logs selecionados</span><span class="value color-accent">${logs.length}</span></div>
      <div class="summary-row"><span class="label">Total de metros</span><span class="value">${totalM}m</span></div>
      <div class="summary-row"><span class="label">Total de jobs</span><span class="value">${totalJ}</span></div>
      <div class="summary-row"><span class="label">Suspeitos</span><span class="value ${susp > 0 ? 'color-yellow' : 'color-green'}">${susp}</span></div>
      ${logs.length > 0 ? `
        <div class="summary-row"><span class="label">Máquina</span><span class="value">${logs[0].machine}</span></div>
        <div class="summary-row"><span class="label">Tecido</span><span class="value">${logs[0].fabric}</span></div>
        <div class="summary-row"><span class="label">Operador</span><span class="value">${logs[0].operator}</span></div>
      ` : ''}
      <hr class="divider" />
      <button class="btn-primary w-full" ${logs.length === 0 ? 'disabled style="opacity:.4;cursor:not-allowed"' : ''} onclick="proceedToClose()">
        Prosseguir para Fechamento →
      </button>
      ${susp > 0 ? `<div class="alert-item warn mt-16" style="margin-top:12px"><span>⚠️ ${susp} log(s) suspeito(s) selecionado(s)</span></div>` : ''}
    </div>`;
}

function proceedToClose() {
  if (selectedLogs.size === 0) return;
  renderFechamento([...selectedLogs]);
}

// ============================================================
// FECHAMENTO DO ROLO
// ============================================================
function renderFechamento(logIds) {
  document.getElementById('page-title').textContent = 'Fechamento do Rolo';
  document.querySelectorAll('.nav-item').forEach(a => a.classList.toggle('active', a.dataset.route === 'operacao'));

  const allLogs   = DB.get('logs', []);
  const selLogs   = allLogs.filter(l => logIds.includes(l.id));
  const totalM    = selLogs.reduce((s,l) => s + l.meters, 0);
  const totalJ    = selLogs.reduce((s,l) => s + l.jobs, 0);
  const susp      = selLogs.filter(l => l.status === 'suspicious').length;
  const rolls     = DB.get('rolls', []);
  const nextId    = (rolls.length ? Math.max(...rolls.map(r => r.id)) : 0) + 1;
  const code      = `ROLO-2025-${String(nextId).padStart(4,'0')}`;

  const c = document.getElementById('content');
  c.innerHTML = `
    <div style="max-width:860px;margin:0 auto">
      <div class="flex items-center gap-16 mb" style="margin-bottom:24px">
        <button class="btn-secondary" onclick="navigate('operacao')">← Voltar</button>
        <div>
          <div class="section-title">Revisão e Fechamento</div>
          <div class="section-sub">Confira o resumo antes de registrar o rolo</div>
        </div>
      </div>

      <div class="grid-2 gap-16" style="margin-bottom:20px">
        <div class="card">
          <div class="card-title">Código do Rolo</div>
          <div class="card-value color-accent" style="font-size:22px">${code}</div>
        </div>
        <div class="card">
          <div class="card-title">Total de Metros</div>
          <div class="card-value">${totalM}<span style="font-size:14px;font-weight:400;color:var(--text2)"> m</span></div>
        </div>
      </div>

      <div class="grid-4 gap-16" style="margin-bottom:24px">
        <div class="card card-sm"><div class="card-title">Logs</div><div class="fw-600" style="font-size:20px">${selLogs.length}</div></div>
        <div class="card card-sm"><div class="card-title">Jobs</div><div class="fw-600" style="font-size:20px">${totalJ}</div></div>
        <div class="card card-sm"><div class="card-title">Suspeitos</div><div class="fw-600 ${susp>0?'color-yellow':'color-green'}" style="font-size:20px">${susp}</div></div>
        <div class="card card-sm"><div class="card-title">Tecido</div><div class="fw-600" style="font-size:13px;margin-top:4px">${selLogs[0]?.fabric || '—'}</div></div>
      </div>

      <div class="card" style="margin-bottom:20px">
        <div class="section-title" style="margin-bottom:16px">Dados do Rolo</div>
        <div class="grid-2 gap-16">
          <div class="form-group">
            <label class="form-label">Máquina</label>
            <select id="fc-machine">
              ${DB.get('machines',[]).filter(m=>m.active).map(m=>`<option ${m.name===selLogs[0]?.machine?'selected':''}>${m.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Operador</label>
            <select id="fc-operator">
              ${DB.get('operators',[]).filter(o=>o.active).map(o=>`<option ${o.name===selLogs[0]?.operator?'selected':''}>${o.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Tecido</label>
            <select id="fc-fabric">
              ${DB.get('fabrics',[]).filter(f=>f.active).map(f=>`<option ${f.name===selLogs[0]?.fabric?'selected':''}>${f.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Observações</label>
            <input type="text" id="fc-obs" placeholder="Observações opcionais..." />
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px">
        <div class="section-title" style="margin-bottom:12px">Logs Incluídos</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Arquivo</th><th>Metros</th><th>Jobs</th><th>Status</th></tr></thead>
            <tbody>
              ${selLogs.map((l,i) => `
                <tr>
                  <td class="text-muted">${i+1}</td>
                  <td class="fw-600">${l.filename}</td>
                  <td>${l.meters}m</td>
                  <td>${l.jobs}</td>
                  <td>${statusBadge(l.status)}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>

      ${susp > 0 ? `<div class="alert-item warn" style="margin-bottom:20px">⚠️ Este rolo contém <strong>${susp}</strong> log(s) suspeito(s). Revise antes de fechar.</div>` : ''}

      <div class="flex gap-12" style="justify-content:flex-end">
        <button class="btn-secondary" onclick="navigate('operacao')">Cancelar</button>
        <button class="btn-primary" onclick="closeRoll(${JSON.stringify(logIds)}, '${code}')">
          ✓ Fechar Rolo e Exportar
        </button>
      </div>
    </div>
  `;
}

async function closeRoll(logIds, code) {
  const allLogs = DB.get('logs', []);
  const selLogs = allLogs.filter(l => logIds.includes(l.id));
  const rolls   = DB.get('rolls', []);
  const nextId  = (rolls.length ? Math.max(...rolls.map(r => r.id)) : 0) + 1;
  const totalM  = selLogs.reduce((s,l) => s + l.meters, 0);

  const machine  = document.getElementById('fc-machine')?.value || selLogs[0]?.machine;
  const operator = document.getElementById('fc-operator')?.value || selLogs[0]?.operator;
  const fabric   = document.getElementById('fc-fabric')?.value  || selLogs[0]?.fabric;
  const obs      = document.getElementById('fc-obs')?.value || '';

  if (SERVER_ONLINE) {
    const jobIds = selLogs.map(l => l.id).filter(id => id != null);
    const serverRoll = await apiCreateRoll(machine, fabric, obs, jobIds);
    if (serverRoll && !serverRoll.error) {
      await apiCloseRoll(serverRoll.id);
      await syncFromServer();
      selectedLogs.clear();
      toast(`Rolo <strong>${serverRoll.roll_name || code}</strong> fechado e salvo no banco!`, 'success');
      navigate('rolos');
      return;
    }
  }

  const roll = {
    id: nextId, code,
    date: new Date().toISOString(),
    fabric, machine, operator,
    logs: selLogs.length, meters: totalM,
    status: 'fechado',
    suspicious: selLogs.some(l => l.status === 'suspicious'),
    exported: true, obs
  };
  rolls.push(roll);
  DB.set('rolls', rolls);

  const updated = allLogs.map(l => logIds.includes(l.id) ? { ...l, available: false, rollId: nextId } : l);
  DB.set('logs', updated);
  selectedLogs.clear();

  toast(`Rolo <strong>${code}</strong> fechado com sucesso!`, 'success');
  navigate('rolos');
}

// ============================================================
// ROLOS
// ============================================================
function renderRolos() {
  const rolls = DB.get('rolls', []).slice().reverse();
  const c = document.getElementById('content');
  c.innerHTML = `
    <div class="section-header">
      <div>
        <div class="section-title">Consulta de Rolos</div>
        <div class="section-sub">${rolls.length} rolos registrados</div>
      </div>
    </div>

    <div class="filter-bar" style="margin-bottom:16px">
      <div class="search-bar" style="flex:1">
        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" placeholder="Buscar por código, tecido, operador..." oninput="filterRolls(this.value)" />
      </div>
      <select onchange="filterRollStatus(this.value)">
        <option value="">Todos os status</option>
        <option value="fechado">Fechado</option>
        <option value="aberto">Aberto</option>
      </select>
    </div>

    <div class="card" style="padding:0;overflow:hidden">
      <div class="table-wrap" id="rolls-table">
        ${renderRollsTable(rolls)}
      </div>
    </div>
  `;
}

function renderRollsTable(rolls) {
  if (rolls.length === 0) return `<div class="empty-state"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/></svg><p>Nenhum rolo encontrado</p></div>`;
  return `<table>
    <thead><tr><th>Código</th><th>Tecido</th><th>Máquina</th><th>Operador</th><th>Metros</th><th>Logs</th><th>Status</th><th>Data</th><th>Ações</th></tr></thead>
    <tbody>
      ${rolls.map(r => `
        <tr>
          <td class="fw-600 color-accent">${r.code}</td>
          <td>${r.fabric}</td>
          <td>${r.machine}</td>
          <td>${r.operator}</td>
          <td>${r.meters}m</td>
          <td>${r.logs}</td>
          <td>${statusBadge(r.status)} ${r.suspicious ? '<span class="badge badge-yellow">⚠</span>' : ''}</td>
          <td class="text-muted text-sm">${fmtDateShort(r.date)}</td>
          <td>
            <div class="tbl-actions">
              <button class="btn-ghost btn-sm" onclick="viewRoll(${r.id})">Detalhe</button>
              <button class="btn-ghost btn-sm" onclick="reexportRoll(${r.id})">Reexportar</button>
            </div>
          </td>
        </tr>`).join('')}
    </tbody>
  </table>`;
}

function filterRolls(q) {
  const rolls = DB.get('rolls', []).slice().reverse().filter(r =>
    r.code.toLowerCase().includes(q.toLowerCase()) ||
    r.fabric.toLowerCase().includes(q.toLowerCase()) ||
    r.operator.toLowerCase().includes(q.toLowerCase())
  );
  document.getElementById('rolls-table').innerHTML = renderRollsTable(rolls);
}
function filterRollStatus(s) {
  const rolls = DB.get('rolls', []).slice().reverse().filter(r => !s || r.status === s);
  document.getElementById('rolls-table').innerHTML = renderRollsTable(rolls);
}

function viewRoll(id) {
  const roll = DB.get('rolls', []).find(r => r.id === id);
  if (!roll) return;
  const logs = DB.get('logs', []).filter(l => l.rollId === id);
  openModal(`Detalhe — ${roll.code}`,
    `<div class="flex flex-col gap-16">
      <div class="grid-2 gap-12">
        <div><div class="form-label">Código</div><div class="fw-600 color-accent">${roll.code}</div></div>
        <div><div class="form-label">Status</div>${statusBadge(roll.status)}</div>
        <div><div class="form-label">Tecido</div><div>${roll.fabric}</div></div>
        <div><div class="form-label">Máquina</div><div>${roll.machine}</div></div>
        <div><div class="form-label">Operador</div><div>${roll.operator}</div></div>
        <div><div class="form-label">Data</div><div>${fmtDate(roll.date)}</div></div>
        <div><div class="form-label">Total Metros</div><div class="fw-600">${roll.meters}m</div></div>
        <div><div class="form-label">Total Logs</div><div>${roll.logs}</div></div>
      </div>
      ${roll.obs ? `<div><div class="form-label">Observações</div><div>${roll.obs}</div></div>` : ''}
      ${logs.length > 0 ? `
        <div>
          <div class="form-label" style="margin-bottom:8px">Logs do Rolo</div>
          <div class="table-wrap"><table>
            <thead><tr><th>Arquivo</th><th>Metros</th><th>Jobs</th><th>Status</th></tr></thead>
            <tbody>${logs.map(l => `<tr><td>${l.filename}</td><td>${l.meters}m</td><td>${l.jobs}</td><td>${statusBadge(l.status)}</td></tr>`).join('')}</tbody>
          </table></div>
        </div>` : ''}
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Fechar</button>
     <button class="btn-primary" onclick="reexportRoll(${id});closeModal()">Reexportar</button>`
  );
}

function reexportRoll(id) {
  const roll = DB.get('rolls', []).find(r => r.id === id);
  if (!roll) return;
  toast(`PDF e JPG do rolo <strong>${roll.code}</strong> reexportados com sucesso!`, 'success');
}

// ============================================================
// PLANEJAMENTO
// ============================================================
function renderPlanejamento() {
  const plan = DB.get('planning', []);
  const c = document.getElementById('content');
  c.innerHTML = `
    <div class="section-header">
      <div>
        <div class="section-title">Fila de Produção</div>
        <div class="section-sub">${plan.length} itens na fila</div>
      </div>
      <button class="btn-primary" onclick="openAddPlan()">+ Adicionar</button>
    </div>

    <div class="grid-3 gap-16" style="margin-bottom:24px">
      <div class="card card-sm">
        <div class="card-title">Em Andamento</div>
        <div class="fw-600" style="font-size:20px;color:var(--green)">${plan.filter(p=>p.status==='em_andamento').length}</div>
      </div>
      <div class="card card-sm">
        <div class="card-title">Aguardando</div>
        <div class="fw-600" style="font-size:20px;color:var(--yellow)">${plan.filter(p=>p.status==='aguardando').length}</div>
      </div>
      <div class="card card-sm">
        <div class="card-title">Metros Planejados</div>
        <div class="fw-600" style="font-size:20px">${plan.reduce((s,p)=>s+p.meters,0)}m</div>
      </div>
    </div>

    <div class="card" style="padding:0;overflow:hidden">
      <table>
        <thead><tr><th>#</th><th>Tecido</th><th>Máquina</th><th>Operador</th><th>Metros</th><th>Estimativa</th><th>Status</th><th>Ações</th></tr></thead>
        <tbody id="plan-tbody">
          ${plan.map(p => renderPlanRow(p)).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function renderPlanRow(p) {
  return `<tr>
    <td><div class="plan-order">${p.order}</div></td>
    <td class="fw-600">${p.fabric}</td>
    <td>${p.machine}</td>
    <td>${p.operator}</td>
    <td>${p.meters}m</td>
    <td>${p.estimated}</td>
    <td>${statusBadge(p.status)}</td>
    <td>
      <div class="tbl-actions">
        ${p.status === 'aguardando' ? `<button class="btn-ghost btn-sm" onclick="startPlan(${p.id})">Iniciar</button>` : ''}
        ${p.status === 'em_andamento' ? `<button class="btn-ghost btn-sm" onclick="completePlan(${p.id})">Concluir</button>` : ''}
        <button class="btn-ghost btn-sm" onclick="deletePlan(${p.id})">Remover</button>
      </div>
    </td>
  </tr>`;
}

function openAddPlan() {
  const fabrics  = DB.get('fabrics', []).filter(f => f.active);
  const machines = DB.get('machines', []).filter(m => m.active);
  const ops      = DB.get('operators', []).filter(o => o.active);
  openModal('Adicionar à Fila',
    `<div class="flex flex-col gap-16">
      <div class="form-group"><label class="form-label">Tecido</label>
        <select id="np-fabric">${fabrics.map(f=>`<option>${f.name}</option>`).join('')}</select></div>
      <div class="form-group"><label class="form-label">Máquina</label>
        <select id="np-machine">${machines.map(m=>`<option>${m.name}</option>`).join('')}</select></div>
      <div class="form-group"><label class="form-label">Operador</label>
        <select id="np-operator">${ops.map(o=>`<option>${o.name}</option>`).join('')}</select></div>
      <div class="form-group"><label class="form-label">Metros Planejados</label>
        <input type="number" id="np-meters" placeholder="Ex: 400" /></div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="addPlan()">Adicionar</button>`
  );
}

function addPlan() {
  const plan   = DB.get('planning', []);
  const fabric  = document.getElementById('np-fabric').value;
  const machine = document.getElementById('np-machine').value;
  const operator= document.getElementById('np-operator').value;
  const meters  = parseInt(document.getElementById('np-meters').value) || 300;
  const hrs = Math.round(meters / 120 * 10) / 10;
  const est = `${Math.floor(hrs)}h ${Math.round((hrs%1)*60)}m`;
  plan.push({ id: Date.now(), order: plan.length + 1, fabric, machine, operator, meters, estimated: est, status: 'aguardando' });
  DB.set('planning', plan);
  closeModal();
  toast('Item adicionado à fila!', 'success');
  renderPlanejamento();
}

function startPlan(id) {
  const plan = DB.get('planning', []).map(p => p.id === id ? { ...p, status: 'em_andamento' } : p);
  DB.set('planning', plan);
  toast('Produção iniciada!', 'success');
  renderPlanejamento();
}
function completePlan(id) {
  const plan = DB.get('planning', []).map(p => p.id === id ? { ...p, status: 'cancelado' } : p);
  DB.set('planning', plan);
  toast('Bloco concluído!', 'success');
  renderPlanejamento();
}
function deletePlan(id) {
  const plan = DB.get('planning', []).filter(p => p.id !== id).map((p,i) => ({ ...p, order: i+1 }));
  DB.set('planning', plan);
  renderPlanejamento();
}

// ============================================================
// ESTOQUE
// ============================================================
function renderEstoque() {
  const stock = DB.get('stock', []);
  const c = document.getElementById('content');
  c.innerHTML = `
    <div class="section-header">
      <div>
        <div class="section-title">Controle de Estoque</div>
        <div class="section-sub">Disponibilidade de tecidos e materiais</div>
      </div>
      <button class="btn-primary" onclick="openAddStock()">+ Registrar Entrada</button>
    </div>

    <div class="grid-4 gap-16" style="margin-bottom:24px">
      <div class="card card-sm">
        <div class="card-title">Tipos de Tecido</div>
        <div class="fw-600" style="font-size:20px">${stock.length}</div>
      </div>
      <div class="card card-sm">
        <div class="card-title">Total de Rolos</div>
        <div class="fw-600" style="font-size:20px">${stock.reduce((s,i)=>s+i.rolls,0)}</div>
      </div>
      <div class="card card-sm">
        <div class="card-title">Total de Metros</div>
        <div class="fw-600" style="font-size:20px">${stock.reduce((s,i)=>s+i.meters,0)}m</div>
      </div>
      <div class="card card-sm">
        <div class="card-title">Metros Reservados</div>
        <div class="fw-600 color-yellow" style="font-size:20px">${stock.reduce((s,i)=>s+i.reserved,0)}m</div>
      </div>
    </div>

    <div class="grid-2 gap-16">
      ${stock.map(s => {
        const pct = Math.min(100, Math.round(s.reserved / s.meters * 100));
        const avail = s.meters - s.reserved;
        return `
          <div class="stock-item">
            <div class="stock-fabric">${s.fabric}</div>
            <div class="stock-row"><span class="stock-label">Rolos em estoque</span><span class="fw-600">${s.rolls}</span></div>
            <div class="stock-row"><span class="stock-label">Total metros</span><span class="fw-600">${s.meters}m</span></div>
            <div class="stock-row"><span class="stock-label">Reservado</span><span class="fw-600 color-yellow">${s.reserved}m</span></div>
            <div class="stock-row"><span class="stock-label">Disponível</span><span class="fw-600 color-green">${avail}m</span></div>
            <div style="margin-top:10px">
              <div class="flex justify-between text-sm text-muted" style="margin-bottom:4px"><span>Ocupação</span><span>${pct}%</span></div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill ${pct>80?'red':pct>50?'yellow':'green'}" style="width:${pct}%"></div>
              </div>
            </div>
            <div class="flex gap-8 mt-16">
              <button class="btn-ghost btn-sm" onclick="stockEntry(${s.id})">+ Entrada</button>
              <button class="btn-ghost btn-sm" onclick="stockExit(${s.id})">- Saída</button>
            </div>
          </div>`;
      }).join('')}
    </div>
  `;
}

function openAddStock() {
  const fabrics = DB.get('fabrics', []).filter(f => f.active);
  openModal('Registrar Entrada',
    `<div class="flex flex-col gap-16">
      <div class="form-group"><label class="form-label">Tecido</label>
        <select id="se-fabric">${fabrics.map(f=>`<option>${f.name}</option>`).join('')}</select></div>
      <div class="form-group"><label class="form-label">Metros</label>
        <input type="number" id="se-meters" placeholder="Ex: 200" /></div>
      <div class="form-group"><label class="form-label">Rolos</label>
        <input type="number" id="se-rolls" placeholder="Ex: 2" /></div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="addStock()">Registrar</button>`
  );
}
function addStock() {
  const fabric = document.getElementById('se-fabric').value;
  const meters = parseInt(document.getElementById('se-meters').value) || 0;
  const rolls  = parseInt(document.getElementById('se-rolls').value) || 1;
  const stock  = DB.get('stock', []);
  const idx    = stock.findIndex(s => s.fabric === fabric);
  if (idx >= 0) { stock[idx].meters += meters; stock[idx].rolls += rolls; }
  else { stock.push({ id: Date.now(), fabric, rolls, meters, reserved: 0, unit: 'm' }); }
  DB.set('stock', stock);
  closeModal();
  toast('Entrada registrada!', 'success');
  renderEstoque();
}
function stockEntry(id) {
  openModal('Registrar Entrada',
    `<div class="form-group"><label class="form-label">Metros a adicionar</label>
      <input type="number" id="se2-meters" placeholder="Ex: 100" /></div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="doStockEntry(${id})">Confirmar</button>`);
}
function doStockEntry(id) {
  const m = parseInt(document.getElementById('se2-meters').value) || 0;
  const stock = DB.get('stock', []).map(s => s.id === id ? { ...s, meters: s.meters + m } : s);
  DB.set('stock', stock); closeModal(); toast('Entrada registrada!', 'success'); renderEstoque();
}
function stockExit(id) {
  openModal('Registrar Saída',
    `<div class="form-group"><label class="form-label">Metros a retirar</label>
      <input type="number" id="sx-meters" placeholder="Ex: 50" /></div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-danger" onclick="doStockExit(${id})">Confirmar Saída</button>`);
}
function doStockExit(id) {
  const m = parseInt(document.getElementById('sx-meters').value) || 0;
  const stock = DB.get('stock', []).map(s => s.id === id ? { ...s, meters: Math.max(0, s.meters - m) } : s);
  DB.set('stock', stock); closeModal(); toast('Saída registrada!', 'success'); renderEstoque();
}

// ============================================================
// CADASTROS
// ============================================================
let cadastroTab = 'operadores';

function renderCadastros() {
  const c = document.getElementById('content');
  c.innerHTML = `
    <div class="tabs">
      <div class="tab ${cadastroTab==='operadores'?'active':''}" onclick="setCadTab('operadores')">Operadores</div>
      <div class="tab ${cadastroTab==='maquinas'?'active':''}" onclick="setCadTab('maquinas')">Máquinas</div>
      <div class="tab ${cadastroTab==='tecidos'?'active':''}" onclick="setCadTab('tecidos')">Tecidos</div>
    </div>
    <div id="cad-content"></div>
  `;
  renderCadTab();
}

function setCadTab(tab) {
  cadastroTab = tab;
  document.querySelectorAll('.tabs .tab').forEach(t => t.classList.toggle('active', t.textContent.toLowerCase().replace('á','a').replace('ã','a') === tab));
  renderCadTab();
}

function renderCadTab() {
  const el = document.getElementById('cad-content');
  if (!el) return;
  if (cadastroTab === 'operadores') renderOperadores(el);
  else if (cadastroTab === 'maquinas') renderMaquinas(el);
  else renderTecidos(el);
}

function renderOperadores(el) {
  const ops = DB.get('operators', []);
  el.innerHTML = `
    <div class="section-header">
      <span class="section-title">Operadores (${ops.length})</span>
      <button class="btn-primary" onclick="openAddOperador()">+ Novo Operador</button>
    </div>
    <div class="card" style="padding:0;overflow:hidden">
      <table>
        <thead><tr><th>Nome</th><th>Código</th><th>Status</th><th>Ações</th></tr></thead>
        <tbody>
          ${ops.map(o => `<tr>
            <td class="fw-600">${o.name}</td>
            <td class="text-muted">${o.code}</td>
            <td>${statusBadge(o.active ? 'ativo' : 'inativo')}</td>
            <td><div class="tbl-actions">
              <button class="btn-ghost btn-sm" onclick="toggleOperador(${o.id})">${o.active ? 'Desativar' : 'Ativar'}</button>
              <button class="btn-ghost btn-sm" onclick="editOperador(${o.id})">Editar</button>
            </div></td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

function openAddOperador() {
  openModal('Novo Operador',
    `<div class="flex flex-col gap-12">
      <div class="form-group"><label class="form-label">Nome</label><input type="text" id="op-name" placeholder="Nome completo" /></div>
      <div class="form-group"><label class="form-label">Código</label><input type="text" id="op-code" placeholder="Ex: CM01" /></div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="addOperador()">Salvar</button>`);
}
function addOperador() {
  const name = document.getElementById('op-name').value.trim();
  const code = document.getElementById('op-code').value.trim();
  if (!name) return;
  const ops = DB.get('operators', []);
  ops.push({ id: Date.now(), name, code, active: true });
  DB.set('operators', ops); closeModal(); toast('Operador cadastrado!', 'success');
  renderCadastros();
}
function toggleOperador(id) {
  const ops = DB.get('operators', []).map(o => o.id === id ? { ...o, active: !o.active } : o);
  DB.set('operators', ops); renderCadastros();
}
function editOperador(id) {
  const op = DB.get('operators', []).find(o => o.id === id);
  if (!op) return;
  openModal('Editar Operador',
    `<div class="flex flex-col gap-12">
      <div class="form-group"><label class="form-label">Nome</label><input type="text" id="op-edit-name" value="${op.name}" /></div>
      <div class="form-group"><label class="form-label">Código</label><input type="text" id="op-edit-code" value="${op.code}" /></div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="saveOperador(${id})">Salvar</button>`);
}
function saveOperador(id) {
  const name = document.getElementById('op-edit-name').value.trim();
  const code = document.getElementById('op-edit-code').value.trim();
  const ops = DB.get('operators', []).map(o => o.id === id ? { ...o, name, code } : o);
  DB.set('operators', ops); closeModal(); toast('Salvo!', 'success'); renderCadastros();
}

function renderMaquinas(el) {
  const machines = DB.get('machines', []);
  el.innerHTML = `
    <div class="section-header">
      <span class="section-title">Máquinas (${machines.length})</span>
      <button class="btn-primary" onclick="openAddMaquina()">+ Nova Máquina</button>
    </div>
    <div class="card" style="padding:0;overflow:hidden">
      <table>
        <thead><tr><th>Nome</th><th>Código</th><th>Tipo</th><th>Status</th><th>Ações</th></tr></thead>
        <tbody>
          ${machines.map(m => `<tr>
            <td class="fw-600">${m.name}</td>
            <td class="text-muted">${m.code}</td>
            <td>${m.type}</td>
            <td>${statusBadge(m.active ? 'ativo' : 'inativo')}</td>
            <td><div class="tbl-actions">
              <button class="btn-ghost btn-sm" onclick="toggleMaquina(${m.id})">${m.active ? 'Desativar' : 'Ativar'}</button>
            </div></td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}
function openAddMaquina() {
  openModal('Nova Máquina',
    `<div class="flex flex-col gap-12">
      <div class="form-group"><label class="form-label">Nome</label><input type="text" id="mq-name" placeholder="Ex: Máquina E" /></div>
      <div class="form-group"><label class="form-label">Código</label><input type="text" id="mq-code" placeholder="Ex: MQ-E" /></div>
      <div class="form-group"><label class="form-label">Tipo</label>
        <select id="mq-type"><option>Tear</option><option>Acabamento</option><option>Inspeção</option><option>Revisão</option></select>
      </div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="addMaquina()">Salvar</button>`);
}
function addMaquina() {
  const name = document.getElementById('mq-name').value.trim();
  const code = document.getElementById('mq-code').value.trim();
  const type = document.getElementById('mq-type').value;
  if (!name) return;
  const ms = DB.get('machines', []);
  ms.push({ id: Date.now(), name, code, type, active: true });
  DB.set('machines', ms); closeModal(); toast('Máquina cadastrada!', 'success'); renderCadastros();
}
function toggleMaquina(id) {
  const ms = DB.get('machines', []).map(m => m.id === id ? { ...m, active: !m.active } : m);
  DB.set('machines', ms); renderCadastros();
}

function renderTecidos(el) {
  const fabrics = DB.get('fabrics', []);
  el.innerHTML = `
    <div class="section-header">
      <span class="section-title">Tecidos (${fabrics.length})</span>
      <button class="btn-primary" onclick="openAddTecido()">+ Novo Tecido</button>
    </div>
    <div class="card" style="padding:0;overflow:hidden">
      <table>
        <thead><tr><th>Nome</th><th>Código</th><th>Cor</th><th>Status</th><th>Ações</th></tr></thead>
        <tbody>
          ${fabrics.map(f => `<tr>
            <td class="fw-600">${f.name}</td>
            <td class="text-muted">${f.code}</td>
            <td>${f.color}</td>
            <td>${statusBadge(f.active ? 'ativo' : 'inativo')}</td>
            <td><div class="tbl-actions">
              <button class="btn-ghost btn-sm" onclick="toggleTecido(${f.id})">${f.active ? 'Desativar' : 'Ativar'}</button>
            </div></td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}
function openAddTecido() {
  openModal('Novo Tecido',
    `<div class="flex flex-col gap-12">
      <div class="form-group"><label class="form-label">Nome</label><input type="text" id="fab-name" placeholder="Ex: Voil 100g" /></div>
      <div class="form-group"><label class="form-label">Código</label><input type="text" id="fab-code" placeholder="Ex: VOI100" /></div>
      <div class="form-group"><label class="form-label">Cor Principal</label><input type="text" id="fab-color" placeholder="Ex: Branco" /></div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="addTecido()">Salvar</button>`);
}
function addTecido() {
  const name  = document.getElementById('fab-name').value.trim();
  const code  = document.getElementById('fab-code').value.trim();
  const color = document.getElementById('fab-color').value.trim();
  if (!name) return;
  const fs = DB.get('fabrics', []);
  fs.push({ id: Date.now(), name, code, color, active: true });
  DB.set('fabrics', fs); closeModal(); toast('Tecido cadastrado!', 'success'); renderCadastros();
}
function toggleTecido(id) {
  const fs = DB.get('fabrics', []).map(f => f.id === id ? { ...f, active: !f.active } : f);
  DB.set('fabrics', fs); renderCadastros();
}

// ============================================================
// CONFIGURAÇÕES
// ============================================================
function renderConfiguracoes() {
  const cfg = DB.get('config', {});
  const c = document.getElementById('content');
  c.innerHTML = `
    <div style="max-width:720px">
      <div class="section-header"><div class="section-title">Configurações do Sistema</div></div>

      <div class="card" style="margin-bottom:20px">
        <div class="fw-600 mb" style="margin-bottom:16px">Pastas e Caminhos</div>
        <div class="flex flex-col gap-16">
          <div class="form-group">
            <label class="form-label">Pasta de Logs</label>
            <input type="text" id="cfg-logfolder" value="${cfg.logFolder || ''}" placeholder="C:\\Producao\\Logs" />
          </div>
          <div class="form-group">
            <label class="form-label">Pasta de Exportação</label>
            <input type="text" id="cfg-exportfolder" value="${cfg.exportFolder || ''}" placeholder="C:\\Producao\\Exportados" />
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:20px">
        <div class="fw-600 mb" style="margin-bottom:16px">Importação Automática</div>
        <div class="flex flex-col gap-16">
          <div class="flex items-center gap-12">
            <input type="checkbox" id="cfg-autoimport" ${cfg.autoImport ? 'checked' : ''} style="width:auto;accent-color:var(--accent)" />
            <label class="form-label" for="cfg-autoimport" style="cursor:pointer">Ativar importação automática de logs</label>
          </div>
          <div class="form-group">
            <label class="form-label">Intervalo de verificação (minutos)</label>
            <input type="number" id="cfg-interval" value="${cfg.importInterval || 5}" style="max-width:120px" />
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:20px">
        <div class="fw-600 mb" style="margin-bottom:16px">Exportação</div>
        <div class="flex flex-col gap-12">
          <div class="flex items-center gap-12">
            <input type="checkbox" id="cfg-pdf" ${cfg.pdfExport ? 'checked' : ''} style="width:auto;accent-color:var(--accent)" />
            <label class="form-label" for="cfg-pdf" style="cursor:pointer">Exportar PDF ao fechar rolo</label>
          </div>
          <div class="flex items-center gap-12">
            <input type="checkbox" id="cfg-jpg" ${cfg.jpgExport ? 'checked' : ''} style="width:auto;accent-color:var(--accent)" />
            <label class="form-label" for="cfg-jpg" style="cursor:pointer">Exportar JPG (espelho) ao fechar rolo</label>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px">
        <div class="fw-600 mb" style="margin-bottom:16px">Padrões Operacionais</div>
        <div class="grid-2 gap-16">
          <div class="form-group">
            <label class="form-label">Máquina padrão</label>
            <select id="cfg-machine">
              ${DB.get('machines',[]).filter(m=>m.active).map(m=>`<option ${m.name===cfg.defaultMachine?'selected':''}>${m.name}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Operador padrão</label>
            <select id="cfg-operator">
              ${DB.get('operators',[]).filter(o=>o.active).map(o=>`<option ${o.name===cfg.defaultOperator?'selected':''}>${o.name}</option>`).join('')}
            </select>
          </div>
        </div>
      </div>

      <div class="flex gap-12">
        <button class="btn-primary" onclick="saveConfig()">Salvar Configurações</button>
        <button class="btn-secondary" onclick="resetData()">Resetar Dados de Demonstração</button>
      </div>

      ${SERVER_ONLINE ? `
      <hr class="divider" />
      <div class="card" style="margin-bottom:20px">
        <div class="fw-600 mb" style="margin-bottom:16px">Fontes de Logs <span class="badge badge-green" style="margin-left:8px">API conectada</span></div>
        ${(() => {
          const sources = DB.get('log_sources', []);
          return sources.length === 0
            ? `<div class="text-muted text-sm">Nenhuma fonte cadastrada.</div>`
            : sources.map(s => `<div class="flex items-center justify-between" style="padding:8px 0;border-bottom:1px solid var(--border)">
                <div><div class="fw-600">${s.name}</div><div class="text-muted text-sm">${s.path}</div></div>
                <span class="badge ${s.enabled ? 'badge-green' : 'badge-gray'}">${s.enabled ? 'Ativa' : 'Inativa'}</span>
              </div>`).join('');
        })()}
        <div class="flex gap-8 mt-16">
          <button class="btn-secondary" onclick="openAddSource()">+ Adicionar Fonte</button>
          <button class="btn-primary" onclick="runImport()">▶ Importar Agora</button>
        </div>
      </div>` : `
      <hr class="divider" />
      <div class="alert-item info" style="margin-top:0">
        ℹ️ Servidor offline. Inicie com <strong>python server.py</strong> na raiz do projeto Python para habilitar importação real.
      </div>`}
    </div>
  `;
}

function saveConfig() {
  DB.set('config', {
    logFolder:       document.getElementById('cfg-logfolder').value,
    exportFolder:    document.getElementById('cfg-exportfolder').value,
    autoImport:      document.getElementById('cfg-autoimport').checked,
    importInterval:  parseInt(document.getElementById('cfg-interval').value) || 5,
    pdfExport:       document.getElementById('cfg-pdf').checked,
    jpgExport:       document.getElementById('cfg-jpg').checked,
    defaultMachine:  document.getElementById('cfg-machine').value,
    defaultOperator: document.getElementById('cfg-operator').value,
  });
  toast('Configurações salvas!', 'success');
}

function resetData() {
  openModal('Resetar Dados',
    `<p style="color:var(--text2)">Isso apagará todos os dados e restaurará os dados de demonstração. Esta ação não pode ser desfeita.</p>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-danger" onclick="doResetData()">Confirmar Reset</button>`);
}
function doResetData() {
  localStorage.removeItem('nexor_seeded');
  Object.keys(localStorage).filter(k => k.startsWith('nexor_')).forEach(k => localStorage.removeItem(k));
  seedIfEmpty();
  closeModal();
  toast('Dados resetados com sucesso!', 'info');
  navigate('home');
}

// ============================================================
// SERVER ACTIONS (Importação / Fontes de Log)
// ============================================================
async function runImport() {
  toast('Importando logs...', 'info');
  const result = await apiRunImport();
  if (result && result.ok) {
    await syncFromServer();
    navigate('operacao');
    toast('Importação concluída! Logs atualizados.', 'success');
  } else {
    toast(`Erro na importação: ${result?.error || 'desconhecido'}`, 'error');
  }
}

function openAddSource() {
  openModal('Adicionar Fonte de Logs',
    `<div class="flex flex-col gap-12">
      <div class="form-group"><label class="form-label">Nome</label><input type="text" id="src-name" placeholder="Ex: Logs Produção" /></div>
      <div class="form-group"><label class="form-label">Caminho da pasta</label><input type="text" id="src-path" placeholder="C:\\Producao\\Logs" /></div>
      <div class="flex items-center gap-12">
        <input type="checkbox" id="src-recursive" checked style="width:auto;accent-color:var(--accent)" />
        <label class="form-label" for="src-recursive" style="cursor:pointer">Incluir subpastas (recursivo)</label>
      </div>
    </div>`,
    `<button class="btn-secondary" onclick="closeModal()">Cancelar</button>
     <button class="btn-primary" onclick="saveAddSource()">Adicionar</button>`
  );
}

async function saveAddSource() {
  const name      = document.getElementById('src-name').value.trim();
  const path      = document.getElementById('src-path').value.trim();
  const recursive = document.getElementById('src-recursive').checked;
  if (!name || !path) { toast('Preencha nome e caminho.', 'error'); return; }
  const result = await apiAddLogSource(name, path, recursive, null);
  if (result && !result.error) {
    await syncFromServer();
    closeModal();
    toast('Fonte adicionada!', 'success');
    renderConfiguracoes();
  } else {
    toast(`Erro: ${result?.error || 'desconhecido'}`, 'error');
  }
}

// ============================================================
// BOOT
// ============================================================
(async function boot() {
  const hash = window.location.hash.replace('#', '') || 'home';
  navigate(ROUTES[hash] ? hash : 'home');
  await apiCheck();
  if (SERVER_ONLINE) {
    const currentHash = window.location.hash.replace('#', '') || 'home';
    navigate(ROUTES[currentHash] ? currentHash : 'home');
  }
})();
