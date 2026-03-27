# ui/log_sources_panel.py
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from application.log_sources_service import (
    LogSourceFormData,
    LogSourceRow,
    LogSourcesService,
)
from ui.common_widgets import (
    apply_common_styles,
    clear_tree,
    meta_cell,
    metric_cell,
)
from ui.table_list_panel import TableListPanel
from ui.workspace_layout import TwoRowWorkspace


SUMMARY_PANEL_WIDTH = 300


class CreateLogSourceDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Nova fonte de logs")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result: LogSourceFormData | None = None

        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.machine_hint_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.enabled_var = tk.BooleanVar(value=True)

        self.columnconfigure(0, weight=1)
        self._build_ui()
        self._center(master)

        self.bind("<Return>", self._on_confirm)
        self.bind("<Escape>", lambda event: self.destroy())

    def _build_ui(self) -> None:
        body = ttk.Frame(self, padding=16)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="Nome").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(body, textvariable=self.name_var, width=44).grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(body, text="Pasta").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        path_wrap = ttk.Frame(body)
        path_wrap.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        path_wrap.columnconfigure(0, weight=1)

        ttk.Entry(path_wrap, textvariable=self.path_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(path_wrap, text="Buscar", command=self._pick_folder).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(body, text="Machine hint").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(body, textvariable=self.machine_hint_var).grid(row=2, column=1, sticky="ew", pady=(0, 8))

        flags = ttk.Frame(body)
        flags.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Checkbutton(flags, text="Buscar recursivamente", variable=self.recursive_var).pack(side="left")
        ttk.Checkbutton(flags, text="Criar já habilitada", variable=self.enabled_var).pack(side="left", padx=(12, 0))

        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(actions, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Salvar fonte", command=self._confirm).pack(side="right", padx=(0, 8))

    def _pick_folder(self) -> None:
        directory = filedialog.askdirectory(title="Selecione a pasta de logs", parent=self)
        if directory:
            self.path_var.set(directory)

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
        self.result = LogSourceFormData(
            name=(self.name_var.get() or "").strip(),
            path=(self.path_var.get() or "").strip(),
            machine_hint=(self.machine_hint_var.get() or "").strip() or None,
            recursive=self.recursive_var.get(),
            enabled=self.enabled_var.get(),
        )
        self.destroy()


class LogSourcesPanel(ttk.Frame):
    """
    Painel content-only para gestão das fontes de logs.

    Regras:
    - a UI só conversa com LogSourcesService
    - nada de SQL direto ou regra operacional na tela
    - pensado para operador conferir e ajustar as fontes do import local
    """

    def __init__(self, master: tk.Misc, service: LogSourcesService | None = None) -> None:
        super().__init__(master)
        self.service = service or LogSourcesService()

        self.search_var = tk.StringVar(value="")
        self.include_disabled_var = tk.BooleanVar(value=True)

        self.sources_count_var = tk.StringVar(value="0")
        self.total_var = tk.StringVar(value="0")
        self.enabled_var = tk.StringVar(value="0")
        self.disabled_var = tk.StringVar(value="0")
        self.checkpoints_var = tk.StringVar(value="0")
        self.runs_var = tk.StringVar(value="0")
        self.errors_var = tk.StringVar(value="0")

        self.detail_title_var = tk.StringVar(value="Nenhuma fonte selecionada")
        self.detail_name_var = tk.StringVar(value="-")
        self.detail_path_var = tk.StringVar(value="-")
        self.detail_machine_hint_var = tk.StringVar(value="-")
        self.detail_enabled_var = tk.StringVar(value="-")
        self.detail_recursive_var = tk.StringVar(value="-")
        self.detail_last_scan_var = tk.StringVar(value="-")
        self.detail_checkpoint_var = tk.StringVar(value="-")
        self.detail_created_var = tk.StringVar(value="-")
        self.detail_updated_var = tk.StringVar(value="-")
        self.detail_last_run_start_var = tk.StringVar(value="-")
        self.detail_last_run_finish_var = tk.StringVar(value="-")
        self.detail_last_run_counts_var = tk.StringVar(value="-")
        self.detail_last_run_notes_var = tk.StringVar(value="-")

        self.current_source_id: int | None = None

        self.sources_tree: ttk.Treeview

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
        filters.columnconfigure(1, weight=1)

        ttk.Label(filters, text="Busca").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ttk.Checkbutton(
            filters,
            text="Incluir desabilitadas",
            variable=self.include_disabled_var,
        ).grid(row=0, column=2, sticky="w")

        actions = ttk.Frame(filters)
        actions.grid(row=1, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Limpar filtros", command=self.clear_filters).pack(side="right")
        ttk.Button(actions, text="Atualizar", command=self.refresh_all).pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="Aplicar filtros", command=self.refresh_table).pack(side="right", padx=(0, 8))

    def _build_body(self) -> None:
        workspace = TwoRowWorkspace(
            self,
            right_width=SUMMARY_PANEL_WIDTH,
            top_weight=3,
            bottom_weight=2,
        )
        workspace.grid(row=1, column=0, sticky="nsew")

        self._build_sources_list_panel(workspace.left_top)
        self._build_detail_panel(workspace.left_bottom)
        self._build_summary_panel(workspace.right_panel)

    def _build_sources_list_panel(self, master: tk.Misc) -> None:
        panel = TableListPanel(
            master,
            panel_title="Fontes de logs",
            count_label="Total visível:",
            count_var=self.sources_count_var,
            tree_columns={
                "source_id": ("ID", 60),
                "name": ("Nome", 180),
                "machine_hint": ("Machine", 90),
                "enabled": ("Ativa", 70),
                "recursive": ("Rec.", 60),
                "path": ("Caminho", 420),
                "checkpoint": ("Checkpoint", 120),
                "last_run": ("Última execução", 140),
            },
            left_aligned_columns={"name", "path"},
            footer_actions=[
                ("Nova fonte", self.create_source),
                ("Habilitar / Desabilitar", self.toggle_selected_source),
                ("Resetar checkpoint", self.reset_selected_checkpoint),
                ("Remover", self.delete_selected_source),
                ("Atualizar", self.refresh_all),
            ],
        )
        panel.grid(row=0, column=0, sticky="nsew")

        self.sources_tree = panel.tree
        self.sources_tree.bind("<<TreeviewSelect>>", lambda event: self.load_selected_source_detail())
        self.sources_tree.bind("<Double-1>", lambda event: self.toggle_selected_source())

    def _build_detail_panel(self, master: tk.Misc) -> None:
        panel = ttk.LabelFrame(master, text="Detalhes da fonte", style="Section.TLabelframe", padding=10)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, textvariable=self.detail_title_var, style="PanelTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        meta_cell(panel, row=1, col=0, label="Nome", variable=self.detail_name_var, wraplength=320)
        meta_cell(panel, row=1, col=1, label="Machine hint", variable=self.detail_machine_hint_var, wraplength=220)
        meta_cell(panel, row=2, col=0, label="Caminho", variable=self.detail_path_var, wraplength=420)
        meta_cell(panel, row=2, col=1, label="Ativa", variable=self.detail_enabled_var)
        meta_cell(panel, row=3, col=0, label="Recursiva", variable=self.detail_recursive_var)
        meta_cell(panel, row=3, col=1, label="Último scan", variable=self.detail_last_scan_var)
        meta_cell(panel, row=4, col=0, label="Checkpoint", variable=self.detail_checkpoint_var)
        meta_cell(panel, row=4, col=1, label="Criada em", variable=self.detail_created_var)
        meta_cell(panel, row=5, col=0, label="Atualizada em", variable=self.detail_updated_var)
        meta_cell(panel, row=5, col=1, label="Último run iniciado", variable=self.detail_last_run_start_var)
        meta_cell(panel, row=6, col=0, label="Último run finalizado", variable=self.detail_last_run_finish_var)
        meta_cell(panel, row=6, col=1, label="Resultado do último run", variable=self.detail_last_run_counts_var)
        meta_cell(panel, row=7, col=0, label="Notas do último run", variable=self.detail_last_run_notes_var, wraplength=420)

        actions = ttk.Frame(panel)
        actions.grid(row=8, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Nova fonte", command=self.create_source).pack(side="left")
        ttk.Button(actions, text="Alternar ativa", command=self.toggle_selected_source).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Resetar checkpoint", command=self.reset_selected_checkpoint).pack(side="left", padx=(8, 0))

    def _build_summary_panel(self, master: tk.Misc) -> None:
        panel = ttk.LabelFrame(master, text="Resumo", style="Section.TLabelframe", padding=10)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.columnconfigure(0, weight=1)

        metrics = ttk.Frame(panel)
        metrics.grid(row=0, column=0, sticky="ew")
        metrics.columnconfigure(0, weight=1)

        metric_cell(metrics, row=0, col=0, label="Total", variable=self.total_var)
        metric_cell(metrics, row=1, col=0, label="Habilitadas", variable=self.enabled_var)
        metric_cell(metrics, row=2, col=0, label="Desabilitadas", variable=self.disabled_var)
        metric_cell(metrics, row=3, col=0, label="Com checkpoint", variable=self.checkpoints_var)
        metric_cell(metrics, row=4, col=0, label="Com runs", variable=self.runs_var)
        metric_cell(metrics, row=5, col=0, label="Com erros", variable=self.errors_var)

        ttk.Separator(panel, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=(10, 10))

        ttk.Label(panel, text="Ações sugeridas", style="PanelTitle.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(
            panel,
            text=(
                "• Cadastre as pastas que concentram os logs reais.\n"
                "• Use machine hint para ajudar a identificar a origem.\n"
                "• Resetar checkpoint força nova leitura da fonte no próximo ciclo.\n"
                "• Fontes desabilitadas permanecem cadastradas, mas saem do fluxo."
            ),
            justify="left",
            wraplength=250,
        ).grid(row=3, column=0, sticky="nw", pady=(6, 0))

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.include_disabled_var.set(True)
        self.refresh_table()

    def refresh_all(self) -> None:
        self.snapshot = self.service.get_snapshot()
        self._apply_snapshot_metrics(self.snapshot)
        self.refresh_table()

    def refresh_table(self) -> None:
        previous_id = self.current_source_id
        rows = self.snapshot.rows if hasattr(self, "snapshot") else self.service.list_sources(include_disabled=True)

        if not self.include_disabled_var.get():
            rows = [row for row in rows if row.enabled]

        search_term = (self.search_var.get() or "").strip().lower()
        if search_term:
            rows = [row for row in rows if self._matches_search(row, search_term)]

        self._populate_sources_tree(rows)
        self.sources_count_var.set(str(len(rows)))

        if not rows:
            self.current_source_id = None
            self._clear_detail_panel()
            return

        selected_item = None
        for item_id in self.sources_tree.get_children():
            values = self.sources_tree.item(item_id, "values")
            if values and previous_id is not None and int(values[0]) == int(previous_id):
                selected_item = item_id
                break

        if selected_item is None:
            children = self.sources_tree.get_children()
            selected_item = children[0] if children else None

        if selected_item is not None:
            self.sources_tree.selection_set(selected_item)
            self.sources_tree.focus(selected_item)
            self.load_selected_source_detail()

    def create_source(self) -> None:
        dialog = CreateLogSourceDialog(self.winfo_toplevel())
        self.wait_window(dialog)

        if dialog.result is None:
            return

        try:
            created = self.service.create_source(dialog.result)
        except Exception as exc:
            messagebox.showerror("Fontes de logs", f"Falha ao salvar fonte.\n\nMotivo: {exc}", parent=self)
            return

        self.current_source_id = created.source_id
        self.refresh_all()

    def toggle_selected_source(self) -> None:
        row = self._get_selected_source()
        if row is None:
            messagebox.showwarning("Fontes de logs", "Selecione uma fonte primeiro.", parent=self)
            return

        try:
            if row.enabled:
                updated = self.service.disable_source(row.source_id)
            else:
                updated = self.service.enable_source(row.source_id)
        except Exception as exc:
            messagebox.showerror("Fontes de logs", f"Falha ao atualizar fonte.\n\nMotivo: {exc}", parent=self)
            return

        self.current_source_id = updated.source_id
        self.refresh_all()

    def reset_selected_checkpoint(self) -> None:
        row = self._get_selected_source()
        if row is None:
            messagebox.showwarning("Fontes de logs", "Selecione uma fonte primeiro.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Resetar checkpoint",
            f"Deseja resetar o checkpoint da fonte '{row.name}'?\n\n"
            "No próximo ciclo ela poderá ser relida desde o início.",
            parent=self,
        )
        if not confirm:
            return

        try:
            updated = self.service.reset_checkpoint(row.source_id)
        except Exception as exc:
            messagebox.showerror("Fontes de logs", f"Falha ao resetar checkpoint.\n\nMotivo: {exc}", parent=self)
            return

        self.current_source_id = updated.source_id
        self.refresh_all()

    def delete_selected_source(self) -> None:
        row = self._get_selected_source()
        if row is None:
            messagebox.showwarning("Fontes de logs", "Selecione uma fonte primeiro.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Remover fonte",
            f"Deseja remover a fonte '{row.name}'?\n\nEsta ação remove o cadastro da fonte.",
            parent=self,
        )
        if not confirm:
            return

        try:
            self.service.delete_source(row.source_id)
        except Exception as exc:
            messagebox.showerror("Fontes de logs", f"Falha ao remover fonte.\n\nMotivo: {exc}", parent=self)
            return

        self.current_source_id = None
        self.refresh_all()

    def load_selected_source_detail(self) -> None:
        row = self._get_selected_source()
        if row is None:
            self._clear_detail_panel()
            return

        self.current_source_id = row.source_id
        self._apply_detail(row)

    def _populate_sources_tree(self, rows: list[LogSourceRow]) -> None:
        clear_tree(self.sources_tree)
        for row in rows:
            self.sources_tree.insert(
                "",
                "end",
                values=(
                    row.source_id,
                    row.name,
                    row.machine_hint or "-",
                    "SIM" if row.enabled else "NÃO",
                    "SIM" if row.recursive else "NÃO",
                    row.path,
                    self._fmt_checkpoint(row.last_successful_mtime),
                    self._fmt_dt(row.last_run_started_at),
                ),
            )

    def _apply_snapshot_metrics(self, snapshot) -> None:
        self.total_var.set(str(snapshot.total_sources))
        self.enabled_var.set(str(snapshot.enabled_sources))
        self.disabled_var.set(str(snapshot.disabled_sources))
        self.checkpoints_var.set(str(snapshot.sources_with_checkpoint))
        self.runs_var.set(str(snapshot.sources_with_runs))
        self.errors_var.set(str(snapshot.sources_with_errors))

    def _apply_detail(self, row: LogSourceRow) -> None:
        self.detail_title_var.set(f"{row.name} (ID {row.source_id})")
        self.detail_name_var.set(row.name)
        self.detail_path_var.set(row.path)
        self.detail_machine_hint_var.set(row.machine_hint or "-")
        self.detail_enabled_var.set("SIM" if row.enabled else "NÃO")
        self.detail_recursive_var.set("SIM" if row.recursive else "NÃO")
        self.detail_last_scan_var.set(self._fmt_dt(row.last_scan_at))
        self.detail_checkpoint_var.set(self._fmt_checkpoint(row.last_successful_mtime))
        self.detail_created_var.set(self._fmt_dt(row.created_at))
        self.detail_updated_var.set(self._fmt_dt(row.updated_at))
        self.detail_last_run_start_var.set(self._fmt_dt(row.last_run_started_at))
        self.detail_last_run_finish_var.set(self._fmt_dt(row.last_run_finished_at))
        self.detail_last_run_counts_var.set(
            f"Encontrados: {row.last_run_total_found} • "
            f"Importados: {row.last_run_imported_count} • "
            f"Duplicados: {row.last_run_duplicate_count} • "
            f"Erros: {row.last_run_error_count}"
        )
        self.detail_last_run_notes_var.set(row.last_run_notes or "-")

    def _clear_detail_panel(self) -> None:
        self.detail_title_var.set("Nenhuma fonte selecionada")
        self.detail_name_var.set("-")
        self.detail_path_var.set("-")
        self.detail_machine_hint_var.set("-")
        self.detail_enabled_var.set("-")
        self.detail_recursive_var.set("-")
        self.detail_last_scan_var.set("-")
        self.detail_checkpoint_var.set("-")
        self.detail_created_var.set("-")
        self.detail_updated_var.set("-")
        self.detail_last_run_start_var.set("-")
        self.detail_last_run_finish_var.set("-")
        self.detail_last_run_counts_var.set("-")
        self.detail_last_run_notes_var.set("-")

    def _get_selected_source(self) -> LogSourceRow | None:
        selection = self.sources_tree.selection()
        if not selection:
            return None

        values = self.sources_tree.item(selection[0], "values")
        if not values:
            return None

        try:
            source_id = int(values[0])
        except (TypeError, ValueError):
            return None

        return self.service.get_source(source_id)

    @staticmethod
    def _matches_search(row: LogSourceRow, search_term: str) -> bool:
        haystack = " ".join(
            [
                str(row.source_id),
                row.name or "",
                row.path or "",
                row.machine_hint or "",
                "enabled" if row.enabled else "disabled",
                "recursive" if row.recursive else "flat",
            ]
        ).lower()
        return search_term in haystack

    @staticmethod
    def _fmt_dt(value) -> str:
        if value is None:
            return "-"
        try:
            return value.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_checkpoint(value: float | None) -> str:
        if value is None:
            return "-"
        return f"{value:.0f}"


def run_log_sources_panel(service: LogSourcesService | None = None) -> None:
    root = tk.Tk()
    LogSourcesPanel(root, service=service)
    root.mainloop()


def main() -> None:
    run_log_sources_panel()


if __name__ == "__main__":
    main()