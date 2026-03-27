from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from application.operations_panel_service import OperationsPanelService, RollSummaryDTO
from ui.common_widgets import apply_common_styles, fmt_m


class RollClosureDialog(tk.Toplevel):
    """
    Diálogo de fechamento de rolo.

    Objetivo:
    - revisar os dados do rolo antes do fechamento
    - permitir observação final
    - opcionalmente exportar logo após fechar
    - manter a regra de negócio no service
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        service: OperationsPanelService,
        summary: RollSummaryDTO,
    ) -> None:
        super().__init__(master)

        self.service = service
        self.summary = summary
        self.result_summary: RollSummaryDTO | None = None
        self.export_result: dict | None = None
        self.is_processing = False

        self.note_var = tk.StringVar(value=summary.note or "")
        self.export_after_close_var = tk.BooleanVar(value=False)
        self.export_dir_var = tk.StringVar(value="")

        self.title("Fechamento do rolo")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.columnconfigure(0, weight=1)

        apply_common_styles()
        self._build_ui()
        self._center(master)

        self.bind("<Escape>", lambda event: self._safe_close())
        self.bind("<Return>", self._on_confirm)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)

        self._build_header(root)
        self._build_roll_info(root)
        self._build_totals(root)
        self._build_warning_box(root)
        self._build_note_box(root)
        self._build_export_options(root)
        self._build_actions(root)

    def _build_header(self, master: tk.Misc) -> None:
        box = ttk.Frame(master)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)

        ttk.Label(
            box,
            text="Fechamento do rolo",
            style="PanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            box,
            text="Revise os dados abaixo antes de concluir o fechamento.",
            wraplength=620,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_roll_info(self, master: tk.Misc) -> None:
        info = ttk.LabelFrame(master, text="Dados do rolo", style="Section.TLabelframe", padding=10)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        info.columnconfigure(1, weight=1)

        self._info_row(info, 0, "Rolo", self.summary.roll_name)
        self._info_row(info, 1, "ID", str(self.summary.roll_id))
        self._info_row(info, 2, "Máquina", self.summary.machine)
        self._info_row(info, 3, "Tecido", self.summary.fabric or "-")
        self._info_row(info, 4, "Status atual", self.summary.status)
        self._info_row(info, 5, "Jobs", str(self.summary.jobs_count))

    def _build_totals(self, master: tk.Misc) -> None:
        box = ttk.LabelFrame(master, text="Resumo", style="Section.TLabelframe", padding=10)
        box.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=1)

        efficiency_text = self._format_efficiency(self.summary.efficiency_ratio)

        self._metric(box, 0, 0, "Planejado", fmt_m(self.summary.total_planned_m))
        self._metric(box, 0, 1, "Efetivo", fmt_m(self.summary.total_effective_m))
        self._metric(box, 1, 0, "Gap", fmt_m(self.summary.total_gap_m))
        self._metric(box, 1, 1, "Consumido", fmt_m(self.summary.total_consumed_m))
        self._metric(box, 2, 0, "Pendentes", str(self.summary.pending_review_count))
        self._metric(box, 2, 1, "Suspeitos", str(self.summary.suspicious_count))
        self._metric(box, 3, 0, "Revisados OK", str(self.summary.reviewed_ok_count))
        self._metric(box, 3, 1, "Eficiência", efficiency_text)

    def _build_warning_box(self, master: tk.Misc) -> None:
        needs_attention = self.summary.pending_review_count > 0 or self.summary.suspicious_count > 0
        title = "Atenção" if needs_attention else "Observação final"

        box = ttk.LabelFrame(master, text=title, style="Section.TLabelframe", padding=10)
        box.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)

        if needs_attention:
            parts: list[str] = []
            if self.summary.pending_review_count > 0:
                parts.append(
                    f"- Este rolo contém {self.summary.pending_review_count} job(s) com PENDING_REVIEW."
                )
            if self.summary.suspicious_count > 0:
                parts.append(
                    f"- Este rolo contém {self.summary.suspicious_count} item(ns) marcado(s) como suspeito(s)."
                )
            parts.append("- Ao fechar, o rolo deixa de aceitar novas alterações operacionais.")
            text = "\n".join(parts)
        else:
            text = (
                "Nenhum alerta crítico foi identificado neste rolo.\n"
                "Você pode fechar normalmente ou adicionar uma observação final."
            )

        ttk.Label(
            box,
            text=text,
            wraplength=620,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

    def _build_note_box(self, master: tk.Misc) -> None:
        box = ttk.LabelFrame(master, text="Observação final", style="Section.TLabelframe", padding=10)
        box.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)

        ttk.Entry(box, textvariable=self.note_var).grid(row=0, column=0, sticky="ew")

    def _build_export_options(self, master: tk.Misc) -> None:
        box = ttk.LabelFrame(master, text="Exportação", style="Section.TLabelframe", padding=10)
        box.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            box,
            text="Exportar imediatamente após fechar",
            variable=self.export_after_close_var,
            command=self._toggle_export_state,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(box, text="Pasta:").grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.export_dir_entry = ttk.Entry(box, textvariable=self.export_dir_var, state="disabled")
        self.export_dir_entry.grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))

        self.export_dir_button = ttk.Button(
            box,
            text="Selecionar",
            command=self._choose_export_dir,
            state="disabled",
        )
        self.export_dir_button.grid(row=1, column=2, sticky="e", pady=(10, 0))

    def _build_actions(self, master: tk.Misc) -> None:
        actions = ttk.Frame(master)
        actions.grid(row=6, column=0, sticky="e")

        self.cancel_button = ttk.Button(actions, text="Cancelar", command=self._safe_close)
        self.cancel_button.pack(side="right")

        self.confirm_button = ttk.Button(
            actions,
            text="Confirmar fechamento",
            command=self._confirm,
        )
        self.confirm_button.pack(side="right", padx=(0, 8))

    # ------------------------------------------------------------------
    # Small UI helpers
    # ------------------------------------------------------------------

    def _info_row(self, master: tk.Misc, row: int, label: str, value: str) -> None:
        ttk.Label(master, text=f"{label}:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=2)
        ttk.Label(master, text=value, wraplength=420, justify="left").grid(
            row=row,
            column=1,
            sticky="w",
            pady=2,
        )

    def _metric(self, master: tk.Misc, row: int, col: int, label: str, value: str) -> None:
        cell = ttk.Frame(master)
        cell.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
        ttk.Label(cell, text=label).pack(anchor="w")
        ttk.Label(cell, text=value, style="MetricValue.TLabel").pack(anchor="w", pady=(2, 0))

    def _toggle_export_state(self) -> None:
        enabled = self.export_after_close_var.get()
        state = "normal" if enabled else "disabled"
        self.export_dir_entry.configure(state=state)
        self.export_dir_button.configure(state=state)

    def _choose_export_dir(self) -> None:
        directory = filedialog.askdirectory(
            title="Selecione a pasta de exportação",
            parent=self,
        )
        if directory:
            self.export_dir_var.set(directory)

    def _on_confirm(self, event: tk.Event | None = None) -> None:
        self._confirm()

    def _set_processing(self, is_processing: bool) -> None:
        self.is_processing = is_processing
        confirm_state = "disabled" if is_processing else "normal"
        cancel_state = "disabled" if is_processing else "normal"
        browse_state = "disabled"

        if not is_processing and self.export_after_close_var.get():
            browse_state = "normal"

        self.confirm_button.configure(state=confirm_state)
        self.cancel_button.configure(state=cancel_state)
        self.export_dir_button.configure(state=browse_state)
        self.export_dir_entry.configure(state=("normal" if browse_state == "normal" else "disabled"))

    def _safe_close(self) -> None:
        if self.is_processing:
            return
        self.destroy()

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        if self.is_processing:
            return

        if self.summary.jobs_count <= 0:
            messagebox.showwarning(
                "Fechamento do rolo",
                "Não é possível fechar um rolo vazio.",
                parent=self,
            )
            return

        export_after = self.export_after_close_var.get()
        export_dir = self.export_dir_var.get().strip()

        if export_after and not export_dir:
            messagebox.showwarning(
                "Fechamento do rolo",
                "Selecione a pasta de exportação.",
                parent=self,
            )
            return

        if self.summary.pending_review_count > 0:
            proceed = messagebox.askyesno(
                "Fechamento do rolo",
                "Este rolo possui jobs com PENDING_REVIEW.\n\nDeseja fechar mesmo assim?",
                parent=self,
            )
            if not proceed:
                return

        self._set_processing(True)
        try:
            closed_summary = self.service.close_roll(
                roll_id=self.summary.roll_id,
                note=self.note_var.get().strip() or None,
            )
            self.result_summary = closed_summary

            if export_after:
                self.export_result = self.service.export_roll(
                    roll_id=closed_summary.roll_id,
                    output_dir=Path(export_dir),
                )

        except Exception as exc:
            self._set_processing(False)
            messagebox.showerror(
                "Fechamento do rolo",
                f"Falha ao concluir o fechamento.\n\nMotivo: {exc}",
                parent=self,
            )
            return

        self.destroy()

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    def _center(self, master: tk.Misc) -> None:
        self.update_idletasks()

        if isinstance(master, (tk.Tk, tk.Toplevel)):
            root_x = master.winfo_rootx()
            root_y = master.winfo_rooty()
            root_w = master.winfo_width() or 1200
            root_h = master.winfo_height() or 800
        else:
            root_x, root_y, root_w, root_h = 100, 100, 1200, 800

        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        x = root_x + max((root_w - width) // 2, 0)
        y = root_y + max((root_h - height) // 2, 0)

        self.geometry(f"+{x}+{y}")

    @staticmethod
    def _format_efficiency(value: float | None) -> str:
        if value is None:
            return "-"
        try:
            return f"{value * 100:.1f}%"
        except Exception:
            return "-"