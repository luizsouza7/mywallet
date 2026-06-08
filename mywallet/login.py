"""
Tela de login e cadastro do MyWallet.
"""

import customtkinter as ctk
from database import cadastrar_usuario, autenticar_usuario
from theme import (
    COR_ACENTO,
    COR_ATIVO,
    COR_BOTAO_PRIMARIO,
    COR_BOTAO_PRIMARIO_HOVER,
    COR_DESPESA,
    COR_FUNDO,
    COR_FUNDO_CARD,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_SEC,
    ESPACO_MD,
    RAIO_BOTAO,
    RAIO_CARD,
)


class TelaLogin(ctk.CTk):
    """Janela inicial com opções de login e cadastro."""

    def __init__(self):
        super().__init__(fg_color=COR_FUNDO)

        self.usuario_logado = None
        self._processando = False

        self.title("MyWallet - Login")
        self.geometry("440x600")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self._fechar)

        self._criar_interface()

    def _fechar(self):
        self.usuario_logado = None
        self.withdraw()
        self.quit()

    def _criar_interface(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=ESPACO_MD, pady=ESPACO_MD)

        cabecalho = ctk.CTkFrame(frame, fg_color="transparent")
        cabecalho.pack(pady=(0, ESPACO_MD))

        badge = ctk.CTkFrame(
            cabecalho, width=48, height=48, corner_radius=12, fg_color=COR_ATIVO
        )
        badge.pack()
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge,
            text="₿",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COR_ACENTO,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame,
            text="MyWallet",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            frame,
            text="Controle financeiro pessoal",
            font=ctk.CTkFont(size=14),
            text_color=COR_TEXTO_SEC,
        ).pack(pady=(0, ESPACO_MD))

        card = ctk.CTkFrame(
            frame,
            corner_radius=RAIO_CARD,
            fg_color=COR_FUNDO_CARD,
            border_width=0,
        )
        card.pack(fill="both", expand=True)

        self.abas = ctk.CTkTabview(
            card, width=360, height=380, corner_radius=RAIO_BOTAO
        )
        self.abas.pack(fill="both", expand=True, padx=ESPACO_MD, pady=ESPACO_MD)
        self.abas.add("Login")
        self.abas.add("Cadastro")

        self._criar_aba_login()
        self._criar_aba_cadastro()

        self.lbl_mensagem = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color=COR_DESPESA
        )
        self.lbl_mensagem.pack(pady=(12, 0))

    def _estilizar_campo(self, aba, rotulo, entry):
        ctk.CTkLabel(
            aba,
            text=rotulo,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
        ).pack(fill="x", padx=20, pady=(12, 0))
        entry.configure(
            width=300,
            height=38,
            corner_radius=RAIO_BOTAO,
            border_width=0,
        )
        entry.pack(padx=20, pady=(6, 4))

    def _criar_aba_login(self):
        aba = self.abas.tab("Login")

        self.entry_login_email = ctk.CTkEntry(aba, placeholder_text="seu@email.com")
        self._estilizar_campo(aba, "E-mail", self.entry_login_email)

        self.entry_login_senha = ctk.CTkEntry(aba, placeholder_text="••••••", show="*")
        self._estilizar_campo(aba, "Senha", self.entry_login_senha)

        self.btn_entrar = ctk.CTkButton(
            aba,
            text="Entrar",
            width=300,
            height=42,
            corner_radius=RAIO_BOTAO,
            fg_color=COR_BOTAO_PRIMARIO,
            hover_color=COR_BOTAO_PRIMARIO_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._fazer_login,
        )
        self.btn_entrar.pack(padx=20, pady=(20, 10))

        self.entry_login_senha.bind("<Return>", lambda e: self._fazer_login())

    def _criar_aba_cadastro(self):
        aba = self.abas.tab("Cadastro")

        self.entry_cad_nome = ctk.CTkEntry(aba, placeholder_text="Seu nome")
        self._estilizar_campo(aba, "Nome", self.entry_cad_nome)

        self.entry_cad_email = ctk.CTkEntry(aba, placeholder_text="seu@email.com")
        self._estilizar_campo(aba, "E-mail", self.entry_cad_email)

        self.entry_cad_senha = ctk.CTkEntry(
            aba, placeholder_text="Mínimo 4 caracteres", show="*"
        )
        self._estilizar_campo(aba, "Senha", self.entry_cad_senha)

        ctk.CTkButton(
            aba,
            text="Criar conta",
            width=300,
            height=42,
            corner_radius=RAIO_BOTAO,
            fg_color=COR_BOTAO_PRIMARIO,
            hover_color=COR_BOTAO_PRIMARIO_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._fazer_cadastro,
        ).pack(padx=20, pady=(16, 10))

    def _mostrar_mensagem(self, texto, sucesso=False):
        cor = COR_RECEITA if sucesso else COR_DESPESA
        self.lbl_mensagem.configure(text=texto, text_color=cor)

    def _fazer_login(self):
        if self._processando:
            return

        email = self.entry_login_email.get().strip()
        senha = self.entry_login_senha.get()

        if not email or not senha:
            self._mostrar_mensagem("Preencha e-mail e senha.")
            return

        if "@" not in email:
            self._mostrar_mensagem("Informe um e-mail válido.")
            return

        self._processando = True
        self.btn_entrar.configure(state="disabled")

        usuario = autenticar_usuario(email, senha)
        if usuario:
            self.usuario_logado = usuario
            self.withdraw()
            self.quit()
        else:
            self._mostrar_mensagem("E-mail ou senha incorretos.")
            self._processando = False
            self.btn_entrar.configure(state="normal")

    def _fazer_cadastro(self):
        nome = self.entry_cad_nome.get().strip()
        email = self.entry_cad_email.get().strip()
        senha = self.entry_cad_senha.get()

        if not nome or not email or not senha:
            self._mostrar_mensagem("Preencha todos os campos.")
            return

        if "@" not in email:
            self._mostrar_mensagem("Informe um e-mail válido.")
            return

        if len(senha) < 4:
            self._mostrar_mensagem("A senha deve ter pelo menos 4 caracteres.")
            return

        sucesso, mensagem = cadastrar_usuario(nome, email, senha)
        if sucesso:
            self._mostrar_mensagem(mensagem, sucesso=True)
            self.abas.set("Login")
            self.entry_login_email.delete(0, "end")
            self.entry_login_email.insert(0, email)
        else:
            self._mostrar_mensagem(mensagem)
