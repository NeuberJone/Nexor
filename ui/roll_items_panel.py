from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable

from ui.common_widgets import (
    apply_common_styles,
    clear_tree,
    configure_tree_columns,
    meta_cell,
)


class RollItemsPanel(ttk.LabelFrame):
    """
    Bloco reutilizável para exibir:

    - título do rolo
    - metadados do rolo
    - tabela de itens do rolo
    - ações no cabeçalho (opcional)

    O conteúdo dos itens é inserido por tuplas já formatadas.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        panel_title: str,
        title_var: tk.StringVar,
        meta_fields: list[tuple[str, tk.StringVar]],
        tree_columns: dict[str, tuple[str, int]],
        left_aligned_columns: set[str] | None = None,
        header_actions: list[tuple[str, object]] | None = None,
        tree_title: str = "Itens do rolo",
        title_wraplength: int = 700,
        helper_text: str | None = None,
    ) -> None:
        super().__init__(master, text=panel_title, style="Section.TLabelframe", padding=8)

        apply_common_styles()

        self.title_var = title_var
        self.meta_fields = meta_fields
        self.tree_columns = tree_columns
        self.left_aligned_columns = left_aligned_columns or set()
        self.header_actions = header_actions or []
        self.tree_title = tree_title
        self.title_wraplength = title_wraplength
        self.helper_text = helper_text

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.items_tree: ttk.Treeview

        self._build_ui()

    def _build_ui(self) -> None:
        self._build_title_row()
        self._build_meta_row()
        self._build_items_box()

    def _build_title_row(self) -> None:
        title_row = ttk.Frame(self)
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        title_row.columnconfigure(0, weight=1)

        title_box = ttk.Frame(title_row)
        title_box.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_box,
            textvariable=self.title_var,
            style="PanelTitle.TLabel",
            wraplength=self.title_wraplength,
        ).pack(anchor="w")

        if self.helper_text:
            ttk.Label(
                title_box,
                text=self.helper_text,
                style="Muted.TLabel",
                wraplength=self.title_wraplength,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

        if self.header_actions:
            buttons = ttk.Frame(title_row)
            buttons.grid(row=0, column=1, sticky="e")

            for index, (text, command) in enumerate(self.header_actions):
                padx = (8, 0) if index > 0 else (0, 0)
                ttk.Button(buttons, text=text, command=command).pack(side="left", padx=padx)

    def _build_meta_row(self) -> None:
        meta = ttk.Frame(self)
        meta.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        total = max(len(self.meta_fields), 1)
        for col in range(total):
            meta.columnconfigure(col, weight=1)

        for col, (label, variable) in enumerate(self.meta_fields):
            meta_cell(meta, row=0, col=col, label=label, variable=variable)

    def _build_items_box(self) -> None:
        items_box = ttk.LabelFrame(self, text=self.tree_title, style="Section.TLabelframe", padding=6)
        items_box.grid(row=2, column=0, sticky="nsew")
        items_box.columnconfigure(0, weight=1)
        items_box.rowconfigure(0, weight=1)

        self.items_tree = ttk.Treeview(
            items_box,
            columns=tuple(self.tree_columns.keys()),
            show="headings",
            selectmode="browse",
        )
        self.items_tree.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(items_box, orient="vertical", command=self.items_tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")

        sb_x = ttk.Scrollbar(items_box, orient="horizontal", command=self.items_tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")

        self.items_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        configure_tree_columns(
            self.items_tree,
            self.tree_columns,
            left_aligned=self.left_aligned_columns,
        )

    def set_items(self, rows: Iterable[tuple]) -> None:
        clear_tree(self.items_tree)
        for row in rows:
            self.items_tree.insert("", "end", values=row)

    def clear_items(self) -> None:
        clear_tree(self.items_tree)

    def get_selected_row_id(self) -> int | None:
        selection = self.items_tree.selection()
        if not selection:
            return None

        values = self.items_tree.item(selection[0], "values")
        if not values:
            return None

        try:
            return int(values[0])
        except (TypeError, ValueError):
            return None

    def item_count(self) -> int:
        return len(self.items_tree.get_children())