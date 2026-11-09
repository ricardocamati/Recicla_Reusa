# Regras de negócio — v2.1

Regras do desenho de produto v2.1. Os identificadores não substituem retroativamente o marco V2. A implementação das Etapas 9 a 15 atende parte desses critérios; campos, comandos e garantias ainda diferentes do desenho estão explicitados no [modelo](modelo_dados.md), nos [contratos](contratos_http.md) e na [matriz](matriz_rastreabilidade.md). Não usar esta especificação isoladamente como prova de implementação integral. A Etapa 16 implementa leitura pública com projeção restrita e preservação do legado; a experiência completa de descarte como diretório ainda depende das etapas seguintes. Regras retiradas abaixo permanecem apenas como IDs históricos.

## V21-RN-01 — Atores e identidade

Visitante consulta o diretório sem identidade ou sessão. Tipos de conta implementados: `pessoa` e `ponto_coleta`. Dono, interessado e selecionado são relações. Identidade, destinatários, autor de evento e permissões são derivados da sessão e das referências persistidas, nunca escolhidos no payload. Operador não cadastra oferta como pessoa.

## V21-RN-02 — Modalidade e condição

No modelo-alvo, modalidade de novo item é doacao ou venda; descarte é consulta independente, não modalidade cadastrável. Não há compatibilidade de itens de descarte nem conversão de dados. Enquanto o item for rascunho, o proprietário pode corrigir a modalidade antes de publicar; depois de publicado, ou com interesse, a troca deixa de ser edição comum e exige arquivar e cadastrar nova intenção. Condição física independente: funcional, funcional_com_defeito, reparavel, sem_conserto ou recondicionado. Venda não exige reparar. Não transformar valor ausente em zero; venda exige preço finito maior que zero, doação usa null. Esta restrição de preço é intencionalmente diferente da v2.0.

## V21-RN-03 — Visão pública do catálogo

Catálogo de ofertas exige sessão e retorna apenas ofertas publicadas. Não confundir com o diretório de descarte, cuja leitura é pública. Padrão: situacao=disponivel. Filtro explícito pode incluir reservado, sem ação de interesse; nunca inclui descarte, rascunho, aguardando_confirmacao, concluido ou arquivado. Detalhe próprio de gestão pode acessar esses estados. API deve aplicar a regra, não somente frontend.

## V21-RN-04 — Cadastro, edição e publicação

Oferta nasce rascunho; publicar exige campos válidos e muda para disponivel. Não criar item de descarte: sua entrada abre “Onde descartar”. Editar oferta disponível com interesses pendentes permite descrição/especificações, mas alterações materiais de condição ou preço exigem arquivar, avisar pendentes e nova oferta; não modificar silenciosamente o objeto que motivou interesse. Reservado/aguardando_confirmacao não admite edição material. Histórico registra mudanças permitidas.

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

## V21-RN-11 — Locais ativos e filtros de consulta

Diretório e detalhe de local ativo são acessíveis sem sessão. Cidade e categoria são filtros opcionais e cumulativos; a categoria deve pertencer às categorias aceitas do local. Comparar cidade sem depender de maiúsculas/minúsculas; não inferir posição, distância ou capacidade. Aplicar filtros e ativo=true antes de paginar. Local inativo não aparece nem é recuperado pelo detalhe público.

## V21-RN-12 — Retirado: tentativa de encaminhamento

Não criar encaminhamento ou vínculo com item na consulta. O ID identifica a regra anterior, retirada do alvo; a ausência de efeitos da nova consulta é definida em V21-RN-24.

## V21-RN-13 — Retirado: cancelar e trocar tentativa

Sem tentativa persistida, não há comando de cancelamento/troca. A pessoa pode mudar filtros ou consultar outro local, sem registrar uma operação de descarte.

## V21-RN-14 — Inativação e atualização do diretório

Somente o operador responsável altera ativo/inativo. Inativar remove o local das consultas públicas subsequentes; reativar o torna consultável novamente. Uma tela já aberta não é garantia de atendimento: ao recarregar um detalhe agora inativo, informar indisponibilidade e oferecer retorno à lista. Não criar aviso, tentativa nem resolução em massa; não criar vínculo com equipamentos.

## V21-RN-15 — Retirado: confirmação de descarte no ponto

O operador mantém informações do local, sem confirmar entrega de equipamento no novo fluxo. A consulta não comprova recebimento ou reciclagem; confirmação bilateral de doação/venda continua em V21-RN-09.

## V21-RN-16 — Gestão e referências dos locais

Criar, editar e ativar/inativar exige conta operacional. Derivar responsavel_id da sessão e não aceitar transferência por edição comum. A listagem de gestão filtra os próprios locais antes de paginar e pode incluir inativos. Visitante e pessoa comum não acessam essa gestão. Categorias, endereço e horário descrevem o local, sem vínculo com um novo equipamento. Locais não possuem fila, referência de equipamento ou dependência de encaminhamento. Histórico e referências de ofertas permanecem protegidos no seu próprio fluxo.

