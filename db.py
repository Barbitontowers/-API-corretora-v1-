import sqlite3
import bcrypt

# =========================
# CONEXÃO
# =========================
def conectar():
    conn = sqlite3.connect("carteira.db")
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
    return conn


# =========================
# CRIAR TABELAS
# =========================
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT    UNIQUE NOT NULL,
        senha TEXT    NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker  TEXT    NOT NULL,
        tipo    TEXT    NOT NULL,
        FOREIGN KEY(user_id) REFERENCES usuarios(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posicoes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        ativo_id    INTEGER NOT NULL,
        quantidade  REAL    NOT NULL,
        preco       REAL    NOT NULL,
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
    """
    Cria um novo usuário com senha hasheada.
    Retorna {"ok": True} ou lança ValueError se o e-mail já existir.
    """
    conn = conectar()
    cursor = conn.cursor()

    # verifica duplicata
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Usuário já existe")

    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO usuarios (email, senha) VALUES (?, ?)",
        (email, senha_hash)
    )
    conn.commit()
    conn.close()

    return {"ok": True}


# =========================
# AUTENTICAR USUÁRIO
# =========================
def autenticar_usuario(email: str, senha: str) -> int | None:
    """
    Verifica e-mail e senha.
    Retorna o user_id se válido, ou None caso contrário.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, senha FROM usuarios WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    senha_ok = bcrypt.checkpw(senha.encode(), row["senha"].encode())

    return row["id"] if senha_ok else None


# =========================
# CRIAR ATIVO
# =========================
def criar_ativo(user_id: int, ticker: str, tipo: str) -> dict:
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ativos (user_id, ticker, tipo) VALUES (?, ?, ?)",
        (user_id, ticker.upper(), tipo)
    )
    ativo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": ativo_id, "ticker": ticker.upper(), "tipo": tipo}


# =========================
# LISTAR ATIVOS
# =========================
def listar_ativos(user_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, ticker, tipo FROM ativos WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# =========================
# CRIAR POSIÇÃO (COMPRA)
# =========================
def criar_posicao(user_id: int, ativo_id: int, quantidade: float, preco: float) -> dict:
    conn = conectar()
    cursor = conn.cursor()

    # valida que o ativo pertence ao usuário
    cursor.execute(
        "SELECT id FROM ativos WHERE id = ? AND user_id = ?",
        (ativo_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Ativo não encontrado para este usuário")

    cursor.execute(
        "INSERT INTO posicoes (user_id, ativo_id, quantidade, preco) VALUES (?, ?, ?, ?)",
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
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.id          AS ativo_id,
            a.ticker,
            a.tipo,
            SUM(p.quantidade)               AS quantidade,
            AVG(p.preco)                    AS preco_medio,
            SUM(p.quantidade * p.preco)     AS valor_investido
        FROM posicoes p
        JOIN ativos   a ON a.id = p.ativo_id
        WHERE p.user_id = ?
        GROUP BY a.id, a.ticker, a.tipo
        ORDER BY valor_investido DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    ativos = []
    total_investido = 0.0

    for r in rows:
        item = dict(r)
        item["valor_total"] = round(item["quantidade"] * item["preco_medio"], 2)
        item["preco_medio"] = round(item["preco_medio"], 2)
        item["quantidade"]  = round(item["quantidade"], 4)
        total_investido    += item["valor_investido"]
        ativos.append(item)

    return {
        "user_id":          user_id,
        "patrimonio_total": round(total_investido, 2),
        "ativos":           ativos
    }
