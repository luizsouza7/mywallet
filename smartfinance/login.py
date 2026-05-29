"""
Tela de login e cadastro do MyWallet.
"""

import customtkinter as ctk
from database import cadastrar_usuario, autenticar_usuario


class TelaLogin(ctk.CTk):
    """Janela inicial com opções de login e cadastro."""

    def __init__(self):
        super().__init__()

        self.usuario_logado = None
        self._processando = False

        self.title("MyWallet - Login")
        self.geometry("480x620")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self._fechar)

        self._criar_interface()

    def _fechar(self):
        """Encerra a tela de login sem autenticar."""
        self.usuario_logado = None
        self.withdraw()
        self.quit()

    def _criar_interface(self):
        """Monta os elementos visuais da tela."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        ctk.CTkLabel(
            frame,
            text="💰 MyWallet",
            font=ctk.CTkFont(size=32, weight="bold"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            frame,
            text="Controle financeiro pessoal",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=(0, 30))

        self.abas = ctk.CTkTabview(frame, width=380, height=420)
        self.abas.pack(fill="both", expand=True)
        self.abas.add("Login")
        self.abas.add("Cadastro")

        self._criar_aba_login()
        self._criar_aba_cadastro()

        self.lbl_mensagem = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b"
        )
        self.lbl_mensagem.pack(pady=(10, 0))

    def _criar_aba_login(self):
        """Formulário de login."""
        aba = self.abas.tab("Login")

        ctk.CTkLabel(aba, text="E-mail", anchor="w").pack(fill="x", padx=20, pady=(20, 0))
        self.entry_login_email = ctk.CTkEntry(aba, placeholder_text="seu@email.com", width=320)
        self.entry_login_email.pack(padx=20, pady=(5, 15))

        ctk.CTkLabel(aba, text="Senha", anchor="w").pack(fill="x", padx=20)
        self.entry_login_senha = ctk.CTkEntry(aba, placeholder_text="••••••", show="*", width=320)
        self.entry_login_senha.pack(padx=20, pady=(5, 25))

        self.btn_entrar = ctk.CTkButton(
            aba,
            text="Entrar",
            width=320,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._fazer_login,
        )
        self.btn_entrar.pack(padx=20)

        self.entry_login_senha.bind("<Return>", lambda e: self._fazer_login())

    def _criar_aba_cadastro(self):
        """Formulário de cadastro."""
        aba = self.abas.tab("Cadastro")

        ctk.CTkLabel(aba, text="Nome", anchor="w").pack(fill="x", padx=20, pady=(15, 0))
        self.entry_cad_nome = ctk.CTkEntry(aba, placeholder_text="Seu nome", width=320)
        self.entry_cad_nome.pack(padx=20, pady=(5, 10))

        ctk.CTkLabel(aba, text="E-mail", anchor="w").pack(fill="x", padx=20)
        self.entry_cad_email = ctk.CTkEntry(aba, placeholder_text="seu@email.com", width=320)
        self.entry_cad_email.pack(padx=20, pady=(5, 10))

        ctk.CTkLabel(aba, text="Senha", anchor="w").pack(fill="x", padx=20)
        self.entry_cad_senha = ctk.CTkEntry(aba, placeholder_text="Mínimo 4 caracteres", show="*", width=320)
        self.entry_cad_senha.pack(padx=20, pady=(5, 20))

        ctk.CTkButton(
            aba,
            text="Criar conta",
            width=320,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._fazer_cadastro,
        ).pack(padx=20)

    def _mostrar_mensagem(self, texto, sucesso=False):
        """Exibe mensagem de feedback na tela."""
        cor = "#4ade80" if sucesso else "#ff6b6b"
        self.lbl_mensagem.configure(text=texto, text_color=cor)

    def _fazer_login(self):
        """Valida campos e tenta autenticar o usuário."""
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
        """Valida campos e cadastra novo usuário."""
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
