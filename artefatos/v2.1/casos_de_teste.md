# Casos de teste — v2.1

Cenários de aceitação da v2.1, preservados como critérios verificáveis. Há automação nesta versão, mas os cenários não estão todos comprovados integralmente: versões genéricas, chaves de operação e navegação paginada, por exemplo, não correspondem ao contrato atual. Evidências por família e limites estão centralizados na [matriz](matriz_rastreabilidade.md); não inferir aprovação de cada cenário a partir da contagem total de testes.

## Ambiente e dados

Pessoas A/B/C e operadores O1/O2 com locais próprios, registros sintéticos identificados. MongoDB real replica set para concorrência/rollback; testes unitários e de API para validação; Selenium para experiência. Não executar validadores que exigem base vazia contra o banco de demonstração. Datas do servidor, IDs BSON e versões preservados.

## V21-CT-01 — Uma pessoa oferece e recebe

**Vínculos:** V21-RF-01; V21-RN-01, V21-RN-22.

**Precondições:** Duas pessoas A/B; conta operacional O.

**Passos:** A publica; B demonstra interesse; A demonstra interesse em oferta de B; O tenta criar interesse.

**Resultado esperado:** A/B atuam nas duas pontas sem trocar perfil; operador negado; autoria derivada da sessão.

## V21-CT-02 — Visibilidade de catálogo na API

**Vínculos:** V21-RF-02; V21-RN-03, V21-RN-21.

**Precondições:** Ofertas disponíveis, reservadas, concluídas, arquivadas, rascunhos e descarte.

**Passos:** Consultar catálogo padrão, incluir reservados e tentar filtro de descarte.

**Resultado esperado:** Padrão só disponíveis doação/venda; filtro só acrescenta reservado; nunca expõe descarte/concluído; acesso próprio continua possível.

## V21-CT-03 — Filtrar, paginar e voltar do detalhe

**Vínculos:** V21-RF-02, V21-RF-15; V21-RN-03, V21-RN-21.

**Precondições:** Mais de uma página de ofertas de várias cidades/condições.

**Passos:** Aplicar filtros cumulativos, ir à página seguinte, abrir detalhe e voltar.

**Resultado esperado:** Filtros/página preservados; sem vazamento de outras cidades; faixa de preço só inclui vendas, sem doação null como zero.

## V21-CT-04 — Cadastro por intenção e validação

**Vínculos:** V21-RF-03; V21-RN-02, V21-RN-04.

**Precondições:** Pessoa autenticada.

**Passos:** Criar rascunho de doação, publicar venda, salvar descarte; tentar preço zero/negativo e preço em descarte.

**Resultado esperado:** Estados iniciais corretos; venda exige positivo; doação/descarte sem preço; campos e especificações preservados em erro.

## V21-CT-05 — Interesse próprio, repetido e fora de hora

**Vínculos:** V21-RF-04; V21-RN-05.

**Precondições:** Oferta própria e alheia em cada estado.

**Passos:** Criar interesse próprio, duplicado, em reserva e em descarte; criar válido.

**Resultado esperado:** Somente válido cria pendente; índice/serviço impedem duplicata; falhas não criam avisos.

## V21-CT-06 — Retomar sem contornar recusa

**Vínculos:** V21-RF-04; V21-RN-05.

**Precondições:** Relações cancelada, recusada e encerrada.

**Passos:** Autor retoma cancelada; tenta retomar recusada/encerrada; proprietário convida recusada.

**Resultado esperado:** Só caminhos permitidos reabrem; tentativa aumenta e histórico/razão permanecem; combinação antiga é invalidada.

## V21-CT-07 — Reserva única concorrente

**Vínculos:** V21-RF-05; V21-RN-06, V21-RN-20.

**Precondições:** Dois interesses pendentes na mesma oferta.

**Passos:** Disputar seleção dos dois com versões iniciais.

**Resultado esperado:** Uma seleção vence; outra conflita; item tem um vínculo; nenhum sucesso parcial ou aviso duplicado.

## V21-CT-08 — Desistência e não comparecimento

**Vínculos:** V21-RF-05, V21-RF-08; V21-RN-06, V21-RN-07.

**Precondições:** Doação/venda reservadas, sem declaração de entrega.

**Passos:** Selecionado desiste ou proprietário libera por não comparecimento.

**Resultado esperado:** Item disponível; combinação encerrada; pendentes preservados; histórico e avisos corretos; indicador não cresce.

