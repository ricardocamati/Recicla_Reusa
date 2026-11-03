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

### Estado atual do repositório

As duas entregas estão concluídas no código: a v1.0 está publicada e a v2.0 foi implementada por etapas, com PRs revisados, suíte de 170 testes e jornadas reais em Docker registradas em [verificação da Etapa 8](docs/verificacao-etapa8.md). A v2.0 cobre usuários com endereço aninhado, itens com especificações e histórico, pontos de coleta, interesses e reserva, os fluxos de doação, descarte e revenda, notificações transacionais, indicadores e as telas correspondentes, com datas em UTC, sessão em cookie HttpOnly e autorização por identidade e propriedade.

Itens referenciam o usuário por `proprietario_id` e não duplicam o endereço. O aceite de interesse em uma doação reserva o item e registra seu histórico na mesma transação MongoDB. A conclusão registra o beneficiário do interesse aceito, o ponto de coleta do descarte e o comprador da revenda. As notificações são emitidas na mesma transação da decisão de interesse e da mudança de status do item. A área autenticada reúne indicadores de itens concluídos e telas de interesses, pontos de coleta e notificações. Consulte as verificações de [interesses](docs/verificacao-interesses.md), [fluxos](docs/verificacao-fluxos.md), [notificações](docs/verificacao-notificacoes.md) e [indicadores e telas](docs/verificacao-etapa7.md), além do contrato [OpenAPI](docs/openapi.md).

### Modelo em uso

A v2.0 usa cinco coleções: `usuarios`, `itens`, `interesses`, `pontos_coleta` e `notificacoes`. Cada item guarda o histórico acumulativo do ciclo de vida:

```json
{
  "titulo": "Notebook usado",
  "proprietario_id": "...",
  "destino": "revenda",
  "historico": [
    {"etapa": "cadastro", "status": "disponivel", "data": "..."},
    {"etapa": "avaliacao", "status": "reparavel", "data": "..."},
    {"etapa": "reaproveitamento", "status": "recondicionado", "data": "..."}
  ]
}
```

A v2.1 está documentada em [artefatos/v2.1/](artefatos/v2.1/) e avança por etapas no [TODO](TODO.md). A Etapa 9 já saiu do papel: o cadastro público agora cria apenas conta de pessoa, que oferece e demonstra interesse com a mesma sessão, enquanto o operador continua provisionado e restrito aos próprios pontos. As etapas seguintes da v2.1 ainda não têm código.

## 6. Stack planejada

- Python 3.11+;
- FastAPI e Uvicorn;
- MongoDB e PyMongo;
- Pydantic;
- Pytest, pytest-cov, mongomock e Selenium;
- HTML, CSS e JavaScript no frontend simples da v2.0, sem build;
- Docker Compose para o ambiente local.

## 7. Arquitetura

```text
Frontend -> API FastAPI -> Service -> Repository -> MongoDB
MongoDB -> Model -> Mapper -> DTO de resposta -> API
```

A separação entre API, DTOs, serviços, repositórios, modelos e mapeadores mantém as responsabilidades explícitas e demonstra o uso de programação orientada a objetos.

Consulte [docs/architecture.md](docs/architecture.md), [docs/decisions.md](docs/decisions.md), [docs/http-api.md](docs/http-api.md) e [TODO.md](TODO.md).

Os artefatos estão separados por entrega em [artefatos/v1.0/](artefatos/v1.0/) e [artefatos/v2.0/](artefatos/v2.0/), com requisitos, regras de negócio, modelo de dados, casos de teste e matriz próprios para cada versão. O [registro da entrega v1.0](artefatos/v1.0/registro_entrega.md) vincula a base ao commit verificável e reúne as [evidências reproduzíveis](artefatos/v1.0/evidencias/).

## 8. Estrutura do repositório

```text
app/            backend Python em camadas (api, services, repositories, models)
frontend/       telas HTML e JavaScript modular, sem build
tests/          suíte pytest, incluindo Selenium e integração com MongoDB
docs/           arquitetura, decisões, contratos e verificações por etapa
scripts/        geração da OpenAPI, smoke Docker e jornadas pela interface
artefatos/      requisitos, regras, casos de teste e matriz por versão
compose.yaml    MongoDB em replica set, backend FastAPI e frontend
Dockerfile      imagem do backend
pyproject.toml  dependências e configuração de testes
```

