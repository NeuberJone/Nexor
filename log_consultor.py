from __future__ import annotations

import configparser
import json
import math
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

APP_TITLE = "Consultor de Logs de Impressão"
CONFIG_FILE = "log_consultor_config.json"
DATE_FMT = "%d/%m/%Y %H:%M:%S"
CHANNELS = ["K", "C", "M", "Y"]

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    HAS_DND = True
except Exception:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False


# =========================
# Helpers
# =========================
def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(str(value).strip())
    except ValueError:
        return None


def human_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(size)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{size} B"


def fmt_num(value: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suffix


def fmt_mm_as_m(value_mm: Optional[float]) -> str:
    if value_mm is None:
        return "—"
    return fmt_num(value_mm / 1000.0, 4, " m")


def fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h {m:02d}min {s:02d}s"


def pct(part: Optional[float], total: Optional[float]) -> Optional[float]:
    if part is None or total in (None, 0):
        return None
    return (part / total) * 100.0


def parse_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value.strip(), DATE_FMT)
    except Exception:
        return None


def parse_drop_sizes(text: str) -> List[float]:
    return [v for v in [safe_float(x) for x in str(text).split(",")] if v is not None]


def list_to_multiline(items: List[str]) -> str:
    return "\n".join(f"• {item}" for item in items) if items else "—"


def normalize_key_name(name: str) -> str:
    return re.sub(r"\s+", "", name or "").strip()


def extract_fabric_from_document(document: str) -> Optional[str]:
    if not document:
        return None
    parts = [p.strip() for p in document.split(" - ")]
    if len(parts) >= 2 and parts[1]:
        return parts[1]
    return None


def split_dnd_paths(data: str) -> List[str]:
    if not data:
        return []
    # Handles Windows paths with spaces wrapped in braces.
    pattern = re.compile(r"\{([^}]*)\}|(\S+)")
    paths: List[str] = []
    for match in pattern.finditer(data):
        path = match.group(1) or match.group(2)
        if path:
            paths.append(path)
    return paths


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# =========================
# Config
# =========================
@dataclass
class PaperConfig:
    name: str = "Papel padrão"
    width_mm: float = 1780.0
    grammage_gsm: float = 60.0
    roll_length_m: float = 0.0
    price_per_kg: float = 0.0
    price_per_m: float = 0.0
    notes: str = ""


@dataclass
class InkConfig:
    cost_per_ml_k: float = 0.0
    cost_per_ml_c: float = 0.0
    cost_per_ml_m: float = 0.0
    cost_per_ml_y: float = 0.0
    notes: str = ""


@dataclass
class AppConfig:
    paper: PaperConfig = field(default_factory=PaperConfig)
    ink: InkConfig = field(default_factory=InkConfig)

    @staticmethod
    def load(path: Path) -> "AppConfig":
        if not path.exists():
            return AppConfig()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            paper = PaperConfig(**data.get("paper", {}))
            ink = InkConfig(**data.get("ink", {}))
            return AppConfig(paper=paper, ink=ink)
        except Exception:
            return AppConfig()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


# =========================
# Parsing and analysis
# =========================
@dataclass
class InkChannelData:
    channel: str
    ml: Optional[float] = None
    drop_sizes: List[float] = field(default_factory=list)
    level_1: Optional[int] = None
    level_2: Optional[int] = None
    level_3: Optional[int] = None

    @property
    def total_drops(self) -> Optional[int]:
        parts = [self.level_1, self.level_2, self.level_3]
        if all(v is None for v in parts):
            return None
        return sum(v or 0 for v in parts)


@dataclass
class ItemData:
    section_name: str
    name: str = ""
    h_position_mm: Optional[float] = None
    v_position_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    width_dots: Optional[int] = None
    height_dots: Optional[int] = None
    gray_icc: str = ""
    rgb_icc: str = ""
    cmyk_icc: str = ""
    proofing_icc: str = ""
    brightness: str = ""
    contrast: str = ""
    saturation: str = ""
    color_replacement: str = ""
    channel_drops: Dict[str, InkChannelData] = field(default_factory=dict)


