// ============================================================
// NEXOR — Application Logic (Flask Version)
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
function navigate(route) {
  const routes = {
    'home': '/',
    'operacao': '/operacao',
    'rolos': '/rolos',
    'planejamento': '/planejamento',
    'estoque': '/estoque',
    'cadastros': '/cadastros',
    'configuracoes': '/configuracoes'
  };
  
  if (routes[route]) {
    window.location.href = routes[route];
  }
}

// ---- API Check ----
async function checkServerStatus() {
  try {
    const r = await fetch('/api/status', { signal: AbortSignal.timeout(1500) });
    if (r.ok) {
      const data = await r.json();
      document.getElementById('status-dot').className = 'status-dot online';
      document.getElementById('status-text').textContent = 'Sistema ativo';
      return true;
    }
  } catch {
    document.getElementById('status-dot').className = 'status-dot offline';
    document.getElementById('status-text').textContent = 'Sistema offline';
    return false;
  }
}

// ---- Helpers ----
function fmtDate(iso) {
  if (!iso) return '—';
  try {
    const dt = new Date(iso);
    return dt.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

function fmtDateShort(iso) {
  if (!iso) return '—';
  try {
    const dt = new Date(iso);
    return dt.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return iso;
  }
}

function statusBadge(s) {
  const map = {
    'ok': ['badge-green', 'OK'],
    'suspicious': ['badge-yellow', 'Suspeito'],
    'fechado': ['badge-blue', 'Fechado'],
    'aberto': ['badge-yellow', 'Aberto'],
    'em_andamento': ['badge-green', 'Em andamento'],
    'aguardando': ['badge-gray', 'Aguardando'],
    'cancelado': ['badge-red', 'Cancelado'],
    'disponivel': ['badge-green', 'Disponível'],
    'reservado': ['badge-yellow', 'Reservado'],
    'exportado': ['badge-purple', 'Exportado'],
    'ativo': ['badge-green', 'Ativo'],
    'inativo': ['badge-gray', 'Inativo'],
  };
  const [cls, label] = map[s] || ['badge-gray', s];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', function() {
  checkServerStatus();
  setInterval(checkServerStatus, 30000);
});
