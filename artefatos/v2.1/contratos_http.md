# Contratos HTTP — v2.1

## Contrato executável — leitura pública da Etapa 16

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
| Consulta pública (Etapa 16) | Lista/detalhe de ativos sem sessão, cinco campos públicos, filtros e paginação; gestão protegida com `escopo=meus` |
| Situação do ponto | `POST /api/pontos-coleta/{id}/situacao` com `ativo`; sem versão/chave genérica |
| Indicadores | `ofertas_ativas`, `pendencias`, `doados`, `vendidos`, `coletados`, `indicados`, `total`; escopo global, não pendências pessoais |
| Reenvio | Há caminhos específicos idempotentes e índice de eventos; isso não implementa recuperação genérica por chave com fingerprint de payload |

Verificação de status no banco e revisão da combinação não detectam todo conflito entre edições no mesmo estado. Não declarar versionamento otimista genérico, rollback de qualquer comando ou idempotência persistida por chave como já entregues. Os testes de runtime exercitam subconjuntos específicos dessas garantias.

## Contrato-alvo revisado — ainda não usar como referência de chamada

O conteúdo abaixo mantém os critérios de ofertas e substitui explicitamente o descarte por um diretório público. Leitura anônima e projeção pública foram implementadas na Etapa 16; a retirada dos comandos de descarte permanece pendente. As rotas de leitura de pontos abaixo são executáveis, mas versões/chaves genéricas e demais diferenças continuam propostas; os caminhos atuais permanecem descritos acima e em docs/http-api.md. A Etapa 16 não migra o banco nem retira o processo anterior. Documentos sem `ativo` mantêm o padrão ativo sem alteração persistida.

## Convenções

- Prefixo `/api` preservado; versão de produto não obriga mudar o prefixo.
- Sessão/cookie e origem de mutações mantidos. Lista/detalhe público de pontos ativos não exigem sessão; gestão e ofertas continuam protegidas. `401` sessão ausente em rota protegida; `403` ator sem permissão; `404` recurso inexistente/inacessível conforme política comum; `400` entrada ou query extra; `409` estado/versão/chave incompatível; `503` indisponibilidade, sem detalhes internos.
- Erros sob `detail`. IDs dos atores e datas vêm do servidor.
- Listas: offset=0, limite=20, máximo 100, ordenação estável. Restrição por proprietário/operador aplicada ANTES da paginação.
- Todos os comandos de ciclo levam `id_operacao` e versões dos registros existentes, conforme a tabela de concorrência abaixo; criação de cadastro sem agregado anterior não inventa `versao_esperada`. A chave de reenvio é item + ator + id_operacao nas operações de item/interesse; para ativação/inativação de local, é ponto + ator + id_operacao. Reenvio idêntico recupera resultado persistido antes de exigir novamente as versões originais. Não tratar repetição aleatória como novo sucesso.
- Não expor PATCH genérico para estado. Requests aceitam apenas campos conhecidos.

## Pessoas e itens

| Método/caminho | Entrada/resultado proposto | Fronteira |
|---|---|---|
| POST `/api/usuarios` | Cadastro público cria pessoa | Não aceita operador por autoatribuição |
| GET `/api/usuarios/me` | Perfil da sessão | Sem hash |
| POST `/api/itens` | Características, modalidade, preço e intenção de salvar/publicar | Pessoa; proprietário derivado; somente oferta de doação/venda rascunho/publicada; não criar item de descarte |
| GET `/api/itens` | escopo=catalogo (padrão) ou meus; filtros documentados | Catálogo só oferta; gestão inclui ofertas próprias, com legado tratado separadamente e sem apagar registros |
| GET `/api/itens/{id}` | Detalhe projetado para ator | Não vaza combinação de terceiros |
| PUT `/api/itens/{id}` | Campos editáveis + versão | Sem alteração livre de modalidade/situação |
| POST `/api/itens/{id}/transicoes` | publicar, arquivar, declarar_entrega, confirmar_recebimento | Ator e estado da oferta validados; indicação/desfazimento de descarte retirados do alvo |
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

## Descarte: diretório e gestão de locais

| Método/caminho proposto | Entrada/resultado | Acesso-alvo |
|---|---|---|
| GET `/api/pontos-coleta` | cidade/categoria opcionais, offset=0, limite=20 (1–100); lista de DTOs públicos | Sem sessão; somente ativos, filtros antes de paginar, ordem nome/ID |
| GET `/api/pontos-coleta/{id}` | DTO público do local ativo | Sem sessão; ausente/inativo retorna `404` sem dados privados |
| GET `/api/pontos-coleta?escopo=meus` | Gestão própria paginada; filtro ativo opcional, incluindo inativos | Sessão operacional; `401` sem sessão e `403` pessoa comum |
| GET `/api/pontos-coleta/{id}?escopo=meus` | Detalhe de gestão, inclusive inativo | Somente operador responsável; não confundir com detalhe público |
| POST `/api/pontos-coleta` | Nome, endereço público, categorias e horário; responsável derivado | Operador; identidade e datas não são campos livres |
| PUT `/api/pontos-coleta/{id}` | Campos editáveis e versão proposta | Operador responsável; não transfere responsável |
| POST `/api/pontos-coleta/{id}/situacao` | Ativo/inativo, versão e chave propostas | Operador responsável; altera visibilidade, não confirma recebimentos |

