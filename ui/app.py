from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


# Suporte temporário para rodar tanto por:
#   python -m ui.app
# quanto por:
#   python ui/app.py
#
# No futuro, o ideal é manter somente execução por pacote.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from application.operations_panel_service import OperationsPanelService
from ui.operations_panel import OperationsPanel


APP_TITLE = "Nexor - Operação"
APP_MIN_WIDTH = 1360
APP_MIN_HEIGHT = 780
APP_DEFAULT_WIDTH = 1540
APP_DEFAULT_HEIGHT = 900


class NexorOperationsApp:
    """
    Bootstrap oficial da interface operacional local do Nexor.

    Responsabilidades:
    - subir a janela principal
    - carregar a tela de operação
    - centralizar atalhos globais simples
    - manter a entrada da UI separada da tela em si
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.service = OperationsPanelService()
        self.panel: OperationsPanel | None = None

        self._configure_root()
        self._build_ui()
        self._bind_shortcuts()

    def _configure_root(self) -> None:
        self.root.title(APP_TITLE)
        self.root.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        self.root.geometry(self._get_initial_geometry())
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.panel = OperationsPanel(self.root, service=self.service)
        self.panel.grid(row=0, column=0, sticky="nsew")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<F5>", self._refresh_all)
        self.root.bind("<Control-r>", self._refresh_all)
        self.root.bind("<Control-R>", self._refresh_all)

        self.root.bind("<Control-n>", self._create_roll)
        self.root.bind("<Control-N>", self._create_roll)

        self.root.bind("<Escape>", self._escape_action)

    def _refresh_all(self, event: tk.Event | None = None) -> None:
        if self.panel is not None:
            self.panel.refresh_all()

    def _create_roll(self, event: tk.Event | None = None) -> None:
        if self.panel is not None:
            self.panel.create_roll()

    def _escape_action(self, event: tk.Event | None = None) -> None:
        """
        Mantido simples no MVP.
        Evita encerrar a aplicação por acidente.
        """
        return

    def _on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    def _get_initial_geometry(self) -> str:
        self.root.update_idletasks()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        width = min(APP_DEFAULT_WIDTH, max(APP_MIN_WIDTH, screen_w - 120))
        height = min(APP_DEFAULT_HEIGHT, max(APP_MIN_HEIGHT, screen_h - 120))

        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)

        return f"{width}x{height}+{x}+{y}"


def main() -> int:
    try:
        app = NexorOperationsApp()
        app.run()
        return 0
    except Exception as exc:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Nexor",
                "Falha ao iniciar a interface operacional.\n\n"
                f"Motivo: {exc}",
                parent=root,
            )
            root.destroy()
        except Exception:
            print("Falha ao iniciar a interface operacional:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())