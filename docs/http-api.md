# Contratos HTTP

Base path: `/api/usuarios`. A documentação OpenAPI está disponível em `/docs`.

| Método | Caminho | Entrada | Sucesso |
|---|---|---|---|
| `GET` | `/api/usuarios` | — | `200` com lista resumida |
| `GET` | `/api/usuarios/{id}` | — | `200` com usuário completo |
| `POST` | `/api/usuarios` | `UsuarioCreateRequest` | `201`, `Location` e usuário |
| `PUT` | `/api/usuarios/{id}` | `UsuarioUpdateRequest` | `200` com usuário |
| `DELETE` | `/api/usuarios/{id}` | — | `204` sem corpo |

## Corpo de criação/atualização

```json
{
  "nome": "Maria",
  "email": "maria@example.com",
  "tipo": "doador",
  "cidade": "Maringá"
}
```

`tipo` aceita `doador`, `beneficiario` ou `ponto_coleta`. O servidor gera `data_cadastro` no POST.

Identificador inexistente retorna `404`. Dados inválidos retornam `400` com `fieldErrors`.
