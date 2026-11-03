# Verificação — Etapa 8 (fechamento da v2.0)

Execução de **03/11/2026**, em stack Docker isolada do ambiente de demonstração:

```text
projeto Compose   recicla_fechamento
backend           127.0.0.1:8029
frontend          127.0.0.1:8109
MongoDB           127.0.0.1:27119 (rs0)
volume            recicla_v2_fechamento_mongo_data
```

O banco da jornada estava vazio no início e recebeu apenas dados sintéticos com o prefixo `jornada-`.

## Suíte completa

```text
170 passed, 1 warning in 112.92s
```

Os 24 testes de runtime usaram o MongoDB real da stack isolada (`INTERESSES_TEST_MONGO_URI`), sem tocar no banco de demonstração. O aviso é a depreciação de `BlockingPortal` no `TestClient` do Starlette, sem relação com o projeto.

## Jornadas pela interface

Executadas por `scripts/validar_jornadas_v2.py`, com Chrome headless apontando para o frontend da stack e `window.RECICLA_API_BASE` para o backend isolado.

```text
jornada_doacao=ok
jornada_descarte=ok
jornada_revenda=ok
referencias_persistidas=ok
```

1. **Doação** — a doadora se cadastra, entra e publica um notebook para doação; a beneficiária se cadastra, encontra o item no catálogo e registra interesse; a doadora aceita o interesse em *Interesses* e conclui o item como doado em *Meus itens*; a beneficiária vê o aviso "passou para doado".
2. **Descarte** — o operador do ponto entra, cadastra um ponto que aceita notebook e sai; a doadora publica um monitor para descarte, encaminha ao ponto compatível e marca a coleta.
3. **Revenda** — a doadora publica um tablet com valor, inicia a avaliação, marca como recondicionado e registra a venda escolhendo o comprador.

Conferência direta no banco depois das jornadas:

- doação `doado` com `beneficiario_id` igual ao `_id` da beneficiária;
- descarte `coletado` com `ponto_coleta_id` preenchido;
- revenda `vendido` com `comprador_id` preenchido;
- notificação emitida para o item concluído.

Para as jornadas serem executáveis pelo operador, o fechamento acrescentou duas ações que faltavam na interface: o botão **Tenho interesse** no catálogo (somente para itens de doação ou revenda, disponíveis e de outra pessoa) e a barra de **próxima ação do fluxo** em *Meus itens*, com seleção de ponto compatível no descarte e de comprador na revenda.

## Auditoria temporal

```text
auditoria_datas=ok; usuarios=3 itens=3 pontos_coleta=1 interesses=1 notificacoes=2
```

Para cada documento das cinco coleções: `data_adicao` e `data_modificacao` presentes, com fuso UTC, microssegundos zerados (precisão de milissegundos) e `data_modificacao >= data_adicao`.

## Limpeza seletiva

```text
limpeza=ok; removidos usuarios=3 itens=3 pontos=1
```

A limpeza remove apenas documentos cujos e-mails, títulos e nomes começam com `jornada-`, na ordem notificações → interesses → itens → pontos → usuários, e confere contagem zero ao final. A execução seguinte recomeça do mesmo prefixo, sem apagar dados de demonstração.

## OpenAPI

`tests/test_openapi_runtime.py` compara `docs/openapi.json` com o documento gerado pelo runtime e passou (2 testes), mantendo as diferenças de prosa registradas em [openapi.md](openapi.md).

## Regressões de frontend

`tests/test_frontend.py` ganhou duas verificações: o catálogo só oferece interesse a itens de outra pessoa, disponíveis e que não sejam descarte; e a tela de itens expõe exatamente as seis próximas ações do fluxo, com `ponto_coleta_id` e `comprador_id`.

## Pendências conscientes

- A tag `v2.0` é criada após o merge do PR de fechamento; nada é publicado sem autorização.
- Indicadores continuam sendo totais da plataforma, como documentado na Etapa 7.
- A edição de ponto de coleta segue disponível apenas pela API: o formulário da tela não sobrescreve `complemento` nem categorias de um ponto existente.
