# ui/common_widgets.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


TREE_ROW_HEIGHT = 24


def apply_common_styles() -> None:
    """
    Aplica estilos compartilhados da UI local.

    Direção atual:
    - visual simples
    - legibilidade antes de refinamento
    - seguro para chamar várias vezes
    """
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Treeview", rowheight=TREE_ROW_HEIGHT)
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
    style.configure("MetricLabel.TLabel", font=("Segoe UI", 9))
    style.configure("MetricValue.TLabel", font=("Segoe UI", 11, "bold"))
    style.configure("PanelTitle.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Muted.TLabel", font=("Segoe UI", 9))


def configure_tree_columns(
    tree: ttk.Treeview,
    spec: dict[str, tuple[str, int]],
    *,
    left_aligned: set[str] | None = None,
) -> None:
    left_aligned = left_aligned or set()

    for col, (title, width) in spec.items():
        tree.heading(col, text=title)
        anchor = "w" if col in left_aligned else "center"
        tree.column(col, width=width, minwidth=width, anchor=anchor, stretch=True)


def clear_tree(tree: ttk.Treeview) -> None:
    for item_id in tree.get_children():
        tree.delete(item_id)


def metric_cell(
    master: tk.Misc,
    *,
    row: int,
    col: int,
    label: str,
    variable: tk.StringVar,
    padx: int = 4,
    pady: int = 8,
) -> ttk.Frame:
    box = ttk.Frame(master)
    box.grid(row=row, column=col, sticky="ew", padx=padx, pady=pady)
    ttk.Label(box, text=label, style="MetricLabel.TLabel").pack(anchor="w")
    ttk.Label(box, textvariable=variable, style="MetricValue.TLabel").pack(anchor="w")
    return box


def meta_cell(
    master: tk.Misc,
    *,
    row: int,
    col: int,
    label: str,
    variable: tk.StringVar,
    wraplength: int = 180,
    padx: int = 4,
    pady: int = 2,
) -> ttk.Frame:
    box = ttk.Frame(master)
    box.grid(row=row, column=col, sticky="ew", padx=padx, pady=pady)
    ttk.Label(box, text=f"{label}:").pack(anchor="w")
    ttk.Label(
        box,
        textvariable=variable,
        wraplength=wraplength,
        justify="left",
    ).pack(anchor="w")
    return box


def fmt_num(value: float | int | None) -> str:
    return f"{_to_float(value):.2f}"


def fmt_m(value: float | int | None) -> str:
    return f"{_to_float(value):.2f} m"


def fmt_percent(value: float | None, *, scale_100: bool = True) -> str:
    if value is None:
        return "-"
    number = _to_float(value)
    if scale_100:
        number *= 100.0
    return f"{number:.1f}%"


def fmt_dt(value: object, *, empty: str = "-") -> str:
    if value is None:
        return empty

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(value)

    text = str(value).strip()
    return text or empty


def _to_float(value: float | int | None) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0