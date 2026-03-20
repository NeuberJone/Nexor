// ============================================================
// NEXOR — API Client
// Tenta conectar ao servidor Python em localhost:5000.
// Se offline, usa dados mock do localStorage.
// ============================================================

const API_BASE = "http://localhost:5000/api";
let SERVER_ONLINE = false;

async function apiCheck() {
  try {
    const r = await fetch(API_BASE + "/status", { signal: AbortSignal.timeout(1500) });
    if (r.ok) {
      SERVER_ONLINE = true;
      const data = await r.json();
      console.log("[Nexor API] Conectado ao servidor:", data.db);
      showServerBadge(true, data.db);
      await syncFromServer();
    }
  } catch {
    SERVER_ONLINE = false;
    console.log("[Nexor API] Servidor offline. Usando dados mock.");
    showServerBadge(false);
  }
}

function showServerBadge(online, dbPath) {
  const footer = document.querySelector(".sidebar-footer");
  if (!footer) return;
  let badge = document.getElementById("api-badge");
  if (!badge) {
    badge = document.createElement("div");
    badge.id = "api-badge";
    badge.style.cssText = "margin-top:8px;padding:5px 8px;border-radius:4px;font-size:11px;display:flex;align-items:center;gap:6px;cursor:pointer;";
    badge.title = online ? "API conectada — clique para sincronizar" : "API offline — usando dados mock";
    badge.onclick = online ? () => syncFromServer().then(() => { toast("Dados sincronizados!", "success"); }) : null;
    footer.appendChild(badge);
  }
  badge.style.background = online ? "var(--green-muted)" : "var(--bg4)";
  badge.style.color      = online ? "var(--green)" : "var(--text3)";
  badge.innerHTML = online
    ? `<span style="width:7px;height:7px;border-radius:50%;background:var(--green);flex-shrink:0"></span>API conectada`
    : `<span style="width:7px;height:7px;border-radius:50%;background:var(--text3);flex-shrink:0"></span>Modo offline`;
}

