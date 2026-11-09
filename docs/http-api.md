# Contratos HTTP

A documentação OpenAPI está disponível em `/docs`. As rotas de usuários usam `/api/usuarios` e a autenticação usa `/api/auth`.

## Usuários

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/usuarios` | pública | — | `200` com lista resumida |
| `POST` | `/api/usuarios` | pública | `UsuarioCreateRequest` | `201`, `Location` e perfil criado |
| `GET` | `/api/usuarios/{id}` | pública ou sessão do próprio usuário | — | `200` com resumo público ou perfil completo do titular |
| `PUT` | `/api/usuarios/{id}` | titular | `UsuarioUpdateRequest` | `200` com perfil atualizado |
| `DELETE` | `/api/usuarios/{id}` | titular | — | `204` sem corpo |
| `GET` | `/api/usuarios/me` | obrigatória | — | `200` com perfil completo do titular |

A atualização comum não aceita `tipo`; a classificação é imutável nessa operação. O cadastro público aceita somente `doador` e `beneficiario`.

O perfil `ponto_coleta` não é criado por rota HTTP. O responsável técnico deve executar, na raiz do projeto, `python -m app.provisionar_ponto_coleta` com `--nome`, `--email`, `--logradouro`, `--numero`, `--cep` e `--cidade` (e opcionalmente `--complemento`). O comando define o tipo internamente, solicita a senha sem eco e grava somente o hash.

## Autenticação

| Método | Caminho | Entrada | Sucesso |
|---|---|---|---|
| `POST` | `/api/auth/login` | `email`, `senha` | `200`, perfil completo e cookie HttpOnly |
| `POST` | `/api/auth/logout` | — | `204`, sessão removida e cookie expirado |

O login grava uma sessão temporária em memória no cookie `recicla_sessao`, com `HttpOnly`, `SameSite=Lax`, `Path=/` e expiração de 30 minutos. O identificador da sessão nunca aparece no JSON.

Credenciais inválidas retornam `401` com a mesma mensagem genérica, sem indicar se o e-mail existe. Rotas autenticadas sem sessão retornam `401`. Mutações autenticadas com cookie exigem `Origin` ou `Referer` correspondente a uma origem CORS configurada ou à própria origem da API; origem ausente ou não permitida retorna `403`.

## Corpo de cadastro

```json
{
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "senha": "Senha123",
  "tipo": "doador",
  "endereco": {
    "logradouro": "Rua das Flores",
    "numero": "10A",
    "complemento": "Casa 2",
    "cep": "87000-000",
    "cidade": "Maringá"
  }
}
```

O e-mail é normalizado para minúsculas. O CEP aceita a forma com hífen na entrada, mas é persistido e devolvido com oito dígitos. `numero` permanece textual. `senha` é usada apenas para gerar `senha_hash` e nunca é retornada. Os cinco campos do endereço formam o subdocumento `endereco`, tanto no corpo HTTP quanto no documento `usuarios`. `complemento` é opcional; os demais são obrigatórios. O resumo público expõe apenas `cidade`.

## Itens

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/itens` | sessão | `texto`, `categoria`, `condicao`, `destino`, `cidade`, `preco_min`, `preco_max`, `incluir_reservados`, `offset`, `limite` | `200` com catálogo paginado |
| `GET` | `/api/itens/meus` | pessoa | `grupo` (`ativos`, `em_andamento`, `encerrados`), `offset`, `limite` | `200` com as ofertas da sessão |
| `POST` | `/api/itens` | pessoa | `ItemCreateRequest` com `publicar` | `201`, `Location` e item criado |
| `GET` | `/api/itens/{id}` | sessão | — | `200` com item |
| `PUT` | `/api/itens/{id}` | pessoa proprietária | `ItemUpdateRequest` | `200` com item atualizado |
| `POST` | `/api/itens/{id}/publicar` | pessoa proprietária | — | `200` com item publicado |
| `POST` | `/api/itens/{id}/entrega` | pessoa proprietária | — | `200` com item `aguardando_confirmacao` |
| `POST` | `/api/itens/{id}/recebimento` | pessoa selecionada | — | `200` com item `concluido` |
| `POST` | `/api/itens/{id}/arquivar` | pessoa proprietária | — | `200` com item arquivado |
| `DELETE` | `/api/itens/{id}` | pessoa proprietária | — | `204` sem corpo |

