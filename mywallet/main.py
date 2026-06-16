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

from periodo import BarraFiltroPeriodo

from theme import (

    COR_ACENTO,

    COR_ATIVO,

    COR_FUNDO,

    COR_HOVER,

    COR_SIDEBAR,

    COR_TEXTO,

    COR_TEXTO_MUTED,

    COR_TEXTO_SEC,

    ESPACO_SM,

    LARGURA_SIDEBAR,

    RAIO_BOTAO,

)





def _patch_ctk_button_click_animation():

    """Evita 'invalid command name ..._click_animation' ao fechar janelas."""

    _destroy_original = ctk.CTkButton.destroy



    def _clicked_patched(self, event=None):

        import tkinter



        if self._state != tkinter.DISABLED:

            self._on_leave()

            self._click_animation_running = True



            def _animacao_segura(btn=self):

                if btn.winfo_exists():

                    btn._click_animation()



            self._click_animation_job = self.after(100, _animacao_segura)



            if self._command is not None:

                self._command()



    def _destroy_patched(self):

        job = getattr(self, "_click_animation_job", None)

        if job is not None:

            try:

                self.after_cancel(job)

            except Exception:

                pass

            self._click_animation_job = None

        self._click_animation_running = False

        _destroy_original(self)



    ctk.CTkButton._clicked = _clicked_patched

    ctk.CTkButton.destroy = _destroy_patched





def _cancelar_animacoes_botoes(janela):

    """Cancela timers de animação de clique antes de destruir a janela."""

    try:

        for widget in janela.winfo_children():

            _cancelar_animacoes_botoes(widget)

    except Exception:

        pass



    if isinstance(janela, ctk.CTkButton):

        job = getattr(janela, "_click_animation_job", None)

        if job is not None:

            try:

                janela.after_cancel(job)

            except Exception:

                pass

            janela._click_animation_job = None

        janela._click_animation_running = False





def _cancelar_timers_tk(janela):

    """Cancela callbacks agendados pelo Tk/CustomTkinter antes do destroy."""

    try:

        timers = janela.tk.call("after", "info")

    except Exception:

        return

    for timer in timers:

        try:

            janela.after_cancel(timer)

        except Exception:

            pass



