# TODO — implementação da v1.0

Este arquivo contém somente o trabalho necessário para concluir a primeira entrega. Funcionalidades de entregas posteriores não fazem parte desta lista de implementação.

## v1.0 — Primeira entrega

### Base já verificada

- [x] Implementar CRUD simples da coleção `usuarios`.
- [x] Separar API, Service, Repository, Model, Mapper e schemas.
- [x] Criar testes automatizados para a base de usuários.
- [x] Validar a integração com MongoDB real via Docker Compose.
- [x] Obter cobertura superior a 70% — resultado atual: 94,44%.

### Usuários — concluir antes da v1.0

- [x] Substituir `cidade` pelo subdocumento `endereco` com `logradouro`, `numero`, `complemento`, `cep` e `cidade`.
- [x] Normalizar CEP para oito dígitos.
- [x] Substituir `data_cadastro` por `data_adicao`.
- [x] Incluir `data_modificacao`.
- [x] Gerar e atualizar datas no servidor, em UTC.
- [x] Atualizar schemas, modelo, mapper, Service, Repository e API.
- [x] Definir regra de unicidade de e-mail.

### Itens — concluir antes da v1.0

- [x] Criar a coleção separada `itens`.
- [x] Implementar Model, schemas, Mapper, Repository, Service e API de itens.
- [x] Implementar CRUD em `/api/itens`.
- [x] Relacionar item ao usuário por `proprietario_id`.
- [x] Validar a existência do proprietário.
- [x] Definir categorias, condições e destinos.
- [x] Incluir `data_adicao` e `data_modificacao`.
- [x] Manter o endereço somente no usuário, sem cópia no item.
- [x] Permitir filtros de categoria, condição, destino e status.

### Segurança básica — concluir antes da v1.0

- [x] Adicionar `senha` ao contrato de cadastro sem retorná-la nas respostas.
- [x] Persistir somente `senha_hash` com Argon2id ou equivalente mantido.
- [x] Normalizar e tornar o e-mail único por índice no MongoDB.
- [x] Implementar `POST /api/auth/login` com resposta genérica para credenciais inválidas.
- [x] Criar sessões temporárias em memória com identificadores aleatórios seguros.
- [x] Enviar o identificador em cookie `recicla_sessao` com `HttpOnly`, `SameSite=Lax` e `Path=/`.
- [x] Configurar expiração 30 minutos após o login.
- [x] Implementar `POST /api/auth/logout` para remover a sessão e expirar o cookie.
- [x] Implementar `GET /api/usuarios/me`.
- [x] Proteger atualização e exclusão do usuário pela identidade da sessão.
- [x] Obter `proprietario_id` da sessão ao criar item.
- [x] Permitir alteração e exclusão de item somente pelo proprietário.
- [x] Aplicar permissões de `doador`, `beneficiario` e `ponto_coleta`.
- [x] Permitir cadastro público apenas de `doador` e `beneficiario`.
- [ ] Criar forma controlada de provisionar conta `ponto_coleta`.
- [x] Tornar `tipo` imutável na atualização comum.
- [x] Retornar `401` para falha de autenticação e `403` para falta de autorização.
- [x] Ocultar e-mail, endereço completo, senha e hash nos resumos públicos.
- [x] Restringir CORS às origens configuradas.
- [ ] Garantir que logs não incluam senha, hash ou identificador de sessão.
- [x] Criar testes automatizados de autenticação, autorização e exposição de dados.

### Frontend simples — concluir antes da v1.0

- [ ] Manter o cliente separado em `frontend/`.
- [ ] Criar estrutura simples em HTML, CSS e JavaScript, sem build obrigatório.
- [ ] Criar tela ou seção de cadastro.
- [ ] Criar tela ou seção de login.
- [ ] Criar visualização e edição do próprio perfil.
- [ ] Criar catálogo com filtros de itens.
- [ ] Criar formulário para o doador cadastrar e administrar itens próprios.
- [ ] Permitir ao ponto de coleta filtrar itens destinados a descarte.
- [ ] Ocultar ações incompatíveis com o perfil, sem substituir a autorização do backend.
- [ ] Usar `credentials: "include"` no frontend sem ler ou armazenar o cookie HttpOnly.
- [ ] Renderizar dados da API como texto para evitar injeção de HTML/script.
- [ ] Tratar validação, `401`, `403`, `404` e indisponibilidade da API.
- [ ] Configurar origem do frontend na lista CORS do backend.
- [ ] Validar o fluxo completo em navegador.

### Qualidade da v1.0

- [x] Atualizar os testes de usuários para o novo contrato.
- [x] Criar testes de Service, Repository e API para itens.
- [ ] Validar os dois CRUDs contra MongoDB real.
- [x] Confirmar cobertura mínima de 70% após todas as mudanças — resultado atual: 94,44%.
- [x] Atualizar documentação HTTP e arquitetura executável.
- [ ] Validar o projeto em máquina limpa.
- [ ] Publicar no GitHub e identificar a v1.0 por commit, tag ou release.
