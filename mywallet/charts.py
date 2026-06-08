"""
Tela de gráficos financeiros com Matplotlib.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from database import calcular_resumo, obter_gastos_por_categoria, obter_evolucao_financeira
from theme import (
    COR_BORDA,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_MUTED,
)


class TelaGraficos(ctk.CTkFrame):
    """Exibe gráficos de barras e linha integrados à interface."""

    def __init__(self, master, usuario):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self.canvas_widgets = []
        self._job_render = None
        self._criar_interface()

    def _criar_interface(self):
        """Monta área dos gráficos."""
        ctk.CTkLabel(
            self,
            text="Gráficos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=32, pady=(28, 16))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=32, pady=(0, 24))

    def _cancelar_render_agendado(self):
        """Cancela renderização pendente para evitar erro ao trocar de tela."""
        if self._job_render is not None:
            try:
                self.after_cancel(self._job_render)
            except Exception:
                pass
            self._job_render = None

    def _limpar_graficos(self):
        """Remove gráficos anteriores da tela."""
        self._cancelar_render_agendado()
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.canvas_widgets = []
        plt.close("all")

    def _widget_valido(self, widget):
        """Verifica se o widget ainda existe antes de usá-lo."""
        try:
            return widget.winfo_exists()
        except Exception:
            return False

    def atualizar(self):
        """Atualiza todos os gráficos com dados do banco."""
        if not self._widget_valido(self):
            return

        self._limpar_graficos()

        resumo = calcular_resumo(self.usuario["id"])
        gastos = obter_gastos_por_categoria(self.usuario["id"])
        datas, saldos = obter_evolucao_financeira(self.usuario["id"])

        if resumo["receitas"] == 0 and resumo["despesas"] == 0:
            ctk.CTkLabel(
                self.scroll,
                text="Cadastre movimentações para visualizar os gráficos.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=14),
            ).pack(pady=60)
            return

        # Renderiza após a tela carregar; cancela se o usuário sair antes
        self._job_render = self.after(
            200,
            lambda: self._renderizar_graficos_seguro(resumo, gastos, datas, saldos),
        )

    def _renderizar_graficos_seguro(self, resumo, gastos, datas, saldos):
        """Só desenha gráficos se a tela ainda estiver visível."""
        self._job_render = None

        if not self._widget_valido(self) or not self._widget_valido(self.scroll):
            return

        self._renderizar_graficos(resumo, gastos, datas, saldos)

    def _renderizar_graficos(self, resumo, gastos, datas, saldos):
        """Desenha os gráficos na interface."""
        self._grafico_receitas_despesas(resumo)

        if gastos:
            self._grafico_gastos_categoria(gastos)

        if datas:
            self._grafico_evolucao(datas, saldos)

    def _estilo_figure(self):
        """Configura estilo escuro para os gráficos."""
        fig = Figure(figsize=(7, 3.2), dpi=100, facecolor=COR_FUNDO_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_FUNDO_CARD)
        ax.tick_params(colors=COR_TEXTO_MUTED, labelsize=9, length=0)
        ax.xaxis.label.set_color(COR_TEXTO_MUTED)
        ax.yaxis.label.set_color(COR_TEXTO_MUTED)
        ax.title.set_color(COR_TEXTO)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="y", linestyle="-", alpha=0.08, color=COR_TEXTO_MUTED)
        ax.set_axisbelow(True)
        return fig, ax

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _embutir_grafico(self, fig, titulo_frame):
        """Coloca o gráfico matplotlib dentro do CustomTkinter."""
        if not self._widget_valido(self.scroll):
            plt.close(fig)
            return

        frame = ctk.CTkFrame(
            self.scroll,
            corner_radius=12,
            fg_color=COR_FUNDO_CARD,
            border_width=1,
            border_color=COR_BORDA,
        )
        frame.pack(fill="x", pady=8)

        ctk.CTkLabel(
            frame,
            text=titulo_frame,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=18, pady=(16, 4))

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=COR_FUNDO_CARD, highlightthickness=0, bd=0)
        widget.pack(fill="x", padx=12, pady=(0, 14))
        self.canvas_widgets.append(canvas)

    def _grafico_receitas_despesas(self, resumo):
        """Gráfico de barras comparando receitas e despesas."""
        fig, ax = self._estilo_figure()

        categorias = ["Receitas", "Despesas"]
        valores = [resumo["receitas"], resumo["despesas"]]
        cores = [COR_RECEITA, COR_DESPESA]

        barras = ax.bar(categorias, valores, color=cores, width=0.45, edgecolor="none")

        margem = max(valores) * 0.05 if max(valores) > 0 else 0.5
        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + margem,
                self._formatar_moeda(valor),
                ha="center",
                va="bottom",
                color=COR_TEXTO,
                fontsize=9,
            )

        ax.set_ylabel("Valor (R$)")
        ax.set_title("Receitas x Despesas", fontsize=12, pad=10)
        fig.tight_layout()
        self._embutir_grafico(fig, "Comparativo: Receitas e Despesas")

    def _grafico_gastos_categoria(self, gastos):
        """Gráfico de barras com gastos por categoria."""
        fig, ax = self._estilo_figure()

        categorias = [g[0] for g in gastos]
        valores = [g[1] for g in gastos]

        cores = plt.cm.Set2(range(len(categorias)))
        ax.barh(categorias, valores, color=cores, edgecolor="none", height=0.55)

        ax.set_xlabel("Valor (R$)")
        ax.set_title("Gastos por Categoria", fontsize=12, pad=10)
        fig.tight_layout()
        self._embutir_grafico(fig, "Despesas por Categoria")

    def _grafico_evolucao(self, datas, saldos):
        """Gráfico de linha com evolução do saldo."""
        fig, ax = self._estilo_figure()

        indices = list(range(len(datas)))
        ax.plot(indices, saldos, color=COR_RECEITA, linewidth=2, marker="o", markersize=4)
        ax.fill_between(indices, saldos, alpha=0.12, color=COR_RECEITA)

        ax.set_xticks(indices)
        if len(datas) > 5:
            ax.set_xticklabels(datas, rotation=45, ha="right", fontsize=8)
        else:
            ax.set_xticklabels(datas, fontsize=9)

        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Evolução Financeira", fontsize=12, pad=10)
        ax.axhline(y=0, color=COR_TEXTO_MUTED, linestyle="--", linewidth=0.6, alpha=0.5)
        fig.tight_layout()
        self._embutir_grafico(fig, "Evolução do Saldo ao Longo do Tempo")
