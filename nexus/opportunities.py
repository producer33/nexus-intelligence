"""Análise de oportunidades: sinais técnicos determinísticos + contexto macro, com evidências.
Não é recomendação de investimento: classifica o estado dos dados, não prevê preços."""
from datetime import date, timedelta
from . import quant

ATIVOS = ["ibov", "petr4", "vale3", "itub4", "sp500", "brent", "ouro", "btc"]
BENCH = {"petr4": "ibov", "vale3": "ibov", "itub4": "ibov"}

def classe(score):
    if score >= 4: return "Sinal técnico de compra"
    if score >= 2: return "Viés positivo"
    if score >= -1: return "Neutro / aguardar"
    if score >= -3: return "Viés negativo"
    return "Sinal técnico de venda / redução"

def _ret_rel(pts, bench_pts, n=63):
    if len(pts) <= n or not bench_pts:
        return None
    d0 = pts[-n - 1][0]
    b = dict(bench_pts)
    if d0 not in b or not b.get(pts[-1][0]):
        return None
    return (pts[-1][1] / pts[-n - 1][1] - 1) - (b[pts[-1][0]] / b[d0] - 1)

def analisar(s, bench=None):
    base = {"id": s["id"], "nome": s["nome"], "fonte": s["fonte"], "referencia": s.get("referencia")}
    if s["status"] == "erro" or len(s["pontos"]) < 30:
        return {**base, "sinal": "Indisponível", "score": None, "confianca": "Nenhuma",
                "evidencias": [], "riscos": [], "invalidacao": None,
                "aviso": "Sem dados suficientes para análise. Nada foi estimado."}
    px = [v for _, v in s["pontos"]]
    last = px[-1]
    ev, score = [], 0
    s50, s200 = quant.sma(px, 50), quant.sma(px, 200)
    def pt(cond, txt, v=1):
        nonlocal score
        score += v if cond else -v
        ev.append({"pontos": v if cond else -v, "texto": txt})
    pt(last > s50, f"Preço {last:,.2f} {'acima' if last > s50 else 'abaixo'} da média de 50 dias ({s50:,.2f})")
    if s200:
        pt(last > s200, f"Preço {'acima' if last > s200 else 'abaixo'} da média de 200 dias ({s200:,.2f})")
        pt(s50 > s200, f"Média de 50 {'acima' if s50 > s200 else 'abaixo'} da de 200 dias")
    else:
        ev.append({"pontos": 0, "texto": "Histórico < 200 dias: tendência de longo prazo não avaliada"})
    if len(px) > 63:
        r3 = px[-1] / px[-64] - 1
        pt(r3 > 0, f"Retorno de 3 meses {r3*100:+.1f}%")
    r = quant.rsi(px)
    if r is not None:
        if r > 70:
            score -= 1; ev.append({"pontos": -1, "texto": f"RSI {r:.0f}: sobrecomprado (risco de correção)"})
        elif r < 30:
            score += 1; ev.append({"pontos": 1, "texto": f"RSI {r:.0f}: sobrevendido (possível repique, sujeito a continuar caindo)"})
        else:
            ev.append({"pontos": 0, "texto": f"RSI {r:.0f}: zona neutra"})
    if bench:
        rr = _ret_rel(s["pontos"], bench["pontos"])
        if rr is not None:
            pt(rr > 0, f"Força relativa vs Ibovespa (3m): {rr*100:+.1f} p.p.")
    rets = quant.retornos(px)
    pico = max(px)
    riscos = [f"Volatilidade anualizada {quant.volatilidade_anual(rets)*100:.0f}%",
              f"Queda máxima em 12m {quant.max_drawdown(px)*100:.0f}%",
              f"Distância do topo de 12m {(last/pico-1)*100:.1f}%"]
    v = quant.var_historico(rets)
    if v is not None:
        riscos.append(f"Perda diária histórica em 5% dos piores dias: ≥{v*100:.1f}% (descritivo)")
    if score >= 2:
        inval = f"A leitura positiva perde força se fechar abaixo da média de 50 dias ({s50:,.2f})."
    elif score <= -2:
        inval = f"A leitura negativa perde força se recuperar a média de 50 dias ({s50:,.2f}) com RSI acima de 50."
    else:
        inval = "Sinais mistos: aguardar rompimento claro acima ou abaixo das médias."
    aud = [a["severidade"] for a in s.get("auditoria", [])]
    if s["status"] == "desatualizado" or "Alto" in aud or "Crítico" in aud:
        conf, aviso = "Baixa", "Dados desatualizados ou com alerta de auditoria: tratar com cautela."
    elif not s200 or "Moderado" in aud:
        conf, aviso = "Média", "Histórico curto ou dado com alerta moderado."
    else:
        conf, aviso = "Alta (dos dados)", None
    return {**base, "sinal": classe(score), "score": score, "confianca": conf, "evidencias": ev,
            "riscos": riscos, "invalidacao": inval, "aviso": aviso}

def _em(pts, dias_atras):
    d = date.fromisoformat(pts[-1][0]) - timedelta(days=dias_atras)
    ant = [v for dd, v in pts if date.fromisoformat(dd) <= d]
    return ant[-1] if ant else None

def contexto(m):
    c = []
    def ok(i): return i in m and m[i]["status"] != "erro" and m[i]["pontos"]
    if ok("selic_meta"):
        p = m["selic_meta"]["pontos"]; a = _em(p, 180)
        c.append(f"Selic meta {p[-1][1]:.2f}% a.a." + (f" (há 6 meses: {a:.2f}%)" if a is not None else ""))
    if ok("ipca_mensal"):
        c.append(f"IPCA do último mês divulgado ({m['ipca_mensal']['referencia']}): {m['ipca_mensal']['pontos'][-1][1]:.2f}%")
    if ok("ust10y"):
        p = m["ust10y"]["pontos"]; a = _em(p, 90)
        c.append(f"Treasury 10 anos {p[-1][1]:.2f}%" + (f" ({p[-1][1]-a:+.2f} p.p. em 3 meses)" if a else ""))
    for i, n in (("usdbrl_ptax", "Dólar"), ("brent", "Brent")):
        if ok(i):
            p = m[i]["pontos"]; a = _em(p, 90)
            if a: c.append(f"{n} {(p[-1][1]/a-1)*100:+.1f}% em 3 meses")
    return c

def relatorio(series):
    m = {s["id"]: s for s in series}
    ativos = [analisar(m[i], m.get(BENCH.get(i))) for i in ATIVOS if i in m]
    ativos.sort(key=lambda a: (a["score"] is None, -(a["score"] or 0)))
    return {"ativos": ativos, "contexto": contexto(m),
            "hipoteses": ["Juros altos por mais tempo tendem a pesar sobre ativos de risco e favorecer renda fixa (hipótese, não previsão).",
                          "Dólar e Brent em alta costumam beneficiar exportadoras de commodities (PETR4, VALE3) e pressionar a inflação."],
            "metodo": "Pontuação de -6 a +6: tendência (média 50/200), retorno 3m, RSI 14 e força relativa. Quanto mais evidências na mesma direção, maior o |score|.",
            "aviso": "Classificação técnica de dados públicos, não recomendação de compra ou venda. Não considera seu perfil, impostos, custos nem fundamentos das empresas. Decisão e risco são seus."}
