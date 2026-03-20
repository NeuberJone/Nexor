// ============================================================
// NEXOR — Mock Data & Storage
// ============================================================

const DB = {
  get(key, def) {
    try {
      const v = localStorage.getItem('nexor_' + key);
      return v ? JSON.parse(v) : def;
    } catch { return def; }
  },
  set(key, val) {
    localStorage.setItem('nexor_' + key, JSON.stringify(val));
  }
};

// ---------- Seed data if empty ----------
function seedIfEmpty() {
  if (!DB.get('seeded', false)) {
    DB.set('operators', [
      { id: 1, name: 'Carlos Mendes',   code: 'CM01', active: true },
      { id: 2, name: 'Rosana Teixeira', code: 'RT02', active: true },
      { id: 3, name: 'Leandro Souza',   code: 'LS03', active: true },
      { id: 4, name: 'Patrícia Alves',  code: 'PA04', active: false },
    ]);
    DB.set('machines', [
      { id: 1, name: 'Máquina A',  code: 'MQ-A', type: 'Tear',    active: true },
      { id: 2, name: 'Máquina B',  code: 'MQ-B', type: 'Tear',    active: true },
      { id: 3, name: 'Máquina C',  code: 'MQ-C', type: 'Acabamento', active: true },
      { id: 4, name: 'Máquina D',  code: 'MQ-D', type: 'Inspeção', active: false },
    ]);
    DB.set('fabrics', [
      { id: 1, name: 'Oxford 300g',  code: 'OX300', color: 'Branco',  active: true },
      { id: 2, name: 'Malha PV',     code: 'MPV',   color: 'Preto',   active: true },
      { id: 3, name: 'Tricoline',    code: 'TRI',   color: 'Azul',    active: true },
      { id: 4, name: 'Moletom 330g', code: 'ML330', color: 'Cinza',   active: true },
    ]);

    const now = Date.now();
    const logs = [];
    const statuses = ['ok','ok','ok','suspicious','ok','ok','suspicious','ok'];
    const fabNames = ['Oxford 300g','Malha PV','Tricoline','Moletom 330g'];
    const mNames   = ['MQ-A','MQ-B','MQ-C','MQ-A'];
    const oNames   = ['Carlos Mendes','Rosana Teixeira','Leandro Souza'];
    for (let i = 1; i <= 12; i++) {
      const ts = now - (i * 3600000) - Math.random() * 1800000;
      logs.push({
        id: i,
        filename: `log_${String(i).padStart(3,'0')}_${new Date(ts).toISOString().split('T')[0].replace(/-/g,'')}.txt`,
        date: new Date(ts).toISOString(),
        fabric: fabNames[(i-1) % 4],
        machine: mNames[(i-1) % 4],
        operator: oNames[(i-1) % 3],
        meters: Math.round(80 + Math.random() * 120),
        jobs: Math.round(3 + Math.random() * 8),
        status: statuses[(i-1) % 8],
        rollId: i <= 8 ? Math.ceil(i / 3) : null,
        available: i > 8
      });
    }
    DB.set('logs', logs);

    const rolls = [];
    for (let r = 1; r <= 3; r++) {
      const rLogs = logs.filter(l => l.rollId === r);
      const totalM = rLogs.reduce((s, l) => s + l.meters, 0);
      rolls.push({
        id: r,
        code: `ROLO-2025-${String(r).padStart(4,'0')}`,
        date: new Date(now - r * 86400000 * 2).toISOString(),
        fabric: rLogs[0]?.fabric || 'Oxford 300g',
        machine: rLogs[0]?.machine || 'MQ-A',
        operator: rLogs[0]?.operator || 'Carlos Mendes',
        logs: rLogs.length,
        meters: totalM,
        status: r === 1 ? 'aberto' : 'fechado',
        suspicious: rLogs.some(l => l.status === 'suspicious'),
        exported: r !== 1,
      });
    }
    DB.set('rolls', rolls);

    DB.set('planning', [
      { id: 1, order: 1, fabric: 'Oxford 300g', machine: 'MQ-A', operator: 'Carlos Mendes', meters: 500, estimated: '4h 10m', status: 'em_andamento' },
      { id: 2, order: 2, fabric: 'Malha PV',    machine: 'MQ-B', operator: 'Rosana Teixeira', meters: 320, estimated: '2h 40m', status: 'aguardando' },
      { id: 3, order: 3, fabric: 'Tricoline',   machine: 'MQ-C', operator: 'Leandro Souza',   meters: 450, estimated: '3h 45m', status: 'aguardando' },
      { id: 4, order: 4, fabric: 'Moletom 330g',machine: 'MQ-A', operator: 'Carlos Mendes',   meters: 280, estimated: '2h 20m', status: 'aguardando' },
    ]);

    DB.set('stock', [
      { id: 1, fabric: 'Oxford 300g',  rolls: 14, meters: 3420, reserved: 500, unit: 'm' },
      { id: 2, fabric: 'Malha PV',     rolls: 8,  meters: 1980, reserved: 320, unit: 'm' },
      { id: 3, fabric: 'Tricoline',    rolls: 6,  meters: 1450, reserved: 450, unit: 'm' },
      { id: 4, fabric: 'Moletom 330g', rolls: 3,  meters: 840,  reserved: 280, unit: 'm' },
    ]);

    DB.set('config', {
      logFolder: 'C:\\Producao\\Logs',
      exportFolder: 'C:\\Producao\\Exportados',
      autoImport: true,
      importInterval: 5,
      pdfExport: true,
      jpgExport: true,
      defaultMachine: 'MQ-A',
      defaultOperator: 'Carlos Mendes',
    });

    DB.set('seeded', true);
  }
}

seedIfEmpty();
