# ui/main_window.py
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from application.log_sources_service import LogSourcesService
from application.operations_panel_service import OperationsPanelService
from ui.home_panel import HomePanel
from ui.log_sources_panel import LogSourcesPanel
from ui.operations_panel import OperationsPanel
from ui.rolls_panel import RollsPanel


APP_TITLE = "Nexor"
DEFAULT_WINDOW_SIZE = "1540x900"
MIN_WIDTH = 1280
MIN_HEIGHT = 760
SIDEBAR_WIDTH = 130


@dataclass(frozen=True)
class PageMeta:
    title: str
    subtitle: str
    nav_label: str


PAGE_META: dict[str, PageMeta] = {
    "home": PageMeta(
        title="Home",
        subtitle="Visão geral do estado operacional.",
        nav_label="Home",
    ),
    "operations": PageMeta(
        title="Operação",
        subtitle="Fluxo operacional para teste do núcleo.",
        nav_label="Operação",
    ),
    "rolls": PageMeta(
        title="Rolos",
        subtitle="Consulta simples dos rolos para validação funcional.",
        nav_label="Rolos",
    ),
    "log_sources": PageMeta(
        title="Fontes de logs",
        subtitle="Cadastro e controle das origens locais de importação.",
        nav_label="Fontes",
    ),
}


