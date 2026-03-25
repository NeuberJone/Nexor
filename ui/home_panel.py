from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from application.operations_panel_service import (
    AvailableJobsFilters,
    OperationsPanelService,
    RollListFilters,
)
from ui.common_widgets import apply_common_styles


class HomePanel(ttk.Frame):
    """
    Página Home do Nexor em modo content-only.

    O shell (sidebar, topbar, footer e ações globais)
    pertence ao MainWindow.

    Esta página mostra apenas:
    - cards de resumo
    - leitura operacional
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        service: OperationsPanelService | None = None,
        on_navigate=None,
    ) -> None:
        super().__init__(master)
        self.service = service or OperationsPanelService()
        self.on_navigate = on_navigate

        self.available_jobs_var = tk.StringVar(value="0")
        self.open_rolls_var = tk.StringVar(value="0")
        self.pending_review_var = tk.StringVar(value="0")
        self.suspicious_jobs_var = tk.StringVar(value="0")

        apply_common_styles()
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_summary_cards()
        self._build_main_content()

    def _build_summary_cards(self) -> None:
        cards = ttk.Frame(self)
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            cards.columnconfigure(col, weight=1)

        self._card(cards, 0, "Jobs disponíveis", self.available_jobs_var)
        self._card(cards, 1, "Rolos abertos", self.open_rolls_var)
        self._card(cards, 2, "Pendentes review", self.pending_review_var)
        self._card(cards, 3, "Jobs suspeitos", self.suspicious_jobs_var)

    def _card(self, master: tk.Misc, column: int, title: str, value_var: tk.StringVar) -> None:
        card = ttk.LabelFrame(master, text=title, style="Section.TLabelframe", padding=12)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))
        ttk.Label(card, textvariable=value_var, style="MetricValue.TLabel").pack(anchor="w")
        ttk.Label(card, text="Resumo operacional atual").pack(anchor="w", pady=(4, 0))

    def _build_main_content(self) -> None:
        content = ttk.Frame(self)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        left = ttk.LabelFrame(content, text="Leitura rápida", style="Section.TLabelframe", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        left_text = (
            "A Home resume o estado atual da operação.\n\n"
            "Use a navegação lateral para entrar em Operação ou Rolos.\n\n"
            "Ações globais ficam no shell principal."
        )
        ttk.Label(left, text=left_text, wraplength=520, justify="left").grid(row=0, column=0, sticky="nw")

        right = ttk.LabelFrame(content, text="Leitura operacional", style="Section.TLabelframe", padding=12)
        right.grid(row=0, column=1, sticky="nsew")

        right_text = (
            "Use Operação para montar e fechar rolos.\n\n"
            "Use Rolos para consultar, revisar detalhes e reexportar quando necessário.\n\n"
            "Esta Home existe para dar contexto rápido, não para substituir os fluxos principais."
        )
        ttk.Label(right, text=right_text, wraplength=520, justify="left").grid(row=0, column=0, sticky="nw")

    def refresh_all(self) -> None:
        try:
            all_jobs = self.service.list_available_jobs(AvailableJobsFilters(limit=None))
            open_rolls = self.service.list_rolls(RollListFilters(status="OPEN", limit=None))

            pending_review = 0
            suspicious_jobs = 0

            for row in all_jobs:
                if row.review_status == "PENDING_REVIEW":
                    pending_review += 1
                if row.is_suspicious:
                    suspicious_jobs += 1

            self.available_jobs_var.set(str(len(all_jobs)))
            self.open_rolls_var.set(str(len(open_rolls)))
            self.pending_review_var.set(str(pending_review))
            self.suspicious_jobs_var.set(str(suspicious_jobs))

        except Exception as exc:
            messagebox.showerror(
                "Nexor",
                f"Falha ao atualizar a Home.\n\nMotivo: {exc}",
                parent=self,
            )