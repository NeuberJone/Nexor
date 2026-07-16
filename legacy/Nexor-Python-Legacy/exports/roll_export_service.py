# exports/roll_export_service.py
from __future__ import annotations

import base64
import math
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import ROLL_CLOSED, ROLL_EXPORTED, ROLL_REVIEWED
from storage.repository import ProductionRepository

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas
except Exception:
    A4 = None
    canvas = None
    pdfmetrics = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PIL import Image, ImageDraw, ImageOps
except Exception:
    Image = None
    ImageDraw = None
    ImageOps = None


_ALLOWED_EXPORT_STATUSES = {ROLL_CLOSED, ROLL_EXPORTED, ROLL_REVIEWED}

# 1x1 JPEG branco de fallback
_TINY_JPEG_BASE64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBAQEA8QDw8PDw8PDw8PDw8QFREWFhUR"
    "FRUYHSggGBolGxUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDg0OGhAQGy0lICYtLS0tLS0t"
    "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBIgAC"
    "EQEDEQH/xAAXAAADAQAAAAAAAAAAAAAAAAAAAQID/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/a"
    "AAwDAQACEAMQAAAB6AAAAP/EABQQAQAAAAAAAAAAAAAAAAAAACD/2gAIAQEAAT8Af//EABQRA"
    "QAAAAAAAAAAAAAAAAAAACD/2gAIAQIBAT8Af//EABQRAQAAAAAAAAAAAAAAAAAAACD/2gAIAQ"
    "MBAT8Af//Z"
)


@dataclass(slots=True)
class ExportJob:
    job_id: str
    document: str
    fabric: str
    machine: str
    effective_m: float
    gap_m: float
    consumed_m: float
    review_status: str | None
    end_time: datetime | None = None
    job_row_id: int | None = None


@dataclass(slots=True)
class ExportBlock:
    fabric: str
    total_m: float = 0.0
    job_count: int = 0
    newest_end: datetime | None = None
    jobs: list[ExportJob] = field(default_factory=list)

    def add_job(self, job: ExportJob) -> None:
        self.jobs.append(job)
        self.total_m += float(job.effective_m or 0.0)
        self.job_count += 1

        if job.end_time is None:
            return
        if self.newest_end is None or job.end_time > self.newest_end:
            self.newest_end = job.end_time


