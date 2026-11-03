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
| `POST` | `/api/itens/{id}/arquivar` | pessoa proprietária | — | `200` com item arquivado |
| `DELETE` | `/api/itens/{id}` | pessoa proprietária | — | `204` sem corpo |

O `proprietario_id` é obtido da sessão no cadastro e não é aceito no corpo. O catálogo pode ser consultado por contas de pessoa e por pontos de coleta; somente contas de pessoa cadastram ofertas. Alteração e exclusão exigem correspondência entre a sessão e o proprietário do item.

O catálogo devolve apenas itens `disponivel` de doação ou revenda. Descarte, rascunho, arquivado e concluído nunca aparecem; `incluir_reservados=true` acrescenta itens `reservado`, sem oferecer ação de interesse. `destino=descarte` é recusado com `400`, e faixa de preço só vale para revenda. `texto` busca literalmente em título e descrição, sem interpretar expressão regular.

`publicar` no cadastro decide entre oferta publicada (padrão `true`) e rascunho. Rascunho aparece só em `GET /api/itens/meus` e pode ser publicado ou arquivado depois. Editar não muda situação: `publicar` e `arquivar` são comandos próprios, e a modalidade (`destino`) só pode ser corrigida enquanto o item é rascunho.

Categorias aceitas: `informatica`, `notebook`, `desktop`, `telefonia`, `celular`, `tablet`, `televisao`, `audio`, `eletrodomestico`, `perifericos`, `monitor`, `impressora` e `outro`. Também são aceitas entradas com maiúsculas, espaços, hífen e acentos equivalentes, devolvidas no formato canônico em minúsculas.

Condições aceitas: `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto` e `recondicionado` — condição física independente da modalidade. Destinos aceitos: `doacao`, `descarte` e `revenda`. O item nasce `rascunho` quando `publicar=false` e `disponivel` caso contrário. `revenda` exige `valor` maior que zero; doação e descarte não aceitam preço.

`especificacoes` é um subdocumento livre de textos, porque categorias diferentes têm características diferentes. O cadastro grava o primeiro evento em `historico` com etapa `publicacao` (ou `cadastro`, no rascunho), status correspondente, data do servidor e o proprietário como responsável. Publicar e arquivar também registram evento.

`GET /api/itens/meus` agrupa: `ativos` (rascunho e disponível), `em_andamento` (reservado, encaminhado, em avaliação e recondicionado) e `encerrados` (doado, coletado, vendido e arquivado). Arquivar preserva item, histórico e referências; o item arquivado não pode ser excluído.

A listagem aceita `offset` (padrão `0`) e `limite` (padrão `20`, máximo `100`), sempre ordenada por `data_adicao` decrescente. O filtro `cidade` usa a cidade do proprietário e não expõe o endereço.

Transições permitidas, sem saltos entre fluxos:

| Destino | Sequência |
|---|---|
| `doacao` | `disponivel` → `reservado` → `doado` |
| `descarte` | `disponivel` → `encaminhado` → `coletado` |
| `revenda` | `disponivel` → `em_avaliacao` → `recondicionado` → `vendido` |

A atualização aceita `status` opcional; transição inválida retorna `400`, item já concluído não volta a outro fluxo e cada transição acrescenta um evento a `historico` sem apagar os anteriores. O `PUT` substitui os campos descritivos, mas `ponto_coleta_id` e `comprador_id` seguem regras próprias do fluxo.

Cada destino exige as referências abaixo no momento da transição:

| Transição | Exigência |
|---|---|
| `disponivel → encaminhado` | `ponto_coleta_id` de ponto existente que aceite a categoria do item |
| `encaminhado → coletado` | mantém o ponto definido no encaminhamento |
| `reservado → doado` | interesse `aceito` no item; o beneficiário vem desse interesse, nunca do corpo |
| `recondicionado → vendido` | `comprador_id` de outra pessoa cadastrada |

