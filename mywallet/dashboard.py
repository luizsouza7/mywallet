"""
Tela principal (Dashboard) do MyWallet.
Exibe saldo, totais, gráfico resumido e movimentações recentes.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import calcular_resumo, contar_movimentacoes, listar_movimentacoes


class TelaDashboard(ctk.CTkFrame):
    """Painel inicial com resumo financeiro."""

    COR_RECEITA = "#60a5fa"
    COR_DESPESA = "#f87171"
    COR_SALDO_POS = "#4ade80"
    COR_SALDO_NEG = "#f87171"
    COR_NEUTRO = "#a1a1aa"
    COR_FUNDO = "#2b2b2b"
    COR_BORDA = "#3f3f46"
    COR_TEXTO_SEC = "#71717a"
    COR_TEXTO = "#e4e4e7"

    def __init__(self, master, usuario):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self._canvas_grafico = None
        self._criar_interface()

    def _criar_interface(self):
        """Monta layout: cards → gráfico → movimentações recentes."""
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        padx = 36

        ctk.CTkLabel(
            container,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COR_TEXTO,
        ).pack(anchor="w", padx=padx, pady=(24, 4))

        ctk.CTkLabel(
            container,
            text=f"Olá, {self.usuario['nome']}",
            font=ctk.CTkFont(size=13),
            text_color=self.COR_TEXTO_SEC,
        ).pack(anchor="w", padx=padx, pady=(0, 24))

        self.frame_cards = ctk.CTkFrame(container, fg_color="transparent")
        self.frame_cards.pack(fill="x", padx=padx, pady=(0, 20))
        for col in range(4):
            self.frame_cards.grid_columnconfigure(col, weight=1)

        self.card_saldo, _ = self._criar_card(
            self.frame_cards, "Saldo Atual", "R$ 0,00", self.COR_SALDO_POS, 0
        )
        self.card_receitas, _ = self._criar_card(
            self.frame_cards, "Total Recebido", "R$ 0,00", self.COR_RECEITA, 1
        )
        self.card_despesas, _ = self._criar_card(
            self.frame_cards, "Total Gasto", "R$ 0,00", self.COR_DESPESA, 2
        )
        self.card_movimentacoes, _ = self._criar_card(
            self.frame_cards, "Movimentações", "0 registros", self.COR_NEUTRO, 3
        )

        self.frame_secao_grafico = ctk.CTkFrame(
            container,
            corner_radius=14,
            fg_color=self.COR_FUNDO,
            border_width=1,
            border_color=self.COR_BORDA,
        )
        self.frame_secao_grafico.pack(fill="x", padx=padx, pady=(0, 20))

        ctk.CTkLabel(
            self.frame_secao_grafico,
            text="Resumo Financeiro",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COR_TEXTO,
        ).pack(anchor="w", padx=22, pady=(18, 4))

        ctk.CTkLabel(
            self.frame_secao_grafico,
            text="Comparativo entre receitas e despesas",
            font=ctk.CTkFont(size=11),
            text_color=self.COR_TEXTO_SEC,
        ).pack(anchor="w", padx=22, pady=(0, 6))

        self.frame_grafico = ctk.CTkFrame(
            self.frame_secao_grafico, fg_color=self.COR_FUNDO, corner_radius=0
        )
        self.frame_grafico.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            container,
            text="Movimentações Recentes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COR_TEXTO,
        ).pack(anchor="w", padx=padx, pady=(0, 12))

        self.frame_lista = ctk.CTkScrollableFrame(
            container, height=240, fg_color="transparent", border_width=0
        )
        self.frame_lista.pack(fill="x", padx=padx, pady=(0, 28))

    def _criar_card(self, parent, titulo, valor, cor, coluna):
        """Cria card de resumo elegante e compacto."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            fg_color=self.COR_FUNDO,
            border_width=1,
            border_color=self.COR_BORDA,
        )
        card.grid(row=0, column=coluna, padx=5, pady=2, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            inner,
            text=titulo.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.COR_TEXTO_SEC,
            anchor="w",
        ).pack(anchor="w")

        lbl_valor = ctk.CTkLabel(
            inner,
            text=valor,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=cor,
            anchor="w",
        )
        lbl_valor.pack(anchor="w", pady=(8, 0))

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

        texto_registros = f"{total_mov} registro" if total_mov == 1 else f"{total_mov} registros"
        self.card_movimentacoes.configure(text=texto_registros)

        cor_saldo = self.COR_SALDO_POS if resumo["saldo"] >= 0 else self.COR_SALDO_NEG
        self.card_saldo.configure(text_color=cor_saldo)
        self.card_receitas.configure(text_color=self.COR_RECEITA)
        self.card_despesas.configure(text_color=self.COR_DESPESA)
        self.card_movimentacoes.configure(text_color=self.COR_NEUTRO)

    def _limpar_grafico(self):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        if self._canvas_grafico is not None:
            plt.close(self._canvas_grafico.figure)
            self._canvas_grafico = None

    def _atualizar_grafico_resumo(self, resumo):
        self._limpar_grafico()

        receitas = resumo["receitas"]
        despesas = resumo["despesas"]

        if receitas == 0 and despesas == 0:
            ctk.CTkLabel(
                self.frame_grafico,
                text="Nenhuma movimentação para exibir.",
                text_color=self.COR_TEXTO_SEC,
                font=ctk.CTkFont(size=12),
            ).pack(pady=28)
            return

        cor_fundo = self.COR_FUNDO
        fig = Figure(figsize=(7.2, 2.0), dpi=100, facecolor=cor_fundo)
        ax = fig.add_subplot(111)
        ax.set_facecolor(cor_fundo)

        categorias = ["Receitas", "Despesas"]
        valores = [receitas, despesas]
        cores = ["#4ade80", self.COR_DESPESA]

        barras = ax.barh(categorias, valores, color=cores, height=0.38, edgecolor="none", alpha=0.88)

        max_valor = max(valores) if max(valores) > 0 else 1
        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_width() + max_valor * 0.015,
                barra.get_y() + barra.get_height() / 2,
                self._formatar_moeda(valor),
                va="center",
                ha="left",
                color="#d4d4d8",
                fontsize=9,
            )

        ax.set_xlim(0, max_valor * 1.22)
        ax.tick_params(axis="x", colors="#71717a", labelsize=8, length=0)
        ax.tick_params(axis="y", colors="#d4d4d8", labelsize=10, length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="x", linestyle="-", alpha=0.12, color="#71717a", linewidth=0.8)
        ax.set_axisbelow(True)
        fig.subplots_adjust(left=0.12, right=0.98, top=0.95, bottom=0.18)

        self._canvas_grafico = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self._canvas_grafico.draw()
        widget = self._canvas_grafico.get_tk_widget()
        widget.configure(bg=cor_fundo, highlightthickness=0, bd=0)
        widget.pack(fill="x", padx=4, pady=4)

    def _atualizar_lista_recentes(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        movimentacoes = listar_movimentacoes(self.usuario["id"], limite=8)

        if not movimentacoes:
            ctk.CTkLabel(
                self.frame_lista,
                text="Nenhuma movimentação cadastrada ainda.",
                text_color=self.COR_TEXTO_SEC,
                font=ctk.CTkFont(size=12),
            ).pack(pady=36)
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
        self._atualizar_grafico_resumo(resumo)

        if self._widget_valido(self.frame_lista):
            self._atualizar_lista_recentes()

    def _adicionar_item_lista(self, descricao, valor, categoria, tipo, data):
        cor = self.COR_RECEITA if tipo == "receita" else self.COR_DESPESA
        sinal = "+" if tipo == "receita" else "−"

        item = ctk.CTkFrame(
            self.frame_lista,
            corner_radius=10,
            height=58,
            fg_color=self.COR_FUNDO,
            border_width=1,
            border_color=self.COR_BORDA,
        )
        item.pack(fill="x", pady=5)
        item.pack_propagate(False)

        faixa = ctk.CTkFrame(item, width=3, corner_radius=0, fg_color=cor)
        faixa.pack(side="left", fill="y")
        faixa.pack_propagate(False)

        conteudo = ctk.CTkFrame(item, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=(14, 8), pady=10)

        linha_topo = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_topo.pack(fill="x")

        ctk.CTkLabel(
            linha_topo,
            text=descricao,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.COR_TEXTO,
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
            text_color=self.COR_TEXTO_SEC,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
