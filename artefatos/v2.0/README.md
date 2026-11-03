# Artefatos da versão 2.0 — Segunda entrega

A versão 2.0 descreve a evolução final planejada da PoC. Ela é cumulativa: mantém usuários e itens da versão 1.0 e acrescenta interesses, pontos de coleta, notificações e fluxos completos.

## Escopo planejado

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

Os documentos desta pasta são a especificação da segunda entrega. Essas funcionalidades ainda não estão implementadas no código atual e não devem ser apresentadas como concluídas.

## Relação com a v2.1

A [v2.1](../v2.1/README.md) é uma proposta aceita de revisão de negócio e usabilidade que **altera** estes pontos antes da implementação:

- perfis públicos de doador e beneficiário passam a ser uma conta única de pessoa;
- o catálogo deixa de exibir itens de descarte;
- a revenda de usado deixa de exigir avaliação ou reparo obrigatório;
- a conclusão deixa de ser unilateral: reserva, combinação e confirmação bilateral;
- o descarte pode terminar por entrega ao ponto ou por indicação de lugar feita pelo autor.

Ao implementar a segunda entrega, estas decisões devem ser consideradas para não construir comportamento que a v2.1 já substitui. A v2.1 não está implementada e não altera o escopo desta pasta.
