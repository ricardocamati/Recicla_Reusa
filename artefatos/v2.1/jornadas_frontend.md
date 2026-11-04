# Jornadas e funções de frontend — v2.1

Experiência de referência da v2.1. As Etapas 9 a 15 implementaram as jornadas principais; os passos abaixo preservam o desenho aprovado, não um inventário de todos os controles existentes.

## Interface entregue e limites

- Páginas HTML em `frontend/`, catálogo, gestão de itens, interesses, pontos e avisos, com controles para reserva, combinação, entrega bilateral e indicação de lugar.
- O catálogo carrega até 100 registros sem navegação por páginas. `history.replaceState` preserva filtros; não há página selecionada para restaurar.
- Avisos abrem a tela correspondente, não um deep link garantido para cada item/tentativa.
- O bloqueio de duplo envio existe em controles específicos, não foi aplicado uniformemente a todas as mutações. Erros focam a região de mensagens; isso não é foco automático no primeiro campo inválido.
- Resposta de rede não confirmada orienta recarregar. Não há consulta por `id_operacao` ou reconciliação automática persistida.
- Ponto inativo bloqueia novas previsões; entregas previstas anteriormente continuam concluíveis. Este é o comportamento executável, em divergência com o bloqueio de recebimento descrito no esboço original de J-04.

Ver [contratos atuais](../../docs/http-api.md), [testes de frontend](../../tests/test_frontend.py), [Selenium](../../tests/test_selenium_frontend.py) e [jornadas executáveis](../../scripts/validar_jornadas_v2.py). Esses testes não constituem uma auditoria exaustiva de acessibilidade.

## Desenho de experiência preservado

Os nomes visíveis devem traduzir conceitos de negócio, sem expor códigos internos. Ver [regras](regras_de_negocio.md).


## Mapa de navegação

| Pessoa | Operador |
|---|---|
| Início com Doar/Vender/Descartar/Explorar | Painel com entregas previstas e alertas |
| Explorar ofertas | Meus locais (ativo/inativo) |
| Meus itens: Ativos/Em andamento/Encerrados | Entregas previstas por local |
| Minhas negociações: como anunciante/interessado | Recebimentos e tentativas encerradas |
| Pontos de recebimento | Avisos |
| Avisos e perfil | Perfil |

Não usar troca de perfil para alguém conseguir receber doação. Ação principal é por contexto, não um menu com todas as transições técnicas.

## J-01 — Publicar e explorar

1. Início oferece “Quero doar”, “Quero vender” e “Quero descartar”.
2. Cadastro mostra identificação, categoria, condição e descrição; especificações em pares chave/valor compreensíveis, sem exigir JSON.
3. Venda pede preço positivo; demais modalidades não pedem preço.
4. Revisão mostra efeito: salvar rascunho de oferta ou publicar; descarte salva para escolher local.
   Enquanto for rascunho, a pessoa pode corrigir a modalidade (doação, venda ou descarte) antes de publicar; depois de publicada, a correção exige arquivar e cadastrar nova intenção.
5. Meus itens distingue cadastro salvo, disponível, reservado e encerrado.
6. Catálogo padrão mostra só doação/venda disponíveis. Busca, cidade, categoria e condição ficam visíveis; preço só filtra venda, com regra explícita de excluir doações quando faixa de preço for aplicada.
7. Detalhe usa uma página própria ou painel navegável; voltar preserva filtros e página. Compartilhar link interno não dispensa sessão/permissão.

Cards: título, modalidade, condição, cidade, preço quando aplicável, disponibilidade e uma ação clara. Sem botões de reservar no item próprio, sem rótulo “doador” numa venda. Fotos/upload ficam fora do incremento.

## J-02 — Interesse, escolha e retirada

1. Pessoa abre oferta alheia e seleciona “Tenho interesse”.
2. Interface passa a mostrar “Acompanhar negociação”, sem oferecer criação duplicada.
3. Proprietário vê “Interesses recebidos” e escolhe uma pessoa; confirmação explica que reservará o item e deixará outros pendentes.
4. Oferta passa a reservada. Participantes recebem atalho para combinar entrega.
5. Formulário de combinação: local textual, previsão opcional e observação; resumo mostra quem propôs e qual revisão está pendente.
6. Outra parte aceita; mudar a combinação invalida o aceite anterior e avisa a contraparte.
7. Antes da entrega, ambos podem encerrar seleção por desistência/liberação com motivo. Não comparecimento é motivo, não conclusão.
8. Proprietário clica “Já entreguei”; a confirmação explica que ficará aguardando recebimento.
9. Selecionado clica “Recebi o equipamento”; diálogo mostra equipamento, contraparte e preço combinado quando venda. Conclusão não afirma pagamento verificado.
10. Histórico e indicadores mostram o resultado somente depois da confirmação.

**Impasse:** se a outra parte não confirmar, exibir “Aguardando confirmação de recebimento”. Não liberar automaticamente para outra pessoa. Disputa formal é limitação explícita da PoC.

## J-03 — O que faz “Encaminhar descarte”

### Nome e efeito

Preferir “Escolher ponto de entrega” e, no resumo final, “Registrar entrega prevista”. Não significa chamar coleta domiciliar, transportar, reservar horário ou reciclar. Texto fixo: **“Você levará o equipamento ao local. O operador confirmará o recebimento quando ele for entregue.”**

### Assistente

