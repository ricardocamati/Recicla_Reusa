# Artefatos da versão 2.0 — Segunda entrega

A versão 2.0 registra o marco intermediário da evolução da PoC, implementado nas Etapas 1 a 8. Ela é cumulativa: mantém usuários e itens da versão 1.0 e acrescenta interesses, pontos de coleta, notificações e fluxos completos.

## Escopo do marco v2.0

- evolução das coleções `usuarios` e `itens` iniciadas na v1.0;
- coleção `interesses`;
- coleção `pontos_coleta`;
- coleção `notificacoes` para avisar usuários sobre itens de seu interesse;
- relacionamentos por identificadores;
- `especificacoes` e `historico` como estruturas aninhadas em itens;
- fluxos de doação, descarte e reaproveitamento/revenda;
- indicadores de impacto;
- testes e cobertura automatizados;

## Documentos

- [requisitos.md](requisitos.md)
- [regras_de_negocio.md](regras_de_negocio.md)
- [modelo_dados.md](modelo_dados.md)
- [casos_de_teste.md](casos_de_teste.md)
- [matriz_rastreabilidade.md](matriz_rastreabilidade.md)

## Limite atual

Os documentos desta pasta preservam o marco v2.0, fechado em `71e8dfa` (PR #18), sem tag v2.0. Os caminhos e estados aqui registrados não devem ser tratados como contrato do checkout atual: a v2.1 altera parte desse comportamento. Consulte o [README atual](../../README.md) e os [contratos HTTP](../../docs/http-api.md).

## Relação com a v2.1

A [v2.1](../v2.1/README.md), implementada nas Etapas 9 a 15, **substitui** estes pontos:

- perfis públicos de doador e beneficiário passam a ser uma conta única de pessoa;
- o catálogo deixa de exibir itens de descarte;
- a revenda de usado deixa de exigir avaliação ou reparo obrigatório;
- a conclusão deixa de ser unilateral: reserva, combinação e confirmação bilateral;
- o descarte pode terminar por entrega ao ponto ou por indicação de lugar feita pelo autor.

Esta pasta não foi reescrita como se a v2.1 sempre tivesse existido: mantém os requisitos e cenários do marco anterior. A estrutura e as operações atuais estão descritas na documentação v2.1, com as divergências do desenho original explicitadas.
