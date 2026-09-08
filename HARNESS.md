# Harness operacional

Este arquivo reúne os comandos de instalação, execução e validação do projeto ao longo de sua evolução.

## Pré-requisitos

- Python 3.11 ou superior;
- Docker e Docker Compose v2 para o MongoDB local.

## Preparação

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
```

No Linux/macOS, substitua `.venv/Scripts/python.exe` por `.venv/bin/python`.

## Infraestrutura

```bash
docker compose up -d
docker compose ps
```

Serviços previstos:

| Serviço | Endereço |
|---|---|
| MongoDB | `localhost:27018` |
| Mongo Express | `http://localhost:18081` |

Encerrar preservando dados:

```bash
docker compose down
```

## Backend

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Verificações do estado atual:

```bash
curl -i http://127.0.0.1:8000/api/usuarios
curl -i http://127.0.0.1:8000/openapi.json
```

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Testes e cobertura

```bash
.venv/Scripts/python.exe -m pytest
```

O `pyproject.toml` exige cobertura mínima de 70% e mostra as linhas não cobertas no terminal.

## Frontend da v1.0

O frontend simples será servido separadamente a partir de `frontend/`, por exemplo:

```bash
.venv/Scripts/python.exe -m http.server 5500 --directory frontend
```

Endereço planejado: `http://127.0.0.1:5500/`. A origem deverá constar na configuração CORS do backend.

Os testes atuais usam:

- Service com repositório em memória;
- API com transporte ASGI;
- Repository com `mongomock`;
- API executada contra MongoDB real em Docker Compose, com CRUD completo validado.

A validação real realizada confirmou os serviços `mongo` e `mongo-express` em execução saudável e o fluxo HTTP de criação, listagem, consulta, atualização e exclusão.

## Verificações futuras

À medida que novas coleções forem introduzidas, o harness deverá incluir comandos reproduzíveis para:

- preparar dados de demonstração;
- testar relacionamentos entre coleções;
- demonstrar os três fluxos de destinação;
- gerar relatório HTML de cobertura;
- validar o frontend separado da v1.0.

## Definition of Done

Uma tarefa está concluída quando:

1. o projeto importa e executa;
2. os testes aplicáveis passam;
3. a cobertura permanece em pelo menos 70%;
4. contratos HTTP e documentação estão sincronizados;
5. não há regra de negócio na API ou no Repository;
6. limitações de ambiente foram relatadas;
7. o escopo do marco da AEP foi respeitado.

## Validação realizada

Docker Desktop foi validado neste ambiente. O MongoDB 7.0 e o Mongo Express iniciaram pelo Compose, o container `mongo` ficou saudável e a API executou o CRUD real de usuários contra a coleção `usuarios`.

A validação executada foi:

- `POST /api/usuarios` → `201`;
- `GET /api/usuarios` → `200`;
- `PUT /api/usuarios/{id}` → `200`;
- `DELETE /api/usuarios/{id}` → `204`;
- consulta após exclusão → `404`.

A validação em uma máquina limpa ainda está pendente.