O `proprietario_id` é obtido da sessão no cadastro e não é aceito no corpo. O catálogo pode ser consultado por contas de pessoa e por pontos de coleta; somente contas de pessoa cadastram ofertas. Alteração e exclusão exigem correspondência entre a sessão e o proprietário do item.

Doação e venda têm entrega bilateral: o proprietário declara a entrega (`reservado → aguardando_confirmacao`) depois de a combinação estar aceita, e somente a pessoa selecionada confirma o recebimento (`aguardando_confirmacao → concluido`). Declarar não conclui; terceiro não confirma; repetir a confirmação devolve o mesmo resultado sem segundo efeito. O `PUT` comum não conclui item nem aceita `concluido`/`aguardando_confirmacao`.

O catálogo devolve apenas itens `disponivel` de doação ou revenda. Descarte, rascunho, arquivado e concluído nunca aparecem; `incluir_reservados=true` acrescenta itens `reservado`, sem oferecer ação de interesse. `destino=descarte` é recusado com `400`, e faixa de preço só vale para revenda. `texto` busca literalmente em título e descrição, sem interpretar expressão regular.

`publicar` no cadastro decide entre oferta publicada (padrão `true`) e rascunho. Rascunho aparece só em `GET /api/itens/meus` e pode ser publicado ou arquivado depois. Editar não muda situação: `publicar` e `arquivar` são comandos próprios, e a modalidade (`destino`) só pode ser corrigida enquanto o item é rascunho.

Categorias aceitas: `informatica`, `notebook`, `desktop`, `telefonia`, `celular`, `tablet`, `televisao`, `audio`, `eletrodomestico`, `perifericos`, `monitor`, `impressora` e `outro`. Também são aceitas entradas com maiúsculas, espaços, hífen e acentos equivalentes, devolvidas no formato canônico em minúsculas.

Condições aceitas: `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto` e `recondicionado` — condição física independente da modalidade. Novos cadastros e edições de ofertas aceitam `doacao` e `revenda`; `descarte` retorna `400` sem gravar. O item nasce `rascunho` quando `publicar=false`; publicado, fica `disponivel`. `revenda` exige `valor` informado e não negativo; doação não aceita preço. A leitura também aceita somente ofertas.

`especificacoes` é um subdocumento livre de textos, porque categorias diferentes têm características diferentes. O cadastro grava o primeiro evento em `historico` com etapa `publicacao` (ou `cadastro`, no rascunho), status correspondente, data do servidor e o proprietário como responsável. Publicar e arquivar também registram evento.

`GET /api/itens/meus` separa ofertas em `ativos` (rascunho e disponível), `em_andamento` (reservado e aguardando confirmação) e `encerrados` (concluído e arquivado). Proprietário e modalidade são filtrados antes da paginação. Arquivar exige oferta em `rascunho` ou `disponivel`; oferta reservada, aguardando confirmação ou concluída retorna `409` sem mudar de estado, e arquivar um item já arquivado é idempotente. Arquivar preserva item, histórico e referências; item arquivado não pode ser excluído.

A listagem aceita `offset` (padrão `0`) e `limite` (padrão `20`, máximo `100`), ordenada por `data_adicao` e ID decrescentes para desempate estável. O filtro `cidade` usa a cidade do proprietário e não expõe o endereço.

Transições permitidas, sem saltos entre fluxos:

| Destino | Sequência |
|---|---|
| `doacao` | `disponivel` → `reservado` → `aguardando_confirmacao` → `concluido` |
| `revenda` | `disponivel` → `reservado` → `aguardando_confirmacao` → `concluido` |

Reserva de doação e venda nasce da seleção de um interesse; o `PUT` comum não cria reserva com o módulo de interesses habilitado. Declarar entrega e confirmar recebimento têm endpoints próprios. O fluxo de descarte por equipamento é removido, sem campos, rotas ou consultas do processo anterior. Transição inválida retorna `400`; oferta concluída ou arquivada não aceita mais edição (`409`) e cada mudança acrescenta um evento a `historico`. O `PUT` substitui os campos descritivos; `comprador_id` não é aceito no corpo — o comprador vem do interesse selecionado.

| Comando | Exigência |
|---|---|
| `POST /api/itens/{id}/entrega` | interesse `selecionado`, combinação aceita e item `reservado` |
| `POST /api/itens/{id}/recebimento` | pessoa selecionada e item `aguardando_confirmacao` |

