"""
Tela principal (Dashboard) do MyWallet.
Exibe saldo, totais e movimentações recentes.
"""

import customtkinter as ctk
from database import calcular_resumo, listar_movimentacoes


class TelaDashboard(ctk.CTkFrame):
    """Painel inicial com resumo financeiro."""

    def __init__(self, master, usuario):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self._criar_interface()

    def _criar_interface(self):
        """Monta layout do dashboard."""
        # Título
        ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            self,
            text=f"Olá, {self.usuario['nome']}! 👋",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(anchor="w", padx=30, pady=(0, 20))

        # Cards de resumo
        self.frame_cards = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cards.pack(fill="x", padx=30, pady=(0, 20))

        self.card_saldo = self._criar_card(self.frame_cards, "Saldo Atual", "R$ 0,00", "#22c55e", 0)
        self.card_receitas = self._criar_card(self.frame_cards, "Total Recebido", "R$ 0,00", "#3b82f6", 1)
        self.card_despesas = self._criar_card(self.frame_cards, "Total Gasto", "R$ 0,00", "#ef4444", 2)

        # Movimentações recentes
        ctk.CTkLabel(
            self,
            text="Movimentações Recentes",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=30, pady=(10, 10))

        self.frame_lista = ctk.CTkScrollableFrame(self, height=280)
        self.frame_lista.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def _criar_card(self, parent, titulo, valor, cor, coluna):
        """Cria um card de resumo financeiro."""
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color="#333")
        card.grid(row=0, column=coluna, padx=8, pady=5, sticky="nsew")
        parent.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(
            card, text=titulo, font=ctk.CTkFont(size=13), text_color="gray"
        ).pack(padx=20, pady=(18, 0))

        lbl_valor = ctk.CTkLabel(
            card, text=valor, font=ctk.CTkFont(size=22, weight="bold"), text_color=cor
        )
        lbl_valor.pack(padx=20, pady=(5, 18))

        return lbl_valor

    def _formatar_moeda(self, valor):
        """Formata número como moeda brasileira."""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _widget_valido(self, widget):
        """Verifica se o widget ainda existe."""
        try:
            return widget.winfo_exists()
        except Exception:
            return False

    def atualizar(self):
        """Recarrega dados do banco e atualiza a interface."""
        if not self._widget_valido(self) or not self._widget_valido(self.frame_lista):
            return

        resumo = calcular_resumo(self.usuario["id"])

        self.card_saldo.configure(text=self._formatar_moeda(resumo["saldo"]))
        self.card_receitas.configure(text=self._formatar_moeda(resumo["receitas"]))
        self.card_despesas.configure(text=self._formatar_moeda(resumo["despesas"]))

        # Cor do saldo conforme positivo ou negativo
        cor_saldo = "#22c55e" if resumo["saldo"] >= 0 else "#ef4444"
        self.card_saldo.configure(text_color=cor_saldo)

        # Lista de movimentações recentes
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        movimentacoes = listar_movimentacoes(self.usuario["id"], limite=8)

        if not movimentacoes:
            ctk.CTkLabel(
                self.frame_lista,
                text="Nenhuma movimentação cadastrada ainda.",
                text_color="gray",
            ).pack(pady=40)
            return

        for mov in movimentacoes:
            mov_id, descricao, valor, categoria, tipo, data = mov
            self._adicionar_item_lista(descricao, valor, categoria, tipo, data)

    def _adicionar_item_lista(self, descricao, valor, categoria, tipo, data):
        """Adiciona uma linha na lista de movimentações recentes."""
        item = ctk.CTkFrame(self.frame_lista, corner_radius=8, height=55)
        item.pack(fill="x", pady=4)
        item.pack_propagate(False)

        icone = "↑" if tipo == "receita" else "↓"
        cor = "#22c55e" if tipo == "receita" else "#ef4444"
        sinal = "+" if tipo == "receita" else "-"

        ctk.CTkLabel(
            item, text=icone, font=ctk.CTkFont(size=18), text_color=cor, width=30
        ).pack(side="left", padx=(15, 5))

        info = ctk.CTkFrame(item, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=8)

        ctk.CTkLabel(
            info, text=descricao, font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=f"{categoria} • {data}", font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            item,
            text=f"{sinal} {self._formatar_moeda(valor)}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=cor,
        ).pack(side="right", padx=15)