## V21-CT-09 — Propor, revisar e aceitar combinação

**Vínculos:** V21-RF-06; V21-RN-08.

**Precondições:** Reserva válida com participantes A/B.

**Passos:** A propõe; A tenta aceitar; B aceita; A altera; tenta declarar usando revisão antiga.

**Resultado esperado:** Autoaceite negado; alteração invalida aceite; entrega só permitida após contraparte aceitar revisão atual.

## V21-CT-10 — Doação com duas confirmações

**Vínculos:** V21-RF-07; V21-RN-09, V21-RN-10.

**Precondições:** Doação reservada, combinação aceita.

**Passos:** Proprietário declara; terceiro tenta confirmar; selecionado confirma.

**Resultado esperado:** Declaração aguarda confirmação e não conta; terceiro negado; confirmação conclui e encerra demais pendentes.

## V21-CT-11 — Pendência sem confirmação

**Vínculos:** V21-RF-07; V21-RN-09, V21-RN-10.

**Precondições:** Proprietário declarou entrega.

**Passos:** Selecionado não confirma; proprietário tenta liberar, arquivar ou concluir novamente.

**Resultado esperado:** Permanece pendente com instrução; não reoferta, não conta e não afirma resolução automática.

## V21-CT-12 — Venda usada e preço congelado

**Vínculos:** V21-RF-08; V21-RN-02, V21-RN-06, V21-RN-09.

**Precondições:** Item usado funcional com preço positivo.

**Passos:** Publicar sem reparo; selecionar comprador; tentar mudar preço; combinar e concluir bilateralmente.

**Resultado esperado:** Sem avaliação fictícia; reserva explícita; alteração negada; preço selecionado preservado; não afirma pagamento.

## V21-CT-13 — Assistente sem efeitos antes de confirmar

**Vínculos:** V21-RF-09; V21-RN-11, V21-RN-12.

**Precondições:** Descarte aguardando ponto; locais compatíveis e incompatíveis.

**Passos:** Abrir, escolher, voltar, cancelar assistente; reabrir e confirmar local válido.

**Resultado esperado:** Só confirmação cria tentativa; horário/endereço claros; sem promessa de transporte/agendamento; catálogo segue sem descarte.

## V21-CT-14 — Nenhum ponto e seleção além da página

**Vínculos:** V21-RF-09, V21-RF-15; V21-RN-11, V21-RN-21.

**Precondições:** Locais incompatíveis/inativos e compatível em página posterior.

**Passos:** Buscar cidade sem resultado; ampliar filtro; navegar e selecionar.

**Resultado esperado:** Orientação útil, cadastro salvo; compatível posterior acessível; API filtra antes de paginar.

## V21-CT-15 — Previsão disputa inativação/categoria

**Vínculos:** V21-RF-09; V21-RN-11, V21-RN-12, V21-RN-20.

**Precondições:** Local ativo compatível e descarte disponível para ponto.

**Passos:** Concorrer criação de previsão com inativação ou retirada de categoria.

**Resultado esperado:** Nenhuma previsão nova é confirmada sobre leitura obsoleta; se previsão vence, retirar categoria conflita; inativação pode vencer depois e deve avisar previsão preservada.

## V21-CT-16 — Troca atômica de ponto

**Vínculos:** V21-RF-10; V21-RN-12, V21-RN-13, V21-RN-20.

**Precondições:** Tentativa ativa P1; P2 compatível.

**Passos:** Trocar para P2; repetir em cenário com falha injetada antes da criação nova.

**Resultado esperado:** Sucesso encerra P1 e cria uma ativa em P2; falha reverte tudo, mantendo P1; referências e avisos coerentes.

## V21-CT-17 — Cancelar e bloquear depois de recebido

**Vínculos:** V21-RF-10; V21-RN-13, V21-RN-15.

**Precondições:** Uma previsão ativa e outra tentativa recebida.

**Passos:** Autor cancela ativa; tenta cancelar/trocar recebida.

**Resultado esperado:** Ativa encerra, item aguarda ponto; recebida não muda; histórico permanece e indicador não regride.

## V21-CT-18 — Inativação com previsões existentes

**Vínculos:** V21-RF-11; V21-RN-14, V21-RN-16.

**Precondições:** Local próprio com previsão ativa.

**Passos:** Inativar; tentar nova previsão/recebimento; autor troca/cancela; reativar em cenário separado.

**Resultado esperado:** Previsões preservadas e avisadas; novas e recebimento bloqueados enquanto inativo; alternativas acessíveis; reativação restaura atendimento.