Campo de fluxo indevido retorna `400`, referência já definida retorna `409` e pessoa inexistente retorna `404`. Modalidade de oferta pode ser corrigida em rascunho ou disponível. A exclusão de oferta é aceita em `rascunho` ou `disponivel`, quando não houver referências; depois disso retorna `409`.

`beneficiario_id` é definido pelo servidor. `beneficiario_id` e `comprador_id` aparecem na resposta. Excluir uma pessoa que seja proprietária, beneficiária ou compradora de item retorna `409`, preservando a referência.

Exemplo de cadastro:

```json
{
  "titulo": "Notebook usado",
  "descricao": "Funcionando com bateria fraca",
  "categoria": "Informática",
  "marca": "Dell",
  "modelo": "Inspiron 15",
  "condicao": "funcional_com_defeito",
  "destino": "doacao",
  "valor": null,
  "especificacoes": {
    "memoria_ram": "8 GB",
    "armazenamento": "256 GB SSD"
  }
}
```

A resposta inclui `cidade_proprietario`, `especificacoes`, `historico` e, quando aplicável, `beneficiario_id` e `comprador_id`, mas não inclui o endereço completo. `id`, `proprietario_id`, `status`, `data_adicao` e `data_modificacao` são controlados pelo servidor. Dados inválidos retornam `400`, sessão ausente retorna `401`, origem inválida retorna `403`, perfil sem permissão retorna `403` e item inexistente retorna `404`.

## Corpo de atualização

```json
{
  "nome": "Maria Silva",
  "email": "maria.silva@example.com",
  "endereco": {
    "logradouro": "Avenida Brasil",
    "numero": "200",
    "complemento": null,
    "cep": "87010000",
    "cidade": "Sarandi"
  }
}
```

O servidor gera `data_adicao` no cadastro e mantém esse valor imutável. `data_modificacao` é atualizada pelo servidor a cada alteração; ambas são UTC.

## Interesses

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `POST` | `/api/interesses` | pessoa | `item_id` | `201` com interesse pendente |
| `GET` | `/api/interesses` | pessoa | `escopo=meus` (padrão) ou `recebidos`, `item_id`, `status`, `offset`, `limite` | `200` com lista restrita à sessão |
| `GET` | `/api/interesses/{id}` | participante | — | `200` com interesse |
| `PUT` | `/api/interesses/{id}/combinacao` | selecionado ou proprietário | `local_texto`, `previsao` e `observacao` | `200` com nova revisão da combinação |
| `POST` | `/api/interesses/{id}/combinacao/aceite` | contraparte de quem propôs | `revisao` | `200` com combinação aceita |
| `POST` | `/api/interesses/{id}/acoes` | participante autorizado | `acao` (`selecionar`, `recusar`, `desistir`, `liberar`, `retomar`, `reabrir`) e `motivo` quando exigido | `200` com interesse atualizado |
| `PATCH` | `/api/interesses/{id}` | participante autorizado | `status` (`selecionado`, `recusado`, `cancelado`) — alias legado | `200` com interesse atualizado |

O interessado vem da sessão, não do corpo. O cadastro exige item disponível de doação ou revenda, não pertencente ao próprio interessado. Operadores não manifestam interesse. O par `item_id`/`usuario_id` é único por índice; uma relação encerrada não é recriada nesta versão.

Estados do interesse: `pendente`, `selecionado`, `recusado`, `cancelado` e `encerrado`. Cada relação guarda `tentativa`, `motivo`, `preco_selecionado` e `historico` acumulativo.

Ações e permissões: `selecionar`, `recusar`, `liberar` e `reabrir` são do proprietário; `desistir` e `retomar` são do interessado. Recusar e liberar exigem `motivo`. `retomar` só vale para `cancelado` com item disponível e incrementa `tentativa`; `reabrir` só vale para `recusado` e também incrementa. `encerrado` não reabre. Terceiros não consultam detalhes nem alteram a relação; `recebidos` é restrito ao proprietário e os filtros são aplicados antes da paginação (`offset=0`, `limite=20`, máximo `100`).

Selecionar atualiza o interesse para `selecionado`, reserva o item (`reservado`, com `interesse_aceito_id`) e registra os dois históricos **na mesma transação**; outro selecionar concorrente retorna `409`. Os demais interesses permanecem `pendente` e não se cria interesse novo enquanto o item está reservado. Na venda, `preco_selecionado` congela o valor do item no momento da seleção.

