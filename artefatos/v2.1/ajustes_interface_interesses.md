# Ajustes de interface — perfil e interesses compactos

## Contexto e escopo

Planejamento aprovado em conversa em 11/11/2026. **Etapas 21–24 concluídas; Etapas 23 e 24 validadas em 12/11/2026.** Este documento complementa as jornadas v2.1 somente nos pontos descritos abaixo. Os comportamentos entregues são de apresentação e interação; não substituem contratos HTTP ou regras de autorização.

No início deste planejamento, a interface repetia o tipo da conta em selos, misturava interesses cancelados aos ativos e mantinha aberto o formulário de combinação. As Etapas 21–23 tratam esses pontos: identificação sem repetição, ativos/histórico e cards compactos com edição explícita.

Objetivo: reduzir ruído visual e separar acompanhamento, edição e histórico, sem alterar reserva, desistência, retomada ou conclusão bilateral.

## Requisitos da revisão

### UI-RF-01 — Identificação do perfil

- Retirar os selos de tipo de conta (“Pessoa”/“Ponto de coleta”) do cabeçalho compartilhado e dos destaques das telas comuns.
- Manter o nome do usuário onde ele já identifica a sessão.
- Manter o tipo da conta visível em “Meu perfil”. Não remover a opção ou informação necessária para gerenciar o perfil operacional.
- Preservar a navegação por perfil, as guardas da interface e a autorização do servidor. Esconder o selo não transforma operador em pessoa nem libera ações.

### UI-RF-02 — Interesses ativos e histórico

- Adotar os filtros “Ativos” (padrão) e “Histórico” nas listas de interesses enviados e recebidos.
- Ativos reúne interesses `pendente` e `selecionado`; Histórico reúne `cancelado`, `recusado` e `encerrado`, conforme os estados já existentes no contrato. A classificação não cria novos estados de domínio.
- Depois de “Desistir”, retirar o card da lista ativa somente após confirmação da API e reconciliar a lista recebida do servidor. Mostrar “Você desistiu deste interesse.”
- Preservar o documento, a tentativa e as referências. O card cancelado fica acessível em Histórico; “Retomar” continua disponível apenas quando a regra atual permitir.
- Em Histórico, uma retomada ou reabertura bem-sucedida move o card para Ativos na próxima reconciliação. Não deixa card ativo preso na lista histórica.
- Falha confirmada conserva o card e apresenta erro. Resposta perdida/ambígua exige releitura antes de afirmar sucesso ou fracasso; nenhuma remoção otimista definitiva.
- Contadores e mensagens de vazio correspondem ao filtro selecionado. Atualizar a lista preserva o filtro; a paginação da API deve ser percorrida antes da classificação local para não ocultar registros de páginas posteriores.

### UI-RF-03 — Resumo compacto e edição sob demanda

- Cards de interesses recebidos e enviados iniciam compactos: título, estado, modalidade, categoria, situação do item e resumo da combinação quando existir.
- Uma combinação existente exibe local, previsão e observação quando informados, além de “aguardando aceite” ou “aceita”. Diferenciar “aguardando seu aceite” de “aguardando aceite da outra pessoa”.
- “Ver detalhes” expande informações secundárias e ações adicionais; “Recolher” retorna ao resumo. Não usar o formulário como visualização de detalhes.
- Não exibir a contagem de tentativas do interesse no card; o número é dado de histórico e permanece consultável pela API.
- “Propor combinação”, quando ainda não há proposta, ou “Alterar combinação”, quando já existe, abre o formulário por ação explícita.
- Ao editar, preencher os valores atuais, inclusive previsão convertida para o horário local; manter o envio UTC existente. Não alterar data/hora por conversão duplicada.
- Previsão é data e hora, sem segundos nem milissegundos, na exibição e no campo de edição. Salvar sem alterar o campo preserva o instante original persistido; alterar grava o minuto escolhido; limpar envia nulo.
- “Salvar alteração” só recolhe após confirmação e releitura da revisão salva. “Cancelar edição” fecha sem requisição nem persistência. Erro de validação/rede mantém os campos preenchidos para correção.
- Cancelar uma edição descarta apenas o rascunho visual; reabrir carrega a combinação persistida. Cancelar a primeira proposta volta ao resumo sem criar combinação.
- “Aceitar combinação” permanece visível no resumo para a contraparte elegível. Não permitir aceitar a própria proposta nem uma revisão desatualizada.
- “Liberar reserva” fica na área expandida, mantém solicitação de motivo e depende da autorização atual. Desistência e demais ações mantêm suas regras; compactação não concede nem retira permissão.
- Depois de atualizar, aceitar ou salvar com sucesso, apresentar o card reconciliado e compacto.
- Não manter formulário aberto em interesse cancelado, recusado ou encerrado; item concluído também não admite edição de combinação.

## Acessibilidade e estados de interação

- Botões de expansão/edição devem funcionar por teclado e expor estado com `aria-expanded` e associação ao conteúdo por `aria-controls`.
- Conteúdo recolhido não pode permanecer na ordem de tabulação.
- Ao abrir a edição, focar o primeiro campo; ao cancelar/recolher, devolver foco ao controle correspondente. Se o card sair da lista, encaminhar foco para mensagem ou cabeçalho da lista.
- Bloquear duplo envio enquanto a ação aguarda resposta e reabilitar controles em erro.
- A 360 px de largura e em desktop, os cards não devem causar rolagem horizontal.

