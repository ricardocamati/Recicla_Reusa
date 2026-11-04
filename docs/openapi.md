# OpenAPI do runtime

O arquivo [openapi.json](openapi.json) é um snapshot gerado a partir da aplicação real, não escrito à mão. Ele permite comparar o contrato executável com a descrição em [http-api.md](http-api.md).

## Como regenerar

```bash
python scripts/gerar_openapi.py
python -m pytest tests/test_openapi_runtime.py -q --no-cov -o addopts=
```

O teste falha quando o snapshot diverge do runtime, então qualquer mudança de rota ou modelo exige regenerar e revisar o diff.

## Cobertura

O snapshot reúne os caminhos de usuários, sessão, itens, interesses e combinação, pontos de coleta, encaminhamentos, destinação informada, notificações, indicadores e saúde. Todas as rotas de negócio descritas em [http-api.md](http-api.md) aparecem na OpenAPI com os mesmos métodos.

## Diferenças registradas

- **Validação:** o FastAPI anuncia `422` para corpo inválido, mas o runtime converte `RequestValidationError` em `400` com a lista de erros. A prosa documenta `400`; a OpenAPI mantém o `422` padrão do framework.
- **Erros de negócio:** `401`, `403`, `404`, `409` e `503` são descritos em prosa e não declaram esquema de resposta na OpenAPI. O runtime devolve `{"detail": "..."}`.
- **`/health`:** existe na OpenAPI e não faz parte do contrato de negócio em `http-api.md`.
- **Autenticação:** a sessão via cookie `HttpOnly` não é representada como security scheme; os endpoints aparecem sem `security` declarado, embora exijam sessão em runtime.

Essas diferenças são de representação, não de comportamento: a suíte executa os endpoints reais e cobre os códigos devolvidos.
