import yfinance as yf

def get_preco(ticker):
    try:
        acao = yf.Ticker(ticker + ".SA")
        data = acao.history(period="1d")
        return float(data["Close"].iloc[-1])
    except:
        return None