def export_closed_roll(
    *,
    roll_id: int,
    output_dir: str | Path,
    repository: ProductionRepository | None = None,
) -> dict[str, Any]:
    repo = repository or ProductionRepository()

    roll = repo.get_roll(roll_id=roll_id)
    if not roll:
        raise ValueError(f"Rolo não encontrado: id={roll_id}")

    if roll.status not in _ALLOWED_EXPORT_STATUSES:
        raise ValueError(
            f"O rolo {roll.roll_name} precisa estar fechado para exportação. "
            f"Status atual: {roll.status}"
        )

    summary = repo.get_roll_summary(roll_id)
    jobs_count = int(summary["jobs_count"] or 0)

    if jobs_count <= 0:
        raise ValueError("Não é possível exportar um rolo vazio ou sem itens.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    safe_roll_name = _sanitize_filename(roll.roll_name or f"roll_{roll_id}")
    pdf_path = output_path / f"{safe_roll_name}.pdf"
    jpg_path = output_path / f"{safe_roll_name}.jpg"

    payload = _build_export_payload(repo, summary)

    if _has_reportlab():
        _write_pxprintlogs_style_pdf(
            pdf_path=pdf_path,
            blocks=payload["blocks"],
            roll_name=str(roll.roll_name),
            machine=str(roll.machine),
            note=getattr(roll, "note", None),
        )
    else:
        _write_fallback_pdf(pdf_path, payload["fallback_lines"])

    if _has_pdf_render_stack() and pdf_path.exists():
        _render_first_page_to_mirrored_jpg(
            pdf_path=pdf_path,
            jpg_path=jpg_path,
            target_width_cm=21.0,
            dpi=300,
            quality=95,
        )
    elif Image is not None and ImageDraw is not None:
        _write_fallback_summary_jpg(jpg_path, payload["fallback_lines"], mirrored=True)
    else:
        jpg_path.write_bytes(base64.b64decode(_TINY_JPEG_BASE64))

    repo.mark_roll_exported(roll_id)
    exported_roll = repo.get_roll(roll_id=roll_id)

    return {
        "roll_id": roll_id,
        "roll_name": roll.roll_name,
        "pdf_path": str(pdf_path),
        "jpg_path": str(jpg_path),
        "mirror_jpg_path": str(jpg_path),
        "jobs_count": payload["jobs_count"],
        "total_planned_m": payload["total_planned_m"],
        "total_effective_m": payload["total_effective_m"],
        "total_gap_m": payload["total_gap_m"],
        "total_consumed_m": payload["total_consumed_m"],
        "efficiency_ratio": payload["efficiency_ratio"],
        "status": exported_roll.status if exported_roll else ROLL_EXPORTED,
    }


def _build_export_payload(repo: ProductionRepository, summary: dict[str, Any]) -> dict[str, Any]:
    roll = summary["roll"]
    raw_items = summary.get("items", [])

    jobs = _build_export_jobs(repo, raw_items)
    blocks = _group_jobs_by_fabric(jobs)

    jobs_count = int(summary.get("jobs_count") or 0)
    total_planned_m = float(summary.get("total_planned_m") or 0.0)
    total_effective_m = float(summary.get("total_effective_m") or 0.0)
    total_gap_m = float(summary.get("total_gap_m") or 0.0)
    total_consumed_m = float(summary.get("total_consumed_m") or 0.0)
    efficiency_ratio = _to_float_or_none(summary.get("efficiency_ratio"))

    fallback_lines = [
        f"Ordem do Rolo - {roll.roll_name}",
        f"Máquina: {roll.machine}",
        f"Tecido: {roll.fabric or '-'}",
        f"Status: {roll.status}",
        f"Criado em: {_fmt_dt(getattr(roll, 'created_at', None))}",
        f"Fechado em: {_fmt_dt(getattr(roll, 'closed_at', None))}",
        f"Exportado em: {_fmt_dt(getattr(roll, 'exported_at', None))}",
        f"Observação: {getattr(roll, 'note', None) or '-'}",
        "",
        "Resumo do rolo:",
        f"Jobs: {jobs_count}",
        f"Total planejado: {_fmt_m(total_planned_m)}",
        f"Total efetivo: {_fmt_m(total_effective_m)}",
        f"Gap total: {_fmt_m(total_gap_m)}",
        f"Total consumido: {_fmt_m(total_consumed_m)}",
        f"Eficiência: {_fmt_efficiency(efficiency_ratio)}",
        "",
        "Blocos por tecido:",
    ]

    for index, block in enumerate(blocks, start=1):
        fallback_lines.append(
            f"{index:02d}. {block.fabric} | total={_fmt_m(block.total_m)} | "
            f"qtd={block.job_count} | último fim={_fmt_dt(block.newest_end)}"
        )

    return {
        "blocks": blocks,
        "jobs_count": jobs_count,
        "total_planned_m": total_planned_m,
        "total_effective_m": total_effective_m,
        "total_gap_m": total_gap_m,
        "total_consumed_m": total_consumed_m,
        "efficiency_ratio": efficiency_ratio,
        "fallback_lines": fallback_lines,
    }


def _build_export_jobs(repo: ProductionRepository, raw_items: list[Any]) -> list[ExportJob]:
    jobs: list[ExportJob] = []

    for item in raw_items:
        end_time = None
        machine = str(getattr(item, "machine", "") or "")
        fabric = (getattr(item, "fabric", None) or "").strip() or "SEM TECIDO"

        job_row_id = getattr(item, "job_row_id", None)
        if job_row_id is not None:
            try:
                persisted_job = repo.get_job_by_row_id(int(job_row_id))
            except Exception:
                persisted_job = None

            if persisted_job is not None:
                end_time = getattr(persisted_job, "end_time", None)
                if not machine:
                    machine = str(getattr(persisted_job, "machine", "") or "")
                persisted_fabric = (getattr(persisted_job, "fabric", None) or "").strip()
                if persisted_fabric:
                    fabric = persisted_fabric

        jobs.append(
            ExportJob(
                job_id=str(getattr(item, "job_id", "") or ""),
                document=str(getattr(item, "document", "") or ""),
                fabric=fabric,
                machine=machine,
                effective_m=float(getattr(item, "effective_printed_length_m", 0.0) or 0.0),
                gap_m=float(getattr(item, "gap_before_m", 0.0) or 0.0),
                consumed_m=float(getattr(item, "consumed_length_m", 0.0) or 0.0),
                review_status=(getattr(item, "review_status", None) or None),
                end_time=end_time,
                job_row_id=int(job_row_id) if job_row_id is not None else None,
            )
        )

    jobs.sort(
        key=lambda job: (
            job.fabric or "",
            job.end_time or datetime.min,
            job.job_id,
        )
    )
    return jobs


def _group_jobs_by_fabric(jobs: list[ExportJob]) -> list[ExportBlock]:
    blocks_map: OrderedDict[str, ExportBlock] = OrderedDict()

    for job in jobs:
        key = (job.fabric or "SEM TECIDO").strip() or "SEM TECIDO"
        if key not in blocks_map:
            blocks_map[key] = ExportBlock(fabric=key)
        blocks_map[key].add_job(job)

    return list(blocks_map.values())


def _has_reportlab() -> bool:
    return canvas is not None and A4 is not None and pdfmetrics is not None


def _has_pdf_render_stack() -> bool:
    return fitz is not None and Image is not None and ImageOps is not None


def _cm_to_px(cm: float, dpi: int) -> int:
    return max(1, int(round((float(cm) / 2.54) * int(dpi))))


def _render_first_page_to_mirrored_jpg(
    *,
    pdf_path: str | Path,
    jpg_path: str | Path,
    target_width_cm: float,
    dpi: int = 300,
    quality: int = 95,
) -> None:
    if not _has_pdf_render_stack():
        raise RuntimeError("Pilha de renderização não disponível para JPG mirror.")

    pdf_path = str(pdf_path)
    jpg_path = str(jpg_path)
    target_width_px = _cm_to_px(target_width_cm, dpi)

    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(0)
        page_width_pt = float(page.rect.width)
        if page_width_pt <= 0:
            raise RuntimeError("Página inválida para renderização.")

        zoom = target_width_px / page_width_pt
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        image = ImageOps.mirror(image)
        image.save(jpg_path, "JPEG", dpi=(dpi, dpi), quality=int(quality))
    finally:
        doc.close()


def _write_pxprintlogs_style_pdf(
    *,
    pdf_path: Path,
    blocks: list[ExportBlock],
    roll_name: str,
    machine: str,
    note: str | None,
) -> None:
    if not _has_reportlab():
        raise RuntimeError("reportlab não está instalado.")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    page_w, page_h = A4
    c = canvas.Canvas(str(pdf_path), pagesize=A4)

    y = page_h - 40
    y = _pdf_draw_header(
        c=c,
        roll_name=roll_name,
        machine=machine,
        mode="summary",
        page_w=page_w,
        top_y=y,
    )
    y = _pdf_draw_summary_table(
        c=c,
        blocks=blocks,
        y=y,
        page_w=page_w,
        page_h=page_h,
        roll_name=roll_name,
        machine=machine,
        mode="summary",
        mirrored=False,
    )

    if note and note.strip():
        if _pdf_need_new_page(y, min_y=110):
            c.showPage()
            y = page_h - 40
            y = _pdf_draw_header(
                c=c,
                roll_name=roll_name,
                machine=machine,
                mode="summary",
                page_w=page_w,
                top_y=y,
            )

        y -= 4
        c.setLineWidth(1)
        c.line(40, y, page_w - 40, y)
        y -= 20

        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Observação")
        y -= 16

        c.setFont("Helvetica", 10)
        for line in _wrap_text(note.strip(), page_w - 80, "Helvetica", 10):
            if _pdf_need_new_page(y, min_y=70):
                c.showPage()
                y = page_h - 40
                y = _pdf_draw_header(
                    c=c,
                    roll_name=roll_name,
                    machine=machine,
                    mode="summary",
                    page_w=page_w,
                    top_y=y,
                )
                c.setFont("Helvetica-Bold", 11)
                c.drawString(40, y, "Observação")
                y -= 16
                c.setFont("Helvetica", 10)

            c.drawString(40, y, line)
            y -= 12

    c.showPage()
    c.save()


def _pdf_need_new_page(y: float, min_y: float = 60) -> bool:
    return y < min_y


def _pdf_draw_header(
    c,
    roll_name: str,
    machine: str,
    mode: str,
    page_w: float,
    top_y: float,
) -> float:
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, top_y, f"Ordem do Rolo - {roll_name}")

    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        top_y - 18,
        (
            f"Máquina: {machine}    "
            f"Modo: {'Completo' if mode == 'full' else 'Resumido'}    "
            f"Gerado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ),
    )

    c.line(40, top_y - 26, page_w - 40, top_y - 26)
    return top_y - 40


