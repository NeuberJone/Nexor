# Arquivo: exports/roll_export_service.py
#
# Resumo do que este arquivo implementa:
# - valida se o rolo pode ser exportado
# - monta um payload único para PDF/JPG
# - inclui eficiência, datas e observação no resumo exportado
# - mantém fallback para JPG simples caso Pillow não esteja disponível
# - continua marcando o rolo como EXPORTED após exportar

from __future__ import annotations

import base64
from pathlib import Path

from core.models import ROLL_CLOSED, ROLL_EXPORTED, ROLL_REVIEWED
from storage.repository import ProductionRepository


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


def export_closed_roll(
    *,
    roll_id: int,
    output_dir: str | Path,
    repository: ProductionRepository | None = None,
) -> dict:
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

    payload = _build_export_payload(summary)

    _write_simple_pdf(pdf_path, payload["lines"])
    _write_jpg_summary(jpg_path, payload["lines"])

    repo.mark_roll_exported(roll_id)
    exported_roll = repo.get_roll(roll_id=roll_id)

    return {
        "roll_id": roll_id,
        "roll_name": roll.roll_name,
        "pdf_path": str(pdf_path),
        "jpg_path": str(jpg_path),
        "jobs_count": payload["jobs_count"],
        "total_planned_m": payload["total_planned_m"],
        "total_effective_m": payload["total_effective_m"],
        "total_gap_m": payload["total_gap_m"],
        "total_consumed_m": payload["total_consumed_m"],
        "efficiency_ratio": payload["efficiency_ratio"],
        "status": exported_roll.status if exported_roll else ROLL_EXPORTED,
    }


def _build_export_payload(summary: dict) -> dict:
    roll = summary["roll"]
    items = summary["items"]

    jobs_count = int(summary["jobs_count"] or 0)
    total_planned_m = float(summary["total_planned_m"] or 0.0)
    total_effective_m = float(summary["total_effective_m"] or 0.0)
    total_gap_m = float(summary["total_gap_m"] or 0.0)
    total_consumed_m = float(summary["total_consumed_m"] or 0.0)
    efficiency_ratio = summary.get("efficiency_ratio")
    note = getattr(roll, "note", None)

    lines = [
        "Nexor Roll Export",
        f"Roll: {roll.roll_name}",
        f"Machine: {roll.machine}",
        f"Fabric: {roll.fabric or '-'}",
        f"Status: {roll.status}",
        f"Created at: {_fmt_dt(getattr(roll, 'created_at', None))}",
        f"Closed at: {_fmt_dt(getattr(roll, 'closed_at', None))}",
        f"Exported at: {_fmt_dt(getattr(roll, 'exported_at', None))}",
        f"Jobs: {jobs_count}",
        f"Total planned (m): {_fmt_m(total_planned_m)}",
        f"Total effective (m): {_fmt_m(total_effective_m)}",
        f"Total gap (m): {_fmt_m(total_gap_m)}",
        f"Total consumed (m): {_fmt_m(total_consumed_m)}",
        f"Efficiency: {_fmt_efficiency(efficiency_ratio)}",
        f"Note: {note or '-'}",
        "",
        "Items:",
    ]

    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index:02d}. {item.job_id} | {item.document} | "
            f"rev={getattr(item, 'review_status', '-') or '-'} | "
            f"eff={_fmt_m(item.effective_printed_length_m)}m | "
            f"gap={_fmt_m(item.gap_before_m)}m | "
            f"cons={_fmt_m(item.consumed_length_m)}m"
        )

    return {
        "lines": lines,
        "jobs_count": jobs_count,
        "total_planned_m": total_planned_m,
        "total_effective_m": total_effective_m,
        "total_gap_m": total_gap_m,
        "total_consumed_m": total_consumed_m,
        "efficiency_ratio": efficiency_ratio,
    }


def _fmt_m(value: float) -> str:
    return f"{float(value or 0.0):.3f}"


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
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value)
    return str(value)


def _sanitize_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_")
    return cleaned or "roll_export"


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
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


def _write_jpg_summary(path: Path, lines: list[str]) -> None:
    try:
        from PIL import Image, ImageDraw  # type: ignore

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

        image.save(path, format="JPEG", quality=92)
        return
    except Exception:
        pass

    path.write_bytes(base64.b64decode(_TINY_JPEG_BASE64))