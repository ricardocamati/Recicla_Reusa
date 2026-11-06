# Contratos HTTP — v2.1

## Contrato executável

As Etapas 9 a 15 têm implementação. Para integrar ou testar o checkout atual, use [docs/http-api.md](../../docs/http-api.md), os schemas em `app/schemas/` e a [OpenAPI gerada](../../docs/openapi.json). A tabela original preservada abaixo não representa todos os caminhos e campos efetivamente entregues.

| Tema | Implementação atual / diferença |
|---|---|
| Campos do item | `destino` (`doacao`, `revenda`, `descarte`), `status`, `valor`; não `modalidade`, `situacao`, `preco` |
| Listagem própria | `GET /api/itens/meus`, com `grupo`; não `escopo=meus` no catálogo |
| Ciclo do item | Endpoints próprios `POST /{id}/publicar`, `/arquivar`, `/entrega`, `/recebimento`; não `/transicoes` genérico |
| Indicação de lugar | `POST /api/itens/{id}/destinacao` e `DELETE` no mesmo caminho |
| Histórico | Integra as respostas; não existe rota `/api/itens/{id}/historico` |
| Comandos | Não aceitam `id_operacao`, `versao_esperada` ou `versao_item_esperada` genéricos |
| Combinação | Proposta por `PUT /api/interesses/{id}/combinacao`; aceite por `POST /combinacao/aceite` com `revisao` |
| Encaminhamentos | Criação com `item_id`/`ponto_id`; ações com `acao`, `motivo`, `novo_ponto_id`; listagem com `escopo=autor` ou `operador` |
| Situação do ponto | `POST /api/pontos-coleta/{id}/situacao` com `ativo`; sem versão/chave genérica |
| Indicadores | `ofertas_ativas`, `pendencias`, `doados`, `vendidos`, `coletados`, `indicados`, `total`; escopo global, não pendências pessoais |
| Reenvio | Há caminhos específicos idempotentes e índice de eventos; isso não implementa recuperação genérica por chave com fingerprint de payload |

Verificação de status no banco e revisão da combinação não detectam todo conflito entre edições no mesmo estado. Não declarar versionamento otimista genérico, rollback de qualquer comando ou idempotência persistida por chave como já entregues. Os testes de runtime exercitam subconjuntos específicos dessas garantias.

## Contrato originalmente planejado — não usar como referência de chamada

O conteúdo abaixo mantém as decisões e critérios originais, inclusive operações ainda não implementadas. A documentação de divergências não autoriza reduzir o escopo dos requisitos nem altera código/banco.

## Convenções

- Prefixo `/api` preservado; versão de produto não obriga mudar o prefixo.
- Sessão/cookie e origem mantidos. `401` sessão ausente; `403` ator sem permissão; `404` recurso inexistente/inacessível conforme política comum; `400` entrada ou query extra; `409` estado/versão/chave incompatível; `503` indisponibilidade, sem detalhes internos.
- Erros sob `detail`. IDs dos atores e datas vêm do servidor.
- Listas: offset=0, limite=20, máximo 100, ordenação estável. Restrição por proprietário/operador aplicada ANTES da paginação.
- Todos os comandos de ciclo levam `id_operacao` e versões dos registros existentes, conforme a tabela de concorrência abaixo; criação de cadastro sem agregado anterior não inventa `versao_esperada`. A chave de reenvio é item + ator + id_operacao nas operações de item/interesse/encaminhamento; para ativação/inativação de local, é ponto + ator + id_operacao. Reenvio idêntico recupera resultado persistido antes de exigir novamente as versões originais. Não tratar repetição aleatória como novo sucesso.
- Não expor PATCH genérico para estado. Requests aceitam apenas campos conhecidos.

## Pessoas e itens

