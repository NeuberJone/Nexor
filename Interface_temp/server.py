"""
Nexor API Server
================
Coloque este arquivo na raiz do projeto Python (junto com app.py, nexor.db, etc.)
Execute: python server.py
Acesse: http://localhost:5000

Dependências: flask (pip install flask)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: garante que o diretório do servidor está no sys.path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from flask import Flask, jsonify, request, send_from_directory, Response
except ImportError:
    print("Flask não encontrado. Instale com: pip install flask")
    sys.exit(1)

from storage.database import init_database, get_connection
from storage.repository import ProductionRepository
from storage.log_sources_repository import LogSourceRepository
from analytics.production_metrics import (
    collect_candidates,
    effective_printed_length_m,
    load_jobs_from_db,
    resolve_default_db_path,
    format_m,
    format_ratio,
)
from machines.registry import list_registered_machines, register_machine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent  # ou ajuste para onde está o frontend

app = Flask(__name__, static_folder=None)

# CORS simples para desenvolvimento
@app.after_request
def add_cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if path and (FRONTEND_DIR / path).exists():
        return send_from_directory(str(FRONTEND_DIR), path)
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return send_from_directory(str(FRONTEND_DIR), "index.html")
    return "Nexor API running. Frontend not found at: " + str(FRONTEND_DIR), 200

@app.route("/api/options", methods=["OPTIONS"])
def handle_options():
    return "", 204

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") if dt else None

def _job_to_dict(job) -> dict:
    return {
        "id": job.id,
        "job_id": job.job_id,
        "machine": job.machine,
        "computer_name": job.computer_name,
        "document": job.document,
        "start_time": _iso(job.start_time) if hasattr(job.start_time, "isoformat") else str(job.start_time or ""),
        "end_time": _iso(job.end_time) if hasattr(job.end_time, "isoformat") else str(job.end_time or ""),
        "duration_seconds": job.duration_seconds,
        "fabric": job.fabric,
        "planned_length_m": job.planned_length_m,
        "actual_printed_length_m": job.actual_printed_length_m,
        "effective_printed_length_m": effective_printed_length_m(
            type("J", (), {"actual_printed_length_m": job.actual_printed_length_m,
                           "consumed_length_m": job.consumed_length_m,
                           "gap_before_m": job.gap_before_m})()
        ),
        "gap_before_m": job.gap_before_m,
        "consumed_length_m": job.consumed_length_m,
        "print_status": job.print_status,
        "job_type": job.job_type,
        "counts_as_valid_production": job.counts_as_valid_production,
        "counts_for_roll_export": job.counts_for_roll_export,
        "error_reason": job.error_reason,
        "suspicion_category": job.suspicion_category,
        "suspicion_reason": job.suspicion_reason,
        "suspicion_ratio": job.suspicion_ratio,
        "suspicion_missing_length_m": job.suspicion_missing_length_m,
        "review_status": job.review_status,
        "review_note": job.review_note,
        "reviewed_by": job.reviewed_by,
        "reviewed_at": _iso(job.reviewed_at) if job.reviewed_at and hasattr(job.reviewed_at, "isoformat") else None,
        "source_path": job.source_path,
        "operator_code": job.operator_code,
        "operator_name": job.operator_name,
        "created_at": _iso(job.created_at) if job.created_at and hasattr(job.created_at, "isoformat") else None,
    }

def _roll_to_dict(roll) -> dict:
    return {
        "id": roll.id,
        "roll_name": roll.roll_name,
        "machine": roll.machine,
        "fabric": roll.fabric,
        "status": roll.status,
        "note": roll.note,
        "created_at": _iso(roll.created_at) if roll.created_at and hasattr(roll.created_at, "isoformat") else str(roll.created_at or ""),
        "closed_at": _iso(roll.closed_at) if roll.closed_at and hasattr(roll.closed_at, "isoformat") else None,
    }

def _item_to_dict(item) -> dict:
    return {
        "id": item.id,
        "roll_id": item.roll_id,
        "job_row_id": item.job_row_id,
        "job_id": item.job_id,
        "document": item.document,
        "machine": item.machine,
        "fabric": item.fabric,
        "sort_order": item.sort_order,
        "planned_length_m": item.planned_length_m,
        "effective_printed_length_m": item.effective_printed_length_m,
        "consumed_length_m": item.consumed_length_m,
        "gap_before_m": item.gap_before_m,
        "metric_category": item.metric_category,
        "review_status": item.review_status,
        "snapshot_print_status": item.snapshot_print_status,
    }

def get_repo() -> ProductionRepository:
    return ProductionRepository()

# ---------------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------------
@app.route("/api/status")
def api_status():
    db_path = resolve_default_db_path()
    return jsonify({
        "ok": True,
        "version": "1.0.0",
        "db": str(db_path),
        "db_exists": db_path.exists(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })

# ---------------------------------------------------------------------------
# JOBS
# ---------------------------------------------------------------------------
@app.route("/api/jobs")
def api_list_jobs():
    repo = get_repo()
    try:
        jobs = repo.list_jobs()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    fabric_filter  = request.args.get("fabric", "").strip().lower()
    machine_filter = request.args.get("machine", "").strip().lower()
    status_filter  = request.args.get("status", "").strip().upper()
    available_only = request.args.get("available") == "1"
    limit          = int(request.args.get("limit", 500))

    filtered = jobs
    if fabric_filter:
        filtered = [j for j in filtered if (j.fabric or "").lower() == fabric_filter]
    if machine_filter:
        filtered = [j for j in filtered if (j.machine or "").lower() == machine_filter]
    if status_filter:
        filtered = [j for j in filtered if j.print_status.upper() == status_filter]
    if available_only:
        # Jobs disponíveis = não estão em nenhum rolo fechado
        try:
            conn = repo.connect()
            in_roll = set(
                row[0] for row in conn.execute(
                    "SELECT job_row_id FROM roll_items ri JOIN rolls r ON r.id = ri.roll_id WHERE r.status = 'CLOSED'"
                ).fetchall()
            )
            conn.close()
        except Exception:
            in_roll = set()
        filtered = [j for j in filtered if j.id not in in_roll]

    return jsonify([_job_to_dict(j) for j in filtered[:limit]])


@app.route("/api/jobs/<int:job_id>")
def api_get_job(job_id: int):
    repo = get_repo()
    try:
        job = repo.get_job_by_row_id(job_id)
        if not job:
            return jsonify({"error": "Job não encontrado"}), 404
        return jsonify(_job_to_dict(job))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# SUSPECTS / PENDING REVIEWS
# ---------------------------------------------------------------------------
@app.route("/api/suspects")
def api_list_suspects():
    repo = get_repo()
    try:
        repo.ensure_review_fields()
        jobs = repo.list_pending_reviews()
        return jsonify([_job_to_dict(j) for j in jobs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/suspects/scan", methods=["POST"])
def api_scan_suspects():
    try:
        repo = get_repo()
        repo.ensure_review_fields()
        _, _, jobs_snap = load_jobs_from_db()
        aborted, partial = collect_candidates(jobs_snap)
        active_ids: set[int] = set()
        marked = 0
        for candidate in [*aborted, *partial]:
            if candidate.job.rowid is None:
                continue
            rid = int(candidate.job.rowid)
            active_ids.add(rid)
            repo.mark_job_suspicion(
                row_id=rid,
                category=candidate.decision.category or "UNKNOWN",
                reason=candidate.decision.reason,
                ratio=candidate.decision.ratio,
                missing_length_m=candidate.decision.missing_length_m,
            )
            marked += 1
        cleared = repo.clear_stale_pending_suspicions(active_ids)
        return jsonify({"marked": marked, "cleared": cleared,
                        "aborted": len(aborted), "partial": len(partial)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/suspects/<int:job_id>/review", methods=["POST"])
def api_review_suspect(job_id: int):
    data = request.get_json(force=True)
    status    = data.get("status")
    note      = data.get("note")
    reviewed_by = data.get("reviewed_by")
    sync_ops  = data.get("sync_operational_status", False)

    allowed = {"REVIEWED_OK", "REVIEWED_PARTIAL", "REVIEWED_FAILED"}
    if status not in allowed:
        return jsonify({"error": f"status deve ser um de {allowed}"}), 400

    repo = get_repo()
    try:
        repo.update_review(row_id=job_id, review_status=status,
                           review_note=note, reviewed_by=reviewed_by)
        if sync_ops and status == "REVIEWED_FAILED":
            repo.apply_review_failed_operational_effects(row_id=job_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------
@app.route("/api/metrics")
def api_metrics():
    try:
        _, _, jobs = load_jobs_from_db()
        eligible = [j for j in jobs if j.planned_length_m > 0
                    and j.counts_as_valid_production
                    and j.print_status not in {"FAILED", "CANCELED", "TEST"}
                    and j.job_type not in {"TEST"}]

        total_planned  = sum(j.planned_length_m for j in jobs)
        total_effective= sum(effective_printed_length_m(
            type("J", (), {"actual_printed_length_m": j.actual_printed_length_m,
                           "consumed_length_m": j.consumed_length_m,
                           "gap_before_m": j.gap_before_m})()) for j in jobs)
        total_gap      = sum(j.gap_before_m for j in jobs)
        total_consumed = sum(j.consumed_length_m for j in jobs)
        ratio          = (total_effective / total_planned) if total_planned > 0 else None
        aborted, partial = collect_candidates(jobs)

        fabrics: dict[str, dict] = {}
        for j in eligible:
            f = j.fabric or "Desconhecido"
            if f not in fabrics:
                fabrics[f] = {"fabric": f, "jobs": 0, "planned_m": 0.0, "effective_m": 0.0}
            eff = effective_printed_length_m(
                type("J", (), {"actual_printed_length_m": j.actual_printed_length_m,
                               "consumed_length_m": j.consumed_length_m,
                               "gap_before_m": j.gap_before_m})())
            fabrics[f]["jobs"] += 1
            fabrics[f]["planned_m"] += j.planned_length_m
            fabrics[f]["effective_m"] += eff

        machines: dict[str, dict] = {}
        for j in eligible:
            m = j.machine or "Desconhecido"
            if m not in machines:
                machines[m] = {"machine": m, "jobs": 0, "planned_m": 0.0, "effective_m": 0.0}
            eff = effective_printed_length_m(
                type("J", (), {"actual_printed_length_m": j.actual_printed_length_m,
                               "consumed_length_m": j.consumed_length_m,
                               "gap_before_m": j.gap_before_m})())
            machines[m]["jobs"] += 1
            machines[m]["planned_m"] += j.planned_length_m
            machines[m]["effective_m"] += eff

        return jsonify({
            "total_jobs": len(jobs),
            "eligible_jobs": len(eligible),
            "total_planned_m": round(total_planned, 3),
            "total_effective_m": round(total_effective, 3),
            "total_gap_m": round(total_gap, 3),
            "total_consumed_m": round(total_consumed, 3),
            "global_efficiency": round(ratio, 4) if ratio else None,
            "aborted_candidates": len(aborted),
            "partial_candidates": len(partial),
            "by_fabric": sorted(fabrics.values(), key=lambda x: -x["planned_m"]),
            "by_machine": sorted(machines.values(), key=lambda x: -x["planned_m"]),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# ROLLS
# ---------------------------------------------------------------------------
@app.route("/api/rolls")
def api_list_rolls():
    repo = get_repo()
    try:
        rolls = repo.list_rolls()
        result = []
        for roll in rolls:
            d = _roll_to_dict(roll)
            try:
                summary = repo.get_roll_summary(roll.id)
                d.update({
                    "total_jobs": summary.get("total_jobs", 0),
                    "total_planned_m": summary.get("total_planned_m", 0.0),
                    "total_effective_m": summary.get("total_effective_m", 0.0),
                    "total_consumed_m": summary.get("total_consumed_m", 0.0),
                    "has_suspects": summary.get("has_suspects", False),
                })
            except Exception:
                pass
            result.append(d)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rolls/<int:roll_id>")
def api_get_roll(roll_id: int):
    repo = get_repo()
    try:
        roll = repo.get_roll(roll_id)
        if not roll:
            return jsonify({"error": "Rolo não encontrado"}), 404
        d = _roll_to_dict(roll)
        try:
            summary = repo.get_roll_summary(roll_id)
            d["summary"] = summary
        except Exception:
            pass
        try:
            items = repo.list_roll_items(roll_id)
            d["items"] = [_item_to_dict(i) for i in items]
        except Exception:
            d["items"] = []
        return jsonify(d)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rolls", methods=["POST"])
def api_create_roll():
    data = request.get_json(force=True)
    machine = data.get("machine", "")
    fabric  = data.get("fabric")
    note    = data.get("note")
    job_ids = data.get("job_ids", [])

    if not machine:
        return jsonify({"error": "machine é obrigatório"}), 400

    repo = get_repo()
    try:
        repo.ensure_roll_tables()
        roll_name = repo.generate_roll_name(machine=machine)
        roll = repo.create_roll(roll_name=roll_name, machine=machine, fabric=fabric, note=note)

        for idx, job_row_id in enumerate(job_ids):
            try:
                repo.add_job_to_roll(roll_id=roll.id, job_row_id=int(job_row_id), sort_order=idx)
            except Exception:
                pass

        return jsonify(_roll_to_dict(roll)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rolls/<int:roll_id>/close", methods=["POST"])
def api_close_roll(roll_id: int):
    repo = get_repo()
    try:
        repo.close_roll(roll_id)
        roll = repo.get_roll(roll_id)
        return jsonify(_roll_to_dict(roll))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rolls/<int:roll_id>/items", methods=["POST"])
def api_add_roll_item(roll_id: int):
    data = request.get_json(force=True)
    job_row_id = data.get("job_row_id")
    sort_order = data.get("sort_order", 0)
    if job_row_id is None:
        return jsonify({"error": "job_row_id é obrigatório"}), 400
    repo = get_repo()
    try:
        repo.add_job_to_roll(roll_id=roll_id, job_row_id=int(job_row_id), sort_order=sort_order)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rolls/<int:roll_id>/items/<int:job_row_id>", methods=["DELETE"])
def api_remove_roll_item(roll_id: int, job_row_id: int):
    repo = get_repo()
    try:
        repo.remove_job_from_roll(roll_id=roll_id, job_row_id=job_row_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# LOG SOURCES
# ---------------------------------------------------------------------------
@app.route("/api/log-sources")
def api_list_sources():
    repo = LogSourceRepository()
    try:
        rows = repo.list_enabled()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/log-sources", methods=["POST"])
def api_add_source():
    data = request.get_json(force=True)
    name     = data.get("name", "").strip()
    path     = data.get("path", "").strip()
    recursive = data.get("recursive", True)
    machine_hint = data.get("machine_hint")
    if not name or not path:
        return jsonify({"error": "name e path são obrigatórios"}), 400
    repo = LogSourceRepository()
    try:
        repo.insert(name=name, path=path, recursive=recursive, machine_hint=machine_hint)
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------
@app.route("/api/import", methods=["POST"])
def api_run_import():
    try:
        from app import main as run_import
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_import()
        output = buf.getvalue()
        return jsonify({"ok": True, "output": output})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False}), 500

# ---------------------------------------------------------------------------
# MACHINES (registry)
# ---------------------------------------------------------------------------
@app.route("/api/machines")
def api_list_machines():
    registry = list_registered_machines()
    result = [{"computer_name": cn, "machine_id": mid} for cn, mid in registry.items()]
    return jsonify(result)


@app.route("/api/machines", methods=["POST"])
def api_add_machine():
    data = request.get_json(force=True)
    computer_name = data.get("computer_name", "").strip()
    machine_id    = data.get("machine_id", "").strip()
    if not computer_name or not machine_id:
        return jsonify({"error": "computer_name e machine_id são obrigatórios"}), 400
    try:
        register_machine(computer_name, machine_id)
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------------------------------------------------------------------
# FABRICS (extraídos dos jobs)
# ---------------------------------------------------------------------------
@app.route("/api/fabrics")
def api_list_fabrics():
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT DISTINCT fabric FROM production_jobs WHERE fabric IS NOT NULL ORDER BY fabric"
        ).fetchall()
        conn.close()
        return jsonify([{"name": r["fabric"]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# BOOT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  NEXOR API SERVER")
    print("=" * 60)
    print(f"  Raiz do projeto : {ROOT}")
    print(f"  Frontend        : {FRONTEND_DIR}")
    print(f"  Banco de dados  : {resolve_default_db_path()}")
    print(f"  URL             : http://localhost:5000")
    print("=" * 60)
    print()
    init_database()
    app.run(host="0.0.0.0", port=5000, debug=False)
