from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from application.operations_panel_service import (
    OpenRollRow,
    OperationsPanelService,
    OperationsSnapshotDTO,
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

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

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
            title="Alertas operacionais",
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

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        try:
            snapshot = self.service.get_operations_snapshot()
            all_rolls = self.service.list_rolls(RollListFilters(limit=None))
            last_closed = self._pick_last_closed_roll(all_rolls)

            self._apply_snapshot_cards(snapshot, last_closed)
            self.recent_summary_var.set(
                self._build_recent_summary_text(
                    snapshot=snapshot,
                    last_closed=last_closed,
                )
            )
            self.next_action_var.set(
                self._build_next_action_text(
                    snapshot=snapshot,
                    last_closed=last_closed,
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Nexor",
                f"Falha ao atualizar a Home.\n\nMotivo: {exc}",
                parent=self,
            )

    def _apply_snapshot_cards(
        self,
        snapshot: OperationsSnapshotDTO,
        last_closed: OpenRollRow | None,
    ) -> None:
        self.available_jobs_var.set(str(snapshot.available_jobs_count))
        if snapshot.suspicious_jobs_count > 0:
            self.available_jobs_sub_var.set(
                f"{snapshot.suspicious_jobs_count} suspeito(s) entre os jobs disponíveis"
            )
        else:
            self.available_jobs_sub_var.set("Jobs prontos para uso")

        self.open_rolls_var.set(str(snapshot.open_rolls_count))
        if snapshot.open_rolls_count > 0:
            self.open_rolls_sub_var.set("Há rolos aguardando montagem ou fechamento")
        else:
            self.open_rolls_sub_var.set("Sem rolos em aberto")

        if last_closed is None:
            self.last_closed_var.set("Nenhum")
            self.last_closed_sub_var.set("Nenhum rolo fechado ainda")
        else:
            self.last_closed_var.set(last_closed.roll_name)
            self.last_closed_sub_var.set(
                f"{last_closed.machine} • {last_closed.fabric or 'Sem tecido'} • {self._fmt_dt(last_closed.created_at)}"
            )

        total_alerts = (
            snapshot.suspicious_jobs_count
            + snapshot.invalid_logs_count
            + snapshot.pending_logs_count
        )
        self.alerts_var.set(str(total_alerts))

        if total_alerts <= 0:
            self.alerts_sub_var.set("Sem alertas no momento")
        else:
            parts: list[str] = []
            if snapshot.suspicious_jobs_count > 0:
                parts.append(f"{snapshot.suspicious_jobs_count} suspeito(s)")
            if snapshot.pending_logs_count > 0:
                parts.append(f"{snapshot.pending_logs_count} log(s) pendente(s)")
            if snapshot.invalid_logs_count > 0:
                parts.append(f"{snapshot.invalid_logs_count} inválido(s)")
            self.alerts_sub_var.set(" • ".join(parts))

    # ------------------------------------------------------------------
    # Text builders
    # ------------------------------------------------------------------

    def _build_recent_summary_text(
        self,
        *,
        snapshot: OperationsSnapshotDTO,
        last_closed: OpenRollRow | None,
    ) -> str:
        lines: list[str] = []

        lines.append(f"Jobs disponíveis agora: {snapshot.available_jobs_count}")
        lines.append(f"Jobs suspeitos: {snapshot.suspicious_jobs_count}")
        lines.append(f"Rolos em aberto: {snapshot.open_rolls_count}")
        lines.append(f"Logs pendentes de parse/importação: {snapshot.pending_logs_count}")
        lines.append(f"Logs prontos para normalização/uso: {snapshot.ready_logs_count}")
        lines.append(f"Logs convertidos em job: {snapshot.converted_logs_count}")
        lines.append(f"Logs inválidos: {snapshot.invalid_logs_count}")
        lines.append(f"Logs duplicados: {snapshot.duplicated_logs_count}")

        if last_closed is None:
            lines.append("Último rolo fechado: nenhum registro encontrado ainda.")
        else:
            lines.append(
                "Último rolo fechado: "
                f"{last_closed.roll_name} • {last_closed.machine} • "
                f"{last_closed.fabric or 'Sem tecido'} • "
                f"{self._fmt_dt(last_closed.created_at)}"
            )

        lines.append("")
        if snapshot.open_rolls_count > 0:
            lines.append("Há rolos em aberto. O caminho mais natural agora é entrar em Operação.")
        elif snapshot.available_jobs_count > 0:
            lines.append("Há jobs disponíveis para começar uma nova montagem de rolo.")
        elif snapshot.pending_logs_count > 0:
            lines.append("Ainda existem logs pendentes; vale conferir a fila antes de concluir que não há trabalho.")
        else:
            lines.append("Não há pressão operacional imediata. O melhor uso da Home agora é consulta rápida do estado.")

        return "\n".join(lines)

    def _build_next_action_text(
        self,
        *,
        snapshot: OperationsSnapshotDTO,
        last_closed: OpenRollRow | None,
    ) -> str:
        if snapshot.invalid_logs_count > 0:
            return "Conferir a fila de logs na Operação, porque existem registros inválidos que podem esconder erro de origem."
        if snapshot.suspicious_jobs_count > 0:
            return "Entrar em Operação e revisar os jobs suspeitos antes de avançar para um fechamento novo."
        if snapshot.open_rolls_count > 0:
            return "Retomar a montagem ou fechar um dos rolos em aberto."
        if snapshot.available_jobs_count > 0:
            return "Iniciar um novo fechamento de rolo a partir dos jobs disponíveis."
        if snapshot.pending_logs_count > 0:
            return "Entrar em Operação e conferir a fila de logs pendentes."
        if last_closed is not None:
            return "Consultar Rolos para revisão histórica ou exportação adicional, se necessário."
        return "Aguardar nova entrada operacional ou usar a consulta de rolos para inspeção histórica."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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