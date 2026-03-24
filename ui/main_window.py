from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from application.operations_panel_service import OperationsPanelService
from ui.home_panel import HomePanel
from ui.operations_panel import OperationsPanel
from ui.rolls_panel import RollsPanel


APP_TITLE = "Nexor"
DEFAULT_WINDOW_SIZE = "1540x900"
MIN_WIDTH = 1360
MIN_HEIGHT = 780
SIDEBAR_WIDTH = 220


class MainWindow(ttk.Frame):
    """
    Janela principal do Nexor.

    Responsabilidades:
    - manter um shell único da aplicação
    - oferecer navegação lateral consistente
    - trocar a área central entre páginas
    - compartilhar uma única instância de service
    """

    def __init__(self, master: tk.Misc, service: OperationsPanelService | None = None) -> None:
        super().__init__(master)
        self.master = master
        self.service = service or OperationsPanelService()

        self.current_page_key: str | None = None
        self.pages: dict[str, ttk.Frame] = {}

        self.page_title_var = tk.StringVar(value="Home")
        self.page_subtitle_var = tk.StringVar(value="Visão geral do estado operacional.")
        self.status_var = tk.StringVar(value="Pronto.")

        self.nav_buttons: dict[str, ttk.Button] = {}

        self._configure_styles()
        self._configure_root()
        self._build_ui()
        self.show_page("home")

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Sidebar.TFrame", padding=0)
        style.configure("SidebarTitle.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("ShellTitle.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("ShellSubtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Nav.TButton", anchor="w", padding=(10, 8))
        style.configure("NavActive.TButton", anchor="w", padding=(10, 8))
        style.map(
            "NavActive.TButton",
            relief=[("!disabled", "solid")],
        )

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
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(12, 12, 10, 12))
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.configure(width=SIDEBAR_WIDTH)
        sidebar.grid_propagate(False)

        ttk.Label(sidebar, text="Nexor", style="SidebarTitle.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(sidebar, text="Operação local-first").pack(anchor="w", pady=(0, 16))

        nav = ttk.LabelFrame(sidebar, text="Navegação", padding=8)
        nav.pack(fill="x", pady=(0, 12))

        self.nav_buttons["home"] = ttk.Button(
            nav,
            text="Home",
            style="Nav.TButton",
            command=lambda: self.show_page("home"),
        )
        self.nav_buttons["home"].pack(fill="x", pady=2)

        self.nav_buttons["operations"] = ttk.Button(
            nav,
            text="Operação",
            style="Nav.TButton",
            command=lambda: self.show_page("operations"),
        )
        self.nav_buttons["operations"].pack(fill="x", pady=2)

        self.nav_buttons["rolls"] = ttk.Button(
            nav,
            text="Rolos",
            style="Nav.TButton",
            command=lambda: self.show_page("rolls"),
        )
        self.nav_buttons["rolls"].pack(fill="x", pady=2)

        ttk.Button(nav, text="Planejamento", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Estoque", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Cadastros", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="Configurações", state="disabled", style="Nav.TButton").pack(fill="x", pady=2)

        quick = ttk.LabelFrame(sidebar, text="Ações rápidas", padding=8)
        quick.pack(fill="x", pady=(0, 12))

        ttk.Button(quick, text="Ir para Home", command=lambda: self.show_page("home")).pack(fill="x", pady=2)
        ttk.Button(quick, text="Ir para Operação", command=lambda: self.show_page("operations")).pack(fill="x", pady=2)
        ttk.Button(quick, text="Ir para Rolos", command=lambda: self.show_page("rolls")).pack(fill="x", pady=2)
        ttk.Button(quick, text="Atualizar página", command=self.refresh_current_page).pack(fill="x", pady=2)

        status_box = ttk.LabelFrame(sidebar, text="Estado", padding=8)
        status_box.pack(fill="both", expand=True)
        ttk.Label(status_box, textvariable=self.status_var, wraplength=180, justify="left").pack(anchor="w")

    def _build_shell(self) -> None:
        shell = ttk.Frame(self)
        shell.grid(row=0, column=1, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        self._build_topbar(shell)
        self._build_content_area(shell)
        self._build_footer(shell)

    def _build_topbar(self, master: tk.Misc) -> None:
        topbar = ttk.Frame(master, padding=(12, 12, 12, 8))
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.columnconfigure(0, weight=1)

        text_box = ttk.Frame(topbar)
        text_box.grid(row=0, column=0, sticky="w")

        ttk.Label(text_box, textvariable=self.page_title_var, style="ShellTitle.TLabel").pack(anchor="w")
        ttk.Label(text_box, textvariable=self.page_subtitle_var, style="ShellSubtitle.TLabel").pack(
            anchor="w", pady=(2, 0)
        )

        actions = ttk.Frame(topbar)
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(actions, text="Atualizar página", command=self.refresh_current_page).pack(side="right")

    def _build_content_area(self, master: tk.Misc) -> None:
        self.content = ttk.Frame(master, padding=(12, 0, 12, 8))
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def _build_footer(self, master: tk.Misc) -> None:
        footer = ttk.Frame(master, padding=(12, 0, 12, 10))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        ttk.Separator(footer, orient="horizontal").grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(footer, textvariable=self.status_var).grid(row=1, column=0, sticky="w")

    def _create_page(self, key: str) -> ttk.Frame:
        if key == "home":
            return HomePanel(self.content, service=self.service, on_navigate=self.show_page)
        if key == "operations":
            return OperationsPanel(self.content, service=self.service)
        if key == "rolls":
            return RollsPanel(self.content, service=self.service)
        raise ValueError(f"Página desconhecida: {key}")

    def show_page(self, key: str) -> None:
        if key not in self.pages:
            self.pages[key] = self._create_page(key)

        for page_key, page in self.pages.items():
            if page_key == key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_forget()

        self.current_page_key = key
        self._apply_page_metadata(key)
        self._refresh_nav_state()
        self.refresh_current_page()

    def refresh_current_page(self) -> None:
        if self.current_page_key is None:
            return

        page = self.pages.get(self.current_page_key)
        if page is None:
            return

        refresh_method = getattr(page, "refresh_all", None)
        if callable(refresh_method):
            refresh_method()

        if self.current_page_key == "home":
            self.status_var.set("Página atual: Home")
        elif self.current_page_key == "operations":
            self.status_var.set("Página atual: Operação")
        elif self.current_page_key == "rolls":
            self.status_var.set("Página atual: Rolos")

    def _apply_page_metadata(self, key: str) -> None:
        if key == "home":
            self.page_title_var.set("Home")
            self.page_subtitle_var.set("Visão geral do estado operacional.")
        elif key == "operations":
            self.page_title_var.set("Operação")
            self.page_subtitle_var.set("Montagem operacional de rolos.")
        elif key == "rolls":
            self.page_title_var.set("Rolos")
            self.page_subtitle_var.set("Consulta operacional e inspeção de rolos.")
        else:
            self.page_title_var.set("Nexor")
            self.page_subtitle_var.set("")

    def _refresh_nav_state(self) -> None:
        for key, button in self.nav_buttons.items():
            style = "NavActive.TButton" if key == self.current_page_key else "Nav.TButton"
            button.configure(style=style)

    def run(self) -> None:
        if isinstance(self.master, tk.Tk):
            self.master.mainloop()


def run_main_window(service: OperationsPanelService | None = None) -> None:
    root = tk.Tk()
    MainWindow(root, service=service)
    root.mainloop()


def main() -> None:
    run_main_window()


if __name__ == "__main__":
    main()