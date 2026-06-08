"""
Tela principal (Dashboard) do MyWallet.
Exibe saldo, totais, comparativo visual e movimentações recentes.
"""

import customtkinter as ctk
from datetime import datetime

from database import calcular_resumo, contar_movimentacoes, listar_movimentacoes
from theme import (
    COR_BARRA_FUNDO,
    COR_BORDA,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_NEUTRO,
    COR_RECEITA,
    COR_SALDO_NEG,
    COR_SALDO_POS,
    COR_TEXTO,
    COR_TEXTO_MUTED,
    COR_TEXTO_SEC,
)


class TelaDashboard(ctk.CTkFrame):
    """Painel inicial com resumo financeiro."""

    def __init__(self, master, usuario):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self._criar_interface()

    def _criar_interface(self):
        """Monta layout: saldo em destaque → cards → comparativo → recentes."""
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        padx = 32

        cabecalho = ctk.CTkFrame(container, fg_color="transparent")
        cabecalho.pack(fill="x", padx=padx, pady=(28, 20))

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
            text=f"Olá, {self.usuario['nome']}",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_SEC,
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            cabecalho,
            text=datetime.now().strftime("%d/%m/%Y"),
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_MUTED,
        ).pack(side="right", anchor="ne")

        self.card_saldo = self._criar_card_destaque(container, padx)

        self.frame_cards = ctk.CTkFrame(container, fg_color="transparent")
        self.frame_cards.pack(fill="x", padx=padx, pady=(0, 20))
        for col in range(3):
            self.frame_cards.grid_columnconfigure(col, weight=1)

        self.card_receitas, _ = self._criar_card(
            self.frame_cards, "Receitas", "R$ 0,00", COR_RECEITA, 0
        )
        self.card_despesas, _ = self._criar_card(
            self.frame_cards, "Despesas", "R$ 0,00", COR_DESPESA, 1
        )
        self.card_movimentacoes, _ = self._criar_card(
            self.frame_cards, "Registros", "0", COR_NEUTRO, 2
        )

        self.frame_secao_grafico = ctk.CTkFrame(
            container,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        self.frame_secao_grafico.pack(fill="x", padx=padx, pady=(0, 20))

        ctk.CTkLabel(
            self.frame_secao_grafico,
            text="Receitas x Despesas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=20, pady=(18, 2))

        ctk.CTkLabel(
            self.frame_secao_grafico,
            text="Distribuição do período",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.frame_barras = ctk.CTkFrame(
            self.frame_secao_grafico, fg_color="transparent"
        )
        self.frame_barras.pack(fill="x", padx=20, pady=(0, 20))

        self.frame_secao_recentes = ctk.CTkFrame(
            container,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        self.frame_secao_recentes.pack(fill="x", padx=padx, pady=(0, 28))

        ctk.CTkLabel(
            self.frame_secao_recentes,
            text="Movimentações Recentes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        self.frame_lista = ctk.CTkFrame(
            self.frame_secao_recentes, fg_color="transparent"
        )
        self.frame_lista.pack(fill="x", padx=16, pady=(0, 16))

    def _criar_card_destaque(self, parent, padx):
        """Card principal com saldo em destaque."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        card.pack(fill="x", padx=padx, pady=(0, 14))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=22)

        ctk.CTkLabel(
            inner,
            text="Saldo atual",
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
            anchor="w",
        ).pack(anchor="w")

        lbl_saldo = ctk.CTkLabel(
            inner,
            text="R$ 0,00",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=COR_SALDO_POS,
            anchor="w",
        )
        lbl_saldo.pack(anchor="w", pady=(6, 0))

        return lbl_saldo

    def _criar_card(self, parent, titulo, valor, cor, coluna):
        """Cria card compacto de resumo."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        card.grid(row=0, column=coluna, padx=4, pady=2, sticky="nsew")

        faixa = ctk.CTkFrame(card, height=3, corner_radius=0, fg_color=cor)
        faixa.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            inner,
            text=titulo,
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_SEC,
            anchor="w",
        ).pack(anchor="w")

        lbl_valor = ctk.CTkLabel(
            inner,
            text=valor,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=cor,
            anchor="w",
        )
        lbl_valor.pack(anchor="w", pady=(6, 0))

        return lbl_valor, card

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _widget_valido(self, widget):
        try:
            return widget.winfo_exists()
        except Exception:
            return False

    def _atualizar_cards(self, resumo, total_mov):
        self.card_saldo.configure(text=self._formatar_moeda(resumo["saldo"]))
        self.card_receitas.configure(text=self._formatar_moeda(resumo["receitas"]))
        self.card_despesas.configure(text=self._formatar_moeda(resumo["despesas"]))

        texto_registros = str(total_mov)
        self.card_movimentacoes.configure(text=texto_registros)

        cor_saldo = COR_SALDO_POS if resumo["saldo"] >= 0 else COR_SALDO_NEG
        self.card_saldo.configure(text_color=cor_saldo)
        self.card_receitas.configure(text_color=COR_RECEITA)
        self.card_despesas.configure(text_color=COR_DESPESA)
        self.card_movimentacoes.configure(text_color=COR_NEUTRO)

    def _limpar_barras(self):
        for widget in self.frame_barras.winfo_children():
            widget.destroy()

    def _criar_barra(self, parent, titulo, valor, max_valor, cor):
        """Barra horizontal nativa — visual limpo sem matplotlib."""
        bloco = ctk.CTkFrame(parent, fg_color="transparent")
        bloco.pack(fill="x", pady=8)

        linha_topo = ctk.CTkFrame(bloco, fg_color="transparent")
        linha_topo.pack(fill="x")

        ctk.CTkLabel(
            linha_topo,
            text=titulo,
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO_SEC,
        ).pack(side="left")

        ctk.CTkLabel(
            linha_topo,
            text=self._formatar_moeda(valor),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=cor,
        ).pack(side="right")

        proporcao = valor / max_valor if max_valor > 0 else 0
        barra = ctk.CTkProgressBar(
            bloco,
            height=6,
            corner_radius=3,
            progress_color=cor,
            fg_color=COR_BARRA_FUNDO,
            border_width=0,
        )
        barra.set(min(proporcao, 1.0))
        barra.pack(fill="x", pady=(8, 0))

    def _atualizar_comparativo(self, resumo):
        self._limpar_barras()

        receitas = resumo["receitas"]
        despesas = resumo["despesas"]

        if receitas == 0 and despesas == 0:
            ctk.CTkLabel(
                self.frame_barras,
                text="Nenhuma movimentação para exibir.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=12)
            return

        max_valor = max(receitas, despesas, 1)
        self._criar_barra(self.frame_barras, "Receitas", receitas, max_valor, COR_RECEITA)
        self._criar_barra(self.frame_barras, "Despesas", despesas, max_valor, COR_DESPESA)

    def _atualizar_lista_recentes(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        movimentacoes = listar_movimentacoes(self.usuario["id"], limite=6)

        if not movimentacoes:
            ctk.CTkLabel(
                self.frame_lista,
                text="Nenhuma movimentação cadastrada ainda.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=24)
            return

        for mov in movimentacoes:
            _, descricao, valor, categoria, tipo, data = mov
            self._adicionar_item_lista(descricao, valor, categoria, tipo, data)

    def atualizar(self):
        if not self._widget_valido(self):
            return

        resumo = calcular_resumo(self.usuario["id"])
        total_mov = contar_movimentacoes(self.usuario["id"])

        self._atualizar_cards(resumo, total_mov)
        self._atualizar_comparativo(resumo)

        if self._widget_valido(self.frame_lista):
            self._atualizar_lista_recentes()

    def _adicionar_item_lista(self, descricao, valor, categoria, tipo, data):
        cor = COR_RECEITA if tipo == "receita" else COR_DESPESA
        sinal = "+" if tipo == "receita" else "−"

        item = ctk.CTkFrame(
            self.frame_lista,
            corner_radius=8,
            height=52,
            fg_color="#1f1f23",
            border_width=0,
        )
        item.pack(fill="x", pady=3)
        item.pack_propagate(False)

        faixa = ctk.CTkFrame(item, width=3, corner_radius=0, fg_color=cor)
        faixa.pack(side="left", fill="y")
        faixa.pack_propagate(False)

        conteudo = ctk.CTkFrame(item, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=(12, 8), pady=8)

        linha_topo = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_topo.pack(fill="x")

        ctk.CTkLabel(
            linha_topo,
            text=descricao,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COR_TEXTO,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            linha_topo,
            text=f"{sinal} {self._formatar_moeda(valor)}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=cor,
        ).pack(side="right")

        ctk.CTkLabel(
            conteudo,
            text=f"{categoria}  ·  {data}",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