Desistência do selecionado e liberação pelo proprietário encerram a reserva: o interesse vira `cancelado`, o item volta a `disponivel` e os demais pendentes continuam. Depois de a entrega avançar, a liberação unilateral retorna `409`.

A combinação guarda local textual, previsão opcional, observação, número da revisão e quem propôs/aceitou. Cada alteração cria revisão nova e invalida o aceite anterior; quem propôs não aceita a própria revisão, e a recusa por revisão desatualizada retorna `409`. A combinação não comprova entrega nem reserva horário externo.

Ao confirmar o recebimento, o item vira `concluido`, o interesse selecionado vira `encerrado` com `resultado=concluido` e os demais interesses pendentes viram `encerrado` com `resultado=item_concluido`. Os indicadores contam cada item uma única vez, somente depois dessa confirmação.

Com o módulo habilitado, o `PUT` comum do item não cria reserva: o proprietário precisa selecionar um interesse. A edição preserva a seleção interna e verifica o status lido, inclusive quando apenas os campos descritivos mudam. Referências de interesses existentes bloqueiam a exclusão do item e do interessado e a troca do destino (`409`); essas verificações de exclusão não constituem garantia transacional para todas as intercalações com criação concorrente.

Parâmetros de query desconhecidos são rejeitados com `400`. No detalhe, sessão e visibilidade são verificadas antes de validar o corpo, sem revelar a relação a terceiros. As evidências estão nos testes de runtime com replica set.

O Compose usa replica set de um nó para executar essas transações; consulte [docker/mongo/README.md](../docker/mongo/README.md). Sem suporte transacional, a operação falha com `503`, sem executar uma alternativa de escrita parcial. Entradas inválidas retornam `400`, sessão ausente `401`, ação não permitida `403`, recurso ausente ou não visível `404` e conflito de estado/unicidade `409`.

## Notificações

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/notificacoes` | sessão | `lida`, `offset`, `limite` | `200` com a caixa do próprio usuário |
| `PATCH` | `/api/notificacoes/{id}` | destinatário | `{"lida": true}` | `200` com a notificação lida |

Os avisos são criados pelo servidor, nunca pelo cliente. Tipos de aviso pertencem somente às ações de ofertas/interesses, sem entrega prevista, recebimento em ponto ou inativação de local. Cada aviso traz `link` interno para a tela em que o destinatário age, e o índice único por evento, destinatário e item impede repetição.

Nas decisões transacionais de interesse e nas transições de entrega que emitem avisos, a gravação ocorre na mesma transação: a decisão de um interesse avisa o interessado (aceito/recusado) ou o proprietário (cancelado), e cada transição de status avisa quem possui interesse pendente ou aceito no item. O aceite de uma doação também avisa os demais interessados de que o item foi reservado, sem repetir o aviso para quem foi escolhido; o cancelamento do aceite avisa que o item voltou a ficar disponível. Quem não tem vínculo com o item não recebe aviso, e o proprietário não é notificado das próprias mudanças.

Alterar/inativar um local não emite aviso de descarte. Avisos pertencem às ofertas; a revisão geral de produto é da Etapa 19. Links internos indicam a tela de ação, não necessariamente o registro individual. A emissão para cada evento previsto no desenho de produto deve ser conferida nos testes específicos.

O índice único por `evento_id`, destinatário e item garante uma única notificação por evento; repetir a gravação não duplica. A listagem é ordenada por `data_adicao` decrescente, aceita `offset`/`limite` (padrão 20, máximo 100) e o filtro `lida`. Marcar leitura preserva `data_adicao`, registra `data_leitura` e atualiza `data_modificacao`. Notificação de outro usuário ou identificador inválido retorna `404`; sessão ausente `401`; parâmetro desconhecido `400`.

## Pontos de coleta

A leitura do diretório é pública e não exige cadastro de item (Etapas 16–17). A Etapa 18 entrega a gestão privada “Meus locais”, sem fila de recebimento, e remove o processo anterior sem consultas do processo anterior ou compatibilidade.

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/pontos-coleta` | pública, mesmo sem cookie | `cidade`, `categoria`, `offset`, `limite` | `200`, lista de locais ativos com DTO público |
| `GET` | `/api/pontos-coleta/{id}` | pública | — | `200`, DTO público; `404` para inativo/inexistente |
| `GET` | `/api/pontos-coleta?escopo=meus` | operador | filtros anteriores e `ativo` opcional | `200`, somente locais próprios, incluindo inativos |
| `GET` | `/api/pontos-coleta/{id}?escopo=meus` | operador responsável | — | `200`, detalhe de gestão, inclusive inativo |
| `POST` | `/api/pontos-coleta` | conta `ponto_coleta` | `PontoColetaCreateRequest` | `201`, `Location` e ponto criado |
| `PUT` | `/api/pontos-coleta/{id}` | responsável | `PontoColetaUpdateRequest` | `200` com ponto atualizado |
| `POST` | `/api/pontos-coleta/{id}/situacao` | responsável | `{"ativo": bool}` | `200` com ponto ativo ou inativo |
| `DELETE` | `/api/pontos-coleta/{id}` | responsável | — | `204` sem corpo |

