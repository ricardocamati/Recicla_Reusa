# Requisitos — v2.1

**Especificação proposta, não implementada.** As escolhas de produto aceitas já estão refletidas nestes requisitos e nas [regras de negócio](regras_de_negocio.md). Casos verificáveis em [casos_de_teste.md](casos_de_teste.md).

## Objetivo e atores

Pessoa: proprietária de equipamento ou interessada em oferta alheia. Operador: conta responsável por um ou mais pontos físicos. Sistema: aplica invariantes e cria avisos; não certifica acontecimentos físicos nem movimenta dinheiro.

## Requisitos funcionais

### V21-RF-01 — Conta de pessoa e operação

Permitir que uma conta pública ofereça e receba/compre sem troca de perfil. Conta operacional continua provisionada e limitada aos seus locais.

**Aceitação:** A mesma sessão publica item e manifesta interesse alheio, mas não no próprio item; operador não recebe comandos de compra.

### V21-RF-02 — Catálogo de ofertas

Consultar somente doação/venda publicadas e disponíveis por padrão, com detalhe e filtros de texto, modalidade, categoria, condição, cidade e preço quando for venda.

**Aceitação:** Descarte, rascunho, arquivado e concluído não aparecem; reservado só aparece quando solicitado explicitamente e sem novo interesse.

### V21-RF-03 — Cadastro por intenção e gestão

Guiar cadastro em intenção, características e revisão; salvar rascunho e publicar ofertas. Manter descarte salvo sem expor no catálogo. Exibir Ativos, Em andamento e Encerrados.

**Aceitação:** Preço não aparece em doação/descarte; validação preserva preenchimento; editar não altera estado por campo genérico.

### V21-RF-04 — Interesse e reabertura

Registrar interesse, acompanhar decisão e permitir retomada controlada. Exibir interessados nas próprias ofertas.

**Aceitação:** Cancelado pelo autor pode ser retomado com histórico; recusado só reabre por iniciativa do proprietário; uma relação por item/pessoa.

### V21-RF-05 — Reserva e liberação

Selecionar um interessado e tornar reserva explícita para doação e venda; permitir desistência/liberação antes da declaração de entrega.

**Aceitação:** Uma única seleção ativa; outros pendentes não são recusados prematuramente; liberação recupera disponibilidade e preserva histórico.

### V21-RF-06 — Combinação da entrega

Oferecer combinação estruturada aos participantes selecionados: local textual, previsão opcional e observação.

**Aceitação:** Alteração de combinação exige novo aceite da outra parte; não cria transporte ou agendamento garantido.

### V21-RF-07 — Entrega e recebimento bilateral

Proprietário declara entrega após combinação aceita; selecionado confirma recebimento e conclui.

**Aceitação:** Declaração sozinha não conclui; terceiro não confirma; reenvio da mesma operação não duplica evento ou indicador.

### V21-RF-08 — Venda direta com preço reservado

Permitir venda de usado sem avaliação/reparo obrigatório. Manter condição independente da situação comercial.

**Aceitação:** Aceite congela preço; venda não permanece disponível; alterar preço reservado exige liberação e novo aceite.

### V21-RF-09 — Escolha guiada do ponto

**Caminhos:** escolher ponto cadastrado, indicar outro lugar (V21-RF-16) ou decidir depois. A opção de indicar lugar fica sempre disponível, sem depender da ausência de ponto compatível.

Selecionar ponto ativo e compatível por cidade/categoria, revisar e registrar entrega prevista.

**Aceitação:** Selecionar sem confirmar não cria vínculo; nenhuma opção compatível mantém cadastro salvo com orientação; não prometer proximidade sem distância.

### V21-RF-10 — Cancelar/trocar encaminhamento

Permitir ao proprietário cancelar tentativa ou trocar ponto antes do recebimento; disponibilizar solução quando local não puder receber.

**Aceitação:** Tentativas antigas permanecem; troca falha sem perder vínculo anterior; após recebimento não há troca/cancelamento.

### V21-RF-11 — Operação do ponto