## 9. Execução em máquina limpa com Docker

O Compose sobe MongoDB, backend e frontend sem exigir Python, Node.js ou instalação de dependências na máquina host. Essa é a forma recomendada para validar a entrega.

```bash
# Opcional: criar configurações locais a partir do exemplo.
cp .env.example .env

# Validar a configuração resolvida sem iniciar os serviços.
docker compose config --quiet

# Construir as imagens e iniciar a aplicação.
docker compose up -d --build

# Conferir o estado e os healthchecks.
docker compose ps
```

Acesse:

- frontend: <http://127.0.0.1:8080>;
- saúde da API: <http://127.0.0.1:8000/health>;
- documentação OpenAPI: <http://127.0.0.1:8000/docs>;
- Mongo Express opcional: <http://127.0.0.1:18081>.

O backend usa o nome de serviço `mongo` para acessar o banco dentro da rede Docker. O navegador acessa a API pela porta publicada `8000`, e o Compose acrescenta as origens das portas `5500` e `8080` à configuração CORS. Além do CORS, mutações que transportam o cookie de sessão exigem `Origin` ou `Referer` permitido. `SECURE_COOKIES=false` é intencional no ambiente HTTP local; em produção, use HTTPS e uma configuração própria.

Para acompanhar os logs e encerrar o ambiente:

```bash
docker compose logs -f backend frontend
docker compose down
```

`docker compose down -v` remove também o volume do MongoDB e deve ser usado somente quando a base local puder ser apagada.

## 10. Execução manual do backend e frontend

Quando a validação precisar executar a aplicação Python diretamente, suba somente o banco:

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
docker compose up -d mongo
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Documentação interativa: <http://127.0.0.1:8000/docs>.

Para servir o frontend sem etapa de build, em outro terminal execute:

```bash
.venv/Scripts/python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Depois abra <http://127.0.0.1:5500>. A origem `http://127.0.0.1:5500` já está incluída na configuração CORS de exemplo.

Os endpoints de usuários estão em `/api/usuarios`, os itens em `/api/itens` e login/logout em `/api/auth`. Os contratos estão documentados em [docs/http-api.md](docs/http-api.md).

## 11. Testes e cobertura

```bash
.venv/Scripts/python.exe -m pytest
```

A suíte da v2.0 aprovou **170 testes**, sendo 24 contra MongoDB real em replica set, além do Selenium que percorre as nove telas do frontend. Os testes de runtime só rodam quando `INTERESSES_TEST_MONGO_URI` aponta para um replica set; sem a variável, são ignorados em vez de falharem. O snapshot `docs/openapi.json` é comparado com o documento gerado pelo runtime.

Para reproduzir o fechamento em stack isolada:

```bash
# 1. suba a stack com portas e volume próprios (não use os da demonstração)
MONGO_DATA_VOLUME=recicla_v2_fechamento_mongo_data MONGO_PORT=27119 \
BACKEND_PORT=8029 FRONTEND_PORT=8109 \
docker compose --env-file .env.example --project-name recicla_fechamento up -d --build --wait

# 2. rode as três jornadas pela interface; o script audita datas e limpa o que criou
JORNADAS_MONGO_URI="<uri do replica set com directConnection=true>" \
JORNADAS_FRONTEND_URL=http://127.0.0.1:8109 JORNADAS_API_URL=http://127.0.0.1:8029 \
python scripts/validar_jornadas_v2.py
```

O resultado da execução está em [docs/verificacao-etapa8.md](docs/verificacao-etapa8.md).

## 12. Limites atuais

Os indicadores somam a plataforma inteira, sem recorte por conta ou cidade, e essa escolha está documentada no contrato. A edição de ponto de coleta existe apenas na API: a tela cadastra e exclui, mas não sobrescreve complemento nem categorias de um ponto existente. Da v2.1, apenas a conta única de pessoa (Etapa 9) está implementada; o restante permanece documental. Bancos criados na v2.0 são normalizados por `scripts/migrar_papeis_v2_1.py`, que simula por padrão e só altera com `--aplicar`. A autenticação usa sessão em memória, adequada ao escopo acadêmico e não a uma implantação com múltiplas instâncias.

> Projeto iniciado a partir do **template fornecido pelo professor Munif Gebara Júnior** e adaptado para Python conforme a proposta da AEP.
