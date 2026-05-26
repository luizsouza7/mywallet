"""
Módulo de exportação de relatórios em CSV.
"""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox
from database import listar_movimentacoes


def exportar_csv(usuario_id, nome_usuario="usuario"):
    """
    Exporta todas as movimentações do usuário para um arquivo CSV.
    Retorna True se exportou com sucesso.
    """
    movimentacoes = listar_movimentacoes(usuario_id)

    if not movimentacoes:
        messagebox.showinfo("Exportar CSV", "Não há movimentações para exportar.")
        return False

    # Sugere nome do arquivo com data atual
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_sugerido = f"mywallet_{nome_usuario}_{data_atual}.csv"

    caminho = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        initialfile=nome_sugerido,
        title="Salvar relatório CSV",
    )

    if not caminho:
        return False  # usuário cancelou

    try:
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")

            # Cabeçalho
            escritor.writerow(["descricao", "valor", "categoria", "tipo", "data"])

            # Dados (ignora o id interno)
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
