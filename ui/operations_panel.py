import json
import math
import os
import re
import tkinter as tk
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from tkinter import filedialog, messagebox, ttk

APP_VERSION = "NEXOR-DEV"
MODULE_NAME = "PXPrintLogs"

STATUS_PENDING = "PENDING_REVIEW"
STATUS_OK = "PRINTED_OK"
STATUS_PARTIAL = "PARTIAL"
STATUS_ABORTED = "ABORTED"
STATUS_REPRINT = "REPRINT"
STATUS_IGNORED = "IGNORED"

STATUS_OPTIONS = [
    STATUS_PENDING,
    STATUS_OK,
    STATUS_PARTIAL,
    STATUS_ABORTED,
    STATUS_REPRINT,
    STATUS_IGNORED,
]


# ---- PDF (reportlab) ----
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas
except Exception:
    A4 = None
    pdfmetrics = None
    canvas = None


# ---- JPG (PyMuPDF) ----
try:
    import fitz  # PyMuPDF

    _HAS_PYMUPDF = True
except Exception:
    fitz = None
    _HAS_PYMUPDF = False


# ---- Drag & drop (tkinterdnd2) ----
try:
    from tkinterdnd2 import DND_FILES  # type: ignore

    _HAS_DND = True
except Exception:
    DND_FILES = None
    _HAS_DND = False


# ---- JPG export (Pillow) ----
try:
    from PIL import Image

    _HAS_PIL = True
except Exception:
    Image = None
    _HAS_PIL = False


# --------------------------
# Base dirs / config
# --------------------------
def _nexor_base_dir() -> Path:
    env = os.environ.get("NEXOR_BASE_DIR", "").strip()
    base_dir = Path(env) if env else (Path.home() / "NexorData")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _ym(dt: datetime) -> tuple[str, str]:
    return f"{dt.year:04d}", f"{dt.month:02d}"


def _default_pdf_export_dir() -> Path:
    y, m = _ym(datetime.now())
    out = _nexor_base_dir() / "pdf" / MODULE_NAME / "rolls" / y / m
    out.mkdir(parents=True, exist_ok=True)
    return out


def _default_mirror_jpg_export_dir() -> Path:
    y, m = _ym(datetime.now())
    out = _nexor_base_dir() / "print" / MODULE_NAME / "jpg" / y / m
    out.mkdir(parents=True, exist_ok=True)
    return out


def _default_summary_jpg_export_dir() -> Path:
    out = _nexor_base_dir() / "print" / MODULE_NAME / "resumo"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _temp_dir() -> Path:
    out = _nexor_base_dir() / "temp" / MODULE_NAME
    out.mkdir(parents=True, exist_ok=True)
    return out


APP_DIR = Path(os.environ.get("APPDATA") or str(Path.home())) / "Nexor" / "PXPrintLogs"
APP_DIR.mkdir(parents=True, exist_ok=True)
CFG_PATH = APP_DIR / "config.json"
OVERRIDES_PATH = APP_DIR / "job_overrides.json"
FABRICS_PATH = APP_DIR / "fabrics.json"

DEFAULT_CFG = {
    "mirror_jpg_width_mode": "17",
    "mirror_jpg_width_cm_custom": 17.0,
    "mirror_jpg_dpi": 300,
    "pdf_export_enabled": True,
    "mirror_jpg_export_enabled": True,
    "summary_jpg_export_enabled": True,
    "pdf_export_dir": str(_default_pdf_export_dir()),
    "mirror_jpg_export_dir": str(_default_mirror_jpg_export_dir()),
    "summary_jpg_export_dir": str(_default_summary_jpg_export_dir()),
}


def load_cfg() -> dict:
    if CFG_PATH.exists():
        try:
            data = json.loads(CFG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {**DEFAULT_CFG, **data}
        except Exception:
            pass
    return dict(DEFAULT_CFG)


def save_cfg(cfg: dict) -> None:
    try:
        CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_job_overrides() -> dict:
    if OVERRIDES_PATH.exists():
        try:
            data = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_job_overrides(data: dict) -> None:
    try:
        OVERRIDES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _job_override_key(src_file: str) -> str:
    try:
        return str(Path(src_file).resolve()).lower()
    except Exception:
        return str(src_file).strip().lower()


# --------------------------
# Fabrics / aliases
# --------------------------
def _default_fabrics() -> Dict[str, List[str]]:
    return {
        "Dryfit": ["dryfit", "dry fit", "dry-fit", "drifit"],
        "Ribana": ["ribana"],
        "Elastano": ["elastano"],
        "Poliamida": ["poliamida"],
        "Crepe": ["crepe"],
        "Malha": ["malha"],
        "Helanca": ["helanca"],
        "Tactel": ["tactel"],
        "Microfibra": ["microfibra"],
        "Aeroready": ["aeroready", "aero ready", "aero-ready"],
        "Oxford": ["oxford"],
        "Faixa de Capitão": ["faixa de capitão", "faixa cap"],
        "DryX": ["dryx", "dry x"],
        "Jaquard Corinthians": ["corinthians"],
        "Telinha": ["telinha"],
    }


def load_fabrics() -> Dict[str, List[str]]:
    if FABRICS_PATH.exists():
        try:
            data = json.loads(FABRICS_PATH.read_text(encoding="utf-8"))
            out: Dict[str, List[str]] = {}
            if isinstance(data, dict):
                for canonical, aliases in data.items():
                    if not isinstance(canonical, str):
                        continue
                    if isinstance(aliases, list):
                        out[canonical] = [str(x).strip() for x in aliases if str(x).strip()]
                    else:
                        out[canonical] = []
            if out:
                return out
        except Exception:
            pass
    data = _default_fabrics()
    save_fabrics(data)
    return data


def save_fabrics(data: Dict[str, List[str]]) -> None:
    try:
        FABRICS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)
    )


