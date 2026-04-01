# ui/operations_panel.py
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable

from application.operations_panel_service import (
    AvailableJobRow,
    AvailableJobsFilters,
    LogQueueFilters,
    LogQueueRow,
    OperationsPanelService,
    OperationsSnapshotDTO,
    RollItemRow,
    RollSummaryDTO,
)
from ui.common_widgets import apply_common_styles, clear_tree, fmt_m, fmt_num
from ui.roll_closure_dialog import RollClosureDialog
from ui.roll_export_result_dialog import RollExportResultDialog


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
    """
    Tela simplificada de Operação para testes funcionais.

    Estrutura:
    - barra superior com ações principais
    - resumo operacional curto
    - abas separadas:
        1) Jobs disponíveis
        2) Rolo ativo
        3) Fila de logs
    """

    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.service = service or OperationsPanelService()

        self.active_roll_id: int | None = None
        self.current_summary: RollSummaryDTO | None = None

        # snapshot
        self.snapshot_jobs_var = tk.StringVar(value="0")
        self.snapshot_rolls_var = tk.StringVar(value="0")
        self.snapshot_pending_logs_var = tk.StringVar(value="0")
        self.snapshot_alerts_var = tk.StringVar(value="0")

        # jobs filters
        self.machine_var = tk.StringVar(value="ALL")
        self.fabric_var = tk.StringVar(value="ALL")
        self.review_status_var = tk.StringVar(value="ALL")
        self.exclude_suspicious_var = tk.BooleanVar(value=False)
        self.search_var = tk.StringVar(value="")

        # logs filters
        self.log_status_var = tk.StringVar(value="ALL")
        self.log_parse_status_var = tk.StringVar(value="ALL")
        self.log_normalized_status_var = tk.StringVar(value="ALL")
        self.log_search_var = tk.StringVar(value="")

        # counts
        self.jobs_count_var = tk.StringVar(value="0")
        self.logs_count_var = tk.StringVar(value="0")

        # active roll vars
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
        self.logs_tree: ttk.Treeview

        self.machine_combo: ttk.Combobox
        self.fabric_combo: ttk.Combobox
        self.review_combo: ttk.Combobox
        self.log_status_combo: ttk.Combobox
        self.log_parse_combo: ttk.Combobox
        self.log_normalized_combo: ttk.Combobox

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

        self._build_action_bar()
        self._build_snapshot_bar()
        self._build_tabs()

    def _build_action_bar(self) -> None:
        bar = ttk.LabelFrame(self, text="Ações principais", padding=10)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        bar.columnconfigure(0, weight=1)

        left = ttk.Frame(bar)
        left.grid(row=0, column=0, sticky="w")

        ttk.Button(left, text="Atualizar tudo", command=self.refresh_all).pack(side="left")
        ttk.Button(left, text="Novo rolo", command=self.create_roll).pack(side="left", padx=(8, 0))
        ttk.Button(left, text="Fechar rolo", command=self.close_active_roll).pack(side="left", padx=(8, 0))
        ttk.Button(left, text="Exportar rolo", command=self.export_active_roll).pack(side="left", padx=(8, 0))

        ttk.Label(
            bar,
            text="Tela reduzida para teste funcional do fluxo.",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_snapshot_bar(self) -> None:
        box = ttk.LabelFrame(self, text="Resumo rápido", padding=10)
        box.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        for col in range(4):
            box.columnconfigure(col, weight=1)

        self._snapshot_cell(box, 0, "Jobs disponíveis", self.snapshot_jobs_var)
        self._snapshot_cell(box, 1, "Rolos abertos", self.snapshot_rolls_var)
        self._snapshot_cell(box, 2, "Logs pendentes", self.snapshot_pending_logs_var)
        self._snapshot_cell(box, 3, "Alertas", self.snapshot_alerts_var)

    def _snapshot_cell(self, master: tk.Misc, column: int, label: str, var: tk.StringVar) -> None:
        cell = ttk.Frame(master, padding=(6, 2))
        cell.grid(row=0, column=column, sticky="w")
        ttk.Label(cell, text=label).pack(anchor="w")
        ttk.Label(cell, textvariable=var, style="MetricValue.TLabel").pack(anchor="w")

    def _build_tabs(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.grid(row=2, column=0, sticky="nsew")

        jobs_tab = ttk.Frame(notebook, padding=8)
        jobs_tab.columnconfigure(0, weight=1)
        jobs_tab.rowconfigure(1, weight=1)

        roll_tab = ttk.Frame(notebook, padding=8)
        roll_tab.columnconfigure(0, weight=1)
        roll_tab.rowconfigure(1, weight=1)

        logs_tab = ttk.Frame(notebook, padding=8)
        logs_tab.columnconfigure(0, weight=1)
        logs_tab.rowconfigure(1, weight=1)

        notebook.add(jobs_tab, text="Jobs disponíveis")
        notebook.add(roll_tab, text="Rolo ativo")
        notebook.add(logs_tab, text="Fila de logs")

        self._build_jobs_tab(jobs_tab)
        self._build_roll_tab(roll_tab)
        self._build_logs_tab(logs_tab)

    def _build_jobs_tab(self, master: tk.Misc) -> None:
        filters = ttk.LabelFrame(master, text="Filtros", padding=8)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(8):
            filters.columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        ttk.Label(filters, text="Máquina").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.machine_combo = ttk.Combobox(filters, textvariable=self.machine_var, state="readonly")
        self.machine_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Tecido").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.fabric_combo = ttk.Combobox(filters, textvariable=self.fabric_var, state="readonly")
        self.fabric_combo.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Review").grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.review_combo = ttk.Combobox(filters, textvariable=self.review_status_var, state="readonly")
        self.review_combo.grid(row=0, column=5, sticky="ew", padx=(0, 10))

        ttk.Checkbutton(
            filters,
            text="Excluir suspeitos",
            variable=self.exclude_suspicious_var,
        ).grid(row=0, column=6, sticky="w")

        ttk.Label(filters, text="Busca").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(8, 0))
        ttk.Entry(filters, textvariable=self.search_var).grid(
            row=1,
            column=1,
            columnspan=5,
            sticky="ew",
            padx=(0, 10),
            pady=(8, 0),
        )

        actions = ttk.Frame(filters)
        actions.grid(row=1, column=6, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(actions, text="Aplicar", command=self.refresh_jobs).pack(side="left")
        ttk.Button(actions, text="Limpar", command=self.clear_filters).pack(side="left", padx=(8, 0))

        area = ttk.LabelFrame(master, text="Jobs disponíveis", padding=8)
        area.grid(row=1, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)

        top = ttk.Frame(area)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Itens visíveis:").grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.jobs_count_var, style="MetricValue.TLabel").grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.jobs_tree = ttk.Treeview(
            area,
            columns=(
                "row_id",
                "job_id",
                "machine",
                "fabric",
                "review",
                "document",
                "effective",
                "gap",
                "consumed",
                "sus",
            ),
            show="headings",
            selectmode="browse",
        )
        self.jobs_tree.grid(row=1, column=0, sticky="nsew")
        self.jobs_tree.bind("<Double-1>", lambda event: self.add_selected_job_to_active_roll())

        self._configure_tree_columns(
            self.jobs_tree,
            {
                "row_id": ("ID", 60, "center"),
                "job_id": ("Job", 90, "center"),
                "machine": ("Máquina", 80, "center"),
                "fabric": ("Tecido", 100, "w"),
                "review": ("Review", 120, "w"),
                "document": ("Documento", 420, "w"),
                "effective": ("Efetivo (m)", 90, "center"),
                "gap": ("Gap (m)", 80, "center"),
                "consumed": ("Consumido (m)", 100, "center"),
                "sus": ("Suspeito", 80, "center"),
            },
        )

        sb_y = ttk.Scrollbar(area, orient="vertical", command=self.jobs_tree.yview)
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(area, orient="horizontal", command=self.jobs_tree.xview)
        sb_x.grid(row=2, column=0, sticky="ew")
        self.jobs_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        footer = ttk.Frame(area)
        footer.grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Button(footer, text="Adicionar ao rolo ativo", command=self.add_selected_job_to_active_roll).pack(side="left")
        ttk.Button(footer, text="Atualizar jobs", command=self.refresh_jobs).pack(side="left", padx=(8, 0))

    def _build_roll_tab(self, master: tk.Misc) -> None:
        header = ttk.LabelFrame(master, text="Rolo ativo", padding=8)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(4):
            header.columnconfigure(col, weight=1)

        ttk.Label(header, textvariable=self.roll_title_var, style="PanelTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        self._meta_cell(header, 1, 0, "Máquina", self.roll_machine_var)
        self._meta_cell(header, 1, 1, "Tecido", self.roll_fabric_var)
        self._meta_cell(header, 1, 2, "Status", self.roll_status_var)
        self._meta_cell(header, 1, 3, "Observação", self.roll_note_var)

        self._meta_cell(header, 2, 0, "Jobs", self.roll_jobs_var)
        self._meta_cell(header, 2, 1, "Planejado", self.roll_planned_var)
        self._meta_cell(header, 2, 2, "Efetivo", self.roll_effective_var)
        self._meta_cell(header, 2, 3, "Consumido", self.roll_consumed_var)

        self._meta_cell(header, 3, 0, "Gap", self.roll_gap_var)
        self._meta_cell(header, 3, 1, "Pendentes", self.roll_pending_var)
        self._meta_cell(header, 3, 2, "Revisados OK", self.roll_ok_var)
        self._meta_cell(header, 3, 3, "Suspeitos", self.roll_suspicious_var)

        actions = ttk.Frame(header)
        actions.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Novo rolo", command=self.create_roll).pack(side="left")
        ttk.Button(actions, text="Fechar rolo", command=self.close_active_roll).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Exportar rolo", command=self.export_active_roll).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Atualizar resumo", command=self.refresh_active_roll_summary).pack(side="left", padx=(8, 0))

        area = ttk.LabelFrame(master, text="Itens do rolo", padding=8)
        area.grid(row=1, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)

        self.roll_items_tree = ttk.Treeview(
            area,
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
                "document": ("Documento", 520, "w"),
                "consumed": ("Cons. (m)", 90, "center"),
            },
        )

        sb_y = ttk.Scrollbar(area, orient="vertical", command=self.roll_items_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(area, orient="horizontal", command=self.roll_items_tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self.roll_items_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        footer = ttk.Frame(area)
        footer.grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Button(footer, text="Remover item selecionado", command=self.remove_selected_item_from_roll).pack(side="left")
        ttk.Button(footer, text="Ver detalhes", command=self.show_roll_detail_dialog).pack(side="left", padx=(8, 0))

    def _build_logs_tab(self, master: tk.Misc) -> None:
        filters = ttk.LabelFrame(master, text="Filtros", padding=8)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for col in range(8):
            filters.columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)

        ttk.Label(filters, text="Status").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.log_status_combo = ttk.Combobox(filters, textvariable=self.log_status_var, state="readonly")
        self.log_status_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Parse").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.log_parse_combo = ttk.Combobox(filters, textvariable=self.log_parse_status_var, state="readonly")
        self.log_parse_combo.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Normalização").grid(row=0, column=4, sticky="w", padx=(0, 6))
        self.log_normalized_combo = ttk.Combobox(filters, textvariable=self.log_normalized_status_var, state="readonly")
        self.log_normalized_combo.grid(row=0, column=5, sticky="ew", padx=(0, 10))

        ttk.Label(filters, text="Busca").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(8, 0))
        ttk.Entry(filters, textvariable=self.log_search_var).grid(
            row=1,
            column=1,
            columnspan=5,
            sticky="ew",
            padx=(0, 10),
            pady=(8, 0),
        )

        actions = ttk.Frame(filters)
        actions.grid(row=1, column=6, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(actions, text="Aplicar", command=self.refresh_logs).pack(side="left")
        ttk.Button(actions, text="Limpar", command=self.clear_log_filters).pack(side="left", padx=(8, 0))

        area = ttk.LabelFrame(master, text="Fila de logs", padding=8)
        area.grid(row=1, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(1, weight=1)

        top = ttk.Frame(area)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Logs visíveis:").grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.logs_count_var, style="MetricValue.TLabel").grid(row=0, column=1, sticky="w", padx=(6, 0))

        self.logs_tree = ttk.Treeview(
            area,
            columns=(
                "log_id",
                "source_name",
                "machine_raw",
                "parse_status",
                "normalized_status",
                "status",
                "captured_at",
                "job_id",
                "error",
            ),
            show="headings",
            selectmode="browse",
        )
        self.logs_tree.grid(row=1, column=0, sticky="nsew")
        self.logs_tree.bind("<Double-1>", lambda event: self.show_selected_log_detail_dialog())

        self._configure_tree_columns(
            self.logs_tree,
            {
                "log_id": ("ID", 60, "center"),
                "source_name": ("Arquivo", 190, "w"),
                "machine_raw": ("Máquina raw", 100, "w"),
                "parse_status": ("Parse", 90, "center"),
                "normalized_status": ("Normalização", 110, "center"),
                "status": ("Legado", 90, "center"),
                "captured_at": ("Capturado", 140, "center"),
                "job_id": ("Job row", 80, "center"),
                "error": ("Erro", 260, "w"),
            },
        )

        sb_y = ttk.Scrollbar(area, orient="vertical", command=self.logs_tree.yview)
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(area, orient="horizontal", command=self.logs_tree.xview)
        sb_x.grid(row=2, column=0, sticky="ew")
        self.logs_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        footer = ttk.Frame(area)
        footer.grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Button(footer, text="Ver detalhe do log", command=self.show_selected_log_detail_dialog).pack(side="left")
        ttk.Button(footer, text="Atualizar logs", command=self.refresh_logs).pack(side="left", padx=(8, 0))

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
    # Refresh
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        self._load_filter_values()
        self._load_log_filter_values()
        self.refresh_snapshot()
        self.refresh_jobs()
        self.refresh_logs()
        self.refresh_active_roll_summary()

    def refresh_snapshot(self) -> None:
        snapshot = self.service.get_operations_snapshot()
        self._apply_snapshot(snapshot)

    def refresh_jobs(self) -> None:
        filters = AvailableJobsFilters(
            machine=self._none_if_all(self.machine_var.get()),
            fabric=self._none_if_all(self.fabric_var.get()),
            review_status=self._none_if_all(self.review_status_var.get()),
            exclude_suspicious=self.exclude_suspicious_var.get(),
            limit=None,
        )

        jobs = self.service.list_available_jobs(filters)
        jobs = self._apply_job_search(jobs, self.search_var.get())
        self._populate_jobs_tree(jobs)
        self.jobs_count_var.set(str(len(jobs)))

    def refresh_logs(self) -> None:
        filters = LogQueueFilters(
            status=self._none_if_all(self.log_status_var.get()),
            parse_status=self._none_if_all(self.log_parse_status_var.get()),
            normalized_status=self._none_if_all(self.log_normalized_status_var.get()),
            search=(self.log_search_var.get() or "").strip() or None,
            limit=None,
        )

        logs = self.service.list_log_queue(filters)
        self._populate_logs_tree(logs)
        self.logs_count_var.set(str(len(logs)))

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

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def clear_filters(self) -> None:
        self.machine_var.set("ALL")
        self.fabric_var.set("ALL")
        self.review_status_var.set("ALL")
        self.exclude_suspicious_var.set(False)
        self.search_var.set("")
        self.refresh_jobs()

    def clear_log_filters(self) -> None:
        self.log_status_var.set("ALL")
        self.log_parse_status_var.set("ALL")
        self.log_normalized_status_var.set("ALL")
        self.log_search_var.set("")
        self.refresh_logs()

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
            self.review_status_var.set("ALL")

    def _load_log_filter_values(self) -> None:
        values = self.service.get_log_filter_values()

        status_values = ["ALL", *values.get("statuses", [])]
        parse_values = ["ALL", *values.get("parse_statuses", [])]
        normalized_values = ["ALL", *values.get("normalized_statuses", [])]

        self.log_status_combo["values"] = status_values
        self.log_parse_combo["values"] = parse_values
        self.log_normalized_combo["values"] = normalized_values

        if self.log_status_var.get() not in status_values:
            self.log_status_var.set("ALL")
        if self.log_parse_status_var.get() not in parse_values:
            self.log_parse_status_var.set("ALL")
        if self.log_normalized_status_var.get() not in normalized_values:
            self.log_normalized_status_var.set("ALL")

    # ------------------------------------------------------------------
    # Roll actions
    # ------------------------------------------------------------------

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

        summary = self.service.add_job_to_roll(
            roll_id=self.active_roll_id,
            job_row_id=job_row_id,
        )
        self.current_summary = summary
        self._apply_summary(summary)
        self.refresh_jobs()
        self.refresh_snapshot()

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

        summary = self.service.remove_job_from_roll(
            roll_id=self.active_roll_id,
            job_row_id=job_row_id,
        )
        self.current_summary = summary
        self._apply_summary(summary)
        self.refresh_jobs()
        self.refresh_snapshot()

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

        self.current_summary = dialog.result_summary

        if dialog.export_result is not None:
            result_dialog = RollExportResultDialog(self.winfo_toplevel(), result=dialog.export_result)
            self.wait_window(result_dialog)
        else:
            messagebox.showinfo(
                "Fechamento concluído",
                f"Rolo fechado com sucesso:\n{self.current_summary.roll_name}",
                parent=self,
            )

        self.refresh_jobs()
        self.refresh_logs()
        self.refresh_snapshot()
        self.refresh_active_roll_summary()

    def export_active_roll(self) -> None:
        if self.active_roll_id is None:
            messagebox.showwarning("Exportar rolo", "Nenhum rolo ativo selecionado.", parent=self)
            return

        directory = filedialog.askdirectory(title="Selecione a pasta de exportação", parent=self)
        if not directory:
            return

        result = self.service.export_roll(
            roll_id=self.active_roll_id,
            output_dir=Path(directory),
        )
        result_dialog = RollExportResultDialog(self.winfo_toplevel(), result=result)
        self.wait_window(result_dialog)
        self.refresh_active_roll_summary()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

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
            f"Observação: {s.note or '-'}\n"
            f"Jobs: {s.jobs_count}\n"
            f"Planejado: {fmt_m(s.total_planned_m)}\n"
            f"Efetivo: {fmt_m(s.total_effective_m)}\n"
            f"Gap: {fmt_m(s.total_gap_m)}\n"
            f"Consumido: {fmt_m(s.total_consumed_m)}\n"
            f"Pendentes: {s.pending_review_count}\n"
            f"Revisados OK: {s.reviewed_ok_count}\n"
            f"Suspeitos: {s.suspicious_count}"
        )
        messagebox.showinfo("Detalhes do rolo", text, parent=self)

    def show_selected_log_detail_dialog(self) -> None:
        selection = self.logs_tree.selection()
        if not selection:
            messagebox.showinfo("Fila de logs", "Selecione um log para visualizar.", parent=self)
            return

        values = self.logs_tree.item(selection[0], "values")
        if not values:
            return

        text = (
            f"Log ID: {values[0]}\n"
            f"Arquivo: {values[1]}\n"
            f"Máquina raw: {values[2]}\n"
            f"Parse: {values[3]}\n"
            f"Normalização: {values[4]}\n"
            f"Legado: {values[5]}\n"
            f"Capturado: {values[6]}\n"
            f"Job row: {values[7]}\n"
            f"Erro: {values[8]}"
        )
        messagebox.showinfo("Detalhe do log", text, parent=self)

    # ------------------------------------------------------------------
    # Apply state
    # ------------------------------------------------------------------

    def _apply_snapshot(self, snapshot: OperationsSnapshotDTO) -> None:
        alerts = snapshot.suspicious_jobs_count + snapshot.invalid_logs_count + snapshot.pending_logs_count
        self.snapshot_jobs_var.set(str(snapshot.available_jobs_count))
        self.snapshot_rolls_var.set(str(snapshot.open_rolls_count))
        self.snapshot_pending_logs_var.set(str(snapshot.pending_logs_count))
        self.snapshot_alerts_var.set(str(alerts))

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
        clear_tree(self.roll_items_tree)

    # ------------------------------------------------------------------
    # Tree population
    # ------------------------------------------------------------------

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

    def _populate_logs_tree(self, logs: Iterable[LogQueueRow]) -> None:
        clear_tree(self.logs_tree)
        for row in logs:
            self.logs_tree.insert(
                "",
                "end",
                values=(
                    row.log_id,
                    row.source_name or "-",
                    row.machine_code_raw or "-",
                    row.parse_status,
                    row.normalized_status,
                    row.status,
                    _fmt_dt(row.captured_at),
                    row.job_id or "-",
                    row.parse_error or "-",
                ),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_job_search(self, jobs: list[AvailableJobRow], text: str) -> list[AvailableJobRow]:
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


def _fmt_dt(value: object) -> str:
    if isinstance(value, str):
        return value
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value)
    return str(value or "-")