# ui/home_panel.py
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from application.log_sources_service import LogSourceSnapshot, LogSourcesService
from application.operations_panel_service import (
    OpenRollRow,
    OperationsPanelService,
    OperationsSnapshotDTO,
    RollListFilters,
)
from ui.common_widgets import apply_common_styles


class HomePanel(ttk.Frame):
    """
    Home simplificada para testes funcionais.

    Objetivo:
    - abrir limpo
    - mostrar contexto mínimo
    - facilitar navegação para Operação, Rolos e Fontes
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        service: OperationsPanelService | None = None,
        log_sources_service: LogSourcesService | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master)

        self.service = service or OperationsPanelService()
        self.log_sources_service = log_sources_service or LogSourcesService()
        self.on_navigate = on_navigate

        self.jobs_var = tk.StringVar(value="0")
        self.open_rolls_var = tk.StringVar(value="0")
        self.pending_logs_var = tk.StringVar(value="0")
        self.enabled_sources_var = tk.StringVar(value="0")

        self.jobs_sub_var = tk.StringVar(value="Jobs disponíveis")
        self.open_rolls_sub_var = tk.StringVar(value="Rolos em aberto")
        self.pending_logs_sub_var = tk.StringVar(value="Logs pendentes")
        self.enabled_sources_sub_var = tk.StringVar(value="Fontes habilitadas")

        self.next_action_var = tk.StringVar(value="Carregando...")
        self.summary_var = tk.StringVar(value="Carregando resumo operacional...")

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

        self._build_actions()
        self._build_cards()
        self._build_bottom_area()

    def _build_actions(self) -> None:
        box = ttk.LabelFrame(self, text="Acesso rápido", padding=10)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(0, weight=1)

        buttons = ttk.Frame(box)
        buttons.grid(row=0, column=0, sticky="w")

        ttk.Button(
            buttons,
            text="Ir para Operação",
            command=lambda: self._navigate("operations"),
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="Consultar Rolos",
            command=lambda: self._navigate("rolls"),
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            buttons,
            text="Fontes de Logs",
            command=lambda: self._navigate("log_sources"),
        ).pack(side="left", padx=(8, 0))

        ttk.Label(
            box,
            text="Home reduzida para validar o fluxo sem poluição visual.",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_cards(self) -> None:
        cards = ttk.Frame(self)
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for col in range(4):
            cards.columnconfigure(col, weight=1)

        self._card(cards, 0, "Jobs disponíveis", self.jobs_var, self.jobs_sub_var)
        self._card(cards, 1, "Rolos em aberto", self.open_rolls_var, self.open_rolls_sub_var)
        self._card(cards, 2, "Logs pendentes", self.pending_logs_var, self.pending_logs_sub_var)
        self._card(cards, 3, "Fontes habilitadas", self.enabled_sources_var, self.enabled_sources_sub_var)

    def _card(
        self,
        master: tk.Misc,
        column: int,
        title: str,
        value_var: tk.StringVar,
        subtitle_var: tk.StringVar,
    ) -> None:
        card = ttk.LabelFrame(master, text=title, padding=12)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
        card.columnconfigure(0, weight=1)

        ttk.Label(
            card,
            textvariable=value_var,
            style="MetricValue.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            card,
            textvariable=subtitle_var,
            wraplength=240,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_bottom_area(self) -> None:
        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, sticky="nsew")
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(bottom, text="Próxima ação", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)

        ttk.Label(
            left,
            textvariable=self.next_action_var,
            wraplength=320,
            justify="left",
        ).grid(row=0, column=0, sticky="nw")

        right = ttk.LabelFrame(bottom, text="Resumo operacional", padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ttk.Label(
            right,
            textvariable=self.summary_var,
            wraplength=860,
            justify="left",
        ).grid(row=0, column=0, sticky="nw")

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        try:
            snapshot = self.service.get_operations_snapshot()
            sources_snapshot = self.log_sources_service.get_snapshot()
            last_closed = self._load_last_closed_roll()

            self._apply_cards(snapshot, sources_snapshot)
            self.next_action_var.set(
                self._build_next_action_text(
                    snapshot=snapshot,
                    sources_snapshot=sources_snapshot,
                    last_closed=last_closed,
                )
            )
            self.summary_var.set(
                self._build_summary_text(
                    snapshot=snapshot,
                    sources_snapshot=sources_snapshot,
                    last_closed=last_closed,
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Nexor",
                f"Falha ao atualizar a Home.\n\nMotivo: {exc}",
                parent=self,
            )

    def _apply_cards(
        self,
        snapshot: OperationsSnapshotDTO,
        sources_snapshot: LogSourceSnapshot,
    ) -> None:
        self.jobs_var.set(str(snapshot.available_jobs_count))
        self.open_rolls_var.set(str(snapshot.open_rolls_count))
        self.pending_logs_var.set(str(snapshot.pending_logs_count))
        self.enabled_sources_var.set(str(sources_snapshot.enabled_sources))

        self.jobs_sub_var.set("Jobs fora de rolo")
        self.open_rolls_sub_var.set("Aguardando fechamento")
        self.pending_logs_sub_var.set("Ainda não tratados")
        self.enabled_sources_sub_var.set("Prontas para leitura")

    def _load_last_closed_roll(self) -> OpenRollRow | None:
        rows = self.service.list_rolls(RollListFilters(limit=None))
        closed = [row for row in rows if (row.status or "").upper() != "OPEN"]
        if not closed:
            return None

        closed.sort(
            key=lambda row: row.created_at if row.created_at is not None else datetime.min,
            reverse=True,
        )
        return closed[0]

    # ------------------------------------------------------------------
    # Text builders
    # ------------------------------------------------------------------

    def _build_next_action_text(
        self,
        *,
        snapshot: OperationsSnapshotDTO,
        sources_snapshot: LogSourceSnapshot,
        last_closed: OpenRollRow | None,
    ) -> str:
        if sources_snapshot.enabled_sources <= 0:
            return "Abra Fontes de Logs e habilite pelo menos uma origem antes de depender da fila operacional."

        if sources_snapshot.sources_with_errors > 0:
            return "Confira Fontes de Logs, porque existe pelo menos uma origem com erro recente."

        if snapshot.open_rolls_count > 0:
            return "Entre em Operação para continuar ou fechar um rolo já aberto."

        if snapshot.available_jobs_count > 0:
            return "Entre em Operação para montar um novo rolo com os jobs disponíveis."

        if snapshot.pending_logs_count > 0:
            return "Há logs pendentes. Vale conferir a fila na tela de Operação."

        if last_closed is not None:
            return "Use Rolos para revisar o histórico ou reexportar o último fechamento."

        return "Sem pressão operacional imediata. A base está pronta para novos testes."

    def _build_summary_text(
        self,
        *,
        snapshot: OperationsSnapshotDTO,
        sources_snapshot: LogSourceSnapshot,
        last_closed: OpenRollRow | None,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Jobs disponíveis: {snapshot.available_jobs_count}")
        parts.append(f"Jobs suspeitos: {snapshot.suspicious_jobs_count}")
        parts.append(f"Rolos em aberto: {snapshot.open_rolls_count}")
        parts.append(f"Logs pendentes: {snapshot.pending_logs_count}")
        parts.append(f"Logs prontos: {snapshot.ready_logs_count}")
        parts.append(f"Logs convertidos: {snapshot.converted_logs_count}")
        parts.append(f"Logs inválidos: {snapshot.invalid_logs_count}")
        parts.append(f"Logs duplicados: {snapshot.duplicated_logs_count}")
        parts.append(f"Fontes cadastradas: {sources_snapshot.total_sources}")
        parts.append(f"Fontes habilitadas: {sources_snapshot.enabled_sources}")
        parts.append(f"Fontes com erro: {sources_snapshot.sources_with_errors}")

        if last_closed is None:
            parts.append("Último rolo fechado: nenhum encontrado.")
        else:
            parts.append(
                "Último rolo fechado: "
                f"{last_closed.roll_name} • {last_closed.machine} • "
                f"{last_closed.fabric or 'Sem tecido'} • "
                f"{self._fmt_dt(last_closed.created_at)}"
            )

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _navigate(self, key: str) -> None:
        if callable(self.on_navigate):
            self.on_navigate(key)
            return
        messagebox.showinfo("Nexor", f"Navegação indisponível para: {key}", parent=self)

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str:
        if value is None:
            return "-"
        return value.strftime("%d/%m/%Y %H:%M")