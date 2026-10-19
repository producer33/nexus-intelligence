"""Orquestrador mínimo: coleta -> cache incremental -> métricas -> auditoria -> docs/data.json"""
import json, os, sys
from datetime import datetime, timezone
from . import sources, quant, auditor, opportunities

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "docs", "data.json")
NAO_PRECO = auditor.MENSAIS

def metricas(s):
    if s["status"] == "erro" or len(s["pontos"]) < 2:
        return {}
    px = [v for _, v in s["pontos"]]
    r = quant.retornos(px)
    preco = s["id"] not in NAO_PRECO
    return {"ultimo": px[-1], "var_1d": r[-1] if r else None,
            "ret_12m": quant.retorno_acumulado(px) if preco else None,
            "vol_anual": quant.volatilidade_anual(r) if preco else None,
            "max_drawdown": quant.max_drawdown(px) if preco else None,
            "var95_1d": quant.var_historico(r) if preco else None}

def correlacoes(series, ids):
    mapa = {s["id"]: dict(s["pontos"]) for s in series if s["status"] != "erro" and s["id"] in ids}
    comuns = None
    for m in mapa.values():
        comuns = set(m) if comuns is None else comuns & set(m)
    datas = sorted(comuns or [])
    rets = {k: quant.retornos([m[d] for d in datas]) for k, m in mapa.items()}
    return {a: {b: quant.correlacao(rets[a], rets[b]) for b in rets} for a in rets}, len(datas)

def carregar_anterior(caminho=SAIDA):
    try:
        with open(caminho, encoding="utf-8") as f:
            return {s["id"]: s for s in json.load(f)["series"]}
    except Exception:
        return {}

def main(fetch=sources.http_json, saida=SAIDA):
    ant = carregar_anterior(saida)
    series = []
    for item in sources.CATALOGO:
        s = sources.coletar(item, fetch)
        old = ant.get(item[0])
        if s["status"] == "erro" and old and old["status"] in ("ok", "desatualizado"):
            s = {**old, "status": "desatualizado", "erro": s["erro"], "tentativa_em": s["coletado_em"]}
        s["metricas"] = metricas(s)
        s["auditoria"] = [{"severidade": a, "msg": m} for a, m in auditor.auditar(s)]
        series.append(s)
    corr, n = correlacoes(series, ["ibov", "petr4", "vale3", "itub4", "sp500", "btc", "usdbrl_ptax", "ouro"])
    out = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "aviso": "Análise informativa. Não é recomendação de investimento.",
           "series": series, "oportunidades": opportunities.relatorio(series), "correlacoes": {"janela_dias_comuns": n, "matriz": corr}}
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    ok = sum(s["status"] == "ok" for s in series)
    print(f"{ok}/{len(series)} séries atualizadas")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
