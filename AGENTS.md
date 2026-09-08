# Orientações para agentes de IA

## Objetivo do projeto

O Recicla/Reusa é uma PoC acadêmica de Engenharia de Software alinhada ao ODS 12. O produto completo deverá apoiar doação, descarte formal e reaproveitamento/revenda de eletrônicos, com rastreamento do ciclo de vida.

O estado inicial possui somente o CRUD da coleção MongoDB `usuarios`. Essa limitação é intencional para que a evolução arquitetural e funcional permaneça visível no histórico do projeto.

## Stack

- Python 3.11+
- FastAPI e Uvicorn
- PyMongo e MongoDB
- Pydantic
- Pytest, pytest-cov e mongomock
- Docker Compose
- frontend simples da v1.0 em HTML, CSS e JavaScript

## Arquitetura

```text
API -> Schema -> Service -> Repository -> MongoDB
MongoDB -> Model -> Service -> Mapper -> Response Schema -> API
```

## Responsabilidades

- **API:** HTTP, validação e status; nenhuma regra de negócio ou persistência direta.
- **Schemas:** contratos públicos por caso de uso.
- **Service:** casos de uso e regras do domínio.
- **Repository:** persistência e consulta.
- **Model:** documento MongoDB, não contrato HTTP.
- **Mapper:** conversões explícitas.
- **Frontend:** cliente separado, consumindo apenas a API pública.

## Domínio planejado

- `usuarios`: participantes;
- `itens`: eletrônicos e destino;
- `interesses`: solicitações de doação/revenda;
- `pontos_coleta`: destinação de descarte;
- `historico`: subdocumentos aninhados em itens.

Fluxos futuros:

- doação: disponível → reservado → doado;
- descarte: disponível → encaminhado → coletado;
- revenda: disponível → em avaliação → recondicionado → vendido.

## Regras de desenvolvimento

1. Examinar os arquivos existentes antes de alterar uma área.
2. Preservar a separação de responsabilidades.
3. Não expor Models MongoDB diretamente pela API.
4. Não colocar regras no Repository ou nas rotas.
5. Criar DTOs específicos quando os casos de uso divergirem.
6. Introduzir abstrações somente quando houver necessidade concreta.
7. Toda funcionalidade ou correção deve possuir teste automatizado aplicável.
8. Executar a suíte completa antes de concluir.
9. Manter cobertura mínima de 70% em cada marco.
10. Atualizar README, arquitetura, decisões e contratos quando necessário.
11. Não versionar `.env`, credenciais reais, caches ou ambientes virtuais.
12. Manter `frontend/` separado de `app/`.
13. Respeitar o escopo de cada etapa para preservar a evolução demonstrável do projeto.

## Processo de trabalho

1. Ler `README.md`, `HARNESS.md` e a documentação da área afetada.
2. Escrever ou atualizar o teste do comportamento.
3. Implementar a menor solução coerente.
4. Executar testes e cobertura.
5. Revisar arquitetura, documentação e limitações reais.
