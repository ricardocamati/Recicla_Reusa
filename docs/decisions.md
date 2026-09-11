# Decisões arquiteturais

## ADR-001 — Python 3.11+

**Decisão:** desenvolver o backend em Python 3.11 ou superior.

**Motivação:** utilizar uma linguagem com suporte direto a programação orientada a objetos, tipagem moderna e ferramentas simples para API e testes.

**Consequência:** o template Java do professor permanece como referência de organização, mas não como stack de execução.

## ADR-002 — FastAPI e Pydantic

**Decisão:** usar FastAPI para HTTP e Pydantic para os contratos de entrada e saída.

**Motivação:** validação declarativa, documentação OpenAPI automática e baixo volume de configuração.

**Consequência:** a documentação interativa fica disponível em `/docs`.

## ADR-003 — MongoDB com PyMongo

**Decisão:** usar MongoDB como banco NoSQL e PyMongo como driver.

**Motivação:** atender ao requisito da AEP e permitir evolução natural de documentos simples para listas de subdocumentos.

**Consequência:** consultas e conversões BSON ficam isoladas nos repositórios.

## ADR-004 — Arquitetura em camadas

**Decisão:** separar API, Schemas, Service, Repository, Model, Mapper e Exceptions.

**Motivação:** tornar responsabilidades e conceitos de POO visíveis para avaliação.

**Consequência:** há mais arquivos pequenos, mas a API não expõe diretamente documentos MongoDB e as regras não ficam nos Controllers.

## ADR-005 — Concluir primeiro o núcleo `usuarios`

**Decisão:** a primeira entrega conclui o fluxo de usuários antes de introduzir a coleção `itens`.

**Motivação:** criar uma base funcional com endereço, auditoria temporal, cadastro seguro e autorização do próprio perfil, deixando a evolução para eletrônicos e relacionamentos visível nos commits posteriores.

**Consequência:** usuários já possuem contrato estável para serem referenciados pelos itens; os fluxos completos de doação, descarte e revenda continuam fora deste marco.

## ADR-006 — Evolução para múltiplas coleções

**Decisão:** planejar `usuarios`, `itens`, `interesses` e `pontos_coleta`, com histórico aninhado em `itens`.

**Motivação:** atender à etapa avançada da AEP e representar o ciclo de vida de um eletrônico.

**Consequência:** relacionamentos usarão identificadores entre coleções e subdocumentos quando pertencentes ao ciclo de vida do próprio item.

## ADR-007 — Regras de fluxo no Service

**Decisão:** transições de doação, descarte e reaproveitamento ficarão na camada Service.

**Motivação:** evitar regra de negócio em rotas ou repositórios.

**Consequência:** Strategy ou State poderá ser adotado somente quando houver comportamentos distintos suficientes para justificar a abstração.

## ADR-008 — Frontend separado

**Decisão:** manter `frontend/` na raiz, separado de `app/`.

**Motivação:** permitir evolução independente do cliente web e do backend.

**Consequência:** a pasta contém as seis telas HTML, o tema escuro e módulos JavaScript separados; o frontend é servido sem etapa de build obrigatória.

## ADR-009 — Estratégia de testes

**Decisão:** usar Pytest, pytest-cov e `mongomock` nos testes unitários de persistência.

**Motivação:** garantir execução reproduzível mesmo sem Docker nos testes unitários, mantendo também uma validação de integração real para a entrega.

**Consequência:** os testes unitários usam `mongomock` e a integração inicial foi validada contra MongoDB 7.0 em Docker Compose.

## ADR-010 — Sessão de usuário em memória

**Decisão:** autenticar com sessões temporárias armazenadas em memória e identificador aleatório enviado em cookie HttpOnly.

**Motivação:** atender à segurança básica da primeira entrega sem introduzir infraestrutura adicional de persistência de sessões; a autorização permanece no backend.

**Consequência:** reiniciar a aplicação invalida as sessões ativas. O cookie usa `SameSite=Lax`, `Path=/` e expiração de 30 minutos; a evolução futura poderá substituir o armazenamento quando houver necessidade de múltiplas instâncias.

## ADR-011 — Item em coleção própria e proprietário derivado da sessão

**Decisão:** persistir itens na coleção `itens`, relacionando-os a `usuarios` por `proprietario_id`; no cadastro, esse identificador será obtido exclusivamente da sessão autenticada.

