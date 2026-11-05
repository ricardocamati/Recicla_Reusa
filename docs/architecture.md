# Arquitetura

## Visão geral

O Recicla/Reusa é uma PoC local com frontend estático, API FastAPI e MongoDB em replica set. Este documento descreve o código após as Etapas 1 a 15; a primeira entrega permanece preservada na tag `v1.0`.

```text
Navegador → frontend HTML/CSS/JavaScript
         → API FastAPI → Service → Repository → MongoDB
                         ↓           ↓
                      Mapper ← Model
                         ↓
                   DTO de resposta
```

## Responsabilidades

- **API (`app/api`)**: rotas, dependências de sessão, validação HTTP e tradução de erros.
- **Schemas (`app/schemas`)**: contratos Pydantic de entrada e resposta; não são os documentos persistidos.
- **Services (`app/services`)**: casos de uso, permissões, propriedade e regras de negócio.
- **Repositories (`app/repositories`)**: consultas, índices, persistência e operações transacionais.
- **Models (`app/models`)**: classes de domínio/persistência, incluindo subdocumentos de endereço, histórico e combinação.
- **Mappers (`app/mappers`)**: projeção para os DTOs, sem expor hash ou endereço privado em consultas de terceiros.
- **Security (`app/security`)**: scrypt e sessão em memória.
- **Frontend (`frontend`)**: páginas HTML separadas e módulos JavaScript por responsabilidade; sem build obrigatório.

Serviços recebem repositórios por injeção. O wiring e a inicialização dos índices ficam em `app/main.py`; os testes usam doubles e MongoDB real conforme a camada.

## Execução integrada

O [Compose](../compose.yaml) reúne MongoDB, backend Uvicorn e frontend servido por [servidor.py](../frontend/servidor.py), baseado em `http.server`, com Mongo Express como ferramenta auxiliar. O servidor estático versiona referências de páginas, CSS e imports JavaScript por conteúdo e não permite armazenar respostas antigas no cache. O MongoDB precisa de replica set para as transações dos fluxos. Inicialização e healthcheck ficam em [docker/mongo/](../docker/mongo/README.md).

O backend usa o hostname `mongo` na rede Docker; o navegador usa a porta publicada da API. CORS e validação de `Origin`/`Referer` permitem apenas as origens configuradas nas mutações com cookie. Comandos, portas padrão e execução manual estão no [README](../README.md).

## Coleções e relações

```text
usuarios ← proprietario_id ─ itens ← item_id ─ interesses → usuario_id → usuarios
   ↑                         ↑
responsavel_id            item_id
   │                         │
pontos_coleta ← ponto_id ─ encaminhamentos → autor_id → usuarios

notificacoes → usuario_id, item_id e interesse_id opcional
```

- `usuarios`: conta `pessoa` ou `ponto_coleta`, endereço aninhado e hash da senha.
- `itens`: proprietário, destino, condição, valor, status, especificações e histórico acumulativo.
- `interesses`: uma relação por item/pessoa, tentativa, histórico, preço selecionado e combinação de entrega.
- `pontos_coleta`: local físico, responsável, endereço público, categorias, horário e situação ativa/inativa.
- `encaminhamentos`: tentativas de entrega, com item, autor, ponto, status, motivo e histórico.
- `notificacoes`: destinatário, evento, item, interesse opcional, link interno e leitura.

IDs relacionais são BSON ObjectId na persistência e strings no JSON. Datas são geradas pelo servidor em UTC; a persistência normaliza a precisão BSON. `data_adicao` é preservada nas atualizações. O [modelo atual](../artefatos/v2.1/modelo_dados.md) distingue essas estruturas do desenho original.

## Identidade e privacidade

O cadastro público cria `pessoa`. A mesma pessoa publica e manifesta interesse em ofertas alheias; proprietário, interessado e comprador são relações, não perfis públicos diferentes. A conta `ponto_coleta` é provisionada localmente e opera seus próprios locais.

A senha é persistida como hash scrypt. O login emite cookie de sessão `HttpOnly`/`SameSite=Lax`; o frontend envia `credentials: "include"`, sem ler o cookie. Sessões em memória não são uma solução para múltiplas instâncias.

Permissões são verificadas no backend. DTOs públicos não retornam hash nem endereço completo do proprietário. `destinacao_informada` é visível somente ao autor. Ocultar botões não constitui autorização.

## Fluxos atuais

| Caminho | Transições principais |
|---|---|
| Oferta de doação/venda | `rascunho → disponivel → reservado → aguardando_confirmacao → concluido` |
| Liberação antes da entrega | `reservado → disponivel` |
| Descarte em ponto | `aguardando_ponto → entrega_prevista → recebido` |
| Cancelamento ou impossibilidade | `entrega_prevista → aguardando_ponto` |
| Lugar indicado pelo autor | `aguardando_ponto → destinacao_informada → aguardando_ponto` (ao desfazer) |

Reserva nasce da seleção de interesse. A combinação tem revisão e aceite da contraparte; declarar entrega não conclui, e só o selecionado confirma o recebimento. No descarte, criar encaminhamento registra a previsão; só o operador do ponto confirma o recebimento. Indicação de outro lugar não cria ponto nem comprova recebimento.

Seleção, entrega bilateral e operações de encaminhamento executam suas escritas relacionadas em transações. Isso não deve ser generalizado para toda operação do sistema: a alteração de situação do ponto e o aviso de inativação, por exemplo, têm chamadas separadas no handler. O contrato atual não possui `id_operacao` nem versões genéricas de todos os agregados. Os limites de concorrência estão nos [contratos](../artefatos/v2.1/contratos_http.md).

## Avisos e indicadores

Avisos usam índice único por evento/destinatário/item, têm leitura idempotente e links internos para as telas de ação. O link não concede permissão sobre o destino.

Indicadores são globais: ofertas ativas e pendências ficam separados das conclusões. `total` soma doações/vendas concluídas e recebimentos em pontos; `indicados` é separado e não comprova reciclagem ou recebimento.

## Testabilidade e reprodução

- [Testes](../tests/): serviços, API, repositórios, segurança, frontend, integração e equivalência OpenAPI.
- [Jornadas](../scripts/validar_jornadas_v2.py): doação, descarte e revenda pela interface, referências persistidas, datas UTC e limpeza seletiva.
- [README](../README.md): comandos para suíte, medição de cobertura e stack isolada.

Os testes de runtime exigem uma URI de replica set de teste; sem ela, são ignorados. A validação funcional anterior não substitui medição de cobertura nem nova execução após mudanças de código. Evidências permanecem nos testes, comandos e histórico de PRs, sem relatórios de verificação separados.
