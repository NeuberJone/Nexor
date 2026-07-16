"""
Nexor — Sistema de Gerenciamento de Produção Têxtil
Aplicação Flask com interface web reproduzindo o layout da Interface_temp
Baseada no ProjetoJocasta (PXPrintLogs e PXSearchOrders)
"""

import os
import sys
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Importar módulos da aplicação
from app.parsers import parse_log_txt, group_jobs_into_blocks, Job
from app.exporters import export_blocks_to_pdf, export_blocks_to_jpg
from app.planning import ProductionPlanner, Job as PlanningJob
from app.analytics import ProductionAnalytics
from app.sync import get_sync_manager
from app.backup import get_backup_manager
from app.backend_client import get_backend_client, set_backend_url
from app.validators import JobValidator, RollValidator, MachineValidator, FabricValidator, OperatorValidator
from app.error_handler import handle_errors, safe_request_json, ErrorResponse, APIError, ValidationError
from app import database as db

load_dotenv()

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
CORS(app)

# Configurações
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
UPLOAD_FOLDER = '/tmp/nexor_uploads'
ALLOWED_EXTENSIONS = {'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configurar backend client
set_backend_url(BACKEND_API_URL)
backend_client = get_backend_client()

# ============================================================
# HELPERS
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_date(iso_string):
    """Formata data ISO para formato brasileiro."""
    if not iso_string:
        return "—"
    try:
        if isinstance(iso_string, str):
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        else:
            dt = iso_string
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return str(iso_string)

def format_date_short(iso_string):
    """Formata data ISO para formato curto brasileiro."""
    if not iso_string:
        return "—"
    try:
        if isinstance(iso_string, str):
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        else:
            dt = iso_string
        return dt.strftime('%d/%m/%Y')
    except:
        return str(iso_string)

# ============================================================
# ROTAS - PAGES
# ============================================================

@app.route('/')
def index():
    """Página inicial (Home)."""
    return render_template('index.html')

@app.route('/operacao')
def operacao():
    """Página de Operação (Inbox de jobs)."""
    return render_template('operacao.html')

@app.route('/rolos')
def rolos():
    """Página de Rolos."""
    return render_template('rolos.html')

@app.route('/planejamento')
def planejamento():
    """Página de Planejamento de Produção."""
    return render_template('planejamento-novo.html')

@app.route('/estoque')
def estoque():
    """Página de Estoque."""
    return render_template('estoque-novo.html')

@app.route('/analytics')
def analytics():
    """Página de Analytics."""
    return render_template('analytics-novo.html')

@app.route('/cadastros')
def cadastros():
    """Página de Cadastros (Dados mestres)."""
    return render_template('cadastros.html')

@app.route('/configuracoes')
def configuracoes():
    """Página de Configurações."""
    return render_template('configuracoes.html')

@app.route('/sistema')
def sistema():
    """Página de Sistema (Sincronização e Backup)."""
    return render_template('sistema.html')

@app.route('/auditoria')
def auditoria():
    """Página de Auditoria e Inconsistências."""
    return render_template('auditoria.html')

@app.route('/reexportacao')
def reexportacao():
    """Página de Reexportação de Rolos em PDF."""
    return render_template('reexportacao.html')

@app.route('/revisao-inconsistencias')
def revisao_inconsistencias():
    """Página de Revisão de Inconsistências."""
    return render_template('revisao-inconsistencias.html')

# ============================================================
# API - STATUS & METRICS
# ============================================================

@app.route('/api/status')
def api_status():
    """Verifica status do servidor."""
    stats = db.get_statistics()
    return jsonify({
        'ok': True,
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
    })

@app.route('/api/metrics')
def api_metrics():
    """Retorna métricas de produção."""
    stats = db.get_statistics()
    return jsonify(stats)

# ============================================================
# API - JOBS
# ============================================================

@app.route('/api/jobs')
def api_jobs():
    """Retorna lista de jobs."""
    limit = request.args.get('limit', 1000, type=int)
    roll_id = request.args.get('roll_id', None, type=int)
    
    jobs = db.get_jobs(roll_id=roll_id, limit=limit)
    return jsonify(jobs)

@app.route('/api/jobs/unassigned')
def api_unassigned_jobs():
    """Retorna jobs não atribuídos a nenhum rolo."""
    limit = request.args.get('limit', 1000, type=int)
    jobs = db.get_unassigned_jobs(limit=limit)
    return jsonify(jobs)

# ============================================================
# API - ROLLS
# ============================================================

@app.route('/api/rolls')
def api_rolls():
    """Retorna lista de rolos com filtros avançados."""
    status = request.args.get('status', None)
    machine = request.args.get('machine', None)
    fabric = request.args.get('fabric', None)
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)
    limit = request.args.get('limit', 300, type=int)
    
    rolls = db.get_rolls(
        status=status,
        machine=machine,
        fabric=fabric,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )
    return jsonify(rolls)

