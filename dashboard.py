import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Corretora IA", layout="wide")

# ======================
# LOGIN
# ======================
if "token" not in st.session_state:
    st.session_state.token = None

st.sidebar.title("🔐 Acesso")

email = st.sidebar.text_input("Email")
senha = st.sidebar.text_input("Senha", type="password")

if st.sidebar.button("Login"):
    try:
        res = requests.post(f"{API_URL}/login", json={
            "email": email,
            "senha": senha
        })
        if res.status_code == 200:
            st.session_state.token = res.json()["token"]
            st.success("Logado com sucesso")
        else:
            st.error("Erro no login")
    except:
        st.error("Backend offline")

# ======================
# SEM LOGIN
# ======================
if not st.session_state.token:
    st.title("📊 Plataforma de Investimentos")
    st.info("Faça login para acessar")
    st.stop()

headers = {
    "Authorization": st.session_state.token
}

# ======================
# TOPO
# ======================
st.title("💼 Minha Corretora")
st.markdown("---")

# ======================
# CARREGAR CARTEIRA
# ======================
try:
    carteira = requests.get(
        f"{API_URL}/carteira",
        headers=headers
    ).json()

    df = pd.DataFrame(carteira)

except:
    st.error("Erro ao carregar carteira")
    st.stop()

# ======================
# RESUMO
# ======================
st.subheader("📊 Visão Geral")

if not df.empty:
    total = df["valor_total"].sum()
    lucro = df["valor_total"].sum() - df["valor_investido"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Patrimônio", f"R$ {total:,.2f}")
    col2.metric("📈 Lucro", f"R$ {lucro:,.2f}")
    col3.metric("📊 Ativos", len(df))

# ======================
# GRÁFICO
# ======================
st.subheader("📊 Alocação")

if not df.empty:
    df_group = df.groupby("tipo")["valor_total"].sum()

    st.bar_chart(df_group)

# ======================
# TABELA
# ======================
st.subheader("📋 Carteira")

st.dataframe(df)

# ======================
# ADICIONAR ATIVO
# ======================
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Novo Ativo")

ticker = st.sidebar.text_input("Ticker")
tipo = st.sidebar.selectbox("Tipo", ["acao", "fii", "cripto", "renda_fixa"])

if st.sidebar.button("Adicionar Ativo"):
    try:
        res = requests.post(
            f"{API_URL}/ativo",
            json={"ticker": ticker, "tipo": tipo},
            headers=headers
        )
        st.success("Ativo cadastrado")
    except:
        st.error("Erro")

# ======================
# ADICIONAR POSIÇÃO
# ======================
st.sidebar.subheader("📥 Nova Compra")

ativo_id = st.sidebar.number_input("ID do Ativo", step=1)
quantidade = st.sidebar.number_input("Quantidade")
preco = st.sidebar.number_input("Preço")

if st.sidebar.button("Registrar"):
    try:
        res = requests.post(
            f"{API_URL}/posicao",
            json={
                "ativo_id": ativo_id,
                "quantidade": quantidade,
                "preco": preco
            },
            headers=headers
        )
        st.success("Compra registrada")
    except:
        st.error("Erro")

# ======================
# ANÁLISE
# ======================
st.markdown("---")
st.subheader("🧠 Análise Inteligente")

if st.button("Rodar análise"):
    try:
        analise = requests.get(
            f"{API_URL}/analise",
            headers=headers
        ).json()

        st.json(analise)

    except:
        st.error("Erro na análise")