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
    obter_categorias,
    data_hoje,
)
from periodo import formatar_intervalo
from theme import (
    COR_ACENTO,
    COR_BOTAO_PRIMARIO,
    COR_BOTAO_PRIMARIO_HOVER,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_FUNDO_HOVER,
    COR_FUNDO_ITEM,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_MUTED,
    COR_TEXTO_SEC,
    ESPACO_LG,
    ESPACO_MD,
    ESPACO_SM,
    RAIO_BOTAO,
    RAIO_CARD,
    RAIO_ITEM,
)

# Layout compartilhado entre cabeçalho e linhas (alinhamento consistente)
_COLUNAS_TABELA = (
    {"titulo": "Descrição", "minsize": 220, "weight": 1, "anchor": "w"},
    {"titulo": "Categoria", "minsize": 130, "weight": 0, "anchor": "w"},
    {"titulo": "Data", "minsize": 72, "weight": 0, "anchor": "w"},
    {"titulo": "Valor", "minsize": 118, "weight": 0, "anchor": "e"},
    {"titulo": "", "minsize": 88, "weight": 0, "anchor": "e"},
)


class ModalTransacao(ctk.CTkToplevel):
    """Janela modal para criar ou editar uma movimentação."""

    def __init__(self, master, usuario, ao_salvar, dados_edicao=None):
        super().__init__(master)
        self.usuario = usuario
        self.ao_salvar = ao_salvar
        self.mov_id = dados_edicao["id"] if dados_edicao else None

        titulo = "Editar transação" if dados_edicao else "Nova transação"
        self.title(titulo)
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(fg_color=COR_FUNDO_CARD)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._criar_formulario(dados_edicao)
        self.after(50, self.focus_force)

    def _criar_formulario(self, dados):
        pad = ESPACO_MD

        ctk.CTkLabel(
            self,
            text="Editar transação" if dados else "Nova transação",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=pad, pady=(pad, 4))

        ctk.CTkLabel(
            self,
            text="Preencha os dados da movimentação",
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
        ).pack(anchor="w", padx=pad, pady=(0, ESPACO_SM))

        self._campo("Tipo", pad)
        self.combo_tipo = ctk.CTkComboBox(
            self, values=["receita", "despesa"], height=38,
            corner_radius=RAIO_BOTAO, state="readonly",
        )
        self.combo_tipo.set(dados["tipo"] if dados else "despesa")
        self.combo_tipo.pack(fill="x", padx=pad, pady=(4, 12))

        self._campo("Descrição", pad)
        self.entry_descricao = ctk.CTkEntry(
            self, placeholder_text="Ex: Almoço", height=38, corner_radius=RAIO_BOTAO,
        )
        self.entry_descricao.pack(fill="x", padx=pad, pady=(4, 12))
        if dados:
            self.entry_descricao.insert(0, dados["descricao"])

        self._campo("Valor (R$)", pad)
        self.entry_valor = ctk.CTkEntry(
            self, placeholder_text="0,00", height=38, corner_radius=RAIO_BOTAO,
        )
        self.entry_valor.pack(fill="x", padx=pad, pady=(4, 12))
        if dados:
            self.entry_valor.insert(0, str(dados["valor"]))

        self._campo("Categoria", pad)
        self.entry_categoria = ctk.CTkEntry(
            self, placeholder_text="Ex: Transporte", height=38, corner_radius=RAIO_BOTAO,
        )
        self.entry_categoria.pack(fill="x", padx=pad, pady=(4, 12))
        if dados:
            self.entry_categoria.insert(0, dados["categoria"])

        self._campo("Data (AAAA-MM-DD)", pad)
        self.entry_data = ctk.CTkEntry(self, height=38, corner_radius=RAIO_BOTAO)
        self.entry_data.pack(fill="x", padx=pad, pady=(4, 20))
        self.entry_data.insert(0, dados["data"] if dados else data_hoje())

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=pad, pady=(0, pad))

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=40,
            corner_radius=RAIO_BOTAO,
            fg_color="transparent",
            text_color=COR_TEXTO_SEC,
            hover_color=COR_FUNDO_ITEM,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            botoes,
            text="Salvar",
            height=40,
            corner_radius=RAIO_BOTAO,
            fg_color=COR_BOTAO_PRIMARIO,
            hover_color=COR_BOTAO_PRIMARIO_HOVER,
            font=ctk.CTkFont(weight="bold"),
            command=self._salvar,
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))

    def _campo(self, rotulo, pad):
        ctk.CTkLabel(
            self,
            text=rotulo,
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
            anchor="w",
        ).pack(fill="x", padx=pad)

    def _validar(self):
        descricao = self.entry_descricao.get().strip()
        categoria = self.entry_categoria.get().strip()
        data = self.entry_data.get().strip()
        valor_texto = self.entry_valor.get().strip().replace(",", ".")
        tipo = self.combo_tipo.get()

        if not descricao or not categoria or not data:
            messagebox.showwarning("Atenção", "Preencha todos os campos.", parent=self)
            return None

        if tipo not in ("receita", "despesa"):
            messagebox.showwarning("Atenção", "Selecione um tipo válido.", parent=self)
            return None

        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Atenção", "Data inválida. Use AAAA-MM-DD.", parent=self)
            return None

        try:
            valor = float(valor_texto)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido maior que zero.", parent=self)
            return None

        return {
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria,
            "tipo": tipo,
            "data": data,
        }

    def _salvar(self):
        dados = self._validar()
        if not dados:
            return

        try:
            if self.mov_id:
                atualizar_movimentacao(
                    self.mov_id,
                    self.usuario["id"],
                    dados["descricao"],
                    dados["valor"],
                    dados["categoria"],
                    dados["tipo"],
                    dados["data"],
                )
            else:
                adicionar_movimentacao(
                    self.usuario["id"],
                    dados["descricao"],
                    dados["valor"],
                    dados["categoria"],
                    dados["tipo"],
                    dados["data"],
                )

            self.ao_salvar()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}", parent=self)