class MainWindow(ttk.Frame):
    """
    Shell principal do Nexor.

    Diretriz atual:
    - priorizar previsibilidade e isolamento entre telas
    - não manter páginas antigas vivas quando trocar de seção
    - simplificar a navegação para facilitar teste funcional
    """

    def __init__(
        self,
        master: tk.Misc,
        service: OperationsPanelService | None = None,
        log_sources_service: LogSourcesService | None = None,
    ) -> None:
        super().__init__(master)

        self.master = master
        self.service = service or OperationsPanelService()
        self.log_sources_service = log_sources_service or LogSourcesService()

        self.current_page_key: str | None = None
        self.current_page_widget: ttk.Frame | None = None

        self.page_title_var = tk.StringVar(value=PAGE_META["home"].title)
        self.page_subtitle_var = tk.StringVar(value=PAGE_META["home"].subtitle)
        self.status_var = tk.StringVar(value="Pronto.")

        self.nav_buttons: dict[str, ttk.Button] = {}

        self._configure_styles()
        self._configure_root()
        self._build_ui()
        self.show_page("home")

    # ------------------------------------------------------------------
    # Shell setup
    # ------------------------------------------------------------------

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Sidebar.TFrame", padding=0)
        style.configure("SidebarTitle.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("SidebarSub.TLabel", font=("Segoe UI", 9))
        style.configure("ShellTitle.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("ShellSubtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Nav.TButton", anchor="center", padding=(10, 8))
        style.configure("NavActive.TButton", anchor="center", padding=(10, 8))
        style.map("NavActive.TButton", relief=[("!disabled", "solid")])

    def _configure_root(self) -> None:
        if isinstance(self.master, tk.Tk):
            self.master.title(APP_TITLE)
            self.master.geometry(DEFAULT_WINDOW_SIZE)
            self.master.minsize(MIN_WIDTH, MIN_HEIGHT)
            self.master.columnconfigure(0, weight=1)
            self.master.rowconfigure(0, weight=1)

    def _build_ui(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_shell()

    def _build_sidebar(self) -> None:
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(8, 12, 8, 12))
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.configure(width=SIDEBAR_WIDTH)
        sidebar.grid_propagate(False)

        brand = ttk.Frame(sidebar)
        brand.pack(fill="x", pady=(0, 16))
        ttk.Label(brand, text="Nexor", style="SidebarTitle.TLabel").pack(anchor="w")
        ttk.Label(
            brand,
            text="Operação local-first",
            style="SidebarSub.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        nav = ttk.LabelFrame(sidebar, text="Navegação", padding=8)
        nav.pack(fill="x")

        self._add_nav_button(nav, "home")
        self._add_nav_button(nav, "operations")
        self._add_nav_button(nav, "rolls")
        self._add_nav_button(nav, "log_sources")

        ttk.Button(nav, text="Planejamento", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Estoque", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Cadastros", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Configurações", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)

    def _add_nav_button(self, master: tk.Misc, key: str) -> None:
        meta = PAGE_META[key]
        button = ttk.Button(
            master,
            text=meta.nav_label,
            style="Nav.TButton",
            command=lambda page_key=key: self.show_page(page_key),
        )
        button.pack(fill="x", pady=2)
        self.nav_buttons[key] = button

    def _build_shell(self) -> None:
        shell = ttk.Frame(self, padding=(12, 12, 12, 10))
        shell.grid(row=0, column=1, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        self._build_topbar(shell)
        self._build_content_area(shell)
        self._build_footer(shell)

    def _build_topbar(self, master: tk.Misc) -> None:
        topbar = ttk.Frame(master)
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        topbar.columnconfigure(0, weight=1)

        text_box = ttk.Frame(topbar)
        text_box.grid(row=0, column=0, sticky="w")

        ttk.Label(
            text_box,
            textvariable=self.page_title_var,
            style="ShellTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            text_box,
            textvariable=self.page_subtitle_var,
            style="ShellSubtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        actions = ttk.Frame(topbar)
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(
            actions,
            text="Atualizar página",
            command=self.refresh_current_page,
        ).pack(side="right")

    def _build_content_area(self, master: tk.Misc) -> None:
        self.content = ttk.Frame(master)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def _build_footer(self, master: tk.Misc) -> None:
        footer = ttk.Frame(master)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)

        ttk.Separator(footer, orient="horizontal").grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(footer, textvariable=self.status_var).grid(row=1, column=0, sticky="w")

    # ------------------------------------------------------------------
    # Page lifecycle
    # ------------------------------------------------------------------

    def _destroy_current_page(self) -> None:
        if self.current_page_widget is None:
            return

        try:
            self.current_page_widget.grid_forget()
            self.current_page_widget.destroy()
        finally:
            self.current_page_widget = None

    def _create_page(self, key: str) -> ttk.Frame:
        if key == "home":
            return HomePanel(
                self.content,
                service=self.service,
                log_sources_service=self.log_sources_service,
                on_navigate=self.show_page,
            )

        if key == "operations":
            return OperationsPanel(
                self.content,
                service=self.service,
            )

        if key == "rolls":
            return RollsPanel(
                self.content,
                service=self.service,
            )

        if key == "log_sources":
            return LogSourcesPanel(
                self.content,
                service=self.log_sources_service,
            )

        raise ValueError(f"Página desconhecida: {key}")

    def show_page(self, key: str) -> None:
        if key not in PAGE_META:
            raise ValueError(f"Página desconhecida: {key}")

        same_page = key == self.current_page_key and self.current_page_widget is not None
        if same_page:
            self.refresh_current_page()
            return

        self._destroy_current_page()

        page = self._create_page(key)
        page.grid(row=0, column=0, sticky="nsew")

        self.current_page_key = key
        self.current_page_widget = page

        self._apply_page_metadata(key)
        self._refresh_nav_state()
        self.refresh_current_page()

    def refresh_current_page(self) -> None:
        if self.current_page_key is None or self.current_page_widget is None:
            return

        refresh_method = getattr(self.current_page_widget, "refresh_all", None)
        if callable(refresh_method):
            refresh_method()

        meta = PAGE_META.get(self.current_page_key)
        if meta is not None:
            self.status_var.set(f"Página atual: {meta.title}")

    # ------------------------------------------------------------------
    # Metadata / state
    # ------------------------------------------------------------------

    def _apply_page_metadata(self, key: str) -> None:
        meta = PAGE_META.get(key)
        if meta is None:
            self.page_title_var.set(APP_TITLE)
            self.page_subtitle_var.set("")
            return

        self.page_title_var.set(meta.title)
        self.page_subtitle_var.set(meta.subtitle)

    def _refresh_nav_state(self) -> None:
        for key, button in self.nav_buttons.items():
            style = "NavActive.TButton" if key == self.current_page_key else "Nav.TButton"
            button.configure(style=style)

    # ------------------------------------------------------------------
    # Entrypoints
    # ------------------------------------------------------------------

    def run(self) -> None:
        if isinstance(self.master, tk.Tk):
            self.master.mainloop()


def run_main_window(
    service: OperationsPanelService | None = None,
    log_sources_service: LogSourcesService | None = None,
) -> None:
    root = tk.Tk()
    MainWindow(root, service=service, log_sources_service=log_sources_service)
    root.mainloop()


def main() -> None:
    run_main_window()


if __name__ == "__main__":
    main()