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

## Segurança implementada

O cadastro público aceita somente `doador` e `beneficiario`. A senha não é persistida em texto claro: o Service gera um hash scrypt com salt aleatório. O login cria uma sessão em memória e devolve apenas o cookie `recicla_sessao`, configurado como `HttpOnly`, `SameSite=Lax`, `Path=/` e com duração de 30 minutos.

As origens CORS são lidas de `CORS_ORIGINS`; credenciais são permitidas somente para essa lista. O frontend deverá usar `credentials: "include"` sem tentar ler o cookie.

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
