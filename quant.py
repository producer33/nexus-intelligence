"""Camada quantitativa determinística (sem IA)."""
import math, statistics as st

def retornos(precos):
    return [b / a - 1 for a, b in zip(precos, precos[1:]) if a]

def retornos_log(precos):
    return [math.log(b / a) for a, b in zip(precos, precos[1:]) if a > 0 and b > 0]

def retorno_acumulado(precos):
    return precos[-1] / precos[0] - 1 if len(precos) > 1 and precos[0] else None

def volatilidade_anual(rets, periodos=252):
    return st.stdev(rets) * math.sqrt(periodos) if len(rets) > 1 else None

def max_drawdown(precos):
    pico, mdd = precos[0], 0.0
    for p in precos:
        pico = max(pico, p)
        mdd = min(mdd, p / pico - 1)
    return mdd

def correlacao(a, b):
    n = min(len(a), len(b))
    if n < 3:
        return None
    a, b = a[-n:], b[-n:]
    if st.pstdev(a) == 0 or st.pstdev(b) == 0:
        return None
    return st.correlation(a, b)

def var_historico(rets, nivel=0.95):
    """VaR histórico de 1 período (perda positiva). Descritivo, não preditivo."""
    if len(rets) < 20:
        return None
    s = sorted(rets)
    return -s[int((1 - nivel) * len(s))]

def sma(px, n):
    return sum(px[-n:]) / n if len(px) >= n else None

def rsi(px, n=14):
    """RSI de Wilder. None se histórico insuficiente."""
    if len(px) <= n:
        return None
    d = [b - a for a, b in zip(px, px[1:])]
    g = [max(x, 0) for x in d]; l = [max(-x, 0) for x in d]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    for i in range(n, len(d)):
        ag = (ag * (n - 1) + g[i]) / n
        al = (al * (n - 1) + l[i]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