### Projeção pública e validação

DTO público permite apenas `id`, `nome`, `endereco`, `categorias_aceitas` e `horario_atendimento`. Não retornar `responsavel_id`, usuário, hash, contato privado, endereço pessoal, histórico de equipamento ou indicações legadas. DTO de gestão contém também campos necessários à edição e não é reutilizado cegamente na leitura pública.

Consultas públicas aceitam cidade/categoria e paginação; não aceitam filtro para revelar inativos, identidade de visitante, `item_id`, dados de entrega ou `id_operacao`. Na gestão, `escopo=meus` seleciona uma operação protegida antes de interpretar seu filtro ativo; jamais fazer fallback público quando a autorização falhar. Outros escopos/querys extras são inválidos. Resultado vazio retorna `200` e lista vazia; falha de serviço retorna erro sob `detail`, não uma lista vazia fictícia.

Os GETs não criam sessão obrigatória nem escrevem item, encaminhamento, indicação, notificação ou evento de descarte. Cópia de endereço e link opcional de mapa são ações de interface, sem endpoint de registro. Nenhuma consulta garante capacidade ou recebimento físico.

### Operações retiradas do contrato-alvo

Não expor no novo fluxo criação/listagem/ações de `/api/encaminhamentos`, nem informar/desfazer destinação em `/api/itens/{id}/destinacao` ou `/transicoes`. Essas rotas ainda existem no programa de referência; sua descontinuação e a apresentação dos registros anteriores precisam de estratégia explícita, não de uma exclusão de banco. Não criar endpoints substitutos de previsão, confirmação ou rastreamento de descarte.

## Versões por comando e validação concorrente

| Mutação | Versão enviada pelo cliente | Validação adicional do servidor |
|---|---|---|
| Criar interesse | versao_item_esperada | Item disponível, autoria, unicidade e operação anterior |
| Ações/combinação/aceite de interesse | versao_esperada do interesse + versao_item_esperada | Relação atual, seleção e revisão da combinação |
| Publicar/arquivar/declarar entrega/confirmar recebimento de oferta | versao_esperada do item | Seleção, combinação aceita e estado do interesse lidos/validados na transação |
| Ativar/inativar ou editar ponto | versao_esperada do ponto | Propriedade e consistência da edição; referências legadas preservadas |
| Edição/exclusão comum de item | versao_esperada do item | Restrições de mutabilidade e referências |

O frontend deve receber/consultar essas versões antes da ação; não fabricá-las com valor padrão. Interesses retornam `versao_item` no detalhe autorizado para compor os comandos. A versão enviada de um registro não autoriza confiar em relações antigas: o servidor relê e protege os demais documentos na unidade transacional. Conflito deixa tudo inalterado, incluindo avisos.

## Avisos, resultados e indicadores

- GET `/api/notificacoes`: destinatário da sessão, leitura/paginação; PATCH de leitura idempotente preservado.
- GET `/api/indicadores`: chaves-alvo de resultados `doacoes_confirmadas` e `vendas_confirmadas`; não incluir resultados de descarte obtidos por consulta. `total` de conclusões, se retornado, soma somente essas duas chaves. Os campos atuais `coletados` e `indicados` não são recontados como visitas ou mantidos como resultados do novo diretório; descontinuá-los exige atualizar consumidores coordenadamente, sem apagar documentos históricos. Não inventar valores de pagamentos/reciclagem. Contagem de locais ativos, se houver, é informação cadastral separada, sem somar a equipamentos. Estatística de pendências próprias é separada e não expõe pessoas.
- GET `/api/itens/{id}/operacoes/{id_operacao}`: consulta autenticada do resultado de comando sobre esse item, limitado ao ator da operação. Comandos sobre interesse devem registrar também referência de operação no item. Não conceder acesso geral ao item por saber uma chave.
- GET `/api/pontos-coleta/{id}/operacoes/{id_operacao}`: equivalente para resultado de ativação/inativação do local, limitado ao ator da operação; a chave não concede propriedade do ponto.
- Resultado de operação possui recurso/versão resultantes e estado confirmado, não payload arbitrário ou segredo. Resposta perdida é reconciliada por essa consulta; sem registro, frontend só repete a mesma chave/payload, nunca gera nova chave automaticamente.

## Compatibilidade e decisões em aberto

`tipo=pessoa`, `modalidade=venda`, novos estados, indicadores e DTOs não são compatíveis automaticamente com consumidores v2.0. Esta é proposta para incremento local coordenado; definir estratégia de dados e regenerar frontend/API juntos. Não aceitar simultaneamente formatos incompatíveis sem regra e teste explícitos.

Preço precisa de representação única (recomendação: inteiro em centavos para evitar ambiguidade de moeda; fechar na especificação de implementação). Campos, limites textuais e schemas completos serão formalizados antes do código. A OpenAPI gerada já existe para o runtime anterior; ela não comprova a revisão do diretório. Só regenerá-la quando o contrato-alvo estiver implementado e validado, sem fornecer JSON planejado como se fosse executável.