| Método/caminho | Entrada/resultado proposto | Fronteira |
|---|---|---|
| POST `/api/usuarios` | Cadastro público cria pessoa | Não aceita operador por autoatribuição |
| GET `/api/usuarios/me` | Perfil da sessão | Sem hash |
| POST `/api/itens` | Características, modalidade, preço e intenção de salvar/publicar | Pessoa; proprietário derivado; oferta rascunho/publicada ou descarte aguardando ponto |
| GET `/api/itens` | escopo=catalogo (padrão) ou meus; filtros documentados | Catálogo só oferta; meus inclui descartes/encerrados próprios |
| GET `/api/itens/{id}` | Detalhe projetado para ator | Não vaza combinação de terceiros |
| PUT `/api/itens/{id}` | Campos editáveis + versão | Sem alteração livre de modalidade/situação |
| POST `/api/itens/{id}/transicoes` | publicar, arquivar, declarar_entrega, confirmar_recebimento, informar_destinacao, desfazer_destinacao | Ator e estado validados; no descarte, apenas o autor informa ou desfaz |
| GET `/api/itens/{id}/historico` | Histórico paginado projetado | Participantes e dono conforme permissão |
| DELETE `/api/itens/{id}` | versão esperada | Apenas cadastro sem dependências |

Filtros de catálogo: texto, modalidade, categoria, condicao, cidade, preco_min/preco_max e incluir_reservados. Faixa de preço implica ofertas de venda e rejeita modalidade=doacao; não interpretar null de doação como preço zero. `incluir_reservados` amplia apenas disponível/reservado, nunca descarte ou concluído. Busca textual é literal/normalizada, com limite, não expressão executável.

## Interesses e combinação

| Método/caminho | Operação proposta | Permissão |
|---|---|---|
| POST `/api/interesses` | item_id, versao_item_esperada, id_operacao; cria pendente | Pessoa não proprietária; oferta disponível |
| GET `/api/interesses` | escopo=meus/recebidos; item/status/paginação | Meus por autor; recebidos por propriedade, sem antigo bloqueio a beneficiário |
| GET `/api/interesses/{id}` | Detalhe da relação e combinação autorizada | Autor/proprietário |
| POST `/api/interesses/{id}/acoes` | acao, motivo quando aplicável, versao_esperada do interesse, versao_item_esperada, id_operacao | Conforme regras V21-RN-05 a V21-RN-07 |
| PUT `/api/interesses/{id}/combinacao` | local_texto, previsao opcional, observacao, versao_esperada do interesse, versao_item_esperada, id_operacao | Selecionado/proprietário; nova revisão |
| POST `/api/interesses/{id}/combinacao/aceite` | revisao aceita, versao_esperada do interesse, versao_item_esperada, id_operacao | Contraparte de quem propôs |

Selecionar é do proprietário; desistir é do autor selecionado; liberar é do proprietário. Cancelamento de pendente usa desistir. Recusar exige motivo. Retomar é do autor cancelado; reabrir é iniciativa do proprietário após recusa. Operações encerradas não reabrem. Seleção/liberação deve conferir CAS também no item dentro da unidade transacional; o cliente não atualiza documentos separadamente.

## Descarte e locais

| Método/caminho | Operação proposta | Permissão |
|---|---|---|
| GET `/api/pontos-coleta` | cidade, categoria, ativo, escopo=meus opcional, paginação | Pessoa consulta ativos por padrão; operador pode incluir seus inativos |
| POST/PUT `/api/pontos-coleta[/{id}]` | Cadastro/edição de local; `ativo` por comando específico | Operador do local; categoria ativa protegida |
| POST `/api/pontos-coleta/{id}/situacao` | ativar/inativar + versão/id_operacao | Responsável; aviso a previsões afetadas |
| POST `/api/encaminhamentos` | item_id, ponto_id, versao_item_esperada, id_operacao | Dono do descarte; registra previsão |
| GET `/api/encaminhamentos` | escopo=meus/operacao; ponto_id/status/paginação | Dono vê próprios; operador vê somente locais próprios |
| GET `/api/encaminhamentos/{id}` | Tentativa e histórico permitido | Autor/operador correspondente |
| POST `/api/encaminhamentos/{id}/acoes` | acao, motivo/novo ponto quando aplicáveis, versao_esperada da tentativa, versao_item_esperada, id_operacao | Cancelar/trocar pelo dono; demais pelo operador |

O caminho sem ponto cadastrado usa as ações `informar_destinacao` e `desfazer_destinacao` em `/api/itens/{id}/transicoes`, com `tipo_local` obrigatório e `nome`, `cidade` e `observacao` opcionais. A indicação não aparece para operadores, não entra no diretório e não é contada como recebimento; o autor é o único que a lê e pode desfazê-la enquanto o item não estiver arquivado.