| Passo | Conteúdo | Gravação |
|---|---|---|
| 1. Equipamento | Título, categoria, condição; voltar para corrigir antes de vincular | Nenhuma |
| 2. Destino | Três opções: ponto cadastrado, indicar outro lugar (tipo obrigatório; nome/cidade/observação opcionais) ou decidir depois; cidade editável, somente locais ativos e compatíveis, com paginação | Seleção local apenas |
| 3. Revisão | Equipamento + destino escolhido + aviso de entrega presencial, quando houver ponto | Nenhuma até confirmar |
| 4. Confirmação | Registrar previsão (ponto) ou informar destinação (lugar), com versão e chave de operação | Uma tentativa/vínculo ou uma indicação, atômicos |

Sem resultado: “Nenhum ponto compatível. Tente outra cidade, indique outro lugar ou escolha depois.” Não cadastrar vínculo incompleto. Fechar o assistente preserva cadastro do equipamento, não cria previsão.

### Passo 2 alternativo — indicar outro lugar

```text
Como você vai descartar?

( ) Levar a um ponto de coleta cadastrado      <- recomendado
      [ locais ativos e compatíveis ]
( ) Indicar outro lugar
      Tipo: [ecoponto / cooperativa / comércio / outro]
      Nome: [__________]  Cidade: [__________]
      Observação: [__________]
( ) Decidir depois
```

- a opção de indicar lugar aparece **sempre**, não só quando faltar ponto compatível;
- o tipo de local é obrigatório; nome, cidade e observação são opcionais; não pedir localização nem validar endereço;
- ao confirmar, o item sai como **destinação informada** e o card mostra o rótulo “Informado por você, não verificado”, com “Desfazer indicação” enquanto o item não estiver arquivado;
- a indicação não é exibida a operadores nem no diretório de locais; nenhuma outra pessoa a confirma;
- o indicador de destinações informadas é exibido separado de “equipamentos recebidos nos pontos”.

Após sucesso: cartão com endereço, horário, “Copiar endereço”, “Ver encaminhamento”, “Trocar ponto” e “Cancelar encaminhamento”. Não usar “mais próximo” sem cálculo de distância. Não pedir data/hora para simular agendamento inexistente.

### Troca e cancelamento

- Troca reabre escolha compatível e mostra comparação antigo/novo antes de confirmar.
- Se novo local ficar inativo durante a escolha, falha preserva a previsão anterior e oferece atualizar lista.
- Cancelar exige confirmação do efeito: a pessoa precisará escolher local novamente.
- Tentativas encerradas ficam legíveis com motivo e data; não há apagar histórico.
- Após recebimento, substituir ações por “Ver recebimento”, sem editar o passado.

## J-04 — Operação do ponto

Painel distingue locais e mostra pendências do local selecionado. Lista paginada exibe equipamento, categoria, autor, registro e situação. Não carregar apenas os primeiros 100 itens globais e filtrar no navegador: API deve limitar aos locais do operador antes da paginação.

- “Confirmar recebimento” abre resumo e pergunta se o equipamento foi entregue fisicamente.
- “Não foi possível receber” exige motivo, informa que a pessoa poderá escolher outro local e não aumenta indicadores.
- Local inativo apresenta aviso, não aceita novas previsões nem recebimento; previsões anteriores ficam acessíveis para troca/cancelamento.
- Histórico de recebimentos é separado da fila atual; sucesso não deve simplesmente fazer o card sumir sem explicação.

## J-05 — Avisos e indicadores

Avisos apontam para item, negociação ou encaminhamento. Ao abrir registro encerrado, mostrar o que ocorreu e somente informações autorizadas. Não reconstruir ação antiga com base no texto do aviso.

Início da pessoa apresenta pendências antes dos indicadores: “Você precisa confirmar recebimento”, “Há interessados na sua oferta”. Operador vê entregas previstas e alertas de locais.

Rótulos de resultado: “Doações recebidas”, “Vendas concluídas com recebimento confirmado” e “Equipamentos recebidos nos pontos”. Nunca “pagamentos confirmados” ou “reciclados” sem acompanhamento correspondente.

## Padrões obrigatórios de usabilidade

- Só esconder campo dependente depois de preservar seu significado; não manter preço oculto vazando para descarte.
- Validar junto do campo e manter conteúdo em erro; mover foco para primeiro erro.
- Durante envio bloquear repetição e mostrar andamento; ao falhar, restaurar ação quando seguro.
- Em resposta perdida, consultar resultado pela chave de operação antes de repetir com chave nova.
- `409`: explicar que registro mudou, oferecer recarga e preservar texto não enviado quando possível; não sobrescrever versão automaticamente.
- Vazio, erro e carregamento são estados diferentes; erro não deve aparecer como “nenhum item”.
- Paginar filtros, filas e seleções; manter ordenação estável e filtros ao voltar.
- Diálogo acessível por teclado, foco devolvido ao acionador, rótulos e região de mensagens legíveis; cabeçalho fixo não pode bloquear clique ou foco.
- Testar largura pequena e jornada completa sem depender de tabela larga ou hover.

## Esboço textual do cartão de descarte

```text
Monitor de 19 polegadas                        ENTREGA PREVISTA
Ponto Centro • atendimento: segunda a sexta
Endereço: endereço público do local
Próximo passo: leve o equipamento ao ponto.
[Copiar endereço] [Ver detalhes] [Trocar ponto] [Cancelar]
```

É um esboço, não conteúdo já criado na aplicação. Após recebimento, mostrar data e local confirmados, sem as ações de troca/cancelamento.
