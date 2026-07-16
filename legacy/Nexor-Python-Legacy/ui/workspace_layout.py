# ui/workspace_layout.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TwoRowWorkspace(ttk.Frame):
    """
    Workspace reutilizável para páginas com:

    - área principal à esquerda dividida em 2 blocos verticais
    - painel lateral à direita
    - possibilidade de ajuste visual por sash

    Estrutura pública:
        left_top
        left_bottom
        right_panel

    Motivação:
    - o grid puro estava deixando a distribuição muito dependente do conteúdo
    - com paned windows, a proporção inicial fica mais previsível
    - o usuário pode ajustar visualmente em tempo de teste se necessário
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
        left_min_width: int = 680,
        right_min_width: int = 220,
        top_min_height: int = 180,
        bottom_min_height: int = 220,
    ) -> None:
        super().__init__(master)

        self.right_width = int(right_width)
        self.column_gap = int(column_gap)
        self.row_gap = int(row_gap)
        self.top_weight = max(1, int(top_weight))
        self.bottom_weight = max(1, int(bottom_weight))

        self.left_min_width = int(left_min_width)
        self.right_min_width = int(right_min_width)
        self.top_min_height = int(top_min_height)
        self.bottom_min_height = int(bottom_min_height)

        self._layout_initialized = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_ui()
        self.bind("<Configure>", self._on_configure)
        self.after_idle(self._apply_initial_layout)

    def _build_ui(self) -> None:
        self.main_pane = tk.PanedWindow(
            self,
            orient="horizontal",
            sashwidth=6,
            sashpad=0,
            opaqueresize=True,
            bd=0,
            highlightthickness=0,
        )
        self.main_pane.grid(row=0, column=0, sticky="nsew")

        self.left_wrapper = ttk.Frame(self, padding=(0, 0, self.column_gap, 0))
        self.left_wrapper.columnconfigure(0, weight=1)
        self.left_wrapper.rowconfigure(0, weight=1)

        self.left_pane = tk.PanedWindow(
            self.left_wrapper,
            orient="vertical",
            sashwidth=6,
            sashpad=0,
            opaqueresize=True,
            bd=0,
            highlightthickness=0,
        )
        self.left_pane.grid(row=0, column=0, sticky="nsew")

        self.left_top = ttk.Frame(self.left_pane, padding=(0, 0, 0, self.row_gap))
        self.left_top.columnconfigure(0, weight=1)
        self.left_top.rowconfigure(0, weight=1)

        self.left_bottom = ttk.Frame(self.left_pane)
        self.left_bottom.columnconfigure(0, weight=1)
        self.left_bottom.rowconfigure(0, weight=1)

        self.right_panel = ttk.Frame(self.main_pane, width=self.right_width)
        self.right_panel.grid_propagate(False)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=1)

        self.left_pane.add(self.left_top, minsize=self.top_min_height)
        self.left_pane.add(self.left_bottom, minsize=self.bottom_min_height)

        self.main_pane.add(self.left_wrapper, minsize=self.left_min_width)
        self.main_pane.add(self.right_panel, minsize=self.right_min_width)

    def _on_configure(self, event: tk.Event | None = None) -> None:
        if not self._layout_initialized:
            self._apply_initial_layout()

    def _apply_initial_layout(self) -> None:
        total_width = self.winfo_width()
        total_height = self.winfo_height()

        if total_width <= 1 or total_height <= 1:
            self.after(50, self._apply_initial_layout)
            return

        self._apply_horizontal_layout(total_width)
        self._apply_vertical_layout(total_height)
        self._layout_initialized = True

    def _apply_horizontal_layout(self, total_width: int) -> None:
        usable_width = max(total_width, self.left_min_width + self.right_min_width)

        target_right = min(
            max(self.right_width, self.right_min_width),
            max(self.right_min_width, usable_width - self.left_min_width),
        )
        sash_x = max(self.left_min_width, usable_width - target_right)

        try:
            self.main_pane.sash_place(0, sash_x, 0)
        except tk.TclError:
            pass

        self.right_panel.configure(width=target_right)

    def _apply_vertical_layout(self, total_height: int) -> None:
        total_weight = self.top_weight + self.bottom_weight
        desired_top = int(total_height * (self.top_weight / total_weight))

        min_top = self.top_min_height
        max_top = max(min_top, total_height - self.bottom_min_height)
        sash_y = min(max(desired_top, min_top), max_top)

        try:
            self.left_pane.sash_place(0, 0, sash_y)
        except tk.TclError:
            pass

    def set_right_width(self, width: int) -> None:
        self.right_width = int(width)
        self.right_panel.configure(width=self.right_width)
        self.after_idle(self._reapply_layout)

    def set_row_weights(self, top_weight: int, bottom_weight: int) -> None:
        self.top_weight = max(1, int(top_weight))
        self.bottom_weight = max(1, int(bottom_weight))
        self.after_idle(self._reapply_layout)

    def set_min_sizes(
        self,
        *,
        left_min_width: int | None = None,
        right_min_width: int | None = None,
        top_min_height: int | None = None,
        bottom_min_height: int | None = None,
    ) -> None:
        if left_min_width is not None:
            self.left_min_width = int(left_min_width)
        if right_min_width is not None:
            self.right_min_width = int(right_min_width)
        if top_min_height is not None:
            self.top_min_height = int(top_min_height)
        if bottom_min_height is not None:
            self.bottom_min_height = int(bottom_min_height)

        try:
            self.main_pane.paneconfigure(self.left_wrapper, minsize=self.left_min_width)
            self.main_pane.paneconfigure(self.right_panel, minsize=self.right_min_width)
            self.left_pane.paneconfigure(self.left_top, minsize=self.top_min_height)
            self.left_pane.paneconfigure(self.left_bottom, minsize=self.bottom_min_height)
        except tk.TclError:
            pass

        self.after_idle(self._reapply_layout)

    def _reapply_layout(self) -> None:
        total_width = self.winfo_width()
        total_height = self.winfo_height()

        if total_width <= 1 or total_height <= 1:
            return

        self._apply_horizontal_layout(total_width)
        self._apply_vertical_layout(total_height)