## Critérios de aceitação

| Caso | Dado / Quando / Então | Referência |
|---|---|---|
| UI-CT-01 | Dada pessoa ou operador autenticado, ao navegar nas telas comuns, não há selo de tipo repetido; o tipo permanece em Meu perfil e o menu conserva as permissões. | UI-RF-01 |
| UI-CT-02 | Dado interesse ativo, ao confirmar Desistir com sucesso, ele sai de Ativos, a mensagem aparece e o mesmo registro é encontrado em Histórico após recarregar. | UI-RF-02 |
| UI-CT-03 | Dada falha de desistência, o card permanece e o erro aparece; em resposta perdida, a interface relê o servidor antes de apresentar resultado definitivo. | UI-RF-02 |
| UI-CT-04 | Dado interesse cancelado retomável em Histórico, ao retomar com sucesso, ele volta a Ativos sem duplicação nem perda de tentativa/histórico. | UI-RF-02 |
| UI-CT-05 | Dados interesses em várias páginas, ao filtrar/atualizar, todos são classificados e os contadores/vazios refletem o filtro; recusado e concluído ficam em Histórico. | UI-RF-02 |
| UI-CT-06 | Dado card selecionado com combinação, ao carregar a tela, o resumo aparece e nenhum campo de edição está aberto; Alterar combinação abre valores atuais. | UI-RF-03 |
| UI-CT-07 | Dado formulário editado, ao cancelar, nenhuma mutação é enviada e o card recolhe; ao reabrir, recupera os valores persistidos. | UI-RF-03 |
| UI-CT-08 | Dada alteração válida, ao salvar, a revisão confirmada aparece no resumo compacto; em erro, o formulário mantém os dados e não anuncia sucesso. | UI-RF-03 |
| UI-CT-09 | Dada proposta pendente, somente a contraparte elegível vê Aceitar combinação no resumo; proposta própria ou revisão vencida não pode ser aceita. | UI-RF-03 |
| UI-CT-10 | Dado card recebido, ao expandir detalhes, Liberar reserva aparece com motivo obrigatório; cancelar, recusar ou concluir não deixa edição ativa. | UI-RF-03 |
| UI-CT-11 | Dado card sem combinação, Propor combinação abre formulário vazio e cancelar não cria registro; previsão existente conserva o instante após edição. | UI-RF-03 |
| UI-CT-12 | Dado uso por teclado/tela estreita, expansão, edição, cancelamento e remoção preservam foco, sem tabulação em campos ocultos nem rolagem horizontal; duplo clique não duplica ação. | Acessibilidade |
| UI-CT-13 | Dada combinação com previsão gravada com segundos, ao abrir a edição, o campo mostra apenas data e hora; salvar sem alterar conserva o instante original e alterar grava o minuto escolhido. | UI-RF-03 |
| UI-CT-14 | Dado interesse em primeira tentativa ou retomada, os detalhes do card não exibem contagem de tentativas; o histórico e a API continuam com o valor. | UI-RF-03 |

Critérios escritos não são resultados de teste. UI-CT-13 e UI-CT-14 foram implementados em 12/11/2026 e verificados em `tests/test_etapa24_interesses.py`. UI-CT-01 a UI-CT-12 estão implementados e verificados: identificação em `tests/test_selenium_frontend.py`, ativos/histórico em `tests/test_etapa22_interesses.py` e cards/combinação em `tests/test_etapa23_interesses.py`. O consumidor `scripts/validar_jornadas_v2.py` abre explicitamente a edição antes de preencher e foi exercitado nas jornadas Docker isoladas. Não houve mudança dos contratos de negócio nem aplicação na base de demonstração.

## Contratos, dados e exclusões

- Reutilizar listagens, paginação e comandos de interesses existentes. Não criar endpoint nem alterar schema por este planejamento.
- Filtros e estado de expansão são apresentação local, não campos persistidos no MongoDB.
- Não apagar interesses cancelados, converter tipos de conta, migrar banco ou tocar na demonstração.
- Não redesenhar outras telas, adicionar chat, automatizar aceite ou enfraquecer confirmação bilateral.
- Se a implementação exigir mudança de contrato ou nova regra de domínio, revisar o planejamento antes de prosseguir.

## Sequência da implementação

1. Criar testes de regressão inicialmente falhando para identificação do perfil, filtros e compactação; conservar os testes de permissões existentes.
2. Ajustar cabeçalho e telas comuns sem remover a identificação em Meu perfil.
3. Implementar filtros de ativos/histórico e reconciliação de desistência/retomada/reabertura, com mensagens e contadores.
4. Implementar resumo compacto, detalhes e formulário sob demanda com preenchimento, cancelamento e ações por ator.
5. Exercitar erros, resposta perdida, revisões concorrentes, paginação, teclado e telas estreitas.
6. Reconstruir imagens e validar no navegador em stack isolada com MongoDB real; rodar regressões de ofertas e permissões. Só então marcar tarefas do TODO.

Arquivos prováveis: `frontend/js/comum.js`, `frontend/js/interesses.js`, `frontend/interesses.html`, templates de páginas com `session-chip`/`role-badge` e estilos compartilhados. Testes de referência: `tests/test_frontend.py`, `tests/test_selenium_frontend.py`, `tests/test_interesses_v2.py` e `tests/test_interesses_runtime.py`. A implementação deve identificar os seletores reais antes de editar e acrescentar testes de navegador específicos para os novos critérios.
