import sqlite3

def conectar():
    return sqlite3.connect("carteira.db")


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        senha TEXT
    )
    """)

    # carteira real
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carteira (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ativo TEXT,
        quantidade REAL,
        preco REAL
    )
    """)

    conn.commit()
    conn.close()


def criar_usuario(email, senha_hash):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (email, senha) VALUES (?, ?)",
        (email, senha_hash)
    )

    conn.commit()
    conn.close()


def buscar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, senha FROM usuarios WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id": user[0], "email": user[1], "senha": user[2]}
    return None


# 🔥 NOVO: adicionar ativo
def adicionar_ativo(user_id, ativo, quantidade, preco):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO carteira (user_id, ativo, quantidade, preco)
    VALUES (?, ?, ?, ?)
    """, (user_id, ativo, quantidade, preco))

    conn.commit()
    conn.close()


# 🔥 NOVO: buscar carteira
def buscar_carteira(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT ativo, quantidade, preco
    FROM carteira
    WHERE user_id = ?
    """, (user_id,))

    dados = cursor.fetchall()
    conn.close()

    carteira = []
    for ativo, qtd, preco in dados:
        carteira.append({
            "ativo": ativo,
            "quantidade": qtd,
            "preco": preco,
            "total": qtd * preco
        })

    return carteira