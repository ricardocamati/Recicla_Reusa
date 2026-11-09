# Recicla/Reusa — Plataforma de Doação, Descarte e Reaproveitamento de Eletrônicos

PoC acadêmica para ofertas de **doação e venda/reaproveitamento** de eletrônicos e consulta pública de **locais de descarte**, sem exigir cadastro de equipamento para consultar o diretório.

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

A primeira entrega está preservada na tag `v1.0`. A segunda entrega evoluiu nas Etapas 1 a 8 (marco v2.0, commit `71e8dfa`, PR #18) e recebeu a revisão de negócio e usabilidade v2.1 nas Etapas 9 a 20. O marco final da segunda entrega é o commit da `main` resultante do merge do PR #27 (Etapas 16 a 20) e da correção de leitura de ofertas legadas do PR #29, validado com a suíte completa. Registro completo em [artefatos/v2.1/registro_entrega.md](artefatos/v2.1/registro_entrega.md).

A aplicação permite cadastro de pessoa, publicação de ofertas de doação/venda, interesse, reserva reversível, combinação aceita e entrega bilateral. O descarte usa o diretório público de locais. O processo anterior por equipamento é removido, sem entregas previstas, recebimento, indicação de destinação ou aba histórica de descarte. Autenticação usa sessão em cookie HttpOnly; permissões são verificadas no backend por identidade e propriedade.

### Modelo em uso

São cinco coleções: `usuarios`, `itens`, `interesses`, `pontos_coleta` e `notificacoes`. Usuários e pontos têm endereço aninhado; itens contêm `especificacoes` e `historico`; interesses contêm combinação de entrega e histórico. IDs BSON estabelecem os relacionamentos, sem copiar o endereço privado do proprietário para o item.

No contrato executável, novos itens e edições de ofertas usam `destino` (`doacao` ou `revenda`), `status` e `valor`. Doação/venda seguem `disponivel → reservado → aguardando_confirmacao → concluido`, com rascunhos e arquivamento na gestão do autor. Escrita e leitura de itens usam somente doação/revenda; estados e campos exclusivos do descarte são removidos.

A documentação da revisão está em [artefatos/v2.1/](artefatos/v2.1/README.md); o [modelo de dados](artefatos/v2.1/modelo_dados.md) distingue a estrutura implementada do desenho original. Contratos atuais: [HTTP](docs/http-api.md) e [OpenAPI](docs/openapi.md). O [TODO](TODO.md) registra as etapas e o histórico de tarefas, não substitui os testes nem comprova a entrega externa.

## 6. Stack utilizada

A Etapa 16 acrescenta leitura pública de locais ativos em `GET /api/pontos-coleta` e `GET /api/pontos-coleta/{id}`, sem login nem cadastro de equipamento. As respostas expõem somente dados do local; a gestão continua autenticada com `escopo=meus`. A Etapa 17 acrescenta a tela pública [Onde descartar](frontend/onde-descartar.html), com filtros, paginação, detalhe e cópia de endereço, acessível pela página inicial e pela navegação autenticada. Ela não cria registros de descarte. A Etapa 18 removeu o fluxo antigo por completo, sem histórico de descarte ou adaptadores, e entregou “Meus locais”. A Etapa 19 separa resultados de ofertas confirmadas da contagem cadastral de locais e garante que consultar o diretório não produza avisos nem resultados de equipamentos. Detalhes e política de preservação em [docs/http-api.md](docs/http-api.md) e nos [artefatos v2.1](artefatos/v2.1/README.md).

- Python 3.11+;
- FastAPI e Uvicorn;
- MongoDB e PyMongo;
- Pydantic;
- Pytest, pytest-cov, mongomock e Selenium;
- HTML, CSS e JavaScript no frontend, sem build;
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
docs/           arquitetura, decisões e contratos HTTP/OpenAPI
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

### 9.1 Subir com os dados de demonstração

O comando acima inicia a aplicação **sem contas nem ofertas**: o banco nasce vazio e o login
retorna `401`. Para percorrer as jornadas com dados fictícios, execute o povoamento uma vez,
depois que os serviços estiverem de pé.

O script roda no host, com as dependências de desenvolvimento instaladas (`pip install -e '.[dev]'`),
e precisa de duas informações que **não** podem vir do `MONGO_URI` padrão do `.env`:

- `directConnection=true`, porque o replica set é acessado pela porta publicada;
- um `MONGO_DATABASE` igual ao que a API está usando, pois o script confere a identidade das
  contas no banco antes de escrever.

```bash
# 1. Subir a aplicação (banco vazio).
docker compose up -d --build --wait

# 2. Povoar, no host, com as mesmas variáveis que o Compose usa.
set -a; . ./.env; set +a          # carrega porta, usuário e banco do .env
MONGO_URI="mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@127.0.0.1:${MONGO_PORT}/${MONGO_DATABASE}?authSource=admin&replicaSet=rs0&directConnection=true" \
MONGO_DATABASE="${MONGO_DATABASE}" \
DEMO_SENHA="<senha fictícia com ao menos 8 caracteres>" \
  .venv/Scripts/python.exe scripts/povoar_demonstracao.py --aplicar --ampliar \
    --api-url http://127.0.0.1:${BACKEND_PORT:-8000} \
    --origin http://127.0.0.1:${FRONTEND_PORT:-8080}
```

A saída termina em `Demonstração confirmada` e lista as contas criadas. A partir daí
`ana.demo@example.test` autentica com a senha informada em `DEMO_SENHA`.

O povoamento é **aditivo e reexecutável**: não apaga banco, não redefine senhas e não duplica
registros quando a carga anterior está intacta. Para apenas conferir o que seria criado, rode o
script sem `--aplicar`. Para remover tudo, `docker compose down -v` apaga o volume do MongoDB.

> O `MONGO_URI` do `.env` serve ao backend dentro da rede Docker e aponta para o host `mongo`;
> ele não funciona para o script rodando no host. Use a forma acima.

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
.venv/Scripts/python.exe frontend/servidor.py 5500 --bind 127.0.0.1 --directory frontend
```

Depois abra <http://127.0.0.1:5500>. A origem `http://127.0.0.1:5500` já está incluída na configuração CORS de exemplo.

O servidor estático acrescenta uma versão derivada do conteúdo às referências locais de páginas, estilos e módulos JavaScript, sem editar os arquivos-fonte, e envia `Cache-Control: no-store`. Isso evita misturar HTML e módulos de implantações diferentes. Uma aba que já estava aberta antes dessa proteção precisa navegar uma vez para uma URL nova da página, como `catalogo.html?atualizacao=atual`; o servidor não consegue substituir sozinho um documento já retido pelo navegador.

Os endpoints de usuários estão em `/api/usuarios`, os itens em `/api/itens` e login/logout em `/api/auth`. Os contratos estão documentados em [docs/http-api.md](docs/http-api.md).

## 11. Testes e cobertura

```bash
.venv/Scripts/python.exe -m pytest
```

O comando padrão mede cobertura sobre `app` e exige o mínimo configurado em `pyproject.toml` (`--cov-fail-under=70`), de modo que a própria suíte falha se a cobertura ficar abaixo do exigido.

No marco final da segunda entrega, com MongoDB real em replica set e Selenium, a suíte completa foi executada em 09/11/2026: **310 testes coletados, 310 executados, 0 falhas e 0 ignorados**, com **91,56% de cobertura** sobre `app`. Medições anteriores (201, 216 e 309 testes) pertencem a marcos antigos e não valem para o commit desta entrega. O arquivo `.coverage` é local e ignorado pelo Git; a evidência reproduzível é o comando acima, reexecutado no marco informado. O commit exato do marco está em [artefatos/v2.1/registro_entrega.md](artefatos/v2.1/registro_entrega.md).

Os testes de runtime exigem `INTERESSES_TEST_MONGO_URI` apontando para MongoDB em replica set; sem a variável, esses cenários são ignorados. Configure uma instância de teste separada, nunca o banco de demonstração. Para rodar os testes com integração e medição, usando a URI de teste autorizada:

```bash
INTERESSES_TEST_MONGO_URI="<uri do replica set de teste com directConnection=true>" \
python -m pytest
```

Testes relevantes estão em [tests/](tests/), incluindo [fluxos](tests/test_fluxos_runtime.py), [interesses](tests/test_interesses_runtime.py), [diretório](tests/test_etapa18_api.py), [notificações](tests/test_notificacoes_runtime.py) e [frontend](tests/test_selenium_frontend.py). O [teste OpenAPI](tests/test_openapi_runtime.py) compara o snapshot com o contrato gerado da aplicação. A evolução e os resultados registrados nas revisões estão nos commits e PRs de cada etapa; não há relatórios de verificação separados em `docs/`.

Para reproduzir o fechamento em stack isolada:

```bash
# 1. suba a stack com portas e volume próprios (não use os da demonstração)
MONGO_DATA_VOLUME=recicla_v2_fechamento_mongo_data MONGO_PORT=27119 \
BACKEND_PORT=8029 FRONTEND_PORT=8109 \
docker compose --env-file .env.example --project-name recicla_fechamento up -d --build --wait

# 2. rode as três jornadas (doação, venda e consulta anônima do diretório); o script audita datas, confere indicadores e limpa o que criou
JORNADAS_MONGO_URI="<uri do replica set com directConnection=true>" \
JORNADAS_FRONTEND_URL=http://127.0.0.1:8109 JORNADAS_API_URL=http://127.0.0.1:8029 \
python scripts/validar_jornadas_v2.py
```

A Etapa 20 executou as três jornadas revisadas em stack e volume próprios, conferiu indicadores antes/depois da consulta pública e removeu somente as fixtures criadas. Para validar uma alteração, execute novamente os comandos; o resultado anterior não aprova automaticamente um checkout diferente.

## 12. Dados fictícios de demonstração

O script [scripts/povoar_demonstracao.py](scripts/povoar_demonstracao.py) mantém a carga básica e o modo aditivo `--ampliar`, com contas, ofertas variadas e locais fictícios em Maringá, Sarandi e Paiçandu. O manifesto e as chamadas do processo antigo de descarte foram removidos, sem migração ou limpeza de bancos: cenários de descarte não são criados nem avançados. Cargas novas exercitam doação/venda e cadastro de locais. As relações de ofertas são criadas pela API; apenas a conta operacional é provisionada localmente pelo serviço administrativo.

```bash
# Apenas descreve a carga; não conecta ao banco nem altera registros.
python scripts/povoar_demonstracao.py

# Com a API v2.1 já apontando para o MESMO banco de demonstração:
MONGO_URI="<uri local do replica set com directConnection=true>" \
MONGO_DATABASE=recicla_reusa_demo_v21 DEMO_SENHA="<senha fictícia escolhida>" \
python scripts/povoar_demonstracao.py --aplicar --ampliar \
  --api-url http://127.0.0.1:8000 --origin http://127.0.0.1:8080
```

Instale as dependências de desenvolvimento para executar o script no host. A senha vem de `DEMO_SENHA`; não existe senha padrão no código. As contas básicas são `ana.demo@example.test`, `bruno.demo@example.test`, `carla.demo@example.test` e `operador.demo@example.test`; `--ampliar` acrescenta Diego, Elisa, Felipe e Gabriela com e-mails no formato `<nome>.demo@example.test`. A ampliação preserva os registros da carga básica e as contas existentes. O script confirma o login e o perfil antes de usar cada conta, percorre todas as páginas das listagens e relê os registros criados. A reexecução sobre a carga intacta não duplica dados. Não apaga banco, não redefine senhas e não reinicia ciclos já alterados manualmente; identidades ambíguas ou estados divergentes interrompem a carga, que pode permanecer parcial para inspeção.

Para esta demonstração local, a aplicação está usando `recicla_reusa_demo_v21`, separado de `recicla_reusa`. Confirme a configuração efetiva antes de recriar os serviços: o Compose usa `MONGO_DATABASE` para escolher o banco. Não use `down -v` para alternar entre eles. O acesso local preparado fica em `artefatos/nao_versionados/acesso_demonstracao.json`, ignorado pelo Git; esse arquivo não faz parte do pacote versionado.

> Projeto iniciado a partir do **template fornecido pelo professor Munif Gebara Júnior** e adaptado para Python conforme a proposta da AEP.
