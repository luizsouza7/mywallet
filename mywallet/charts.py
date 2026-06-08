"""
Tela de gráficos financeiros com Matplotlib.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import calcular_resumo, obter_gastos_por_categoria, obter_evolucao_financeira
from periodo import formatar_intervalo
from theme import (
    COR_ACENTO,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_MUTED,
    COR_TEXTO_SEC,
    ESPACO_LG,
    ESPACO_MD,
    RAIO_CARD,
)


class TelaGraficos(ctk.CTkFrame):
    """Exibe gráficos de barras e linha integrados à interface."""

    def __init__(self, master, usuario, obter_periodo=None):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self.obter_periodo = obter_periodo
        self.canvas_widgets = []
        self._job_render = None
        self.lbl_subtitulo = None
        self._criar_interface()

    def _periodo(self):
        if self.obter_periodo:
            p = self.obter_periodo()
            return p.get("data_inicio"), p.get("data_fim")
        return None, None

    def _criar_interface(self):
        ctk.CTkLabel(
            self,
            text="Gráficos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=ESPACO_LG, pady=(ESPACO_MD, 4))

        self.lbl_subtitulo = ctk.CTkLabel(
            self,
            text="Análise visual das suas finanças",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_SEC,
        )
        self.lbl_subtitulo.pack(anchor="w", padx=ESPACO_LG, pady=(0, ESPACO_MD))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=ESPACO_LG, pady=(0, ESPACO_MD))

    def _cancelar_render_agendado(self):
        if self._job_render is not None:
            try:
                self.after_cancel(self._job_render)
            except Exception:
                pass
            self._job_render = None

    def _limpar_graficos(self):
        self._cancelar_render_agendado()
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.canvas_widgets = []
        plt.close("all")

    def _widget_valido(self, widget):
        try:
            return widget.winfo_exists()
        except Exception:
            return False

    def atualizar(self):
        if not self._widget_valido(self):
            return

        self._limpar_graficos()

        data_inicio, data_fim = self._periodo()
        if self.lbl_subtitulo:
            self.lbl_subtitulo.configure(
                text=f"Período: {formatar_intervalo(data_inicio, data_fim)}"
            )

        resumo = calcular_resumo(self.usuario["id"], data_inicio, data_fim)
        gastos = obter_gastos_por_categoria(self.usuario["id"], data_inicio, data_fim)
        datas, saldos = obter_evolucao_financeira(self.usuario["id"], data_inicio, data_fim)

        if resumo["receitas"] == 0 and resumo["despesas"] == 0:
            ctk.CTkLabel(
                self.scroll,
                text="Cadastre movimentações para visualizar os gráficos.",
                text_color=COR_TEXTO_MUTED,
                font=ctk.CTkFont(size=14),
            ).pack(pady=60)
            return

        self._job_render = self.after(
            200,
            lambda: self._renderizar_graficos_seguro(resumo, gastos, datas, saldos),
        )

    def _renderizar_graficos_seguro(self, resumo, gastos, datas, saldos):
        self._job_render = None
        if not self._widget_valido(self) or not self._widget_valido(self.scroll):
            return
        self._renderizar_graficos(resumo, gastos, datas, saldos)

    def _renderizar_graficos(self, resumo, gastos, datas, saldos):
        self._grafico_receitas_despesas(resumo)
        if gastos:
            self._grafico_gastos_categoria(gastos)
        if datas:
            self._grafico_evolucao(datas, saldos)

    def _estilo_figure(self, altura=2.4):
        fig = Figure(figsize=(6.5, altura), dpi=100, facecolor=COR_FUNDO_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_FUNDO_CARD)
        ax.tick_params(colors=COR_TEXTO_MUTED, labelsize=8, length=0, pad=4)
        ax.xaxis.label.set_color(COR_TEXTO_MUTED)
        ax.yaxis.label.set_color(COR_TEXTO_MUTED)
        ax.title.set_color(COR_TEXTO)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="y", linestyle="-", alpha=0.04, color=COR_TEXTO_MUTED)
        ax.set_axisbelow(True)
        return fig, ax

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _embutir_grafico(self, fig, titulo):
        if not self._widget_valido(self.scroll):
            plt.close(fig)
            return

        frame = ctk.CTkFrame(
            self.scroll,
            corner_radius=RAIO_CARD,
            fg_color=COR_FUNDO_CARD,
            border_width=0,
        )
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(anchor="w", padx=ESPACO_MD, pady=(ESPACO_MD, 8))

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=COR_FUNDO_CARD, highlightthickness=0, bd=0)
        widget.pack(fill="x", padx=ESPACO_MD, pady=(0, ESPACO_MD))
        self.canvas_widgets.append(canvas)

    def _grafico_receitas_despesas(self, resumo):
        fig, ax = self._estilo_figure(2.2)

        categorias = ["Receitas", "Despesas"]
        valores = [resumo["receitas"], resumo["despesas"]]
        cores = [COR_RECEITA, COR_DESPESA]

        barras = ax.bar(
            categorias, valores, color=cores, width=0.38,
            edgecolor="none", alpha=0.85, zorder=3,
        )

        margem = max(valores) * 0.04 if max(valores) > 0 else 0.5
        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + margem,
                self._formatar_moeda(valor),
                ha="center", va="bottom",
                color=COR_TEXTO_SEC, fontsize=8,
            )

        ax.set_title("Receitas x Despesas", fontsize=11, pad=8, color=COR_TEXTO)
        fig.tight_layout(pad=1.2)
        self._embutir_grafico(fig, "Comparativo")

    def _grafico_gastos_categoria(self, gastos):
        fig, ax = self._estilo_figure(2.0)

        categorias = [g[0] for g in gastos]
        valores = [g[1] for g in gastos]

        cores = [COR_DESPESA if i == 0 else COR_TEXTO_MUTED for i in range(len(categorias))]
        ax.barh(categorias, valores, color=cores, edgecolor="none", height=0.5, alpha=0.8)

        ax.set_title("Gastos por categoria", fontsize=11, pad=8, color=COR_TEXTO)
        fig.tight_layout(pad=1.2)
        self._embutir_grafico(fig, "Despesas por categoria")

    def _grafico_evolucao(self, datas, saldos):
        fig, ax = self._estilo_figure(2.2)

        indices = list(range(len(datas)))
        ax.plot(
            indices, saldos, color=COR_ACENTO,
            linewidth=2, marker="o", markersize=3, zorder=3,
        )
        ax.fill_between(indices, saldos, alpha=0.08, color=COR_ACENTO)

        ax.set_xticks(indices)
        if len(datas) > 5:
            ax.set_xticklabels(datas, rotation=45, ha="right", fontsize=7)
        else:
            ax.set_xticklabels(datas, fontsize=8)

        ax.axhline(y=0, color=COR_TEXTO_MUTED, linestyle="--", linewidth=0.4, alpha=0.3)
        ax.set_title("Evolução do saldo", fontsize=11, pad=8, color=COR_TEXTO)
        fig.tight_layout(pad=1.2)
        self._embutir_grafico(fig, "Evolução financeira")
