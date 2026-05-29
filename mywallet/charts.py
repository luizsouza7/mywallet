"""
Tela de gráficos financeiros com Matplotlib.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from database import calcular_resumo, obter_gastos_por_categoria, obter_evolucao_financeira


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
            self, text="Gráficos", font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", padx=30, pady=(25, 15))

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))

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
                text_color="gray",
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
        fig = Figure(figsize=(7, 3.5), dpi=100, facecolor="#2b2b2b")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1e1e1e")
        ax.tick_params(colors="white", labelsize=9)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_color("#444")
        return fig, ax

    def _formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _embutir_grafico(self, fig, titulo_frame):
        """Coloca o gráfico matplotlib dentro do CustomTkinter."""
        if not self._widget_valido(self.scroll):
            plt.close(fig)
            return

        frame = ctk.CTkFrame(self.scroll, corner_radius=12)
        frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            frame, text=titulo_frame, font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 5))

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 12))
        self.canvas_widgets.append(canvas)

    def _grafico_receitas_despesas(self, resumo):
        """Gráfico de barras comparando receitas e despesas."""
        fig, ax = self._estilo_figure()

        categorias = ["Receitas", "Despesas"]
        valores = [resumo["receitas"], resumo["despesas"]]
        cores = ["#22c55e", "#ef4444"]

        barras = ax.bar(categorias, valores, color=cores, width=0.5, edgecolor="#333")

        margem = max(valores) * 0.05 if max(valores) > 0 else 0.5
        for barra, valor in zip(barras, valores):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + margem,
                self._formatar_moeda(valor),
                ha="center",
                va="bottom",
                color="white",
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
        ax.barh(categorias, valores, color=cores, edgecolor="#333")

        ax.set_xlabel("Valor (R$)")
        ax.set_title("Gastos por Categoria", fontsize=12, pad=10)
        fig.tight_layout()
        self._embutir_grafico(fig, "Despesas por Categoria")

    def _grafico_evolucao(self, datas, saldos):
        """Gráfico de linha com evolução do saldo."""
        fig, ax = self._estilo_figure()

        indices = list(range(len(datas)))
        ax.plot(indices, saldos, color="#3b82f6", linewidth=2, marker="o", markersize=4)
        ax.fill_between(indices, saldos, alpha=0.15, color="#3b82f6")

        ax.set_xticks(indices)
        if len(datas) > 5:
            ax.set_xticklabels(datas, rotation=45, ha="right", fontsize=8)
        else:
            ax.set_xticklabels(datas, fontsize=9)

        ax.set_ylabel("Saldo (R$)")
        ax.set_title("Evolução Financeira", fontsize=12, pad=10)
        ax.axhline(y=0, color="#666", linestyle="--", linewidth=0.8)
        fig.tight_layout()
        self._embutir_grafico(fig, "Evolução do Saldo ao Longo do Tempo")
