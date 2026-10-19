"""Coleta de dados de fontes gratuitas e sem chave: BCB SGS, Yahoo Finance (chart), CoinGecko."""
import json, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 nexus-intelligence/0.1"}

CATALOGO = [
    # id, nome, fonte, tipo, parâmetro, unidade
    ("selic_meta", "Selic meta (% a.a.)", "BCB SGS 432", "bcb", 432, "% a.a."),
    ("ipca_mensal", "IPCA mensal (%)", "BCB SGS 433", "bcb", 433, "% a.m."),
    ("usdbrl_ptax", "Dólar comercial venda", "BCB SGS 1", "bcb", 1, "BRL"),
    ("ibov", "Ibovespa", "Yahoo Finance ^BVSP", "yahoo", "^BVSP", "pontos"),
    ("petr4", "PETR4", "Yahoo Finance PETR4.SA", "yahoo", "PETR4.SA", "BRL"),
    ("vale3", "VALE3", "Yahoo Finance VALE3.SA", "yahoo", "VALE3.SA", "BRL"),
    ("itub4", "ITUB4", "Yahoo Finance ITUB4.SA", "yahoo", "ITUB4.SA", "BRL"),
    ("sp500", "S&P 500", "Yahoo Finance ^GSPC", "yahoo", "^GSPC", "pontos"),
    ("ust10y", "Treasury 10 anos (yield %)", "Yahoo Finance ^TNX", "yahoo", "^TNX", "%"),
    ("brent", "Petróleo Brent", "Yahoo Finance BZ=F", "yahoo", "BZ=F", "USD"),
    ("ouro", "Ouro", "Yahoo Finance GC=F", "yahoo", "GC=F", "USD"),
    ("btc", "Bitcoin", "CoinGecko bitcoin/USD", "coingecko", "bitcoin", "USD"),
]

def url_de(tipo, p):
    if tipo == "bcb":
        return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{p}/dados/ultimos/400?formato=json"
    if tipo == "yahoo":
        return f"https://query1.finance.yahoo.com/v8/finance/chart/{p}?range=1y&interval=1d"
    return f"https://api.coingecko.com/api/v3/coins/{p}/market_chart?vs_currency=usd&days=365&interval=daily"

def parse_bcb(raw):
    return [[datetime.strptime(r["data"], "%d/%m/%Y").date().isoformat(), float(r["valor"])] for r in raw]

def parse_yahoo(raw):
    res = raw["chart"]["result"][0]
    ts, close = res["timestamp"], res["indicators"]["quote"][0]["close"]
    return [[datetime.fromtimestamp(t, timezone.utc).date().isoformat(), float(c)]
            for t, c in zip(ts, close) if c is not None]

def parse_coingecko(raw):
    return [[datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat(), float(v)]
            for t, v in raw["prices"]]

PARSERS = {"bcb": parse_bcb, "yahoo": parse_yahoo, "coingecko": parse_coingecko}

def http_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def coletar(item, fetch=http_json):
    """Retorna registro com proveniência. Nunca inventa dados: em erro, status='erro'."""
    sid, nome, fonte, tipo, p, unidade = item
    url = url_de(tipo, p)
    reg = {"id": sid, "nome": nome, "fonte": fonte, "url": url, "unidade": unidade,
           "coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        pts = PARSERS[tipo](fetch(url))
        pts = [[d, v] for d, v in sorted({d: v for d, v in pts}.items())]
        if not pts:
            raise ValueError("série vazia")
        reg.update(status="ok", pontos=pts, referencia=pts[-1][0])
    except Exception as e:  # noqa
        reg.update(status="erro", erro=f"{type(e).__name__}: {e}", pontos=[], referencia=None)
    return reg
