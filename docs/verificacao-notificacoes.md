# Verificação — Etapa 6: notificações

## Escopo entregue

- Coleção `notificacoes` com índice único por `evento_id`, destinatário e item, além do índice de consulta por destinatário e data.
- Emissão na **mesma transação** da mudança que origina o aviso:
  - decisão de interesse (`aceito` e `recusado` para o interessado; `cancelado` para o proprietário);
  - transição de status do item para quem tem interesse pendente ou aceito, com tipo `item_concluido` quando o destino é `doado`, `coletado` ou `vendido`.
- Caixa de entrada `GET /api/notificacoes` restrita ao destinatário, com filtro `lida` e paginação, e `PATCH /api/notificacoes/{id}` para marcar leitura.
- Gravação idempotente por `upsert` ancorado no índice único: repetir o mesmo evento não cria outro aviso.
- Marcar como lida preserva `data_adicao`, registra `data_leitura` e atualiza `data_modificacao`.

## Resultados executados

- Suíte completa com integração habilitada: **163 testes passaram**, sem casos ignorados. Um aviso de depreciação do `BlockingPortal` vem do TestClient/Starlette.
- **23 testes executam contra MongoDB real** (replica set `rs0`, banco exclusivo por UUID): 10 de interesses, 4 de fluxos e 9 desta etapa.
- `tests/test_notificacoes_runtime.py` cobre:
  - aceite e recusa notificando o interessado, com `item_id` correto e `lida: false`;
  - aceite avisando os demais interessados de que o item foi reservado, sem duplicar o aviso do escolhido;
  - cancelamento do interessado notificando o proprietário;
  - mudança de status e conclusão da doação gerando `item_concluido`;
  - listagem apenas do próprio destinatário, `404` para terceiro e para identificador inválido, leitura alterando `lida`, `data_leitura` e `data_modificacao`;
  - repetição do mesmo evento mantendo uma única notificação;
  - usuário sem interesse e o próprio proprietário sem avisos;
  - **rollback**: falha forçada ao registrar o aviso depois da escrita do item desfaz a transição, mantendo o item `disponivel` e a coleção de avisos vazia;
  - rejeição de parâmetro de query desconhecido e de corpo inválido.

## Stack Docker

Backend e frontend reconstruídos e saudáveis. O smoke HTTP no backend real confirmou: aceite gerando `interesse_aceito`, conclusão da doação gerando `item_concluido`, marcação de leitura com `data_leitura`, terceiro recebendo `404` e proprietário sem avisos. As fixtures foram removidas por identificador e a releitura confirmou zero usuários, itens, interesses e notificações no banco da stack de teste.

## Limites

- O `evento_id` das transições de item inclui o instante do servidor; uma mesma transição repetida é bloqueada antes pelo CAS de status, e o índice único cobre o reenvio do mesmo evento.
- A emissão depende do replica set: sem transação, a operação falha em vez de gravar aviso parcial. O Compose já prepara `rs0`.
- A caixa de entrada não tem tela própria nesta etapa; a interface das notificações está na Etapa 7.
- Testes de integração exigem `INTERESSES_TEST_MONGO_URI`; sem a variável, são ignorados por segurança.

## Reproduzir

```bash
python -m pytest -q --no-cov -o addopts= --tb=short
```

Nenhum dado de demonstração foi usado ou alterado: cada caso cria e remove apenas o próprio banco, identificado por UUID.
