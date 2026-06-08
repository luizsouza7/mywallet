"""
Tela principal (Dashboard) do MyWallet.
Exibe saldo, totais e movimentações recentes.
"""

import customtkinter as ctk
from datetime import datetime

from database import (
    calcular_resumo,
    contar_movimentacoes,
    listar_movimentacoes,
)
from periodo import formatar_variacao, periodo_anterior
from theme import (
    COR_ACENTO,
    COR_BARRA_FUNDO,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_FUNDO_HOVER,
    COR_FUNDO_ITEM,
    COR_RECEITA,
    COR_SALDO_NEG,
    COR_SALDO_POS,
    COR_TEXTO,
    COR_TEXTO_MUTED,
    COR_TEXTO_SEC,
    ESPACO_LG,
    ESPACO_MD,
    ESPACO_SM,
    ICONE_DESPESA,
    ICONE_RECEITA,
    RAIO_AVATAR,
    RAIO_CARD,
    RAIO_ITEM,
    iniciais_usuario,
)


class TelaDashboard(ctk.CTkFrame):
    """Painel inicial com resumo financeiro."""

    def __init__(self, master, usuario, obter_periodo=None):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self.obter_periodo = obter_periodo
        self._cards_variacao = {}
        self._criar_interface()

    def _periodo(self):
        if self.obter_periodo:
            p = self.obter_periodo()
            return p.get("data_inicio"), p.get("data_fim")
        return None, None

    def _criar_interface(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        padx = ESPACO_LG

        # Cabeçalho
        cabecalho = ctk.CTkFrame(container, fg_color="transparent")
        cabecalho.pack(fill="x", padx=padx, pady=(ESPACO_MD, ESPACO_SM))

        col_titulo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        col_titulo.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            col_titulo,
            text="Dashboard",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w")

        ctk.CTkLabel(
            col_titulo,
            text="Resumo financeiro",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_SEC,
        ).pack(anchor="w", pady=(4, 0))

        col_direita = ctk.CTkFrame(cabecalho, fg_color="transparent")
        col_direita.pack(side="right")

        ctk.CTkLabel(
            col_direita,
            text=datetime.now().strftime("%d/%m/%Y"),
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
        ).pack(side="left", padx=(0, ESPACO_SM))

        avatar = ctk.CTkFrame(
            col_direita, width=40, height=40, corner_radius=RAIO_AVATAR, fg_color=COR_FUNDO_ITEM
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=iniciais_usuario(self.usuario["nome"]),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COR_ACENTO,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Linha 1: 4 cards
        self.frame_cards = ctk.CTkFrame(container, fg_color="transparent")
        self.frame_cards.pack(fill="x", padx=padx, pady=(0, ESPACO_SM))
        for col in range(4):
            self.frame_cards.grid_columnconfigure(col, weight=1)

        self.lbl_saldo, self.lbl_saldo_var = self._criar_card_metrica(
            self.frame_cards, "Saldo atual", "R$ 0,00", 0, COR_TEXTO
        )
        self.lbl_receitas, self.lbl_receitas_var = self._criar_card_metrica(
            self.frame_cards, "Receitas", "R$ 0,00", 1, COR_RECEITA
        )
        self.lbl_despesas, self.lbl_despesas_var = self._criar_card_metrica(
            self.frame_cards, "Despesas", "R$ 0,00", 2, COR_DESPESA
        )
        self.lbl_movs, self.lbl_movs_var = self._criar_card_metrica(
            self.frame_cards, "Movimentações", "0", 3, COR_TEXTO
        )

        # Linha 2: gráfico resumido
        self.frame_grafico = ctk.CTkFrame(
            container, corner_radius=RAIO_CARD, fg_color=COR_FUNDO_CARD, border_width=0
        )
        self.frame_grafico.pack(fill="x", padx=padx, pady=(0, ESPACO_SM))

        topo_graf = ctk.CTkFrame(self.frame_grafico, fg_color="transparent")
        topo_graf.pack(fill="x", padx=ESPACO_MD, pady=(ESPACO_SM, 4))
        ctk.CTkLabel(
            topo_graf,
            text="Receitas x Despesas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w")

        self.frame_barras = ctk.CTkFrame(self.frame_grafico, fg_color="transparent")
        self.frame_barras.pack(fill="x", padx=ESPACO_MD, pady=(0, ESPACO_MD))

        # Linha 3: movimentações recentes
        secao_recentes = ctk.CTkFrame(container, fg_color="transparent")
        secao_recentes.pack(fill="x", padx=padx, pady=(0, ESPACO_MD))

        ctk.CTkLabel(
            secao_recentes,
            text="Movimentações recentes",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", pady=(0, ESPACO_SM))

        self.frame_lista = ctk.CTkFrame(
            secao_recentes, corner_radius=RAIO_CARD, fg_color=COR_FUNDO_CARD, border_width=0
        )
        self.frame_lista.pack(fill="x")

        header_lista = ctk.CTkFrame(self.frame_lista, fg_color="transparent", height=28)
        header_lista.pack(fill="x", padx=ESPACO_SM, pady=(8, 0))
        header_lista.pack_propagate(False)
        for col, (txt, w) in enumerate(
            [("Descrição", 3), ("Categoria", 2), ("Data", 1), ("Valor", 2)]
        ):
            header_lista.grid_columnconfigure(col, weight=w)
            ctk.CTkLabel(
                header_lista,
                text=txt,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COR_TEXTO_MUTED,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=(12 if col == 0 else 4, 0))

        self.frame_lista_inner = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        self.frame_lista_inner.pack(fill="x", padx=4, pady=(0, 4))

    def _criar_card_metrica(self, parent, titulo, valor, coluna, cor_valor):
        card = ctk.CTkFrame(
            parent, corner_radius=RAIO_CARD, fg_color=COR_FUNDO_CARD, border_width=0
        )
        card.grid(row=0, column=coluna, padx=5, pady=2, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=ESPACO_SM, pady=ESPACO_SM)

        ctk.CTkLabel(
            inner, text=titulo, font=ctk.CTkFont(size=12), text_color=COR_TEXTO_SEC, anchor="w"
        ).pack(anchor="w")

        lbl_valor = ctk.CTkLabel(
            inner,
            text=valor,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=cor_valor,
            anchor="w",
        )
        lbl_valor.pack(anchor="w", pady=(8, 2))

        lbl_var = ctk.CTkLabel(
            inner, text="", font=ctk.CTkFont(size=10), text_color=COR_TEXTO_MUTED, anchor="w"
        )
        lbl_var.pack(anchor="w")

        return lbl_valor, lbl_var

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _widget_valido(self, widget):
        try:
            return widget.winfo_exists()
        except Exception:
            return False

    def _atualizar_cards(self, resumo, total_mov, resumo_ant):
        cor_saldo = COR_SALDO_POS if resumo["saldo"] >= 0 else COR_SALDO_NEG
        self.lbl_saldo.configure(text=self._formatar_moeda(resumo["saldo"]), text_color=cor_saldo)
        self.lbl_receitas.configure(
            text=self._formatar_moeda(resumo["receitas"]), text_color=COR_RECEITA
        )
        self.lbl_despesas.configure(
            text=self._formatar_moeda(resumo["despesas"]), text_color=COR_DESPESA
        )
        self.lbl_movs.configure(text=str(total_mov))

        txt, cor = formatar_variacao(resumo["saldo"], resumo_ant["saldo"])
        self.lbl_saldo_var.configure(text=txt, text_color=cor)

        txt, cor = formatar_variacao(resumo["receitas"], resumo_ant["receitas"])
        self.lbl_receitas_var.configure(text=txt, text_color=cor)

        txt, cor = formatar_variacao(resumo["despesas"], resumo_ant["despesas"])
        # Para despesas, queda é positiva (verde) e alta é negativa (vermelho)
        if resumo["despesas"] < resumo_ant["despesas"]:
            cor = COR_RECEITA
        elif resumo["despesas"] > resumo_ant["despesas"]:
            cor = COR_DESPESA
        self.lbl_despesas_var.configure(text=txt, text_color=cor)

        txt, cor = formatar_variacao(total_mov, resumo_ant.get("movimentacoes", 0))
        self.lbl_movs_var.configure(text=txt, text_color=cor)

    def _limpar_barras(self):
        for w in self.frame_barras.winfo_children():
            w.destroy()

    def _atualizar_grafico_resumo(self, resumo):
        self._limpar_barras()
        receitas = resumo["receitas"]
        despesas = resumo["despesas"]

        if receitas == 0 and despesas == 0:
            ctk.CTkLabel(
                self.frame_barras,
                text="Sem movimentações no período selecionado.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=12)
            return

        max_valor = max(receitas, despesas, 1)
        for titulo, valor, cor in [
            ("Receitas", receitas, COR_RECEITA),
            ("Despesas", despesas, COR_DESPESA),
        ]:
            bloco = ctk.CTkFrame(self.frame_barras, fg_color="transparent")
            bloco.pack(fill="x", pady=6)

            linha = ctk.CTkFrame(bloco, fg_color="transparent")
            linha.pack(fill="x")
            ctk.CTkLabel(
                linha, text=titulo, font=ctk.CTkFont(size=12), text_color=COR_TEXTO_SEC
            ).pack(side="left")
            ctk.CTkLabel(
                linha,
                text=self._formatar_moeda(valor),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=cor,
            ).pack(side="right")

            barra = ctk.CTkProgressBar(
                bloco, height=6, corner_radius=3, progress_color=cor,
                fg_color=COR_BARRA_FUNDO, border_width=0,
            )
            barra.set(min(valor / max_valor, 1.0))
            barra.pack(fill="x", pady=(6, 0))

    def _atualizar_lista_recentes(self, data_inicio, data_fim):
        for widget in self.frame_lista_inner.winfo_children():
            widget.destroy()

        movimentacoes = listar_movimentacoes(
            self.usuario["id"], limite=8, data_inicio=data_inicio, data_fim=data_fim
        )

        if not movimentacoes:
            ctk.CTkLabel(
                self.frame_lista_inner,
                text="Nenhuma movimentação no período selecionado.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=ESPACO_MD, padx=ESPACO_SM)
            return

        for mov in movimentacoes:
            _, descricao, valor, categoria, tipo, data = mov
            self._adicionar_item_lista(descricao, valor, categoria, tipo, data)

    def atualizar(self):
        if not self._widget_valido(self):
            return

        data_inicio, data_fim = self._periodo()
        resumo = calcular_resumo(self.usuario["id"], data_inicio, data_fim)
        total_mov = contar_movimentacoes(self.usuario["id"], data_inicio, data_fim)

        resumo_ant = {"saldo": 0, "receitas": 0, "despesas": 0, "movimentacoes": 0}
        if data_inicio and data_fim:
            ini_ant, fim_ant = periodo_anterior(data_inicio, data_fim)
            ant = calcular_resumo(self.usuario["id"], ini_ant, fim_ant)
            resumo_ant = {
                **ant,
                "movimentacoes": contar_movimentacoes(self.usuario["id"], ini_ant, fim_ant),
            }

        self._atualizar_cards(resumo, total_mov, resumo_ant)
        self._atualizar_grafico_resumo(resumo)

        if self._widget_valido(self.frame_lista_inner):
            self._atualizar_lista_recentes(data_inicio, data_fim)

    def _adicionar_item_lista(self, descricao, valor, categoria, tipo, data):
        cor = COR_RECEITA if tipo == "receita" else COR_DESPESA
        sinal = "+" if tipo == "receita" else "−"
        data_fmt = data[5:10].replace("-", "/") if len(data) >= 10 else data

        item = ctk.CTkFrame(
            self.frame_lista_inner, corner_radius=RAIO_ITEM, height=40, fg_color="transparent"
        )
        item.pack(fill="x", pady=1)
        item.pack_propagate(False)

        def _hover_on(_):
            if item.winfo_exists():
                item.configure(fg_color=COR_FUNDO_HOVER)

        def _hover_off(_):
            if item.winfo_exists():
                item.configure(fg_color="transparent")

        item.bind("<Enter>", _hover_on)
        item.bind("<Leave>", _hover_off)

        for col, w in enumerate([3, 2, 1, 2]):
            item.grid_columnconfigure(col, weight=w)

        icone = ICONE_RECEITA if tipo == "receita" else ICONE_DESPESA
        linha_desc = ctk.CTkFrame(item, fg_color="transparent")
        linha_desc.grid(row=0, column=0, sticky="w", padx=(12, 4), pady=8)

        ctk.CTkLabel(
            linha_desc, text=icone, font=ctk.CTkFont(size=12, weight="bold"), text_color=cor
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            linha_desc, text=descricao, font=ctk.CTkFont(size=13), text_color=COR_TEXTO, anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            item, text=categoria, font=ctk.CTkFont(size=12), text_color=COR_TEXTO_SEC, anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=4, pady=8)

        ctk.CTkLabel(
            item, text=data_fmt, font=ctk.CTkFont(size=12), text_color=COR_TEXTO_MUTED, anchor="w"
        ).grid(row=0, column=2, sticky="w", padx=4, pady=8)

        ctk.CTkLabel(
            item,
            text=f"{sinal} {self._formatar_moeda(valor)}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=cor,
            anchor="e",
        ).grid(row=0, column=3, sticky="e", padx=(4, 16), pady=8)