O DTO público contém somente `id`, `nome`, `endereco`, `categorias_aceitas` e `horario_atendimento`: não retorna responsável, datas internas, endereço pessoal, equipamento, histórico ou indicação privada. Enviar cookie não amplia essa projeção; é necessário selecionar explicitamente `escopo=meus` para a gestão. Esse escopo exige sessão operacional antes de validar filtros, sem fallback público: `401` sem sessão, `403` para pessoa comum e `404` no detalhe de gestão de local alheio.

Na leitura pública, filtros desconhecidos, repetidos e tentativas de enviar `ativo`, `responsavel_id`, `item_id` ou chave de operação retornam `400`. O detalhe só admite `escopo=meus` para a operação protegida. Cidade é literal, sem distinção de maiúsculas/minúsculas; categoria usa a enumeração existente. Os filtros e a visibilidade são aplicados antes da paginação, em ordem estável por nome e ID (`offset=0`, `limite=20`, máximo 100). Resultado vazio é `200` com lista vazia.

Consultas não criam sessão obrigatória nem documento de domínio, evento, aviso ou resultado de descarte. Registros antigos sem o campo `ativo` preservam a convenção existente de ativo por padrão, sem escrita de normalização; `ativo=false` é ocultado na lista e no detalhe públicos.

O ponto guarda nome, endereço aninhado, categorias aceitas e horário de atendimento. O `responsavel_id` vem da sessão, precisa ser uma conta `ponto_coleta` e não é aceito no corpo. `categorias_aceitas` exige ao menos uma categoria conhecida e recusa repetição.

Local inativo sai da consulta pública, mas continua visível na gestão do responsável. Inativar/reativar não modifica ofertas nem gera avisos ou confirmações de equipamento. Locais não mantêm referências a equipamentos. Alteração, situação e exclusão só são aceitas para o responsável; outro operador recebe `404`, sem revelar a existência do ponto. Excluir um usuário que ainda responde por um ponto retorna `409`, preservando a referência.

## Indicadores

| Método | Caminho | Autenticação | Sucesso |
|---|---|---|---|
| `GET` | `/api/indicadores` | sessão | `200` com `ofertas_ativas`, `pendencias`, `doados`, `vendidos`, `total` e `locais_ativos` |

`ofertas_ativas` conta ofertas disponíveis; `pendencias` reúne ofertas reservadas ou aguardando confirmação. `doados` e `vendidos` contam somente ofertas concluídas com confirmação bilateral; `total` soma essas conclusões. `locais_ativos` é contagem cadastral do diretório e não entra em `total`. Registros com modalidade fora de doação/revenda não participam de nenhuma chave. Consulta, cópia e gestão de locais não alteram resultados nem comprovam reciclagem.

O snapshot da OpenAPI gerada do runtime e suas diferenças em relação a esta descrição estão em [openapi.md](openapi.md).

## Exposição de dados

A lista e o acesso público a outro usuário retornam somente `id`, `nome`, `tipo` e `cidade`. E-mail e endereço completo aparecem apenas no perfil do próprio usuário autenticado. Senha e hash nunca aparecem em respostas.

E-mail duplicado retorna `409`. Em `PUT`/`DELETE` de usuário, a sessão e a propriedade são verificadas antes da existência do ID: outro ID retorna `403` mesmo inexistente. Para consulta de usuário e para recursos de item, identificador inexistente retorna `404`; dados inválidos retornam `400` com detalhes de validação.
