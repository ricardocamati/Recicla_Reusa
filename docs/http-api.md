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

## Autenticação

| Método | Caminho | Entrada | Sucesso |
|---|---|---|---|
| `POST` | `/api/auth/login` | `email`, `senha` | `200`, perfil completo e cookie HttpOnly |
| `POST` | `/api/auth/logout` | — | `204`, sessão removida e cookie expirado |

O login grava uma sessão temporária em memória no cookie `recicla_sessao`, com `HttpOnly`, `SameSite=Lax`, `Path=/` e expiração de 30 minutos. O identificador da sessão nunca aparece no JSON.

Credenciais inválidas retornam `401` com a mesma mensagem genérica, sem indicar se o e-mail existe. Rotas autenticadas sem sessão retornam `401`; tentativa de alterar ou excluir outro usuário retorna `403`.

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

O e-mail é normalizado para minúsculas. O CEP aceita a forma com hífen na entrada, mas é persistido e devolvido com oito dígitos. `numero` permanece textual. `senha` é usada apenas para gerar `senha_hash` e nunca é retornada.

## Corpo de atualização

```json
{
  "nome": "Maria Silva",
  "email": "maria.silva@example.com",
  "endereco": {
    "logradouro": "Avenida Brasil",
    "numero": "200",
    "cep": "87010000",
    "cidade": "Sarandi"
  }
}
```

O servidor gera `data_adicao` no cadastro e mantém esse valor imutável. `data_modificacao` é atualizada pelo servidor a cada alteração; ambas são UTC.

## Exposição de dados

A lista e o acesso público a outro usuário retornam somente `id`, `nome`, `tipo` e `cidade`. E-mail e endereço completo aparecem apenas no perfil do próprio usuário autenticado. Senha e hash nunca aparecem em respostas.

E-mail duplicado retorna `409`. Identificador inexistente retorna `404`. Dados inválidos retornam `400` com detalhes de validação.
