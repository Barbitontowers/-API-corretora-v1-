import os
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import db

BASE_DIR = Path(__file__).parent

SECRET_KEY = "segredo_super_forte"
ALGORITHM  = "HS256"

app = FastAPI(title="Corretora IA", version="2.0.0")
db.criar_tabelas()

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

security = HTTPBearer()

def criar_token(user_id):
    return jwt.encode({"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=12)},
                      SECRET_KEY, algorithm=ALGORITHM)

def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

class UserSchema(BaseModel):
    email: str
    senha: str

class AtivoSchema(BaseModel):
    ticker: str
    tipo: str

class PosicaoSchema(BaseModel):
    ativo_id: int
    quantidade: float
    preco: float


# ---------- STATUS ----------

@app.get("/", tags=["Status"])
def home():
    return {"status": "API ONLINE 🚀", "versao": "2.0"}


# ---------- DASHBOARD ----------

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard():
    with open(BASE_DIR / "dashboard.html", "r", encoding="utf-8") as f:
        return f.read()


# ---------- AUTH ----------

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
def add_ativo(ativo: AtivoSchema, user_id: int = Depends(get_user_id)):
    try:
        return db.criar_ativo(user_id, ativo.ticker, ativo.tipo)
    except Exception as e:
        print("🔥 ERRO ATIVO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao criar ativo")


@app.get("/ativos", tags=["Ativos"])
def listar_ativos(user_id: int = Depends(get_user_id)):
    try:
        return db.listar_ativos(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao listar ativos")


# ---------- POSIÇÕES ----------

@app.post("/posicao", tags=["Posições"])
def add_posicao(posicao: PosicaoSchema, user_id: int = Depends(get_user_id)):
    try:
        return db.criar_posicao(user_id, posicao.ativo_id, posicao.quantidade, posicao.preco)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("🔥 ERRO POSICAO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao registrar posição")


# ---------- CARTEIRA ----------

@app.get("/carteira", tags=["Carteira"])
def carteira(user_id: int = Depends(get_user_id)):
    try:
        return db.get_carteira(user_id)
    except Exception as e:
        print("🔥 ERRO CARTEIRA:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao carregar carteira")


# ---------- PREÇOS ----------

@app.get("/precos", tags=["Preços"])
def precos(user_id: int = Depends(get_user_id)):
    try:
        ativos = db.listar_ativos(user_id)
        if not ativos:
            return {}
        from precos import buscar_precos
        return buscar_precos(ativos)
    except Exception as e:
        print("🔥 ERRO PRECOS:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao buscar preços")


# ---------- ANÁLISE ----------

@app.get("/analise", tags=["Análise"])
def analise(user_id: int = Depends(get_user_id)):
    try:
        from precos import buscar_precos
        from analise import calcular_risco, comparar_ibovespa

        cart = db.get_carteira(user_id)
        ativos = cart["ativos"]
        if not ativos:
            return {"msg": "Nenhum ativo cadastrado"}

        precos_atual = buscar_precos(db.listar_ativos(user_id))

        # Patrimônio atual com preços reais
        patrimonio_atual = sum(
            (precos_atual.get(a["ticker"]) or 0) * a["quantidade"]
            if precos_atual.get(a["ticker"]) else a["valor_investido"]
            for a in ativos
        )
        total_investido = cart["patrimonio_total"]

        # Salva snapshot diário do patrimônio
        db.salvar_historico(user_id, round(patrimonio_atual, 2))

        risco = calcular_risco(ativos, precos_atual)

        primeira_compra = min(
            (a.get("primeira_compra") or "9999-12-31" for a in ativos),
            default=None
        )
        ibov = comparar_ibovespa(primeira_compra, patrimonio_atual, total_investido)

        return {
            "patrimonio_atual": round(patrimonio_atual, 2),
            "total_investido": round(total_investido, 2),
            "risco": risco,
            "vs_ibovespa": ibov
        }
    except Exception as e:
        print("🔥 ERRO ANALISE:", repr(e))
        raise HTTPException(status_code=500, detail="Erro na análise")


# ---------- HISTÓRICO ----------

@app.get("/historico", tags=["Histórico"])
def historico(user_id: int = Depends(get_user_id)):
    try:
        return db.get_historico(user_id, dias=90)
    except Exception as e:
        print("🔥 ERRO HISTORICO:", repr(e))
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico")