@app.route('/api/rolls/<int:roll_id>')
def api_get_roll(roll_id):
    """Obtém detalhes de um rolo específico."""
    roll = db.get_roll(roll_id)
    if not roll:
        return jsonify({'error': 'Rolo não encontrado'}), 404
    
    # Adicionar jobs do rolo
    roll['jobs'] = db.get_jobs(roll_id=roll_id)
    roll['events'] = db.get_events(roll_id)
    
    return jsonify(roll)

@app.route('/api/rolls', methods=['POST'])
@handle_errors
def api_create_roll():
    """Criar novo rolo a partir de jobs selecionados."""
    data = request.get_json()
    
    job_ids = data.get('job_ids', [])
    machine = data.get('machine', 'DESCONHECIDA')
    fabric = data.get('fabric', '')
    notes = data.get('notes', '')
    
    if not job_ids:
        return jsonify({'error': 'Nenhum job selecionado'}), 400
    
    try:
        # Obter jobs do banco e converter para objetos Job
        jobs_data = db.get_jobs(limit=len(job_ids))
        jobs = []
        
        for job_data in jobs_data:
            if job_data['id'] in job_ids:
                job = Job(
                    end_time=datetime.fromisoformat(job_data['end_time']),
                    document=job_data['document'],
                    fabric=job_data['fabric'],
                    height_mm=job_data['height_mm'],
                    vpos_mm=job_data['vpos_mm'],
                    src_file=job_data['src_file'],
                )
                jobs.append(job)
        
        if not jobs:
            return jsonify({'error': 'Jobs não encontrados'}), 400
        
        # Agrupar em blocos
        blocks = group_jobs_into_blocks(jobs, machine=machine)
        
        if not blocks:
            return jsonify({'error': 'Falha ao agrupar jobs'}), 400
        
        # Calcular totais
        total_m = sum(b.total_m for b in blocks)
        total_jobs = sum(b.job_count for b in blocks)
        
        # Criar rolo
        roll_name = f"ROLO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        roll_id = db.insert_roll(
            roll_name=roll_name,
            machine=machine,
            fabric=fabric or blocks[0].fabric,
            total_m=total_m,
            job_count=total_jobs,
            notes=notes,
        )
        
        # Atribuir jobs ao rolo
        db.assign_jobs_to_roll(job_ids, roll_id)
        
        # Registrar evento
        db.insert_event(roll_id, 'roll_created', {
            'job_count': total_jobs,
            'total_m': round(total_m, 2),
            'blocks': len(blocks),
        })
        
        return jsonify({
            'ok': True,
            'id': roll_id,
            'roll_name': roll_name,
            'total_m': round(total_m, 2),
            'job_count': total_jobs,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rolls/<int:roll_id>/close', methods=['POST'])
@handle_errors
def api_close_roll(roll_id):
    """Fechar rolo e exportar PDF."""
    try:
        roll = db.get_roll(roll_id)
        if not roll:
            return jsonify({'error': 'Rolo não encontrado'}), 404
        
        # Fechar rolo
        db.close_roll(roll_id)
        
        # Registrar evento
        db.insert_event(roll_id, 'roll_closed', {
            'total_m': roll['total_m'],
            'job_count': roll['job_count'],
        })
        
        return jsonify({
            'ok': True,
            'roll_id': roll_id,
            'status': 'closed',
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rolls/<int:roll_id>/export-jpg', methods=['GET'])
def api_export_roll_jpg(roll_id):
    """Exportar rolo em JPG mirror."""
    try:
        roll = db.get_roll(roll_id)
        if not roll:
            return jsonify({'error': 'Rolo nao encontrado'}), 404
        
        # Obter jobs do rolo
        jobs = db.get_roll_jobs(roll_id)
        if not jobs:
            return jsonify({'error': 'Rolo sem jobs'}), 400
        
        # Agrupar em blocos
        blocks = group_jobs_into_blocks(jobs)
        
        # Criar arquivo temporario
        import tempfile
        temp_dir = tempfile.gettempdir()
        jpg_path = os.path.join(temp_dir, f"rolo_{roll_id}.jpg")
        
        # Exportar
        success = export_blocks_to_jpg(blocks, roll['name'], jpg_path, mirror=True)
        
        if not success:
            return jsonify({'error': 'Erro ao exportar JPG'}), 500
        
        # Registrar evento
        db.insert_event(roll_id, 'jpg_exported', {'format': 'mirror'})
        
        # Enviar arquivo
        return send_file(jpg_path, mimetype='image/jpeg', as_attachment=True, 
                        download_name=f"rolo_{roll_id}_mirror.jpg")
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - MASTER DATA
# ============================================================

@app.route('/api/fabrics')
def api_fabrics():
    """Retorna lista de tecidos únicos."""
    try:
        conn = sqlite3.connect(db.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT DISTINCT fabric FROM jobs ORDER BY fabric")
        fabrics = [row[0] for row in c.fetchall()]
        conn.close()
        
        return jsonify([{'name': f, 'code': f} for f in fabrics])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/machines')
def api_machines():
    """Retorna lista de máquinas."""
    # TODO: Implementar tabela de máquinas no banco
    return jsonify([
        {'id': 1, 'code': 'MQ-A', 'name': 'Máquina A', 'type': 'Impressora'},
        {'id': 2, 'code': 'MQ-B', 'name': 'Máquina B', 'type': 'Impressora'},
        {'id': 3, 'code': 'MQ-C', 'name': 'Máquina C', 'type': 'Impressora'},
    ])

@app.route('/api/log-sources')
def api_log_sources():
    """Retorna lista de fontes de logs."""
    return jsonify([])

# ============================================================
# API - IMPORT
# ============================================================

@app.route('/api/import', methods=['POST'])
def api_import():
    """Importar arquivo .txt de log."""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo vazio'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Apenas arquivos .txt são suportados'}), 400
    
    try:
        # Salvar arquivo temporário
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse do arquivo
        job = parse_log_txt(filepath)
        if not job:
            os.remove(filepath)
            return jsonify({'error': 'Falha ao parsear arquivo'}), 400
        
        # Inserir no banco
        job_id = db.insert_job(
            document=job.document,
            fabric=job.fabric,
            height_mm=job.height_mm,
            vpos_mm=job.vpos_mm,
            real_m=job.real_m,
            end_time=job.end_time,
            src_file=filepath,
        )
        
        return jsonify({
            'ok': True,
            'job_id': job_id,
            'document': job.document,
            'fabric': job.fabric,
            'real_m': round(job.real_m, 2),
            'end_time': job.end_time.isoformat(),
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import/directory', methods=['POST'])
def api_import_directory():
    """Importar todos os arquivos .txt de um diretório."""
    data = request.get_json()
    directory = data.get('directory', '')
    
    if not directory:
        return jsonify({'error': 'Diretório não especificado'}), 400
    
    try:
        from app.parsers import import_logs_from_directory
        jobs, errors = import_logs_from_directory(directory)
        
        imported_count = 0
        for job in jobs:
            try:
                db.insert_job(
                    document=job.document,
                    fabric=job.fabric,
                    height_mm=job.height_mm,
                    vpos_mm=job.vpos_mm,
                    real_m=job.real_m,
                    end_time=job.end_time,
                    src_file=job.src_file,
                )
                imported_count += 1
            except Exception as e:
                errors.append(f"Erro ao inserir job: {str(e)}")
        
        return jsonify({
            'ok': True,
            'imported_count': imported_count,
            'total_count': len(jobs),
            'errors': errors,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - AUDIT & INCONSISTENCIES
# ============================================================

@app.route('/api/rolls/<int:roll_id>/audit')
def api_roll_audit(roll_id):
    """Obtém trilha de auditoria de um rolo."""
    roll = db.get_roll(roll_id)
    if not roll:
        return jsonify({'error': 'Rolo não encontrado'}), 404
    
    events = db.get_roll_audit_trail(roll_id)
    return jsonify({
        'roll_id': roll_id,
        'roll_name': roll['roll_name'],
        'events': events,
    })

@app.route('/api/inconsistencies')
def api_inconsistencies():
    """Retorna lista de inconsistências detectadas."""
    inconsistencies = db.get_inconsistencies()
    return jsonify({
        'count': len(inconsistencies),
        'items': inconsistencies,
    })

@app.route('/api/rolls/<int:roll_id>/export-pdf', methods=['GET'])
def api_export_roll_pdf(roll_id):
    """Exporta rolo em PDF."""
    try:
        roll = db.get_roll(roll_id)
        if not roll:
            return jsonify({'error': 'Rolo não encontrado'}), 404
        
        # Obter jobs do rolo
        jobs_data = db.get_jobs(roll_id=roll_id)
        
        # Converter para objetos Job
        jobs = []
        for job_data in jobs_data:
            job = Job(
                end_time=datetime.fromisoformat(job_data['end_time']),
                document=job_data['document'],
                fabric=job_data['fabric'],
                height_mm=job_data['height_mm'],
                vpos_mm=job_data['vpos_mm'],
                src_file=job_data['src_file'],
            )
            jobs.append(job)
        
        # Agrupar em blocos
        blocks = group_jobs_into_blocks(jobs, machine=roll['machine'])
        
        # Gerar PDF
        mode = request.args.get('mode', 'summary')  # summary ou full
        pdf_path = f"/tmp/rolo_{roll_id}_{mode}.pdf"
        
        success = export_blocks_to_pdf(
            blocks=blocks,
            roll_name=roll['roll_name'],
            output_path=pdf_path,
            mode=mode,
        )
        
        if not success:
            return jsonify({'error': 'Falha ao gerar PDF'}), 500
        
        # Retornar URL do arquivo
        return jsonify({
            'ok': True,
            'file': pdf_path,
            'roll_id': roll_id,
            'mode': mode,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - SUSPECTS (placeholder)
# ============================================================

@app.route('/api/suspects')
def api_suspects():
    """Retorna lista de jobs suspeitos (não implementado)."""
    return jsonify([])

@app.route('/api/suspects/<int:job_id>/review', methods=['POST'])
def api_review_suspect(job_id):
    """Revisa job suspeito (não implementado)."""
    return jsonify({'error': 'Não implementado'}), 501

# ============================================================
# API - PLANNING
# ============================================================

@app.route('/api/planning/generate', methods=['POST'])
def api_planning_generate():
    """Gera plano de produção para jobs selecionados."""
    try:
        data = request.get_json()
        jobs_data = data.get('jobs', [])
        
        if not jobs_data:
            return jsonify({'error': 'Nenhum job fornecido'}), 400
        
        # Criar planejador
        planner = ProductionPlanner()
        
        # Adicionar máquinas
        machines = db.get_machines()
        for machine in machines:
            planner.add_machine(machine['code'], machine['name'], speed_m_per_hour=100.0)
        
        # Converter jobs para formato do planejador
        planning_jobs = []
        for job_data in jobs_data:
            job = PlanningJob(
                id=job_data.get('id', 0),
                document=job_data.get('document', ''),
                fabric=job_data.get('fabric', ''),
                planned_length_m=job_data.get('planned_length_m', 0),
                machine_code=job_data.get('machine', 'DESCONHECIDA'),
                priority=job_data.get('priority', 0),
            )
            planning_jobs.append(job)
        
        # Gerar plano
        schedule = planner.plan_jobs(planning_jobs)
        summary = planner.get_schedule_summary()
        utilization = planner.get_utilization_report()
        
        return jsonify({
            'ok': True,
            'schedule': planner.export_schedule(),
            'summary': summary,
            'utilization': utilization,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/planning/optimize', methods=['POST'])
def api_planning_optimize():
    """Otimiza sequência de jobs."""
    try:
        data = request.get_json()
        jobs_data = data.get('jobs', [])
        
        if not jobs_data:
            return jsonify({'error': 'Nenhum job fornecido'}), 400
        
        # Criar planejador
        planner = ProductionPlanner()
        
        # Converter jobs
        planning_jobs = []
        for job_data in jobs_data:
            job = PlanningJob(
                id=job_data.get('id', 0),
                document=job_data.get('document', ''),
                fabric=job_data.get('fabric', ''),
                planned_length_m=job_data.get('planned_length_m', 0),
                machine_code=job_data.get('machine', 'DESCONHECIDA'),
                priority=job_data.get('priority', 0),
            )
            planning_jobs.append(job)
        
        # Otimizar sequência
        optimized = planner.optimize_sequence(planning_jobs)
        
        return jsonify({
            'ok': True,
            'optimized_jobs': [
                {
                    'id': j.id,
                    'document': j.document,
                    'fabric': j.fabric,
                    'planned_length_m': j.planned_length_m,
                    'machine': j.machine_code,
                }
                for j in optimized
            ],
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/planning/gaps', methods=['POST'])
def api_planning_gaps():
    """Calcula gaps entre jobs."""
    try:
        data = request.get_json()
        jobs_data = data.get('jobs', [])
        
        if not jobs_data:
            return jsonify({'error': 'Nenhum job fornecido'}), 400
        
        # Criar planejador
        planner = ProductionPlanner()
        
        # Adicionar máquinas
        machines = db.get_machines()
        for machine in machines:
            planner.add_machine(machine['code'], machine['name'], speed_m_per_hour=100.0)
        
        # Converter jobs
        planning_jobs = []
        for job_data in jobs_data:
            job = PlanningJob(
                id=job_data.get('id', 0),
                document=job_data.get('document', ''),
                fabric=job_data.get('fabric', ''),
                planned_length_m=job_data.get('planned_length_m', 0),
                machine_code=job_data.get('machine', 'DESCONHECIDA'),
                priority=job_data.get('priority', 0),
            )
            planning_jobs.append(job)
        
        # Gerar plano
        planner.plan_jobs(planning_jobs)
        
        # Calcular gaps
        gaps = planner.calculate_gaps()
        
        return jsonify({
            'ok': True,
            'gaps': gaps,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/planning/gantt', methods=['POST'])
def api_planning_gantt():
    """Retorna dados para visualização Gantt."""
    try:
        data = request.get_json()
        jobs_data = data.get('jobs', [])
        
        if not jobs_data:
            return jsonify({'error': 'Nenhum job fornecido'}), 400
        
        # Criar planejador
        planner = ProductionPlanner()
        
        # Adicionar máquinas
        machines = db.get_machines()
        for machine in machines:
            planner.add_machine(machine['code'], machine['name'], speed_m_per_hour=100.0)
        
        # Converter jobs
        planning_jobs = []
        for job_data in jobs_data:
            job = PlanningJob(
                id=job_data.get('id', 0),
                document=job_data.get('document', ''),
                fabric=job_data.get('fabric', ''),
                planned_length_m=job_data.get('planned_length_m', 0),
                machine_code=job_data.get('machine', 'DESCONHECIDA'),
                priority=job_data.get('priority', 0),
            )
            planning_jobs.append(job)
        
        # Gerar plano
        planner.plan_jobs(planning_jobs)
        
        # Obter dados Gantt
        gantt_data = planner.get_gantt_data()
        
        return jsonify({
            'ok': True,
            'gantt': gantt_data,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - STOCK
# ============================================================

@app.route('/api/stock/rolls', methods=['GET'])
def api_stock_rolls():
    """Retorna rolos de estoque."""
    try:
        fabric = request.args.get('fabric')
        status = request.args.get('status', 'available')
        
        rolls = db.get_stock_rolls(fabric=fabric, status=status)
        
        return jsonify({
            'ok': True,
            'rolls': rolls,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/rolls', methods=['POST'])
def api_add_stock_roll():
    """Adiciona novo rolo de estoque."""
    try:
        data = request.get_json()
        
        fabric = data.get('fabric')
        quantity_m = data.get('quantity_m', 0)
        supplier = data.get('supplier')
        batch_code = data.get('batch_code')
        location = data.get('location')
        
        if not fabric or quantity_m <= 0:
            return jsonify({'error': 'Dados invalidos'}), 400
        
        stock_id = db.add_stock_roll(fabric, quantity_m, supplier, batch_code, location)
        
        return jsonify({
            'ok': True,
            'stock_id': stock_id,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/consume', methods=['POST'])
def api_consume_stock():
    """Consome estoque."""
    try:
        data = request.get_json()
        
        stock_roll_id = data.get('stock_roll_id')
        quantity_m = data.get('quantity_m', 0)
        roll_id = data.get('roll_id')
        operator = data.get('operator')
        
        if not stock_roll_id or quantity_m <= 0:
            return jsonify({'error': 'Dados invalidos'}), 400
        
        success = db.consume_stock(stock_roll_id, quantity_m, roll_id, operator)
        
        if not success:
            return jsonify({'error': 'Estoque insuficiente'}), 400
        
        return jsonify({
            'ok': True,
            'consumed': quantity_m,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/movements', methods=['GET'])
def api_stock_movements():
    """Retorna movimentacoes de estoque."""
    try:
        stock_roll_id = request.args.get('stock_roll_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        movements = db.get_stock_movements(stock_roll_id, limit)
        
        return jsonify({
            'ok': True,
            'movements': movements,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/alerts', methods=['GET'])
def api_stock_alerts():
    """Retorna alertas de estoque."""
    try:
        status = request.args.get('status', 'active')
        
        alerts = db.get_stock_alerts(status)
        
        return jsonify({
            'ok': True,
            'alerts': alerts,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/summary', methods=['GET'])
def api_stock_summary():
    """Retorna resumo de estoque."""
    try:
        summary = db.get_stock_summary()
        
        return jsonify({
            'ok': True,
            'summary': summary,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - ANALYTICS
# ============================================================

@app.route('/api/analytics/metrics', methods=['GET'])
def api_analytics_metrics():
    """Retorna métricas gerais de produção."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        metrics = ProductionAnalytics.get_production_metrics(date_from, date_to)
        
        return jsonify({
            'ok': True,
            'metrics': metrics,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/machines', methods=['GET'])
def api_analytics_machines():
    """Retorna utilização por máquina."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        utilization = ProductionAnalytics.get_machine_utilization(date_from, date_to)
        
        return jsonify({
            'ok': True,
            'utilization': utilization,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/fabrics', methods=['GET'])
def api_analytics_fabrics():
    """Retorna distribuição de tecidos."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        distribution = ProductionAnalytics.get_fabric_distribution(date_from, date_to)
        
        return jsonify({
            'ok': True,
            'distribution': distribution,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/daily', methods=['GET'])
def api_analytics_daily():
    """Retorna produção diária."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        daily = ProductionAnalytics.get_daily_production(date_from, date_to)
        
        return jsonify({
            'ok': True,
            'daily': daily,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/efficiency', methods=['GET'])
def api_analytics_efficiency():
    """Retorna métricas de eficiência."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        efficiency = ProductionAnalytics.get_efficiency_metrics(date_from, date_to)
        
        return jsonify({
            'ok': True,
            'efficiency': efficiency,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/comparison', methods=['GET'])
def api_analytics_comparison():
    """Retorna comparação entre períodos."""
    try:
        periods = request.args.get('periods', 4, type=int)
        
        comparison = ProductionAnalytics.get_comparison_periods(periods)
        
        return jsonify({
            'ok': True,
            'comparison': comparison,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API - SYNC & BACKUP
# ============================================================

@app.route('/api/sync/health', methods=['GET'])
def api_sync_health():
    """Verifica saúde do backend Python."""
    try:
        sync_manager = get_sync_manager()
        health = sync_manager.check_backend_health()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/status', methods=['GET'])
def api_sync_status():
    """Retorna status de sincronização."""
    try:
        sync_manager = get_sync_manager()
        status = sync_manager.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/full', methods=['POST'])
def api_sync_full():
    """Realiza sincronização completa."""
    try:
        sync_manager = get_sync_manager()
        result = sync_manager.full_sync()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/jobs', methods=['POST'])
def api_sync_jobs():
    """Sincroniza jobs do backend Python."""
    try:
        sync_manager = get_sync_manager()
        result = sync_manager.sync_jobs_from_backend()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/rolls', methods=['POST'])
def api_sync_rolls():
    """Sincroniza rolos para o backend Python."""
    try:
        sync_manager = get_sync_manager()
        result = sync_manager.sync_rolls_to_backend()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/create', methods=['POST'])
def api_backup_create():
    """Cria backup do banco de dados."""
    try:
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.create_backup(compress=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/list', methods=['GET'])
def api_backup_list():
    """Lista backups disponíveis."""
    try:
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.list_backups()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
def api_backup_restore():
    """Restaura um backup."""
    try:
        data = request.get_json()
        backup_name = data.get('backup_name')
        
        if not backup_name:
            return jsonify({'error': 'backup_name requerido'}), 400
        
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.restore_backup(backup_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/delete', methods=['POST'])
def api_backup_delete():
    """Deleta um backup."""
    try:
        data = request.get_json()
        backup_name = data.get('backup_name')
        
        if not backup_name:
            return jsonify({'error': 'backup_name requerido'}), 400
        
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.delete_backup(backup_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/cleanup', methods=['POST'])
def api_backup_cleanup():
    """Remove backups antigos."""
    try:
        data = request.get_json()
        keep_count = data.get('keep_count', 10)
        
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.cleanup_old_backups(keep_count)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/stats', methods=['GET'])
def api_backup_stats():
    """Retorna estatísticas de backup."""
    try:
        backup_manager = get_backup_manager('nexor.db')
        result = backup_manager.get_backup_stats()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# TEMPLATE CONTEXT
# ============================================================

@app.context_processor
def inject_helpers():
    """Injeta funções auxiliares nos templates."""
    return {
        'format_date': format_date,
        'format_date_short': format_date_short,
        'now': datetime.now(),
    }

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=DEBUG, host='127.0.0.1', port=port)
