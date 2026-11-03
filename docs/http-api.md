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
| `GET` | `/api/itens` | sessão | filtros `categoria`, `condicao`, `destino`, `status` e `cidade`, com `offset` e `limite` | `200` com catálogo paginado |
| `POST` | `/api/itens` | doador | `ItemCreateRequest` | `201`, `Location` e item criado |
| `GET` | `/api/itens/{id}` | sessão | — | `200` com item |
| `PUT` | `/api/itens/{id}` | doador proprietário | `ItemUpdateRequest` | `200` com item atualizado |
| `DELETE` | `/api/itens/{id}` | doador proprietário | — | `204` sem corpo |

O `proprietario_id` é obtido da sessão no cadastro e não é aceito no corpo. O catálogo pode ser consultado por doadores, beneficiários e pontos de coleta; somente doadores podem cadastrar itens. Alteração e exclusão exigem correspondência entre a sessão e o proprietário do item.

Categorias aceitas: `informatica`, `notebook`, `desktop`, `telefonia`, `celular`, `tablet`, `televisao`, `audio`, `eletrodomestico`, `perifericos`, `monitor`, `impressora` e `outro`. Também são aceitas entradas com maiúsculas, espaços, hífen e acentos equivalentes, devolvidas no formato canônico em minúsculas.

Condições aceitas: `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto` e `recondicionado`. Destinos aceitos: `doacao`, `descarte` e `revenda`. Todo item começa com status `disponivel`. `revenda` exige `valor` não negativo; doação e descarte não aceitam preço.

`especificacoes` é um subdocumento livre de textos, porque categorias diferentes têm características diferentes. O cadastro grava o primeiro evento em `historico` com etapa `cadastro`, status `disponivel`, data do servidor e o proprietário como responsável.

A listagem aceita `offset` (padrão `0`) e `limite` (padrão `20`, máximo `100`), sempre ordenada por `data_adicao` decrescente. O filtro `cidade` usa a cidade do proprietário e não expõe o endereço.

Transições permitidas, sem saltos entre fluxos:

| Destino | Sequência |
|---|---|
| `doacao` | `disponivel` → `reservado` → `doado` |
| `descarte` | `disponivel` → `encaminhado` → `coletado` |
| `revenda` | `disponivel` → `em_avaliacao` → `recondicionado` → `vendido` |

A atualização aceita `status` opcional; transição inválida retorna `400`, item já concluído não volta a outro fluxo e cada transição acrescenta um evento a `historico` sem apagar os anteriores.

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

A resposta inclui `cidade_proprietario`, `especificacoes` e `historico`, mas não inclui o endereço completo. `id`, `proprietario_id`, `status`, `data_adicao` e `data_modificacao` são controlados pelo servidor. Dados inválidos retornam `400`, sessão ausente retorna `401`, origem inválida retorna `403`, perfil sem permissão retorna `403` e item inexistente retorna `404`.

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

## Exposição de dados

A lista e o acesso público a outro usuário retornam somente `id`, `nome`, `tipo` e `cidade`. E-mail e endereço completo aparecem apenas no perfil do próprio usuário autenticado. Senha e hash nunca aparecem em respostas.

E-mail duplicado retorna `409`. Em `PUT`/`DELETE` de usuário, a sessão e a propriedade são verificadas antes da existência do ID: outro ID retorna `403` mesmo inexistente. Para consulta de usuário e para recursos de item, identificador inexistente retorna `404`; dados inválidos retornam `400` com detalhes de validação.
