# Artefatos da versão 1.0 — Primeira entrega

A versão 1.0 passa a ter como meta uma base funcional com usuários e itens eletrônicos. Os itens ficam em coleção própria; somente o endereço é um subdocumento.

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

O backend atual implementa somente o CRUD simples de `usuarios`, ainda com `cidade` e `data_cadastro`, sem autenticação. A pasta `frontend/` existe, mas ainda está vazia. Portanto, endereço aninhado, novas datas, coleção `itens`, segurança básica e frontend estão **planejados para completar a v1.0**, mas ainda não devem ser apresentados como implementados.

## Documentos

- [requisitos.md](requisitos.md)
- [regras_de_negocio.md](regras_de_negocio.md)
- [modelo_dados.md](modelo_dados.md)
- [casos_de_teste.md](casos_de_teste.md)
- [matriz_rastreabilidade.md](matriz_rastreabilidade.md)

## Evidências já verificadas da base atual

- CRUD simples de usuários executável;
- MongoDB 7.0 validado via Docker Compose;
- 6 testes automatizados aprovados;
- cobertura total atual de 94,44%.

## Pendências para fechar a v1.0

- migrar usuário para `endereco`, `data_adicao` e `data_modificacao`;
- implementar a coleção e o CRUD de `itens`;
- implementar senha com hash, sessão simples e autorização por perfil/proprietário;
- implementar as telas simples de cadastro, login, perfil e catálogo/gestão de itens;
- atualizar e ampliar os testes;
- repetir a validação com MongoDB real;
- produzir as evidências externas de GitHub e identificação da versão.
