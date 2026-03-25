from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from application.operations_panel_service import (
    AvailableJobsFilters,
    OpenRollRow,
    OperationsPanelService,
    RollListFilters,
)
from ui.common_widgets import apply_common_styles


class HomePanel(ttk.Frame):
    """
    Página Home do Nexor em modo content-only.

    O shell principal pertence ao MainWindow.
    A Home deve ser um painel operacional simples, com:
    - ação principal clara
    - cards de contexto rápido
    - atalhos
    - leitura operacional recente
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        service: OperationsPanelService | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.service = service or OperationsPanelService()
        self.on_navigate = on_navigate

        self.available_jobs_var = tk.StringVar(value="0")
        self.open_rolls_var = tk.StringVar(value="0")
        self.last_closed_var = tk.StringVar(value="Nenhum")
        self.alerts_var = tk.StringVar(value="0")

        self.available_jobs_sub_var = tk.StringVar(value="Jobs prontos para uso")
        self.open_rolls_sub_var = tk.StringVar(value="Sem rolos em aberto")
        self.last_closed_sub_var = tk.StringVar(value="Nenhum rolo fechado ainda")
        self.alerts_sub_var = tk.StringVar(value="Sem alertas no momento")

        self.recent_summary_var = tk.StringVar(value="Carregando resumo operacional...")
        self.next_action_var = tk.StringVar(value="Verificando próxima ação sugerida...")

        apply_common_styles()
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_primary_action()
        self._build_summary_cards()
        self._build_main_content()

    def _build_primary_action(self) -> None:
        box = ttk.LabelFrame(self, text="Ação principal", style="Section.TLabelframe", padding=12)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(0, weight=1)

        ttk.Label(
            box,
            text="O próximo passo operacional deve ficar óbvio em poucos segundos.",
            wraplength=900,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(box)
        actions.grid(row=1, column=0, sticky="w", pady=(10, 0))

        ttk.Button(
            actions,
            text="Novo fechamento de rolo",
            command=lambda: self._navigate("operations"),
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Consultar rolos",
            command=lambda: self._navigate("rolls"),
        ).pack(side="left", padx=(8, 0))

    def _build_summary_cards(self) -> None:
        cards = ttk.Frame(self)
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            cards.columnconfigure(col, weight=1)

        self._card(
            cards,
            column=0,
            title="Jobs disponíveis",
            value_var=self.available_jobs_var,
            subtitle_var=self.available_jobs_sub_var,
        )
        self._card(
            cards,
            column=1,
            title="Rolos em aberto",
            value_var=self.open_rolls_var,
            subtitle_var=self.open_rolls_sub_var,
        )
        self._card(
            cards,
            column=2,
            title="Último rolo fechado",
            value_var=self.last_closed_var,
            subtitle_var=self.last_closed_sub_var,
        )
        self._card(
            cards,
            column=3,
            title="Alertas / suspeitas",
            value_var=self.alerts_var,
            subtitle_var=self.alerts_sub_var,
        )

    def _card(
        self,
        master: tk.Misc,
        *,
        column: int,
        title: str,
        value_var: tk.StringVar,
        subtitle_var: tk.StringVar,
    ) -> None:
        card = ttk.LabelFrame(master, text=title, style="Section.TLabelframe", padding=12)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
        card.columnconfigure(0, weight=1)

        ttk.Label(
            card,
            textvariable=value_var,
            style="MetricValue.TLabel",
            wraplength=240,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            card,
            textvariable=subtitle_var,
            wraplength=240,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_main_content(self) -> None:
        content = ttk.Frame(self)
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._build_quick_actions(content)
        self._build_recent_summary(content)

    def _build_quick_actions(self, master: tk.Misc) -> None:
        left = ttk.LabelFrame(master, text="Ações rápidas", style="Section.TLabelframe", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)

        ttk.Button(left, text="Ir para Operação", command=lambda: self._navigate("operations")).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(left, text="Consultar Rolos", command=lambda: self._navigate("rolls")).grid(
            row=1, column=0, sticky="ew", pady=(8, 0)
        )
        ttk.Button(left, text="Planejamento", state="disabled").grid(
            row=2, column=0, sticky="ew", pady=(8, 0)
        )
        ttk.Button(left, text="Estoque", state="disabled").grid(
            row=3, column=0, sticky="ew", pady=(8, 0)
        )
        ttk.Button(left, text="Cadastros", state="disabled").grid(
            row=4, column=0, sticky="ew", pady=(8, 0)
        )

        ttk.Separator(left, orient="horizontal").grid(row=5, column=0, sticky="ew", pady=(12, 12))

        ttk.Label(left, text="Próxima ação sugerida", style="PanelTitle.TLabel").grid(
            row=6, column=0, sticky="w"
        )
        ttk.Label(
            left,
            textvariable=self.next_action_var,
            wraplength=280,
            justify="left",
        ).grid(row=7, column=0, sticky="w", pady=(6, 0))

    def _build_recent_summary(self, master: tk.Misc) -> None:
        right = ttk.LabelFrame(master, text="Resumo operacional recente", style="Section.TLabelframe", padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ttk.Label(
            right,
            textvariable=self.recent_summary_var,
            wraplength=760,
            justify="left",
        ).grid(row=0, column=0, sticky="nw")

    def refresh_all(self) -> None:
        try:
            all_jobs = self.service.list_available_jobs(AvailableJobsFilters(limit=None))
            all_rolls = self.service.list_rolls(RollListFilters(limit=None))

            pending_review = 0
            suspicious_jobs = 0

            for row in all_jobs:
                if row.review_status == "PENDING_REVIEW":
                    pending_review += 1
                if row.is_suspicious:
                    suspicious_jobs += 1

            open_rolls = [r for r in all_rolls if (r.status or "").upper() == "OPEN"]
            last_closed = self._pick_last_closed_roll(all_rolls)

            self.available_jobs_var.set(str(len(all_jobs)))
            if pending_review > 0:
                self.available_jobs_sub_var.set(f"{pending_review} pendente(s) de review")
            else:
                self.available_jobs_sub_var.set("Jobs prontos para uso")

            self.open_rolls_var.set(str(len(open_rolls)))
            if open_rolls:
                self.open_rolls_sub_var.set("Há rolos aguardando montagem/fechamento")
            else:
                self.open_rolls_sub_var.set("Sem rolos em aberto")

            if last_closed is None:
                self.last_closed_var.set("Nenhum")
                self.last_closed_sub_var.set("Nenhum rolo fechado ainda")
            else:
                self.last_closed_var.set(last_closed.roll_name)
                created_txt = self._fmt_dt(last_closed.created_at)
                self.last_closed_sub_var.set(
                    f"{last_closed.machine} • {last_closed.fabric or 'Sem tecido'} • {created_txt}"
                )

            total_alerts = pending_review + suspicious_jobs
            self.alerts_var.set(str(total_alerts))
            if total_alerts == 0:
                self.alerts_sub_var.set("Sem alertas no momento")
            else:
                self.alerts_sub_var.set(
                    f"{suspicious_jobs} suspeito(s) • {pending_review} pendente(s)"
                )

            self.recent_summary_var.set(
                self._build_recent_summary_text(
                    jobs_count=len(all_jobs),
                    open_rolls_count=len(open_rolls),
                    pending_review=pending_review,
                    suspicious_jobs=suspicious_jobs,
                    last_closed=last_closed,
                )
            )
            self.next_action_var.set(
                self._build_next_action_text(
                    open_rolls_count=len(open_rolls),
                    pending_review=pending_review,
                    suspicious_jobs=suspicious_jobs,
                    jobs_count=len(all_jobs),
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Nexor",
                f"Falha ao atualizar a Home.\n\nMotivo: {exc}",
                parent=self,
            )

    def _build_recent_summary_text(
        self,
        *,
        jobs_count: int,
        open_rolls_count: int,
        pending_review: int,
        suspicious_jobs: int,
        last_closed: OpenRollRow | None,
    ) -> str:
        lines: list[str] = []

        lines.append(f"Jobs disponíveis agora: {jobs_count}")
        lines.append(f"Rolos em aberto: {open_rolls_count}")
        lines.append(f"Pendentes de review: {pending_review}")
        lines.append(f"Jobs suspeitos: {suspicious_jobs}")

        if last_closed is None:
            lines.append("Último rolo fechado: nenhum registro encontrado ainda.")
        else:
            lines.append(
                "Último rolo fechado: "
                f"{last_closed.roll_name} • {last_closed.machine} • "
                f"{last_closed.fabric or 'Sem tecido'} • "
                f"{self._fmt_dt(last_closed.created_at)}"
            )

        if open_rolls_count > 0:
            lines.append("")
            lines.append("Há rolos em aberto. O caminho mais natural agora é entrar em Operação.")
        elif jobs_count > 0:
            lines.append("")
            lines.append("Há jobs disponíveis para começar uma nova montagem de rolo.")
        else:
            lines.append("")
            lines.append("Não há jobs disponíveis no momento. A próxima ação tende a ser consulta ou conferência.")

        return "\n".join(lines)

    def _build_next_action_text(
        self,
        *,
        open_rolls_count: int,
        pending_review: int,
        suspicious_jobs: int,
        jobs_count: int,
    ) -> str:
        if pending_review > 0 or suspicious_jobs > 0:
            return "Entrar em Operação e revisar os itens pendentes/suspeitos antes de avançar."
        if open_rolls_count > 0:
            return "Retomar a montagem ou fechar um dos rolos em aberto."
        if jobs_count > 0:
            return "Iniciar um novo fechamento de rolo a partir dos jobs disponíveis."
        return "Consultar Rolos para revisão histórica ou aguardar nova entrada operacional."

    def _pick_last_closed_roll(self, rolls: list[OpenRollRow]) -> OpenRollRow | None:
        closed_rolls = [r for r in rolls if (r.status or "").upper() != "OPEN"]
        if not closed_rolls:
            return None
        closed_rolls.sort(
            key=lambda r: r.created_at if r.created_at is not None else datetime.min,
            reverse=True,
        )
        return closed_rolls[0]

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