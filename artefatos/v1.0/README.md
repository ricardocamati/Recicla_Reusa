# Artefatos da versão 1.0 — Primeira entrega

A versão 1.0 tem como meta uma base funcional com usuários e itens eletrônicos. Os itens ficam em coleção própria e os campos de endereço ficam no nível raiz do documento de usuário.

## Escopo definido para a entrega

- coleção `usuarios` com CRUD;
- coleção `itens` com CRUD;
- item relacionado ao proprietário por `proprietario_id`;
- `logradouro`, `numero`, `complemento`, `cep` e `cidade` como campos planos de `usuarios`;
- `data_adicao` e `data_modificacao` em todos os documentos das duas coleções;
- autenticação básica por e-mail e senha com sessão em cookie HttpOnly;
- autorização por tipo de usuário e propriedade do recurso;
- proteção de origem em mutações autenticadas com cookie;
- frontend simples em HTML, CSS e JavaScript, separado do backend;
- API FastAPI documentada por OpenAPI;
- testes automatizados com cobertura mínima de 70%;
- aplicação completa executada em Docker Compose, com backend FastAPI e frontend Python `http.server`.

## Situação do código

O backend atual conclui o núcleo de `usuarios` e o CRUD de `itens`: cadastro público de doadores e beneficiários, campos de endereço planos no documento MongoDB, datas de auditoria em UTC, e-mail normalizado com índice único, hash de senha, login, logout, perfil próprio, catálogo filtrável e proteção de atualização/exclusão pela sessão. Contas `ponto_coleta` são provisionadas pelo comando administrativo local, sem permitir autoatribuição no cadastro público. Itens usam coleção própria, referenciam o proprietário por `proprietario_id` e não duplicam o endereço. Listagens públicas usam resumo sem e-mail ou endereço completo.

O frontend simples está implementado em `frontend/`, com cadastro, login, perfil, catálogo, filtros e gestão de itens próprios. Os fluxos de interesse/coleta detalhados permanecem dependentes da v2.0.

## Documentos

- [requisitos.md](requisitos.md)
- [regras_de_negocio.md](regras_de_negocio.md)
- [modelo_dados.md](modelo_dados.md)
- [casos_de_teste.md](casos_de_teste.md)
- [matriz_rastreabilidade.md](matriz_rastreabilidade.md)
- [registro_entrega.md](registro_entrega.md)
- [evidencias/](evidencias/)

## Evidências verificadas

- CRUD HTTP de usuários com endereço persistido em campos planos e auditoria temporal;
- MongoDB 7.0 real via Docker Compose, coleções `usuarios`/`itens`, índices e CRUDs completos com limpeza dos dados de teste;
- login, logout, sessão HttpOnly, perfil próprio e autorização do usuário;
- provisionamento controlado de `ponto_coleta` por comando local, com senha solicitada sem eco;
- proteção `Origin`/`Referer` validada pelo backend em mutações autenticadas;
- frontend validado em navegador com API e MongoDB ativos;
- seis telas do frontend validadas com Selenium e Chrome headless, usando servidores locais isolados;
- frontend servido pelo Python `http.server` e backend executados em um Compose integrado, com volume MongoDB novo;
- 77 testes automatizados aprovados;
- cobertura total atual de 94,87%, incluindo `app/main.py`;
- verificador read-only e smoke E2E Docker/MongoDB versionados em `scripts/`, com relatórios em `evidencias/`.

## Pendências para fechar a v1.0

- informar a URL pública do vídeo de apresentação;
- publicar a tag/release no GitHub, após autorização explícita;
- concluir a política/teste específico de logging sem segredos, caso logging de aplicação seja adicionado.
