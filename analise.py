import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def calcular_risco(ativos: list, precos: dict) -> dict:
    """
    Calcula score de risco, concentração e diversificação da carteira.
    """
    if not ativos:
        return {}

    total = sum(
        (precos.get(a["ticker"]) or 0) * a["quantidade"]
        if precos.get(a["ticker"]) else a["valor_investido"]
        for a in ativos
    )
    if total == 0:
        return {}

    # Concentração por ativo
    concentracao = []
    for a in ativos:
        val = (precos.get(a["ticker"]) or 0) * a["quantidade"] if precos.get(a["ticker"]) else a["valor_investido"]
        pct = val / total * 100 if total > 0 else 0
        concentracao.append({"ticker": a["ticker"], "tipo": a["tipo"], "pct": round(pct, 2), "valor": round(val, 2)})

    concentracao.sort(key=lambda x: x["pct"], reverse=True)

    # Concentração por tipo
    por_tipo = {}
    for item in concentracao:
        t = item["tipo"]
        por_tipo[t] = por_tipo.get(t, 0) + item["pct"]
    por_tipo = {k: round(v, 2) for k, v in sorted(por_tipo.items(), key=lambda x: -x[1])}

    # Score de risco (0-100)
    # Penaliza: muita concentração em 1 ativo, pouca diversificação de tipos
    maior_pct = concentracao[0]["pct"] if concentracao else 0
    n_tipos = len(por_tipo)
    n_ativos = len(ativos)

    score = 50  # base
    if maior_pct > 50: score += 25
    elif maior_pct > 30: score += 15
    elif maior_pct > 20: score += 5

    if n_tipos == 1: score += 20
    elif n_tipos == 2: score += 10
    elif n_tipos >= 4: score -= 10

    if n_ativos <= 2: score += 10
    elif n_ativos >= 8: score -= 10

    score = max(10, min(95, score))

    if score < 35: nivel = "Baixo"
    elif score < 60: nivel = "Moderado"
    elif score < 80: nivel = "Alto"
    else: nivel = "Muito alto"

    return {
        "score_risco": score,
        "nivel_risco": nivel,
        "n_ativos": n_ativos,
        "n_tipos": n_tipos,
        "maior_concentracao": {"ticker": concentracao[0]["ticker"], "pct": maior_pct} if concentracao else None,
        "concentracao_por_ativo": concentracao,
        "concentracao_por_tipo": por_tipo,
        "sugestoes": gerar_sugestoes(score, maior_pct, n_tipos, n_ativos, concentracao)
    }


def gerar_sugestoes(score, maior_pct, n_tipos, n_ativos, concentracao):
    sugestoes = []
    if maior_pct > 40:
        sugestoes.append(f"{concentracao[0]['ticker']} representa {maior_pct:.0f}% da carteira — considere reduzir a concentração")
    if n_tipos == 1:
        sugestoes.append("Carteira concentrada em um único tipo de ativo — diversifique entre ações, FIIs e renda fixa")
    if n_ativos < 5:
        sugestoes.append("Poucos ativos aumentam o risco específico — considere ampliar para 8-15 ativos")
    if not sugestoes:
        sugestoes.append("Carteira bem diversificada — continue monitorando a concentração")
    return sugestoes


def comparar_ibovespa(primeira_compra: str, patrimonio_atual: float, total_investido: float) -> dict:
    """
    Compara rentabilidade da carteira com o Ibovespa desde a primeira compra.
    """
    try:
        if not primeira_compra:
            return {}

        inicio = datetime.strptime(primeira_compra[:10], "%Y-%m-%d")
        hoje = datetime.today()

        ibov = yf.download("^BVSP", start=inicio, end=hoje, progress=False, auto_adjust=True)

        if ibov.empty:
            return {}

        preco_inicio = float(ibov["Close"].iloc[0])
        preco_fim = float(ibov["Close"].iloc[-1])
        rent_ibov = (preco_fim - preco_inicio) / preco_inicio * 100

        rent_carteira = (patrimonio_atual - total_investido) / total_investido * 100 if total_investido > 0 else 0

        return {
            "rentabilidade_carteira_pct": round(rent_carteira, 2),
            "rentabilidade_ibovespa_pct": round(rent_ibov, 2),
            "diferenca_pct": round(rent_carteira - rent_ibov, 2),
            "periodo_dias": (hoje - inicio).days,
            "ibov_inicio": round(preco_inicio, 2),
            "ibov_atual": round(preco_fim, 2),
            "primeira_compra": primeira_compra[:10]
        }
    except Exception as e:
        print("Erro Ibovespa:", e)
        return {}
