# Artefatos do projeto

Esta pasta preserva a **primeira entrega (v1.0)**, o marco intermediário da **segunda entrega (v2.0)** e a revisão de negócio e usabilidade **v2.1**, implementada nas Etapas 9 a 15. Os documentos históricos não substituem a descrição do checkout atual no [README](../README.md) e nos [contratos HTTP](../docs/http-api.md).

## Organização

```text
artefatos/
├── v1.0/              primeira entrega: marco preservado
├── v2.0/              segunda entrega: marco intermediário
├── v2.1/              revisão de negócio e usabilidade
└── nao_versionados/   materiais locais ignorados pelo Git
```

## Versão 1.0 — Primeira entrega

[Índice da v1.0](v1.0/)

- coleções `usuarios` e `itens`;
- CRUD de usuários e itens;
- campos de endereço planos no documento de usuário;
- `data_adicao` e `data_modificacao` nas duas coleções;
- autenticação por sessão simples e autorização básica por perfil e propriedade;
- frontend simples em HTML, CSS e JavaScript;
- testes automatizados e cobertura registrada;
- base da primeira entrega validada com MongoDB 7.0 real via Docker Compose; provisionamento operacional controlado; frontend separado validado em navegador; backend e frontend também executáveis no Compose integrado.

Documentos: [requisitos](v1.0/requisitos.md) · [regras de negócio](v1.0/regras_de_negocio.md) · [modelo de dados](v1.0/modelo_dados.md) · [casos de teste](v1.0/casos_de_teste.md) · [matriz](v1.0/matriz_rastreabilidade.md) · [registro da entrega](v1.0/registro_entrega.md) · [evidências](v1.0/evidencias/)

## Versão 2.0 — Segunda entrega

[Índice da v2.0](v2.0/)

- múltiplas coleções relacionadas: `usuarios`, `itens`, `interesses`, `pontos_coleta` e `notificacoes`;
- endereço como subdocumento de usuários e pontos de coleta;
- `data_adicao` e `data_modificacao` em todas as coleções;
- itens relacionados ao proprietário, sem duplicar seu endereço;
- `especificacoes` e `historico` aninhados em itens;
- fluxos de doação, descarte e reaproveitamento/revenda;
- notificações internas para avisar usuários sobre itens de seu interesse.

Documentos: [requisitos](v2.0/requisitos.md) · [regras de negócio](v2.0/regras_de_negocio.md) · [modelo de dados](v2.0/modelo_dados.md) · [casos de teste](v2.0/casos_de_teste.md) · [matriz](v2.0/matriz_rastreabilidade.md)

> A v2.0 foi implementada nas Etapas 1 a 8, com fechamento em `71e8dfa` (PR #18). Sua documentação é histórica: a v2.1 substitui perfis, transições e contratos indicados no índice de cada versão.

## Versão 2.1 — Revisão de negócio e usabilidade

[Índice da v2.1](v2.1/)

- conta única de pessoa para oferecer e receber/comprar, com operador separado;
- catálogo apenas de ofertas (doação e venda), sem descarte;
- condição física separada da situação comercial e venda direta de usado;
- reserva, combinação da entrega e confirmação bilateral;
- descarte por entrega ao ponto ou por indicação de lugar feita pelo autor;
- cancelamento, troca de ponto, indisponibilidade e não comparecimento com saída;
- avisos acionáveis e indicadores que não confundem recebimento com reciclagem.

Documentos: [requisitos](v2.1/requisitos.md) · [regras de negócio](v2.1/regras_de_negocio.md) · [jornadas e frontend](v2.1/jornadas_frontend.md) · [modelo de dados](v2.1/modelo_dados.md) · [contratos HTTP](v2.1/contratos_http.md) · [casos de teste](v2.1/casos_de_teste.md) · [matriz](v2.1/matriz_rastreabilidade.md)

> A v2.1 tem implementação e testes próprios. As diferenças entre o desenho original e o código estão nos contratos e no modelo desta versão; a existência de uma etapa concluída não comprova todos os critérios escritos. Medição final de cobertura, integração e vídeo são conferências separadas.

## Materiais locais

A pasta [nao_versionados/](nao_versionados/) guarda checklist e extrações auxiliares que não devem ser enviados ao Git.
