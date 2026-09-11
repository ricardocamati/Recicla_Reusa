# Requisitos da versão 1.0

## 1. Objetivo

Entregar a primeira versão funcional da PoC com cadastros de usuários e itens eletrônicos, campos de endereço planos na persistência, auditoria temporal, POO, documentação e testes automatizados.

> **Estado atual:** o backend atende aos requisitos de usuários, itens, endereço, auditoria, sessão, autorização e provisionamento controlado de `ponto_coleta`; o frontend simples em HTML, CSS e JavaScript também está implementado e validado em navegador.

## 2. Requisitos funcionais

### V1-RF-01 — Cadastrar usuário

Cadastrar usuário por `POST /api/usuarios` com `nome`, `email`, `senha`, `tipo`, `logradouro`, `numero`, `complemento`, `cep` e `cidade`, todos no nível raiz do corpo e da coleção `usuarios`.

**Critérios de aceitação:**

- `logradouro`, `numero`, `cep` e `cidade` são obrigatórios; `complemento` é opcional;
- a chave `endereco` não faz parte do contrato HTTP v1.0 nem é gravada como subdocumento MongoDB;
- servidor gera `id`, `data_adicao` e `data_modificacao`;
- criação válida retorna HTTP `201` e cabeçalho `Location`;
- documento é persistido em `usuarios`.
- senha nunca aparece na resposta e somente seu hash é persistido.
- cadastro público aceita somente `doador` e `beneficiario`; conta `ponto_coleta` é provisionada pelo responsável técnico.
- o provisionamento operacional é feito localmente por `python -m app.provisionar_ponto_coleta`, que não recebe `tipo` como argumento e solicita a senha sem eco.

### V1-RF-02 — Listar usuários

Listar usuários por `GET /api/usuarios`, retornando HTTP `200` e uma lista pública resumida, inclusive quando vazia. E-mail, senha, hash e endereço completo não são expostos.

### V1-RF-03 — Consultar usuário

Consultar usuário por `GET /api/usuarios/{id}`. O próprio usuário autenticado recebe seus dados completos, exceto senha/hash; outros usuários recebem somente o resumo público. Recurso inexistente retorna HTTP `404`.

### V1-RF-04 — Atualizar usuário

Atualizar campos permitidos por `PUT /api/usuarios/{id}`. Somente o próprio usuário pode alterar seus dados; `id`, `tipo` e `data_adicao` são preservados e `data_modificacao` é renovada.

### V1-RF-05 — Excluir usuário

Excluir usuário por `DELETE /api/usuarios/{id}`. Somente o próprio usuário pode excluir seu cadastro. Usuário existente retorna HTTP `204`; inexistente retorna HTTP `404`.

### V1-RF-06 — Cadastrar item

Cadastrar item por `POST /api/itens` com `titulo`, `descricao`, `categoria`, `marca`, `modelo`, `condicao`, `destino` e `valor` quando aplicável. `proprietario_id` é obtido da sessão autenticada, não do corpo da requisição.

**Critérios de aceitação:**

- proprietário precisa existir;
- servidor gera `id`, `status`, `data_adicao` e `data_modificacao`;
- criação válida retorna HTTP `201` e cabeçalho `Location`;
- documento é persistido em `itens`.
- somente usuário do tipo `doador` pode cadastrar item.

### V1-RF-07 — Listar itens

Listar itens por `GET /api/itens`, com filtros opcionais de categoria, condição, destino e status.

### V1-RF-08 — Consultar item

Consultar item por `GET /api/itens/{id}`. Item existente retorna HTTP `200`; inexistente ou inválido retorna HTTP `404`.

### V1-RF-09 — Atualizar item

Atualizar os dados permitidos por `PUT /api/itens/{id}`. Somente o proprietário pode atualizar; `id`, `proprietario_id` e `data_adicao` são preservados e `data_modificacao` é renovada.

### V1-RF-10 — Excluir item

Excluir item por `DELETE /api/itens/{id}`. Somente o proprietário pode excluir; item existente retorna HTTP `204` e inexistente retorna HTTP `404`.

### V1-RF-11 — Validar entradas

Rejeitar campos ausentes, formatos inválidos, referências inexistentes e valores incompatíveis com as regras de negócio, sem persistência parcial.

### V1-RF-12 — Documentar a API

Disponibilizar OpenAPI em `/docs` e `/openapi.json` com os endpoints dos dois CRUDs.

### V1-RF-13 — Autenticar usuário

Autenticar por `POST /api/auth/login` com e-mail e senha. Quando as credenciais forem válidas, o servidor cria uma sessão temporária e envia seu identificador aleatório em cookie HttpOnly.

### V1-RF-14 — Consultar usuário autenticado

