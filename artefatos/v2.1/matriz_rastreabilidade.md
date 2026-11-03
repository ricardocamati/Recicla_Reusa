# Matriz de rastreabilidade — v2.1

**Situação da implementação: Etapas 9 e 10 concluídas.** V21-RF-01 (conta de pessoa), V21-RF-02 (catálogo de ofertas) e V21-RF-03 (cadastro por intenção) estão implementados e cobertos por testes; V21-RF-14 tem arquivamento básico, com avisos de interesses pendentes previstos para a Etapa 11. As demais linhas seguem planejadas.

## Requisitos funcionais

| Requisito | Regras | Casos escritos | Superfícies de implementação futuras |
|---|---|---|---|
| V21-RF-01 — Conta de pessoa e operação | V21-RN-01, V21-RN-21, V21-RN-22 | V21-CT-01, V21-CT-29 — **implementados** | `tipo` restrito a `pessoa`/`ponto_coleta`, cadastro público só de pessoa, operador provisionado; migração em `scripts/migrar_papeis_v2_1.py` |
| V21-RF-02 — Catálogo de ofertas | V21-RN-03, V21-RN-09, V21-RN-15, V21-RN-19, V21-RN-20, V21-RN-21 | V21-CT-02, V21-CT-03 — **implementados** | `GET /api/itens` só devolve doação/venda `disponivel`; descarte/rascunho/arquivado/concluído ficam fora; `incluir_reservados` explícito; busca textual, modalidade, categoria, condição, cidade e faixa de preço de revenda |
| V21-RF-03 — Cadastro por intenção e gestão | V21-RN-02, V21-RN-04, V21-RN-20, V21-RN-22 | V21-CT-04, V21-CT-25 — **cadastro implementado** | Assistente em três passos, `publicar` no cadastro, `POST /api/itens/{id}/publicar`, `POST /{id}/arquivar` e grupos Ativos/Em andamento/Encerrados em `GET /api/itens/meus` |
| V21-RF-04 — Interesse e reabertura | V21-RN-05 | V21-CT-05, V21-CT-06 | `frontend/js/interesses.js::loadInterests`, `app/services/interesse_service.py::InteresseService.criar` |
| V21-RF-05 — Reserva e liberação | V21-RN-06, V21-RN-07, V21-RN-20 | V21-CT-07, V21-CT-08, V21-CT-27 | `app/services/interesse_service.py::InteresseService.transicionar`, `frontend/js/interesses.js::updateInterest` |
| V21-RF-06 — Combinação da entrega | V21-RN-08 | V21-CT-09 | Novo fluxo de combinação a implementar em API/service e `frontend/js/interesses.js` |
| V21-RF-07 — Entrega e recebimento bilateral | V21-RN-03, V21-RN-09, V21-RN-10, V21-RN-15, V21-RN-19, V21-RN-20, V21-RN-22 | V21-CT-10, V21-CT-11, V21-CT-26, V21-CT-30 | `app/services/item_service.py::ItemService.transicionar` e novos comandos de confirmação |
| V21-RF-08 — Venda direta com preço reservado | V21-RN-02, V21-RN-06, V21-RN-07, V21-RN-09 | V21-CT-08, V21-CT-12 | `frontend/js/itens.js::secaoTransicoes`, `app/schemas/item.py`; remover obrigatoriedade de reparo |
| V21-RF-09 — Escolha guiada do ponto | V21-RN-11, V21-RN-12, V21-RN-20, V21-RN-21 | V21-CT-13, V21-CT-14, V21-CT-15 | `frontend/js/itens.js::prepararEncaminhamento`; novo assistente e API de tentativas |
| V21-RF-10 — Cancelar/trocar encaminhamento | V21-RN-12, V21-RN-13, V21-RN-15, V21-RN-20, V21-RN-22 | V21-CT-16, V21-CT-17, V21-CT-26, V21-CT-27 | Novos comandos de encaminhamento; `app/repositories/` e formulário de seleção |
| V21-RF-11 — Operação do ponto | V21-RN-01, V21-RN-03, V21-RN-09, V21-RN-14, V21-RN-15, V21-RN-16, V21-RN-19, V21-RN-20, V21-RN-21, V21-RN-22 | V21-CT-18, V21-CT-19, V21-CT-20, V21-CT-21, V21-CT-29, V21-CT-30 | `frontend/js/pontos.js::loadIncomingItems` / `confirmarColeta`, `app/api/pontos_coleta.py::criar_router_pontos` |
| V21-RF-12 — Avisos acionáveis | V21-RN-18, V21-RN-20 | V21-CT-22, V21-CT-27 | `app/repositories/notificacao_eventos.py`, `frontend/js/notificacoes.js::loadNotificacoes` |
| V21-RF-13 — Indicadores precisos | V21-RN-03, V21-RN-09, V21-RN-15, V21-RN-19, V21-RN-20 | V21-CT-23, V21-CT-30 | `frontend/js/home.js::carregarIndicadores`, `app/api/indicadores.py` |
| V21-RF-14 — Arquivamento e histórico | V21-RN-04, V21-RN-17 | V21-CT-24 | `frontend/js/itens.js::deleteItem`, `app/repositories/mongo_item_repository.py`; novo arquivamento |
| V21-RF-16 — Indicar lugar de descarte | V21-RN-11, V21-RN-23 | V21-CT-31, V21-CT-32, V21-CT-33, V21-CT-34 | `frontend/js/itens.js`, `app/api/itens.py`, `app/schemas/item.py`, `app/services/item_service.py` |
| V21-RF-15 — Navegação e recuperação | V21-RN-01, V21-RN-03, V21-RN-04, V21-RN-11, V21-RN-16, V21-RN-20, V21-RN-21, V21-RN-22 | V21-CT-03, V21-CT-14, V21-CT-21, V21-CT-25, V21-CT-26, V21-CT-28, V21-CT-29 | `frontend/js/comum.js`, `frontend/js/api.js`, componentes das páginas |