## V21-CT-19 — Não foi possível receber

**Vínculos:** V21-RF-11; V21-RN-14.

**Precondições:** Tentativa ativa no local do operador.

**Passos:** Enviar sem motivo, depois motivo válido; autor escolhe outro ponto.

**Resultado esperado:** Sem motivo rejeita; válido encerra como nao_recebido, libera item e avisa autor; nova tentativa não apaga anterior.

## V21-CT-20 — Recebimento e repetição no ponto

**Vínculos:** V21-RF-11; V21-RN-15, V21-RN-20.

**Precondições:** Tentativa ativa, operador correto e operador alheio.

**Passos:** Alheio tenta confirmar; correto confirma; reenvia mesma chave; disputa cancelar/receber.

**Resultado esperado:** Somente ator correto e uma transição válida; uma contagem final; reenvio recupera resultado; sem órfãos ou dupla conclusão.

## V21-CT-21 — Filas limitadas ao operador e paginadas

**Vínculos:** V21-RF-11, V21-RF-15; V21-RN-16, V21-RN-21.

**Precondições:** Muitos locais/itens de dois operadores, próprios além dos primeiros 100 globais.

**Passos:** Consultar fila/pontos paginados e aplicar local/status.

**Resultado esperado:** Só próprios, inclusive páginas posteriores; operador não recebe páginas vazias falsas por filtro no cliente.

## V21-CT-22 — Destinatários e links de aviso

**Vínculos:** V21-RF-12; V21-RN-18.

**Precondições:** Proprietário, selecionado, pendente, ex-selecionado e operador.

**Passos:** Executar novo interesse, reserva, combinação, declaração, previsão e recebimento; abrir aviso antigo.

**Resultado esperado:** Quem precisa agir recebe aviso único; terceiros não recebem dados; link antigo não restaura permissão de mutação.

## V21-CT-23 — Indicadores sem resultados fictícios

**Vínculos:** V21-RF-13; V21-RN-19.

**Precondições:** Rascunhos, previsões, reservas, declarações e conclusões.

**Passos:** Consultar totais antes/depois de receber doação/venda/descarte e repetir comando.

**Resultado esperado:** Só conclusões permitidas aumentam uma vez; não mede pagamento/reciclagem; tentativas canceladas não contam.

## V21-CT-24 — Arquivar e excluir sem apagar histórico

**Vínculos:** V21-RF-14; V21-RN-04, V21-RN-17.

**Precondições:** Oferta disponível com pendentes, reservada e item com tentativa antiga.

**Passos:** Arquivar disponível; tentar arquivar reserva; excluir item referenciado.

**Resultado esperado:** Pendentes encerram com aviso; reserva exige resolver; dependências impedem exclusão; gestão mostra encerrados.

## V21-CT-25 — Conflito preserva formulário

**Vínculos:** V21-RF-03, V21-RF-15; V21-RN-04, V21-RN-20, V21-RN-22.

**Precondições:** Duas sessões editam o mesmo registro.

**Passos:** Salvar em uma, tentar salvar versão antiga na outra.

**Resultado esperado:** 409 legível, nenhuma sobrescrita; texto não enviado preservado até recarregar conscientemente.

## V21-CT-26 — Resposta perdida e consulta de operação

**Vínculos:** V21-RF-07, V21-RF-10, V21-RF-15; V21-RN-20, V21-RN-22.

**Precondições:** Comando confirmado no servidor com resposta interrompida.

**Passos:** Consultar resultado pela mesma origem/ator/chave; repetir igual; reutilizar com payload diferente.

**Resultado esperado:** Resultado recuperado sem novo efeito; payload distinto conflita; terceiro não consulta resultado alheio.

## V21-CT-27 — Rollback com avisos

**Vínculos:** V21-RF-05, V21-RF-10, V21-RF-12; V21-RN-20.

**Precondições:** Replica set real, relações e tentativa isoladas.

**Passos:** Injetar falha depois de primeira escrita e antes de todos os avisos; comparar antes/depois.

**Resultado esperado:** Nenhuma mutação parcial em item, relação/tentativa, histórico e avisos; sem alegar atomicidade só por mocks.

## V21-CT-28 — Navegação acessível e responsiva

**Vínculos:** V21-RF-15; V21-RN-21, V21-RN-22.

**Precondições:** Chrome em largura pequena e teclado, dados de todas as jornadas.