## V21-RN-17 — Arquivar versus excluir

Proprietário arquiva oferta rascunho/disponível sem seleção/entrega ativa. A consulta de descarte não produz item arquivável. Pendentes encerram com motivo oferta_arquivada e recebem aviso. Arquivado não reabre nesta versão. Excluir só cadastro sem interesses, tentativas ou eventos operacionais; não usar exclusão para resolver histórico. Conta referenciada mantém restrições básicas existentes.

## V21-RN-18 — Avisos por ação necessária

Novo interesse avisa proprietário; decisão avisa interessado; combinação avisa contraparte; declaração avisa selecionado; confirmação avisa proprietário de doação/venda. Consulta, cópia de endereço, abertura de mapa e alteração do diretório não geram avisos de descarte. Evitar autoaviso e duplicação equivalente por destinatário no mesmo evento. Leitura privada/idempotente é preservada.

## V21-RN-19 — Indicadores e resultados verificáveis

Doação/venda contam itens concluídos com recebimento confirmado. Reserva e declaração ainda sem confirmação não contam. Não há contagem de descarte feito, recebido, indicado ou reciclado a partir de consultas de local. Se houver quantidade de locais ativos, rotular como informação cadastral e não somar a total de equipamentos. O total-alvo de conclusões soma somente doações e vendas; indicadores antigos de descarte não são reapresentados como resultado do diretório. Não implementar histórico de descarte ou conversão automática de dados.

## V21-RN-20 — Versão, comandos e transações

Mutação de registro existente exige versão esperada; criação de interesse exige a versão do item referenciado, sem inventar versão de registro ainda inexistente. Comandos de ciclo exigem id_operacao. A chave estável é item + ator + id_operacao para item/interesse, e ponto + ator + id_operacao para ativação/inativação de local. Registrar resultado/evento; reenvio idêntico recupera o resultado antes de exigir novamente as versões originais, mesma chave com payload distinto conflita. As versões por rota estão em contratos_http.md. Item de oferta, interesse, histórico e avisos derivados mudam atomicamente. Consultas do diretório não são comandos, não exigem versão/id_operacao e não executam transação de negócio. Em resposta perdida, consultar resultado antes de novo comando. Não copiar alegações de idempotência sem testes reais.

## V21-RN-21 — Consultas e acesso

Listas paginadas, offset≥0, limite 1–100, ordenação estável por data e ID, filtros cumulativos. Busca é dado, não regex/código executável. Catálogo não expõe endereço pessoal. Participantes selecionados e proprietário acessam combinação; gestão de locais somente pelo operador responsável. O DTO público contém apenas dados do local, não responsavel_id, contato privado, endereço pessoal, itens ou indicações anteriores. Aviso antigo não restitui permissão operacional. Histórico com pessoa encerrada exige DTO reduzido, sem combinação atual de terceiro.

## V21-RN-22 — Feedback e contrato seguro

Preservar login, validação de origem nas mutações, cookie HttpOnly e respostas sob detail. Leitura pública do diretório é exceção explícita à exigência de sessão; não liberar outras rotas por extensão. Erro não é sucesso; conflito oferece recarga e preserva texto quando possível. Inputs não recebem IDs de atores nem datas geradas. Não remover proteções básicas sob justificativa de uso local.

## V21-RN-23 — Retirado: destinação informada pelo autor

Não registrar nem desfazer indicação privada como etapa de descarte no novo produto. Rotas, schemas e campos da indicação são removidos, sem adaptadores.

## V21-RN-24 — Consulta sem efeitos de descarte

Abrir página, filtrar, paginar, consultar detalhe, copiar endereço e abrir mapa não criam item, interesse, encaminhamento, indicação, notificação ou evento de descarte. Não exigir confirmação final, ID de equipamento ou login. Os filtros são estado de navegação, não documento de domínio. Sem resultado, orientar alteração/limpeza dos filtros; erro de rede não é lista vazia nem descarte concluído.

## V21-RN-25 — Retirado: compatibilidade de descarte

Não há dados de descarte por item a conservar. Por decisão de escopo, não manter rotas antigas, adaptadores, campos ou aba de histórico desse fluxo. A remoção é do código e dos contratos ativos, não uma autorização para apagar bancos. Histórico de ofertas permanece.

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

### Descarte: navegação, não ciclo de item

Abrir diretório → filtrar/paginar → consultar detalhes/copiar endereço → voltar ou escolher outro local. Nenhuma dessas etapas altera dados de domínio, exige confirmação do operador ou produz conclusão de descarte.

Não há transporte, previsão, recebimento ou destinação informada no fluxo-alvo. Os estados exclusivos do processo anterior são removidos do modelo executável. `concluido` continua terminal para as ofertas; não há estorno automático nesta revisão.
