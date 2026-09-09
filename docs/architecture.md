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

O frontend permanece em uma pasta própria na raiz e conclui o escopo simples da v1.0. Ele usa HTML, CSS e JavaScript, sem etapa de build obrigatória, consumindo somente os contratos públicos da API.

## Execução integrada com Docker Compose

A execução reproduzível usa três serviços principais no mesmo Compose, com Mongo Express opcional:

```text
Navegador --HTTP--> frontend (Python http.server:80)
Navegador --HTTP/CORS--> backend (Uvicorn:8000) -> mongo (MongoDB:27017)
```

O frontend é servido como conteúdo estático pelo Python `http.server`. A API é publicada na porta local `8000` para que o navegador possa enviar requisições com `credentials: "include"`; o backend acessa o MongoDB pelo hostname interno `mongo`. Healthchecks impedem que o frontend seja iniciado antes de a API e o banco estarem disponíveis. Mongo Express permanece como ferramenta opcional de inspeção local.

## Responsabilidades

- **API (`app/api`)**: traduz HTTP em chamadas de casos de uso, valida DTOs e define respostas HTTP.
- **Schemas (`app/schemas`)**: contratos Pydantic específicos para criação, atualização, login e resposta.
- **Services (`app/services`)**: regras de negócio, autenticação, unicidade e coordenação dos casos de uso.
- **Repositories (`app/repositories`)**: persistência e consultas MongoDB, incluindo o índice único de e-mail.
- **Models (`app/models`)**: representação dos documentos persistidos, incluindo o endereço aninhado e auditoria temporal.
- **Mappers (`app/mappers`)**: conversões explícitas entre contratos e modelos, sem expor `senha_hash`.
- **Security (`app/security`)**: hash de senha com scrypt, sessões em memória e identificadores aleatórios.
- **Exceptions**: falhas do domínio tratadas de forma centralizada pela API.
- **Frontend (`frontend`)**: cliente web simples da v1.0, separado do backend.

Models de persistência não devem ser expostos diretamente como contratos HTTP.

## Estado atual de usuários

O fluxo implementado é:

```text
/api/usuarios e /api/auth
        -> UsuarioService
        -> MongoUsuarioRepository
        -> usuarios
```

Um documento persistido possui a seguinte forma lógica:

```json
{
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "tipo": "doador",
  "endereco": {
    "logradouro": "Rua das Flores",
    "numero": "10A",
    "complemento": "Casa 2",
    "cep": "87000000",
    "cidade": "Maringá"
  },
  "senha_hash": "scrypt$...",
  "data_adicao": "2026-09-07T12:00:00Z",
  "data_modificacao": "2026-09-07T12:00:00Z"
}
```

O `_id` do MongoDB é convertido para `id` nos DTOs. `data_adicao` e `data_modificacao` são geradas pelo servidor em UTC. O índice `usuario_email_unico` impede duplicidade depois da normalização do e-mail.

Listagens públicas usam DTOs resumidos. O perfil completo exige que a sessão corresponda ao usuário consultado; a autorização de alteração e exclusão também é validada no backend.

## Estado atual de itens

O fluxo implementado é:

```text
/api/itens
      -> ItemService
      -> MongoItemRepository
      -> itens
           |
           +--> proprietario_id -> usuarios
```

O item fica em coleção própria. O Service consulta o usuário relacionado para validar o proprietário e derivar somente sua cidade no DTO público; `endereco`, `senha_hash` e demais dados privados não são copiados nem expostos. O repositório cria índices para proprietário, categoria, condição, destino e status.

O cadastro obtém `proprietario_id` da sessão, inicia `status` como `disponivel` e gera as duas datas em UTC. Atualizações preservam o identificador, o proprietário e `data_adicao`; somente o proprietário pode alterar ou excluir o recurso.

## Segurança implementada

O cadastro público aceita somente `doador` e `beneficiario`. A senha não é persistida em texto claro: o Service gera um hash scrypt com salt aleatório. O login cria uma sessão em memória e devolve apenas o cookie `recicla_sessao`, configurado como `HttpOnly`, `SameSite=Lax`, `Path=/` e com duração de 30 minutos.

As origens CORS são lidas de `CORS_ORIGINS`; credenciais são permitidas somente para essa lista. O frontend usa `credentials: "include"` sem tentar ler o cookie.

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

Services recebem o repositório por injeção de dependência e o relógio por injeção opcional. Isso permite testar datas, expiração de sessão e regras sem depender do relógio do sistema. Os testes do repositório usam `mongomock`; a aplicação utiliza PyMongo e MongoDB em execução normal.