Troca envia novo ponto_id e motivo, com versões esperadas do item/tentativa. Uma chamada atômica cancela a anterior e cria a nova; resposta retorna nova tentativa e item atualizado. Recebimento fecha tentativa e muda item sem uma segunda chamada do frontend. IDs de item/autor/ponto de uma tentativa existente não são livremente regravados por PUT.

Inativar não resolve automaticamente todas as previsões: mantém acesso às tentativas e bloqueia novas destinações/recebimento enquanto inativo. Alteração de categorias conflita quando prejudica previsão ativa.

## Versões por comando e validação concorrente

| Mutação | Versão enviada pelo cliente | Validação adicional do servidor |
|---|---|---|
| Criar interesse | versao_item_esperada | Item disponível, autoria, unicidade e operação anterior |
| Ações/combinação/aceite de interesse | versao_esperada do interesse + versao_item_esperada | Relação atual, seleção e revisão da combinação |
| Publicar/arquivar/declarar entrega/confirmar recebimento de oferta | versao_esperada do item | Seleção, combinação aceita e estado do interesse lidos/validados na transação |
| Criar encaminhamento | versao_item_esperada | Ponto ativo/compatível validado por escrita de proteção na transação |
| Informar/desfazer destinação | versao_item_esperada + id_operacao | Autor, ausência de tentativa ativa e exclusividade entre os dois caminhos |
| Ações de encaminhamento | versao_esperada da tentativa + versao_item_esperada | Estado do ponto e vínculo ativo; troca valida novo ponto |
| Ativar/inativar ou editar ponto | versao_esperada do ponto | Propriedade, categorias e previsões afetadas |
| Edição/exclusão comum de item | versao_esperada do item | Restrições de mutabilidade e referências |

O frontend deve receber/consultar essas versões antes da ação; não fabricá-las com valor padrão. Interesses e encaminhamentos retornam `versao_item` no detalhe autorizado para compor os comandos. A versão enviada de um registro não autoriza confiar em relações antigas: o servidor relê e protege os demais documentos na unidade transacional. Conflito deixa tudo inalterado, incluindo avisos.

## Avisos, resultados e indicadores

- GET `/api/notificacoes`: destinatário da sessão, leitura/paginação; PATCH de leitura idempotente preservado.
- GET `/api/indicadores`: chaves propostas `doacoes_confirmadas`, `vendas_confirmadas`, `recebidos_pontos` e `destinacoes_informadas`; a última é apresentada separadamente e nunca somada ao recebimento verificado. Não inventar valores de pagamentos/reciclagem. Estatística de pendências próprias é separada e não expõe pessoas.
- GET `/api/itens/{id}/operacoes/{id_operacao}`: consulta autenticada do resultado de comando sobre esse item, limitado ao ator da operação. Comandos sobre interesse/encaminhamento devem registrar também referência de operação no item. Não conceder acesso geral ao item por saber uma chave.
- GET `/api/pontos-coleta/{id}/operacoes/{id_operacao}`: equivalente para resultado de ativação/inativação do local, limitado ao ator da operação; a chave não concede propriedade do ponto.
- Resultado de operação possui recurso/versão resultantes e estado confirmado, não payload arbitrário ou segredo. Resposta perdida é reconciliada por essa consulta; sem registro, frontend só repete a mesma chave/payload, nunca gera nova chave automaticamente.

## Compatibilidade e decisões em aberto

`tipo=pessoa`, `modalidade=venda`, novos estados, indicadores e DTOs não são compatíveis automaticamente com consumidores v2.0. Esta é proposta para incremento local coordenado; definir estratégia de dados e regenerar frontend/API juntos. Não aceitar simultaneamente formatos incompatíveis sem regra e teste explícitos.

Preço precisa de representação única (recomendação: inteiro em centavos para evitar ambiguidade de moeda; fechar na especificação de implementação). Campos, limites textuais e schemas completos serão formalizados antes do código. Ausência de OpenAPI v2.1 nesta fase é intencional: não fornecer um JSON incompleto como se fosse contrato validado.
