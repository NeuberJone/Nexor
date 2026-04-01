# ui/app.py
from __future__ import annotations

import argparse
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

from application.log_sources_service import LogSourcesService
from application.operations_panel_service import OperationsPanelService
from storage.database import init_database, resolve_default_db_path
from storage.repository import ProductionRepository
from ui.main_window import MainWindow


APP_TITLE = "Nexor"
DEFAULT_START_PAGE = "home"
VALID_START_PAGES = ("home", "operations", "rolls", "log_sources")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nexor desktop UI")
    parser.add_argument(
        "--db-path",
        default=None,
        help="Caminho opcional para o banco SQLite local.",
    )
    parser.add_argument(
        "--page",
        choices=VALID_START_PAGES,
        default=DEFAULT_START_PAGE,
        help="Página inicial da interface.",
    )
    return parser.parse_args(argv)


def build_services(
    db_path: str | Path | None = None,
) -> tuple[OperationsPanelService, LogSourcesService, Path]:
    target_db = init_database(db_path=db_path)

    production_repository = ProductionRepository(db_path=target_db)
    operations_service = OperationsPanelService(repository=production_repository)
    log_sources_service = LogSourcesService(db_path=target_db)

    return operations_service, log_sources_service, Path(target_db)


def show_startup_error(exc: Exception) -> None:
    message = (
        "Falha ao iniciar a interface do Nexor.\n\n"
        f"Motivo: {exc}"
    )

    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_TITLE, message, parent=root)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


class NexorApp:
    """
    Bootstrap dedicado da interface desktop do Nexor.

    Objetivos:
    - garantir init_database ao abrir a UI diretamente
    - montar MainWindow com serviços compartilhando o mesmo banco
    - manter navegação inicial por página
    """

    def __init__(
        self,
        *,
        db_path: str | Path | None = None,
        start_page: str = DEFAULT_START_PAGE,
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else resolve_default_db_path()
        self.start_page = start_page if start_page in VALID_START_PAGES else DEFAULT_START_PAGE

        self.root = tk.Tk()
        (
            self.operations_service,
            self.log_sources_service,
            self.initialized_db_path,
        ) = build_services(self.db_path)

        self.main_window: MainWindow | None = None

        self._configure_root()
        self._build_ui()
        self._bind_shortcuts()
        self._open_start_page()

    def _configure_root(self) -> None:
        self.root.title(APP_TITLE)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.main_window = MainWindow(
            self.root,
            service=self.operations_service,
            log_sources_service=self.log_sources_service,
        )

    def _bind_shortcuts(self) -> None:
        self.root.bind("<F5>", self._refresh_current_page)
        self.root.bind("<Control-r>", self._refresh_current_page)
        self.root.bind("<Control-R>", self._refresh_current_page)

        self.root.bind("<Control-1>", lambda event: self._show_page("home"))
        self.root.bind("<Control-2>", lambda event: self._show_page("operations"))
        self.root.bind("<Control-3>", lambda event: self._show_page("rolls"))
        self.root.bind("<Control-4>", lambda event: self._show_page("log_sources"))

        self.root.bind("<F1>", self._show_shortcuts_help)

    def _open_start_page(self) -> None:
        if self.main_window is not None:
            self.main_window.show_page(self.start_page)

    def _refresh_current_page(self, event: tk.Event | None = None) -> None:
        if self.main_window is not None:
            self.main_window.refresh_current_page()

    def _show_page(self, key: str) -> None:
        if self.main_window is not None:
            self.main_window.show_page(key)

    def _show_shortcuts_help(self, event: tk.Event | None = None) -> None:
        text = (
            "Atalhos disponíveis:\n\n"
            "F5 / Ctrl+R  → Atualizar página atual\n"
            "Ctrl+1       → Home\n"
            "Ctrl+2       → Operação\n"
            "Ctrl+3       → Rolos\n"
            "Ctrl+4       → Fontes de logs\n"
            "F1           → Mostrar esta ajuda"
        )
        messagebox.showinfo(APP_TITLE, text, parent=self.root)

    def _on_close(self) -> None:
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        app = NexorApp(
            db_path=args.db_path,
            start_page=args.page,
        )
        app.run()
        return 0
    except Exception as exc:
        show_startup_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())