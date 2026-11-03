# Verificação — Etapa 7: indicadores e telas

## Escopo entregue

- `GET /api/indicadores` autenticado, somando apenas itens concluídos: `doados`, `coletados`, `vendidos` e `total`. Itens `disponivel`, `reservado`, `encaminhado`, `em_avaliacao` e `recondicionado` não entram na conta.
- Telas novas em HTML e JavaScript modular, sem build: `interesses.html`, `notificacoes.html` e `pontos.html`.
- Painel de indicadores em `itens.html`, alimentado pelo endpoint autenticado.
- `docs/openapi.json` gerado do runtime por `scripts/gerar_openapi.py` e comparado por teste; diferenças registradas em [openapi.md](openapi.md).
- Selenium cobre as nove telas, incluindo as três novas.

## Resultados executados

- Suíte completa com integração habilitada: **168 testes passaram**, sem casos ignorados. Um aviso de depreciação do `BlockingPortal` vem do TestClient/Starlette.
- **24 testes executam contra MongoDB real** (replica set `rs0`, banco exclusivo por UUID): 10 de interesses, 5 de fluxos, 9 de notificações. O caso novo conclui uma doação e uma revenda, cria um descarte disponível e confirma `{"doados": 1, "coletados": 0, "vendidos": 1, "total": 2}`; sem sessão, o endpoint responde `401`.
- `tests/test_indicadores_v2.py` prova que só status concluídos entram no total e que base sem conclusão retorna zeros.
- `tests/test_openapi_runtime.py` compara o snapshot com a geração do runtime e confere as treze rotas de negócio documentadas.
- `tests/test_frontend.py` verifica as novas páginas, os módulos por responsabilidade, as rotas consumidas e a ausência de `innerHTML`, `localStorage` e `document.cookie`.
- `tests/test_selenium_frontend.py` percorre as nove telas em modo escuro, com API simulada, e confirma título, folha de estilo e ausência de referências institucionais.

## Stack Docker

Backend e frontend reconstruídos e saudáveis. As três páginas novas responderam `200` no frontend publicado, `GET /api/indicadores` sem sessão respondeu `401` e o `/openapi.json` do container anunciou a rota de indicadores.

## Limites

- O painel de indicadores aparece apenas na área do doador (`itens.html`); a consulta em si aceita qualquer sessão autenticada.
- A tela de pontos permite cadastrar e excluir para contas `ponto_coleta`; a edição existe na API (`PUT`) mas não foi exposta nessa tela. A criação dessas contas continua sendo um comando local, fora do cadastro público.
- Os indicadores são totais da plataforma, não recortados por conta ou por proprietário.
- A OpenAPI não declara esquema para erros de negócio nem o cookie de sessão; ver as diferenças em [openapi.md](openapi.md).
- Selenium depende de Chrome local; sem ele o caso é ignorado, e essa execução não comprova as telas.

## Reproduzir

```bash
python -m pytest -q --no-cov -o addopts= --tb=short
python scripts/gerar_openapi.py
```
