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
from reports import exportar_csv, gerar_relatorio_pdf
from theme import (
    COR_ATIVO,
    COR_BORDA,
    COR_HOVER,
    COR_SIDEBAR,
    COR_TEXTO,
    COR_TEXTO_SEC,
)


def _destruir_janela(janela):
    """Destrói janela CustomTkinter sem conflito com timers internos."""
    try:
        janela.withdraw()
        janela.update_idletasks()
    except Exception:
        pass
    try:
        janela.destroy()
    except Exception:
        pass


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
        self.after(100, lambda: self._mostrar_tela("dashboard"))

    def _fechar_janela(self):
        """Fecha o app ao clicar no X da janela."""
        self.voltar_login = False
        self.destroy()

    def _criar_layout(self):
        """Cria sidebar e área de conteúdo."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="MyWallet",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COR_TEXTO,
        ).grid(row=0, column=0, padx=22, pady=(28, 2), sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text=self.usuario["nome"][:22],
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
        ).grid(row=1, column=0, padx=22, pady=(0, 16), sticky="w")

        separador = ctk.CTkFrame(self.sidebar, height=1, fg_color=COR_BORDA)
        separador.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")

        self.btn_dashboard = self._criar_botao_menu("Dashboard", "dashboard", 3)
        self.btn_transacoes = self._criar_botao_menu("Movimentações", "transacoes", 4)
        self.btn_graficos = self._criar_botao_menu("Gráficos", "graficos", 5)

        ctk.CTkLabel(
            self.sidebar,
            text="EXPORTAR",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COR_TEXTO_SEC,
        ).grid(row=6, column=0, padx=22, pady=(14, 4), sticky="w")

        self.btn_exportar = self._criar_botao_menu("Exportar CSV", "exportar", 7)
        self.btn_pdf = self._criar_botao_menu("Exportar PDF", "pdf", 8)

        ctk.CTkButton(
            self.sidebar,
            text="Sair",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=COR_BORDA,
            text_color=COR_TEXTO_SEC,
            hover_color=COR_HOVER,
            font=ctk.CTkFont(size=13),
            command=self._sair,
        ).grid(row=10, column=0, padx=18, pady=(0, 22), sticky="ew")

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
        """Cria botão na sidebar com estilo discreto."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=texto,
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color=COR_TEXTO_SEC,
            hover_color=COR_HOVER,
            font=ctk.CTkFont(size=13),
            command=lambda: self._navegar(destino),
        )
        btn.grid(row=linha, column=0, padx=14, pady=2, sticky="ew")
        return btn

    def _navegar(self, destino):
        """Navega para tela ou executa ação."""
        if destino == "exportar":
            exportar_csv(self.usuario["id"], self.usuario["nome"].replace(" ", "_"))
            return
        if destino == "pdf":
            gerar_relatorio_pdf(self.usuario)
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
                btn.configure(fg_color=COR_ATIVO, text_color=COR_TEXTO)
            else:
                btn.configure(fg_color="transparent", text_color=COR_TEXTO_SEC)

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

        if usuario is None:
            _destruir_janela(login)
            break

        app = AplicacaoPrincipal(usuario)
        app.mainloop()

        _destruir_janela(login)

        if not app.voltar_login:
            break


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    inicializar_banco()
    executar_app()
