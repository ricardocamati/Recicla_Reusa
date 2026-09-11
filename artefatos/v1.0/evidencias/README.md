# Evidências reproduzíveis da v1.0

Esta pasta contém saídas capturadas de comandos executados sobre a versão entregue. Os scripts e comandos são a fonte de reprodução; os relatórios são somente evidência do ambiente em que foram executados.

## Comandos

```bash
.venv/Scripts/python.exe -m pytest -q --cov=app --cov-report=term-missing
.venv/Scripts/python.exe -m pytest --no-cov -q tests/test_selenium_frontend.py
docker compose up -d --build
.venv/Scripts/python.exe scripts/validar_stack_docker.py
.venv/Scripts/python.exe scripts/smoke_api_docker.py --crud
docker compose down
```

## Arquivos

- `testes.txt`: saída real da suíte com cobertura;
- `selenium.txt`: saída real do teste de navegador;
- `docker.txt`: saída real do verificador e do CRUD E2E em stack Docker/MongoDB isolada.

Os relatórios não devem conter senhas, hashes, cookies, tokens ou strings de conexão. `validar_stack_docker.py` é somente de leitura depois que a stack é iniciada; `smoke_api_docker.py --crud` cria um usuário/item temporários somente na stack isolada e remove esses dados ao terminar.