def _pdf_draw_summary_table(
    c,
    blocks: list[ExportBlock],
    y: float,
    page_w: float,
    page_h: float,
    roll_name: str,
    machine: str,
    mode: str,
    mirrored: bool,
) -> float:
    w_num = 30
    w_fab = 180
    w_total = 90
    w_jobs = 70
    w_last = 145

    def _reprint_summary_header(y0: float) -> float:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y0, "Resumo (ordem do rolo)")
        y0 -= 16

        c.setFont("Helvetica", 10)
        c.line(40, y0, page_w - 40, y0)
        y0 -= 18

        c.setFont("Helvetica-Bold", 10)
        x = 40
        c.drawString(x, y0, "#")
        x += w_num
        c.drawString(x, y0, "Tecido")
        x += w_fab
        c.drawCentredString(x + (w_total / 2), y0, "Total (m)")
        x += w_total
        c.drawCentredString(x + (w_jobs / 2), y0, "Qtd Pedidos")
        x += w_jobs
        c.drawString(x, y0, "Último fim")
        y0 -= 14

        c.setFont("Helvetica", 10)
        return y0

    y = _reprint_summary_header(y)

    for index, block in enumerate(blocks, start=1):
        if _pdf_need_new_page(y, min_y=85):
            if mirrored:
                c.restoreState()
            c.showPage()
            if mirrored:
                c.saveState()
                c.transform(-1, 0, 0, 1, page_w, 0)

            y = page_h - 40
            y = _pdf_draw_header(c, roll_name, machine, mode, page_w, y)
            y = _reprint_summary_header(y)

        x = 40
        c.drawString(x, y, str(index))
        x += w_num

        c.drawString(x, y, block.fabric)
        x += w_fab

        c.drawCentredString(x + (w_total / 2), y, _fmt_m(block.total_m, suffix=False))
        x += w_total

        c.drawCentredString(x + (w_jobs / 2), y, str(block.job_count))
        x += w_jobs

        c.drawString(x, y, _fmt_dt(block.newest_end))
        y -= 14

    if _pdf_need_new_page(y, min_y=85):
        if mirrored:
            c.restoreState()
        c.showPage()
        if mirrored:
            c.saveState()
            c.transform(-1, 0, 0, 1, page_w, 0)

        y = page_h - 40
        y = _pdf_draw_header(c, roll_name, machine, mode, page_w, y)

    y -= 6
    c.setLineWidth(1)
    c.line(40, y, page_w - 40, y)
    y -= 18

    total_roll = sum(block.total_m for block in blocks)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Total geral do rolo:")
    c.drawRightString(page_w - 40, y, _fmt_m(total_roll))
    c.setFont("Helvetica", 10)
    y -= 18

    return y


