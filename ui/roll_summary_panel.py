# ui/roll_summary_panel.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.common_widgets import apply_common_styles, metric_cell


class RollSummaryPanel(ttk.LabelFrame):
    """
    Painel lateral reutilizável para:

    - métricas do rolo
    - ações operacionais
    - texto de apoio opcional

    metrics:
        list[tuple[str, tk.StringVar]]

    actions:
        list[tuple[str, callable]]

    Direção visual:
    - métricas compactas em grade
    - ações em coluna única por padrão, para evitar botões cortados
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str = "Resumo",
        width: int = 300,
        metrics: list[tuple[str, tk.StringVar]] | None = None,
        actions: list[tuple[str, object]] | None = None,
        helper_text: str | None = None,
        metrics_columns: int = 2,
        actions_columns: int = 1,
    ) -> None:
        super().__init__(master, text=title, style="Section.TLabelframe", padding=8)

        apply_common_styles()

        self.configure(width=width)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)

        self.metrics = metrics or []
        self.actions = actions or []
        self.helper_text = helper_text
        self.metrics_columns = max(1, int(metrics_columns or 1))
        self.actions_columns = max(1, int(actions_columns or 1))

        self._next_row = 0

        self._build_header()
        self._build_metrics()
        self._build_actions()

    def _build_header(self) -> None:
        if not self.helper_text:
            return

        header = ttk.Frame(self)
        header.grid(row=self._next_row, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=self.helper_text,
            style="Muted.TLabel",
            wraplength=260,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self._next_row += 1

    def _build_metrics(self) -> None:
        if not self.metrics:
            return

        metrics_box = ttk.Frame(self)
        metrics_box.grid(row=self._next_row, column=0, sticky="ew")

        for col in range(self.metrics_columns):
            metrics_box.columnconfigure(col, weight=1)

        for index, (label, variable) in enumerate(self.metrics):
            row = index // self.metrics_columns
            col = index % self.metrics_columns
            metric_cell(metrics_box, row=row, col=col, label=label, variable=variable)

        self._next_row += 1

    def _build_actions(self) -> None:
        if not self.actions:
            return

        separator = ttk.Separator(self, orient="horizontal")
        separator.grid(row=self._next_row, column=0, sticky="ew", pady=(12, 10))
        self._next_row += 1

        actions_header = ttk.Frame(self)
        actions_header.grid(row=self._next_row, column=0, sticky="ew", pady=(0, 8))
        actions_header.columnconfigure(0, weight=1)

        ttk.Label(
            actions_header,
            text="Ações do rolo",
            style="PanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        self._next_row += 1

        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=self._next_row, column=0, sticky="ew")

        for col in range(self.actions_columns):
            actions_frame.columnconfigure(col, weight=1)

        for index, (text, command) in enumerate(self.actions):
            row = index // self.actions_columns
            col = index % self.actions_columns

            if self.actions_columns == 1:
                padx = 0
            else:
                padx = (0, 8) if col < self.actions_columns - 1 else (0, 0)

            pady = (0, 0) if row == 0 else (8, 0)

            ttk.Button(
                actions_frame,
                text=text,
                command=command,
            ).grid(
                row=row,
                column=col,
                sticky="ew",
                padx=padx,
                pady=pady,
            )