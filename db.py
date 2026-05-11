import os
import bcrypt

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    def conectar():
        return psycopg2.connect(DATABASE_URL)
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
    return ", ".join([PLACEHOLDER] * n)


def criar_tabelas():
    conn = conectar()
    c = cursor_dict(conn)

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS ativos (
        id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL, tipo TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES usuarios(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS posicoes (
        id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
        ativo_id INTEGER NOT NULL, quantidade REAL NOT NULL, preco REAL NOT NULL,
        data_compra DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY(user_id) REFERENCES usuarios(id),
        FOREIGN KEY(ativo_id) REFERENCES ativos(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS historico_patrimonio (
        id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
        data DATE NOT NULL, patrimonio REAL NOT NULL,
        UNIQUE(user_id, data),
        FOREIGN KEY(user_id) REFERENCES usuarios(id))""")

    conn.commit()
    conn.close()


def criar_usuario(email, senha):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"SELECT id FROM usuarios WHERE email = {PLACEHOLDER}", (email,))
    if c.fetchone():
        conn.close(); raise ValueError("Usuário já existe")
    h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    c.execute(f"INSERT INTO usuarios (email, senha) VALUES ({P(2)})", (email, h))
    conn.commit(); conn.close()
    return {"ok": True}


def autenticar_usuario(email, senha):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"SELECT id, senha FROM usuarios WHERE email = {PLACEHOLDER}", (email,))
    row = c.fetchone(); conn.close()
    if not row: return None
    h = row["senha"] if isinstance(row, dict) else row[1]
    uid = row["id"] if isinstance(row, dict) else row[0]
    return uid if bcrypt.checkpw(senha.encode(), h.encode()) else None


def criar_ativo(user_id, ticker, tipo):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"INSERT INTO ativos (user_id, ticker, tipo) VALUES ({P(3)})",
              (user_id, ticker.upper(), tipo))
    conn.commit()
    c.execute(f"SELECT id FROM ativos WHERE user_id={PLACEHOLDER} AND ticker={PLACEHOLDER} ORDER BY id DESC LIMIT 1",
              (user_id, ticker.upper()))
    row = c.fetchone(); conn.close()
    aid = row["id"] if isinstance(row, dict) else row[0]
    return {"id": aid, "ticker": ticker.upper(), "tipo": tipo}


def listar_ativos(user_id):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"SELECT id, ticker, tipo FROM ativos WHERE user_id = {PLACEHOLDER}", (user_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]


def criar_posicao(user_id, ativo_id, quantidade, preco):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"SELECT id FROM ativos WHERE id={PLACEHOLDER} AND user_id={PLACEHOLDER}", (ativo_id, user_id))
    if not c.fetchone():
        conn.close(); raise ValueError("Ativo não encontrado")
    c.execute(f"INSERT INTO posicoes (user_id, ativo_id, quantidade, preco) VALUES ({P(4)})",
              (user_id, ativo_id, quantidade, preco))
    conn.commit(); conn.close()
    return {"ok": True, "quantidade": quantidade, "preco": preco}


def get_carteira(user_id):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"""
        SELECT a.id AS ativo_id, a.ticker, a.tipo,
               SUM(p.quantidade) AS quantidade,
               AVG(p.preco) AS preco_medio,
               SUM(p.quantidade * p.preco) AS valor_investido,
               MIN(p.data_compra) AS primeira_compra
        FROM posicoes p JOIN ativos a ON a.id = p.ativo_id
        WHERE p.user_id = {PLACEHOLDER}
        GROUP BY a.id, a.ticker, a.tipo
        ORDER BY valor_investido DESC
    """, (user_id,))
    rows = c.fetchall(); conn.close()
    ativos = []
    total = 0.0
    for r in rows:
        item = dict(r)
        item["valor_total"] = round(float(item["quantidade"]) * float(item["preco_medio"]), 2)
        item["preco_medio"] = round(float(item["preco_medio"]), 2)
        item["quantidade"] = round(float(item["quantidade"]), 4)
        item["valor_investido"] = round(float(item["valor_investido"]), 2)
        if item.get("primeira_compra"):
            item["primeira_compra"] = str(item["primeira_compra"])
        total += item["valor_investido"]
        ativos.append(item)
    return {"user_id": user_id, "patrimonio_total": round(total, 2), "ativos": ativos}


def salvar_historico(user_id, patrimonio):
    from datetime import date
    conn = conectar(); c = cursor_dict(conn)
    hoje = str(date.today())
    if DATABASE_URL:
        c.execute(f"""INSERT INTO historico_patrimonio (user_id, data, patrimonio)
                      VALUES ({P(3)}) ON CONFLICT (user_id, data) DO UPDATE SET patrimonio = EXCLUDED.patrimonio""",
                  (user_id, hoje, patrimonio))
    else:
        c.execute(f"""INSERT OR REPLACE INTO historico_patrimonio (user_id, data, patrimonio)
                      VALUES ({P(3)})""", (user_id, hoje, patrimonio))
    conn.commit(); conn.close()


def get_historico(user_id, dias=90):
    conn = conectar(); c = cursor_dict(conn)
    c.execute(f"""SELECT data, patrimonio FROM historico_patrimonio
                  WHERE user_id = {PLACEHOLDER}
                  ORDER BY data ASC
                  LIMIT {PLACEHOLDER}""", (user_id, dias))
    rows = c.fetchall(); conn.close()
    return [{"data": str(r["data"] if isinstance(r, dict) else r[0]),
             "patrimonio": float(r["patrimonio"] if isinstance(r, dict) else r[1])}
            for r in rows]