## Requisitos não funcionais

| Requisito | Cenários/validação futura | Evidência exigida |
|---|---|---|
| V21-RNF-01 | Estratégia de dados e preservação do comportamento v1.0 | Decisão autorizada; nenhuma exclusão nesta fase |
| V21-RNF-02 | V21-CT-07, V21-CT-15, V21-CT-16, V21-CT-20, V21-CT-26, V21-CT-27, V21-CT-29 | Testes de API, índices reais, disputa/rollback em replica set |
| V21-RNF-03 | V21-CT-03, V21-CT-14, V21-CT-21, V21-CT-25, V21-CT-28 | Navegador, teclado e viewport pequeno |
| V21-RNF-04 | V21-CT-30 e suíte completa | Comandos/saídas reais; fixtures isoladas e limpeza comprovada |
| V21-RNF-05 | Conferência de regras/HTTP/DTOs e casos de erro | OpenAPI futura confrontada com aplicação; não existe runtime v2.0 nem v2.1 ainda |
| V21-RNF-06 | V21-CT-29 e inspeção de fronteira | Proteções existentes preservadas sem ampliar tópico I |
| V21-RNF-07 | V21-CT-31, V21-CT-32 | Indicação legível apenas pelo autor; nenhuma exposição a operador ou terceiro |

## Regras e origem documental

- Regras V21-RN-01 a V21-RN-23 estão em [regras_de_negocio.md](regras_de_negocio.md).
- Requisitos funcionais e não funcionais: [requisitos.md](requisitos.md).
- Jornadas J-01 a J-05: [jornadas_frontend.md](jornadas_frontend.md).
- Critérios executáveis futuros: [casos_de_teste.md](casos_de_teste.md).
- Estrutura e operações propostas: [modelo_dados.md](modelo_dados.md) e [contratos_http.md](contratos_http.md).

## Evidências e limites

Nesta preparação: somente leitura do projeto, elaboração e validação documental (links, IDs, referências e rastreabilidade). Não há commit de implementação, suíte v2.1 aprovada, coleção criada ou jornada v2.1 validada.

A [v2.0](../v2.0/README.md) é apenas especificação nesta reorganização e não traz evidências de execução. Nova validação deverá produzir testes de comportamento, contrato, concorrência relevante e três jornadas em Docker. Não copiar percentuais ou contagens antigas para declarar aprovação da versão nova.

## Revisão antes da implementação

- Resolver alternativas de confirmação bilateral, modalidade fixa, reabertura e coleção de tentativas.
- Fixar tipos/limites dos contratos, inclusive moeda e escopo de idempotência.
- Definir conversão de perfis/dados existentes e casos de regressão.
- Conferir que todo estado tem ações e saídas legítimas; bloqueios intencionais precisam de mensagem.
- Depois da execução real, acrescentar vínculos de cada caso aos testes/símbolos efetivos e relatórios, sem alterar o passado da v2.0.
