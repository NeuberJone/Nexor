from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.common_widgets import apply_common_styles, metric_cell


class RollSummaryPanel(ttk.LabelFrame):
    """
    Painel lateral reutilizável para:

    - métricas do rolo
    - ações operacionais

    metrics:
        list[tuple[str, tk.StringVar]]

    actions:
        list[tuple[str, callable]]
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str = "Resumo",
        width: int = 300,
        metrics: list[tuple[str, tk.StringVar]] | None = None,
        actions: list[tuple[str, object]] | None = None,
    ) -> None:
        super().__init__(master, text=title, style="Section.TLabelframe", padding=8)

        apply_common_styles()

        self.configure(width=width)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.metrics = metrics or []
        self.actions = actions or []

        self._build_metrics()
        self._build_actions()

    def _build_metrics(self) -> None:
        for index, (label, variable) in enumerate(self.metrics):
            row = index // 2
            col = index % 2
            metric_cell(self, row=row, col=col, label=label, variable=variable)

    def _build_actions(self) -> None:
        if not self.actions:
            return

        start_row = (len(self.metrics) + 1) // 2
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=start_row, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)

        for index, (text, command) in enumerate(self.actions):
            row = index // 2
            col = index % 2
            padx = (0, 8) if col == 0 else (0, 0)
            pady = (0, 0) if row == 0 else (8, 0)
            ttk.Button(actions_frame, text=text, command=command).grid(
                row=row,
                column=col,
                sticky="ew",
                padx=padx,
                pady=pady,
            )