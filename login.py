import streamlit as st
import requests

API = "http://127.0.0.1:8000"

st.title("🔐 Login")

email = st.text_input("Email")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):
    res = requests.post(f"{API}/login", json={"email": email, "senha": senha})
    
    if res.status_code == 200:
        token = res.json()["token"]
        st.session_state["token"] = token
        st.success("Logado!")
    else:
        st.error("Erro no login")