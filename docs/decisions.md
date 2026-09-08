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

## ADR-005 — Começar pela coleção `usuarios`

**Decisão:** o primeiro CRUD do repositório utiliza somente a coleção `usuarios`.

**Motivação:** criar uma base funcional pequena e deixar a evolução para eletrônicos e relacionamentos visível nos commits posteriores.

**Consequência:** o estado inicial ainda não executa os fluxos completos de doação, descarte e revenda.

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
