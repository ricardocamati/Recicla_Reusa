# Verificação — Etapa 5: fluxos de doação, descarte e revenda

## Escopo entregue

Conclusão dos três fluxos sobre o `PUT /api/itens/{id}` já existente:

- **Doação:** `reservado → doado` só a partir de interesse aceito. O beneficiário é gravado em `beneficiario_id` a partir do interessado do aceite, nunca do corpo da requisição.
- **Descarte:** `disponivel → encaminhado` exige ponto existente que aceite a categoria; o ponto fica registrado em `ponto_coleta_id` e não pode ser trocado. `encaminhado → coletado` mantém a referência.
- **Revenda:** `disponivel → em_avaliacao → recondicionado → vendido`. A avaliação pode ser registrada como `observacao` do evento e a conclusão exige `comprador_id` de outra pessoa cadastrada; o `valor` continua sendo o campo do item, obrigatório e não negativo na revenda.
- Destino imutável depois que o item sai de `disponivel`; item concluído não reabre nem troca de destino.
- Referências protegidas: excluir ponto ainda usado por item retorna `409`; excluir pessoa que seja proprietária, beneficiária ou compradora de item também.
- Item com fluxo iniciado não pode ser excluído, para não apagar histórico nem liberar as referências que protegem beneficiário, comprador e ponto.

Indicadores, notificações e telas continuam nas etapas seguintes do [TODO](../TODO.md).

## Resultados executados

- Suíte completa com integração habilitada: **154 testes passaram**, sem casos ignorados. Um aviso de depreciação do `BlockingPortal` vem do TestClient/Starlette.
- Destes, **14 executam contra MongoDB real** (replica set `rs0`, banco exclusivo por UUID): 10 da etapa de interesses e 4 desta etapa.
- `tests/test_fluxos_runtime.py` percorre os três fluxos completos pela API: doação com aceite e beneficiário, descarte com ponto compatível e incompatível, revenda com avaliação, comprador e segunda conclusão recusada, além dos bloqueios de exclusão.
- `tests/test_fluxos_v2.py` cobre as regras com dublês: campo de fluxo em destino errado, referência já fixada, comprador ausente/desconhecido/próprio dono, operador como comprador, doação sem aceite, categoria recategorizada no mesmo `PUT` do encaminhamento, recusa de mudar destino e iniciar fluxo na mesma atualização, correção de destino antes do fluxo e exclusão bloqueada depois de iniciado.
- `tests/test_mongo_item_repository.py` garante que as referências são persistidas como `ObjectId` e que documentos antigos, sem os campos novos, são lidos com `None`.
- Stack Docker reconstruída e saudável (MongoDB, backend e frontend). Smoke HTTP executou os três fluxos no backend real: doação com beneficiário do aceite, descarte com ponto fixado e revenda com comprador. As fixtures foram removidas por identificador e a releitura confirmou zero usuários, itens, pontos e interesses no banco da stack de teste.

## Atomicidade e limites

Item e histórico vivem no **mesmo documento**; cada transição é uma única gravação com filtro por `_id` e status anterior (CAS). Uma transição recusada não altera o documento, verificado no teste de doação sem aceite e na segunda conclusão da revenda. Não há escrita em outra coleção nesta etapa, portanto não existe transação multi-documento a demonstrar aqui; os indicadores serão calculados na Etapa 7 e as notificações têm transação própria na Etapa 6.

O modelo de pontos de coleta não possui campo de ativação: "ponto ativo" significa ponto cadastrado, e a compatibilidade verificada é a de categoria. As verificações de referência na exclusão são sequenciais; não são apresentadas como serialização global entre exclusão e criação concorrente.

## Reproduzir

```bash
python -m pytest -q --no-cov -o addopts= --tb=short
```

Com uma instância de testes em replica set e `INTERESSES_TEST_MONGO_URI` configurada, os 14 casos de integração executam; sem a variável, eles são ignorados por segurança. O guia de infraestrutura está em [docker/mongo/README.md](../docker/mongo/README.md).

Nenhum dado de demonstração foi usado ou alterado: os testes criam e removem apenas o próprio banco, identificado por UUID.
