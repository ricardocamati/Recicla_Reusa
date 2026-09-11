# Registro da entrega v1.0

## Identificação

- **Versão:** `v1.0`.
- **Commit de referência da mudança de modelo:** [`190595f`](https://github.com/ricardocamati/Recicla_Reusa/commit/190595f).
- **Tag da entrega corrigida:** `v1.0` — deve apontar para o commit final desta branch após a validação.
- **Branch de correção:** `feat/endereco-sem-subdocumento`.
- **Casos documentados:** 40; **funções de teste Python:** 58; **execuções Pytest verificadas:** 77.
- **Vídeo de apresentação:** pendente; a URL ainda não foi informada.

A tag e o commit final identificam a versão que contém as correções de segurança, rastreabilidade, cobertura e evidências. A publicação da tag ou de uma release no GitHub depende de autorização explícita.

## Escopo entregue

- CRUD de `usuarios` e `itens` em MongoDB;
- campos `logradouro`, `numero`, `complemento`, `cep` e `cidade` no nível raiz de `usuarios`, além de `proprietario_id` no item;
- autenticação por sessão em memória e cookie HttpOnly;
- autorização por perfil e propriedade;
- validação de origem em mutações autenticadas com cookie;
- frontend separado, servido sem etapa de build obrigatória;
- testes automatizados de API, Service, Repository, frontend, Docker e Selenium.

## Evidências reproduzíveis

| Evidência | Comando ou arquivo | Tipo |
|---|---|---|
| Suíte e cobertura | `.venv/Scripts/python.exe -m pytest -q --cov=app --cov-report=term-missing` | automatizada |
| Navegação das seis telas | `.venv/Scripts/python.exe -m pytest --no-cov -q tests/test_selenium_frontend.py` | automatizada, Chrome headless |
| Stack Docker/MongoDB/API/frontend | `scripts/validar_stack_docker.py` após `docker compose up -d --build` | automatizada, leitura da stack |
| CRUD E2E na stack isolada | `scripts/smoke_api_docker.py --crud` | automatizada, mutação temporária com limpeza |
| Resultado capturado | `evidencias/` | relatório versionado |

Os relatórios em `evidencias/` devem ser substituídos somente por saídas reais dos comandos indicados. Nenhum relatório usa credenciais, tokens ou dados pessoais.