**Passos:** Abrir diálogos, preencher, voltar, confirmar; simular vazio/erro/carregamento.

**Resultado esperado:** Foco correto, mensagem local, botão não encoberto; erro distinto de vazio; nenhuma conclusão fictícia.

## V21-CT-29 — Proteções comuns preservadas

**Vínculos:** V21-RF-01, V21-RF-11, V21-RF-15; V21-RN-01, V21-RN-21, V21-RN-22.

**Precondições:** Sem sessão, sessão de outro participante, origem inválida.

**Passos:** Chamar comandos/detalhes diretamente, sem depender dos botões.

**Resultado esperado:** Precedência/autorização preservadas; servidor deriva ator; hash e campos internos ausentes dos DTOs.

## V21-CT-30 — Três jornadas completas isoladas

**Vínculos:** V21-RF-02, V21-RF-07, V21-RF-11, V21-RF-13; V21-RN-03, V21-RN-09, V21-RN-15, V21-RN-19, V21-RN-20.

**Precondições:** Stack e volume próprios de teste; pessoas e pontos sintéticos identificados.

**Passos:** Concluir doação, venda direta e entrega no ponto pelo navegador; conferir documentos e avisos; limpar fixtures da execução.

**Resultado esperado:** Estados/indicadores correspondem aos atos confirmados, referências válidas e limpeza seletiva comprovada; banco de demonstração não é afetado.

## V21-CT-31 — Indicar lugar sem confirmação de terceiro

**Vínculos:** V21-RF-09, V21-RF-16; V21-RN-11, V21-RN-23.

**Precondições:** descarte próprio em `aguardando_ponto`; duas cidades, uma sem ponto compatível.

**Passos:** abrir o assistente na cidade sem ponto compatível; escolher “Indicar outro lugar”; tentar confirmar só com tipo; confirmar com tipo e nome; abrir o item como proprietário e como outro usuário; abrir a área do operador de um ponto existente.

**Resultado esperado:** a opção de indicar lugar aparece mesmo quando existe ponto compatível; sem tipo a confirmação é rejeitada; com tipo, o item vai para `destinacao_informada` com rótulo de informação não verificada; nenhum ponto novo aparece no diretório; o operador não vê a indicação; o indicador de recebidos não aumenta.

## V21-CT-32 — Desfazer indicação e conflito com tentativa ativa

**Vínculos:** V21-RF-16; V21-RN-11, V21-RN-23.

**Precondições:** item com destinação informada; item em `aguardando_ponto` com ponto compatível disponível.

**Passos:** desfazer a indicação; conferir o estado e o histórico; informar destinação e tentar registrar previsão; cancelar a indicação e então registrar previsão; tentar desfazer a indicação em item arquivado.

**Resultado esperado:** desfazer devolve o item a `aguardando_ponto` preservando o registro anterior; indicação e tentativa ativa não coexistem (`409` sem efeito parcial); item arquivado não aceita desfazer.

## V21-CT-33 — Validação da indicação de lugar

**Vínculos:** V21-RF-16; V21-RN-22, V21-RN-23.

**Precondições:** pessoa autenticada com descarte próprio.

**Passos:** enviar tipo inexistente; enviar nome/cidade/observação acima do limite; enviar coordenada ou arquivo; repetir o comando com a mesma chave de operação e payload diferente.

**Resultado esperado:** valores inválidos retornam `400` sem alterar o item; apenas tipo estruturado e textos livres são aceitos; a chave reutilizada com payload distinto conflita; nada sensível aparece na resposta.

## V21-CT-34 — Indicadores separam recebido de indicado

**Vínculos:** V21-RF-13, V21-RF-16; V21-RN-19, V21-RN-23.

**Precondições:** um descarte recebido no ponto e outro com destinação informada.

**Passos:** consultar indicadores; desfazer a indicação e consultar de novo; confirmar recebimento do segundo item em um ponto compatível.

**Resultado esperado:** indicado e recebido aparecem em contagens distintas; desfazer remove a contagem de indicados; o recebimento confirmado aumenta apenas a contagem de recebidos; a soma de indicados nunca é apresentada como reciclagem.

## Reprodução e critérios ainda não comprovados

Executar a suíte completa, contratos, navegação e jornadas reais; registrar comandos, data e resultado real. Não estimar contagem de testes. Simultaneidade sem intercalação instrumentada não prova todas as ordens; documentar precisamente o que foi exercitado. Novos índices e coleção devem ser verificados no bootstrap real.
