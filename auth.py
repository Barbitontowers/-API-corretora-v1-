from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import db
import auth

app = FastAPI()

# CORS (frontend depois)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# AUTH
# ------------------------

def get_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    try:
        payload = auth.verificar_token(authorization)
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Token inválido")


# ------------------------
# ROTAS
# ------------------------

@app.get("/")
def home():
    return {"msg": "API rodando 🚀"}


@app.post("/registro")
def registro(data: dict):
    try:
        ok = db.criar_usuario(data["email"], data["senha"])
        if not ok:
            raise HTTPException(status_code=400, detail="Usuário já existe")
        return {"msg": "Usuário criado com sucesso"}
    except Exception as e:
        print("ERRO REGISTRO:", e)
        raise HTTPException(status_code=400, detail="Erro ao registrar")


@app.post("/login")
def login(data: dict):
    user_id = db.login_usuario(data["email"], data["senha"])

    if not user_id:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = auth.criar_token(user_id)

    return {"token": token}


@app.post("/ativo")
def add_ativo(data: dict, user_id: int = Header(None, alias="Authorization")):
    user_id = get_user(user_id)

    db.add_ativo(
        user_id,
        data["nome"],
        data["tipo"]
    )

    return {"msg": "Ativo adicionado"}


@app.get("/ativos")
def listar_ativos(user_id: int = Header(None, alias="Authorization")):
    user_id = get_user(user_id)

    ativos = db.listar_ativos(user_id)
    return ativos


@app.post("/posicao")
def add_posicao(data: dict, user_id: int = Header(None, alias="Authorization")):
    user_id = get_user(user_id)

    db.add_posicao(
        user_id,
        data["ativo_id"],
        data["quantidade"],
        data["preco"]
    )

    return {"msg": "Posição adicionada"}


@app.get("/carteira")
def carteira(user_id: int = Header(None, alias="Authorization")):
    user_id = get_user(user_id)

    return db.get_carteira(user_id)