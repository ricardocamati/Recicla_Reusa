# Regras de negócio — v2.1

Regras do desenho de produto v2.1. Os identificadores não substituem retroativamente o marco V2. A implementação das Etapas 9 a 15 atende parte desses critérios; campos, comandos e garantias ainda diferentes do desenho estão explicitados no [modelo](modelo_dados.md), nos [contratos](contratos_http.md) e na [matriz](matriz_rastreabilidade.md). Não usar esta especificação isoladamente como prova de implementação integral.

## V21-RN-01 — Atores e identidade

Tipos implementados: `pessoa` e `ponto_coleta`. Dono, interessado e selecionado são relações. Identidade, destinatários, autor de evento e permissões são derivados da sessão e das referências persistidas, nunca escolhidos no payload. Operador não cadastra oferta como pessoa.

## V21-RN-02 — Modalidade e condição

Modalidade fixa no ciclo: doacao, venda, descarte. Enquanto o item for rascunho, o proprietário pode corrigir a modalidade antes de publicar; depois de publicado, ou com interesse ou vínculo de descarte ativo, a troca deixa de ser edição comum e exige arquivar e cadastrar nova intenção. Condição física independente: funcional, funcional_com_defeito, reparavel, sem_conserto ou recondicionado. Venda não exige reparar. Não transformar valor ausente em zero; venda exige preço finito maior que zero, doação/descarte usam null. Esta restrição de preço é intencionalmente diferente da v2.0.

## V21-RN-03 — Visão pública do catálogo

Catálogo exige sessão e retorna apenas ofertas publicadas. Padrão: situacao=disponivel. Filtro explícito pode incluir reservado, sem ação de interesse; nunca inclui descarte, rascunho, aguardando_confirmacao, concluido ou arquivado. Detalhe próprio de gestão pode acessar esses estados. API deve aplicar a regra, não somente frontend.

## V21-RN-04 — Cadastro, edição e publicação

Oferta nasce rascunho; publicar exige campos válidos e muda para disponivel. Descarte nasce aguardando_ponto. Editar oferta disponível com interesses pendentes permite descrição/especificações, mas alterações materiais de condição ou preço exigem arquivar, avisar pendentes e nova oferta; não modificar silenciosamente o objeto que motivou interesse. Reservado/aguardando_confirmacao não admite edição material. Histórico registra mudanças permitidas.

## V21-RN-05 — Interesse único e reabertura

Uma relação por item/pessoa. Criar pendente somente para oferta disponível de outra pessoa. Autor cancela pendente; proprietário recusa com motivo. Autor pode retomar cancelado enquanto disponível. Recusado reabre somente por comando do proprietário. Nova tentativa incrementa tentativa, limpa combinação antiga e mantém histórico. Encerrado por conclusão ou arquivamento não reabre.

## V21-RN-06 — Seleção e reserva

Proprietário seleciona pendente e item passa disponivel→reservado, com interesse_selecionado_id. Interesse passa selecionado. Dois aceites concorrentes não podem selecionar duas pessoas. Outros pendentes permanecem, sem nova criação durante reserva. Venda congela preço na seleção; não renova preço pelo cadastro atual.

## V21-RN-07 — Liberação antes da entrega

Selecionado pode desistir e proprietário pode liberar reserva com motivo enquanto item=reservado. Selecionado vira cancelado, item volta disponível, vínculo e combinação ativa são encerrados. Outros pendentes continuam. Sem expiração automática; não comparecimento registra motivo e usa o mesmo fluxo de liberação. Após declaração de entrega, liberação unilateral fica bloqueada.

## V21-RN-08 — Combinação aceita

Somente participantes selecionados propõem local textual, previsão opcional e observação. Cada proposta tem revisão; quem propôs não aceita a própria revisão. Alteração invalida aceite anterior. Proprietário só declara entrega depois de a contraparte aceitar a revisão atual. Proposta/aceite não comprovam entrega ou reserva de horário externo.

## V21-RN-09 — Declaração e recebimento