`ponto_coleta_id` só é aceito no encaminhamento e não pode ser trocado ou removido depois; `comprador_id` só é aceito na conclusão da revenda e também fica fixado. Campo de fluxo enviado para outro destino retorna `400`, referência já definida retorna `409`, ponto ou pessoa inexistente `404`, categoria não aceita `400` e conclusão de doação sem aceite `409`. O destino pode ser corrigido apenas enquanto o item está `disponivel` e não pode ser alterado junto com uma transição de status; depois de iniciado o fluxo, fica fixo. O encaminhamento valida a categoria enviada no próprio `PUT`. A transição aceita `observacao` opcional (até 300 caracteres), gravada no evento correspondente — por exemplo, o laudo da avaliação na revenda.

A exclusão só é aceita enquanto o item está `disponivel`; depois disso retorna `409`, preservando o histórico e as referências do fluxo. `observacao` sem transição de status é ignorada.

`beneficiario_id` é definido pelo servidor. `ponto_coleta_id`, `beneficiario_id` e `comprador_id` aparecem na resposta. Excluir um ponto ainda referenciado por item ou uma pessoa que seja proprietária, beneficiária ou compradora de item retorna `409`, preservando a referência.

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

A resposta inclui `cidade_proprietario`, `especificacoes`, `historico` e, quando aplicável, `ponto_coleta_id`, `beneficiario_id` e `comprador_id`, mas não inclui o endereço completo. `id`, `proprietario_id`, `status`, `data_adicao` e `data_modificacao` são controlados pelo servidor. Dados inválidos retornam `400`, sessão ausente retorna `401`, origem inválida retorna `403`, perfil sem permissão retorna `403` e item inexistente retorna `404`.

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
| `POST` | `/api/interesses` | doador ou beneficiário | `item_id` | `201` com interesse pendente |
| `GET` | `/api/interesses` | doador ou beneficiário | `escopo=meus` (padrão) ou `recebidos`, `item_id`, `status`, `offset`, `limite` | `200` com lista restrita à sessão |
| `GET` | `/api/interesses/{id}` | participante | — | `200` com interesse |
| `PATCH` | `/api/interesses/{id}` | participante autorizado para a ação | `status` | `200` com interesse atualizado |

O interessado vem da sessão, não do corpo. O cadastro exige item disponível de doação ou revenda, não pertencente ao próprio interessado. Operadores não manifestam interesse. O par `item_id`/`usuario_id` é único por índice; uma relação encerrada não é recriada nesta versão.

O proprietário pode aceitar ou recusar interesse pendente; o interessado pode cancelar o próprio interesse pendente ou aceito, antes de a operação avançar para um estado que impeça a liberação. Terceiros não consultam detalhes nem alteram a relação. `recebidos` é restrito ao proprietário e os filtros são aplicados antes da paginação (`offset=0`, `limite=20`, máximo `100`).

Aceitar uma doação atualiza o interesse, reserva o item e acrescenta o evento no histórico **na mesma transação**. Outro aceite concorrente retorna `409`. Cancelar o interesse aceito libera sua reserva e registra a liberação na mesma unidade. Na revenda, a seleção não antecipa avaliação/reparo: a etapa do item é mantida e apenas um interesse pode ficar selecionado.

Com o módulo habilitado, o `PUT` comum do item não cria uma reserva de doação: o proprietário precisa aceitar um interesse. A edição preserva a seleção interna e verifica o status lido, inclusive quando apenas os campos descritivos mudam. Referências de interesses existentes bloqueiam a exclusão do item e do interessado e a troca do destino (`409`); essas verificações de exclusão não constituem garantia transacional para todas as intercalações com criação concorrente.

Parâmetros de query desconhecidos são rejeitados com `400`. No detalhe, sessão e visibilidade são verificadas antes de validar o corpo, sem revelar a relação a terceiros. Veja as [evidências da etapa](verificacao-interesses.md).

O Compose usa replica set de um nó para executar essas transações; consulte [docker/mongo/README.md](../docker/mongo/README.md). Sem suporte transacional, a operação falha com `503`, sem executar uma alternativa de escrita parcial. Entradas inválidas retornam `400`, sessão ausente `401`, ação não permitida `403`, recurso ausente ou não visível `404` e conflito de estado/unicidade `409`.