def _destruir_janela(janela):

    """Destrói janela CustomTkinter sem conflito com timers internos."""

    try:

        _cancelar_animacoes_botoes(janela)

        _cancelar_timers_tk(janela)

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



    _MENU_ITENS = [

        ("dashboard", "🏠", "Dashboard"),

        ("transacoes", "💳", "Movimentações"),

        ("graficos", "📊", "Gráficos"),

    ]



    _EXPORT_ITENS = [

        ("exportar", "📄", "Exportar CSV"),

        ("pdf", "📄", "Exportar PDF"),

    ]



    def __init__(self, usuario):

        super().__init__(fg_color=COR_FUNDO)



        self.usuario = usuario

        self.tela_atual = None

        self.voltar_login = False

        self._botoes_nav = {}

        self.periodo = {}



        self.title("MyWallet")

        self.geometry("1180x720")

        self.minsize(1020, 640)



        self.protocol("WM_DELETE_WINDOW", self._fechar_janela)



        self._criar_layout()

        self.periodo = self.barra_periodo.obter()

        self.after(100, lambda: self._mostrar_tela("dashboard"))



    def _fechar_janela(self):

        self.voltar_login = False

        _destruir_janela(self)



    def _obter_periodo(self):

        return self.periodo



    def _criar_layout(self):

        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)



        self._criar_sidebar()



        painel = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)

        painel.grid(row=0, column=1, sticky="nsew")

        painel.grid_columnconfigure(0, weight=1)

        painel.grid_rowconfigure(1, weight=1)



        self.barra_periodo = BarraFiltroPeriodo(painel, ao_mudar=self._ao_mudar_periodo)

        self.barra_periodo.grid(row=0, column=0, sticky="ew")



        self.area_conteudo = ctk.CTkFrame(painel, corner_radius=0, fg_color=COR_FUNDO)

        self.area_conteudo.grid(row=1, column=0, sticky="nsew")

        self.area_conteudo.grid_columnconfigure(0, weight=1)

        self.area_conteudo.grid_rowconfigure(0, weight=1)



        self.telas = {

            "dashboard": TelaDashboard(

                self.area_conteudo, self.usuario, obter_periodo=self._obter_periodo

            ),

            "transacoes": TelaTransacoes(

                self.area_conteudo,

                self.usuario,

                ao_atualizar=self._atualizar_tudo,

                obter_periodo=self._obter_periodo,

            ),

            "graficos": TelaGraficos(

                self.area_conteudo, self.usuario, obter_periodo=self._obter_periodo

            ),

        }



        for tela in self.telas.values():

            tela.grid(row=0, column=0, sticky="nsew")



    def _criar_sidebar(self):

        self.sidebar = ctk.CTkFrame(

            self, width=LARGURA_SIDEBAR, corner_radius=0, fg_color=COR_SIDEBAR, border_width=0

        )

        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.sidebar.grid_propagate(False)

        self.sidebar.grid_columnconfigure(0, weight=1)

        self.sidebar.grid_rowconfigure(10, weight=1)



        pad = ESPACO_SM



        cabecalho = ctk.CTkFrame(self.sidebar, fg_color="transparent")

        cabecalho.grid(row=0, column=0, sticky="ew", padx=pad, pady=(24, 24))



        logo = ctk.CTkFrame(

            cabecalho, width=40, height=40, corner_radius=10, fg_color=COR_ATIVO

        )

        logo.pack(side="left")

        logo.pack_propagate(False)

        ctk.CTkLabel(

            logo, text="₿", font=ctk.CTkFont(size=17, weight="bold"), text_color=COR_ACENTO

        ).place(relx=0.5, rely=0.5, anchor="center")



        titulo_box = ctk.CTkFrame(cabecalho, fg_color="transparent")

        titulo_box.pack(side="left", padx=(10, 0))



        ctk.CTkLabel(

            titulo_box, text="MyWallet", font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_TEXTO

        ).pack(anchor="w")

        ctk.CTkLabel(

            titulo_box, text="Finanças", font=ctk.CTkFont(size=11), text_color=COR_TEXTO_MUTED

        ).pack(anchor="w")



        for i, (destino, icone, rotulo) in enumerate(self._MENU_ITENS):

            btn = self._criar_botao_nav(icone, rotulo, destino, row=1 + i)

            self._botoes_nav[destino] = btn



        ctk.CTkLabel(

            self.sidebar,

            text="RELATÓRIOS",

            font=ctk.CTkFont(size=10, weight="bold"),

            text_color=COR_TEXTO_MUTED,

            anchor="w",

        ).grid(row=5, column=0, sticky="w", padx=pad, pady=(18, 6))



        for i, (destino, icone, rotulo) in enumerate(self._EXPORT_ITENS):

            btn = self._criar_botao_nav(icone, rotulo, destino, row=6 + i, muted=True)

            self._botoes_nav[destino] = btn



        rodape = ctk.CTkFrame(self.sidebar, fg_color="transparent")

        rodape.grid(row=11, column=0, sticky="ew", padx=pad, pady=(0, 20))



        ctk.CTkLabel(

            rodape,

            text=self.usuario["nome"][:24],

            font=ctk.CTkFont(size=11),

            text_color=COR_TEXTO_MUTED,

            anchor="w",

        ).pack(fill="x", pady=(0, 8))



        ctk.CTkButton(

            rodape,

            text="  🚪   Sair",

            height=42,

            corner_radius=RAIO_BOTAO,

            anchor="w",

            fg_color="transparent",

            text_color=COR_TEXTO_SEC,

            hover_color=COR_HOVER,

            font=ctk.CTkFont(size=13),

            command=self._sair,

        ).pack(fill="x")



    def _criar_botao_nav(self, icone, rotulo, destino, row, muted=False):

        btn = ctk.CTkButton(

            self.sidebar,

            text=f"  {icone}   {rotulo}",

            height=44,

            corner_radius=RAIO_BOTAO,

            anchor="w",

            fg_color="transparent",

            text_color=COR_TEXTO_MUTED if muted else COR_TEXTO,

            hover_color=COR_HOVER,

            font=ctk.CTkFont(size=13),

            command=lambda d=destino: self._navegar(d),

        )

        btn.grid(row=row, column=0, sticky="ew", padx=ESPACO_SM, pady=4)

        return btn



    def _ao_mudar_periodo(self, periodo):

        self.periodo = periodo

        self._atualizar_todas_telas()



    def _atualizar_todas_telas(self):

        for tela in self.telas.values():

            tela.atualizar()



    def _navegar(self, destino):

        if destino == "exportar":

            exportar_csv(self.usuario["id"], self.usuario["nome"].replace(" ", "_"))

            return

        if destino == "pdf":

            gerar_relatorio_pdf(self.usuario)

            return

        self._mostrar_tela(destino)



    def _mostrar_tela(self, nome):

        if nome not in self.telas or not self.winfo_exists():

            return



        self.telas[nome].tkraise()

        self.tela_atual = nome

        self.telas[nome].atualizar()

        self._destacar_botao_ativo(nome)



    def _destacar_botao_ativo(self, nome):

        nav_keys = {item[0] for item in self._MENU_ITENS}

        for chave, btn in self._botoes_nav.items():

            if chave not in nav_keys:

                continue

            if chave == nome:

                btn.configure(fg_color=COR_ATIVO, text_color=COR_ACENTO, hover_color=COR_ATIVO)

            else:

                btn.configure(fg_color="transparent", text_color=COR_TEXTO, hover_color=COR_HOVER)



    def _atualizar_tudo(self):

        if "dashboard" in self.telas:

            self.telas["dashboard"].atualizar()



    def _sair(self):

        self.voltar_login = True

        _destruir_janela(self)





def executar_app():

    while True:

        login = TelaLogin()

        login.mainloop()



        usuario = login.usuario_logado

        _destruir_janela(login)



        if usuario is None:

            break



        app = AplicacaoPrincipal(usuario)

        app.mainloop()



        if not app.voltar_login:

            break





if __name__ == "__main__":

    ctk.set_appearance_mode("dark")

    ctk.set_default_color_theme("blue")

    _patch_ctk_button_click_animation()

    inicializar_banco()

    executar_app()


