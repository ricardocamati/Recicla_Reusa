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

**Motivação:** criar uma base funcional com endereço aninhado, auditoria temporal, cadastro seguro e autorização do próprio perfil, deixando a evolução para eletrônicos e relacionamentos visível nos commits posteriores.

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

**Consequência:** a pasta existe desde o início, mas não contém implementação neste marco.

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

**Motivação:** impedir que o cliente associe um item a outro usuário, manter o endereço normalizado em um único documento e permitir filtros independentes de catálogo.

**Consequência:** o Service coordena a validação do proprietário e a autorização de alteração/exclusão. A resposta pode derivar a cidade do usuário, mas o item não duplica o subdocumento `endereco`. Status inicial, identificador e auditoria permanecem controlados pelo servidor.
