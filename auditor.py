"""Auditor independente: alerta/reprova dados sem depender de quem produziu a análise."""
from datetime import date

MENSAIS = ("ipca_mensal", "selic_meta")

def idade_dias(ref, hoje=None):
    return ((hoje or date.today()) - date.fromisoformat(ref)).days

def auditar(serie, hoje=None):
    ach = []
    if serie["status"] == "erro":
        return [("Alto", f"sem dados: {serie.get('erro')}")]
    if serie["status"] == "desatualizado":
        ach.append(("Alto", f"coleta falhou; exibindo último dado válido ({serie.get('erro')})"))
    lim = 75 if serie["id"] in MENSAIS else 5
    i = idade_dias(serie["referencia"], hoje)
    if i > lim:
        ach.append(("Moderado", f"dado desatualizado: {i} dias (limite {lim})"))
    if serie["id"] not in MENSAIS and any(v <= 0 for _, v in serie["pontos"]):
        ach.append(("Crítico", "valores não positivos em série de preço"))
    if len(serie["pontos"]) < 30 and serie["id"] not in MENSAIS:
        ach.append(("Moderado", "histórico curto (<30 pontos); métricas pouco confiáveis"))
    return ach
