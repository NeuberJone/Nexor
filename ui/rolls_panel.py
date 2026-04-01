# ui/rolls_panel.py
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable

from application.operations_panel_service import (
    OpenRollRow,
    OperationsPanelService,
    RollItemRow,
    RollListFilters,
    RollSummaryDTO,
)
from ui.common_widgets import apply_common_styles, clear_tree, fmt_m, fmt_num
from ui.roll_export_result_dialog import RollExportResultDialog


class RollsPanel(ttk.Frame):
    """
    Tela simplificada de Rolos para testes funcionais.

    Estrutura:
    - filtros básicos
    - lista de rolos
    - detalhe simples do rolo selecionado
    - tabela de itens
    """

    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.service = service or OperationsPanelService()

        self.status_var = tk.StringVar(value="ALL")
        self.machine_var = tk.StringVar(value="ALL")
        self.search_var = tk.StringVar(value="")

        self.rolls_count_var = tk.StringVar(value="0")

        self.roll_title_var = tk.StringVar(value="Nenhum rolo selecionado")
        self.roll_status_var = tk.StringVar(value="-")
        self.roll_machine_var = tk.StringVar(value="-")
        self.roll_fabric_var = tk.StringVar(value="-")
        self.roll_note_var = tk.StringVar(value="-")

        self.roll_jobs_var = tk.StringVar(value="0")
        self.roll_planned_var = tk.StringVar(value="0.00 m")
        self.roll_effective_var = tk.StringVar(value="0.00 m")
        self.roll_gap_var = tk.StringVar(value="0.00 m")
        self.roll_consumed_var = tk.StringVar(value="0.00 m")
        self.roll_pending_var = tk.StringVar(value="0")
        self.roll_ok_var = tk.StringVar(value="0")
        self.roll_suspicious_var = tk.StringVar(value="0")

        self.current_summary: RollSummaryDTO | None = None
        self.current_roll_id: int | None = None

        self.rolls_tree: ttk.Treeview
        self.roll_items_tree: ttk.Treeview
        self.status_combo: ttk.Combobox
        self.machine_combo: ttk.Combobox

        apply_common_styles()
        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_filters()
        self._build_rolls_list()
        self._build_detail_area()

    def _build_filters(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros", padding=8)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
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
        actions.grid(row=1, column=0, columnspan=6, sticky="e", pady=(8, 0))
        ttk.Button(actions, text="Aplicar filtros", command=self.refresh_rolls).pack(side="left")
        ttk.Button(actions, text="Atualizar", command=self.refresh_all).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Limpar filtros", command=self.clear_filters).pack(side="left", padx=(8, 0))

    def _build_rolls_list(self) -> None:
        area = ttk.LabelFrame(self, text="Lista de rolos", padding=8)
        area.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        area.columnconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)

        top = ttk.Frame(area)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Total visível:").grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.rolls_count_var, style="MetricValue.TLabel").grid(
            row=0, column=1, sticky="w", padx=(6, 0)
        )

        self.rolls_tree = ttk.Treeview(
            area,
            columns=("roll_id", "roll_name", "machine", "fabric", "jobs", "consumed", "status"),
            show="headings",
            selectmode="browse",
        )
        self.rolls_tree.grid(row=1, column=0, sticky="nsew")
        self.rolls_tree.bind("<<TreeviewSelect>>", lambda event: self.load_selected_roll_detail())
        self.rolls_tree.bind("<Double-1>", lambda event: self.load_selected_roll_detail())

        self._configure_tree_columns(
            self.rolls_tree,
            {
                "roll_id": ("ID", 60, "center"),
                "roll_name": ("Rolo", 260, "w"),
                "machine": ("Máquina", 90, "center"),
                "fabric": ("Tecido", 120, "w"),
                "jobs": ("Jobs", 70, "center"),
                "consumed": ("Consumido (m)", 120, "center"),
                "status": ("Status", 100, "center"),
            },
        )

        sb_y = ttk.Scrollbar(area, orient="vertical", command=self.rolls_tree.yview)
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(area, orient="horizontal", command=self.rolls_tree.xview)
        sb_x.grid(row=2, column=0, sticky="ew")
        self.rolls_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

    def _build_detail_area(self) -> None:
        area = ttk.LabelFrame(self, text="Rolo selecionado", padding=8)
        area.grid(row=2, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)

        summary = ttk.Frame(area)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(4):
            summary.columnconfigure(col, weight=1)

        ttk.Label(summary, textvariable=self.roll_title_var, style="PanelTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        self._meta_cell(summary, 1, 0, "Status", self.roll_status_var)
        self._meta_cell(summary, 1, 1, "Máquina", self.roll_machine_var)
        self._meta_cell(summary, 1, 2, "Tecido", self.roll_fabric_var)
        self._meta_cell(summary, 1, 3, "Observação", self.roll_note_var)

        self._meta_cell(summary, 2, 0, "Jobs", self.roll_jobs_var)
        self._meta_cell(summary, 2, 1, "Planejado", self.roll_planned_var)
        self._meta_cell(summary, 2, 2, "Efetivo", self.roll_effective_var)
        self._meta_cell(summary, 2, 3, "Gap", self.roll_gap_var)

        self._meta_cell(summary, 3, 0, "Consumido", self.roll_consumed_var)
        self._meta_cell(summary, 3, 1, "Pendentes", self.roll_pending_var)
        self._meta_cell(summary, 3, 2, "Revisados OK", self.roll_ok_var)
        self._meta_cell(summary, 3, 3, "Suspeitos", self.roll_suspicious_var)

        actions = ttk.Frame(summary)
        actions.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Ver detalhe textual", command=self.show_detail_dialog).pack(side="left")
        ttk.Button(actions, text="Exportar novamente", command=self.export_selected_roll).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Atualizar seleção", command=self.load_selected_roll_detail).pack(side="left", padx=(8, 0))

        items_box = ttk.LabelFrame(area, text="Itens do rolo", padding=8)
        items_box.grid(row=1, column=0, sticky="nsew")
        items_box.columnconfigure(0, weight=1)
        items_box.rowconfigure(0, weight=1)

        self.roll_items_tree = ttk.Treeview(
            items_box,
            columns=("row_id", "job_id", "machine", "fabric", "review", "document", "consumed"),
            show="headings",
            selectmode="browse",
        )
        self.roll_items_tree.grid(row=0, column=0, sticky="nsew")

        self._configure_tree_columns(
            self.roll_items_tree,
            {
                "row_id": ("ID", 60, "center"),
                "job_id": ("Job", 90, "center"),
                "machine": ("Máquina", 80, "center"),
                "fabric": ("Tecido", 100, "w"),
                "review": ("Review", 120, "w"),
                "document": ("Documento", 560, "w"),
                "consumed": ("Cons. (m)", 90, "center"),
            },
        )

        sb_y = ttk.Scrollbar(items_box, orient="vertical", command=self.roll_items_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(items_box, orient="horizontal", command=self.roll_items_tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self.roll_items_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

    def _meta_cell(self, master: tk.Misc, row: int, col: int, label: str, variable: tk.StringVar) -> None:
        box = ttk.Frame(master, padding=(0, 2))
        box.grid(row=row, column=col, sticky="w")
        ttk.Label(box, text=f"{label}:").pack(anchor="w")
        ttk.Label(box, textvariable=variable).pack(anchor="w")

    def _configure_tree_columns(
        self,
        tree: ttk.Treeview,
        columns: dict[str, tuple[str, int, str]],
    ) -> None:
        for column_id, (title, width, anchor) in columns.items():
            tree.heading(column_id, text=title)
            tree.column(column_id, width=width, minwidth=width, anchor=anchor, stretch=True)

    # ------------------------------------------------------------------
    # Refresh / filters
    # ------------------------------------------------------------------

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
        previous_roll_id = self.current_roll_id

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
            self.current_roll_id = None
            self.current_summary = None
            self._clear_roll_panel()
            return

        target_roll_id = previous_roll_id if any(row.roll_id == previous_roll_id for row in rows) else rows[0].roll_id
        self._select_roll_in_tree(target_roll_id)
        self.load_selected_roll_detail()

    def load_selected_roll_detail(self) -> None:
        roll_id = self._get_selected_roll_id()
        if roll_id is None:
            return

        summary = self.service.get_roll_detail(roll_id)
        self.current_roll_id = summary.roll_id
        self.current_summary = summary
        self._apply_summary(summary)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

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
        efficiency_text = f"{(s.efficiency_ratio * 100):.1f}%" if s.efficiency_ratio is not None else "-"

        text = (
            f"Rolo: {s.roll_name}\n"
            f"ID: {s.roll_id}\n"
            f"Status: {s.status}\n"
            f"Máquina: {s.machine}\n"
            f"Tecido: {s.fabric or '-'}\n"
            f"Criado em: {self._fmt_dt(s.created_at)}\n"
            f"Fechado em: {self._fmt_dt(s.closed_at)}\n"
            f"Exportado em: {self._fmt_dt(s.exported_at)}\n"
            f"Jobs: {s.jobs_count}\n"
            f"Planejado: {fmt_m(s.total_planned_m)}\n"
            f"Efetivo: {fmt_m(s.total_effective_m)}\n"
            f"Gap: {fmt_m(s.total_gap_m)}\n"
            f"Consumido: {fmt_m(s.total_consumed_m)}\n"
            f"Eficiência: {efficiency_text}\n"
            f"Pendentes: {s.pending_review_count}\n"
            f"Revisados OK: {s.reviewed_ok_count}\n"
            f"Suspeitos: {s.suspicious_count}\n"
            f"Observação: {s.note or '-'}"
        )
        messagebox.showinfo("Detalhes do rolo", text, parent=self)

    # ------------------------------------------------------------------
    # Apply state
    # ------------------------------------------------------------------

    def _populate_rolls_tree(self, rows: Iterable[OpenRollRow]) -> None:
        clear_tree(self.rolls_tree)
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
                    fmt_num(row.total_consumed_m),
                    row.status,
                ),
            )

    def _apply_summary(self, summary: RollSummaryDTO) -> None:
        self.roll_title_var.set(f"{summary.roll_name} (ID {summary.roll_id})")
        self.roll_status_var.set(summary.status)
        self.roll_machine_var.set(summary.machine)
        self.roll_fabric_var.set(summary.fabric or "-")
        self.roll_note_var.set(summary.note or "-")

        self.roll_jobs_var.set(str(summary.jobs_count))
        self.roll_planned_var.set(fmt_m(summary.total_planned_m))
        self.roll_effective_var.set(fmt_m(summary.total_effective_m))
        self.roll_gap_var.set(fmt_m(summary.total_gap_m))
        self.roll_consumed_var.set(fmt_m(summary.total_consumed_m))
        self.roll_pending_var.set(str(summary.pending_review_count))
        self.roll_ok_var.set(str(summary.reviewed_ok_count))
        self.roll_suspicious_var.set(str(summary.suspicious_count))

        self._populate_roll_items_tree(summary.items)

    def _populate_roll_items_tree(self, items: Iterable[RollItemRow]) -> None:
        clear_tree(self.roll_items_tree)
        for item in items:
            self.roll_items_tree.insert(
                "",
                "end",
                values=(
                    item.row_id or "-",
                    item.job_id,
                    item.machine,
                    item.fabric or "-",
                    item.review_status or "-",
                    item.document,
                    fmt_num(item.consumed_length_m),
                ),
            )

    def _clear_roll_panel(self) -> None:
        self.roll_title_var.set("Nenhum rolo selecionado")
        self.roll_status_var.set("-")
        self.roll_machine_var.set("-")
        self.roll_fabric_var.set("-")
        self.roll_note_var.set("-")
        self.roll_jobs_var.set("0")
        self.roll_planned_var.set("0.00 m")
        self.roll_effective_var.set("0.00 m")
        self.roll_gap_var.set("0.00 m")
        self.roll_consumed_var.set("0.00 m")
        self.roll_pending_var.set("0")
        self.roll_ok_var.set("0")
        self.roll_suspicious_var.set("0")
        clear_tree(self.roll_items_tree)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def _select_roll_in_tree(self, roll_id: int) -> None:
        for item_id in self.rolls_tree.get_children():
            values = self.rolls_tree.item(item_id, "values")
            if not values:
                continue
            try:
                value_roll_id = int(values[0])
            except (TypeError, ValueError):
                continue
            if value_roll_id == roll_id:
                self.rolls_tree.selection_set(item_id)
                self.rolls_tree.focus(item_id)
                self.rolls_tree.see(item_id)
                return

    @staticmethod
    def _none_if_all(value: str | None) -> str | None:
        text = (value or "").strip()
        if not text or text.upper() == "ALL":
            return None
        return text

    @staticmethod
    def _fmt_dt(value: object) -> str:
        if value is None:
            return "-"
        if hasattr(value, "strftime"):
            try:
                return value.strftime("%d/%m/%Y %H:%M")
            except Exception:
                return str(value)
        return str(value)


def run_rolls_panel(service: OperationsPanelService | None = None) -> None:
    root = tk.Tk()
    RollsPanel(root, service=service)
    root.mainloop()


def main() -> None:
    run_rolls_panel()


if __name__ == "__main__":
    main()