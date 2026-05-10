import os
import bcrypt

# =========================
# CONEXÃO
# Usa PostgreSQL na nuvem (DATABASE_URL),
# SQLite localmente para desenvolvimento
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def conectar():
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def cursor_dict(conn):
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    PLACEHOLDER = "%s"

else:
    import sqlite3

    def conectar():
        conn = sqlite3.connect("carteira.db")
        conn.row_factory = sqlite3.Row
        return conn

    def cursor_dict(conn):
        return conn.cursor()

    PLACEHOLDER = "?"


def P(n=1):
    """Retorna n placeholders corretos para o banco ativo."""
    return ", ".join([PLACEHOLDER] * n)


# =========================
# CRIAR TABELAS
# =========================
def criar_tabelas():
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id    SERIAL PRIMARY KEY,
        email TEXT   UNIQUE NOT NULL,
        senha TEXT   NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id      SERIAL  PRIMARY KEY,
        user_id INTEGER NOT NULL,
        ticker  TEXT    NOT NULL,
        tipo    TEXT    NOT NULL,
        FOREIGN KEY(user_id) REFERENCES usuarios(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posicoes (
        id         SERIAL  PRIMARY KEY,
        user_id    INTEGER NOT NULL,
        ativo_id   INTEGER NOT NULL,
        quantidade REAL    NOT NULL,
        preco      REAL    NOT NULL,
        FOREIGN KEY(user_id)  REFERENCES usuarios(id),
        FOREIGN KEY(ativo_id) REFERENCES ativos(id)
    )
    """)

    conn.commit()
    conn.close()


# =========================
# CRIAR USUÁRIO
# =========================
def criar_usuario(email: str, senha: str) -> dict:
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(
        f"SELECT id FROM usuarios WHERE email = {PLACEHOLDER}",
        (email,)
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError("Usuário já existe")

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        f"INSERT INTO usuarios (email, senha) VALUES ({P(2)})",
        (email, senha_hash)
    )
    conn.commit()
    conn.close()

    return {"ok": True}


# =========================
# AUTENTICAR USUÁRIO
# =========================
def autenticar_usuario(email: str, senha: str):
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(
        f"SELECT id, senha FROM usuarios WHERE email = {PLACEHOLDER}",
        (email,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    senha_hash = row["senha"] if isinstance(row, dict) else row[1]
    user_id    = row["id"]   if isinstance(row, dict) else row[0]

    senha_ok = bcrypt.checkpw(senha.encode(), senha_hash.encode())

    return user_id if senha_ok else None


# =========================
# CRIAR ATIVO
# =========================
def criar_ativo(user_id: int, ticker: str, tipo: str) -> dict:
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(
        f"INSERT INTO ativos (user_id, ticker, tipo) VALUES ({P(3)})",
        (user_id, ticker.upper(), tipo)
    )
    conn.commit()

    cursor.execute(
        f"SELECT id FROM ativos WHERE user_id = {PLACEHOLDER} AND ticker = {PLACEHOLDER} ORDER BY id DESC LIMIT 1",
        (user_id, ticker.upper())
    )
    row = cursor.fetchone()
    conn.close()

    ativo_id = row["id"] if isinstance(row, dict) else row[0]

    return {"id": ativo_id, "ticker": ticker.upper(), "tipo": tipo}


# =========================
# LISTAR ATIVOS
# =========================
def listar_ativos(user_id: int) -> list:
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(
        f"SELECT id, ticker, tipo FROM ativos WHERE user_id = {PLACEHOLDER}",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# =========================
# CRIAR POSIÇÃO
# =========================
def criar_posicao(user_id: int, ativo_id: int, quantidade: float, preco: float) -> dict:
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(
        f"SELECT id FROM ativos WHERE id = {PLACEHOLDER} AND user_id = {PLACEHOLDER}",
        (ativo_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Ativo não encontrado para este usuário")

    cursor.execute(
        f"INSERT INTO posicoes (user_id, ativo_id, quantidade, preco) VALUES ({P(4)})",
        (user_id, ativo_id, quantidade, preco)
    )
    conn.commit()
    conn.close()

    return {"ok": True, "quantidade": quantidade, "preco": preco}


# =========================
# GET CARTEIRA
# =========================
def get_carteira(user_id: int) -> dict:
    conn = conectar()
    cursor = cursor_dict(conn)

    cursor.execute(f"""
        SELECT
            a.id                            AS ativo_id,
            a.ticker,
            a.tipo,
            SUM(p.quantidade)               AS quantidade,
            AVG(p.preco)                    AS preco_medio,
            SUM(p.quantidade * p.preco)     AS valor_investido
        FROM posicoes p
        JOIN ativos   a ON a.id = p.ativo_id
        WHERE p.user_id = {PLACEHOLDER}
        GROUP BY a.id, a.ticker, a.tipo
        ORDER BY valor_investido DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    ativos = []
    total  = 0.0

    for r in rows:
        item = dict(r)
        item["valor_total"]     = round(float(item["quantidade"]) * float(item["preco_medio"]), 2)
        item["preco_medio"]     = round(float(item["preco_medio"]), 2)
        item["quantidade"]      = round(float(item["quantidade"]), 4)
        item["valor_investido"] = round(float(item["valor_investido"]), 2)
        total += item["valor_investido"]
        ativos.append(item)

    return {
        "user_id":          user_id,
        "patrimonio_total": round(total, 2),
        "ativos":           ativos
    }
