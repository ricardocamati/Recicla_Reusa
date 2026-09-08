# Recicla/Reusa — Plataforma de Doação, Descarte e Reaproveitamento de Eletrônicos

PoC acadêmica que pretende oferecer um fluxo único e rastreável para eletrônicos usados, direcionando cada equipamento para **doação**, **descarte formal** ou **reaproveitamento/revenda**.

## 1. Problema

Eletrônicos usados frequentemente permanecem parados, são descartados de forma incorreta ou deixam de ser reaproveitados por falta de um canal organizado. Ao mesmo tempo, pessoas e instituições podem precisar de equipamentos funcionais ou de baixo custo, enquanto pontos de coleta e cooperativas dependem do encaminhamento correto desses materiais.

**Problema central:** falta de uma plataforma que conecte usuários, equipamentos e destinos adequados, mantendo o histórico do eletrônico desde o cadastro até sua destinação final.

## 2. ODS atendido

O projeto está alinhado principalmente ao **ODS 12 — Consumo e Produção Responsáveis** porque pretende:

- prolongar a vida útil de aparelhos;
- incentivar doação e reaproveitamento antes do descarte;
- encaminhar resíduos eletrônicos a pontos de coleta;
- registrar resultados como itens doados, reaproveitados ou descartados corretamente.

Também pode contribuir secundariamente com o ODS 11, pela destinação urbana adequada, e com a redução de desigualdades por meio da doação de equipamentos.

## 3. Visão da solução

A plataforma deverá permitir que usuários cadastrem eletrônicos e escolham um destino inicial:

- **Doação:** disponibilização gratuita para outro usuário ou instituição.
- **Descarte:** encaminhamento para ponto de coleta ou cooperativa.
- **Reaproveitamento/revenda:** avaliação, eventual reparo e disponibilização para venda.

Cada destino terá seu próprio fluxo de status e um histórico rastreável. O sistema registrará o processo; a PoC não realizará reparos físicos, pagamentos ou transporte real.

## 4. Público-alvo

- pessoas com eletrônicos ociosos;
- pessoas ou instituições interessadas em receber equipamentos;
- compradores de equipamentos usados ou recondicionados;
- pontos de coleta e cooperativas de reciclagem.

## 5. Evolução incremental da AEP

### Estado inicial do repositório

O primeiro marco começa pequeno, com uma única coleção MongoDB chamada `usuarios` e CRUD completo. Os documentos são simples e homogêneos, contendo `nome`, `email`, `tipo`, `cidade` e `data_cadastro`.

Esse início cria a base de participantes que será relacionada aos eletrônicos nas etapas seguintes e permite que a evolução fique visível no histórico de commits.

### Evolução planejada

A solução deverá evoluir para múltiplas coleções:

- `usuarios`: proprietários, interessados e responsáveis por pontos de coleta;
- `itens`: eletrônicos cadastrados e seu destino atual;
- `interesses`: solicitações relacionadas a doação ou revenda;
- `pontos_coleta`: locais de recebimento para descarte formal.

A coleção `itens` deverá conter uma lista de subdocumentos com o histórico do ciclo de vida:

```json
{
  "titulo": "Notebook usado",
  "usuario_id": "...",
  "destino": "revenda",
  "historico": [
    {"etapa": "cadastro", "status": "disponivel", "data": "..."},
    {"etapa": "avaliacao", "status": "reparavel", "data": "..."},
    {"etapa": "reaproveitamento", "status": "recondicionado", "data": "..."}
  ]
}
```

## 6. Stack planejada

- Python 3.11+;
- FastAPI e Uvicorn;
- MongoDB e PyMongo;
- Pydantic;
- Pytest, pytest-cov e mongomock;
- HTML, CSS e JavaScript no frontend simples da v1.0;
- Docker Compose para o ambiente local.

## 7. Arquitetura

```text
Frontend -> API FastAPI -> Service -> Repository -> MongoDB
MongoDB -> Model -> Mapper -> DTO de resposta -> API
```

A separação entre API, DTOs, serviços, repositórios, modelos e mapeadores mantém as responsabilidades explícitas e demonstra o uso de programação orientada a objetos.

Consulte [docs/architecture.md](docs/architecture.md), [docs/decisions.md](docs/decisions.md), [docs/http-api.md](docs/http-api.md) e [TODO.md](TODO.md).

Os artefatos estão separados por entrega em [artefatos/v1.0/](artefatos/v1.0/) e [artefatos/v2.0/](artefatos/v2.0/), com requisitos, regras de negócio, modelo de dados, casos de teste e matriz próprios para cada versão.

## 8. Estrutura do repositório

```text
app/            backend Python
frontend/       cliente web simples planejado para a v1.0
 tests/         testes automatizados
docs/           arquitetura, decisões e contratos
compose.yaml    MongoDB local
pyproject.toml  dependências e configuração de testes
```

## 9. Execução do estado atual

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
docker compose up -d
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Documentação interativa: <http://127.0.0.1:8000/docs>.

O CRUD inicial está em `/api/usuarios`. Os contratos estão documentados em [docs/http-api.md](docs/http-api.md).

## 10. Testes e cobertura

```bash
.venv/Scripts/python.exe -m pytest
```

A suíte deve manter cobertura mínima de **70%**, conforme a AEP. Os testes unitários do repositório usam `mongomock`; a aplicação utiliza PyMongo e MongoDB em execução normal.

## 11. Limites atuais

Ainda não foram implementados itens eletrônicos, autenticação nem o frontend simples da v1.0. Interesses, pontos de coleta, notificações e fluxos completos permanecem na especificação da v2.0, fora do `TODO.md` de implementação atual.

> Projeto iniciado a partir do **template fornecido** e adaptado para Python conforme a proposta da AEP.
