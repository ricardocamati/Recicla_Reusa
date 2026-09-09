# Harness operacional

Este arquivo reúne os comandos de instalação, execução e validação do projeto ao longo de sua evolução.

## Pré-requisitos

- Python 3.11 ou superior para a execução manual e os testes;
- Docker e Docker Compose v2 para executar o ambiente completo.

## Preparação

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
```

No Linux/macOS, substitua `.venv/Scripts/python.exe` por `.venv/bin/python`.

## Ambiente completo em Docker

```bash
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Serviços publicados:

| Serviço | Endereço |
|---|---|
| Backend | `http://localhost:8000` |
| Frontend Python `http.server` | `http://localhost:8080` |
| MongoDB | `localhost:27018` |
| Mongo Express | `http://localhost:18081` |

A API usa `mongo` como hostname dentro da rede Compose. O navegador usa a porta publicada do backend e o CORS inclui as origens do frontend nas portas `5500` e `8080`.

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

No ambiente completo, o frontend é servido pelo Python `http.server` na porta `8080`. Para execução manual sem container, ele pode ser servido separadamente a partir de `frontend/`, por exemplo:

```bash
.venv/Scripts/python.exe -m http.server 5500 --directory frontend
```

Endereço planejado: `http://127.0.0.1:5500/`. A origem deverá constar na configuração CORS do backend.

Os testes atuais usam:

- Service com repositório em memória;
- API com transporte ASGI;
- Repository com `mongomock`;
- API executada contra MongoDB real em Docker Compose, com CRUD completo validado;
- aplicação completa executável no Compose com backend FastAPI e frontend Python `http.server`.

A validação real realizada confirmou os serviços `mongo`, `backend` e `frontend` em execução saudável e os fluxos HTTP de criação, listagem, consulta, atualização e exclusão.

## Verificações futuras

À medida que novas coleções forem introduzidas, o harness deverá incluir comandos reproduzíveis para:

- preparar dados de demonstração;
- testar relacionamentos entre coleções;
- demonstrar os três fluxos de destinação;
- gerar relatório HTML de cobertura;

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

Docker Desktop foi validado neste ambiente com uma execução isolada e sem reutilizar o volume do MongoDB anterior. A configuração foi resolvida sem o `.env` local, as imagens do backend e frontend foram construídas com `--no-cache` e o Compose criou um volume MongoDB novo.

A validação executada confirmou:

- `docker compose config --quiet` → sucesso;
- backend FastAPI → healthcheck saudável;
- frontend Python `http.server` → healthcheck saudável;
- MongoDB 7.0 → healthcheck saudável;
- `GET /health`, `/docs`, páginas HTML e módulos JavaScript → HTTP `200`;
- base inicial de usuários → lista vazia;
- smoke test funcional → cadastro `201`, login `200`, `/me` `200`, CRUD de item, logout `204` e `/me` posterior `401`;
- frontend aberto no navegador a partir de `http://127.0.0.1:8080`.

A suíte completa também foi executada: 52 testes aprovados, cobertura total de 94,28%, compilação Python, verificação `node --check` dos módulos JavaScript e `git diff --check` sem erros.