// ---------------------------------------------------------------------------
// Sync: popula o localStorage com dados reais do servidor
// ---------------------------------------------------------------------------
async function syncFromServer() {
  if (!SERVER_ONLINE) return;
  try {
    const [jobsRes, rollsRes, sourcesRes, metricsRes, suspectsRes, fabricsRes, machinesRes] = await Promise.allSettled([
      fetch(API_BASE + "/jobs?limit=1000").then(r => r.json()),
      fetch(API_BASE + "/rolls").then(r => r.json()),
      fetch(API_BASE + "/log-sources").then(r => r.json()),
      fetch(API_BASE + "/metrics").then(r => r.json()),
      fetch(API_BASE + "/suspects").then(r => r.json()),
      fetch(API_BASE + "/fabrics").then(r => r.json()),
      fetch(API_BASE + "/machines").then(r => r.json()),
    ]);

    if (jobsRes.status === "fulfilled" && Array.isArray(jobsRes.value)) {
      const jobs = jobsRes.value.map(j => ({
        id: j.id,
        filename: (j.source_path ? j.source_path.split(/[\\/]/).pop() : j.job_id) || j.job_id,
        date: j.start_time,
        fabric: j.fabric || "Desconhecido",
        machine: j.machine || "Desconhecido",
        operator: j.operator_name || j.operator_code || "—",
        meters: Math.round((j.effective_printed_length_m || j.planned_length_m || 0) * 1000) / 1000,
        meters_m: j.effective_printed_length_m || j.planned_length_m || 0,
        jobs: 1,
        status: j.suspicion_category ? "suspicious" : "ok",
        rollId: null,
        available: true,
        job_id: j.job_id,
        document: j.document,
        print_status: j.print_status,
        planned_length_m: j.planned_length_m,
        actual_printed_length_m: j.actual_printed_length_m,
        gap_before_m: j.gap_before_m,
        consumed_length_m: j.consumed_length_m,
        suspicion_category: j.suspicion_category,
        review_status: j.review_status,
        _raw: j,
      }));
      DB.set("logs", jobs);
    }

    if (rollsRes.status === "fulfilled" && Array.isArray(rollsRes.value)) {
      const rolls = rollsRes.value.map(r => ({
        id: r.id,
        code: r.roll_name,
        date: r.created_at || r.closed_at,
        fabric: r.fabric || "—",
        machine: r.machine || "—",
        operator: "—",
        logs: r.total_jobs || 0,
        meters: Math.round((r.total_effective_m || 0) * 100) / 100,
        status: (r.status || "").toLowerCase() === "closed" ? "fechado" : "aberto",
        suspicious: r.has_suspects || false,
        exported: (r.status || "").toLowerCase() === "closed",
        _id: r.id,
      }));
      DB.set("rolls", rolls);

      // Marca logs pertencentes a rolos fechados
      const logsNow = DB.get("logs", []);
      if (logsNow.length) DB.set("logs", logsNow);
    }

    if (metricsRes.status === "fulfilled" && !metricsRes.value.error) {
      DB.set("server_metrics", metricsRes.value);
    }

    if (suspectsRes.status === "fulfilled" && Array.isArray(suspectsRes.value)) {
      DB.set("suspects", suspectsRes.value);
    }

    if (fabricsRes.status === "fulfilled" && Array.isArray(fabricsRes.value)) {
      const existing = DB.get("fabrics", []);
      const serverFabrics = fabricsRes.value.map((f, i) => {
        const ex = existing.find(e => e.name === f.name);
        return ex || { id: i + 1, name: f.name, code: f.name.slice(0, 6).toUpperCase(), color: "—", active: true };
      });
      if (serverFabrics.length) DB.set("fabrics", serverFabrics);
    }

    if (machinesRes.status === "fulfilled" && Array.isArray(machinesRes.value)) {
      const machines = machinesRes.value.map((m, i) => ({
        id: i + 1, name: m.machine_id, code: m.computer_name, type: "Impressora", active: true
      }));
      if (machines.length) DB.set("machines", machines);
    }

    if (sourcesRes.status === "fulfilled" && Array.isArray(sourcesRes.value)) {
      DB.set("log_sources", sourcesRes.value);
      if (sourcesRes.value.length > 0) {
        const cfg = DB.get("config", {});
        cfg.logFolder = sourcesRes.value[0].path || cfg.logFolder;
        DB.set("config", cfg);
      }
    }

  } catch (e) {
    console.error("[Nexor API] Falha ao sincronizar:", e);
  }
}

// ---------------------------------------------------------------------------
// API calls usados pelo app.js
// ---------------------------------------------------------------------------

async function apiCreateRoll(machine, fabric, note, jobIds) {
  if (!SERVER_ONLINE) return null;
  try {
    const r = await fetch(API_BASE + "/rolls", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ machine, fabric, note, job_ids: jobIds }),
    });
    return await r.json();
  } catch { return null; }
}

async function apiCloseRoll(rollId) {
  if (!SERVER_ONLINE) return null;
  try {
    const r = await fetch(API_BASE + `/rolls/${rollId}/close`, { method: "POST" });
    return await r.json();
  } catch { return null; }
}

async function apiRunImport() {
  if (!SERVER_ONLINE) return { ok: false, error: "Servidor offline" };
  try {
    const r = await fetch(API_BASE + "/import", { method: "POST" });
    return await r.json();
  } catch (e) { return { ok: false, error: String(e) }; }
}

async function apiScanSuspects() {
  if (!SERVER_ONLINE) return null;
  try {
    const r = await fetch(API_BASE + "/suspects/scan", { method: "POST" });
    return await r.json();
  } catch { return null; }
}

async function apiReviewSuspect(jobId, status, note, reviewedBy) {
  if (!SERVER_ONLINE) return null;
  try {
    const r = await fetch(API_BASE + `/suspects/${jobId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, note, reviewed_by: reviewedBy }),
    });
    return await r.json();
  } catch { return null; }
}

async function apiAddLogSource(name, path, recursive, machineHint) {
  if (!SERVER_ONLINE) return null;
  try {
    const r = await fetch(API_BASE + "/log-sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, path, recursive, machine_hint: machineHint }),
    });
    return await r.json();
  } catch { return null; }
}
