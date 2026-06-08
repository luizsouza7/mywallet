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


def _clausulas_filtro(data_inicio=None, data_fim=None, tipo=None, categoria=None, busca=None):
    """Monta cláusulas SQL adicionais e parâmetros para filtros."""
    clausulas = []
    params = []

    if data_inicio and data_fim:
        clausulas.append("data BETWEEN ? AND ?")
        params.extend([data_inicio, data_fim])

    if tipo and tipo not in ("todos", "Todos"):
        clausulas.append("tipo = ?")
        params.append(tipo.lower())

    if categoria and categoria not in ("todas", "Todas"):
        clausulas.append("categoria = ?")
        params.append(categoria)

    if busca:
        clausulas.append("LOWER(descricao) LIKE ?")
        params.append(f"%{busca.lower()}%")

    if not clausulas:
        return "", []
    return " AND " + " AND ".join(clausulas), params


def listar_movimentacoes(
    usuario_id,
    limite=None,
    data_inicio=None,
    data_fim=None,
    tipo=None,
    categoria=None,
    busca=None,
):
    """Retorna lista de movimentações do usuário, da mais recente para a mais antiga."""
    conn = conectar()
    cursor = conn.cursor()
    filtro_sql, filtro_params = _clausulas_filtro(
        data_inicio, data_fim, tipo, categoria, busca
    )
    query = f"""
        SELECT id, descricao, valor, categoria, tipo, data
        FROM movimentacoes
        WHERE usuario_id = ?{filtro_sql}
        ORDER BY data DESC, id DESC
    """
    params = [usuario_id] + filtro_params
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


def calcular_resumo(usuario_id, data_inicio=None, data_fim=None):
    """
    Calcula saldo, total de receitas e total de despesas.
    Retorna dicionário com os valores.
    """
    conn = conectar()
    cursor = conn.cursor()
    filtro_sql, filtro_params = _clausulas_filtro(data_inicio, data_fim)

    cursor.execute(
        f"""
        SELECT COALESCE(SUM(valor), 0) FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'receita'{filtro_sql}
        """,
        (usuario_id, *filtro_params),
    )
    total_receitas = cursor.fetchone()[0]

    cursor.execute(
        f"""
        SELECT COALESCE(SUM(valor), 0) FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'despesa'{filtro_sql}
        """,
        (usuario_id, *filtro_params),
    )
    total_despesas = cursor.fetchone()[0]

    conn.close()

    saldo = total_receitas - total_despesas
    return {
        "saldo": saldo,
        "receitas": total_receitas,
        "despesas": total_despesas,
    }


def obter_gastos_por_categoria(usuario_id, data_inicio=None, data_fim=None):
    """Retorna totais de despesas agrupados por categoria."""
    conn = conectar()
    cursor = conn.cursor()
    filtro_sql, filtro_params = _clausulas_filtro(data_inicio, data_fim)
    cursor.execute(
        f"""
        SELECT categoria, SUM(valor)
        FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'despesa'{filtro_sql}
        GROUP BY categoria
        ORDER BY SUM(valor) DESC
        """,
        (usuario_id, *filtro_params),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def obter_evolucao_financeira(usuario_id, data_inicio=None, data_fim=None):
    """
    Retorna evolução do saldo acumulado por data no período.
    Útil para gráfico de linha.
    """
    conn = conectar()
    cursor = conn.cursor()
    filtro_sql, filtro_params = _clausulas_filtro(data_inicio, data_fim)
    cursor.execute(
        f"""
        SELECT data, tipo, valor
        FROM movimentacoes
        WHERE usuario_id = ?{filtro_sql}
        ORDER BY data ASC, id ASC
        """,
        (usuario_id, *filtro_params),
    )
    movimentacoes = cursor.fetchall()
    conn.close()

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


def contar_movimentacoes(usuario_id, data_inicio=None, data_fim=None):
    """Retorna a quantidade de movimentações do usuário."""
    conn = conectar()
    cursor = conn.cursor()
    filtro_sql, filtro_params = _clausulas_filtro(data_inicio, data_fim)
    cursor.execute(
        f"SELECT COUNT(*) FROM movimentacoes WHERE usuario_id = ?{filtro_sql}",
        (usuario_id, *filtro_params),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


def obter_categorias(usuario_id):
    """Retorna lista de categorias distintas do usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT categoria FROM movimentacoes
        WHERE usuario_id = ?
        ORDER BY categoria ASC
        """,
        (usuario_id,),
    )
    categorias = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categorias


def obter_estatisticas_relatorio(usuario_id):
    """
    Retorna estatísticas para o relatório PDF.
    maior_receita / maior_despesa: tupla (descricao, valor) ou None
    categoria_maior_gasto: nome da categoria ou None
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT descricao, valor FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'receita'
        ORDER BY valor DESC LIMIT 1
        """,
        (usuario_id,),
    )
    maior_receita = cursor.fetchone()

    cursor.execute(
        """
        SELECT descricao, valor FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'despesa'
        ORDER BY valor DESC LIMIT 1
        """,
        (usuario_id,),
    )
    maior_despesa = cursor.fetchone()

    cursor.execute(
        """
        SELECT categoria, SUM(valor) AS total
        FROM movimentacoes
        WHERE usuario_id = ? AND tipo = 'despesa'
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT 1
        """,
        (usuario_id,),
    )
    cat_row = cursor.fetchone()
    categoria_maior_gasto = cat_row[0] if cat_row else None

    conn.close()

    return {
        "maior_receita": maior_receita,
        "maior_despesa": maior_despesa,
        "categoria_maior_gasto": categoria_maior_gasto,
    }


def data_hoje():
    """Retorna data atual no formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")
