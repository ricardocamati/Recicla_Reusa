# Arquitetura

## Visão geral

O Recicla/Reusa usa uma arquitetura em camadas para separar protocolo HTTP, casos de uso, persistência e contratos públicos.

```text
Frontend
   |
   v
API FastAPI -> Request DTO -> Service -> Repository -> MongoDB
                                         |
MongoDB -> Model -> Service -> Mapper -> Response DTO -> JSON
```

O frontend permanece em uma pasta própria na raiz e faz parte do escopo planejado da v1.0. Será simples, em HTML, CSS e JavaScript, consumindo somente os contratos públicos da API.

## Responsabilidades

- **API (`app/api`)**: traduz HTTP em chamadas de casos de uso, valida DTOs e define respostas HTTP.
- **Schemas (`app/schemas`)**: contratos Pydantic específicos para criação, atualização e resposta.
- **Services (`app/services`)**: regras de negócio, transições e coordenação dos casos de uso.
- **Repositories (`app/repositories`)**: persistência e consultas MongoDB, sem regras do domínio.
- **Models (`app/models`)**: representação dos documentos persistidos.
- **Mappers (`app/mappers`)**: conversões explícitas entre contratos e modelos.
- **Exceptions**: falhas do domínio tratadas de forma centralizada pela API.
- **Frontend (`frontend`)**: cliente web simples da v1.0, separado do backend.

Models de persistência não devem ser expostos diretamente como contratos HTTP.

## Estado inicial

O repositório começa com o fluxo abaixo:

```text
/api/usuarios -> UsuarioService -> MongoUsuarioRepository -> usuarios
```

A coleção `usuarios` possui documentos homogêneos:

```json
{
  "nome": "Maria",
  "email": "maria@example.com",
  "tipo": "doador",
  "cidade": "Maringá",
  "data_cadastro": "2026-09-07T12:00:00Z"
}
```

Esse recorte é intencional: entrega um CRUD funcional sem antecipar a complexidade prevista para a evolução.

## Arquitetura-alvo

```text
usuarios ----< itens ----< historico[]
    |            |
    |            +----< interesses
    |
    +-----------------> pontos_coleta
```

Coleções planejadas:

- `usuarios`: participantes da plataforma;
- `itens`: eletrônicos, proprietário, destino e status;
- `interesses`: manifestações de interesse em doação ou revenda;
- `pontos_coleta`: locais para destinação formal.

`itens.historico` será uma lista de subdocumentos contendo etapa, status, data, responsável e observação opcional.

## Fluxos de negócio planejados

| Destino | Fluxo inicial previsto |
|---|---|
| Doação | disponível → reservado → doado |
| Descarte | disponível → encaminhado → coletado |
| Reaproveitamento/revenda | disponível → em avaliação → recondicionado → vendido |

As regras de transição deverão permanecer no Service. Uma abstração como Strategy ou State somente será introduzida quando os três fluxos estiverem implementados e justificarem o custo adicional.

## Testabilidade

Services recebem o repositório por injeção de dependência. Isso permite testes unitários sem MongoDB e mantém um repositório PyMongo real para execução. A integração inicial com MongoDB real foi validada via Docker Compose, enquanto os testes automatizados rápidos continuam usando `mongomock`.
