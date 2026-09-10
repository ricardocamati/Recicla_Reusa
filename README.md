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

A primeira entrega conclui os fluxos de usuários e itens nas coleções MongoDB `usuarios` e `itens`: cadastro público de doadores e beneficiários, endereço como subdocumento, auditoria temporal em UTC, e-mail normalizado com índice único, sessões simples em cookie HttpOnly, catálogo filtrável, autorização por proprietário e frontend simples separado em HTML, CSS e JavaScript.

Itens referenciam o usuário por `proprietario_id` e não duplicam o endereço. O histórico de ciclo de vida, interesses e pontos de coleta permanecem na evolução da v2.0; a implementação atual mantém a evolução visível no histórico de commits.

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
  "proprietario_id": "...",
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
- Pytest, pytest-cov, mongomock e Selenium;
- HTML, CSS e JavaScript no frontend simples da v1.0;
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
app/            backend Python
frontend/       cliente web simples da v1.0; Dockerfile com `http.server`
 tests/         testes automatizados
docs/           arquitetura, decisões e contratos
compose.yaml    MongoDB, backend FastAPI e frontend Python
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

A suíte deve manter cobertura mínima de **70%**, conforme a AEP. A execução validada da entrega aprovou **75 testes**, com **94,15%** de cobertura incluindo `app/main.py`. Os testes unitários do repositório usam `mongomock`; a aplicação utiliza PyMongo e MongoDB em execução normal. O teste Selenium usa Chrome headless e servidores locais isolados para verificar as seis telas do frontend. Para reproduzir a integração Docker/MongoDB, use os scripts documentados em [evidências](artefatos/v1.0/evidencias/).

## 12. Limites atuais

O frontend simples da v1.0 está implementado com cadastro, login, perfil, catálogo, filtros e gestão de itens próprios. Interesses, pontos de coleta detalhados, notificações e fluxos completos permanecem na especificação da v2.0, fora do `TODO.md` de implementação atual.

> Projeto iniciado a partir do **template fornecido pelo professor Munif Gebara Júnior** e adaptado para Python conforme a proposta da AEP.
