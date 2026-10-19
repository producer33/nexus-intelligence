# NEXUS Intelligence (fase 1)

Plataforma gratuita de inteligência financeira: coleta dados públicos (BCB, Yahoo Finance, CoinGecko),
calcula métricas determinísticas, audita a qualidade e publica um dashboard estático.

## Hospedagem gratuita (GitHub Pages + Actions, sem servidor, sem chave de API)
1. Crie um repositório **público** no GitHub e envie estes arquivos.
2. Settings → Pages → Source: *Deploy from a branch* → branch `main`, pasta `/docs`.
3. Actions → "Atualizar dados e publicar" → *Run workflow* (a 1ª coleta). Depois roda sozinho em dias úteis.
4. O site fica em `https://SEU_USUARIO.github.io/NOME_DO_REPO/`.

## Local
    python -m unittest discover -s tests
    python -m nexus.build && python -m http.server -d docs

## Estado das funcionalidades
- Testada (testes unitários): quant, parsers, auditor, cache de último dado válido.
- Implementada, **não validada com dados reais** (sem acesso à rede no ambiente de criação): coleta nas APIs.
- Planejada: agentes de IA (macro, empresas, risco), carteira/B3, cenários, registro de previsões, relatório diário.

Limites conhecidos: Yahoo e CoinGecko são gratuitos sem garantia de SLA nem de licença para redistribuição comercial;
dados podem ter atraso. Não é recomendação de investimento.
