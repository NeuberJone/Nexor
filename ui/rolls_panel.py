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
from ui.common_widgets import (
    apply_common_styles,
    clear_tree,
    configure_tree_columns,
    fmt_m,
    fmt_num,
)
from ui.roll_export_result_dialog import RollExportResultDialog
from ui.roll_items_panel import RollItemsPanel
from ui.roll_summary_panel import RollSummaryPanel
from ui.workspace_layout import TwoRowWorkspace


SUMMARY_PANEL_WIDTH = 300


class RollsPanel(ttk.Frame):
    """
    Painel de rolos em modo content-only, no mesmo layout-base da Operação.
    """

    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.master = master
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

        self.rolls_tree: ttk.Treeview
        self.roll_items_tree: ttk.Treeview
        self.status_combo: ttk.Combobox
        self.machine_combo: ttk.Combobox

        apply_common_styles()
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_filters()
        self._build_body()

    def _build_filters(self) -> None:
        filters = ttk.LabelFrame(self, text="Filtros", style="Section.TLabelframe", padding=10)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(6):
            filters.columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        ttk.Label(filters, text="Status").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.status_combo = ttk.Combobox(filters, textvariable=self.status_var, state="readonly")
        self.status_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(filters, text="Máquina").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.machine_combo = ttk.Combobox(filters, textvariable=self.machine_var, state="readonly")
        self.machine_combo.grid(row=0, column=3, sticky="ew", padx=(0, 12))

        ttk.Label(filters, text="Busca").grid(row=0, column=4, sticky="w", padx=(0, 6))
        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=5, sticky="ew")

        actions = ttk.Frame(filters)
        actions.grid(row=1, column=0, columnspan=6, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Limpar filtros", command=self.clear_filters).pack(side="right")
        ttk.Button(actions, text="Atualizar", command=self.refresh_all).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="Aplicar filtros", command=self.refresh_rolls).pack(side="right", padx=(0, 8))

    def _build_body(self) -> None:
        self.workspace = TwoRowWorkspace(
            self,
            right_width=SUMMARY_PANEL_WIDTH,
            top_weight=3,
            bottom_weight=2,
        )
        self.workspace.grid(row=1, column=0, sticky="nsew")

        self._build_rolls_list_panel(self.workspace.left_top)
        self._build_selected_roll_panel(self.workspace.left_bottom)
        self._build_summary_panel(self.workspace.right_panel)

    def _build_rolls_list_panel(self, master: tk.Misc) -> None:
        panel = ttk.LabelFrame(master, text="Lista de rolos", style="Section.TLabelframe", padding=8)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        top = ttk.Frame(panel)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(top, text="Total visível:").pack(side="left")
        ttk.Label(top, textvariable=self.rolls_count_var, style="MetricValue.TLabel").pack(side="left", padx=(6, 0))

        tree_wrap = ttk.Frame(panel)
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

        configure_tree_columns(
            self.rolls_tree,
            {
                "roll_id": ("ID", 70),
                "roll_name": ("Rolo", 220),
                "machine": ("Máquina", 90),
                "fabric": ("Tecido", 120),
                "jobs": ("Jobs", 70),
                "consumed": ("Consumido (m)", 120),
                "status": ("Status", 100),
            },
            left_aligned={"roll_name", "fabric"},
        )

    def _build_selected_roll_panel(self, master: tk.Misc) -> None:
        self.roll_panel = RollItemsPanel(
            master,
            panel_title="Rolo selecionado",
            title_var=self.roll_title_var,
            meta_fields=[
                ("Status", self.roll_status_var),
                ("Máquina", self.roll_machine_var),
                ("Tecido", self.roll_fabric_var),
                ("Observação", self.roll_note_var),
            ],
            tree_columns={
                "row_id": ("ID", 60),
                "job_id": ("Job", 90),
                "machine": ("Máquina", 80),
                "fabric": ("Tecido", 110),
                "review": ("Review", 110),
                "document": ("Documento", 260),
                "consumed": ("Cons. (m)", 90),
            },
            left_aligned_columns={"fabric", "review", "document"},
        )
        self.roll_panel.grid(row=0, column=0, sticky="nsew")
        self.roll_items_tree = self.roll_panel.items_tree

    def _build_summary_panel(self, master: tk.Misc) -> None:
        self.summary_panel = RollSummaryPanel(
            master,
            width=SUMMARY_PANEL_WIDTH,
            metrics=[
                ("Jobs", self.roll_jobs_var),
                ("Planejado", self.roll_planned_var),
                ("Efetivo", self.roll_effective_var),
                ("Gap", self.roll_gap_var),
                ("Consumido", self.roll_consumed_var),
                ("Pendentes", self.roll_pending_var),
                ("Revisados OK", self.roll_ok_var),
                ("Suspeitos", self.roll_suspicious_var),
            ],
            actions=[
                ("Ver detalhe textual", self.show_detail_dialog),
                ("Exportar novamente", self.export_selected_roll),
                ("Atualizar seleção", self.load_selected_roll_detail),
            ],
        )
        self.summary_panel.grid(row=0, column=0, sticky="nsew")

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
            self._clear_roll_panel()
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
            f"Planejado: {fmt_m(s.total_planned_m)}\n"
            f"Efetivo: {fmt_m(s.total_effective_m)}\n"
            f"Gap: {fmt_m(s.total_gap_m)}\n"
            f"Consumido: {fmt_m(s.total_consumed_m)}\n"
            f"Pendentes: {s.pending_review_count}\n"
            f"Revisados OK: {s.reviewed_ok_count}\n"
            f"Suspeitos: {s.suspicious_count}\n"
            f"Observação: {s.note or '-'}"
        )
        messagebox.showinfo("Detalhes do rolo", text, parent=self)

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
        rows = []
        for item in items:
            rows.append(
                (
                    item.row_id or "-",
                    item.job_id,
                    item.machine,
                    item.fabric or "-",
                    item.review_status or "-",
                    item.document,
                    fmt_num(item.consumed_length_m),
                )
            )
        self.roll_panel.set_items(rows)

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
        self._populate_roll_items_tree([])

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
    def _none_if_all(value: str | None) -> str | None:
        text = (value or "").strip()
        if not text or text.upper() == "ALL":
            return None
        return text


def run_rolls_panel(service: OperationsPanelService | None = None) -> None:
    root = tk.Tk()
    RollsPanel(root, service=service)
    root.mainloop()


def main() -> None:
    run_rolls_panel()


if __name__ == "__main__":
    main()