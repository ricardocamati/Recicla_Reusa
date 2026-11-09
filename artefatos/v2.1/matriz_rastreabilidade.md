# Matriz de rastreabilidade — v2.1

Esta matriz corresponde à revisão de descarte como diretório público. **Implementação parcial: a Etapa 16 entrega leitura pública e preservação do legado; interface, retirada do processo anterior e indicadores permanecem pendentes.** Base: `f216802` (integração do PR #25, incluindo #26). Código ou teste do encaminhamento antigo não comprova acesso anônimo nem consulta sem item. A coluna de evidências descreve referências existentes e trabalho a fazer, não conclusão automática.

## Requisitos ativos

| Requisito | Regras | Casos escritos | Código existente e diferença para o alvo |
|---|---|---|---|
| V21-RF-01 — Conta de pessoa e operação | V21-RN-01, V21-RN-21, V21-RN-22 | V21-CT-01, V21-CT-29, V21-CT-40 | Conta única e operador já existem. Visitantes consultam a API do diretório sem flexibilizar a gestão; a entrada pública na interface permanece para a Etapa 17. |
| V21-RF-02 — Catálogo de ofertas | V21-RN-03, V21-RN-19, V21-RN-21 | V21-CT-02, V21-CT-03 | `GET /api/itens` já restringe ofertas. Diretório deve ser separado do catálogo; paginação navegável continua um limite existente. |
| V21-RF-03 — Cadastro e gestão de ofertas | V21-RN-02, V21-RN-04, V21-RN-20, V21-RN-22 | V21-CT-04, V21-CT-25, V21-CT-44 | Assistente e grupos em `frontend/js/itens.js` existem. Retirar descarte de novos cadastros e apontar entrada ao diretório; preservar registros antigos. |
| V21-RF-04 — Interesse e reabertura | V21-RN-05 | V21-CT-05, V21-CT-06 | Relação única, ações e acompanhamento existem em `app/services/interesse_service.py` e `frontend/js/interesses.js`; não criar interesse para local. |
| V21-RF-05 — Reserva e liberação | V21-RN-06, V21-RN-07, V21-RN-20 | V21-CT-07, V21-CT-08, V21-CT-27 | Reserva/reversão de ofertas permanecem. Garantias genéricas de versão/operação não se tornam comprovadas pela manutenção do fluxo. |
| V21-RF-06 — Combinação | V21-RN-08 | V21-CT-09 | Proposta, revisão e aceite implementados para participantes selecionados; não usados no diretório. |
| V21-RF-07 — Entrega bilateral | V21-RN-09, V21-RN-10, V21-RN-19, V21-RN-20, V21-RN-22 | V21-CT-10, V21-CT-11, V21-CT-26, V21-CT-30 | Declaração e recebimento de oferta permanecem. Retirada da confirmação de descarte não afeta a confirmação de doação/venda. |
| V21-RF-08 — Venda e preço reservado | V21-RN-02, V21-RN-06, V21-RN-07, V21-RN-09 | V21-CT-08, V21-CT-12 | Venda direta e preço selecionado já existem; representação monetária proposta continua distinta do runtime. |
| V21-RF-09 — Diretório público | V21-RN-11, V21-RN-21, V21-RN-22, V21-RN-24 | V21-CT-35, V21-CT-36, V21-CT-37, V21-CT-38, V21-CT-39, V21-CT-41, V21-CT-44 | Reutilizar dados de `pontos_coleta`. Leituras e DTO público implementados em `app/api/pontos_coleta.py` e mapper/schema específicos. `tests/test_diretorio_publico.py` e `tests/test_diretorio_runtime.py` exercitam os recortes de API de V21-CT-35, V21-CT-36, V21-CT-37 e preservação de V21-CT-43. **Tela e passos de navegador pendentes na Etapa 17.** |
| V21-RF-11 — Gestão dos locais | V21-RN-01, V21-RN-14, V21-RN-16, V21-RN-21, V21-RN-22 | V21-CT-40, V21-CT-41, V21-CT-43 | CRUD e ativo/inativo já existem. Leitura de gestão separada da pública, com autorização e propriedade na Etapa 16. Filas/ações e apresentação do legado continuam na Etapa 18; a política inicial preserva documentos e permissões sem migração. |
| V21-RF-12 — Avisos de ofertas | V21-RN-18, V21-RN-20 | V21-CT-22, V21-CT-27, V21-CT-35 | Links e unicidade de evento existem; não atribuir aviso a consulta/gestão do diretório. Retirar emissão de descarte junto com o fluxo, preservando avisos históricos privados. |
| V21-RF-13 — Indicadores | V21-RN-19, V21-RN-24 | V21-CT-23, V21-CT-30, V21-CT-42 | `app/services/indicador_service.py` e repositório ainda incluem coletados/indicados e total antigo. Ajustar contrato e UI: resultados-alvo somente de ofertas; eventual quantidade de locais separada. |
| V21-RF-14 — Arquivamento e histórico | V21-RN-04, V21-RN-17, V21-RN-25 | V21-CT-24, V21-CT-43 | Ofertas mantêm arquivamento e proteção de vínculos. Descarte consultado não produz item arquivável; não apagar o legado. |
| V21-RF-15 — Navegação e recuperação | V21-RN-21, V21-RN-22, V21-RN-24 | V21-CT-03, V21-CT-25, V21-CT-26, V21-CT-28, V21-CT-36, V21-CT-38, V21-CT-39 | Menu compartilhado e filtros em URL existem. Entrada pública, paginação do diretório e retorno ao detalhe precisam de validação própria; não afirmar auditoria completa de acessibilidade. |

## Requisitos retirados, sem reutilização dos IDs

| Identificador | Decisão |
|---|---|
| V21-RF-10 | Cancelar/trocar encaminhamento retirado; nova consulta substitui escolher outro local, sem operação persistida. |
| V21-RF-16 | Indicar/desfazer destinação privada de item retirado; não é fallback do diretório. |
| V21-RNF-07 | Critério da antiga indicação retirado, sem tornar públicos os registros existentes; privacidade do diretório passa a V21-RNF-08. |
| V21-RN-12, V21-RN-13, V21-RN-15, V21-RN-23 | Tentativas, trocas, confirmação e indicação de descarte não são tarefas pendentes do novo alvo. |
| V21-CT-13, V21-CT-14, V21-CT-15, V21-CT-16, V21-CT-17, V21-CT-18, V21-CT-19, V21-CT-20, V21-CT-21 | Casos do processo antigo de entrega em ponto retirados. Novas consultas/gestão têm casos próprios, sem reusar evidência anterior. |
| V21-CT-31, V21-CT-32, V21-CT-33, V21-CT-34 | Casos de indicação/desfazimento e contagens de descarte retirados. Dados antigos permanecem protegidos. |

## Requisitos não funcionais ativos

| Requisito | Casos | Evidência ou critério futuro |
|---|---|---|
| V21-RNF-01 — Preservação | V21-CT-43 | Política sem migração: preservar documentos/referências e comparar snapshots das seis coleções em teste real. A descontinuação posterior não é comprovada por esse recorte. |
| V21-RNF-02 — Integridade | V21-CT-07, V21-CT-26, V21-CT-27, V21-CT-40 | Concorrência/transações das ofertas e autorização da gestão; consulta não exige transação de negócio. |
| V21-RNF-03 — Frontend acessível | V21-CT-03, V21-CT-28, V21-CT-36, V21-CT-38, V21-CT-39 | Teclado, viewport pequeno, paginação e independência de mapas externos. |
| V21-RNF-04 — Evidência própria | V21-CT-30, V21-CT-35 | Jornadas-alvo de doação, venda e consulta anônima; não a antiga terceira jornada de recebimento em ponto. |
| V21-RNF-05 — Contrato documentado | V21-CT-35, V21-CT-37, V21-CT-40, V21-CT-44 | Atualizar OpenAPI somente com implementação, mantendo divergências explícitas até lá. |
| V21-RNF-06 — Limites locais | V21-CT-29, V21-CT-39 | Consulta sem login não implanta internet nem amplia tópico I; mapa opcional não é dependência. |
| V21-RNF-08 — Projeção pública | V21-CT-35, V21-CT-37, V21-CT-40, V21-CT-43 | DTO de local sem dados privados; gestão protegida; nenhuma exposição do legado. |

## Referências de código e testes existentes

| Família | Referências | Limite de evidência |
|---|---|---|
| Conta/permissões | `tests/test_api_usuario.py`, `tests/test_security.py`, `tests/test_provisionamento_ponto_coleta.py` | Não comprovam automaticamente a exceção de leitura pública de pontos. |
| Ofertas/interesses/entrega | `tests/test_api_item.py`, `tests/test_fluxos_v2.py`, `tests/test_interesses_runtime.py`, `tests/test_fluxos_runtime.py` | Permanecem relevantes para doação/venda; validar regressão após implementação. |
| Locais | `tests/test_pontos_coleta_v2.py`, `app/api/pontos_coleta.py`, `app/schemas/ponto_coleta.py` | `tests/test_diretorio_publico.py` e `tests/test_diretorio_runtime.py` exercitam DTO público, consulta sem sessão, filtros/ordenação e snapshots; telas permanecem pendentes. |
| Descarte legado | `tests/test_encaminhamentos_runtime.py`, `tests/test_destinacao_runtime.py` | Evidência do comportamento substituído, não da revisão. |
| Avisos/indicadores | `tests/test_notificacoes_runtime.py`, `tests/test_indicadores_v2.py` | Expectativas precisam acompanhar retirada de eventos/contagens de descarte. |
| Frontend | `tests/test_frontend.py`, `tests/test_selenium_frontend.py` | Acrescentar jornada anônima, retorno/paginação e ausência de cadastro de item. |
| Contrato/jornadas | `tests/test_openapi_runtime.py`, `scripts/validar_jornadas_v2.py` | Snapshot e terceira jornada atuais descrevem o fluxo anterior; não aprovam a revisão. |

## Limites que continuam explícitos

- Versões genéricas, `id_operacao` com fingerprint e recuperação persistida não existem no contrato executável. Os critérios de ofertas mais amplos continuam não comprovados.
- Paginação da API não comprova navegação por páginas na interface. Restauração de filtros não equivale a restauração de página.
- Link de aviso não comprova emissão para cada evento nem acesso direto ao registro correto.
- Consulta pública e gestão privada precisam de testes diferentes; liberar leitura não autoriza CRUD anônimo.
- A Etapa 16 não aprova toda a revisão; o TODO mantém etapas posteriores abertas. Não reutilizar testes de backend como evidência da interface nem os testes antigos de descarte como aprovação do novo alvo.

Fontes normativas: [requisitos](requisitos.md), [regras](regras_de_negocio.md), [jornadas](jornadas_frontend.md), [modelo](modelo_dados.md), [contratos](contratos_http.md) e [casos](casos_de_teste.md). Reprodução do programa atual permanece no [README do projeto](../../README.md).