class TelaTransacoes(ctk.CTkFrame):
    """Lista de movimentações com modal para cadastro/edição."""

    def __init__(self, master, usuario, ao_atualizar=None, obter_periodo=None):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self.ao_atualizar = ao_atualizar
        self.obter_periodo = obter_periodo
        self._criar_interface()

    def _periodo(self):
        if self.obter_periodo:
            p = self.obter_periodo()
            return p.get("data_inicio"), p.get("data_fim")
        return None, None

    def _criar_interface(self):
        padx = ESPACO_LG

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=padx, pady=(ESPACO_MD, ESPACO_SM))

        col_titulo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        col_titulo.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            col_titulo,
            text="Movimentações",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w")

        ctk.CTkLabel(
            col_titulo,
            text="Histórico de transações",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_SEC,
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            cabecalho,
            text="+  Nova Transação",
            height=40,
            corner_radius=RAIO_BOTAO,
            fg_color=COR_BOTAO_PRIMARIO,
            hover_color=COR_BOTAO_PRIMARIO_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._abrir_modal_nova,
        ).pack(side="right")

        # Filtros avançados
        filtros = ctk.CTkFrame(self, fg_color="transparent")
        filtros.pack(fill="x", padx=padx, pady=(0, ESPACO_SM))

        self.lbl_periodo = ctk.CTkLabel(
            filtros,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
        )
        self.lbl_periodo.pack(anchor="w", pady=(0, 8))

        linha_filtros = ctk.CTkFrame(filtros, fg_color="transparent")
        linha_filtros.pack(fill="x")

        ctk.CTkLabel(
            linha_filtros, text="Tipo", font=ctk.CTkFont(size=11), text_color=COR_TEXTO_SEC
        ).pack(side="left", padx=(0, 4))
        self.combo_tipo = ctk.CTkComboBox(
            linha_filtros,
            values=["Todos", "Receita", "Despesa"],
            width=110,
            height=34,
            corner_radius=RAIO_BOTAO,
            state="readonly",
            command=lambda _: self.atualizar(),
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            linha_filtros, text="Categoria", font=ctk.CTkFont(size=11), text_color=COR_TEXTO_SEC
        ).pack(side="left", padx=(0, 4))
        self.combo_categoria = ctk.CTkComboBox(
            linha_filtros,
            values=["Todas"],
            width=130,
            height=34,
            corner_radius=RAIO_BOTAO,
            state="readonly",
            command=lambda _: self.atualizar(),
        )
        self.combo_categoria.set("Todas")
        self.combo_categoria.pack(side="left", padx=(0, 12))

        self.entry_busca = ctk.CTkEntry(
            linha_filtros,
            placeholder_text="🔍  Buscar movimentação...",
            height=34,
            corner_radius=RAIO_BOTAO,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True)
        self.entry_busca.bind("<KeyRelease>", lambda _: self.atualizar())

        # Tabela
        self.frame_tabela = ctk.CTkFrame(
            self,
            corner_radius=RAIO_CARD,
            fg_color=COR_FUNDO_CARD,
            border_width=0,
        )
        self.frame_tabela.pack(fill="both", expand=True, padx=padx, pady=(0, ESPACO_MD))

        self.header_tabela = ctk.CTkFrame(
            self.frame_tabela, fg_color=COR_FUNDO_ITEM, corner_radius=RAIO_ITEM, height=38
        )
        # Margem extra à direita compensa a largura da scrollbar da lista
        self.header_tabela.pack(fill="x", padx=(ESPACO_SM, ESPACO_SM + 14), pady=(ESPACO_SM, 6))
        self.header_tabela.pack_propagate(False)
        self._configurar_colunas(self.header_tabela)
        self._preencher_cabecalho(self.header_tabela)

        self.scroll_lista = ctk.CTkScrollableFrame(
            self.frame_tabela, fg_color="transparent"
        )
        self.scroll_lista.pack(fill="both", expand=True, padx=ESPACO_SM, pady=(0, ESPACO_SM))

    def _configurar_colunas(self, frame):
        for i, col in enumerate(_COLUNAS_TABELA):
            frame.grid_columnconfigure(i, minsize=col["minsize"], weight=col["weight"])

    def _pad_coluna(self, col_idx):
        if col_idx == 0:
            return (14, 8)
        if col_idx == len(_COLUNAS_TABELA) - 1:
            return (4, 10)
        return (8, 8)

    def _preencher_cabecalho(self, header):
        for i, col in enumerate(_COLUNAS_TABELA):
            if not col["titulo"]:
                continue
            sticky = "ew" if col["anchor"] == "e" else "w"
            ctk.CTkLabel(
                header,
                text=col["titulo"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COR_TEXTO_MUTED,
                anchor=col["anchor"],
            ).grid(
                row=0, column=i, sticky=sticky,
                padx=self._pad_coluna(i), pady=10,
            )

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _abrir_modal_nova(self):
        ModalTransacao(self, self.usuario, self._apos_salvar)

    def _abrir_modal_editar(self, mov_id, descricao, valor, categoria, tipo, data):
        dados = {
            "id": mov_id,
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria,
            "tipo": tipo,
            "data": data,
        }
        ModalTransacao(self, self.usuario, self._apos_salvar, dados_edicao=dados)

    def _apos_salvar(self):
        self.atualizar()
        if self.ao_atualizar:
            self.ao_atualizar()

    def _excluir(self, mov_id):
        if messagebox.askyesno("Confirmar", "Deseja excluir esta movimentação?"):
            excluir_movimentacao(mov_id, self.usuario["id"])
            self.atualizar()
            if self.ao_atualizar:
                self.ao_atualizar()

    def _filtros_ativos(self):
        data_inicio, data_fim = self._periodo()
        tipo_sel = self.combo_tipo.get()
        tipo = None
        if tipo_sel == "Receita":
            tipo = "receita"
        elif tipo_sel == "Despesa":
            tipo = "despesa"

        cat_sel = self.combo_categoria.get()
        categoria = None if cat_sel == "Todas" else cat_sel

        busca = self.entry_busca.get().strip() or None
        return data_inicio, data_fim, tipo, categoria, busca

    def _atualizar_categorias(self):
        cats = obter_categorias(self.usuario["id"])
        valores = ["Todas"] + cats
        atual = self.combo_categoria.get()
        self.combo_categoria.configure(values=valores)
        if atual in valores:
            self.combo_categoria.set(atual)
        else:
            self.combo_categoria.set("Todas")

    def atualizar(self):
        try:
            if not self.scroll_lista.winfo_exists():
                return
        except Exception:
            return

        self._atualizar_categorias()

        data_inicio, data_fim = self._periodo()
        if hasattr(self, "lbl_periodo"):
            self.lbl_periodo.configure(
                text=f"Período: {formatar_intervalo(data_inicio, data_fim)}"
            )

        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        di, df, tipo, categoria, busca = self._filtros_ativos()
        movimentacoes = listar_movimentacoes(
            self.usuario["id"],
            data_inicio=di,
            data_fim=df,
            tipo=tipo,
            categoria=categoria,
            busca=busca,
        )

        if not movimentacoes:
            ctk.CTkLabel(
                self.scroll_lista,
                text="Nenhuma movimentação encontrada.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=13),
            ).pack(pady=48)
            return

        for mov in movimentacoes:
            mov_id, descricao, valor, categoria, tipo, data = mov
            self._criar_linha(mov_id, descricao, valor, categoria, tipo, data)

    def _criar_linha(self, mov_id, descricao, valor, categoria, tipo, data):
        cor = COR_RECEITA if tipo == "receita" else COR_DESPESA
        sinal = "+" if tipo == "receita" else "−"
        data_fmt = data[8:10] + "/" + data[5:7] if len(data) >= 10 else data

        linha = ctk.CTkFrame(
            self.scroll_lista,
            corner_radius=RAIO_ITEM,
            height=48,
            fg_color="transparent",
        )
        linha.pack(fill="x", pady=2)
        linha.pack_propagate(False)
        self._configurar_colunas(linha)

        def _hover_on(_):
            if linha.winfo_exists():
                linha.configure(fg_color=COR_FUNDO_HOVER)

        def _hover_off(_):
            if linha.winfo_exists():
                linha.configure(fg_color="transparent")

        for widget in (linha,):
            widget.bind("<Enter>", _hover_on)
            widget.bind("<Leave>", _hover_off)

        # Coluna 0 — descrição com indicador de tipo
        cel_desc = ctk.CTkFrame(linha, fg_color="transparent")
        cel_desc.grid(row=0, column=0, sticky="ew", padx=self._pad_coluna(0), pady=8)

        indicador = ctk.CTkFrame(
            cel_desc, width=8, height=8, corner_radius=4, fg_color=cor
        )
        indicador.pack(side="left", padx=(0, 10), pady=6)
        indicador.pack_propagate(False)

        lbl_desc = ctk.CTkLabel(
            cel_desc,
            text=descricao,
            font=ctk.CTkFont(size=14),
            text_color=COR_TEXTO,
            anchor="w",
        )
        lbl_desc.pack(side="left", fill="x", expand=True)
        lbl_desc.bind("<Enter>", _hover_on)
        lbl_desc.bind("<Leave>", _hover_off)

        # Coluna 1 — categoria
        lbl_cat = ctk.CTkLabel(
            linha,
            text=categoria,
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_SEC,
            anchor="w",
        )
        lbl_cat.grid(row=0, column=1, sticky="w", padx=self._pad_coluna(1), pady=8)
        lbl_cat.bind("<Enter>", _hover_on)
        lbl_cat.bind("<Leave>", _hover_off)

        # Coluna 2 — data
        lbl_data = ctk.CTkLabel(
            linha,
            text=data_fmt,
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_MUTED,
            anchor="w",
        )
        lbl_data.grid(row=0, column=2, sticky="w", padx=self._pad_coluna(2), pady=8)
        lbl_data.bind("<Enter>", _hover_on)
        lbl_data.bind("<Leave>", _hover_off)

        # Coluna 3 — valor (alinhado à direita)
        lbl_valor = ctk.CTkLabel(
            linha,
            text=f"{sinal} {self._formatar_moeda(valor)}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=cor,
            anchor="e",
        )
        lbl_valor.grid(row=0, column=3, sticky="e", padx=self._pad_coluna(3), pady=8)
        lbl_valor.bind("<Enter>", _hover_on)
        lbl_valor.bind("<Leave>", _hover_off)

        # Coluna 4 — ações
        acoes = ctk.CTkFrame(linha, fg_color="transparent")
        acoes.grid(row=0, column=4, sticky="e", padx=self._pad_coluna(4), pady=6)

        ctk.CTkButton(
            acoes,
            text="✏️",
            width=34,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COR_FUNDO_ITEM,
            text_color=COR_ACENTO,
            font=ctk.CTkFont(size=15),
            command=lambda: self._abrir_modal_editar(
                mov_id, descricao, valor, categoria, tipo, data
            ),
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            acoes,
            text="🗑️",
            width=34,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COR_FUNDO_ITEM,
            text_color=COR_DESPESA,
            font=ctk.CTkFont(size=15),
            command=lambda: self._excluir(mov_id),
        ).pack(side="left", padx=1)
