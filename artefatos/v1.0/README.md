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
- testes automatizados com cobertura mínima de 70%.

## Situação do código

O backend atual conclui o núcleo de `usuarios` e o CRUD de `itens`: cadastro público de doadores e beneficiários, endereço aninhado, datas de auditoria em UTC, e-mail normalizado com índice único, hash de senha, login, logout, perfil próprio, catálogo filtrável e proteção de atualização/exclusão pela sessão. Itens usam coleção própria, referenciam o proprietário por `proprietario_id` e não duplicam o endereço. Listagens públicas usam resumo sem e-mail ou endereço completo.

O frontend simples continua pendente. O provisionamento de contas `ponto_coleta` e os fluxos de interesse/coleta permanecem dependentes das próximas implementações.

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
- 35 testes automatizados aprovados;
- cobertura total atual de 94,54%.

## Pendências para fechar a v1.0

- implementar as telas simples de cadastro, login, perfil e catálogo/gestão de itens;
- produzir as evidências externas de GitHub e identificação da versão.
