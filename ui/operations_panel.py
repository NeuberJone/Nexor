from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable

from application.operations_panel_service import (
    AvailableJobRow,
    AvailableJobsFilters,
    OperationsPanelService,
    RollItemRow,
    RollSummaryDTO,
)
from ui.common_widgets import (
    apply_common_styles,
    clear_tree,
    configure_tree_columns,
    fmt_m,
    fmt_num,
)
from ui.roll_closure_dialog import RollClosureDialog
from ui.roll_export_result_dialog import RollExportResultDialog
from ui.roll_items_panel import RollItemsPanel
from ui.roll_summary_panel import RollSummaryPanel
from ui.workspace_layout import TwoRowWorkspace


SUMMARY_PANEL_WIDTH = 300


class CreateRollDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Novo rolo")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result: dict[str, str | None] | None = None

        self.machine_var = tk.StringVar(value="M1")
        self.fabric_var = tk.StringVar()
        self.roll_name_var = tk.StringVar()
        self.note_var = tk.StringVar()

        self.columnconfigure(0, weight=1)
        self._build_ui()
        self._center(master)

        self.bind("<Return>", self._on_confirm)
        self.bind("<Escape>", lambda event: self.destroy())

    def _build_ui(self) -> None:
        body = ttk.Frame(self, padding=16)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="Máquina").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Combobox(
            body,
            textvariable=self.machine_var,
            values=["M1", "M2", "CALANDRA"],
            state="readonly",
            width=20,
        ).grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(body, text="Tecido").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(body, textvariable=self.fabric_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(body, text="Nome do rolo").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(body, textvariable=self.roll_name_var).grid(row=2, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(body, text="Observação").grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(body, textvariable=self.note_var).grid(row=3, column=1, sticky="ew")

        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(actions, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Criar rolo", command=self._confirm).pack(side="right", padx=(0, 8))

    def _center(self, master: tk.Misc) -> None:
        self.update_idletasks()
        if isinstance(master, (tk.Tk, tk.Toplevel)):
            x = master.winfo_rootx()
            y = master.winfo_rooty()
            w = master.winfo_width() or 1200
            h = master.winfo_height() or 800
        else:
            x, y, w, h = 100, 100, 1200, 800

        req_w = self.winfo_reqwidth()
        req_h = self.winfo_reqheight()
        pos_x = x + max((w - req_w) // 2, 0)
        pos_y = y + max((h - req_h) // 2, 0)
        self.geometry(f"+{pos_x}+{pos_y}")

    def _on_confirm(self, event: tk.Event | None = None) -> None:
        self._confirm()

    def _confirm(self) -> None:
        machine = (self.machine_var.get() or "").strip().upper()
        if not machine:
            messagebox.showerror("Novo rolo", "Informe a máquina.", parent=self)
            return

        self.result = {
            "machine": machine,
            "fabric": (self.fabric_var.get() or "").strip() or None,
            "roll_name": (self.roll_name_var.get() or "").strip() or None,
            "note": (self.note_var.get() or "").strip() or None,
        }
        self.destroy()


class OperationsPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.master = master
        self.service = service or OperationsPanelService()

        self.active_roll_id: int | None = None
        self.current_summary: RollSummaryDTO | None = None

        self.machine_var = tk.StringVar(value="ALL")
        self.fabric_var = tk.StringVar(value="ALL")
        self.review_status_var = tk.StringVar(value="REVIEWED_OK")
        self.exclude_suspicious_var = tk.BooleanVar(value=False)
        self.search_var = tk.StringVar(value="")

        self.jobs_count_var = tk.StringVar(value="0")
        self.roll_title_var = tk.StringVar(value="Nenhum rolo ativo")
        self.roll_machine_var = tk.StringVar(value="-")
        self.roll_fabric_var = tk.StringVar(value="-")
        self.roll_status_var = tk.StringVar(value="-")
        self.roll_note_var = tk.StringVar(value="-")

        self.roll_jobs_var = tk.StringVar(value="0")
        self.roll_planned_var = tk.StringVar(value="0.00 m")
        self.roll_effective_var = tk.StringVar(value="0.00 m")
        self.roll_gap_var = tk.StringVar(value="0.00 m")
        self.roll_consumed_var = tk.StringVar(value="0.00 m")
        self.roll_pending_var = tk.StringVar(value="0")
        self.roll_ok_var = tk.StringVar(value="0")
        self.roll_suspicious_var = tk.StringVar(value="0")

        self.jobs_tree: ttk.Treeview
        self.roll_items_tree: ttk.Treeview
        self.machine_combo: ttk.Combobox
        self.fabric_combo: ttk.Combobox
        self.review_combo: ttk.Combobox

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
        bar = ttk.LabelFrame(self, text="Filtros", style="Section.TLabelframe", padding=10)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(9):
            bar.columnconfigure(col, weight=1 if col in {1, 3, 5, 7} else 0)

        ttk.Label(bar, text="Máquina").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.machine_combo = ttk.Combobox(bar, textvariable=self.machine_var, state="readonly")
        self.machine_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(bar, text="Tecido").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.fabric_combo = ttk.Combobox(bar, textvariable=self.fabric_var, state="readonly")
        self.fabric_combo.grid(row=0, column=3, sticky="ew", padx=(0, 12))

        ttk.Label(bar, text="Review").grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.review_combo = ttk.Combobox(bar, textvariable=self.review_status_var, state="readonly")
        self.review_combo.grid(row=0, column=5, sticky="ew", padx=(0, 12))

        ttk.Label(bar, text="Busca").grid(row=0, column=6, sticky="w", padx=(0, 6))
        ttk.Entry(bar, textvariable=self.search_var).grid(row=0, column=7, sticky="ew", padx=(0, 12))

        ttk.Checkbutton(
            bar,
            text="Excluir suspeitos",
            variable=self.exclude_suspicious_var,
        ).grid(row=0, column=8, sticky="w")

        actions = ttk.Frame(bar)
        actions.grid(row=1, column=0, columnspan=9, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Limpar filtros", command=self.clear_filters).pack(side="right")
        ttk.Button(actions, text="Atualizar", command=self.refresh_all).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="Aplicar filtros", command=self.refresh_jobs).pack(side="right", padx=(0, 8))

    def _build_body(self) -> None:
        self.workspace = TwoRowWorkspace(
            self,
            right_width=SUMMARY_PANEL_WIDTH,
            top_weight=3,
            bottom_weight=2,
        )
        self.workspace.grid(row=1, column=0, sticky="nsew")

        self._build_jobs_panel(self.workspace.left_top)
        self._build_roll_panel(self.workspace.left_bottom)
        self._build_summary_panel(self.workspace.right_panel)

    def _build_jobs_panel(self, master: tk.Misc) -> None:
        panel = ttk.LabelFrame(master, text="Jobs disponíveis", style="Section.TLabelframe", padding=8)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        top = ttk.Frame(panel)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(top, text="Itens visíveis:").pack(side="left")
        ttk.Label(top, textvariable=self.jobs_count_var, style="MetricValue.TLabel").pack(side="left", padx=(6, 0))

        tree_wrap = ttk.Frame(panel)
        tree_wrap.grid(row=1, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        self.jobs_tree = ttk.Treeview(
            tree_wrap,
            columns=("row_id", "job_id", "machine", "fabric", "review", "document", "effective", "gap", "consumed", "sus"),
            show="headings",
            selectmode="browse",
        )
        self.jobs_tree.grid(row=0, column=0, sticky="nsew")
        self.jobs_tree.bind("<Double-1>", lambda event: self.add_selected_job_to_active_roll())

        sb_y = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.jobs_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.jobs_tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self.jobs_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        configure_tree_columns(
            self.jobs_tree,
            {
                "row_id": ("ID", 70),
                "job_id": ("Job", 90),
                "machine": ("Máquina", 90),
                "fabric": ("Tecido", 120),
                "review": ("Review", 120),
                "document": ("Documento", 380),
                "effective": ("Efetivo (m)", 100),
                "gap": ("Gap (m)", 90),
                "consumed": ("Consumido (m)", 115),
                "sus": ("Suspeito", 90),
            },
            left_aligned={"fabric", "review", "document"},
        )

        actions = ttk.Frame(panel)
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(actions, text="Adicionar ao rolo ativo", command=self.add_selected_job_to_active_roll).pack(side="left")
        ttk.Button(actions, text="Atualizar jobs", command=self.refresh_jobs).pack(side="left", padx=(8, 0))

    def _build_roll_panel(self, master: tk.Misc) -> None:
        self.roll_panel = RollItemsPanel(
            master,
            panel_title="Rolo em montagem",
            title_var=self.roll_title_var,
            meta_fields=[
                ("Máquina", self.roll_machine_var),
                ("Tecido", self.roll_fabric_var),
                ("Status", self.roll_status_var),
                ("Observação", self.roll_note_var),
            ],
            header_actions=[
                ("Novo rolo", self.create_roll),
                ("Fechar", self.close_active_roll),
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
                ("Remover item", self.remove_selected_item_from_roll),
                ("Exportar rolo", self.export_active_roll),
                ("Atualizar resumo", self.refresh_active_roll_summary),
                ("Ver detalhes", self.show_roll_detail_dialog),
            ],
        )
        self.summary_panel.grid(row=0, column=0, sticky="nsew")

    def clear_filters(self) -> None:
        self.machine_var.set("ALL")
        self.fabric_var.set("ALL")
        self.review_status_var.set("REVIEWED_OK")
        self.exclude_suspicious_var.set(False)
        self.search_var.set("")
        self.refresh_jobs()

    def refresh_all(self) -> None:
        self._load_filter_values()
        self.refresh_jobs()
        self.refresh_active_roll_summary()

    def _load_filter_values(self) -> None:
        values = self.service.get_filter_values()

        machine_values = ["ALL", *values.get("machines", [])]
        fabric_values = ["ALL", *values.get("fabrics", [])]
        review_values = ["ALL", *values.get("review_statuses", [])]

        self.machine_combo["values"] = machine_values
        self.fabric_combo["values"] = fabric_values
        self.review_combo["values"] = review_values

        if self.machine_var.get() not in machine_values:
            self.machine_var.set("ALL")
        if self.fabric_var.get() not in fabric_values:
            self.fabric_var.set("ALL")
        if self.review_status_var.get() not in review_values:
            self.review_status_var.set("REVIEWED_OK" if "REVIEWED_OK" in review_values else "ALL")

    def refresh_jobs(self) -> None:
        filters = AvailableJobsFilters(
            machine=self._none_if_all(self.machine_var.get()),
            fabric=self._none_if_all(self.fabric_var.get()),
            review_status=self._none_if_all(self.review_status_var.get()),
            exclude_suspicious=self.exclude_suspicious_var.get(),
            limit=None,
        )

        jobs = self.service.list_available_jobs(filters)
        jobs = self._apply_text_search(jobs, self.search_var.get())
        self._populate_jobs_tree(jobs)
        self.jobs_count_var.set(str(len(jobs)))

    def refresh_active_roll_summary(self) -> None:
        open_rolls = self.service.list_open_rolls()

        if not open_rolls:
            self.active_roll_id = None
            self.current_summary = None
            self._clear_roll_panel()
            return

        available_ids = {r.roll_id for r in open_rolls}
        if self.active_roll_id not in available_ids:
            self.active_roll_id = open_rolls[0].roll_id

        summary = self.service.get_roll_summary(self.active_roll_id)
        self.current_summary = summary
        self._apply_summary(summary)

    def create_roll(self) -> None:
        dialog = CreateRollDialog(self.winfo_toplevel())
        self.wait_window(dialog)
        if not dialog.result:
            return

        summary = self.service.create_roll(
            machine=str(dialog.result["machine"]),
            fabric=dialog.result["fabric"],
            note=dialog.result["note"],
            roll_name=dialog.result["roll_name"],
        )

        self.active_roll_id = summary.roll_id
        self.current_summary = summary
        self._apply_summary(summary)

    def add_selected_job_to_active_roll(self) -> None:
        if self.active_roll_id is None:
            messagebox.showwarning("Operação", "Crie ou selecione um rolo ativo primeiro.", parent=self)
            return

        job_row_id = self._get_selected_tree_row_id(self.jobs_tree)
        if job_row_id is None:
            messagebox.showwarning("Operação", "Selecione um job para adicionar.", parent=self)
            return

        summary = self.service.add_job_to_roll(roll_id=self.active_roll_id, job_row_id=job_row_id)
        self.current_summary = summary
        self._apply_summary(summary)
        self.refresh_jobs()

        if summary.pending_review_count > 0:
            messagebox.showwarning(
                "Atenção",
                "O rolo ativo contém jobs com PENDING_REVIEW.\n\nNo MVP eles continuam permitidos, mas devem ficar visíveis.",
                parent=self,
            )

    def remove_selected_item_from_roll(self) -> None:
        if self.active_roll_id is None:
            messagebox.showwarning("Operação", "Nenhum rolo ativo selecionado.", parent=self)
            return

        job_row_id = self._get_selected_tree_row_id(self.roll_items_tree)
        if job_row_id is None:
            messagebox.showwarning("Operação", "Selecione um item do rolo para remover.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Remover item",
            f"Deseja remover o item {job_row_id} do rolo ativo?",
            parent=self,
        )
        if not confirm:
            return

        summary = self.service.remove_job_from_roll(roll_id=self.active_roll_id, job_row_id=job_row_id)
        self.current_summary = summary
        self._apply_summary(summary)
        self.refresh_jobs()

    def close_active_roll(self) -> None:
        if self.current_summary is None or self.active_roll_id is None:
            messagebox.showwarning("Fechar rolo", "Nenhum rolo ativo selecionado.", parent=self)
            return

        dialog = RollClosureDialog(
            self.winfo_toplevel(),
            service=self.service,
            summary=self.current_summary,
        )
        self.wait_window(dialog)

        if dialog.result_summary is None:
            return

        closed_summary = dialog.result_summary
        self.current_summary = closed_summary

        if dialog.export_result is not None:
            result_dialog = RollExportResultDialog(self.winfo_toplevel(), result=dialog.export_result)
            self.wait_window(result_dialog)
        else:
            messagebox.showinfo(
                "Fechamento concluído",
                f"Rolo fechado com sucesso:\n{closed_summary.roll_name}",
                parent=self,
            )

        self.refresh_jobs()
        self.refresh_active_roll_summary()

    def export_active_roll(self) -> None:
        if self.active_roll_id is None:
            messagebox.showwarning("Exportar rolo", "Nenhum rolo ativo selecionado.", parent=self)
            return

        directory = filedialog.askdirectory(title="Selecione a pasta de exportação", parent=self)
        if not directory:
            return

        result = self.service.export_roll(roll_id=self.active_roll_id, output_dir=Path(directory))
        result_dialog = RollExportResultDialog(self.winfo_toplevel(), result=result)
        self.wait_window(result_dialog)
        self.refresh_active_roll_summary()

    def show_roll_detail_dialog(self) -> None:
        if self.current_summary is None:
            messagebox.showinfo("Detalhes", "Nenhum rolo ativo carregado.", parent=self)
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

    def _apply_summary(self, summary: RollSummaryDTO) -> None:
        self.roll_title_var.set(f"{summary.roll_name} (ID {summary.roll_id})")
        self.roll_machine_var.set(summary.machine)
        self.roll_fabric_var.set(summary.fabric or "-")
        self.roll_status_var.set(summary.status)
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

    def _clear_roll_panel(self) -> None:
        self.roll_title_var.set("Nenhum rolo ativo")
        self.roll_machine_var.set("-")
        self.roll_fabric_var.set("-")
        self.roll_status_var.set("-")
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

    def _populate_jobs_tree(self, jobs: Iterable[AvailableJobRow]) -> None:
        clear_tree(self.jobs_tree)
        for row in jobs:
            self.jobs_tree.insert(
                "",
                "end",
                values=(
                    row.row_id,
                    row.job_id,
                    row.machine,
                    row.fabric or "-",
                    row.review_status or "-",
                    row.document,
                    fmt_num(row.effective_printed_length_m),
                    fmt_num(row.gap_before_m),
                    fmt_num(row.consumed_length_m),
                    "SIM" if row.is_suspicious else "-",
                ),
            )

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

    def _apply_text_search(self, jobs: list[AvailableJobRow], text: str) -> list[AvailableJobRow]:
        term = (text or "").strip().lower()
        if not term:
            return jobs

        out: list[AvailableJobRow] = []
        for row in jobs:
            hay = " ".join(
                [
                    str(row.job_id),
                    str(row.machine),
                    str(row.fabric or ""),
                    str(row.review_status or ""),
                    str(row.document or ""),
                    str(row.suspicion_reason or ""),
                ]
            ).lower()
            if term in hay:
                out.append(row)
        return out

    def _get_selected_tree_row_id(self, tree: ttk.Treeview) -> int | None:
        selection = tree.selection()
        if not selection:
            return None
        values = tree.item(selection[0], "values")
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


def run_operations_panel(service: OperationsPanelService | None = None) -> None:
    root = tk.Tk()
    OperationsPanel(root, service=service)
    root.mainloop()


def main() -> None:
    run_operations_panel()


if __name__ == "__main__":
    main()