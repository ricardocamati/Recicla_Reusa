# Matriz de rastreabilidade da versão 2.0

Registro histórico do marco v2.0, implementado nas Etapas 1 a 8 e fechado no commit `71e8dfa` (PR #18). As referências de código abaixo descrevem aquele marco; a revisão [v2.1](../v2.1/README.md) substitui parte dos fluxos. A execução atual está documentada no [README](../../README.md), nos testes e nos scripts versionados, sem relatórios de verificação separados.

| Requisito/regra | Casos de teste | Evidência entregue |
|---|---|---|
| V2-RF-01 | V2-CT-01 a V2-CT-04 | `app/models/usuario.py` (`Endereco`), schemas, mapper e `mongo_usuario_repository.py` com leitura compatível do formato plano |
| V2-RF-02 | V2-CT-05 | `app/api/usuarios.py`, `app/services/usuario_service.py`; auditoria em `tests/test_api_usuario.py` |
| V2-RF-03 | V2-CT-06, V2-CT-07 | `app/models/item.py`, `app/schemas/item.py`, `app/repositories/mongo_item_repository.py` |
| V2-RF-04 | V2-CT-08, V2-CT-09 | `GET /api/itens` com cidade, destino, categoria, offset e limite; `frontend/catalogo.html` |
| V2-RF-05 | V2-CT-15, V2-CT-16, V2-CT-21 | `app/services/item_service.py` com histórico acumulativo e CAS por status |
| V2-RF-06 | V2-CT-10, V2-CT-11 | `app/repositories/mongo_interesse_repository.py`; `tests/test_interesses_v2.py` |
| V2-RF-07 | V2-CT-12 | `PATCH /api/interesses/{id}` com decisão transacional e reserva |
| V2-RF-08 | V2-CT-13 | `app/api/pontos_coleta.py`; `tests/test_pontos_coleta_v2.py` |
| V2-RF-09 | V2-CT-14, V2-CT-18 | `ponto_coleta_id` no item, compatibilidade por categoria e bloqueio de exclusão |
| V2-RF-10 | V2-CT-15 | lista `historico` em `ItemResponse` |
| V2-RF-11 | V2-CT-12, V2-CT-17 | fluxo de doação em `tests/test_fluxos_v2.py` e jornada 1 pela interface |
| V2-RF-12 | V2-CT-14, V2-CT-18 | fluxo de descarte com ponto fixado; jornada 2 pela interface |
| V2-RF-13 | V2-CT-19, V2-CT-20 | fluxo de revenda com comprador e valor; jornada 3 pela interface |
| V2-RF-14 | V2-CT-23 | `app/api/indicadores.py` e painel em `frontend/itens.html` |
| V2-RF-15 | V2-CT-05, V2-CT-24 | `tests/test_fluxos_runtime.py` e auditoria UTC das cinco coleções na Etapa 8 |
| V2-RF-16 | — | `docs/openapi.json` gerado do runtime e `docs/openapi.md` com as diferenças |
| V2-RF-17 | V2-CT-26 a V2-CT-30 | `app/services/notificacao_service.py`, `app/api/notificacoes.py`; `tests/test_notificacoes_runtime.py` |
| V2-RN-01 a V2-RN-04 | V2-CT-01 a V2-CT-04, V2-CT-13 | endereço aninhado e validação de CEP |
| V2-RN-05 | V2-CT-01, V2-CT-05, V2-CT-24 | datas UTC com milissegundos, conferidas por auditoria |
| V2-RN-06 a V2-RN-09 | V2-CT-06, V2-CT-07 | criação de item com origem, destino e propriedade |
| V2-RN-10 | V2-CT-16 a V2-CT-19 | `TRANSICOES` em `app/services/item_service.py` |
| V2-RN-11 | V2-CT-15 | histórico somente acumulativo |
| V2-RN-12, V2-RN-13 | V2-CT-10 a V2-CT-12 | interesses únicos e reserva por aceite |
| V2-RN-14 | V2-CT-14, V2-CT-18 | categoria compatível com o ponto |
| V2-RN-15 | V2-CT-19, V2-CT-20 | valor não negativo e comprador distinto do dono |
| V2-RN-16 | V2-CT-17 a V2-CT-21 | item concluído não reabre nem é excluído |
| V2-RN-17, V2-RN-18 | V2-CT-08, V2-CT-22 | catálogo sem endereço privado |
| V2-RN-19 | V2-CT-06 | especificações livres por categoria |
| V2-RN-20 | V2-CT-23 | indicadores apenas de status concluídos |
| V2-RN-21, V2-RN-22 | V2-CT-26, V2-CT-27, V2-CT-30 | destinatários e eventos notificáveis |
| V2-RN-23, V2-RN-25 | V2-CT-28 | leitura restrita ao destinatário, com `lida_em` |
| V2-RN-24 | V2-CT-29 | índice único por `evento_id`/destinatário/item |
| V2-RNF-01 a V2-RNF-03 | V2-CT-06 a V2-CT-30 | cinco coleções com referências e integridade |
| V2-RNF-04 | todos os casos implementados | camadas `api`/`services`/`repositories` em `docs/architecture.md` |
| V2-RNF-05, V2-RNF-06 | V2-CT-25 | **170 testes** aprovados, incluindo 24 contra MongoDB real em replica set |
| V2-RNF-07 | — | `README.md`, `docs/http-api.md`, `docs/architecture.md` e comandos reproduzíveis |
| V2-RNF-08 | — | commits e PRs por etapa; marco v2.0 em `71e8dfa` (PR #18), sem tag v2.0 |
| V2-RNF-09 | V2-CT-08, V2-CT-22 | endereço privado fora do catálogo |
| V2-RNF-10 | V2-CT-24, V2-CT-25 | `compose.yaml` isolado, jornadas em Docker e limpeza seletiva comprovada |

## Evidências externas necessárias

- quadro de tarefas/metodologia: `TODO.md`;
- URL do GitHub: <https://github.com/ricardocamati/Recicla_Reusa>;
- identificação do marco v2.0: commit `71e8dfa` (PR #18); nenhuma tag v2.0 foi criada;
- demonstração da evolução em relação à versão 1.0: PRs #11 a #18, testes versionados e `scripts/validar_jornadas_v2.py` no marco `71e8dfa`.