@dataclass
class LogAnalysis:
    file_path: str
    file_name: str
    file_size_bytes: int
    raw_sections: Dict[str, Dict[str, str]]
    computer_name: str = ""
    software_version: str = ""
    job_id: str = ""
    document: str = ""
    file_count: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    driver: str = ""
    copy: Optional[int] = None
    total_copies: Optional[int] = None
    units: str = ""
    page_width_mm: Optional[float] = None
    print_width_mm: Optional[float] = None
    print_height_mm: Optional[float] = None
    print_width_dots: Optional[int] = None
    print_height_dots: Optional[int] = None
    bits_per_pixel: Optional[int] = None
    scheme: str = ""
    print_mode: str = ""
    advanced_settings: str = ""
    correction: str = ""
    nxcm_overprint: str = ""
    inkset: str = ""
    ink_limit_percent: Optional[float] = None
    ink_usage_percent: Optional[float] = None
    linearization: str = ""
    post_linearization: str = ""
    icc: str = ""
    hueman_version: str = ""
    revision: str = ""
    preset: str = ""
    shadow_optimizer_percent: Optional[float] = None
    rendering_img: str = ""
    rendering_vect: str = ""
    rendering_spot: str = ""
    cmm: str = ""
    direct_colors_table: str = ""
    halftoning: str = ""
    channels: Dict[str, InkChannelData] = field(default_factory=dict)
    items: List[ItemData] = field(default_factory=list)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return max(0.0, (self.end_time - self.start_time).total_seconds())
        return None

    @property
    def fabric_from_name(self) -> Optional[str]:
        return extract_fabric_from_document(self.document)

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def primary_item(self) -> Optional[ItemData]:
        return self.items[0] if self.items else None

    @property
    def actual_print_length_mm(self) -> Optional[float]:
        item = self.primary_item
        if item and item.height_mm is not None:
            return item.height_mm
        return self.print_height_mm

    @property
    def space_before_print_mm(self) -> Optional[float]:
        item = self.primary_item
        if item:
            return item.v_position_mm
        return None

    @property
    def total_paper_used_mm(self) -> Optional[float]:
        printed = self.actual_print_length_mm
        before = self.space_before_print_mm or 0.0
        if printed is None:
            return None
        return printed + before

    @property
    def space_after_print_mm(self) -> Optional[float]:
        # In many logs this information is not explicitly present.
        return None

    @property
    def print_area_m2(self) -> Optional[float]:
        if self.print_width_mm is None or self.print_height_mm is None:
            return None
        return (self.print_width_mm / 1000.0) * (self.print_height_mm / 1000.0)

    @property
    def total_ink_ml(self) -> Optional[float]:
        values = [ch.ml for ch in self.channels.values() if ch.ml is not None]
        if not values:
            return None
        return sum(values)

    @property
    def total_drops(self) -> Optional[int]:
        totals = [ch.total_drops for ch in self.channels.values() if ch.total_drops is not None]
        if not totals:
            return None
        return sum(totals)

    @property
    def avg_speed_m_per_min(self) -> Optional[float]:
        length_mm = self.actual_print_length_mm
        duration = self.duration_seconds
        if length_mm is None or duration in (None, 0):
            return None
        return (length_mm / 1000.0) / (duration / 60.0)

    @property
    def left_margin_mm(self) -> Optional[float]:
        item = self.primary_item
        if not item:
            return None
        return item.h_position_mm

    @property
    def right_margin_mm(self) -> Optional[float]:
        item = self.primary_item
        if not item or self.print_width_mm is None or item.width_mm is None or item.h_position_mm is None:
            return None
        return max(0.0, self.print_width_mm - item.width_mm - item.h_position_mm)

    @property
    def usable_width_gap_mm(self) -> Optional[float]:
        if self.page_width_mm is None or self.print_width_mm is None:
            return None
        return max(0.0, self.page_width_mm - self.print_width_mm)

    @property
    def width_occupancy_percent(self) -> Optional[float]:
        item = self.primary_item
        if not item or item.width_mm is None or self.print_width_mm in (None, 0):
            return None
        return (item.width_mm / self.print_width_mm) * 100.0


class LogParser:
    @staticmethod
    def parse_file(path: str) -> LogAnalysis:
        p = Path(path)
        raw_text = p.read_text(encoding="utf-8", errors="ignore")
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read_string(raw_text)

        sections: Dict[str, Dict[str, str]] = {}
        for section in parser.sections():
            data = {k.strip(): v.strip() for k, v in parser.items(section)}
            sections[section] = data

        analysis = LogAnalysis(
            file_path=str(p),
            file_name=p.name,
            file_size_bytes=p.stat().st_size,
            raw_sections=sections,
        )

        general = sections.get("General", {})
        analysis.computer_name = general.get("ComputerName", "")
        analysis.software_version = general.get("SoftwareVersion", "")
        analysis.job_id = general.get("JobID", "")
        analysis.document = general.get("Document", "")
        analysis.file_count = safe_int(general.get("FileCount"))
        analysis.start_time = parse_datetime(general.get("StartTime", "")) if general.get("StartTime") else None
        analysis.end_time = parse_datetime(general.get("EndTime", "")) if general.get("EndTime") else None
        analysis.driver = general.get("Driver", "")
        analysis.copy = safe_int(general.get("Copy"))
        analysis.total_copies = safe_int(general.get("TotalCopies"))
        analysis.units = general.get("Units", "")

        costs = sections.get("Costs", {})
        analysis.page_width_mm = safe_float(costs.get("PageWidthMM"))
        analysis.print_width_mm = safe_float(costs.get("PrintWidthMM"))
        analysis.print_height_mm = safe_float(costs.get("PrintHeightMM"))
        analysis.print_width_dots = safe_int(costs.get("PrintWidth_Dots"))
        analysis.print_height_dots = safe_int(costs.get("PrintHeight_Dots"))
        analysis.bits_per_pixel = safe_int(costs.get("BitsPerPixel"))
        analysis.channels = LogParser._extract_channel_data(costs)

        ps = sections.get("PrintSettings", {})
        analysis.scheme = ps.get("Scheme", "")
        analysis.print_mode = ps.get("PrintMode", "")
        analysis.advanced_settings = ps.get("AdvancedSettings", "")
        analysis.correction = ps.get("Correction", "")
        analysis.nxcm_overprint = ps.get("DeviceNXCMOverPrint", "")

        cm = sections.get("ColorManagement", {})
        analysis.inkset = cm.get("Inkset", "")
        analysis.ink_limit_percent = safe_float((cm.get("InkLimit", "") or "").replace("%", ""))
        analysis.ink_usage_percent = safe_float((cm.get("InkUsage", "") or "").replace("%", ""))
        analysis.linearization = cm.get("Linearization", "")
        analysis.post_linearization = cm.get("PostLinearization", "")
        analysis.icc = cm.get("ICC", "")
        analysis.hueman_version = cm.get("HuemanVersion", "")
        analysis.revision = cm.get("Revision", "")
        analysis.preset = cm.get("Preset", "")
        analysis.shadow_optimizer_percent = safe_float((cm.get("ShadowOptimizer", "") or "").replace("%", ""))
        analysis.rendering_img = cm.get("RenderingImg", "")
        analysis.rendering_vect = cm.get("RenderingVect", "")
        analysis.rendering_spot = cm.get("RenderingSpot", "")
        analysis.cmm = cm.get("CMM", "")
        analysis.direct_colors_table = cm.get("DirectColorsTable", "")
        analysis.halftoning = cm.get("Halftoning", "")

        item_sections = [name for name in sections if name.isdigit()]
        for section_name in sorted(item_sections, key=lambda x: int(x)):
            item_data = sections[section_name]
            item = ItemData(
                section_name=section_name,
                name=item_data.get("Name", ""),
                h_position_mm=safe_float(item_data.get("HPositionMM")),
                v_position_mm=safe_float(item_data.get("VPositionMM")),
                width_mm=safe_float(item_data.get("WidthMM")),
                height_mm=safe_float(item_data.get("HeightMM")),
                width_dots=safe_int(item_data.get("Width_Dots")),
                height_dots=safe_int(item_data.get("Height_Dots")),
                gray_icc=item_data.get("GrayIcc", ""),
                rgb_icc=item_data.get("RgbIcc", ""),
                cmyk_icc=item_data.get("CmykIcc", ""),
                proofing_icc=item_data.get("ProofingIcc", ""),
                brightness=item_data.get("Brightness", ""),
                contrast=item_data.get("Contrast", ""),
                saturation=item_data.get("Saturation", ""),
                color_replacement=item_data.get("ColorReplacement", ""),
                channel_drops=LogParser._extract_channel_data(item_data, include_ml=False, include_sizes=False),
            )
            analysis.items.append(item)

        return analysis

    @staticmethod
    def _extract_channel_data(data: Dict[str, str], include_ml: bool = True, include_sizes: bool = True) -> Dict[str, InkChannelData]:
        result: Dict[str, InkChannelData] = {}
        for ch in CHANNELS:
            result[ch] = InkChannelData(channel=ch)
            result[ch].level_1 = safe_int(data.get(f"KDots[{ch}][1]"))
            result[ch].level_2 = safe_int(data.get(f"KDots[{ch}][2]"))
            result[ch].level_3 = safe_int(data.get(f"KDots[{ch}][3]"))
            if include_sizes and data.get(f"InkDropsizes[{ch}]"):
                result[ch].drop_sizes = parse_drop_sizes(data.get(f"InkDropsizes[{ch}]", ""))
            if include_ml:
                result[ch].ml = safe_float(data.get(f"InkML[{ch}]"))
        return result


