# Arquivo: ui/table_list_panel.py
#
# Resumo do que este arquivo implementa:
# - mantém o painel reutilizável de listas com Treeview
# - adiciona título auxiliar opcional no topo
# - expõe métodos utilitários para limpar/contar/inserir linhas
# - centraliza melhor a estrutura usada por Operação e Rolos

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.common_widgets import apply_common_styles, clear_tree, configure_tree_columns


class TableListPanel(ttk.LabelFrame):
    """
    Painel reutilizável para listas com Treeview.

    Estrutura:
    - título do painel
    - topo com contador
    - tabela com scroll vertical/horizontal
    - ações inferiores opcionais
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        panel_title: str,
        count_label: str,
        count_var: tk.StringVar,
        tree_columns: dict[str, tuple[str, int]],
        left_aligned_columns: set[str] | None = None,
        footer_actions: list[tuple[str, object]] | None = None,
        helper_text: str | None = None,
    ) -> None:
        super().__init__(master, text=panel_title, style="Section.TLabelframe", padding=8)

        apply_common_styles()

        self.count_label = count_label
        self.count_var = count_var
        self.tree_columns = tree_columns
        self.left_aligned_columns = left_aligned_columns or set()
        self.footer_actions = footer_actions or []
        self.helper_text = helper_text

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.tree: ttk.Treeview

        self._build_ui()

    def _build_ui(self) -> None:
        self._build_top()
        self._build_tree()
        self._build_footer()

    def _build_top(self) -> None:
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(1, weight=1)

        counter = ttk.Frame(top)
        counter.grid(row=0, column=0, sticky="w")

        ttk.Label(counter, text=self.count_label).pack(side="left")
        ttk.Label(counter, textvariable=self.count_var, style="MetricValue.TLabel").pack(
            side="left",
            padx=(6, 0),
        )

        if self.helper_text:
            ttk.Label(
                top,
                text=self.helper_text,
                style="Muted.TLabel",
            ).grid(row=0, column=1, sticky="e")

    def _build_tree(self) -> None:
        tree_wrap = ttk.Frame(self)
        tree_wrap.grid(row=1, column=0, sticky="nsew")
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_wrap,
            columns=tuple(self.tree_columns.keys()),
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")

        sb_x = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        configure_tree_columns(
            self.tree,
            self.tree_columns,
            left_aligned=self.left_aligned_columns,
        )

    def _build_footer(self) -> None:
        if not self.footer_actions:
            return

        footer = ttk.Frame(self)
        footer.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        for index, (text, command) in enumerate(self.footer_actions):
            padx = (8, 0) if index > 0 else (0, 0)
            ttk.Button(footer, text=text, command=command).pack(side="left", padx=padx)

    def clear_rows(self) -> None:
        clear_tree(self.tree)

    def set_count(self, value: int) -> None:
        self.count_var.set(str(int(value)))

    def insert_row(self, values: tuple | list) -> str:
        return str(self.tree.insert("", "end", values=tuple(values)))

    def set_rows(self, rows: list[tuple | list]) -> None:
        self.clear_rows()
        for row in rows:
            self.insert_row(tuple(row))
        self.set_count(len(rows))