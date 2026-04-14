# ui/roll_export_result_dialog.py
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ui.common_widgets import apply_common_styles


class RollExportResultDialog(tk.Toplevel):
    """
    Diálogo simples para exibir o resultado de uma exportação de rolo.

    Regras:
    - aceitar resultado em dict ou objeto/dataclass
    - mostrar caminhos principais de forma tolerante
    - facilitar teste manual com abrir pasta / copiar caminho
    """

    def __init__(self, master: tk.Misc, *, result: object) -> None:
        super().__init__(master)

        self.result = result
        self.title("Resultado da exportação")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.columnconfigure(0, weight=1)

        apply_common_styles()
        self._build_ui()
        self._center(master)

        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", lambda event: self.destroy())

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)

        self._build_header(root)
        self._build_summary(root)
        self._build_paths(root)
        self._build_actions(root)

    def _build_header(self, master: tk.Misc) -> None:
        box = ttk.Frame(master)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)

        ttk.Label(
            box,
            text="Exportação concluída",
            style="PanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            box,
            text=self._build_status_message(),
            wraplength=680,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_summary(self, master: tk.Misc) -> None:
        info = ttk.LabelFrame(master, text="Resumo", padding=10)
        info.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        info.columnconfigure(1, weight=1)

        self._info_row(info, 0, "Rolo", self._get_first_value("roll_name", "roll_code", "name", default="-"))
        self._info_row(info, 1, "ID", self._to_text(self._get_first_value("roll_id", "id", default="-")))
        self._info_row(info, 2, "Status", self._get_first_value("status", "export_status", default="OK"))
        self._info_row(info, 3, "Pasta principal", self._resolve_primary_dir_text())
        self._info_row(info, 4, "Arquivos detectados", str(len(self._collect_existing_paths())))

    def _build_paths(self, master: tk.Misc) -> None:
        box = ttk.LabelFrame(master, text="Arquivos gerados", padding=10)
        box.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        box.columnconfigure(0, weight=1)

        paths = self._collect_existing_paths()
        if not paths:
            ttk.Label(
                box,
                text="Nenhum caminho explícito foi encontrado no resultado da exportação.\nIsso não impede a exportação de ter funcionado, mas o service não retornou os arquivos de forma direta.",
                wraplength=680,
                justify="left",
            ).grid(row=0, column=0, sticky="w")
            return

        for idx, path in enumerate(paths):
            row = ttk.Frame(box)
            row.grid(row=idx, column=0, sticky="ew", pady=(0 if idx == 0 else 8, 0))
            row.columnconfigure(1, weight=1)

            kind = self._label_for_path(path)
            ttk.Label(row, text=f"{kind}:").grid(row=0, column=0, sticky="nw", padx=(0, 8))
            ttk.Label(
                row,
                text=str(path),
                wraplength=560,
                justify="left",
            ).grid(row=0, column=1, sticky="w")

            buttons = ttk.Frame(row)
            buttons.grid(row=0, column=2, sticky="ne", padx=(8, 0))
            ttk.Button(
                buttons,
                text="Copiar",
                command=lambda p=path: self._copy_text(str(p)),
            ).pack(side="top", anchor="e")
            ttk.Button(
                buttons,
                text="Abrir",
                command=lambda p=path: self._open_path(p),
            ).pack(side="top", anchor="e", pady=(6, 0))

    def _build_actions(self, master: tk.Misc) -> None:
        actions = ttk.Frame(master)
        actions.grid(row=3, column=0, sticky="e")

        primary_dir = self._resolve_primary_dir()
        if primary_dir is not None:
            ttk.Button(
                actions,
                text="Abrir pasta",
                command=lambda: self._open_path(primary_dir),
            ).pack(side="right", padx=(8, 0))

        ttk.Button(
            actions,
            text="Fechar",
            command=self.destroy,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Helpers: result access
    # ------------------------------------------------------------------

    def _get_first_value(self, *names: str, default=None):
        for name in names:
            value = self._get_value(name)
            if value not in (None, "", [], (), {}):
                return value
        return default

    def _get_value(self, name: str):
        if isinstance(self.result, dict):
            return self.result.get(name)

        try:
            return getattr(self.result, name)
        except Exception:
            return None

    def _collect_existing_paths(self) -> list[Path]:
        names = [
            "pdf_path",
            "summary_pdf_path",
            "full_pdf_path",
            "mirror_jpg_path",
            "jpg_path",
            "image_path",
            "output_path",
            "export_path",
        ]

        paths: list[Path] = []

        for name in names:
            value = self._get_value(name)
            candidate = self._to_path(value)
            if candidate is not None and candidate not in paths:
                paths.append(candidate)

        files_value = self._get_first_value("files", "generated_files", default=None)
        if isinstance(files_value, (list, tuple)):
            for item in files_value:
                candidate = self._to_path(item)
                if candidate is not None and candidate not in paths:
                    paths.append(candidate)

        return paths

    def _resolve_primary_dir(self) -> Path | None:
        dir_value = self._get_first_value(
            "output_dir",
            "export_dir",
            "directory",
            "folder",
            default=None,
        )
        direct_dir = self._to_path(dir_value)
        if direct_dir is not None:
            return direct_dir

        paths = self._collect_existing_paths()
        if not paths:
            return None
        return paths[0].parent

    def _resolve_primary_dir_text(self) -> str:
        folder = self._resolve_primary_dir()
        if folder is None:
            return "-"
        return str(folder)

    def _build_status_message(self) -> str:
        files = self._collect_existing_paths()
        if files:
            return "Os arquivos principais da exportação foram detectados abaixo. Use este diálogo apenas para conferência rápida e acesso direto aos caminhos."
        return "A exportação retornou sem caminhos explícitos. O fluxo continua válido, mas vale conferir a pasta de saída manualmente."

    # ------------------------------------------------------------------
    # Helpers: formatting
    # ------------------------------------------------------------------

    def _info_row(self, master: tk.Misc, row: int, label: str, value: str) -> None:
        ttk.Label(master, text=f"{label}:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=2)
        ttk.Label(
            master,
            text=value,
            wraplength=560,
            justify="left",
        ).grid(row=row, column=1, sticky="w", pady=2)

    @staticmethod
    def _to_text(value: object) -> str:
        if value is None:
            return "-"
        text = str(value).strip()
        return text or "-"

    @staticmethod
    def _to_path(value: object) -> Path | None:
        if value is None:
            return None
        try:
            text = str(value).strip()
        except Exception:
            return None
        if not text:
            return None
        return Path(text)

    @staticmethod
    def _label_for_path(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "PDF"
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            return "Imagem"
        return "Arquivo"

    # ------------------------------------------------------------------
    # Helpers: actions
    # ------------------------------------------------------------------

    def _copy_text(self, text: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception as exc:
            messagebox.showerror(
                "Resultado da exportação",
                f"Falha ao copiar o caminho.\n\nMotivo: {exc}",
                parent=self,
            )

    def _open_path(self, path: Path) -> None:
        try:
            target = path
            if path.is_file():
                target = path.parent

            if sys.platform.startswith("win"):
                os.startfile(str(target))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
        except Exception as exc:
            messagebox.showerror(
                "Resultado da exportação",
                f"Falha ao abrir o caminho.\n\nMotivo: {exc}",
                parent=self,
            )

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

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