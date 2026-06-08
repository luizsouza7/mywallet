"""
Tela de CRUD de movimentações financeiras.
"""

import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from database import (
    adicionar_movimentacao,
    listar_movimentacoes,
    atualizar_movimentacao,
    excluir_movimentacao,
    data_hoje,
)
from theme import (
    COR_BORDA,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_MUTED,
)


class TelaTransacoes(ctk.CTkFrame):
    """Gerenciamento completo de receitas e despesas."""

    def __init__(self, master, usuario, ao_atualizar=None):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self.ao_atualizar = ao_atualizar  # callback para atualizar dashboard
        self.movimentacao_editando = None
        self._criar_interface()

    def _criar_interface(self):
        """Monta formulário e lista de movimentações."""
        ctk.CTkLabel(
            self,
            text="Movimentações",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=32, pady=(28, 16))

        # Layout em duas colunas
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        # ── Formulário ──
        self.frame_form = ctk.CTkFrame(
            container,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        self.frame_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            self.frame_form,
            text="Nova Movimentação",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=20, pady=(20, 15))

        # Tipo (receita / despesa)
        ctk.CTkLabel(self.frame_form, text="Tipo", anchor="w").pack(fill="x", padx=20)
        self.combo_tipo = ctk.CTkComboBox(
            self.frame_form, values=["receita", "despesa"], width=240, state="readonly"
        )
        self.combo_tipo.set("despesa")
        self.combo_tipo.pack(padx=20, pady=(5, 10))

        # Descrição
        ctk.CTkLabel(self.frame_form, text="Descrição", anchor="w").pack(fill="x", padx=20)
        self.entry_descricao = ctk.CTkEntry(self.frame_form, placeholder_text="Ex: Almoço", width=240)
        self.entry_descricao.pack(padx=20, pady=(5, 10))

        # Valor
        ctk.CTkLabel(self.frame_form, text="Valor (R$)", anchor="w").pack(fill="x", padx=20)
        self.entry_valor = ctk.CTkEntry(self.frame_form, placeholder_text="0,00", width=240)
        self.entry_valor.pack(padx=20, pady=(5, 10))

        # Categoria (livre - digitada pelo usuário)
        ctk.CTkLabel(self.frame_form, text="Categoria", anchor="w").pack(fill="x", padx=20)
        self.entry_categoria = ctk.CTkEntry(
            self.frame_form, placeholder_text="Ex: Transporte, Salário...", width=240
        )
        self.entry_categoria.pack(padx=20, pady=(5, 10))

        # Data
        ctk.CTkLabel(self.frame_form, text="Data (AAAA-MM-DD)", anchor="w").pack(fill="x", padx=20)
        self.entry_data = ctk.CTkEntry(self.frame_form, width=240)
        self.entry_data.insert(0, data_hoje())
        self.entry_data.pack(padx=20, pady=(5, 15))

        # Botões
        self.btn_salvar = ctk.CTkButton(
            self.frame_form,
            text="Adicionar",
            width=240,
            height=38,
            font=ctk.CTkFont(weight="bold"),
            command=self._salvar,
        )
        self.btn_salvar.pack(padx=20, pady=(0, 8))

        self.btn_cancelar = ctk.CTkButton(
            self.frame_form,
            text="Cancelar edição",
            width=240,
            fg_color="gray30",
            hover_color="gray40",
            command=self._cancelar_edicao,
        )
        self.btn_cancelar.pack(padx=20, pady=(0, 20))
        self.btn_cancelar.pack_forget()

        # ── Lista ──
        self.frame_lista = ctk.CTkFrame(
            container,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        self.frame_lista.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            self.frame_lista,
            text="Todas as Movimentações",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=20, pady=(20, 10))

        self.scroll_lista = ctk.CTkScrollableFrame(self.frame_lista)
        self.scroll_lista.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _validar_data(self, data_texto):
        """Valida formato da data AAAA-MM-DD."""
        try:
            datetime.strptime(data_texto, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _validar_campos(self):
        """Verifica se os campos do formulário estão corretos."""
        descricao = self.entry_descricao.get().strip()
        categoria = self.entry_categoria.get().strip()
        data = self.entry_data.get().strip()
        valor_texto = self.entry_valor.get().strip().replace(",", ".")
        tipo = self.combo_tipo.get()

        if not descricao or not categoria or not data:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return None

        if tipo not in ("receita", "despesa"):
            messagebox.showwarning("Atenção", "Selecione um tipo válido.")
            return None

        if not self._validar_data(data):
            messagebox.showwarning("Atenção", "Data inválida. Use o formato AAAA-MM-DD.")
            return None

        try:
            valor = float(valor_texto)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor numérico válido e maior que zero.")
            return None

        return {
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria,
            "tipo": tipo,
            "data": data,
        }

    def _salvar(self):
        """Adiciona ou atualiza movimentação."""
        dados = self._validar_campos()
        if not dados:
            return

        try:
            if self.movimentacao_editando:
                atualizar_movimentacao(
                    self.movimentacao_editando,
                    self.usuario["id"],
                    dados["descricao"],
                    dados["valor"],
                    dados["categoria"],
                    dados["tipo"],
                    dados["data"],
                )
                messagebox.showinfo("Sucesso", "Movimentação atualizada!")
                self._cancelar_edicao()
            else:
                adicionar_movimentacao(
                    self.usuario["id"],
                    dados["descricao"],
                    dados["valor"],
                    dados["categoria"],
                    dados["tipo"],
                    dados["data"],
                )
                messagebox.showinfo("Sucesso", "Movimentação adicionada!")

            self._limpar_formulario()
            self.atualizar()
            if self.ao_atualizar:
                self.ao_atualizar()

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    def _limpar_formulario(self):
        """Limpa os campos do formulário."""
        self.entry_descricao.delete(0, "end")
        self.entry_valor.delete(0, "end")
        self.entry_categoria.delete(0, "end")
        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, data_hoje())
        self.combo_tipo.set("despesa")

    def _cancelar_edicao(self):
        """Cancela modo de edição."""
        self.movimentacao_editando = None
        self.btn_salvar.configure(text="Adicionar")
        self.btn_cancelar.pack_forget()
        self._limpar_formulario()

    def _iniciar_edicao(self, mov_id, descricao, valor, categoria, tipo, data):
        """Preenche formulário para editar movimentação."""
        self.movimentacao_editando = mov_id
        self.entry_descricao.delete(0, "end")
        self.entry_descricao.insert(0, descricao)
        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, str(valor))
        self.entry_categoria.delete(0, "end")
        self.entry_categoria.insert(0, categoria)
        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, data)
        self.combo_tipo.set(tipo)
        self.btn_salvar.configure(text="Salvar alterações")
        self.btn_cancelar.pack(padx=20, pady=(0, 20))

    def _excluir(self, mov_id):
        """Exclui movimentação após confirmação."""
        if messagebox.askyesno("Confirmar", "Deseja excluir esta movimentação?"):
            excluir_movimentacao(mov_id, self.usuario["id"])
            self.atualizar()
            if self.ao_atualizar:
                self.ao_atualizar()

    def atualizar(self):
        """Recarrega lista de movimentações."""
        try:
            if not self.scroll_lista.winfo_exists():
                return
        except Exception:
            return

        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        movimentacoes = listar_movimentacoes(self.usuario["id"])

        if not movimentacoes:
            ctk.CTkLabel(
                self.scroll_lista,
                text="Nenhuma movimentação.",
                text_color=COR_TEXTO_MUTED,
            ).pack(pady=30)
            return

        for mov in movimentacoes:
            mov_id, descricao, valor, categoria, tipo, data = mov
            self._criar_item_lista(mov_id, descricao, valor, categoria, tipo, data)

    def _criar_item_lista(self, mov_id, descricao, valor, categoria, tipo, data):
        """Cria linha na lista com botões editar e excluir."""
        item = ctk.CTkFrame(
            self.scroll_lista, corner_radius=8, fg_color="#1f1f23"
        )
        item.pack(fill="x", pady=4)

        cor = COR_RECEITA if tipo == "receita" else COR_DESPESA
        tipo_label = "Receita" if tipo == "receita" else "Despesa"

        info = ctk.CTkFrame(item, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(
            info, text=descricao, font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"{tipo_label} • {categoria} • {data}",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            item,
            text=self._formatar_moeda(valor),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=cor,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            item,
            text="✏",
            width=35,
            height=30,
            fg_color="#3b82f6",
            command=lambda: self._iniciar_edicao(mov_id, descricao, valor, categoria, tipo, data),
        ).pack(side="right", padx=(0, 5), pady=10)

        ctk.CTkButton(
            item,
            text="✕",
            width=35,
            height=30,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=lambda: self._excluir(mov_id),
        ).pack(side="right", padx=(0, 15), pady=10)