**Motivação:** impedir que o cliente associe um item a outro usuário, manter os campos de endereço no documento do usuário e permitir filtros independentes de catálogo.

**Consequência:** o Service coordena a validação do proprietário e a autorização de alteração/exclusão. A resposta pode derivar a cidade do usuário, mas o item não duplica os campos de endereço. Status inicial, identificador e auditoria permanecem controlados pelo servidor.

## ADR-012 — Provisionamento local de ponto de coleta

**Decisão:** criar contas `ponto_coleta` somente pelo comando administrativo local `python -m app.provisionar_ponto_coleta`, sem rota HTTP pública para atribuição desse perfil.

**Motivação:** impedir autoatribuição de privilégio mantendo a segurança da PoC simples, sem introduzir JWT ou uma conta administrativa adicional.

**Consequência:** o cadastro HTTP continua limitado a `doador` e `beneficiario`; o comando recebe os dados operacionais, define `tipo` internamente e solicita a senha sem eco antes de persistir o hash.

## ADR-013 — Compose integrado para validação reproduzível

**Decisão:** usar Docker Compose para orquestrar MongoDB, backend FastAPI/Uvicorn e frontend estático com Python `http.server`, mantendo portas locais publicadas para o navegador e healthchecks entre as dependências.

**Motivação:** permitir que uma máquina limpa execute a PoC sem instalar Python, Node.js ou dependências da aplicação, preservando também a execução manual para desenvolvimento.

**Consequência:** o backend usa `mongo` como hostname interno, o frontend continua sem etapa de build e o CORS inclui as origens das portas estáticas configuradas. O volume do MongoDB é persistente por padrão; a remoção exige `docker compose down -v` explícito.

## ADR-014 — Proteção de origem para sessões por cookie

**Decisão:** CORS não será tratado como única proteção contra CSRF. Toda mutação (`POST`, `PUT`, `PATCH` ou `DELETE`) que carrega o cookie de sessão deve validar `Origin` ou `Referer` contra as origens configuradas; a origem da própria API também é permitida.

**Motivação:** CORS controla a leitura da resposta, mas não impede sozinho o envio de uma requisição cross-site com efeito colateral.

**Consequência:** `app/main.py` responde `403` quando a origem está ausente ou não permitida. O comportamento é coberto por `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403`.

## ADR-015 — Precedência dos códigos 403 e 404

**Decisão:** nas operações `PUT` e `DELETE` de usuário, a API autentica a sessão e verifica a propriedade antes de consultar a existência do identificador. Em operações de item, o Service consulta o item antes de verificar a propriedade.

**Motivação:** evita revelar a existência de identificadores de usuários a uma sessão que não é titular, sem alterar o contrato útil do catálogo de itens.

**Consequência:** usuário com ID diferente da sessão recebe `403`, inclusive se o ID não existir; consulta ou mutação do próprio ID inexistente pode retornar `404`. Item inexistente retorna `404`; item existente de outro proprietário retorna `403`. A regra está em `V1-RN-15`, `V1-RN-25` e `docs/http-api.md`.

## ADR-016 — Evidências versionadas de execução

**Decisão:** as validações externas à suíte unitária devem ter scripts reproduzíveis e relatórios sem credenciais em `artefatos/v1.0/evidencias/`.

**Motivação:** um relato manual não permite auditar a execução real de Docker, MongoDB e navegador.

**Consequência:** `scripts/validar_stack_docker.py` valida a stack sem mutação; `scripts/smoke_api_docker.py --crud` executa o fluxo E2E em ambiente isolado e remove apenas os dados temporários criados pelo próprio teste; o Selenium possui relatório próprio.

## ADR-017 — Campos de endereço planos na persistência

**Decisão:** representar `logradouro`, `numero`, `complemento`, `cep` e `cidade` como campos no nível raiz do modelo de domínio, dos DTOs HTTP e de `usuarios`, sem o subdocumento `endereco` em nenhuma camada da v1.0.

**Motivação:** manter uma representação única e simples do endereço em todo o fluxo, evitando divergência entre o contrato JSON, o domínio e o documento MongoDB.

**Consequência:** o Mapper transporta os campos planos diretamente entre request, domínio, response e Repository. A v1.0 não grava nem aceita `usuarios.endereco`; subdocumentos previstos para históricos e especificações continuam pertencendo ao escopo futuro da v2.0.
