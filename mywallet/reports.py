"""
Módulo de relatórios: exportação CSV e geração de PDF.
"""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import (
    calcular_resumo,
    contar_movimentacoes,
    listar_movimentacoes,
    obter_estatisticas_relatorio,
)

def _formatar_moeda(valor):
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exportar_csv(usuario_id, nome_usuario="usuario"):
    """
    Exporta todas as movimentações do usuário para um arquivo CSV.
    Retorna True se exportou com sucesso.
    """
    movimentacoes = listar_movimentacoes(usuario_id)

    if not movimentacoes:
        messagebox.showinfo("Exportar CSV", "Não há movimentações para exportar.")
        return False

    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_sugerido = f"mywallet_{nome_usuario}_{data_atual}.csv"

    caminho = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        initialfile=nome_sugerido,
        title="Salvar relatório CSV",
    )

    if not caminho:
        return False

    try:
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["descricao", "valor", "categoria", "tipo", "data"])
            for mov in movimentacoes:
                _, descricao, valor, categoria, tipo, data = mov
                escritor.writerow([descricao, valor, categoria, tipo, data])

        messagebox.showinfo(
            "Exportar CSV",
            f"Arquivo exportado com sucesso!\n\n{caminho}",
        )
        return True

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível exportar: {e}")
        return False


def gerar_relatorio_pdf(usuario):
    """
    Exporta relatório financeiro em PDF via diálogo de salvamento.
    usuario: dicionário com id, nome e email.
    Retorna True se gerou com sucesso.
    """
    usuario_id = usuario["id"]
    movimentacoes = listar_movimentacoes(usuario_id)

    if not movimentacoes:
        messagebox.showinfo(
            "Exportar PDF",
            "Não há movimentações para exportar.",
        )
        return False

    nome_usuario = usuario["nome"].replace(" ", "_")
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_sugerido = f"mywallet_{nome_usuario}_{data_atual}.pdf"

    caminho = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Arquivo PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        initialfile=nome_sugerido,
        title="Salvar relatório PDF",
    )

    if not caminho:
        return False

    try:
        agora = datetime.now()
        _criar_pdf(caminho, usuario, movimentacoes, agora)

        messagebox.showinfo(
            "Exportar PDF",
            f"Relatório exportado com sucesso!\n\n{caminho}",
        )
        return True

    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Não foi possível exportar o relatório PDF.\n\nDetalhes: {e}",
        )
        return False


def _criar_pdf(caminho, usuario, movimentacoes, data_geracao):
    """Monta o documento PDF com ReportLab."""
    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    estilos = getSampleStyleSheet()
    titulo_estilo = ParagraphStyle(
        "TituloMyWallet",
        parent=estilos["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#166534"),
        spaceAfter=6,
    )
    subtitulo_estilo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=4,
    )
    secao_estilo = ParagraphStyle(
        "Secao",
        parent=estilos["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=14,
        spaceAfter=8,
    )
    texto_estilo = estilos["Normal"]

    elementos = []

    elementos.append(Paragraph("MyWallet", titulo_estilo))
    elementos.append(Paragraph("Relatório Financeiro Pessoal", subtitulo_estilo))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(
        Paragraph(
            f"<b>Usuário:</b> {usuario['nome']}<br/>"
            f"<b>E-mail:</b> {usuario['email']}<br/>"
            f"<b>Gerado em:</b> {data_geracao.strftime('%d/%m/%Y às %H:%M')}",
            texto_estilo,
        )
    )
    elementos.append(Spacer(1, 0.5 * cm))

    resumo = calcular_resumo(usuario["id"])
    total_mov = contar_movimentacoes(usuario["id"])

    elementos.append(Paragraph("Resumo Financeiro", secao_estilo))
    dados_resumo = [
        ["Saldo atual", _formatar_moeda(resumo["saldo"])],
        ["Total de receitas", _formatar_moeda(resumo["receitas"])],
        ["Total de despesas", _formatar_moeda(resumo["despesas"])],
        ["Quantidade de movimentações", str(total_mov)],
    ]
    elementos.append(_criar_tabela_simples(dados_resumo, [8 * cm, 8 * cm]))
    elementos.append(Spacer(1, 0.4 * cm))

    stats = obter_estatisticas_relatorio(usuario["id"])
    elementos.append(Paragraph("Estatísticas", secao_estilo))

    if stats["maior_receita"]:
        desc_rec, val_rec = stats["maior_receita"]
        maior_receita_txt = f"{desc_rec} ({_formatar_moeda(val_rec)})"
    else:
        maior_receita_txt = "—"

    if stats["maior_despesa"]:
        desc_desp, val_desp = stats["maior_despesa"]
        maior_despesa_txt = f"{desc_desp} ({_formatar_moeda(val_desp)})"
    else:
        maior_despesa_txt = "—"

    categoria_txt = stats["categoria_maior_gasto"] or "—"

    dados_stats = [
        ["Maior receita", maior_receita_txt],
        ["Maior despesa", maior_despesa_txt],
        ["Categoria com maior gasto", categoria_txt],
    ]
    elementos.append(_criar_tabela_simples(dados_stats, [6 * cm, 10 * cm]))
    elementos.append(Spacer(1, 0.4 * cm))

    elementos.append(Paragraph("Movimentações", secao_estilo))

    mov_ordenadas = sorted(movimentacoes, key=lambda m: (m[5], m[0]))
    cabecalho = ["Data", "Tipo", "Categoria", "Descrição", "Valor"]
    linhas_tabela = [cabecalho]

    for mov in mov_ordenadas:
        _, descricao, valor, categoria, tipo, data = mov
        tipo_label = "Receita" if tipo == "receita" else "Despesa"
        linhas_tabela.append([
            data,
            tipo_label,
            categoria,
            descricao,
            _formatar_moeda(valor),
        ])

    tabela_mov = Table(
        linhas_tabela,
        colWidths=[2.5 * cm, 2.2 * cm, 3.5 * cm, 5.5 * cm, 3 * cm],
        repeatRows=1,
    )
    tabela_mov.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "LEFT"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elementos.append(tabela_mov)

    elementos.append(Spacer(1, 0.8 * cm))
    elementos.append(
        Paragraph(
            "<i>Relatório gerado automaticamente pelo sistema MyWallet.</i>",
            subtitulo_estilo,
        )
    )

    doc.build(elementos)


def _criar_tabela_simples(dados, larguras):
    """Cria tabela formatada para resumo e estatísticas."""
    tabela = Table(dados, colWidths=larguras)
    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e5e7eb")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return tabela
