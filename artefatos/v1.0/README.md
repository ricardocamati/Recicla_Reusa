# Artefatos da versão 1.0 — Primeira entrega

A versão 1.0 tem como meta uma base funcional com usuários e itens eletrônicos. Os itens ficam em coleção própria; somente o endereço é um subdocumento do usuário.

## Escopo definido para a entrega

- coleção `usuarios` com CRUD;
- coleção `itens` com CRUD;
- item relacionado ao proprietário por `proprietario_id`;
- `endereco` como subdocumento de `usuarios`;
- `data_adicao` e `data_modificacao` em todos os documentos das duas coleções;
- autenticação básica por e-mail e senha com sessão em cookie HttpOnly;
- autorização por tipo de usuário e propriedade do recurso;
- frontend simples em HTML, CSS e JavaScript, separado do backend;
- API FastAPI documentada por OpenAPI;
- testes automatizados com cobertura mínima de 70%;
- aplicação completa executada em Docker Compose, com backend FastAPI e frontend Python `http.server`.

## Situação do código

O backend atual conclui o núcleo de `usuarios` e o CRUD de `itens`: cadastro público de doadores e beneficiários, endereço aninhado, datas de auditoria em UTC, e-mail normalizado com índice único, hash de senha, login, logout, perfil próprio, catálogo filtrável e proteção de atualização/exclusão pela sessão. Contas `ponto_coleta` são provisionadas pelo comando administrativo local, sem permitir autoatribuição no cadastro público. Itens usam coleção própria, referenciam o proprietário por `proprietario_id` e não duplicam o endereço. Listagens públicas usam resumo sem e-mail ou endereço completo.

O frontend simples está implementado em `frontend/`, com cadastro, login, perfil, catálogo, filtros e gestão de itens próprios. Os fluxos de interesse/coleta detalhados permanecem dependentes da v2.0.

## Documentos

- [requisitos.md](requisitos.md)
- [regras_de_negocio.md](regras_de_negocio.md)
- [modelo_dados.md](modelo_dados.md)
- [casos_de_teste.md](casos_de_teste.md)
- [matriz_rastreabilidade.md](matriz_rastreabilidade.md)

## Evidências verificadas

- CRUD HTTP de usuários com endereço aninhado e auditoria temporal;
- MongoDB 7.0 real via Docker Compose, coleções `usuarios`/`itens`, índices e CRUDs completos com limpeza dos dados de teste;
- login, logout, sessão HttpOnly, perfil próprio e autorização do usuário;
- provisionamento controlado de `ponto_coleta` por comando local, com senha solicitada sem eco;
- frontend validado em navegador com API e MongoDB ativos;
- frontend servido pelo Python `http.server` e backend executados em um Compose integrado, com volume MongoDB novo;
- 52 testes automatizados aprovados;
- cobertura total atual de 94,28%.

## Pendências para fechar a v1.0

- produzir as evidências externas de GitHub e identificação da versão.
