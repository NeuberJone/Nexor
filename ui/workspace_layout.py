from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TwoRowWorkspace(ttk.Frame):
    """
    Workspace reutilizável para páginas com:

    - área principal à esquerda dividida em 2 blocos verticais
    - painel lateral fixo à direita

    Estrutura:
        left_top
        left_bottom
        right_panel
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        right_width: int = 300,
        top_weight: int = 3,
        bottom_weight: int = 2,
        column_gap: int = 10,
        row_gap: int = 8,
    ) -> None:
        super().__init__(master)

        self.right_width = right_width
        self.column_gap = column_gap
        self.row_gap = row_gap

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=top_weight)
        self.rowconfigure(1, weight=bottom_weight)

        self.left_top = ttk.Frame(self)
        self.left_top.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, self.column_gap),
            pady=(0, self.row_gap),
        )
        self.left_top.columnconfigure(0, weight=1)
        self.left_top.rowconfigure(0, weight=1)

        self.left_bottom = ttk.Frame(self)
        self.left_bottom.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, self.column_gap),
        )
        self.left_bottom.columnconfigure(0, weight=1)
        self.left_bottom.rowconfigure(0, weight=1)

        self.right_panel = ttk.Frame(self, width=self.right_width)
        self.right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self.right_panel.grid_propagate(False)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=1)