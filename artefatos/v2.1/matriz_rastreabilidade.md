# Matriz de rastreabilidade — v2.1

As Etapas 9 a 15 têm implementação, com fechamento funcional em `1f36c2b` (PR #25). A tabela relaciona o desenho aos pontos de código; não significa que cada cenário associado esteja integralmente automatizado ou que o PR tenha sido integrado. Limites de contrato, interface e evidência estão descritos abaixo.

## Requisitos funcionais

| Requisito | Regras | Casos escritos | Implementação e limites |
|---|---|---|---|
| V21-RF-01 — Conta de pessoa e operação | V21-RN-01, V21-RN-21, V21-RN-22 | V21-CT-01, V21-CT-29 | `tipo` restrito a `pessoa`/`ponto_coleta`, cadastro público só de pessoa, operador provisionado; migração em `scripts/migrar_papeis_v2_1.py` |
| V21-RF-02 — Catálogo de ofertas | V21-RN-03, V21-RN-09, V21-RN-15, V21-RN-19, V21-RN-20, V21-RN-21 | V21-CT-02, V21-CT-03 | `GET /api/itens` só devolve doação/venda `disponivel`; descarte/rascunho/arquivado/concluído ficam fora; `incluir_reservados` explícito; busca textual, modalidade, categoria, condição, cidade e faixa de preço de revenda |
| V21-RF-03 — Cadastro por intenção e gestão | V21-RN-02, V21-RN-04, V21-RN-20, V21-RN-22 | V21-CT-04, V21-CT-25 | Assistente em três passos, `publicar` no cadastro, `POST /api/itens/{id}/publicar`, `POST /{id}/arquivar` e grupos Ativos/Em andamento/Encerrados em `GET /api/itens/meus` |
| V21-RF-04 — Interesse e reabertura | V21-RN-05 | V21-CT-05, V21-CT-06 | `POST /api/interesses/{id}/acoes` com `desistir`/`retomar`/`reabrir`; uma relação por par, `tentativa`, `motivo` e histórico acumulativo |
| V21-RF-05 — Reserva e liberação | V21-RN-06, V21-RN-07, V21-RN-20 | V21-CT-07, V21-CT-08 | `selecionar` reserva o item e congela `preco_selecionado`; `desistir`/`liberar` devolvem o item, preservam pendentes e registram histórico; concorrência real com um vencedor |
| V21-RF-06 — Combinação da entrega | V21-RN-08 | V21-CT-09 | `PUT /api/interesses/{id}/combinacao` e `/combinacao/aceite`; revisão nova invalida aceite, quem propôs não aceita a própria proposta |
| V21-RF-07 — Entrega e recebimento bilateral | V21-RN-03, V21-RN-09, V21-RN-10, V21-RN-15, V21-RN-19, V21-RN-20, V21-RN-22 | V21-CT-10, V21-CT-11 | `POST /api/itens/{id}/entrega` e `/recebimento`; declarar não conclui, terceiro não confirma, reenvio não duplica e indicadores contam na confirmação |
| V21-RF-08 — Venda direta com preço reservado | V21-RN-02, V21-RN-06, V21-RN-07, V21-RN-09 | V21-CT-08, V21-CT-12 | Venda sem avaliação/reparo obrigatório, `preco_selecionado` congelado na seleção e mesma entrega bilateral; revisão de combinação invalida aceite anterior |
| V21-RF-09 — Escolha guiada do ponto | V21-RN-11, V21-RN-12, V21-RN-20, V21-RN-21 | V21-CT-13, V21-CT-14, V21-CT-15 | Ponto escolhido entre os ativos que aceitam a categoria, com cidade na listagem; o vínculo só nasce no `POST /api/encaminhamentos`, nunca na seleção |
| V21-RF-10 — Cancelar/trocar encaminhamento | V21-RN-12, V21-RN-13, V21-RN-15, V21-RN-20, V21-RN-22 | V21-CT-16, V21-CT-17, V21-CT-26, V21-CT-27 | `cancelar` devolve o item a `aguardando_ponto`; `trocar` encerra a tentativa como `cancelado` e cria outra, sem apagar histórico; categoria fica travada com entrega prevista |
| V21-RF-11 — Operação do ponto | V21-RN-01, V21-RN-03, V21-RN-09, V21-RN-14, V21-RN-15, V21-RN-16, V21-RN-19, V21-RN-20, V21-RN-21, V21-RN-22 | V21-CT-18, V21-CT-19, V21-CT-20, V21-CT-21, V21-CT-29, V21-CT-30 | Fila `escopo=operador` com filtro por local e paginação; operador de outro ponto recebe `403`; `receber` conta uma vez e `nao_recebido` exige motivo; ponto inativo bloqueia novas entregas e avisa autores |
| V21-RF-12 — Avisos acionáveis | V21-RN-18, V21-RN-20 | V21-CT-22, V21-CT-27 | Cada aviso carrega `link` interno, o índice único por evento/destinatário/item evita repetição e a caixa mostra "Abrir" na tela em que o ator age |
| V21-RF-13 — Indicadores precisos | V21-RN-03, V21-RN-09, V21-RN-15, V21-RN-19, V21-RN-20 | V21-CT-23, V21-CT-30 | `ofertas_ativas` e `pendencias` separadas das conclusões confirmadas; `indicados` fora de `total`; cada conclusão conta uma vez e previsão não conta |
| V21-RF-14 — Arquivamento e histórico | V21-RN-04, V21-RN-17 | V21-CT-24 | `frontend/js/itens.js::deleteItem`, `app/repositories/mongo_item_repository.py`; novo arquivamento |
| V21-RF-16 — Indicar lugar de descarte | V21-RN-11, V21-RN-23 | V21-CT-31, V21-CT-32, V21-CT-33, V21-CT-34 | `POST/DELETE /api/itens/{id}/destinacao` com tipo estruturado e textos livres; item termina em `destinacao_informada`, campo visível só ao autor, sem ponto criado e com contagem separada em `indicados` |
| V21-RF-15 — Navegação e recuperação | V21-RN-01, V21-RN-03, V21-RN-04, V21-RN-11, V21-RN-16, V21-RN-20, V21-RN-21, V21-RN-22 | V21-CT-03, V21-CT-14, V21-CT-21, V21-CT-25, V21-CT-26, V21-CT-28, V21-CT-29 | Filtros preservados no endereço (`history.replaceState`); sem paginação na interface. Bloqueio em controles específicos, foco na mensagem e orientação de recarga, sem chave de operação genérica |

## Requisitos não funcionais

| Requisito | Cenários de referência | Evidência / critério a conferir |
|---|---|---|
| V21-RNF-01 | Estratégia de dados e preservação do comportamento v1.0 | Decisão autorizada; nenhuma exclusão nesta fase |
| V21-RNF-02 | V21-CT-07, V21-CT-15, V21-CT-16, V21-CT-20, V21-CT-26, V21-CT-27, V21-CT-29 | Testes de API, índices reais, disputa/rollback em replica set |
| V21-RNF-03 | V21-CT-03, V21-CT-14, V21-CT-21, V21-CT-25, V21-CT-28 | Navegador, teclado e viewport pequeno |
| V21-RNF-04 | V21-CT-30 e suíte completa | Comandos/saídas reais; fixtures isoladas e limpeza comprovada |
| V21-RNF-05 | Conferência de regras/HTTP/DTOs e casos de erro | Snapshot `docs/openapi.json` confrontado com o gerador em `tests/test_openapi_runtime.py`; diferenças de representação em `docs/openapi.md` |
| V21-RNF-06 | V21-CT-29 e inspeção de fronteira | Proteções existentes preservadas sem ampliar tópico I |
| V21-RNF-07 | V21-CT-31, V21-CT-32 | Indicação legível apenas pelo autor; nenhuma exposição a operador ou terceiro |

## Regras e origem documental

- Regras V21-RN-01 a V21-RN-23 estão em [regras_de_negocio.md](regras_de_negocio.md).
- Requisitos funcionais e não funcionais: [requisitos.md](requisitos.md).
- Jornadas J-01 a J-05: [jornadas_frontend.md](jornadas_frontend.md).
- Cenários de aceitação: [casos_de_teste.md](casos_de_teste.md).
- Estrutura, operações e diferenças do desenho original: [modelo_dados.md](modelo_dados.md) e [contratos_http.md](contratos_http.md).

## Evidências e limites

A execução funcional da Etapa 15 aprovou 201 testes e as três jornadas do script `scripts/validar_jornadas_v2.py`, com referências persistidas, auditoria de datas e limpeza seletiva. Essa execução usou `--no-cov`; não comprova medição de cobertura no marco final. Não foi reexecutada por esta atualização documental.

| Família | Testes / comando reproduzível |
|---|---|
| Conta, migração e permissões | `tests/test_api_usuario.py`, `tests/test_migracao_papeis.py`, `tests/test_provisionamento_ponto_coleta.py` |
| Catálogo, rascunho, publicação e gestão | `tests/test_api_item.py`, `tests/test_item_service.py`, `tests/test_fluxos_v2.py` |
| Interesse e reserva | `tests/test_interesses_v2.py`, `tests/test_interesses_runtime.py`, `tests/test_interesse_repository.py` |
| Combinação e entrega bilateral | `tests/test_fluxos_runtime.py` |
| Encaminhamentos e operação do ponto | `tests/test_encaminhamentos_runtime.py` |
| Indicação de lugar e privacidade | `tests/test_destinacao_runtime.py` |
| Avisos e indicadores | `tests/test_notificacoes_runtime.py`, `tests/test_indicadores_v2.py` |
| Interface e navegação | `tests/test_frontend.py`, `tests/test_selenium_frontend.py`, `scripts/validar_jornadas_v2.py` |
| Contrato gerado | `tests/test_openapi_runtime.py` |

Os arquivos acima são evidências por família, não equivalência automática com todos os passos de cada V21-CT. Testes que inspecionam texto-fonte não comprovam comportamento de navegador ou concorrência.

### Critérios que continuam sem comprovação integral

- Versões esperadas e `id_operacao` persistido com fingerprint de payload não existem no contrato genérico. Cenários como V21-CT-07, V21-CT-26, V21-CT-27 e V21-CT-33 contêm critérios mais amplos que as verificações de estado e idempotência específicas entregues.
- V21-CT-03 exige navegar por páginas e voltar do detalhe. O catálogo da interface não pagina; preservação de filtros não comprova o cenário inteiro.
- A existência do link em notificações não comprova emissão para todo evento previsto em V21-RF-12, nem acesso direto ao registro individual.
- Bloqueio de duplo envio, foco e recuperação estão presentes em pontos específicos; V21-CT-28 e a experiência completa de teclado/viewport pequeno precisam ser avaliados além dos testes de fonte e smoke existentes.
- A inativação de ponto e seu aviso não estão na mesma unidade transacional no handler atual; não generalizar a atomicidade de reserva/entrega para todas as operações.

Reprodução da suíte, integração e medição: [README](../../README.md). Não há relatórios de verificação separados. O histórico v2.0 fica no marco `71e8dfa`, não é reutilizado como aprovação de todo o escopo v2.1. Vídeo, identificação do commit final e integração são passos separados da entrega.