Proprietário declara entrega com seleção e combinação aceita; item reservado→aguardando_confirmacao. Somente selecionado confirma recebimento, item→concluido e interesse→encerrado com resultado concluido. Demais pendentes encerram por item_concluido. Não admitir conclusão genérica por PATCH de estado. Repetição identificada do mesmo comando devolve resultado anterior, sem segundo efeito.

## V21-RN-10 — Impasse após declaração

Sem confirmação, manter aguardando_confirmacao e instrução clara. Não contar em indicadores finais, reofertar ou presumir recebimento por tempo. Disputas e intervenção administrativa são posteriores; a PoC não alega resolver esse impasse.

## V21-RN-11 — Ponto ativo e compatível

Ponto físico tem ativo, categorias, endereço e horário. Registrar previsão exige ponto ativo que aceite categoria e item próprio aguardando_ponto. Consulta por cidade não equivale a distância. Previsão não significa aceite prévio nem agendamento; autor leva equipamento ao local. O caminho alternativo, sem ponto cadastrado, está em V21-RN-23.

## V21-RN-12 — Tentativa de encaminhamento

Criar documento entrega_prevista em encaminhamentos, vincular item e mudar para entrega_prevista na mesma transação. Só uma tentativa ativa por item. Abrir assistente ou selecionar card não grava. Após confirmação, notificar operador. Descarte não recebe interesses.

## V21-RN-13 — Cancelar e trocar ponto

Autor cancela previsão antes do recebimento: tentativa→cancelado, item→aguardando_ponto, vínculo ativo limpo. Troca exige novo ponto distinto, ativo e compatível: cancelar tentativa anterior e criar nova em unidade transacional. Falha mantém previsão anterior; não deixar janela sem vínculo por duas chamadas independentes.

## V21-RN-14 — Não recebimento e inativação

Operador registra nao_recebido com motivo, tentativa encerra e item volta aguardando_ponto. Inativação bloqueia novas previsões/trocas de destino para o local, preserva existentes e avisa seus autores. Pendentes exibem alerta e podem ser trocadas/canceladas; recebimento fica bloqueado enquanto inativo. Reativação restaura possibilidade. Não apagar histórico nem concluir em massa na inativação.

## V21-RN-15 — Recebimento no ponto

Somente operador responsável pelo ponto de tentativa ativa, com ponto ativo, confirma recebimento. Tentativa→recebido, item→recebido, vínculo ativo limpo e tentativa final fica registrada no histórico. Não cancelar ou trocar tentativa recebida. Dupla confirmação conta uma vez; indicador não significa reciclagem.

## V21-RN-16 — Categorias e referências do ponto

Não retirar categoria com previsão ativa incompatível; devolver conflito sem atualização parcial. Nome/endereço/horário podem mudar com versão e aviso aos autores de previsões afetadas. Desativar é alternativa a excluir: local com tentativa/histórico referenciado não é apagado. Responsável não é transferível por edição comum.

## V21-RN-17 — Arquivar versus excluir

Proprietário arquiva rascunho/disponível, ou descarte aguardando_ponto, sem seleção/entrega ativa. Pendentes encerram com motivo oferta_arquivada e recebem aviso. Arquivado não reabre nesta versão. Excluir só cadastro sem interesses, tentativas ou eventos operacionais; não usar exclusão para resolver histórico. Conta referenciada mantém restrições básicas existentes.

## V21-RN-18 — Avisos por ação necessária

Novo interesse avisa proprietário; decisão avisa interessado; combinação avisa contraparte; declaração avisa selecionado; confirmação avisa proprietário; previsão avisa operador; cancelamento/troca avisa operadores afetados; nao_recebido/inativação avisa autor. Evitar autoaviso e duplicação equivalente por destinatário no mesmo evento. Leitura privada/idempotente é preservada.

## V21-RN-19 — Indicadores e derivados

Doação/venda contam itens concluidos com recebimento confirmado. Descarte conta itens recebidos, não documentos de tentativas. Cancelado, entrega_prevista e aguardando_confirmacao não contam. Venda não comprova pagamento. Consultar estado persistido; frontend não incrementa contador otimisticamente como resultado definitivo.

## V21-RN-20 — Versão, comandos e transações

