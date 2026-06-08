"""
Utilitários e widget de filtro de período para o MyWallet.
"""

from datetime import datetime, timedelta

import customtkinter as ctk

from theme import (
    COR_ACENTO,
    COR_BOTAO_PRIMARIO,
    COR_BOTAO_PRIMARIO_HOVER,
    COR_DESPESA,
    COR_FUNDO_CARD,
    COR_FUNDO_ITEM,
    COR_RECEITA,
    COR_TEXTO,
    COR_TEXTO_MUTED,
    COR_TEXTO_SEC,
    ESPACO_SM,
    RAIO_BOTAO,
)

OPCOES_PERIODO = [
    "Hoje",
    "Últimos 7 dias",
    "Últimos 30 dias",
    "Últimos 90 dias",
    "Este mês",
    "Este ano",
    "Personalizado",
]

PERIODO_PADRAO = "Últimos 30 dias"


def calcular_periodo(preset, data_inicio_custom=None, data_fim_custom=None):
    """Retorna (data_inicio, data_fim) no formato YYYY-MM-DD."""
    hoje = datetime.now().date()

    if preset == "Personalizado":
        if data_inicio_custom and data_fim_custom:
            return data_inicio_custom, data_fim_custom
        return None, None

    if preset == "Hoje":
        return hoje.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    if preset == "Últimos 7 dias":
        inicio = hoje - timedelta(days=6)
        return inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    if preset == "Últimos 30 dias":
        inicio = hoje - timedelta(days=29)
        return inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    if preset == "Últimos 90 dias":
        inicio = hoje - timedelta(days=89)
        return inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    if preset == "Este mês":
        inicio = hoje.replace(day=1)
        return inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    if preset == "Este ano":
        inicio = hoje.replace(month=1, day=1)
        return inicio.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")

    return None, None


def periodo_anterior(data_inicio, data_fim):
    """Retorna o período imediatamente anterior com a mesma duração."""
    d1 = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    d2 = datetime.strptime(data_fim, "%Y-%m-%d").date()
    dias = (d2 - d1).days + 1
    fim_ant = d1 - timedelta(days=1)
    inicio_ant = fim_ant - timedelta(days=dias - 1)
    return inicio_ant.strftime("%Y-%m-%d"), fim_ant.strftime("%Y-%m-%d")


def formatar_variacao(atual, anterior):
    """
    Retorna (texto, cor) para indicador de comparação com período anterior.
    Ex: ('↑ 12% vs período anterior', COR_RECEITA)
    """
    if anterior == 0:
        if atual == 0:
            return "— sem dados anteriores", COR_TEXTO_MUTED
        return "↑ 100% vs período anterior", COR_RECEITA

    pct = ((atual - anterior) / abs(anterior)) * 100
    pct_abs = abs(round(pct))

    if pct > 0:
        return f"↑ {pct_abs}% vs período anterior", COR_RECEITA
    if pct < 0:
        return f"↓ {pct_abs}% vs período anterior", COR_DESPESA
    return "— sem variação", COR_TEXTO_MUTED


def formatar_intervalo(data_inicio, data_fim):
    """Formata intervalo para exibição."""
    if not data_inicio or not data_fim:
        return "Todo o período"
    d1 = datetime.strptime(data_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
    d2 = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")
    if d1 == d2:
        return d1
    return f"{d1} — {d2}"


class BarraFiltroPeriodo(ctk.CTkFrame):
    """Barra de filtro global de período no topo da aplicação."""

    def __init__(self, master, ao_mudar):
        super().__init__(master, fg_color=COR_FUNDO_CARD, corner_radius=0, height=52)
        self.ao_mudar = ao_mudar
        self.preset_atual = PERIODO_PADRAO
        self.data_inicio = None
        self.data_fim = None
        self._criar_interface()
        self.preset_atual = PERIODO_PADRAO
        self.data_inicio, self.data_fim = calcular_periodo(PERIODO_PADRAO)
        self.lbl_intervalo.configure(
            text=formatar_intervalo(self.data_inicio, self.data_fim)
        )

    def _criar_interface(self):
        self.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(
            self,
            text="Período",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COR_TEXTO_SEC,
        ).grid(row=0, column=0, padx=(ESPACO_SM, 8), pady=10)

        self.combo_periodo = ctk.CTkComboBox(
            self,
            values=OPCOES_PERIODO,
            width=160,
            height=34,
            corner_radius=RAIO_BOTAO,
            state="readonly",
            command=self._ao_selecionar_preset,
        )
        self.combo_periodo.set(PERIODO_PADRAO)
        self.combo_periodo.grid(row=0, column=1, padx=(0, 12), pady=10)

        self.frame_personalizado = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(
            self.frame_personalizado,
            text="De",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
        ).pack(side="left", padx=(0, 4))

        self.entry_inicio = ctk.CTkEntry(
            self.frame_personalizado,
            width=110,
            height=34,
            corner_radius=RAIO_BOTAO,
            placeholder_text="AAAA-MM-DD",
        )
        self.entry_inicio.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            self.frame_personalizado,
            text="Até",
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO_MUTED,
        ).pack(side="left", padx=(0, 4))

        self.entry_fim = ctk.CTkEntry(
            self.frame_personalizado,
            width=110,
            height=34,
            corner_radius=RAIO_BOTAO,
            placeholder_text="AAAA-MM-DD",
        )
        self.entry_fim.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            self.frame_personalizado,
            text="Aplicar",
            width=80,
            height=34,
            corner_radius=RAIO_BOTAO,
            fg_color=COR_BOTAO_PRIMARIO,
            hover_color=COR_BOTAO_PRIMARIO_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._aplicar_personalizado,
        ).pack(side="left")

        self.lbl_intervalo = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COR_ACENTO,
            anchor="e",
        )
        self.lbl_intervalo.grid(row=0, column=6, padx=ESPACO_SM, pady=10, sticky="e")

    def _ao_selecionar_preset(self, valor):
        if valor == "Personalizado":
            self.frame_personalizado.grid(row=0, column=2, columnspan=3, padx=(0, 8), pady=10, sticky="w")
            hoje = datetime.now().strftime("%Y-%m-%d")
            inicio = (datetime.now() - timedelta(days=29)).strftime("%Y-%m-%d")
            self.entry_inicio.delete(0, "end")
            self.entry_inicio.insert(0, inicio)
            self.entry_fim.delete(0, "end")
            self.entry_fim.insert(0, hoje)
            self.preset_atual = valor
            return

        self.frame_personalizado.grid_forget()
        self._aplicar_preset(valor)

    def _aplicar_personalizado(self):
        inicio = self.entry_inicio.get().strip()
        fim = self.entry_fim.get().strip()
        try:
            datetime.strptime(inicio, "%Y-%m-%d")
            datetime.strptime(fim, "%Y-%m-%d")
        except ValueError:
            return
        if inicio > fim:
            inicio, fim = fim, inicio
        self.preset_atual = "Personalizado"
        self.data_inicio = inicio
        self.data_fim = fim
        self._notificar()

    def _aplicar_preset(self, preset):
        self.preset_atual = preset
        self.data_inicio, self.data_fim = calcular_periodo(preset)
        self._notificar()

    def _notificar(self):
        self.lbl_intervalo.configure(
            text=formatar_intervalo(self.data_inicio, self.data_fim)
        )
        if self.ao_mudar:
            self.ao_mudar(self.obter())

    def obter(self):
        return {
            "preset": self.preset_atual,
            "data_inicio": self.data_inicio,
            "data_fim": self.data_fim,
        }
