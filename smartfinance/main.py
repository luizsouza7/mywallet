"""
MyWallet - Controle Financeiro Pessoal
Ponto de entrada da aplicação.
"""

import customtkinter as ctk
from database import inicializar_banco
from login import TelaLogin
from dashboard import TelaDashboard
from transactions import TelaTransacoes
from charts import TelaGraficos
from reports import exportar_csv


class AplicacaoPrincipal(ctk.CTk):
    """Janela principal com sidebar e navegação entre telas."""

    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.tela_atual = None
        self.voltar_login = False

        self.title("MyWallet - Controle Financeiro")
        self.geometry("1000x650")
        self.minsize(900, 600)

        self.protocol("WM_DELETE_WINDOW", self._fechar_janela)

        self._criar_layout()
        # Atualiza dashboard após a janela estar totalmente carregada
        self.after(100, lambda: self._mostrar_tela("dashboard"))

    def _fechar_janela(self):
        """Fecha o app ao clicar no X da janela."""
        self.voltar_login = False
        self.destroy()

    def _criar_layout(self):
        """Cria sidebar e área de conteúdo."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="💰 MyWallet",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(25, 5))

        ctk.CTkLabel(
            self.sidebar,
            text=self.usuario["nome"][:20],
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).grid(row=1, column=0, padx=20, pady=(0, 25))

        self.btn_dashboard = self._criar_botao_menu("📊  Dashboard", "dashboard", 2)
        self.btn_transacoes = self._criar_botao_menu("💸  Movimentações", "transacoes", 3)
        self.btn_graficos = self._criar_botao_menu("📈  Gráficos", "graficos", 4)
        self.btn_exportar = self._criar_botao_menu("📄  Exportar CSV", "exportar", 5)

        ctk.CTkButton(
            self.sidebar,
            text="🚪  Sair",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self._sair,
        ).grid(row=8, column=0, padx=20, pady=20, sticky="ew")

        # ── Área de conteúdo ──
        self.area_conteudo = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.area_conteudo.grid(row=0, column=1, sticky="nsew")
        self.area_conteudo.grid_columnconfigure(0, weight=1)
        self.area_conteudo.grid_rowconfigure(0, weight=1)

        self.telas = {
            "dashboard": TelaDashboard(self.area_conteudo, self.usuario),
            "transacoes": TelaTransacoes(
                self.area_conteudo, self.usuario, ao_atualizar=self._atualizar_tudo
            ),
            "graficos": TelaGraficos(self.area_conteudo, self.usuario),
        }

        for tela in self.telas.values():
            tela.grid(row=0, column=0, sticky="nsew")

    def _criar_botao_menu(self, texto, destino, linha):
        """Cria botão na sidebar."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=texto,
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=lambda: self._navegar(destino),
        )
        btn.grid(row=linha, column=0, padx=15, pady=4, sticky="ew")
        return btn

    def _navegar(self, destino):
        """Navega para tela ou executa ação."""
        if destino == "exportar":
            exportar_csv(self.usuario["id"], self.usuario["nome"].replace(" ", "_"))
            return
        self._mostrar_tela(destino)

    def _mostrar_tela(self, nome):
        """Exibe a tela selecionada e atualiza dados."""
        if nome not in self.telas:
            return

        if not self.winfo_exists():
            return

        self.telas[nome].tkraise()
        self.tela_atual = nome

        if nome == "dashboard":
            self.telas["dashboard"].atualizar()
        elif nome == "transacoes":
            self.telas["transacoes"].atualizar()
        elif nome == "graficos":
            self.telas["graficos"].atualizar()

        self._destacar_botao_ativo(nome)

    def _destacar_botao_ativo(self, nome):
        """Destaca visualmente o botão da tela atual."""
        botoes = {
            "dashboard": self.btn_dashboard,
            "transacoes": self.btn_transacoes,
            "graficos": self.btn_graficos,
        }
        for chave, btn in botoes.items():
            if chave == nome:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def _atualizar_tudo(self):
        """Atualiza dashboard quando transações mudam."""
        if "dashboard" in self.telas:
            self.telas["dashboard"].atualizar()

    def _sair(self):
        """Volta para a tela de login."""
        self.voltar_login = True
        self.destroy()


def executar_app():
    """Controla o fluxo login → app principal → login."""
    while True:
        login = TelaLogin()
        login.mainloop()

        usuario = login.usuario_logado
        login.destroy()

        if usuario is None:
            break

        app = AplicacaoPrincipal(usuario)
        app.mainloop()

        if not app.voltar_login:
            break


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    inicializar_banco()
    executar_app()
