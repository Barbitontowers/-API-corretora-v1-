import requests
import yfinance as yf
from datetime import date

# =========================
# AÇÕES E FIIs — Yahoo Finance
# Tickers B3 precisam do sufixo .SA
# =========================
def buscar_b3(tickers: list[str]) -> dict:
    resultado = {}
    if not tickers:
        return resultado

    tickers_yf = [t.upper() + ".SA" for t in tickers]

    try:
        dados = yf.download(
            tickers_yf,
            period="1d",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        for ticker_original, ticker_yf in zip(tickers, tickers_yf):
            try:
                if len(tickers) == 1:
                    preco = float(dados["Close"].iloc[-1])
                else:
                    preco = float(dados["Close"][ticker_yf].iloc[-1])

                resultado[ticker_original.upper()] = round(preco, 2)
            except Exception:
                resultado[ticker_original.upper()] = None

    except Exception as e:
        print("Erro Yahoo Finance:", e)

    return resultado


# =========================
# CRIPTOMOEDAS — CoinGecko (gratuito, sem chave)
# =========================
COINGECKO_IDS = {
    "BTC":  "bitcoin",
    "ETH":  "ethereum",
    "BNB":  "binancecoin",
    "SOL":  "solana",
    "ADA":  "cardano",
    "XRP":  "ripple",
    "DOGE": "dogecoin",
    "DOT":  "polkadot",
    "MATIC":"matic-network",
    "LTC":  "litecoin",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI":  "uniswap",
    "ATOM": "cosmos",
}

def buscar_cripto(tickers: list[str]) -> dict:
    resultado = {}
    if not tickers:
        return resultado

    ids = []
    mapa = {}  # id -> ticker original

    for t in tickers:
        cg_id = COINGECKO_IDS.get(t.upper())
        if cg_id:
            ids.append(cg_id)
            mapa[cg_id] = t.upper()
        else:
            resultado[t.upper()] = None

    if not ids:
        return resultado

    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ",".join(ids),
            "vs_currencies": "brl"
        }
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        for cg_id, ticker in mapa.items():
            try:
                resultado[ticker] = round(data[cg_id]["brl"], 2)
            except Exception:
                resultado[ticker] = None

    except Exception as e:
        print("Erro CoinGecko:", e)

    return resultado


# =========================
# RENDA FIXA — retorna rendimento estimado
# Usa a taxa SELIC/CDI atual via API do Banco Central
# =========================
def buscar_selic() -> float:
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        res = requests.get(url, timeout=10)
        data = res.json()
        taxa_anual = float(data[0]["valor"])
        return taxa_anual
    except Exception:
        return 10.75  # fallback: última SELIC conhecida


def calcular_renda_fixa(preco_medio: float, data_compra: str = None) -> dict:
    selic = buscar_selic()
    taxa_diaria = (1 + selic / 100) ** (1 / 252) - 1

    return {
        "selic_anual": selic,
        "rendimento_diario_pct": round(taxa_diaria * 100, 4),
        "preco_atual_estimado": preco_medio  # sem data de compra, retorna custo
    }


# =========================
# FUNÇÃO PRINCIPAL
# Recebe lista de ativos com tipo e retorna preços
# =========================
def buscar_precos(ativos: list[dict]) -> dict:
    """
    ativos: [{"ticker": "VALE3", "tipo": "acao"}, ...]
    Retorna: {"VALE3": 68.50, "BTC": 312000.0, ...}
    """
    acoes_fiis = [a["ticker"] for a in ativos if a["tipo"] in ("acao", "fii")]
    criptos    = [a["ticker"] for a in ativos if a["tipo"] == "cripto"]

    precos = {}
    precos.update(buscar_b3(acoes_fiis))
    precos.update(buscar_cripto(criptos))

    # Renda fixa: sem preço de mercado, marca como None (calculado por taxa)
    for a in ativos:
        if a["tipo"] == "renda_fixa":
            precos[a["ticker"]] = None

    return precos
