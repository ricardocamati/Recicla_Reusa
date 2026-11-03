# Verificação — Etapa 4: interesses

## Escopo entregue

API de criação, consulta privada, listagem de próprios/recebidos e decisão de interesses. O interessado é derivado da sessão. O par item/interessado é único; doação e revenda têm seleção exclusiva. O aceite da doação reserva o item com histórico na mesma transação. O cancelamento do aceite libera a seleção apenas antes de uma conclusão impeditiva.

As telas de interesses, notificações e os fluxos completos de conclusão pertencem às etapas seguintes do [TODO](../TODO.md).

## Resultados executados

- Suíte completa: **130 testes passaram**, sem casos ignorados nessa execução. Houve um aviso de depreciação do `BlockingPortal` utilizado pelo TestClient/Starlette.
- `compileall` sobre `app` e `tests` e `git diff --check`: sem erros.
- A suíte também passou com a medição configurada no projeto. O relatório XML ficou em `artefatos/nao_versionados/interesses-cobertura.xml`, ignorado pelo Git.
- MongoDB real: replica set `rs0` de um nó, projeto Compose isolado `recicla_interesses_verificacao`, porta de banco `27109`, volume próprio `recicla_interesses_verificacao_mongo_data`.
- Backend e frontend construídos e iniciados por Compose; MongoDB, backend e frontend alcançaram `healthy`.
- Verificação HTTP contra o backend Docker na porta `8019`: duas manifestações, dois aceites concorrentes com resultados `200` e `409`, cancelamento do vencedor liberando o item e preservando os três eventos do histórico (cadastro, reserva, liberação).
- As fixtures desse smoke foram removidas por identificadores e identidade conferidos. A releitura confirmou zero usuários, itens e interesses no banco dessa stack de teste. Nenhum banco de demonstração foi utilizado.

## Testes versionados

- `tests/test_interesses_v2.py`: regras do serviço, criação, unicidade, papéis e autenticação da API, com dublê explícito.
- `tests/test_interesse_repository.py`: repositório real, reserva/liberação e seleção exclusiva na revenda.
- `tests/test_interesses_runtime.py`: fábrica e API com MongoDB real, coleções com nomes personalizados, privacidade antes da paginação, concorrência de cadastro e aceite, seleção em revenda, edição preservando seleção, cancelamento após conclusão, rejeição de query extra e guardas sequenciais de referências.
- Regressão do aceite com seleção vazia: os dois casos parametrizados (doação e revenda) persistem `interesse_aceito_id: null`, aceitam pela API e conferem o identificador BSON selecionado e o status. O filtro transacional trata campo nulo ou ausente como não selecionado, sem aceitar uma seleção já preenchida.
- Rollback real: uma falha controlada é lançada **depois** das escritas de item e interesse, dentro da transação. Os dois documentos são relidos e comparados integralmente aos originais; não fica reserva, evento de histórico ou mudança de interesse parcial.
- `tests/test_mongo_item_repository.py`: não expor campos internos ao modelo público e não apagar a seleção na edição comum.
- `tests/test_interesses_infra.py`: configuração de coleção e pré-requisitos de replica set e healthcheck.

Os testes de integração criam bancos exclusivos com UUID, recusam reaproveitar um banco preexistente e removem somente o banco que criaram.

## Reproduzir a suíte

Instale as dependências de desenvolvimento e prepare uma instância **de testes** do MongoDB com replica set. Configure `INTERESSES_TEST_MONGO_URI` com a URI autenticada dessa instância. Quando o teste roda no host e o membro é anunciado como `mongo:27017`, a URI deve usar a porta publicada e `directConnection=true`, conforme o [guia de infraestrutura](../docker/mongo/README.md).

```bash
python -m pytest -q --no-cov -o addopts= --tb=short
```

Para executar somente a integração de interesses:

```bash
python -m pytest tests/test_interesses_runtime.py tests/test_interesse_repository.py -q --no-cov -o addopts= --tb=short
```

Sem a variável de integração, esses casos são ignorados por segurança. Uma execução com esses casos ignorados não comprova transações ou concorrência no MongoDB real.

## Limites da evidência

A disputa executada é uma observação de concorrência, não prova de todas as intercalações possíveis. A atomicidade de aceite/cancelamento usa transações MongoDB; as verificações de existência e de exclusão por referência não são apresentadas como serialização global entre todas as operações do sistema. Sem suporte transacional, interesses falham com erro sanitizado, sem fallback de escrita parcial.

O ambiente de teste é separado dos dados de demonstração. Não é necessário apagar volume existente para habilitar replica set; veja as instruções conservadoras do guia de infraestrutura.