class CostEstimator:
    def __init__(self, config: AppConfig):
        self.config = config

    def estimate_paper_weight_kg(self, analysis: LogAnalysis) -> Optional[float]:
        paper = self.config.paper
        if paper.grammage_gsm <= 0:
            return None
        length_m = analysis.total_paper_used_mm
        width_mm = paper.width_mm or analysis.page_width_mm
        if length_m is None or not width_mm:
            return None
        area_m2 = (width_mm / 1000.0) * (length_m / 1000.0)
        return (area_m2 * paper.grammage_gsm) / 1000.0

    def estimate_paper_cost(self, analysis: LogAnalysis) -> Optional[float]:
        paper = self.config.paper
        if paper.price_per_m > 0 and analysis.total_paper_used_mm is not None:
            return (analysis.total_paper_used_mm / 1000.0) * paper.price_per_m
        weight = self.estimate_paper_weight_kg(analysis)
        if weight is not None and paper.price_per_kg > 0:
            return weight * paper.price_per_kg
        return None

    def estimate_ink_cost(self, analysis: LogAnalysis) -> Optional[float]:
        ink = self.config.ink
        total = 0.0
        used = False
        for ch in CHANNELS:
            ch_data = analysis.channels.get(ch)
            if ch_data and ch_data.ml is not None:
                cost_per_ml = getattr(ink, f"cost_per_ml_{ch.lower()}", 0.0)
                total += ch_data.ml * cost_per_ml
                used = True
        return total if used else None

    def estimate_total_cost(self, analysis: LogAnalysis) -> Optional[float]:
        paper = self.estimate_paper_cost(analysis)
        ink = self.estimate_ink_cost(analysis)
        parts = [v for v in [paper, ink] if v is not None]
        if not parts:
            return None
        return sum(parts)


