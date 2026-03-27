from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class RollExportResultDialog(tk.Toplevel):
    """
    Dialog simples para exibir o resultado da exportação do rolo.

    Espera um dict com pelo menos:
    - roll_name
    - pdf_path
    - jpg_path
    """

    def __init__(self, master: tk.Misc, *, result: dict) -> None:
        super().__init__(master)

        self.result = result

        self.title("Exportação concluída")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.columnconfigure(0, weight=1)

        self._build_ui()
        self._center(master)

        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", lambda event: self.destroy())

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)

        ttk.Label(
            root,
            text="Exportação concluída",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            root,
            text="Os arquivos do rolo foram gerados com sucesso.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        info = ttk.LabelFrame(root, text="Resumo", padding=10)
        info.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        info.columnconfigure(1, weight=1)

        self._info_row(info, 0, "Rolo", str(self.result.get("roll_name", "-")))
        self._info_row(info, 1, "PDF", str(self.result.get("pdf_path", "-")))
        self._info_row(info, 2, "JPG", str(self.result.get("jpg_path", "-")))

        actions = ttk.Frame(root)
        actions.grid(row=3, column=0, sticky="e")

        ttk.Button(actions, text="Abrir pasta", command=self._show_folder_hint).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Fechar", command=self.destroy).pack(side="left")

    def _info_row(self, master: tk.Misc, row: int, label: str, value: str) -> None:
        ttk.Label(master, text=f"{label}:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=3)
        ttk.Label(master, text=value, wraplength=520, justify="left").grid(
            row=row,
            column=1,
            sticky="w",
            pady=3,
        )

    def _show_folder_hint(self) -> None:
        pdf_path = self.result.get("pdf_path")
        jpg_path = self.result.get("jpg_path")

        folder = None
        if pdf_path:
            folder = Path(str(pdf_path)).parent
        elif jpg_path:
            folder = Path(str(jpg_path)).parent

        if folder is None:
            messagebox.showinfo(
                "Exportação concluída",
                "Não foi possível identificar a pasta de saída.",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Pasta de saída",
            f"Arquivos exportados em:\n{folder}",
            parent=self,
        )

    def _center(self, master: tk.Misc) -> None:
        self.update_idletasks()

        if isinstance(master, (tk.Tk, tk.Toplevel)):
            root_x = master.winfo_rootx()
            root_y = master.winfo_rooty()
            root_w = master.winfo_width() or 1200
            root_h = master.winfo_height() or 800
        else:
            root_x, root_y, root_w, root_h = 100, 100, 1200, 800

        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        x = root_x + max((root_w - width) // 2, 0)
        y = root_y + max((root_h - height) // 2, 0)

        self.geometry(f"+{x}+{y}")