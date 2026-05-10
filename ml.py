# =========================
# ANALISAR APORTES
# =========================
def analisar_aportes(aportes):
    if not aportes:
        return None

    total = {
        "fiis": 0,
        "acoes": 0,
        "inter": 0,
        "fixa": 0,
        "caixa": 0
    }

    for a in aportes:
        total["fiis"] += a.get("fiis", 0)
        total["acoes"] += a.get("acoes", 0)
        total["inter"] += a.get("inter", 0)
        total["fixa"] += a.get("fixa", 0)
        total["caixa"] += a.get("caixa", 0)

    soma = sum(total.values())

    if soma == 0:
        return None

    proporcao = {k: v / soma for k, v in total.items()}

    return proporcao


# =========================
# SUGERIR APORTE
# =========================
def sugerir_aporte(aportes, valor):
    proporcao = analisar_aportes(aportes)

    if not proporcao:
        return None

    sugestao = {
        k: round(v * valor, 2)
        for k, v in proporcao.items()
    }

    return sugestao


# =========================
# DETECTAR DESBALANCEAMENTO
# =========================
def detectar_desbalanceamento(proporcao, alvo=None, tolerancia=0.05):
    """
    Compara a alocação atual com uma alocação alvo
    """

    if not proporcao:
        return None

    # Alocação padrão (pode ajustar depois)
    if not alvo:
        alvo = {
            "fiis": 0.25,
            "acoes": 0.35,
            "inter": 0.15,
            "fixa": 0.20,
            "caixa": 0.05
        }

    desbalanceado = {}

    for k in proporcao:
        diff = proporcao[k] - alvo.get(k, 0)

        if abs(diff) > tolerancia:
            desbalanceado[k] = {
                "atual": round(proporcao[k], 2),
                "alvo": alvo[k],
                "diferenca": round(diff, 2)
            }

    return desbalanceado


# =========================
# SUGERIR REBALANCEAMENTO
# =========================
def sugerir_rebalanceamento(proporcao, patrimonio_total, alvo=None):
    if not proporcao:
        return None

    if not alvo:
        alvo = {
            "fiis": 0.25,
            "acoes": 0.35,
            "inter": 0.15,
            "fixa": 0.20,
            "caixa": 0.05
        }

    ajuste = {}

    for k in proporcao:
        atual_valor = proporcao[k] * patrimonio_total
        ideal_valor = alvo[k] * patrimonio_total

        ajuste[k] = round(ideal_valor - atual_valor, 2)

    return ajuste