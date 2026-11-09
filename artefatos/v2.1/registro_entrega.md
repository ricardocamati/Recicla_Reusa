# Registro da entrega — v2.1 (segunda entrega da AEP)

## Identificação

- **Entrega:** segunda entrega da AEP 2026.2 — 6S.
- **Marco final:** commit da `main` após o merge do PR #29 (correção de leitura de ofertas de bancos anteriores), que inclui o PR #27 (Etapas 16 a 20).
- **Pull requests:** [#27](https://github.com/ricardocamati/Recicla_Reusa/pull/27) — 7 commits, 76 arquivos, Etapas 16 a 20; [#29](https://github.com/ricardocamati/Recicla_Reusa/pull/29) — 2 arquivos, leitura de ofertas legadas.
- **Primeira entrega preservada:** tag `v1.0`.
- **Tag ou release da segunda entrega:** não emitida por decisão da equipe; o enunciado aceita commit informado como identificação da versão.
- **Suíte no marco final:** 310 testes coletados, 310 executados, 0 falhas, 0 ignorados, cobertura **91,56%** sobre `app`, com MongoDB real em replica set e Selenium.
- **Vídeo de 3 a 5 minutos:** pendente; a URL ainda não foi informada.

## Escopo entregue

- Conta única de pessoa, perfil operacional de ponto de coleta e sessão em cookie `HttpOnly` com senha em `scrypt`.
- Ofertas de **doação** e **revenda** com rascunho, publicação, arquivamento, interesse, reserva reversível, combinação de entrega revisada e conclusão bilateral.
- **Diretório público de locais de descarte** sem exigir conta, equipamento ou cadastro de item, com filtros de cidade e categoria aplicados antes da paginação e detalhe com cópia de endereço.
- **Gestão "Meus locais"** restrita ao operador responsável, incluindo locais inativos, sem fila de recebimento.
- Avisos acionáveis das ofertas, com privacidade por destinatário e unicidade por evento.
- Indicadores de ofertas confirmadas (`doados`, `vendidos`, `ofertas_ativas`, `pendencias`, `total`) e contagem cadastral `locais_ativos` separada.

Retirado do produto nesta revisão: o descarte por equipamento, com encaminhamentos, entrega prevista, recebimento em ponto e destinação informada. As rotas, modelos, campos e testes exclusivos foram removidos do código, sem resposta de compatibilidade, aba histórica ou migração de banco.

## Modelo de dados

Cinco coleções em MongoDB, com referências por `ObjectId` e endereço aninhado:

| Coleção | Papel |
|---|---|
| `usuarios` | conta de pessoa ou operador, endereço aninhado e hash da senha |
| `itens` | ofertas de doação/revenda, especificações, histórico e referências dos participantes |
| `interesses` | relação item/pessoa, tentativa, combinação revisada e preço selecionado |
| `pontos_coleta` | locais do diretório, categorias aceitas, horário e situação ativa |
| `notificacoes` | avisos por destinatário, evento e leitura |

Atende ao requisito de múltiplas coleções relacionadas e de pelo menos uma estrutura complexa: endereço aninhado, listas de eventos de `historico` e o subdocumento `combinacao` com revisão, proponente e aceitante.

## Evolução em relação à primeira entrega

A v1.0 tinha duas coleções com CRUD, perfis `doador`/`beneficiario` e um fluxo único de item. A segunda entrega introduziu conta única de pessoa, perfil operacional, interesses com reserva transacional, combinação de entrega, avisos, indicadores e o diretório público de locais, além de retirar o descarte por equipamento. O histórico por etapa está no [TODO](../../TODO.md) e nos PRs #11 a #27.

## Evidências reproduzíveis

| Evidência | Comando ou arquivo | Tipo |
|---|---|---|
| Suíte e cobertura | `.venv/Scripts/python.exe -m pytest` | automatizada; exige `--cov-fail-under=70`, configurado em `pyproject.toml` |
| Diretório público e gestão | `pytest tests/test_diretorio_publico.py tests/test_etapa18_api.py tests/test_etapa18_frontend.py` | automatizada, API e Chrome headless |
| Avisos e indicadores | Avisos, indicadores e leitura de ofertas legadas | `pytest tests/test_notificacoes_runtime.py tests/test_etapa19_coerencia.py tests/test_mongo_item_repository.py` | automatizada, replica set real |
| Navegação e telas | `pytest tests/test_selenium_frontend.py tests/test_onde_descartar_selenium.py` | automatizada, Chrome headless |
| Jornadas completas | `scripts/validar_jornadas_v2.py` na stack isolada | doação, venda e consulta anônima, com auditoria de datas e limpeza seletiva |
| CRUD E2E na stack | `scripts/smoke_api_docker.py --crud` | mutação temporária com limpeza |
| Contrato HTTP | `docs/http-api.md` e `docs/openapi.md` | documentação e snapshot gerado do runtime |

Os testes que dependem de banco exigem `INTERESSES_TEST_MONGO_URI` apontando para uma instância de replica set de teste; sem a variável, esses cenários são ignorados e não contam como aprovados. Nenhuma evidência usa credenciais, tokens ou dados pessoais.

## Limites conhecidos

- O brake de "aguardando confirmação" sem confirmação da contraparte permanece aberto por decisão de produto; a PoC não resolve disputa nem presume recebimento por tempo.
- Versões otimistas genéricas e chaves de operação (`id_operacao`) descritas no desenho v2.1 não são campos implementados; as garantias efetivas estão nos contratos e testes.
- A jornada de consulta pública não comprova reciclagem: consultar um local não registra entrega.
- O povoamento de demonstração foi validado em banco de teste; aplicá-lo ao banco de demonstração existente é ação separada, sob autorização da equipe.
- Não há pipeline de CI configurada no repositório; a evidência de testes é a execução local reproduzível.

## Registro de identificação

Preencher no formulário da AEP antes do envio:

- **Curso:** Engenharia de Software — 6S
- **Série:** 6S
- **Acadêmicos e RA:** a preencher
- **Título da PoC:** Recicla/Reusa
- **Link do GitHub:** https://github.com/ricardocamati/Recicla_Reusa
- **Link do vídeo (YouTube):** a preencher