## Notificações

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/notificacoes` | sessão | `lida`, `offset`, `limite` | `200` com a caixa do próprio usuário |
| `PATCH` | `/api/notificacoes/{id}` | destinatário | `{"lida": true}` | `200` com a notificação lida |

Os avisos são criados pelo servidor, nunca pelo cliente. Tipos: `interesse_aceito`, `interesse_recusado`, `interesse_cancelado`, `status_item_alterado` e `item_concluido`.

A emissão ocorre na **mesma transação** da mudança que a origina: a decisão de um interesse avisa o interessado (aceito/recusado) ou o proprietário (cancelado), e cada transição de status avisa quem possui interesse pendente ou aceito no item. O aceite de uma doação também avisa os demais interessados de que o item foi reservado, sem repetir o aviso para quem foi escolhido; o cancelamento do aceite avisa que o item voltou a ficar disponível. Quem não tem vínculo com o item não recebe aviso, e o proprietário não é notificado das próprias mudanças.

O índice único por `evento_id`, destinatário e item garante uma única notificação por evento; repetir a gravação não duplica. A listagem é ordenada por `data_adicao` decrescente, aceita `offset`/`limite` (padrão 20, máximo 100) e o filtro `lida`. Marcar leitura preserva `data_adicao`, registra `data_leitura` e atualiza `data_modificacao`. Notificação de outro usuário ou identificador inválido retorna `404`; sessão ausente `401`; parâmetro desconhecido `400`.

## Pontos de coleta

| Método | Caminho | Autenticação | Entrada | Sucesso |
|---|---|---|---|---|
| `GET` | `/api/pontos-coleta` | sessão | filtros `cidade`, `categoria`, `escopo=meus`, `offset`, `limite` | `200` com lista paginada |
| `POST` | `/api/pontos-coleta` | conta `ponto_coleta` | `PontoColetaCreateRequest` | `201`, `Location` e ponto criado |
| `GET` | `/api/pontos-coleta/{id}` | sessão | — | `200` com ponto |
| `PUT` | `/api/pontos-coleta/{id}` | responsável | `PontoColetaUpdateRequest` | `200` com ponto atualizado |
| `DELETE` | `/api/pontos-coleta/{id}` | responsável | — | `204` sem corpo |

O ponto guarda nome, endereço aninhado, categorias aceitas e horário de atendimento. O `responsavel_id` vem da sessão, precisa ser uma conta `ponto_coleta` e não é aceito no corpo.

`categorias_aceitas` exige ao menos uma categoria conhecida e recusa repetição. A listagem é ordenada por nome, aceita `offset`/`limite` (padrão 20, máximo 100) e o filtro `categoria` seleciona pontos que aceitam aquela categoria.

Alteração e exclusão só são aceitas para o responsável; outro operador recebe `404`, sem revelar a existência do ponto. Excluir um usuário que ainda responde por um ponto retorna `409`, preservando a referência.

## Indicadores

| Método | Caminho | Autenticação | Sucesso |
|---|---|---|---|
| `GET` | `/api/indicadores` | sessão | `200` com `doados`, `coletados`, `vendidos` e `total` |

Somente itens concluídos entram nos totais: `doado`, `coletado` e `vendido`. Itens disponíveis, reservados ou em andamento não são contados. Os números são da plataforma inteira, não de uma conta específica, e a consulta aceita qualquer sessão autenticada; sem sessão retorna `401`.

O snapshot da OpenAPI gerada do runtime e suas diferenças em relação a esta descrição estão em [openapi.md](openapi.md).

## Exposição de dados

A lista e o acesso público a outro usuário retornam somente `id`, `nome`, `tipo` e `cidade`. E-mail e endereço completo aparecem apenas no perfil do próprio usuário autenticado. Senha e hash nunca aparecem em respostas.

E-mail duplicado retorna `409`. Em `PUT`/`DELETE` de usuário, a sessão e a propriedade são verificadas antes da existência do ID: outro ID retorna `403` mesmo inexistente. Para consulta de usuário e para recursos de item, identificador inexistente retorna `404`; dados inválidos retornam `400` com detalhes de validação.
