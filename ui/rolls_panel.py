from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable

from application.operations_panel_service import (
    OpenRollRow,
    OperationsPanelService,
    RollListFilters,
    RollSummaryDTO,
)
from ui.roll_export_result_dialog import RollExportResultDialog


TREE_ROW_HEIGHT = 26


class RollsPanel(ttk.Frame):
    """
    Painel de consulta de rolos em modo content-only.

    O shell (sidebar, topbar, footer e ações rápidas globais)
    pertence ao MainWindow.

    Esta página mostra apenas:
    - filtros
    - lista de rolos
    - detalhes do rolo selecionado
    """

    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.master = master
        self.service = service or OperationsPanelService()

        self.status_var = tk.StringVar(value="ALL")
        self.machine_var = tk.StringVar(value="ALL")
        self.search_var = tk.StringVar(value="")
        self.rolls_count_var = tk.StringVar(value="0")
        self.detail_title_var = tk.StringVar(value="Nenhum rolo selecionado")
        self.detail_status_var = tk.StringVar(value="-")
        self.detail_machine_var = tk.StringVar(value="-")
        self.detail_fabric_var = tk.StringVar(value="-")
        self.detail_note_var = tk.StringVar(value="-")
        self.detail_jobs_var = tk.StringVar(value="0")
        self.detail_planned_var = tk.StringVar(value="0.00 m")
        self.detail_effective_var = tk.StringVar(value="0.00 m")
        self.detail_gap_var = tk.StringVar(value="0.00 m")
        self.detail_consumed_var = tk.StringVar(value="0.00 m")
        self.detail_pending_var = tk.StringVar(value="0")
        self.detail_ok_var = tk.StringVar(value="0")
        self.detail_suspicious_var = tk.StringVar(value="0")

        self.current_summary: RollSummaryDTO | None = None

        self.rolls_tree: ttk.Treeview
        self.items_tree: ttk.Treeview
        self.status_combo: ttk.Combobox
        self.machine_combo: ttk.Combobox

        self._configure_styles()
        self._build_ui()
        self.refresh_all()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", rowheight=TREE_ROW_HEIGHT)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("MetricValue.TLabel", font=("Segoe UI", 11, "bold"))

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        self._build_filters()
        self._build_left_panel()
        self._build_right_panel()

    def _build_filters(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros", style="Section.TLabelframe", padding=10)
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for col in range(6):
            filters.columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        ttk.Label(filters, text="Status").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.status_combo = ttk.Combobox(filters, textvariable=self.status_var, state="readonly")
        self.status_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Máquina").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.machine_combo = ttk.Combobox(filters, textvariable=self.machine_var, state="readonly")
        self.machine_combo.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Busca").grid(row=0, column=4, sticky="w", padx=(0, 6))
        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=5, sticky="ew")

        actions = ttk.Frame(filters)
        actions.grid(row=1, column=0, columnspan=6, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Limpar filtros", command=self.clear_filters).pack(side="right")
        ttk.Button(actions, text="Atualizar", command=self.refresh_all).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="Aplicar filtros", command=self.refresh_rolls).pack(side="right", padx=(0, 8))

    def _build_left_panel(self) -> None:
        panel = ttk.LabelFrame(self, text="Lista de rolos", style="Section.TLabelframe")
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        actions = ttk.Frame(panel, padding=(8, 8, 8, 8))
        actions.grid(row=0, column=0, sticky="ew")
        ttk.Label(actions, text="Total visível:").pack(side="left")
        ttk.Label(actions, textvariable=self.rolls_count_var, style="MetricValue.TLabel").pack(side="left", padx=(6, 0))

        tree_wrap = ttk.Frame(panel, padding=(8, 0, 8, 8))
        tree_wrap.grid(row=1, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        self.rolls_tree = ttk.Treeview(
            tree_wrap,
            columns=("roll_id", "roll_name", "machine", "fabric", "jobs", "consumed", "status"),
            show="headings",
            selectmode="browse",
        )
        self.rolls_tree.grid(row=0, column=0, sticky="nsew")
        self.rolls_tree.bind("<<TreeviewSelect>>", lambda event: self.load_selected_roll_detail())
        self.rolls_tree.bind("<Double-1>", lambda event: self.load_selected_roll_detail())

        sb_y = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.rolls_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.rolls_tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self.rolls_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self._configure_rolls_tree_columns()

    def _build_right_panel(self) -> None:
        panel = ttk.LabelFrame(self, text="Detalhes do rolo", style="Section.TLabelframe")
        panel.grid(row=1, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        top = ttk.Frame(panel, padding=8)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)

        ttk.Label(top, textvariable=self.detail_title_var, style="MetricValue.TLabel", wraplength=420).grid(
            row=0, column=0, sticky="w"
        )

        meta = ttk.Frame(panel, padding=(8, 0, 8, 8))
        meta.grid(row=1, column=0, sticky="ew")
        meta.columnconfigure(1, weight=1)

        self._meta_row(meta, 0, "Status", self.detail_status_var)
        self._meta_row(meta, 1, "Máquina", self.detail_machine_var)
        self._meta_row(meta, 2, "Tecido", self.detail_fabric_var)
        self._meta_row(meta, 3, "Observação", self.detail_note_var)

        items_box = ttk.LabelFrame(panel, text="Itens do rolo", style="Section.TLabelframe", padding=8)
        items_box.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        items_box.columnconfigure(0, weight=1)
        items_box.rowconfigure(0, weight=1)

        self.items_tree = ttk.Treeview(
            items_box,
            columns=("row_id", "job_id", "fabric", "review", "consumed"),
            show="headings",
            selectmode="browse",
            height=12,
        )
        self.items_tree.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(items_box, orient="vertical", command=self.items_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        self.items_tree.configure(yscrollcommand=sb_y.set)

        self._configure_items_tree_columns()

        metrics = ttk.LabelFrame(panel, text="Resumo", style="Section.TLabelframe", padding=8)
        metrics.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)

        self._metric(metrics, 0, 0, "Jobs", self.detail_jobs_var)
        self._metric(metrics, 0, 1, "Planejado", self.detail_planned_var)
        self._metric(metrics, 1, 0, "Efetivo", self.detail_effective_var)
        self._metric(metrics, 1, 1, "Gap", self.detail_gap_var)
        self._metric(metrics, 2, 0, "Consumido", self.detail_consumed_var)
        self._metric(metrics, 2, 1, "Pendentes", self.detail_pending_var)
        self._metric(metrics, 3, 0, "Revisados OK", self.detail_ok_var)
        self._metric(metrics, 3, 1, "Suspeitos", self.detail_suspicious_var)

        actions = ttk.Frame(panel, padding=8)
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        ttk.Button(actions, text="Ver detalhe textual", command=self.show_detail_dialog).grid(row=0, column=0, sticky="ew")
        ttk.Button(actions, text="Exportar novamente", command=self.export_selected_roll).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )

    def _meta_row(self, master: tk.Misc, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(master, text=f"{label}:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=2)
        ttk.Label(master, textvariable=variable, wraplength=320, justify="left").grid(
            row=row, column=1, sticky="ew", pady=2
        )

    def _metric(self, master: tk.Misc, row: int, col: int, label: str, variable: tk.StringVar) -> None:
        box = ttk.Frame(master)
        box.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        ttk.Label(box, text=label).pack(anchor="w")
        ttk.Label(box, textvariable=variable, style="MetricValue.TLabel").pack(anchor="w")

    def _configure_rolls_tree_columns(self) -> None:
        spec = {
            "roll_id": ("ID", 70),
            "roll_name": ("Rolo", 220),
            "machine": ("Máquina", 90),
            "fabric": ("Tecido", 120),
            "jobs": ("Jobs", 70),
            "consumed": ("Consumido (m)", 120),
            "status": ("Status", 100),
        }
        for col, (title, width) in spec.items():
            self.rolls_tree.heading(col, text=title)
            anchor = "w" if col in {"roll_name", "fabric"} else "center"
            self.rolls_tree.column(col, width=width, minwidth=width, anchor=anchor)

    def _configure_items_tree_columns(self) -> None:
        spec = {
            "row_id": ("ID", 60),
            "job_id": ("Job", 80),
            "fabric": ("Tecido", 120),
            "review": ("Review", 110),
            "consumed": ("Cons. (m)", 90),
        }
        for col, (title, width) in spec.items():
            self.items_tree.heading(col, text=title)
            anchor = "w" if col in {"fabric", "review"} else "center"
            self.items_tree.column(col, width=width, minwidth=width, anchor=anchor)

    def clear_filters(self) -> None:
        self.status_var.set("ALL")
        self.machine_var.set("ALL")
        self.search_var.set("")
        self.refresh_rolls()

    def refresh_all(self) -> None:
        self._load_filter_values()
        self.refresh_rolls()

    def _load_filter_values(self) -> None:
        values = self.service.get_roll_filter_values()

        status_values = ["ALL", *values.get("statuses", [])]
        machine_values = ["ALL", *values.get("machines", [])]

        self.status_combo["values"] = status_values
        self.machine_combo["values"] = machine_values

        if self.status_var.get() not in status_values:
            self.status_var.set("ALL")
        if self.machine_var.get() not in machine_values:
            self.machine_var.set("ALL")

    def refresh_rolls(self) -> None:
        filters = RollListFilters(
            status=self._none_if_all(self.status_var.get()),
            machine=self._none_if_all(self.machine_var.get()),
            search=(self.search_var.get() or "").strip() or None,
            limit=None,
        )

        rows = self.service.list_rolls(filters)
        self._populate_rolls_tree(rows)
        self.rolls_count_var.set(str(len(rows)))

        if not rows:
            self.current_summary = None
            self._clear_detail_panel()
            return

        first_item = self.rolls_tree.get_children()
        if first_item:
            self.rolls_tree.selection_set(first_item[0])
            self.rolls_tree.focus(first_item[0])
            self.load_selected_roll_detail()

    def load_selected_roll_detail(self) -> None:
        roll_id = self._get_selected_roll_id()
        if roll_id is None:
            return

        summary = self.service.get_roll_summary(roll_id)
        self.current_summary = summary
        self._apply_summary(summary)

    def export_selected_roll(self) -> None:
        if self.current_summary is None:
            messagebox.showwarning("Rolos", "Selecione um rolo primeiro.", parent=self)
            return

        directory = filedialog.askdirectory(title="Selecione a pasta de exportação", parent=self)
        if not directory:
            return

        result = self.service.export_roll(
            roll_id=self.current_summary.roll_id,
            output_dir=Path(directory),
        )

        dialog = RollExportResultDialog(self.winfo_toplevel(), result=result)
        self.wait_window(dialog)

    def show_detail_dialog(self) -> None:
        if self.current_summary is None:
            messagebox.showinfo("Rolos", "Nenhum rolo selecionado.", parent=self)
            return

        s = self.current_summary
        text = (
            f"Rolo: {s.roll_name}\n"
            f"ID: {s.roll_id}\n"
            f"Status: {s.status}\n"
            f"Máquina: {s.machine}\n"
            f"Tecido: {s.fabric or '-'}\n"
            f"Jobs: {s.jobs_count}\n"
            f"Planejado: {self._fmt_m(s.total_planned_m)}\n"
            f"Efetivo: {self._fmt_m(s.total_effective_m)}\n"
            f"Gap: {self._fmt_m(s.total_gap_m)}\n"
            f"Consumido: {self._fmt_m(s.total_consumed_m)}\n"
            f"Pendentes: {s.pending_review_count}\n"
            f"Revisados OK: {s.reviewed_ok_count}\n"
            f"Suspeitos: {s.suspicious_count}\n"
            f"Observação: {s.note or '-'}"
        )
        messagebox.showinfo("Detalhes do rolo", text, parent=self)

    def _populate_rolls_tree(self, rows: Iterable[OpenRollRow]) -> None:
        self._clear_tree(self.rolls_tree)
        for row in rows:
            self.rolls_tree.insert(
                "",
                "end",
                values=(
                    row.roll_id,
                    row.roll_name,
                    row.machine,
                    row.fabric or "-",
                    row.jobs_count,
                    self._fmt_num(row.total_consumed_m),
                    row.status,
                ),
            )

    def _apply_summary(self, summary: RollSummaryDTO) -> None:
        self.detail_title_var.set(f"{summary.roll_name} (ID {summary.roll_id})")
        self.detail_status_var.set(summary.status)
        self.detail_machine_var.set(summary.machine)
        self.detail_fabric_var.set(summary.fabric or "-")
        self.detail_note_var.set(summary.note or "-")

        self.detail_jobs_var.set(str(summary.jobs_count))
        self.detail_planned_var.set(self._fmt_m(summary.total_planned_m))
        self.detail_effective_var.set(self._fmt_m(summary.total_effective_m))
        self.detail_gap_var.set(self._fmt_m(summary.total_gap_m))
        self.detail_consumed_var.set(self._fmt_m(summary.total_consumed_m))
        self.detail_pending_var.set(str(summary.pending_review_count))
        self.detail_ok_var.set(str(summary.reviewed_ok_count))
        self.detail_suspicious_var.set(str(summary.suspicious_count))

        self._populate_items_tree(summary.items)

    def _populate_items_tree(self, items: Iterable) -> None:
        self._clear_tree(self.items_tree)
        for item in items:
            self.items_tree.insert(
                "",
                "end",
                values=(
                    item.row_id or "-",
                    item.job_id,
                    item.fabric or "-",
                    item.review_status or "-",
                    self._fmt_num(item.consumed_length_m),
                ),
            )

    def _clear_detail_panel(self) -> None:
        self.detail_title_var.set("Nenhum rolo selecionado")
        self.detail_status_var.set("-")
        self.detail_machine_var.set("-")
        self.detail_fabric_var.set("-")
        self.detail_note_var.set("-")
        self.detail_jobs_var.set("0")
        self.detail_planned_var.set("0.00 m")
        self.detail_effective_var.set("0.00 m")
        self.detail_gap_var.set("0.00 m")
        self.detail_consumed_var.set("0.00 m")
        self.detail_pending_var.set("0")
        self.detail_ok_var.set("0")
        self.detail_suspicious_var.set("0")
        self._clear_tree(self.items_tree)

    def _get_selected_roll_id(self) -> int | None:
        selection = self.rolls_tree.selection()
        if not selection:
            return None
        values = self.rolls_tree.item(selection[0], "values")
        if not values:
            return None
        try:
            return int(values[0])
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clear_tree(tree: ttk.Treeview) -> None:
        for item_id in tree.get_children():
            tree.delete(item_id)

    @staticmethod
    def _none_if_all(value: str | None) -> str | None:
        text = (value or "").strip()
        if not text or text.upper() == "ALL":
            return None
        return text

    @staticmethod
    def _fmt_num(value: float | None) -> str:
        return f"{float(value or 0.0):.2f}"

    @staticmethod
    def _fmt_m(value: float | None) -> str:
        return f"{float(value or 0.0):.2f} m"


def run_rolls_panel(service: OperationsPanelService | None = None) -> None:
    root = tk.Tk()
    RollsPanel(root, service=service)
    root.mainloop()


def main() -> None:
    run_rolls_panel()


if __name__ == "__main__":
    main()