def _wrap_text(text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return [""]

    if pdfmetrics is None:
        return [text]

    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"

        if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
            current = test
            continue

        if current:
            lines.append(current)

        if pdfmetrics.stringWidth(word, font_name, font_size) <= max_width:
            current = word
            continue

        chunk = ""
        for ch in word:
            test_chunk = chunk + ch
            if pdfmetrics.stringWidth(test_chunk, font_name, font_size) <= max_width:
                chunk = test_chunk
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        current = chunk

    if current:
        lines.append(current)

    return lines


def _write_fallback_pdf(path: Path, lines: list[str]) -> None:
    content_ops = ["BT", "/F1 11 Tf", "40 800 Td"]

    for index, line in enumerate(lines):
        if index > 0:
            content_ops.append("0 -16 Td")
        content_ops.append(f"({_pdf_escape(line)}) Tj")

    content_ops.append("ET")
    content_stream = "\n".join(content_ops).encode("latin-1", errors="replace")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
        + content_stream
        + b"\nendstream",
    ]

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")
    )

    path.write_bytes(bytes(pdf))


def _write_fallback_summary_jpg(path: Path, lines: list[str], mirrored: bool = False) -> None:
    if Image is None or ImageDraw is None:
        path.write_bytes(base64.b64decode(_TINY_JPEG_BASE64))
        return

    width = 1600
    line_height = 28
    padding = 32
    height = max(300, padding * 2 + line_height * len(lines))

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    y = padding
    for line in lines:
        draw.text((padding, y), line, fill="black")
        y += line_height

    if mirrored and ImageOps is not None:
        image = ImageOps.mirror(image)

    image.save(path, format="JPEG", quality=92)


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _sanitize_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_")
    return cleaned or "roll_export"


def _round_up_cm_m(m: float) -> float:
    try:
        value = float(m)
    except Exception:
        return 0.0
    if value <= 0:
        return 0.0
    return math.ceil(value * 100.0) / 100.0


def _fmt_m(value: float, *, suffix: bool = True) -> str:
    display = f"{_round_up_cm_m(value):.2f}"
    return f"{display} m" if suffix else display


def _fmt_efficiency(value: float | None) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"


def _fmt_dt(value: object) -> str:
    if value is None:
        return "-"
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return str(value)
    return str(value)


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None