# =========================
# UI
# =========================
class ConfigDialog(tk.Toplevel):
    def __init__(self, parent: "LogConsultorApp", config: AppConfig):
        super().__init__(parent.root)
        self.parent = parent
        self.config_data = config
        self.title("Configurações")
        self.geometry("620x520")
        self.resizable(True, True)
        self.transient(parent.root)
        self.grab_set()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        frame_paper = ttk.Frame(nb, padding=12)
        frame_ink = ttk.Frame(nb, padding=12)
        nb.add(frame_paper, text="Papel")
        nb.add(frame_ink, text="Tintas")

        self.paper_vars = {
            "name": tk.StringVar(value=config.paper.name),
            "width_mm": tk.StringVar(value=str(config.paper.width_mm)),
            "grammage_gsm": tk.StringVar(value=str(config.paper.grammage_gsm)),
            "roll_length_m": tk.StringVar(value=str(config.paper.roll_length_m)),
            "price_per_kg": tk.StringVar(value=str(config.paper.price_per_kg)),
            "price_per_m": tk.StringVar(value=str(config.paper.price_per_m)),
            "notes": tk.StringVar(value=config.paper.notes),
        }
        self.ink_vars = {
            "cost_per_ml_k": tk.StringVar(value=str(config.ink.cost_per_ml_k)),
            "cost_per_ml_c": tk.StringVar(value=str(config.ink.cost_per_ml_c)),
            "cost_per_ml_m": tk.StringVar(value=str(config.ink.cost_per_ml_m)),
            "cost_per_ml_y": tk.StringVar(value=str(config.ink.cost_per_ml_y)),
            "notes": tk.StringVar(value=config.ink.notes),
        }

        self._build_form(frame_paper, [
            ("Nome do papel", "name"),
            ("Largura do papel (mm)", "width_mm"),
            ("Gramatura (g/m²)", "grammage_gsm"),
            ("Comprimento do rolo (m)", "roll_length_m"),
            ("Preço por kg (R$)", "price_per_kg"),
            ("Preço por metro (R$)", "price_per_m"),
            ("Observações", "notes"),
        ], self.paper_vars)

        self._build_form(frame_ink, [
            ("Custo por mL - K (R$)", "cost_per_ml_k"),
            ("Custo por mL - C (R$)", "cost_per_ml_c"),
            ("Custo por mL - M (R$)", "cost_per_ml_m"),
            ("Custo por mL - Y (R$)", "cost_per_ml_y"),
            ("Observações", "notes"),
        ], self.ink_vars)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(footer, text="Salvar", command=self.on_save).pack(side="right")
        ttk.Button(footer, text="Cancelar", command=self.destroy).pack(side="right", padx=(0, 8))

    def _build_form(self, parent: ttk.Frame, fields: List[Tuple[str, str]], vars_map: Dict[str, tk.StringVar]) -> None:
        for i, (label, key) in enumerate(fields):
            ttk.Label(parent, text=label).grid(row=i, column=0, sticky="w", padx=(0, 8), pady=6)
            entry = ttk.Entry(parent, textvariable=vars_map[key], width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=6)
        parent.columnconfigure(1, weight=1)

    def on_save(self) -> None:
        try:
            self.config_data.paper = PaperConfig(
                name=self.paper_vars["name"].get().strip() or "Papel padrão",
                width_mm=safe_float(self.paper_vars["width_mm"].get()) or 0.0,
                grammage_gsm=safe_float(self.paper_vars["grammage_gsm"].get()) or 0.0,
                roll_length_m=safe_float(self.paper_vars["roll_length_m"].get()) or 0.0,
                price_per_kg=safe_float(self.paper_vars["price_per_kg"].get()) or 0.0,
                price_per_m=safe_float(self.paper_vars["price_per_m"].get()) or 0.0,
                notes=self.paper_vars["notes"].get().strip(),
            )
            self.config_data.ink = InkConfig(
                cost_per_ml_k=safe_float(self.ink_vars["cost_per_ml_k"].get()) or 0.0,
                cost_per_ml_c=safe_float(self.ink_vars["cost_per_ml_c"].get()) or 0.0,
                cost_per_ml_m=safe_float(self.ink_vars["cost_per_ml_m"].get()) or 0.0,
                cost_per_ml_y=safe_float(self.ink_vars["cost_per_ml_y"].get()) or 0.0,
                notes=self.ink_vars["notes"].get().strip(),
            )
            self.parent.save_config()
            self.parent.refresh_all_reports()
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível salvar as configurações.\n\n{exc}")


