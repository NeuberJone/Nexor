from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


# Permite rodar tanto por:
#   python -m ui.app
# quanto por:
#   python ui/app.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from application.operations_panel_service import OperationsPanelService
from ui.main_window import MainWindow


APP_TITLE = "Nexor"


class NexorApp:
    """
    Bootstrap principal da aplicação Nexor.
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.service = OperationsPanelService()
        self.main_window: MainWindow | None = None

        self._configure_root()
        self._build_ui()
        self._bind_shortcuts()

    def _configure_root(self) -> None:
        self.root.title(APP_TITLE)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.main_window = MainWindow(self.root, service=self.service)
        self.main_window.grid(row=0, column=0, sticky="nsew")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<F5>", self._refresh_current_page)
        self.root.bind("<Control-r>", self._refresh_current_page)
        self.root.bind("<Control-R>", self._refresh_current_page)

        self.root.bind("<Control-1>", lambda event: self._show_page("home"))
        self.root.bind("<Control-2>", lambda event: self._show_page("operations"))
        self.root.bind("<Control-3>", lambda event: self._show_page("rolls"))

    def _refresh_current_page(self, event: tk.Event | None = None) -> None:
        if self.main_window is not None:
            self.main_window.refresh_current_page()

    def _show_page(self, key: str) -> None:
        if self.main_window is not None:
            self.main_window.show_page(key)

    def _on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        app = NexorApp()
        app.run()
        return 0
    except Exception as exc:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Nexor",
                "Falha ao iniciar a aplicação.\n\n"
                f"Motivo: {exc}",
                parent=root,
            )
            root.destroy()
        except Exception:
            print("Falha ao iniciar a aplicação:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())