# Artefatos do projeto

Esta pasta separa formalmente a especificação da **primeira entrega (v1.0)**, já publicada, da evolução planejada para a **segunda entrega (v2.0)** e da proposta de revisão de negócio e usabilidade (**v2.1**). A separação evita apresentar funcionalidades futuras como se já estivessem implementadas.

## Organização

```text
artefatos/
├── v1.0/              primeira entrega: meta e base atual
├── v2.0/              segunda entrega: escopo planejado
├── v2.1/              proposta de revisão de negócio e usabilidade
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
- base atual de usuários e itens validada com MongoDB 7.0 real via Docker Compose; provisionamento operacional controlado; frontend separado validado em navegador; backend e frontend também executáveis no Compose integrado.

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

> A v2.0 é uma especificação planejada. O código atual implementa a base de usuários, o CRUD de itens e o frontend simples da v1.0; interesses, notificações e fluxos completos continuam fora da implementação.

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

> A v2.1 é proposta: não há implementação, testes executados nem evidências próprias. Ela revisa pontos da v2.0 antes de a segunda entrega ser implementada.

## Materiais locais

A pasta [nao_versionados/](nao_versionados/) guarda checklist e extrações auxiliares que não devem ser enviados ao Git.
