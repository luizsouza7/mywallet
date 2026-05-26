"""
Módulo de banco de dados SQLite do MyWallet.
Responsável por criar tabelas e executar operações CRUD.
"""

import sqlite3
import hashlib
from datetime import datetime

# Nome do arquivo do banco (criado automaticamente na primeira execução)
DB_NAME = "mywallet.db"


def conectar():
    """Abre conexão com o banco SQLite."""
    return sqlite3.connect(DB_NAME)


def hash_senha(senha):
    """Converte a senha em hash simples para armazenamento seguro básico."""
    return hashlib.sha256(senha.encode()).hexdigest()


def inicializar_banco():
    """Cria as tabelas caso ainda não existam."""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # Tabela de movimentações financeiras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            tipo TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── USUÁRIOS ───────────────────────────────────────────────

def cadastrar_usuario(nome, email, senha):
    """
    Cadastra novo usuário.
    Retorna (True, mensagem) em sucesso ou (False, mensagem) em erro.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome.strip(), email.strip().lower(), hash_senha(senha)),
        )
        conn.commit()
        conn.close()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este e-mail já está cadastrado."
    except Exception as e:
        return False, f"Erro ao cadastrar: {e}"


def autenticar_usuario(email, senha):
    """
    Verifica login do usuário.
    Retorna dicionário com dados do usuário ou None se inválido.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, email FROM usuarios WHERE email = ? AND senha = ?",
        (email.strip().lower(), hash_senha(senha)),
    )
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        return {"id": usuario[0], "nome": usuario[1], "email": usuario[2]}
    return None


# ─── MOVIMENTAÇÕES ──────────────────────────────────────────

def adicionar_movimentacao(usuario_id, descricao, valor, categoria, tipo, data):
    """Insere uma nova receita ou despesa."""
    if tipo not in ("receita", "despesa"):
        raise ValueError("Tipo de movimentação inválido.")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO movimentacoes
        (usuario_id, descricao, valor, categoria, tipo, data)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (usuario_id, descricao.strip(), float(valor), categoria.strip(), tipo, data),
    )
    conn.commit()
    conn.close()


def listar_movimentacoes(usuario_id, limite=None):
    """Retorna lista de movimentações do usuário, da mais recente para a mais antiga."""
    conn = conectar()
    cursor = conn.cursor()
    query = """
        SELECT id, descricao, valor, categoria, tipo, data
        FROM movimentacoes
        WHERE usuario_id = ?
        ORDER BY data DESC, id DESC
    """
    params = [usuario_id]
    if limite is not None:
        query += " LIMIT ?"
        params.append(int(limite))
    cursor.execute(query, params)
    movimentacoes = cursor.fetchall()
    conn.close()
    return movimentacoes


def atualizar_movimentacao(mov_id, usuario_id, descricao, valor, categoria, tipo, data):
    """Atualiza uma movimentação existente."""
    if tipo not in ("receita", "despesa"):
        raise ValueError("Tipo de movimentação inválido.")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE movimentacoes
        SET descricao = ?, valor = ?, categoria = ?, tipo = ?, data = ?
        WHERE id = ? AND usuario_id = ?
        """,
        (descricao.strip(), float(valor), categoria.strip(), tipo, data, mov_id, usuario_id),
    )
    conn.commit()
    conn.close()


def excluir_movimentacao(mov_id, usuario_id):
    """Remove uma movimentação do banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM movimentacoes WHERE id = ? AND usuario_id = ?",
        (mov_id, usuario_id),
    )
    conn.commit()
    conn.close()


def calcular_resumo(usuario_id):
    """
    Calcula saldo, total de receitas e total de despesas.
    Retorna dicionário com os valores.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM movimentacoes WHERE usuario_id = ? AND tipo = 'receita'",
        (usuario_id,),
    )
    total_receitas = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM movimentacoes WHERE usuario_id = ? AND tipo = 'despesa'",
        (usuario_id,),
    )
    total_despesas = cursor.fetchone()[0]

    conn.close()

    saldo = total_receitas - total_despesas
    return {
        "saldo": saldo,
        "receitas": total_receitas,
        "despesas": total_despesas,
    }


def obter_gastos_por_categoria(usuario_id):
    """Retorna totais de despesas agrupados por categoria."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT categoria, SUM(valor)
        FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'despesa'
        GROUP BY categoria
        ORDER BY SUM(valor) DESC
        """,
        (usuario_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def obter_evolucao_financeira(usuario_id):
    """
    Retorna evolução do saldo acumulado por data.
    Útil para gráfico de linha.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT data, tipo, valor
        FROM movimentacoes
        WHERE usuario_id = ?
        ORDER BY data ASC, id ASC
        """,
        (usuario_id,),
    )
    movimentacoes = cursor.fetchall()
    conn.close()

    # Calcula saldo acumulado dia a dia
    saldo_acumulado = {}
    saldo = 0
    for data, tipo, valor in movimentacoes:
        if tipo == "receita":
            saldo += valor
        else:
            saldo -= valor
        saldo_acumulado[data] = saldo

    datas = list(saldo_acumulado.keys())
    saldos = list(saldo_acumulado.values())
    return datas, saldos


def data_hoje():
    """Retorna data atual no formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")