def _normalize_name(text: str) -> str:
    text = _strip_accents((text or "").lower())
    text = text.replace("_", " ")
    text = text.replace(".", " ")
    text = text.replace("/", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_fabric_alias_index(fabrics_map: Dict[str, List[str]]) -> Dict[str, str]:
    alias_index: Dict[str, str] = {}
    for canonical, aliases in fabrics_map.items():
        alias_index[_normalize_name(canonical)] = canonical
        for alias in aliases:
            alias_norm = _normalize_name(alias)
            if alias_norm:
                alias_index[alias_norm] = canonical
    return alias_index


def infer_fabric_from_text(text: str, fabrics_map: Dict[str, List[str]]) -> str:
    alias_index = _build_fabric_alias_index(fabrics_map)
    candidates = []

    parts = _split_document_parts(text)
    if len(parts) >= 2:
        candidates.append(parts[1])
    if len(parts) >= 3:
        candidates.append(parts[2])
    candidates.append(text)

    for candidate in candidates:
        norm = _normalize_name(candidate)
        if not norm:
            continue
        if norm in alias_index:
            return alias_index[norm]
        for alias, canonical in alias_index.items():
            if alias and alias in norm:
                return canonical

    return "DESCONHECIDO"


# --------------------------
# Domain models
# --------------------------
@dataclass
class Job:
    end_time: datetime
    document: str
    fabric: str
    original_fabric: str
    height_mm: float
    vpos_mm: float
    real_mm: float
    src_file: str
    expected_mm: Optional[float] = None
    print_status: str = STATUS_PENDING
    review_note: str = ""
    auto_reason: str = ""

    @property
    def real_m(self) -> float:
        return self.real_mm / 1000.0

    @property
    def printed_percent(self) -> Optional[float]:
        if self.expected_mm is None:
            return None
        try:
            expected = float(self.expected_mm)
        except Exception:
            return None
        if expected <= 0:
            return None
        pct = (float(self.real_mm) / expected) * 100.0
        if pct < 0:
            return 0.0
        return min(pct, 100.0)

    @property
    def counts_in_media_totals(self) -> bool:
        return self.print_status in {STATUS_OK, STATUS_PARTIAL, STATUS_ABORTED, STATUS_REPRINT}

    @property
    def counts_in_production_totals(self) -> bool:
        return self.print_status == STATUS_OK

    @property
    def is_visible(self) -> bool:
        return self.print_status != STATUS_IGNORED


@dataclass
class Block:
    fabric: str
    machine: str
    jobs: List[Job]

    @property
    def total_m(self) -> float:
        return sum(j.real_m for j in self.jobs if j.counts_in_media_totals)

    @property
    def production_m(self) -> float:
        return sum(j.real_m for j in self.jobs if j.counts_in_production_totals)

    @property
    def job_count(self) -> int:
        return len(self.jobs)

    @property
    def newest_end(self) -> datetime:
        return max(j.end_time for j in self.jobs)

    @property
    def oldest_end(self) -> datetime:
        return min(j.end_time for j in self.jobs)

    def count_status(self, status: str) -> int:
        return sum(1 for j in self.jobs if j.print_status == status)


# --------------------------
# Parsing helpers
# --------------------------
_RE_KV = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$")
_RE_SECTION = re.compile(r"^\s*\[(.+?)\]\s*$")


def _parse_datetime(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def _normalize_document_for_parse(doc: str) -> str:
    text = re.sub(r"\s+", " ", (doc or "").strip())
    m = re.match(r"^(\d{2}-\d{2})\s*-\s*(.+)$", text)
    if m:
        return f"{m.group(1)} - {m.group(2).strip()}"
    return text


def _split_document_parts(doc: str) -> List[str]:
    text = _normalize_document_for_parse(doc)
    m = re.match(r"^(\d{2}-\d{2})\s*-\s*(.+)$", text)
    if not m:
        return [p.strip() for p in re.split(r"\s+-\s+", text) if p.strip()]

    first = m.group(1).strip()
    rest = m.group(2).strip()
    rest_parts = [p.strip() for p in re.split(r"\s*-\s*", rest, maxsplit=1) if p.strip()]
    return [first, *rest_parts]


def _classify_job_status(document: str, src_file: str, expected_mm: float, printed_mm: float) -> tuple[str, str]:
    text = _normalize_name(f"{document} {Path(src_file).name}")

    if any(k in text for k in ["abortado", "aborted", "cancelado", "cancelled", "cancel", "falhou", "failed"]):
        return STATUS_ABORTED, "Status sugerido por palavra-chave no nome do arquivo/documento."

    if any(k in text for k in ["reimpress", "re-print", "reprint"]):
        return STATUS_REPRINT, "Status sugerido por palavra-chave de reimpressão."

    expected = max(float(expected_mm or 0.0), 0.0)
    printed = max(float(printed_mm or 0.0), 0.0)

    if expected <= 0:
        return STATUS_PENDING, "Sem comprimento esperado confiável; revisar entrada."

    ratio = printed / expected if expected > 0 else None
    missing_mm = max(expected - printed, 0.0)

    if expected < 300:
        return STATUS_OK, ""

    if printed <= 50 or (ratio is not None and ratio <= 0.05):
        return STATUS_ABORTED, "Impressão efetiva muito baixa em relação ao tamanho esperado."

    if ratio is not None and ratio < 0.98 and missing_mm >= 200:
        pct = ratio * 100.0
        return STATUS_PARTIAL, f"Impressão parcial detectada automaticamente ({pct:.1f}% do esperado)."

    return STATUS_OK, ""


def parse_log_txt(path: str, fabrics_map: Dict[str, List[str]]) -> Optional[Job]:
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None

    section = None
    general = {}
    item1 = {}
    costs = {}

    for line in txt:
        msec = _RE_SECTION.match(line)
        if msec:
            section = msec.group(1).strip()
            continue

        mkv = _RE_KV.match(line)
        if not mkv:
            continue

        k, v = mkv.group(1).strip(), mkv.group(2).strip()
        if section == "General":
            general[k] = v
        elif section == "1":
            item1[k] = v
        elif section == "Costs":
            costs[k] = v

    end_dt = _parse_datetime(general.get("EndTime", ""))
    if not end_dt:
        return None

    document = general.get("Document") or item1.get("Name") or Path(path).stem

    def _f(x: str) -> float:
        x = (x or "").strip().replace(",", ".")
        try:
            return float(x)
        except Exception:
            return 0.0

    expected_mm = _f(item1.get("HeightMM", "0"))
    vpos_mm = _f(item1.get("VPositionMM", item1.get("VPosMM", "0")))
    costs_print_height_mm = _f(costs.get("PrintHeightMM", "0"))

    if expected_mm <= 0 and costs_print_height_mm > 0:
        expected_mm = costs_print_height_mm

    real_mm = costs_print_height_mm if costs_print_height_mm > 0 else expected_mm
    height_mm = expected_mm

    fabric = infer_fabric_from_text(document, fabrics_map)
    status, reason = _classify_job_status(document, path, expected_mm, real_mm)

    return Job(
        end_time=end_dt,
        document=document,
        fabric=fabric,
        original_fabric=fabric,
        height_mm=height_mm,
        vpos_mm=vpos_mm,
        real_mm=real_mm,
        src_file=str(path),
        expected_mm=expected_mm if expected_mm > 0 else None,
        print_status=status,
        auto_reason=reason,
    )


def build_blocks(jobs: List[Job], machine: str) -> List[Block]:
    visible = [j for j in jobs if j.is_visible]
    jobs_sorted = sorted(visible, key=lambda j: j.end_time, reverse=True)

    blocks: List[Block] = []
    current_jobs: List[Job] = []
    current_fabric: Optional[str] = None

    for j in jobs_sorted:
        if current_fabric is None:
            current_fabric = j.fabric
            current_jobs = [j]
            continue

        if j.fabric == current_fabric:
            current_jobs.append(j)
        else:
            blocks.append(Block(fabric=current_fabric, machine=machine, jobs=current_jobs))
            current_fabric = j.fabric
            current_jobs = [j]

    if current_fabric is not None and current_jobs:
        blocks.append(Block(fabric=current_fabric, machine=machine, jobs=current_jobs))

    return blocks


# --------------------------
# General helpers
# --------------------------
def _round_up_cm(value_m: float) -> float:
    return math.ceil(value_m * 100) / 100 if value_m > 0 else 0.0


def fmt_m(value_m: float, suffix: bool = True) -> str:
    rounded = _round_up_cm(float(value_m or 0.0))
    return f"{rounded:.2f} m" if suffix else f"{rounded:.2f}"


def _versioned_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    m = re.search(r"_v(\d+)$", stem, flags=re.IGNORECASE)
    base = stem[: m.start()] if m else stem

    n = 2
    while True:
        cand = path.with_name(f"{base}_v{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def _sanitize_filename(name: str) -> str:
    bad = r'\\/:*?"<>|'
    for ch in bad:
        name = name.replace(ch, "_")
    name = re.sub(r"\s+", " ", name).strip()
    return name


# --------------------------
# JPG helpers
# --------------------------
def pdf_first_page_to_jpg_scaled(
    pdf_path: str,
    jpg_path: str,
    *,
    target_width_cm: float,
    dpi: int = 300,
    quality: int = 95,
) -> None:
    if not _HAS_PYMUPDF:
        raise RuntimeError("PyMuPDF não instalado. Instale: pip install pymupdf")
    if not _HAS_PIL:
        raise RuntimeError("Pillow não instalado. Instale: pip install pillow")

    width_in = float(target_width_cm) / 2.54
    target_width_px = int(round(width_in * dpi))

    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(0)
        page_width_pt = float(page.rect.width)
        zoom = target_width_px / page_width_pt
        mat = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.save(jpg_path, "JPEG", dpi=(dpi, dpi), quality=int(quality))
    finally:
        doc.close()


# --------------------------
# PDF helpers
# --------------------------
def _pdf_need_new_page(y: float, min_y: float = 60) -> bool:
    return y < min_y


def _wrap_text(text: str, max_width: float, font_name: str, font_size: int) -> List[str]:
    text = (text or "").strip()
    if not text:
        return [""]

    if pdfmetrics is None:
        return [text]

    words = text.split()
    lines: List[str] = []
    current = ""

    for w in words:
        test = w if not current else f"{current} {w}"
        if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            if pdfmetrics.stringWidth(w, font_name, font_size) <= max_width:
                current = w
            else:
                chunk = ""
                for ch in w:
                    test2 = chunk + ch
                    if pdfmetrics.stringWidth(test2, font_name, font_size) <= max_width:
                        chunk = test2
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                current = chunk

    if current:
        lines.append(current)
    return lines


def _draw_wrapped_cell(c, x: float, y_top: float, lines: List[str], font_name: str, font_size: int, line_h: float):
    c.setFont(font_name, font_size)
    yy = y_top
    for line in lines:
        c.drawString(x, yy, line)
        yy -= line_h


def _media_total_m(jobs: List[Job]) -> float:
    return sum(j.real_m for j in jobs if j.counts_in_media_totals)


def export_pdf(
    out_path: str,
    jobs: List[Job],
    blocks: List[Block],
    roll_name: str,
    machine: str,
    mirrored: bool = False,
) -> None:
    if canvas is None or A4 is None:
        raise RuntimeError("reportlab não está instalado. Instale: pip install reportlab")

    page_w, page_h = A4
    c = canvas.Canvas(out_path, pagesize=A4)

    def _begin_page():
        if mirrored:
            c.saveState()
            c.transform(-1, 0, 0, 1, page_w, 0)

    def _end_page():
        if mirrored:
            c.restoreState()
        c.showPage()

    def draw_header(y_top: float) -> float:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y_top, f"Ordem do Rolo - {roll_name}")
        c.setFont("Helvetica", 10)
        c.drawString(
            40,
            y_top - 18,
            f"Máquina: {machine}    Modo: Completo    Gerado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        )
        c.line(40, y_top - 26, page_w - 40, y_top - 26)
        return y_top - 40

    y = page_h - 40
    _begin_page()
    y = draw_header(y)

    # Lista detalhada
    w_end = 118
    w_status = 82
    w_doc = 195
    w_fab = 80
    w_size = 40

    def draw_jobs_header(y0: float) -> float:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y0, "Entradas do log")
        y0 -= 16
        c.setFont("Helvetica", 10)
        c.line(40, y0, page_w - 40, y0)
        y0 -= 18

        c.setFont("Helvetica-Bold", 9)
        x = 40
        c.drawString(x, y0, "EndTime")
        x += w_end
        c.drawString(x, y0, "Status")
        x += w_status
        c.drawString(x, y0, "Documento")
        x += w_doc
        c.drawString(x, y0, "Tecido")
        x += w_fab
        c.drawString(x, y0, "Real")
        y0 -= 14
        c.setFont("Helvetica", 9)
        return y0

    y = draw_jobs_header(y)
    line_h = 11

    for j in sorted([x for x in jobs if x.is_visible], key=lambda jj: jj.end_time, reverse=True):
        end_txt = j.end_time.strftime("%d/%m/%Y %H:%M:%S")
        doc_lines = _wrap_text(j.document, w_doc - 6, "Helvetica", 9)
        fab_lines = _wrap_text(j.fabric, w_fab - 6, "Helvetica", 9)
        row_lines = max(len(doc_lines), len(fab_lines), 1)
        row_h = row_lines * line_h

        if _pdf_need_new_page(y - row_h, min_y=110):
            _end_page()
            _begin_page()
            y = page_h - 40
            y = draw_header(y)
            y = draw_jobs_header(y)

        x0 = 40
        c.setFont("Helvetica", 9)
        c.drawString(x0, y, end_txt)
        c.drawString(x0 + w_end, y, j.print_status)
        _draw_wrapped_cell(c, x0 + w_end + w_status, y, doc_lines, "Helvetica", 9, line_h)
        _draw_wrapped_cell(c, x0 + w_end + w_status + w_doc, y, fab_lines, "Helvetica", 9, line_h)
        c.drawRightString(x0 + w_end + w_status + w_doc + w_fab + w_size - 2, y, fmt_m(j.real_m))
        y -= row_h

    y -= 8
    if _pdf_need_new_page(y, min_y=120):
        _end_page()
        _begin_page()
        y = page_h - 40
        y = draw_header(y)

    c.setLineWidth(1.4)
    c.line(40, y, page_w - 40, y)
    y -= 22

    # Resumo por bloco
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Resumo por bloco")
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "#")
    c.drawString(70, y, "Tecido")
    c.drawRightString(330, y, "Mídia")
    c.drawRightString(415, y, "Produção")
    c.drawRightString(485, y, "Itens")
    c.drawString(505, y, "Último fim")
    y -= 14
    c.setFont("Helvetica", 10)

    for i, b in enumerate(blocks, start=1):
        if _pdf_need_new_page(y, min_y=95):
            _end_page()
            _begin_page()
            y = page_h - 40
            y = draw_header(y)

        c.drawString(40, y, str(i))
        c.drawString(70, y, b.fabric)
        c.drawRightString(330, y, fmt_m(b.total_m))
        c.drawRightString(415, y, fmt_m(b.production_m))
        c.drawRightString(485, y, str(b.job_count))
        c.drawString(505, y, b.newest_end.strftime("%d/%m/%Y %H:%M:%S"))
        y -= 14

    y -= 6
    c.setLineWidth(1)
    c.line(40, y, page_w - 40, y)
    y -= 18

    media_total = _media_total_m(jobs)
    production_total = sum(j.real_m for j in jobs if j.counts_in_production_totals)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Total mídia: {fmt_m(media_total)}")
    y -= 16
    c.drawString(40, y, f"Total produção válida: {fmt_m(production_total)}")
    y -= 16
    c.drawString(40, y, f"OK: {sum(1 for j in jobs if j.print_status == STATUS_OK)}")
    c.drawString(170, y, f"Revisão: {sum(1 for j in jobs if j.print_status == STATUS_PENDING)}")
    c.drawString(320, y, f"Parcial: {sum(1 for j in jobs if j.print_status == STATUS_PARTIAL)}")
    c.drawString(450, y, f"Abortado: {sum(1 for j in jobs if j.print_status == STATUS_ABORTED)}")

    _end_page()
    c.save()


# --------------------------
# UI
# --------------------------
class OperationsPanel(ttk.Frame):
    def __init__(self, parent, service=None):
        super().__init__(parent)
        self.service = service

        self.mcfg = load_cfg()
        self.job_overrides = load_job_overrides()
        self.fabrics_map = load_fabrics()

        self.machine: Optional[str] = None
        self.jobs: List[Job] = []
        self.blocks: List[Block] = []
        self.detail_job_map: dict[str, Job] = {}

        self.var_jpg_mode = tk.StringVar(value=self.mcfg.get("mirror_jpg_width_mode", "17"))
        self.var_jpg_custom = tk.StringVar(value=str(self.mcfg.get("mirror_jpg_width_cm_custom", 17.0)))

        self.var_pdf_dir = tk.StringVar(value=self.mcfg.get("pdf_export_dir", str(_default_pdf_export_dir())))
        self.var_mirror_dir = tk.StringVar(value=self.mcfg.get("mirror_jpg_export_dir", str(_default_mirror_jpg_export_dir())))
        self.var_summary_dir = tk.StringVar(value=self.mcfg.get("summary_jpg_export_dir", str(_default_summary_jpg_export_dir())))

        self.var_export_pdf = tk.BooleanVar(value=bool(self.mcfg.get("pdf_export_enabled", True)))
        self.var_export_mirror = tk.BooleanVar(value=bool(self.mcfg.get("mirror_jpg_export_enabled", True)))
        self.var_export_summary = tk.BooleanVar(value=bool(self.mcfg.get("summary_jpg_export_enabled", True)))

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Nome do rolo").grid(row=0, column=0, sticky="w")
        self.var_roll = tk.StringVar(value="")
        ttk.Entry(top, textvariable=self.var_roll, width=28).grid(row=0, column=1, padx=(6, 6), sticky="w")
        ttk.Button(top, text="Atualizar nome", command=self.on_refresh_roll_name).grid(row=0, column=2, padx=(0, 12), sticky="w")

        self.lbl_machine = ttk.Label(top, text="Máquina do lote: (não definida)")
        self.lbl_machine.grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))

        btns = ttk.Frame(top)
        btns.grid(row=1, column=4, columnspan=3, sticky="e", pady=(6, 0))

        row_actions = ttk.Frame(btns)
        row_actions.pack(anchor="e")
        ttk.Button(row_actions, text="Importar logs", command=self.on_import_files).pack(side="left", padx=4)
        ttk.Button(row_actions, text="Importar pasta", command=self.on_import_folder).pack(side="left", padx=4)
        ttk.Button(row_actions, text="Tecidos...", command=self.open_fabrics_dialog).pack(side="left", padx=4)
        ttk.Button(row_actions, text="Exportação...", command=self.open_export_dialog).pack(side="left", padx=4)
        ttk.Button(row_actions, text="Limpar", command=self.on_clear).pack(side="left", padx=4)

        drop_frame = ttk.LabelFrame(self, text="Arraste e solte logs .txt aqui")
        drop_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.drop_label = ttk.Label(drop_frame, text="Solte arquivos .txt (apenas) para importar")
        self.drop_label.pack(fill="x", padx=10, pady=12)

        if _HAS_DND:
            try:
                self.drop_label.drop_target_register(DND_FILES)  # type: ignore
                self.drop_label.dnd_bind("<<Drop>>", self.on_drop_files)  # type: ignore
            except Exception:
                pass
        else:
            self.drop_label.configure(text="Drag & Drop indisponível (tkinterdnd2 não carregou). Use o botão Importar.")

        details = ttk.LabelFrame(self, text="Detalhes da entrada selecionada")
        details.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        self.var_detail_title = tk.StringVar(value="Selecione um bloco e uma entrada abaixo...")
        details_header = ttk.Frame(details)
        details_header.pack(fill="x", padx=10, pady=(8, 6))
        ttk.Label(details_header, textvariable=self.var_detail_title).pack(side="left", anchor="w")
        ttk.Button(details_header, text="Editar entrada", command=self.on_edit_selected_job).pack(side="right")

        self.tree_jobs = ttk.Treeview(
            details,
            columns=("end", "status", "pct", "doc", "fabric", "h", "v", "real_m", "src"),
            show="headings",
            height=7,
        )
        for col, txt, w, anchor in [
            ("end", "EndTime", 145, "w"),
            ("status", "Status", 115, "w"),
            ("pct", "% impresso", 90, "e"),
            ("doc", "Documento", 250, "w"),
            ("fabric", "Tecido", 120, "w"),
            ("h", "HeightMM", 90, "e"),
            ("v", "VPosMM", 90, "e"),
            ("real_m", "Real (m)", 85, "e"),
            ("src", "Arquivo", 210, "w"),
        ]:
            self.tree_jobs.heading(col, text=txt)
            self.tree_jobs.column(col, width=w, anchor=anchor)
        sbj = ttk.Scrollbar(details, orient="vertical", command=self.tree_jobs.yview)
        self.tree_jobs.configure(yscrollcommand=sbj.set)
        self.tree_jobs.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        sbj.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        self.tree_jobs.bind("<Double-1>", self.on_edit_selected_job)

        blocks_box = ttk.LabelFrame(self, text="Blocos por tecido (último impresso primeiro)")
        blocks_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree_blocks = ttk.Treeview(
            blocks_box,
            columns=("#", "alert", "fabric", "media_m", "prod_m", "jobs", "ok", "review", "last"),
            show="headings",
            height=12,
        )
        for col, txt, w, anchor in [
            ("#", "#", 36, "center"),
            ("alert", "Alerta", 85, "center"),
            ("fabric", "Tecido", 150, "w"),
            ("media_m", "Mídia (m)", 95, "e"),
            ("prod_m", "Produção (m)", 105, "e"),
            ("jobs", "Entradas", 70, "e"),
            ("ok", "OK", 55, "e"),
            ("review", "Revisão", 70, "e"),
            ("last", "Último EndTime", 155, "w"),
        ]:
            self.tree_blocks.heading(col, text=txt)
            self.tree_blocks.column(col, width=w, anchor=anchor)
        sbb = ttk.Scrollbar(blocks_box, orient="vertical", command=self.tree_blocks.yview)
        self.tree_blocks.configure(yscrollcommand=sbb.set)
        self.tree_blocks.pack(side="left", fill="both", expand=True)
        sbb.pack(side="right", fill="y")
        self.tree_blocks.bind("<<TreeviewSelect>>", self.on_select_block)

        self.tree_blocks.tag_configure("needs_review", background="#fff4cc")
        self.tree_blocks.tag_configure("has_partial", background="#fde2c8")
        self.tree_blocks.tag_configure("has_aborted", background="#f8d7da")

        self.tree_jobs.tag_configure("pending_review", background="#fff4cc")
        self.tree_jobs.tag_configure("partial", background="#fde2c8")
        self.tree_jobs.tag_configure("aborted", background="#f8d7da")

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        self.lbl_summary = ttk.Label(footer, text="Mídia: 0.00 m | Produção: 0.00 m | OK: 0 | Revisão: 0 | Abortado: 0")
        self.lbl_summary.pack(side="left")
        self.status = ttk.Label(footer, text="Pronto.")
        self.status.pack(side="right")

    # --------------------------
    # Export dialog
    # --------------------------
    def open_export_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Exportação")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)

        container = ttk.Frame(dlg, padding=12)
        container.pack(fill="both", expand=True)

        cfg_box = ttk.LabelFrame(container, text="Configurações de exportação", padding=10)
        cfg_box.pack(fill="x")
        ttk.Label(cfg_box, text="Largura do JPG espelhado").grid(row=0, column=0, sticky="w")

        def update_custom_state():
            ent_custom.configure(state=("normal" if self.var_jpg_mode.get() == "custom" else "disabled"))

        ttk.Radiobutton(cfg_box, text="17 cm", value="17", variable=self.var_jpg_mode, command=update_custom_state).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Radiobutton(cfg_box, text="21 cm", value="21", variable=self.var_jpg_mode, command=update_custom_state).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(6, 0))
        ttk.Radiobutton(cfg_box, text="Personalizado", value="custom", variable=self.var_jpg_mode, command=update_custom_state).grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        ent_custom = ttk.Entry(cfg_box, textvariable=self.var_jpg_custom, width=8)
        ent_custom.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Label(cfg_box, text="cm").grid(row=1, column=4, sticky="w", padx=(4, 0), pady=(6, 0))
        update_custom_state()

        outputs_box = ttk.LabelFrame(container, text="Arquivos para exportação", padding=10)
        outputs_box.pack(fill="x", pady=(10, 0))
        ttk.Label(outputs_box, text="O PDF é sempre completo.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self._build_export_row(outputs_box, 1, self.var_export_pdf, "PDF", self.var_pdf_dir)
        self._build_export_row(outputs_box, 2, self.var_export_mirror, "JPG espelhado", self.var_mirror_dir)
        self._build_export_row(outputs_box, 3, self.var_export_summary, "JPG resumo", self.var_summary_dir)
        ttk.Label(outputs_box, text=f"Nome fixo do resumo: {self._summary_jpg_filename_preview()}").grid(row=4, column=0, columnspan=5, sticky="w", pady=(8, 0))

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="Salvar configurações", command=lambda: self.save_export_settings(show_message=True)).pack(side="left")
        ttk.Button(footer, text="Exportar selecionados", command=lambda: self.on_export_selected(dialog=dlg)).pack(side="right")
        ttk.Button(footer, text="Fechar", command=dlg.destroy).pack(side="right", padx=(0, 6))

    def _build_export_row(self, master, row: int, check_var, label: str, path_var):
        ttk.Checkbutton(master, variable=check_var).grid(row=row, column=0, sticky="w")
        ttk.Label(master, text=label).grid(row=row, column=1, sticky="w", padx=(4, 8))
        ttk.Entry(master, textvariable=path_var, width=52).grid(row=row, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(master, text="Escolher", command=lambda var=path_var: self.on_choose_dir(var)).grid(row=row, column=3, padx=(0, 6))
        ttk.Button(master, text="Abrir", command=lambda var=path_var: self.on_open_dir(var)).grid(row=row, column=4)

    # --------------------------
    # Config helpers
    # --------------------------
    def _machine_code(self) -> str:
        text = (self.machine or "").strip().upper()
        return text or "M?"

    def _summary_jpg_filename_preview(self) -> str:
        return f"Resumo de Impressão - {self._machine_code()}.jpg"

    def _summary_jpg_filename(self) -> str:
        return f"Resumo de Impressão - {self._machine_code()}.jpg"

    def on_choose_dir(self, target_var):
        initial = (target_var.get() or "").strip()
        folder = filedialog.askdirectory(title="Selecionar pasta", initialdir=initial if initial else str(Path.home()))
        if folder:
            target_var.set(folder)

    def on_open_dir(self, target_var):
        try:
            folder = Path((target_var.get() or "").strip())
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(str(folder))
        except Exception:
            messagebox.showerror("Erro", "Não foi possível abrir a pasta selecionada.")

    def _normalize_dir_var(self, target_var, default_factory) -> str:
        text = (target_var.get() or "").strip()
        folder = Path(text) if text else default_factory()
        folder.mkdir(parents=True, exist_ok=True)
        target_var.set(str(folder))
        return str(folder)

    def _get_mirror_target_cm(self) -> float:
        mode = (self.var_jpg_mode.get() or "").strip()
        if mode in ("17", "21"):
            return float(mode)

        s = (self.var_jpg_custom.get() or "").replace(",", ".").strip()
        try:
            value = float(s)
        except Exception:
            raise ValueError("Largura personalizada inválida.")
        if value < 8 or value > 40:
            raise ValueError("Use entre 8 cm e 40 cm.")
        return value

    def save_export_settings(self, show_message: bool = False) -> bool:
        try:
            cm = self._get_mirror_target_cm()
        except Exception as e:
            messagebox.showerror("Exportação", str(e))
            return False

        pdf_dir = self._normalize_dir_var(self.var_pdf_dir, _default_pdf_export_dir)
        mirror_dir = self._normalize_dir_var(self.var_mirror_dir, _default_mirror_jpg_export_dir)
        summary_dir = self._normalize_dir_var(self.var_summary_dir, _default_summary_jpg_export_dir)

        self.mcfg["mirror_jpg_width_mode"] = self.var_jpg_mode.get()
        self.mcfg["mirror_jpg_width_cm_custom"] = float(cm)
        self.mcfg["pdf_export_dir"] = pdf_dir
        self.mcfg["mirror_jpg_export_dir"] = mirror_dir
        self.mcfg["summary_jpg_export_dir"] = summary_dir
        self.mcfg["pdf_export_enabled"] = bool(self.var_export_pdf.get())
        self.mcfg["mirror_jpg_export_enabled"] = bool(self.var_export_mirror.get())
        self.mcfg["summary_jpg_export_enabled"] = bool(self.var_export_summary.get())
        save_cfg(self.mcfg)

        if show_message:
            messagebox.showinfo("Exportação", "Configurações salvas.")
        return True

    # --------------------------
    # Machine / naming
    # --------------------------
    def ask_machine(self) -> Optional[str]:
        win = tk.Toplevel(self)
        win.title("Selecionar máquina")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        ttk.Label(win, text="Esses logs são de qual máquina?").pack(padx=12, pady=(12, 6), anchor="w")
        var = tk.StringVar(value="M1")
        frm = ttk.Frame(win)
        frm.pack(padx=12, pady=6, anchor="w")
        for machine in ("M1", "M2"):
            ttk.Radiobutton(frm, text=machine, value=machine, variable=var).pack(anchor="w")

        out = {"val": None}

        def ok():
            out["val"] = var.get()
            win.destroy()

        def cancel():
            out["val"] = None
            win.destroy()

        btn = ttk.Frame(win)
        btn.pack(padx=12, pady=(6, 12), fill="x")
        ttk.Button(btn, text="OK", command=ok).pack(side="right", padx=4)
        ttk.Button(btn, text="Cancelar", command=cancel).pack(side="right", padx=4)

        win.wait_window()
        return out["val"]

    def _auto_roll_name(self) -> str:
        machine = self.machine or "M?"
        now = datetime.now()
        return f"{machine}_{now.strftime('%d-%m-%Y')}_{now.strftime('%H%M%S')}"

    def on_refresh_roll_name(self):
        if not self.machine:
            messagebox.showwarning("Sem máquina", "Importe logs primeiro para definir a máquina.")
            return
        self.var_roll.set(self._auto_roll_name())

    def _get_roll_name(self) -> str:
        name = self.var_roll.get().strip()
        if not name:
            name = self._auto_roll_name()
            self.var_roll.set(name)
        return _sanitize_filename(name)

    # --------------------------
    # Fabrics dialog
    # --------------------------
    def _fabric_options(self) -> List[str]:
        return sorted(set(list(self.fabrics_map.keys()) + ["DESCONHECIDO"]))

    def _validate_fabrics_map(self, candidate: Dict[str, List[str]]) -> tuple[bool, str]:
        seen: Dict[str, str] = {}
        for canonical, aliases in candidate.items():
            for raw in [canonical, *aliases]:
                alias = _normalize_name(raw)
                if not alias:
                    continue
                prev = seen.get(alias)
                if prev and prev != canonical:
                    return False, f'Nome/alias duplicado entre "{prev}" e "{canonical}": {raw}'
                seen[alias] = canonical
        return True, ""


    def open_fabrics_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Cadastro de Tecidos e Nomes Alternativos")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.geometry("820x460")

        current = json.loads(json.dumps(self.fabrics_map, ensure_ascii=False))
        editing_name = {"value": None}

        root = ttk.Frame(dlg, padding=12)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(root)
        right.pack(side="right", fill="y", padx=(12, 0))

        ttk.Label(left, text="Tecidos cadastrados").pack(anchor="w")
        lb = tk.Listbox(left, height=16)
        lb.pack(fill="both", expand=True, pady=(6, 0))

        form = ttk.LabelFrame(right, text="Editar tecido", padding=10)
        form.pack(fill="x")

        var_name = tk.StringVar()
        var_aliases = tk.StringVar()
        var_mode = tk.StringVar(value="Novo tecido")

        ttk.Label(form, textvariable=var_mode).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(form, text="Nome canônico").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=var_name, width=30).grid(row=2, column=0, sticky="ew")
        ttk.Label(form, text="Aliases (separados por vírgula)").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=var_aliases, width=30).grid(row=4, column=0, sticky="ew")

        def sorted_names():
            return sorted(current.keys())

        def refresh_list(select_name: Optional[str] = None):
            lb.delete(0, tk.END)
            names = sorted_names()
            for name in names:
                aliases = current.get(name, [])
                desc = ", ".join(aliases) if aliases else "(sem aliases)"
                lb.insert(tk.END, f"{name} -> {desc}")

            if select_name and select_name in names:
                idx = names.index(select_name)
                lb.selection_clear(0, tk.END)
                lb.selection_set(idx)
                lb.activate(idx)
                lb.see(idx)

        def clear_form_for_new():
            editing_name["value"] = None
            var_mode.set("Novo tecido")
            var_name.set("")
            var_aliases.set("")
            lb.selection_clear(0, tk.END)

        def load_selected(_evt=None):
            sel = lb.curselection()
            if not sel:
                return
            names = sorted_names()
            if sel[0] >= len(names):
                return
            name = names[sel[0]]
            editing_name["value"] = name
            var_mode.set("Editando tecido existente")
            var_name.set(name)
            var_aliases.set(", ".join(current.get(name, [])))

        lb.bind("<<ListboxSelect>>", load_selected)
        refresh_list()

        def save_item():
            old_name = editing_name["value"]
            name = var_name.get().strip()
            aliases = [x.strip() for x in var_aliases.get().split(",") if x.strip()]

            if not name:
                messagebox.showerror("Tecidos", "Informe o nome do tecido.", parent=dlg)
                return

            candidate = dict(current)

            if old_name and old_name != name:
                candidate.pop(old_name, None)

            candidate[name] = aliases

            ok, msg = self._validate_fabrics_map(candidate)
            if not ok:
                messagebox.showerror("Tecidos", msg, parent=dlg)
                return

            current.clear()
            current.update(candidate)
            self.fabrics_map = current
            save_fabrics(self.fabrics_map)
            self._reapply_fabric_detection_to_unknowns()

            editing_name["value"] = name
            var_mode.set("Editando tecido existente")
            refresh_list(select_name=name)

        def remove_item():
            name = editing_name["value"]
            if not name:
                messagebox.showinfo("Tecidos", "Selecione um tecido existente para remover.", parent=dlg)
                return

            if not messagebox.askyesno("Tecidos", f'Remover "{name}"?', parent=dlg):
                return

            current.pop(name, None)
            self.fabrics_map = current
            save_fabrics(self.fabrics_map)
            self._reapply_fabric_detection_to_unknowns()
            refresh_list()
            clear_form_for_new()

        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="Novo tecido", command=clear_form_for_new).pack(side="left")
        ttk.Button(buttons, text="Salvar tecido", command=save_item).pack(side="left", padx=(6, 0))
        ttk.Button(buttons, text="Remover", command=remove_item).pack(side="left", padx=(6, 0))

        footer = ttk.Frame(right)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Button(footer, text="Fechar", command=dlg.destroy).pack(side="right")

        clear_form_for_new()

    def _reapply_fabric_detection_to_unknowns(self):
        changed = False
        for job in self.jobs:
            if job.fabric == "DESCONHECIDO" or job.fabric == job.original_fabric:
                new_fabric = infer_fabric_from_text(job.document, self.fabrics_map)
                if new_fabric and new_fabric != job.fabric:
                    job.original_fabric = new_fabric
                    if _job_override_key(job.src_file) not in self.job_overrides:
                        job.fabric = new_fabric
                    changed = True
        if changed and self.machine:
            self.blocks = build_blocks(self.jobs, self.machine)
            self.refresh_blocks()
            self.clear_details()
            self.refresh_summary_labels()

    # --------------------------
    # Drag & drop
    # --------------------------
    def on_drop_files(self, event):
        raw = getattr(event, "data", "") or ""
        files = self._split_dnd_files(raw)
        self._import_paths(files)

    def _split_dnd_files(self, data: str) -> List[str]:
        out = []
        buff = ""
        in_brace = False
        for ch in data:
            if ch == "{":
                in_brace = True
                buff = ""
            elif ch == "}":
                in_brace = False
                if buff:
                    out.append(buff)
                buff = ""
            elif ch == " " and not in_brace:
                if buff:
                    out.append(buff)
                    buff = ""
            else:
                buff += ch
        if buff.strip():
            out.append(buff.strip())
        return [p.strip() for p in out if p.strip()]

    # --------------------------
    # Import
    # --------------------------
    def on_import_files(self):
        paths = filedialog.askopenfilenames(title="Selecionar logs .txt", filetypes=[("Logs TXT", "*.txt")])
        self._import_paths(list(paths))

    def on_import_folder(self):
        folder = filedialog.askdirectory(title="Selecionar pasta com logs .txt")
        if not folder:
            return
        paths = [str(x) for x in Path(folder).glob("*.txt")]
        self._import_paths(paths)

    def _apply_job_override(self, job: Job) -> None:
        override = self.job_overrides.get(_job_override_key(job.src_file))
        if not override:
            return

        document = str(override.get("document", "") or "").strip()
        fabric = str(override.get("fabric", "") or "").strip()
        review_note = str(override.get("review_note", "") or "")
        status = str(override.get("print_status", "") or "").strip()

        if document:
            job.document = document

        if fabric:
            job.fabric = fabric
        else:
            job.fabric = infer_fabric_from_text(job.document, self.fabrics_map)

        if status in STATUS_OPTIONS:
            job.print_status = status

        job.review_note = review_note

    def _import_paths(self, paths: List[str]):
        if not paths:
            return

        txts = [p for p in paths if p.lower().endswith(".txt")]
        if not txts:
            messagebox.showwarning("Sem .txt", "Selecione apenas arquivos .txt.")
            return

        if self.machine:
            machine = self.machine
        else:
            machine = self.ask_machine()
            if not machine:
                self.status.configure(text="Importação cancelada.")
                return
            self.machine = machine
            self.lbl_machine.configure(text=f"Máquina do lote: {machine}")
            if not self.var_roll.get().strip():
                self.var_roll.set(self._auto_roll_name())

        parsed: List[Job] = []
        skipped_invalid = 0
        existing_src = {j.src_file for j in self.jobs}

        for p in txts:
            p_full = str(p)
            if p_full in existing_src:
                continue

            job = parse_log_txt(p_full, self.fabrics_map)
            if not job:
                skipped_invalid += 1
                continue

            self._apply_job_override(job)

            if job.height_mm <= 0:
                skipped_invalid += 1
                continue

            correct_real_m = job.height_mm / 1000.0
            if abs(job.real_m - correct_real_m) > 0.001:
                skipped_invalid += 1
                continue

            parsed.append(job)
            existing_src.add(job.src_file)

        if not parsed and not self.jobs:
            messagebox.showerror("Falha", "Nenhum log válido encontrado.")
            return

        if parsed:
            self.jobs.extend(parsed)

        self.blocks = build_blocks(self.jobs, machine)
        self.refresh_blocks()
        self.clear_details()
        self.refresh_summary_labels()

        extra = f" | Ignorados inválidos: {skipped_invalid}" if skipped_invalid else ""
        added = f" | +{len(parsed)} novos" if parsed else " | +0 novos"
        self.status.configure(text=f"Importado total: {len(self.jobs)} logs{added} | Blocos: {len(self.blocks)} | Máquina: {machine}{extra}")

    # --------------------------
    # Summary / refresh
    # --------------------------
    def _block_alert_text(self, block: Block) -> str:
        aborted = block.count_status(STATUS_ABORTED)
        partial = block.count_status(STATUS_PARTIAL)
        review = block.count_status(STATUS_PENDING)
        missing_expected = any(j.expected_mm is None or float(j.expected_mm or 0.0) <= 0 for j in block.jobs)
        if aborted:
            return "ABORTADO"
        if partial:
            return "PARCIAL"
        if review or missing_expected:
            return "REVISAR"
        return "OK"

    def _block_tag(self, block: Block) -> str:
        if block.count_status(STATUS_ABORTED):
            return "has_aborted"
        if block.count_status(STATUS_PARTIAL):
            return "has_partial"
        if block.count_status(STATUS_PENDING) or any(j.expected_mm is None or float(j.expected_mm or 0.0) <= 0 for j in block.jobs):
            return "needs_review"
        return ""

    def _job_percent_text(self, job: Job) -> str:
        pct = job.printed_percent
        return f"{pct:.1f}%" if pct is not None else "—"

    def refresh_summary_labels(self):
        media_total = sum(j.real_m for j in self.jobs if j.counts_in_media_totals)
        production_total = sum(j.real_m for j in self.jobs if j.counts_in_production_totals)
        ok_count = sum(1 for j in self.jobs if j.print_status == STATUS_OK)
        review_count = sum(1 for j in self.jobs if j.print_status == STATUS_PENDING)
        aborted_count = sum(1 for j in self.jobs if j.print_status == STATUS_ABORTED)
        partial_count = sum(1 for j in self.jobs if j.print_status == STATUS_PARTIAL)
        self.lbl_summary.configure(
            text=(
                f"Mídia: {fmt_m(media_total)} | Produção: {fmt_m(production_total)} | "
                f"OK: {ok_count} | Revisão: {review_count} | Parcial: {partial_count} | Abortado: {aborted_count}"
            )
        )

    def on_clear(self):
        self.machine = None
        self.jobs = []
        self.blocks = []
        self.detail_job_map = {}
        self.var_roll.set("")
        self.lbl_machine.configure(text="Máquina do lote: (não definida)")
        self.tree_blocks.delete(*self.tree_blocks.get_children())
        self.tree_jobs.delete(*self.tree_jobs.get_children())
        self.var_detail_title.set("Selecione um bloco e uma entrada abaixo...")
        self.refresh_summary_labels()
        self.status.configure(text="Limpo.")

    def refresh_blocks(self):
        self.tree_blocks.delete(*self.tree_blocks.get_children())
        for idx, block in enumerate(self.blocks, start=1):
            alert_text = self._block_alert_text(block)
            block_tag = self._block_tag(block)
            self.tree_blocks.insert(
                "",
                "end",
                iid=str(idx - 1),
                values=(
                    idx,
                    alert_text,
                    block.fabric,
                    fmt_m(block.total_m),
                    fmt_m(block.production_m),
                    block.job_count,
                    block.count_status(STATUS_OK),
                    block.count_status(STATUS_PENDING),
                    block.newest_end.strftime("%d/%m/%Y %H:%M:%S"),
                ),
                tags=((block_tag,) if block_tag else ()),
            )

    def clear_details(self):
        self.var_detail_title.set("Selecione um bloco e uma entrada abaixo...")
        self.tree_jobs.delete(*self.tree_jobs.get_children())
        self.detail_job_map = {}

    def on_select_block(self, _evt=None):
        sel = self.tree_blocks.selection()
        if not sel:
            return

        bi = int(sel[0])
        if bi < 0 or bi >= len(self.blocks):
            return

        block = self.blocks[bi]
        self.var_detail_title.set(
            f"Tecido: {block.fabric} | Alerta: {self._block_alert_text(block) or 'OK'} | Entradas: {block.job_count} | Mídia: {fmt_m(block.total_m)} | Produção: {fmt_m(block.production_m)}"
        )

        self.tree_jobs.delete(*self.tree_jobs.get_children())
        self.detail_job_map = {}

        for idx, job in enumerate(sorted(block.jobs, key=lambda jj: jj.end_time, reverse=True), start=1):
            iid = f"job_{idx}"
            self.detail_job_map[iid] = job
            job_tag = ""
            if job.print_status == STATUS_PENDING:
                job_tag = "pending_review"
            elif job.print_status == STATUS_PARTIAL:
                job_tag = "partial"
            elif job.print_status == STATUS_ABORTED:
                job_tag = "aborted"

            self.tree_jobs.insert(
                "",
                "end",
                iid=iid,
                values=(
                    job.end_time.strftime("%d/%m/%Y %H:%M:%S"),
                    job.print_status,
                    self._job_percent_text(job),
                    job.document,
                    job.fabric,
                    f"{job.height_mm:.1f}",
                    f"{job.vpos_mm:.1f}",
                    fmt_m(job.real_m, suffix=False),
                    Path(job.src_file).name,
                ),
                tags=((job_tag,) if job_tag else ()),
            )

    # --------------------------
    # Edit manual entries
    # --------------------------
    def on_edit_selected_job(self, event=None):
        sel = self.tree_jobs.selection()
        if not sel:
            messagebox.showwarning("Editar entrada", "Selecione uma entrada primeiro.")
            return

        job = self.detail_job_map.get(sel[0])
        if job is None:
            messagebox.showerror("Editar entrada", "Não foi possível localizar a entrada selecionada.")
            return

        self._open_job_editor(job)

    def _open_job_editor(self, job: Job) -> None:
        win = tk.Toplevel(self)
        win.title("Editar entrada de log")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Arquivo").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text=Path(job.src_file).name).grid(
            row=0, column=1, sticky="w", columnspan=3, pady=(0, 8)
        )

        ttk.Label(frame, text="Documento").grid(row=1, column=0, sticky="w")
        var_document = tk.StringVar(value=job.document)
        ttk.Entry(frame, textvariable=var_document, width=64).grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=2
        )

        ttk.Label(frame, text="Tecido").grid(row=2, column=0, sticky="w")
        var_fabric = tk.StringVar(value=job.fabric)
        fabric_combo = ttk.Combobox(
            frame,
            textvariable=var_fabric,
            state="readonly",
            width=28,
            values=self._fabric_options(),
        )
        fabric_combo.grid(row=2, column=1, sticky="w", pady=2)
        ttk.Button(frame, text="Tecidos...", command=self.open_fabrics_dialog).grid(
            row=2, column=2, sticky="w", padx=(6, 0), pady=2
        )
        ttk.Button(
            frame,
            text="Recalcular tecido",
            command=lambda: var_fabric.set(
                infer_fabric_from_text(var_document.get(), self.fabrics_map)
            ),
        ).grid(row=2, column=3, sticky="w", padx=(6, 0), pady=2)

        ttk.Label(frame, text="Status").grid(row=3, column=0, sticky="w")
        var_status = tk.StringVar(value=job.print_status)
        ttk.Combobox(
            frame,
            textvariable=var_status,
            state="readonly",
            width=24,
            values=STATUS_OPTIONS,
        ).grid(row=3, column=1, sticky="w", pady=2)

        ttk.Label(frame, text="Comprimento esperado (mm)").grid(row=4, column=0, sticky="w")
        expected_text = f"{job.expected_mm:.1f}" if job.expected_mm is not None else "Indisponível"
        ttk.Label(frame, text=expected_text).grid(row=4, column=1, sticky="w", pady=2)

        ttk.Label(frame, text="% impresso").grid(row=4, column=2, sticky="w", padx=(12, 0))
        percent_text = self._job_percent_text(job)
        ttk.Label(
            frame,
            text=percent_text if percent_text != "—" else "Indisponível (sem esperado)",
        ).grid(row=4, column=3, sticky="w")

        ttk.Label(frame, text="Detecção automática").grid(row=5, column=0, sticky="nw", pady=(8, 0))
        auto_desc = job.auto_reason or "Sem alerta automático para esta entrada."
        ttk.Label(
            frame,
            text=f"Tecido detectado: {job.original_fabric}\n{auto_desc}",
            justify="left",
        ).grid(row=5, column=1, columnspan=3, sticky="w", pady=(8, 0))

        ttk.Label(frame, text="Observação").grid(row=6, column=0, sticky="nw", pady=(8, 0))
        txt_note = tk.Text(frame, width=52, height=4)
        txt_note.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(8, 0))
        txt_note.insert("1.0", job.review_note or "")

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=4, sticky="e", pady=(12, 0))

        def save_edit():
            document = var_document.get().strip()
            fabric = var_fabric.get().strip() or "DESCONHECIDO"
            status = var_status.get().strip()
            note = txt_note.get("1.0", "end").strip()

            if not document:
                messagebox.showerror(
                    "Editar entrada", "Documento não pode ficar vazio.", parent=win
                )
                return
            if status not in STATUS_OPTIONS:
                messagebox.showerror("Editar entrada", "Status inválido.", parent=win)
                return

            job.document = document
            job.fabric = fabric
            job.print_status = status
            job.review_note = note
            job.original_fabric = infer_fabric_from_text(job.document, self.fabrics_map)

            self.job_overrides[_job_override_key(job.src_file)] = {
                "document": job.document,
                "fabric": job.fabric,
                "print_status": job.print_status,
                "review_note": job.review_note,
            }
            save_job_overrides(self.job_overrides)

            self.blocks = build_blocks(self.jobs, self.machine or "")
            self.refresh_blocks()
            self.clear_details()
            self.refresh_summary_labels()
            self.status.configure(text=f"Entrada atualizada: {Path(job.src_file).name}")
            win.destroy()

        def clear_override():
            key = _job_override_key(job.src_file)
            self.job_overrides.pop(key, None)
            save_job_overrides(self.job_overrides)
            reloaded = parse_log_txt(job.src_file, self.fabrics_map)
            if reloaded:
                job.document = reloaded.document
                job.fabric = reloaded.fabric
                job.original_fabric = reloaded.original_fabric
                job.height_mm = reloaded.height_mm
                job.vpos_mm = reloaded.vpos_mm
                job.expected_mm = reloaded.expected_mm
                job.real_mm = reloaded.real_mm
                job.print_status = reloaded.print_status
                job.review_note = ""
                job.auto_reason = reloaded.auto_reason
            self.blocks = build_blocks(self.jobs, self.machine or "")
            self.refresh_blocks()
            self.clear_details()
            self.refresh_summary_labels()
            self.status.configure(text=f"Correções manuais desfeitas: {Path(job.src_file).name}")
            win.destroy()

        has_override = _job_override_key(job.src_file) in self.job_overrides
        btn_clear = ttk.Button(buttons, text="Desfazer correções manuais", command=clear_override)
        btn_clear.pack(side="left")
        if not has_override:
            btn_clear.state(["disabled"])
        ttk.Button(buttons, text="Cancelar", command=win.destroy).pack(side="right")
        ttk.Button(buttons, text="Salvar", command=save_edit).pack(side="right", padx=(0, 6))

    # --------------------------
    # Export
    # --------------------------
    def on_export_selected(self, dialog=None):
        if not self.blocks or not self.machine:
            messagebox.showwarning("Nada para exportar", "Importe logs primeiro.")
            return

        if not self.save_export_settings(show_message=False):
            return

        export_pdf_enabled = bool(self.var_export_pdf.get())
        export_mirror_enabled = bool(self.var_export_mirror.get())
        export_summary_enabled = bool(self.var_export_summary.get())

        if not any((export_pdf_enabled, export_mirror_enabled, export_summary_enabled)):
            messagebox.showwarning("Exportação", "Marque pelo menos um arquivo para exportar.")
            return

        if export_pdf_enabled and canvas is None:
            messagebox.showerror("Dependência faltando", "Instale reportlab: pip install reportlab")
            return
        if (export_mirror_enabled or export_summary_enabled) and not _HAS_PYMUPDF:
            messagebox.showerror("Dependência faltando", "Instale pymupdf: pip install pymupdf")
            return
        if (export_mirror_enabled or export_summary_enabled) and not _HAS_PIL:
            messagebox.showerror("Dependência faltando", "Instale pillow: pip install pillow")
            return

        export_jobs = [j for j in self.jobs if j.is_visible]
        export_blocks = build_blocks(export_jobs, self.machine)
        roll = self._get_roll_name()

        pdf_dir = Path(self.var_pdf_dir.get().strip())
        mirror_dir = Path(self.var_mirror_dir.get().strip())
        summary_dir = Path(self.var_summary_dir.get().strip())
        pdf_dir.mkdir(parents=True, exist_ok=True)
        mirror_dir.mkdir(parents=True, exist_ok=True)
        summary_dir.mkdir(parents=True, exist_ok=True)
        tmp_dir = _temp_dir()

        dt = datetime.now()
        date_iso = dt.strftime("%Y-%m-%d")
        roll_safe = _sanitize_filename(roll)
        base_name = f"{date_iso}_{self.machine}_{roll_safe}_FULL"

        pdf_path = str(_versioned_path(pdf_dir / f"{base_name}.pdf")) if export_pdf_enabled else None
        mirror_path = str(_versioned_path(mirror_dir / f"{base_name}.jpg")) if export_mirror_enabled else None
        summary_path = str(summary_dir / self._summary_jpg_filename()) if export_summary_enabled else None
        tmp_mirror_pdf = str(tmp_dir / f"{base_name}.tmp.pdf")

        target_cm = float(self._get_mirror_target_cm())
        dpi = int(self.mcfg.get("mirror_jpg_dpi", 300))

        try:
            if export_pdf_enabled and pdf_path:
                export_pdf(pdf_path, export_jobs, export_blocks, roll, self.machine, mirrored=False)

            if export_mirror_enabled or export_summary_enabled:
                export_pdf(tmp_mirror_pdf, export_jobs, export_blocks, roll, self.machine, mirrored=True)

                if export_mirror_enabled and mirror_path:
                    pdf_first_page_to_jpg_scaled(tmp_mirror_pdf, mirror_path, target_width_cm=target_cm, dpi=dpi, quality=95)

                if export_summary_enabled and summary_path:
                    pdf_first_page_to_jpg_scaled(tmp_mirror_pdf, summary_path, target_width_cm=target_cm, dpi=dpi, quality=95)

                Path(tmp_mirror_pdf).unlink(missing_ok=True)

        except Exception as e:
            try:
                Path(tmp_mirror_pdf).unlink(missing_ok=True)
            except Exception:
                pass
            messagebox.showerror("Erro ao exportar", str(e))
            return

        try:
            audit_dir = _nexor_base_dir() / "audit" / MODULE_NAME
            audit_dir.mkdir(parents=True, exist_ok=True)
            audit_path = audit_dir / f"exports_{datetime.now().strftime('%Y%m')}.jsonl"
            payload = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "app_version": APP_VERSION,
                "machine": self.machine,
                "roll_name": roll,
                "export_mode": "full",
                "pdf_enabled": export_pdf_enabled,
                "mirror_jpg_enabled": export_mirror_enabled,
                "summary_jpg_enabled": export_summary_enabled,
                "pdf_dir": str(pdf_dir),
                "mirror_jpg_dir": str(mirror_dir),
                "summary_jpg_dir": str(summary_dir),
                "pdf_path": pdf_path,
                "mirror_jpg_path": mirror_path,
                "summary_jpg_path": summary_path,
                "mirror_width_cm": (target_cm if (export_mirror_enabled or export_summary_enabled) else None),
                "mirror_dpi": (dpi if (export_mirror_enabled or export_summary_enabled) else None),
                "jobs": [
                    {
                        "end_time": j.end_time.isoformat(timespec="seconds"),
                        "document": j.document,
                        "fabric": j.fabric,
                        "height_mm": j.height_mm,
                        "vpos_mm": j.vpos_mm,
                        "expected_mm": j.expected_mm,
                        "printed_percent": (round(j.printed_percent, 2) if j.printed_percent is not None else None),
                        "real_m": j.real_m,
                        "print_status": j.print_status,
                        "review_note": j.review_note,
                        "source_path": j.src_file,
                    }
                    for j in export_jobs
                ],
            }
            with audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.status.configure(text=self.status.cget("text") + " | auditoria local ok")
        except Exception as e:
            self.status.configure(text=self.status.cget("text") + f" | auditoria local erro: {type(e).__name__}")

        if dialog is not None:
            try:
                dialog.destroy()
            except Exception:
                pass

        exported_lines = []
        if pdf_path:
            exported_lines.append(f"PDF:\n{pdf_path}")
        if mirror_path:
            exported_lines.append(f"JPG espelhado:\n{mirror_path}")
        if summary_path:
            exported_lines.append(f"JPG resumo:\n{summary_path}")
        messagebox.showinfo("Exportado", "\n\n".join(exported_lines) if exported_lines else "Nenhum arquivo foi exportado.")

    def refresh_all(self):
        self.refresh_blocks()
        self.refresh_summary_labels()


PXPrintLogsUI = OperationsPanel


def build_ui(parent):
    return OperationsPanel(parent)