Disponibilizar `GET /api/usuarios/me` para retornar o perfil completo do usuário autenticado, sem senha ou hash.

### V1-RF-15 — Autorizar doador

Permitir ao `doador` cadastrar, atualizar e excluir somente seus próprios itens, além de consultar o catálogo.

### V1-RF-16 — Autorizar beneficiário

Permitir ao `beneficiario` consultar e filtrar o catálogo. Registro de interesse permanece para a v2.0.

### V1-RF-17 — Autorizar ponto de coleta

Permitir ao `ponto_coleta` previamente provisionado consultar o catálogo e filtrar itens destinados a descarte. Gestão de pontos e coleta permanece para a v2.0.

### V1-RF-18 — Tratar falhas de acesso

Retornar HTTP `401` para sessão ausente, inválida ou expirada e HTTP `403` quando o usuário autenticado não tiver perfil, propriedade ou origem permitida para a operação.

### V1-RF-19 — Disponibilizar frontend simples

Disponibilizar em `frontend/` um cliente web simples em HTML, CSS e JavaScript capaz de consumir a API da v1.0.

**Critérios de aceitação:**

- oferece cadastro e login;
- permite consultar e editar o próprio perfil;
- apresenta catálogo e filtros de itens;
- permite ao doador cadastrar e administrar os próprios itens;
- permite ao ponto de coleta visualizar itens destinados a descarte;
- apresenta mensagens compreensíveis para validação, `401`, `403`, `404` e falha de conexão;
- oculta ações não permitidas ao perfil, sem substituir a autorização obrigatória no backend;
- não contém segredos e não armazena senha, hash ou identificador de sessão em JavaScript ou `localStorage`.

### V1-RF-20 — Encerrar sessão

Encerrar o acesso por `POST /api/auth/logout`, removendo a sessão no servidor e expirando o cookie no navegador.

## 3. Requisitos não funcionais

### V1-RNF-01 — Banco NoSQL

Usar efetivamente MongoDB com as coleções `usuarios` e `itens`.

### V1-RNF-02 — Campos planos de endereço

Persistir `logradouro`, `numero`, `complemento`, `cep` e `cidade` como campos do nível raiz de `usuarios`, sem `usuarios.endereco`. Itens permanecem em coleção separada e referenciam usuários.

### V1-RNF-03 — Programação orientada a objetos

Usar classes de Model, Service, Repository e Mapper para os dois domínios.

### V1-RNF-04 — Separação de responsabilidades

Rotas tratam HTTP, Services coordenam casos de uso, Repositories persistem e schemas validam contratos.

### V1-RNF-05 — Testes automatizados

Os comportamentos implementados devem possuir testes executáveis sem intervenção manual.

### V1-RNF-06 — Cobertura

A cobertura deve ser igual ou superior a 70% e possuir comando reproduzível.

### V1-RNF-07 — Documentação

README e documentos técnicos devem explicar problema, ODS, tecnologias, instalação, execução, API e testes.

### V1-RNF-08 — Versionamento

Publicar a versão em GitHub acessível, com histórico e identificação por commit, tag ou release.

### V1-RNF-09 — Configuração segura

Credenciais locais devem ficar fora do Git; `.env.example` e Docker Compose devem permitir configuração reproduzível.

### V1-RNF-10 — Compatibilidade

Usar Python 3.11 ou superior e MongoDB 7.0.

### V1-RNF-11 — Proteção de senha

Persistir senha somente por hash forte com salt, usando biblioteca mantida; nunca registrar ou retornar senha ou hash.

### V1-RNF-12 — Sessão de acesso

Usar sessão temporária mantida no servidor e identificador aleatório enviado em cookie HttpOnly. A sessão deve ser validada em todas as rotas protegidas e invalidada no logout. Mutações autenticadas que carregam esse cookie devem exigir `Origin` ou `Referer` correspondente a uma origem configurada ou à própria origem da API.

### V1-RNF-13 — Superfície mínima

Restringir CORS às origens configuradas, rejeitar com HTTP `403` mutações autenticadas com origem ausente ou não permitida e manter MongoDB sem exposição pública desnecessária.

### V1-RNF-14 — Respostas seguras

Falhas de login não devem revelar se o e-mail existe, e logs não devem conter senha, hash ou identificador de sessão.

### V1-RNF-15 — Frontend independente

Manter o frontend separado em `frontend/`, sem framework ou etapa de build obrigatória, responsivo para uso básico e integrado somente aos contratos públicos da API.

## 4. Fora do escopo da v1.0

- coleção `interesses`;
- coleção `pontos_coleta`;
- coleção `notificacoes`;
- histórico como lista de subdocumentos;
- notificações sobre interesse;
- execução completa dos fluxos de doação, descarte e revenda;
- pagamentos, logística real, autenticação avançada e frontend avançado.
