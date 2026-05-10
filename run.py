import subprocess

print("🚀 Iniciando sistema...")

# Backend
subprocess.Popen("uvicorn main:app --reload", shell=True)

# Frontend
subprocess.Popen("streamlit run dashboard.py", shell=True)

input("Pressione ENTER para encerrar...")