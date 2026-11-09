# Requisitos — v2.1

Esta é a especificação de produto da v2.1, revisada para descarte como diretório público. A Etapa 16 implementa leitura pública e proteção do legado; a interface pública e a retirada do fluxo por item continuam pendentes nas etapas seguintes. Os critérios abaixo não constituem resultado de teste nem comprovação integral de entrega. A [matriz](matriz_rastreabilidade.md) distingue código, evidências e limites; os [contratos](contratos_http.md) registram as diferenças entre o desenho aprovado e o executável. Casos verificáveis em [casos_de_teste.md](casos_de_teste.md).

## Objetivo e atores

Visitante: qualquer pessoa que consulta onde descartar, sem sessão. Pessoa autenticada: proprietária de oferta ou interessada em doação/venda. Operador: conta responsável por um ou mais locais. Sistema: aplica invariantes de ofertas e gestão, mas não rastreia nem certifica descarte físico.

## Requisitos funcionais

### V21-RF-01 — Conta de pessoa e operação

Permitir que uma conta pública ofereça e receba/compre sem troca de perfil. Conta operacional continua provisionada e limitada aos seus locais.

**Aceitação:** A mesma sessão publica item e manifesta interesse alheio, mas não no próprio item; operador não recebe comandos de compra.

### V21-RF-02 — Catálogo de ofertas

Consultar somente doação/venda publicadas e disponíveis por padrão, com detalhe e filtros de texto, modalidade, categoria, condição, cidade e preço quando for venda.

**Aceitação:** Descarte, rascunho, arquivado e concluído não aparecem; reservado só aparece quando solicitado explicitamente e sem novo interesse.

### V21-RF-03 — Cadastro por intenção e gestão

Guiar cadastro de doação/venda em intenção, características e revisão; salvar rascunho e publicar ofertas. “Onde descartar” abre o diretório, não o formulário de item. Exibir Ativos, Em andamento e Encerrados para ofertas; a apresentação dos registros legados não autoriza conversão ou exclusão automática.

**Aceitação:** Preço não aparece em doação; venda exige preço positivo; validação preserva preenchimento; não existe novo cadastro de item de descarte no fluxo-alvo; editar não altera estado por campo genérico.

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

### V21-RF-09 — Onde descartar: diretório público

Permitir consulta de locais ativos sem login, conta ou item. Oferecer filtros opcionais e cumulativos por cidade e categoria, paginação, detalhe e cópia do endereço público. Exibir nome, endereço, categorias aceitas e horário quando informado. Link opcional para mapa externo não é requisito para consultar o local.

**Aceitação:** Visitante sem cookie consulta lista e detalhe; filtros são aplicados antes da paginação; local inativo não aparece; vazio e falha são distintos; nenhuma ação cria item, encaminhamento, indicação, aviso ou resultado de descarte. Não prometer proximidade sem cálculo de distância.

### V21-RF-10 — Retirado: cancelar/trocar encaminhamento

Fora do escopo revisado. O diretório não registra tentativas; escolher outro local é uma nova consulta, sem cancelamento ou troca persistidos. O ID fica reservado ao requisito anterior; não é pendência futura.

### V21-RF-11 — Gestão dos locais pelo operador

Cadastrar e atualizar os próprios locais, incluindo nome, endereço público, categorias, horário e situação ativo/inativo. Gestão exige sessão operacional, com listagem própria paginada que pode incluir inativos.

**Aceitação:** Visitante e pessoa comum não gerem locais; operador não altera local alheio; inativação retira o local das novas consultas públicas; nenhum painel exige fila, previsão ou confirmação de recebimento. Registros e referências legadas são preservados.

### V21-RF-12 — Avisos acionáveis

Notificar novos interesses, seleção/liberação, combinação e entrega/recebimento de doação ou venda aos afetados. Consulta de local e gestão do diretório não criam avisos de encaminhamento, confirmação ou impossibilidade de descarte.

**Aceitação:** Aviso contém link interno; não duplica por evento/destinatário; não concede acesso operacional a terceiro ou vínculo encerrado.

### V21-RF-13 — Indicadores sem descarte presumido