Mutação de registro existente exige versão esperada; criação de interesse/previsão exige a versão do item referenciado, sem inventar versão de registro ainda inexistente. Comandos de ciclo exigem id_operacao. A chave estável é item + ator + id_operacao para item/interesse/encaminhamento, e ponto + ator + id_operacao para ativação/inativação de local. Registrar resultado/evento; reenvio idêntico recupera o resultado antes de exigir novamente as versões originais, mesma chave com payload distinto conflita. As versões por rota estão em contratos_http.md. Item, interesse/tentativa, histórico e avisos mudam atomicamente. Em resposta perdida, consultar resultado antes de novo comando. Não copiar alegações de idempotência sem testes reais.

## V21-RN-21 — Consultas e acesso

Listas paginadas, offset≥0, limite 1–100, ordenação estável por data e ID, filtros cumulativos. Busca é dado, não regex/código executável. Catálogo não expõe endereço pessoal. Participantes selecionados e proprietário acessam combinação; operador somente encaminhamentos dos próprios pontos. Aviso antigo não restitui permissão operacional. Histórico com pessoa encerrada exige DTO reduzido, sem combinação atual de terceiro.

## V21-RN-22 — Feedback e contrato seguro

Preservar login, validação de origem, cookie HttpOnly e respostas sob detail. Erro não é sucesso; conflito oferece recarga e preserva texto quando possível. Inputs não recebem IDs de atores nem datas geradas. Não remover proteções básicas sob justificativa de uso local.

## V21-RN-23 — Destinação informada pelo próprio autor

Quando não houver ponto compatível, ou quando preferir outro destino, o autor pode indicar um lugar para o descarte. O tipo de local é obrigatório e restrito a `ecoponto`, `cooperativa`, `comercio` ou `outro`; nome, cidade e observação são opcionais. Não aceitar geolocalização, coordenadas, arquivo ou validação de endereço.

A indicação não cria ponto de coleta, não entra no diretório público e não é exibida a operadores nem a terceiros — apenas ao próprio autor e a quem ele autorizar por participação. Não existe confirmação de terceiro para esse caminho: o item termina em `destinacao_informada` e é apresentado como “informado por você, não verificado”.

Indicar lugar e manter tentativa ativa são incompatíveis: informar exige item em `aguardando_ponto` e nenhuma tentativa ativa; tentar registrar previsão exige que a indicação não esteja presente. Enquanto o item não estiver arquivado, o autor pode desfazer a indicação, voltando para `aguardando_ponto` sem apagar o registro anterior do histórico.

`destinacao_informada` **não conta** como “recebido nos pontos” nem como doação/venda: os indicadores mantêm essas contagens separadas.

## Estados e transições resumidos

### Oferta (doação/venda)

| Origem | Comando | Destino | Ator |
|---|---|---|---|
| rascunho | publicar | disponivel | Proprietário |
| disponivel | selecionar interesse | reservado | Proprietário |
| reservado | liberar/desistir | disponivel | Proprietário/selecionado |
| reservado | declarar entrega, combinação aceita | aguardando_confirmacao | Proprietário |
| aguardando_confirmacao | confirmar recebimento | concluido | Selecionado |
| rascunho/disponivel | arquivar | arquivado | Proprietário |

### Descarte

| Origem do item | Comando | Destino | Tentativa |
|---|---|---|---|
| aguardando_ponto | registrar previsão | entrega_prevista | Nova ativa |
| entrega_prevista | trocar ponto | entrega_prevista | Anterior cancelada; nova ativa |
| entrega_prevista | cancelar/não receber | aguardando_ponto | Encerra |
| entrega_prevista | confirmar recebimento | recebido | Recebida |
| aguardando_ponto | informar destinação (lugar indicado) | destinacao_informada | Nenhuma ativa |
| destinacao_informada | desfazer destinação | aguardando_ponto | Nenhuma ativa |
| aguardando_ponto | arquivar | arquivado | Nenhuma ativa |

Não há estado “em transporte”, expiração ou agendamento automático. `concluido` e `recebido` são terminais; correção excepcional/estorno não entra nesta versão. Não aplicar nome de status de uma modalidade em outra.