class LogConsultorApp:
    def __init__(self) -> None:
        root_cls = TkinterDnD.Tk if HAS_DND else tk.Tk
        self.root = root_cls()
        self.root.title(APP_TITLE)
        self.root.geometry("1320x820")
        self.root.minsize(1080, 700)

        self.app_dir = get_app_dir()
        self.config_path = self.app_dir / CONFIG_FILE
        self.config = AppConfig.load(self.config_path)
        self.estimator = CostEstimator(self.config)

        self.analyses: List[LogAnalysis] = []
        self._analysis_by_tree_id: Dict[str, LogAnalysis] = {}

        self._build_ui()
        self._apply_dnd()
        self.refresh_consolidated_report()

    def _build_ui(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        ttk.Button(toolbar, text="Importar logs", command=self.import_logs).pack(side="left")
        ttk.Button(toolbar, text="Remover selecionado", command=self.remove_selected).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Limpar lista", command=self.clear_all).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Exportar relatório TXT", command=self.export_report_txt).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Configurações", command=self.open_config).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Atualizar informações", command=self.refresh_all_reports).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Arraste logs para a janela ou use Importar logs.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        left = ttk.Frame(self.root, padding=(8, 0, 4, 8))
        left.grid(row=1, column=0, sticky="nsew")
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Logs importados", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        tip_text = "Dica: o programa aceita múltiplos arquivos .txt de log."
        if HAS_DND:
            tip_text += " Você também pode usar drag and drop."
        else:
            tip_text += " Para arrastar e soltar, instale tkinterdnd2."
        ttk.Label(left, text=tip_text, foreground="#666").grid(row=1, column=0, sticky="w", pady=(0, 8))

        columns = ("arquivo", "documento", "tecido", "metros", "tempo", "tinta")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=18)
        headings = {
            "arquivo": "Arquivo",
            "documento": "Documento",
            "tecido": "Tecido",
            "metros": "Impresso",
            "tempo": "Tempo",
            "tinta": "Tinta total",
        }
        widths = {"arquivo": 220, "documento": 360, "tecido": 130, "metros": 90, "tempo": 100, "tinta": 100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        scroll_y = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scroll_y.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll_y.set)

        right = ttk.Frame(self.root, padding=(4, 0, 8, 8))
        right.grid(row=1, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Leitura amigável do log", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.tab_friendly = ttk.Frame(self.notebook)
        self.tab_raw = ttk.Frame(self.notebook)
        self.tab_consolidated = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_friendly, text="Resumo amigável")
        self.notebook.add(self.tab_raw, text="Campos brutos")
        self.notebook.add(self.tab_consolidated, text="Consolidado")

        self.friendly_text = self._make_text(self.tab_friendly)
        self.raw_text = self._make_text(self.tab_raw)
        self.consolidated_text = self._make_text(self.tab_consolidated)

    def _make_text(self, parent: ttk.Frame) -> tk.Text:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        text = tk.Text(parent, wrap="word", font=("Consolas", 10))
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        return text

    def _apply_dnd(self) -> None:
        if not HAS_DND:
            return
        for target in [self.root, self.tree]:
            target.drop_target_register(DND_FILES)
            target.dnd_bind("<<Drop>>", self.on_drop)

    def on_drop(self, event: Any) -> None:
        paths = split_dnd_paths(getattr(event, "data", ""))
        self.add_files(paths)

    def import_logs(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecione um ou mais logs",
            filetypes=[("Logs de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        self.add_files(list(paths))

    def add_files(self, paths: List[str]) -> None:
        added = 0
        errors: List[str] = []
        existing = {a.file_path for a in self.analyses}
        for path in paths:
            if not path:
                continue
            path = os.path.normpath(path)
            if not os.path.isfile(path):
                continue
            if path in existing:
                continue
            try:
                analysis = LogParser.parse_file(path)
                self.analyses.append(analysis)
                added += 1
                existing.add(path)
                self._append_to_tree(analysis)
            except Exception as exc:
                errors.append(f"{path}: {exc}")
        self.status_var.set(f"{added} log(s) importado(s). Total na lista: {len(self.analyses)}")
        self.refresh_consolidated_report()
        if errors:
            messagebox.showwarning("Alguns arquivos falharam", "\n\n".join(errors[:10]))
        if added and not self.tree.selection():
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.on_select(None)

    def _append_to_tree(self, analysis: LogAnalysis) -> None:
        iid = self.tree.insert(
            "",
            "end",
            values=(
                analysis.file_name,
                analysis.document or analysis.file_name,
                analysis.fabric_from_name or "—",
                fmt_mm_as_m(analysis.actual_print_length_mm),
                fmt_duration(analysis.duration_seconds),
                fmt_num(analysis.total_ink_ml, 2, " mL"),
            ),
        )
        self._analysis_by_tree_id[iid] = analysis

    def get_selected_analysis(self) -> Optional[LogAnalysis]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self._analysis_by_tree_id.get(sel[0])

    def on_select(self, event: Any) -> None:
        self.refresh_selected_report()

    def refresh_selected_report(self) -> None:
        analysis = self.get_selected_analysis()
        if not analysis:
            for widget in [self.friendly_text, self.raw_text]:
                widget.delete("1.0", "end")
            return
        self.friendly_text.delete("1.0", "end")
        self.friendly_text.insert("1.0", self.build_friendly_report(analysis))
        self.raw_text.delete("1.0", "end")
        self.raw_text.insert("1.0", self.build_raw_report(analysis))

    def refresh_consolidated_report(self) -> None:
        self.consolidated_text.delete("1.0", "end")
        self.consolidated_text.insert("1.0", self.build_consolidated_report())

    def refresh_all_reports(self) -> None:
        self.estimator = CostEstimator(self.config)
        self.refresh_selected_report()
        self.refresh_consolidated_report()

    def save_config(self) -> None:
        self.config.save(self.config_path)
        self.estimator = CostEstimator(self.config)
        self.status_var.set("Configurações salvas. Clique em 'Atualizar informações' se quiser recalcular manualmente.")

    def open_config(self) -> None:
        ConfigDialog(self, self.config)

    def remove_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione um log para remover.")
            return
        for iid in selection:
            analysis = self._analysis_by_tree_id.pop(iid, None)
            if analysis is not None:
                self.analyses = [a for a in self.analyses if a.file_path != analysis.file_path]
            self.tree.delete(iid)
        self.status_var.set(f"Total na lista: {len(self.analyses)} log(s).")
        self.refresh_selected_report()
        self.refresh_consolidated_report()
        children = self.tree.get_children()
        if children and not self.tree.selection():
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
            self.on_select(None)

    def clear_all(self) -> None:
        if not self.analyses:
            return
        if not messagebox.askyesno("Confirmar", "Deseja remover todos os logs da lista?"):
            return
        self.analyses.clear()
        self._analysis_by_tree_id.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.friendly_text.delete("1.0", "end")
        self.raw_text.delete("1.0", "end")
        self.refresh_consolidated_report()
        self.status_var.set("Lista limpa.")

    def build_friendly_report(self, analysis: LogAnalysis) -> str:
        est = CostEstimator(self.config)
        paper_weight = est.estimate_paper_weight_kg(analysis)
        paper_cost = est.estimate_paper_cost(analysis)
        ink_cost = est.estimate_ink_cost(analysis)
        total_cost = est.estimate_total_cost(analysis)
        item = analysis.primary_item

        lines: List[str] = []
        lines.append(f"ARQUIVO: {analysis.file_name}")
        lines.append(f"CAMINHO: {analysis.file_path}")
        lines.append(f"TAMANHO DO ARQUIVO: {human_bytes(analysis.file_size_bytes)}")
        lines.append("")

        lines.append("1) IDENTIFICAÇÃO")
        lines.append(f"- Documento: {analysis.document or '—'}")
        lines.append(f"- Tecido inferido pelo nome: {analysis.fabric_from_name or '—'}")
        lines.append(f"- JobID: {analysis.job_id or '—'}")
        lines.append(f"- Computador de origem: {analysis.computer_name or '—'}")
        lines.append(f"- Driver / impressora: {analysis.driver or '—'}")
        lines.append(f"- Versão do software: {analysis.software_version or '—'}")
        lines.append(f"- Arquivos no job: {analysis.file_count if analysis.file_count is not None else '—'}")
        lines.append(f"- Cópia atual / total de cópias: {analysis.copy if analysis.copy is not None else '—'} / {analysis.total_copies if analysis.total_copies is not None else '—'}")
        lines.append(f"- Itens encontrados no log: {analysis.item_count}")
        lines.append("")

        lines.append("2) TEMPO")
        lines.append(f"- Início: {analysis.start_time.strftime(DATE_FMT) if analysis.start_time else '—'}")
        lines.append(f"- Fim: {analysis.end_time.strftime(DATE_FMT) if analysis.end_time else '—'}")
        lines.append(f"- Tempo de impressão: {fmt_duration(analysis.duration_seconds)}")
        lines.append(f"- Velocidade média aproximada: {fmt_num(analysis.avg_speed_m_per_min, 3, ' m/min')}")
        lines.append("")

        lines.append("3) TAMANHOS E ESPAÇOS")
        lines.append(f"- Largura da página/papel configurado no log: {fmt_num(analysis.page_width_mm, 1, ' mm')} ({fmt_mm_as_m(analysis.page_width_mm)})")
        lines.append(f"- Largura útil de impressão: {fmt_num(analysis.print_width_mm, 1, ' mm')} ({fmt_mm_as_m(analysis.print_width_mm)})")
        lines.append(f"- Altura total da área impressa do job: {fmt_num(analysis.print_height_mm, 1, ' mm')} ({fmt_mm_as_m(analysis.print_height_mm)})")
        if item:
            lines.append(f"- Largura real do item: {fmt_num(item.width_mm, 1, ' mm')} ({fmt_mm_as_m(item.width_mm)})")
            lines.append(f"- Altura real do item: {fmt_num(item.height_mm, 1, ' mm')} ({fmt_mm_as_m(item.height_mm)})")
            lines.append(f"- Espaço antes da impressão (offset vertical): {fmt_num(item.v_position_mm, 1, ' mm')} ({fmt_mm_as_m(item.v_position_mm)})")
            after_print = analysis.space_after_print_mm
            after_print_msg = f"{fmt_num(after_print, 1, ' mm')} ({fmt_mm_as_m(after_print)})" if after_print is not None else "Não informado explicitamente neste tipo de log"
            lines.append(f"- Espaço depois da impressão: {after_print_msg}")
            lines.append(f"- Consumo total de papel até o fim da impressão: {fmt_num(analysis.total_paper_used_mm, 1, ' mm')} ({fmt_mm_as_m(analysis.total_paper_used_mm)})")
            lines.append(f"- Margem esquerda: {fmt_num(analysis.left_margin_mm, 1, ' mm')}")
            lines.append(f"- Margem direita: {fmt_num(analysis.right_margin_mm, 1, ' mm')}")
            lines.append(f"- Faixa não imprimível / folga lateral da página para a área útil: {fmt_num(analysis.usable_width_gap_mm, 1, ' mm')}")
            lines.append(f"- Ocupação da largura útil pelo item: {fmt_num(analysis.width_occupancy_percent, 2, '%')}")
        lines.append(f"- Área impressa aproximada: {fmt_num(analysis.print_area_m2, 4, ' m²')}")
        lines.append("")

        lines.append("4) RASTER E RESOLUÇÃO")
        lines.append(f"- PrintWidth_Dots: {analysis.print_width_dots if analysis.print_width_dots is not None else '—'}")
        lines.append(f"- PrintHeight_Dots: {analysis.print_height_dots if analysis.print_height_dots is not None else '—'}")
        lines.append(f"- Bits por pixel: {analysis.bits_per_pixel if analysis.bits_per_pixel is not None else '—'}")
        lines.append(f"- Modo de impressão: {analysis.print_mode or '—'}")
        lines.append(f"- Configurações avançadas: {analysis.advanced_settings or '—'}")
        lines.append("")

        lines.append("5) TINTA")
        lines.append(f"- Inkset: {analysis.inkset or '—'}")
        lines.append(f"- InkLimit: {fmt_num(analysis.ink_limit_percent, 2, '%')}")
        lines.append(f"- InkUsage: {fmt_num(analysis.ink_usage_percent, 2, '%')}")
        lines.append(f"- Tinta total estimada: {fmt_num(analysis.total_ink_ml, 5, ' mL')}")
        lines.append(f"- Total de gotas estimado: {analysis.total_drops if analysis.total_drops is not None else '—'}")
        lines.append(f"- Consumo de tinta por metro linear: {fmt_num((analysis.total_ink_ml / (analysis.actual_print_length_mm / 1000.0)) if analysis.total_ink_ml is not None and analysis.actual_print_length_mm not in (None, 0) else None, 4, ' mL/m')}")
        lines.append(f"- Consumo de tinta por metro quadrado: {fmt_num((analysis.total_ink_ml / analysis.print_area_m2) if analysis.total_ink_ml is not None and analysis.print_area_m2 not in (None, 0) else None, 4, ' mL/m²')}")
        for ch in CHANNELS:
            chd = analysis.channels.get(ch)
            if not chd:
                continue
            sizes = ", ".join(fmt_num(v, 2, "") for v in chd.drop_sizes) if chd.drop_sizes else "—"
            lines.append(
                f"  - Canal {ch}: {fmt_num(chd.ml, 5, ' mL')} | participação {fmt_num(pct(chd.ml, analysis.total_ink_ml), 2, '%')} | "
                f"gotas L1/L2/L3 = {chd.level_1 if chd.level_1 is not None else '—'}/{chd.level_2 if chd.level_2 is not None else '—'}/{chd.level_3 if chd.level_3 is not None else '—'} | "
                f"total = {chd.total_drops if chd.total_drops is not None else '—'} | tamanhos = {sizes}"
            )
        lines.append("")

        lines.append("6) COR E PROCESSAMENTO")
        lines.append(f"- Scheme: {analysis.scheme or '—'}")
        lines.append(f"- Linearização: {analysis.linearization or '—'}")
        lines.append(f"- Pós-linearização: {analysis.post_linearization or '—'}")
        lines.append(f"- ICC: {analysis.icc or '—'}")
        lines.append(f"- Preset: {analysis.preset or '—'}")
        lines.append(f"- Revisão: {analysis.revision or '—'}")
        lines.append(f"- HuemanVersion: {analysis.hueman_version or '—'}")
        lines.append(f"- Shadow optimizer: {fmt_num(analysis.shadow_optimizer_percent, 2, '%')}")
        lines.append(f"- Rendering imagem: {analysis.rendering_img or '—'}")
        lines.append(f"- Rendering vetor: {analysis.rendering_vect or '—'}")
        lines.append(f"- Rendering spot: {analysis.rendering_spot or '—'}")
        lines.append(f"- CMM: {analysis.cmm or '—'}")
        lines.append(f"- Halftoning: {analysis.halftoning or '—'}")
        lines.append(f"- Correction: {analysis.correction or '—'}")
        lines.append(f"- Overprint NXCM: {analysis.nxcm_overprint or '—'}")
        lines.append("")

        lines.append("7) PERFIS E AJUSTES DO ITEM")
        if item:
            lines.append(f"- Item: {item.name or '—'}")
            lines.append(f"- Gray ICC: {item.gray_icc or '—'}")
            lines.append(f"- RGB ICC: {item.rgb_icc or '—'}")
            lines.append(f"- CMYK ICC: {item.cmyk_icc or '—'}")
            lines.append(f"- Proofing ICC: {item.proofing_icc or '—'}")
            lines.append(f"- Brilho / Contraste / Saturação: {item.brightness or '—'} / {item.contrast or '—'} / {item.saturation or '—'}")
            lines.append(f"- Substituição de cor: {item.color_replacement or '—'}")
        else:
            lines.append("- Nenhum item encontrado no log.")
        lines.append("")

        lines.append("8) CUSTOS ESTIMADOS (com base na configuração salva)")
        lines.append(f"- Papel configurado: {self.config.paper.name}")
        lines.append(f"- Peso estimado do papel consumido: {fmt_num(paper_weight, 4, ' kg')}")
        lines.append(f"- Custo estimado do papel: R$ {fmt_num(paper_cost, 4, '')}")
        lines.append(f"- Custo estimado de tinta: R$ {fmt_num(ink_cost, 4, '')}")
        lines.append(f"- Custo total estimado: R$ {fmt_num(total_cost, 4, '')}")
        lines.append("")

        lines.append("9) LIMITES DE LEITURA")
        limits = [
            "Este tipo de log mostra muito bem metragem, área, tempo, tinta e preset.",
            "Espaço depois da impressão nem sempre aparece explicitamente; quando o log não informa, o programa mostra isso como indisponível.",
            "Quantidade real de cópias concluídas em uma impressão interrompida não pode ser provada só por este log, a menos que a metragem unitária esperada seja conhecida fora dele.",
            "O tecido exibido aqui é inferido pelo nome do documento, não uma confirmação física do tecido colocado na máquina.",
        ]
        lines.append(list_to_multiline(limits))
        lines.append("")

        return "\n".join(lines)

    def build_consolidated_report(self) -> str:
        if not self.analyses:
            return "Nenhum log importado.\n\nImporte ou arraste um ou mais logs para ver o consolidado aqui."

        est = CostEstimator(self.config)
        analyses = self.analyses
        valid_lengths = [a.actual_print_length_mm for a in analyses if a.actual_print_length_mm is not None]
        valid_before = [a.space_before_print_mm for a in analyses if a.space_before_print_mm is not None]
        valid_total_paper = [a.total_paper_used_mm for a in analyses if a.total_paper_used_mm is not None]
        valid_areas = [a.print_area_m2 for a in analyses if a.print_area_m2 is not None]
        valid_inks = [a.total_ink_ml for a in analyses if a.total_ink_ml is not None]
        valid_durations = [a.duration_seconds for a in analyses if a.duration_seconds is not None]
        valid_speeds = [a.avg_speed_m_per_min for a in analyses if a.avg_speed_m_per_min is not None]
        valid_costs_paper = [est.estimate_paper_cost(a) for a in analyses if est.estimate_paper_cost(a) is not None]
        valid_costs_ink = [est.estimate_ink_cost(a) for a in analyses if est.estimate_ink_cost(a) is not None]
        valid_costs_total = [est.estimate_total_cost(a) for a in analyses if est.estimate_total_cost(a) is not None]

        def sum_or_none(values):
            return sum(values) if values else None

        fabric_counts: Dict[str, int] = {}
        scheme_counts: Dict[str, int] = {}
        computer_counts: Dict[str, int] = {}
        driver_counts: Dict[str, int] = {}
        channel_totals: Dict[str, float] = {ch: 0.0 for ch in CHANNELS}
        files_seen: Dict[tuple, int] = {}

        for a in analyses:
            fabric = a.fabric_from_name or "Não identificado"
            scheme = a.scheme or "Não identificado"
            computer = a.computer_name or "Não identificado"
            driver = a.driver or "Não identificado"
            fabric_counts[fabric] = fabric_counts.get(fabric, 0) + 1
            scheme_counts[scheme] = scheme_counts.get(scheme, 0) + 1
            computer_counts[computer] = computer_counts.get(computer, 0) + 1
            driver_counts[driver] = driver_counts.get(driver, 0) + 1
            files_seen[(a.job_id, a.document, a.start_time, a.end_time)] = files_seen.get((a.job_id, a.document, a.start_time, a.end_time), 0) + 1
            for ch in CHANNELS:
                ch_ml = a.channels.get(ch).ml if a.channels.get(ch) else None
                if ch_ml is not None:
                    channel_totals[ch] += ch_ml

        duplicated = [key for key, count in files_seen.items() if count > 1]
        longest = max(analyses, key=lambda a: a.actual_print_length_mm or -1)
        most_ink = max(analyses, key=lambda a: a.total_ink_ml or -1)
        slowest = max(analyses, key=lambda a: a.duration_seconds or -1)

        lines: List[str] = []
        lines.append("CONSOLIDADO DOS LOGS CARREGADOS")
        lines.append("=" * 70)
        lines.append(f"Quantidade de logs: {len(analyses)}")
        lines.append(f"Metragem total realmente impressa: {fmt_mm_as_m(sum_or_none(valid_lengths))}")
        lines.append(f"Espaço total antes da impressão: {fmt_mm_as_m(sum_or_none(valid_before))}")
        lines.append(f"Consumo total estimado de papel até o fim da impressão: {fmt_mm_as_m(sum_or_none(valid_total_paper))}")
        lines.append(f"Espaço depois da impressão: indisponível quando o log não informa explicitamente")
        lines.append(f"Área total impressa: {fmt_num(sum_or_none(valid_areas), 4, ' m²')}")
        lines.append(f"Tinta total estimada: {fmt_num(sum_or_none(valid_inks), 5, ' mL')}")
        lines.append(f"Tempo total de impressão: {fmt_duration(sum_or_none(valid_durations))}")
        avg_speed = (sum(valid_speeds) / len(valid_speeds)) if valid_speeds else None
        lines.append(f"Velocidade média dos jobs: {fmt_num(avg_speed, 4, ' m/min')}")
        lines.append(f"Custo total estimado do papel: R$ {fmt_num(sum_or_none(valid_costs_paper), 4, '')}")
        lines.append(f"Custo total estimado de tinta: R$ {fmt_num(sum_or_none(valid_costs_ink), 4, '')}")
        lines.append(f"Custo total estimado geral: R$ {fmt_num(sum_or_none(valid_costs_total), 4, '')}")
        lines.append("")

        lines.append("TINTA POR CANAL")
        for ch in CHANNELS:
            total_ch = channel_totals[ch]
            total_all = sum_or_none(valid_inks)
            lines.append(f"- {ch}: {fmt_num(total_ch if total_ch > 0 else None, 5, ' mL')} | participação {fmt_num(pct(total_ch, total_all) if total_all else None, 2, '%')}")
        lines.append("")

        def append_ranking(title: str, data: Dict[str, int]) -> None:
            lines.append(title)
            for name, count in sorted(data.items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"- {name}: {count}")
            lines.append("")

        append_ranking("TECIDOS ENCONTRADOS", fabric_counts)
        append_ranking("SCHEMES / PRESETS ENCONTRADOS", scheme_counts)
        append_ranking("COMPUTADORES DE ORIGEM", computer_counts)
        append_ranking("DRIVERS ENCONTRADOS", driver_counts)

        lines.append("DESTAQUES")
        lines.append(f"- Maior job em metragem: {longest.file_name} | {fmt_mm_as_m(longest.actual_print_length_mm)}")
        lines.append(f"- Job com maior tinta: {most_ink.file_name} | {fmt_num(most_ink.total_ink_ml, 5, ' mL')}")
        lines.append(f"- Job mais demorado: {slowest.file_name} | {fmt_duration(slowest.duration_seconds)}")
        lines.append("")

        lines.append("POSSÍVEIS ALERTAS")
        if duplicated:
            lines.append(f"- Há {len(duplicated)} chave(s) repetida(s) por JobID + documento + início/fim. Vale revisar duplicidade.")
        else:
            lines.append("- Nenhuma duplicidade óbvia encontrada pela chave simples JobID + documento + início/fim.")
        if any(a.space_after_print_mm is None for a in analyses):
            lines.append("- O campo de espaço depois da impressão não está disponível neste tipo de log, salvo quando vier explicitamente no arquivo.")
        lines.append("- Custos dependem inteiramente das configurações salvas de papel e tintas. Use 'Atualizar informações' depois de alterar esses valores.")
        lines.append("")

        return "\n".join(lines)

    def build_raw_report(self, analysis: LogAnalysis) -> str:
        parts: List[str] = []
        for section_name, items in analysis.raw_sections.items():
            parts.append(f"[{section_name}]")
            if items:
                for key, value in items.items():
                    parts.append(f"{key} = {value}")
            else:
                parts.append("(vazio)")
            parts.append("")
        return "\n".join(parts)


    def export_report_txt(self) -> None:
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if current_tab == "Consolidado":
            default_name = "logs_consolidado.txt"
            content = self.build_consolidated_report()
        else:
            analysis = self.get_selected_analysis()
            if not analysis:
                messagebox.showinfo("Aviso", "Selecione um log primeiro.")
                return
            default_name = Path(analysis.file_name).stem + "_relatorio.txt"
            content = self.build_friendly_report(analysis) if current_tab == "Resumo amigável" else self.build_raw_report(analysis)
        path = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Texto", "*.txt")],
        )
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Concluído", "Relatório exportado com sucesso.")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = LogConsultorApp()
    app.run()