Separar ofertas ativas e pendências de doações/vendas com recebimento confirmado. O diretório informa locais, não conta equipamentos entregues, recebidos, indicados ou reciclados.

**Aceitação:** Cada conclusão de oferta conta uma vez; consulta, cópia de endereço e abertura de mapa não alteram resultados. Quantidade de locais ativos, se exibida, é informação cadastral separada. Totais-alvo não somam descarte legado a resultados novos de doação/venda; dados históricos não são apagados para isso.

### V21-RF-14 — Arquivamento e histórico

Retirar oferta de circulação sem apagar referências e apresentar histórico legível.

**Aceitação:** Não arquivar reserva/declaração pendente sem resolver a operação; excluir apenas cadastro sem vínculos relevantes.

### V21-RF-15 — Navegação e recuperação

Mostrar próximas ações por ator, estados vazios úteis, foco acessível e respostas consistentes a conflito/rede.

**Aceitação:** Voltar do detalhe preserva filtros/página; envio tem bloqueio de duplo clique; falha não informa sucesso e oferece reconciliação/recarregamento.

### V21-RF-16 — Retirado: indicar lugar de descarte

A indicação privada e seu desfazimento deixam de integrar o produto-alvo porque não há item de descarte a encerrar. Ausência de resultado oferece mudar filtros, não informar uma destinação. Os dados anteriores permanecem preservados; o ID não é reutilizado.

## Requisitos não funcionais

### V21-RNF-01 — Preservação do marco anterior

Preservar a implementação v1.0 e a especificação v2.0 naquilo que não for substituído explicitamente. Definir estratégia de dados antes de qualquer conversão.

### V21-RNF-02 — Integridade e concorrência

Manter autorização, controle de versão, datas UTC, referências e transações. Mutação e avisos derivados constituem a mesma unidade; unicidade precisa existir no banco.

### V21-RNF-03 — Frontend simples e acessível

Manter páginas HTML e módulos JavaScript sem build obrigatório, teclado utilizável e apresentação responsiva. Não depender de mapa ou serviço externo.

### V21-RNF-04 — Evidência própria

Automatizar doação, venda e consulta pública de descarte em stack/volume de teste próprios. A terceira jornada não conclui item nem confirma recebimento em ponto. Testes do fluxo antigo e evidências anteriores não aprovam os critérios revisados.

### V21-RNF-05 — Contrato documentado

Definir requests/responses/comandos e confrontar contrato com runtime. Não declarar OpenAPI planejada como descrição da aplicação sem teste de correspondência.

### V21-RNF-06 — Limites locais

Uso local com dados sintéticos; preservar proteções existentes sem acrescentar projeto de segurança pública, procedimentos técnicos de equipamento ou tópico I.

### V21-RNF-07 — Retirado: privacidade da destinação informada

A criação de indicação privada saiu do escopo com V21-RF-16. Isso não torna públicas indicações já armazenadas. Para o diretório, aplica-se V21-RNF-08.

### V21-RNF-08 — Projeção pública e consulta sem coleta pessoal

Lista e detalhe públicos expõem somente os dados do local: identificador, nome, endereço público, categorias e horário. Não expor usuário responsável, hash, endereço pessoal, dados de itens ou indicações legadas. Não exigir identidade, localização precisa ou dados do equipamento para consultar. A liberação de leitura não altera a sessão e a autorização das mutações.

## Fronteira

A revisão é cumulativa e mantém as decisões de conta única, venda direta e conclusão bilateral de ofertas. O descarte por item é explicitamente substituído por consulta pública de locais; não preservar o processo retirado como alternativa obrigatória. A implementação dessas mudanças é identificada na matriz; os requisitos mais amplos de versão, idempotência, avisos e navegação não se tornam comprovados por estarem escritos. Exclusões: pagamentos, transporte, agendamento de capacidade, chat em tempo real, fotos/upload, certificação, procedimentos de segurança técnica e infraestrutura de implantação pública na internet. Consulta local sem login está incluída. As diferenças remanescentes estão documentadas nos contratos e jornadas desta pasta.