Gerir locais ativos/inativos e filas de entregas previstas e recebidas, com filtro por local e paginação.

**Aceitação:** Operador confirma somente recebimento de item associado a seu ponto; impossibilidade exige motivo; inativação não apaga histórico.

### V21-RF-12 — Avisos acionáveis

Notificar novos interesses, seleção/liberação, combinação, declaração de entrega, confirmação, previsão e impossibilidade de recebimento aos afetados.

**Aceitação:** Aviso contém link interno; não duplica por evento/destinatário; não concede acesso operacional a terceiro ou vínculo encerrado.

### V21-RF-13 — Indicadores precisos

Separar ofertas ativas/pendências de doações e vendas com recebimento confirmado e equipamentos recebidos nos pontos.

**Aceitação:** Cada conclusão conta uma vez; previsão não conta; venda não significa pagamento verificado; recebimento não é reciclagem.

### V21-RF-14 — Arquivamento e histórico

Retirar oferta de circulação sem apagar referências e apresentar histórico legível.

**Aceitação:** Não arquivar reserva/declaração pendente sem resolver a operação; excluir apenas cadastro sem vínculos relevantes.

### V21-RF-15 — Navegação e recuperação

Mostrar próximas ações por ator, estados vazios úteis, foco acessível e respostas consistentes a conflito/rede.

**Aceitação:** Voltar do detalhe preserva filtros/página; envio tem bloqueio de duplo clique; falha não informa sucesso e oferece reconciliação/recarregamento.

### V21-RF-16 — Indicar lugar de descarte

Permitir que a pessoa indique um lugar não cadastrado para descartar o equipamento, informando um tipo de local estruturado e, opcionalmente, nome, cidade e observação. O caminho encerra o item como destinação informada, sem confirmação de terceiro.

**Aceitação:** a indicação não cria ponto de coleta, não aparece no diretório nem para operadores, não conta como recebimento no ponto e vem rotulada como informada pelo próprio autor; o autor pode desfazer a indicação enquanto o item não estiver arquivado, sem perder o histórico.

## Requisitos não funcionais

### V21-RNF-01 — Preservação do marco anterior

Preservar a implementação v1.0 e a especificação v2.0 naquilo que não for substituído explicitamente. Definir estratégia de dados antes de qualquer conversão.

### V21-RNF-02 — Integridade e concorrência

Manter autorização, controle de versão, datas UTC, referências e transações. Mutação e avisos derivados constituem a mesma unidade; unicidade precisa existir no banco.

### V21-RNF-03 — Frontend simples e acessível

Manter páginas HTML e módulos JavaScript sem build obrigatório, teclado utilizável e apresentação responsiva. Não depender de mapa ou serviço externo.

### V21-RNF-04 — Evidência própria

Automatizar os cenários desta versão e executar três jornadas em stack/volume de teste próprios. Evidência v2.0 não é reutilizada como aprovação v2.1.

### V21-RNF-05 — Contrato documentado

Definir requests/responses/comandos e confrontar contrato com runtime. Não declarar OpenAPI planejada como descrição da aplicação sem teste de correspondência.

### V21-RNF-06 — Limites locais

Uso local com dados sintéticos; preservar proteções existentes sem acrescentar projeto de segurança pública, procedimentos técnicos de equipamento ou tópico I.

### V21-RNF-07 — Privacidade da destinação informada

A indicação de lugar pertence ao autor. Ela não é exposta no diretório, não é exibida a operadores de pontos nem a terceiros e não pode ser usada para inferir a localização de outra pessoa. Nome, cidade e observação são textos livres do autor; coordenadas e arquivos não são aceitos.

## Fronteira

A proposta é cumulativa, mas substitui explicitamente os perfis públicos, a obrigatoriedade de reparo da revenda e a conclusão unilateral como padrão. Nenhuma dessas mudanças já existe por causa deste documento. Exclusões: pagamentos, transporte, agendamento de capacidade, chat em tempo real, fotos/upload, certificação, procedimentos de segurança técnica e publicação pública. Ver decisões para as alternativas ainda em revisão.
