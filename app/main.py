from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext

import jwt
from datetime import datetime, timedelta

import db

# =========================
# APP
# =========================
app = FastAPI()

# =========================
# DB
# =========================
db.criar_tabelas()

# =========================
# SECURITY
# =========================
SECRET = "super_secret_key"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

security = HTTPBearer()

# =========================
# MODELS
# =========================
class User(BaseModel):
    email: str
    senha: str


class Ativo(BaseModel):
    ativo: str
    quantidade: float
    preco: float


# =========================
# TOKEN
# =========================
def criar_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }

    token = jwt.encode(
        payload,
        SECRET,
        algorithm="HS256"
    )

    return token


# =========================
# VERIFICAR TOKEN
# =========================
def verificar_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credentials.credentials

        payload = jwt.decode(
            token,
            SECRET,
            algorithms=["HS256"]
        )

        return payload["user_id"]

    except:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {
        "msg": "API INVEST PROFISSIONAL ONLINE 🚀"
    }


# =========================
# REGISTRO
# =========================
@app.post("/registro")
def registro(user: User):

    existe = db.buscar_usuario(user.email)

    if existe:
        raise HTTPException(
            status_code=400,
            detail="Usuário já existe"
        )

    senha_hash = pwd_context.hash(user.senha)

    db.criar_usuario(
        user.email,
        senha_hash
    )

    return {
        "msg": "Usuário criado"
    }


# =========================
# LOGIN
# =========================
@app.post("/login")
def login(user: User):

    try:

        db_user = db.buscar_usuario(user.email)

        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Usuário não encontrado"
            )

        senha_ok = pwd_context.verify(
            user.senha,
            db_user["senha"]
        )

        if not senha_ok:
            raise HTTPException(
                status_code=401,
                detail="Senha inválida"
            )

        token = criar_token(db_user["id"])

        return {
            "token": token
        }

    except Exception as e:

        print("ERRO LOGIN:", e)

        raise HTTPException(
            status_code=500,
            detail="Erro interno"
        )


# =========================
# ADICIONAR ATIVO
# =========================
@app.post("/carteira")
def adicionar_ativo(
    ativo: Ativo,
    user_id: int = Depends(verificar_token)
):

    db.adicionar_ativo(
        user_id,
        ativo.ativo,
        ativo.quantidade,
        ativo.preco
    )

    return {
        "msg": "Ativo adicionado"
    }


# =========================
# VER CARTEIRA
# =========================
@app.get("/carteira")
def ver_carteira(
    user_id: int = Depends(verificar_token)
):

    carteira = db.buscar_carteira(user_id)

    patrimonio = sum(
        item["total"]
        for item in carteira
    )

    return {
        "user_id": user_id,
        "patrimonio_total": patrimonio,
        "ativos": carteira
    }