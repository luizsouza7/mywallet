"""Paleta e constantes visuais compartilhadas do MyWallet."""

# Cores principais
COR_FUNDO = "#0F1115"
COR_SIDEBAR = "#131722"
COR_FUNDO_CARD = "#171B26"
COR_FUNDO_CARD_ALT = "#171B26"
COR_FUNDO_ITEM = "#1C2130"
COR_FUNDO_HOVER = "#1E2433"

COR_BORDA = "#252A38"
COR_BORDA_SUAVE = "#1E2433"
COR_HOVER = "#1C2130"
COR_ATIVO = "#1A2744"
COR_ATIVO_BORDA = "#1A2744"

COR_TEXTO = "#FFFFFF"
COR_TEXTO_SEC = "#9AA4B2"
COR_TEXTO_MUTED = "#6B7280"

COR_RECEITA = "#22C55E"
COR_DESPESA = "#EF4444"
COR_SALDO_POS = "#22C55E"
COR_SALDO_NEG = "#EF4444"
COR_ACENTO = "#3B82F6"
COR_ACENTO_SUAVE = "#2563EB"
COR_NEUTRO = "#9AA4B2"

COR_BARRA_FUNDO = "#252A38"
COR_BOTAO_PRIMARIO = "#3B82F6"
COR_BOTAO_PRIMARIO_HOVER = "#2563EB"

# Geometria
RAIO_CARD = 12
RAIO_BOTAO = 12
RAIO_ITEM = 8
RAIO_AVATAR = 20

ESPACO_SM = 16
ESPACO_MD = 24
ESPACO_LG = 32

LARGURA_SIDEBAR = 220

# Ícones de categoria / tipo
ICONE_RECEITA = "↑"
ICONE_DESPESA = "↓"


def iniciais_usuario(nome):
    """Retorna iniciais do nome para o avatar."""
    partes = nome.strip().split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[-1][0]).upper()
    return nome[:2].upper() if nome else "?"
