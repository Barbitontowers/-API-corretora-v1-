from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from pydantic import BaseModel
import jwt

import db

# =========================
# INICIALIZAÇÃO
# =========================
app = FastAPI(title="Corretora IA", version="1.0.0")

db.criar_tabelas()   # garante que as tabelas existam ao subir

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # em produção restrinja ao domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# JWT
# =========================
SECRET_KEY = "segredo_super_forte"
ALGORITHM  = "HS256"
security   = HTTPBearer()


def criar_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Decodifica o Bearer token e retorna o user_id."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# =========================
# MODELS (validação)
# =========================
class UserSchema(BaseModel):
    email: str
    senha: str


class AtivoSchema(BaseModel):
    ticker: str
    tipo:   str   # acao | fii | cripto | renda_fixa


class PosicaoSchema(BaseModel):
    ativo_id:   int
    quantidade: float
    preco:      float


# =========================
# ROTAS
# =========================

@app.get("/", tags=["Status"])
def home():
    return {"status": "API ONLINE 🚀"}


# ---------- USUÁRIOS ----------

@app.post("/registro", tags=["Auth"])
def registro(user: UserSchema):
    try:
        db.criar_usuario(user.email, user.senha)
        return {"msg": "Usuário criado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("🔥 ERRO REGISTRO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro interno")


@app.post("/login", tags=["Auth"])
def login(user: UserSchema):
    try:
        user_id = db.autenticar_usuario(user.email, user.senha)
        if not user_id:
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
        return {"token": criar_token(user_id)}
    except HTTPException:
        raise
    except Exception as e:
        print("🔥 ERRO LOGIN:", repr(e))
        raise HTTPException(status_code=500, detail="Erro interno")


# ---------- ATIVOS ----------

@app.post("/ativo", tags=["Ativos"])
def add_ativo(
    ativo: AtivoSchema,
    user_id: int = Depends(get_user_id)
):
    try:
        resultado = db.criar_ativo(user_id, ativo.ticker, ativo.tipo)
        return resultado
    except Exception as e:
        print("🔥 ERRO ATIVO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao criar ativo")


@app.get("/ativos", tags=["Ativos"])
def listar_ativos(user_id: int = Depends(get_user_id)):
    try:
        return db.listar_ativos(user_id)
    except Exception as e:
        print("🔥 ERRO LISTAR ATIVOS:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao listar ativos")


# ---------- POSIÇÕES ----------

@app.post("/posicao", tags=["Posições"])
def add_posicao(
    posicao: PosicaoSchema,
    user_id: int = Depends(get_user_id)
):
    try:
        resultado = db.criar_posicao(
            user_id,
            posicao.ativo_id,
            posicao.quantidade,
            posicao.preco
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("🔥 ERRO POSICAO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao registrar posição")




# ---------- DASHBOARD ----------

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

# ---------- CARTEIRA ----------

@app.get("/carteira", tags=["Carteira"])
def carteira(user_id: int = Depends(get_user_id)):
    try:
        return db.get_carteira(user_id)
    except Exception as e:
        print("🔥 ERRO CARTEIRA:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao carregar carteira")
