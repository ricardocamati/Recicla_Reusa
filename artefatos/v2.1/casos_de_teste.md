# Casos de teste — v2.1

Cenários de aceitação da v2.1, revisados para descarte como diretório público. A Etapa 16 tem testes de API e MongoDB para leitura, projeção, filtros e preservação. A Etapa 17 acrescenta Selenium para J-03 e uma jornada anônima via HTTP/API/MongoDB reais, sem alteração das coleções de ofertas e locais. Isso não comprova a retirada dos comandos antigos nem a transição completa de cada cenário. A matriz delimita a evidência. Casos retirados mantêm seu identificador, mas não são requisitos pendentes nem recebem aprovação de testes antigos. Há automação nesta versão, mas os cenários não estão todos comprovados integralmente: versões genéricas, chaves de operação e navegação paginada, por exemplo, não correspondem ao contrato atual. Evidências por família e limites estão centralizados na [matriz](matriz_rastreabilidade.md); não inferir aprovação de cada cenário a partir da contagem total de testes.

## Ambiente e dados

Visitante V sem cookie e sem conta; pessoas A/B/C e operadores O1/O2 com locais próprios, registros sintéticos identificados. MongoDB real replica set para concorrência/rollback; testes unitários e de API para validação; Selenium para experiência. Não executar validadores que exigem base vazia contra o banco de demonstração. Datas do servidor, IDs BSON e versões preservados.

## V21-CT-01 — Uma pessoa oferece e recebe

**Vínculos:** V21-RF-01; V21-RN-01, V21-RN-22.

**Precondições:** Duas pessoas A/B; conta operacional O.

**Passos:** A publica; B demonstra interesse; A demonstra interesse em oferta de B; O tenta criar interesse.

**Resultado esperado:** A/B atuam nas duas pontas sem trocar perfil; operador negado; autoria derivada da sessão.

## V21-CT-02 — Visibilidade de catálogo na API

**Vínculos:** V21-RF-02; V21-RN-03, V21-RN-21.

**Precondições:** Ofertas disponíveis, reservadas, concluídas, arquivadas e rascunhos.

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

**Passos:** Criar rascunho de doação e publicar venda; tentar preço zero/negativo e preço em doação; escolher “Quero descartar” na entrada.

**Resultado esperado:** Estados iniciais de ofertas corretos; venda exige positivo e doação sem preço; campos preservados em erro; descarte abre o diretório sem criar item ou exigir login para consultá-lo.

## V21-CT-05 — Interesse próprio, repetido e fora de hora

**Vínculos:** V21-RF-04; V21-RN-05.

**Precondições:** Oferta própria e alheia em cada estado.

**Passos:** Criar interesse próprio, duplicado, em reserva; tentar modalidade inválida no cadastro e criar interesse válido.

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

## V21-CT-13 — Retirado: Assistente de encaminhamento

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-35, V21-CT-39, V21-CT-44. Evidências antigas permanecem históricas.

## V21-CT-14 — Retirado: Seleção de ponto e cadastro salvo

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-36, V21-CT-38. Evidências antigas permanecem históricas.

## V21-CT-15 — Retirado: Previsão concorrente com inativação

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-41. Evidências antigas permanecem históricas.

## V21-CT-16 — Retirado: Troca atômica de ponto

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-35, V21-CT-39. Evidências antigas permanecem históricas.

## V21-CT-17 — Retirado: Cancelar tentativa ou bloquear após recebido

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-43. Evidências antigas permanecem históricas.

## V21-CT-18 — Retirado: Inativação com previsões existentes

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-41, V21-CT-43. Evidências antigas permanecem históricas.

## V21-CT-19 — Retirado: Impossibilidade de receber descarte

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-38. Evidências antigas permanecem históricas.

## V21-CT-20 — Retirado: Recebimento no ponto

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-42. Evidências antigas permanecem históricas.

## V21-CT-21 — Retirado: Filas de entrega do operador

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-40. Evidências antigas permanecem históricas.

## V21-CT-22 — Destinatários e links de aviso

**Vínculos:** V21-RF-12; V21-RN-18.

**Precondições:** Proprietário, selecionado, pendente e ex-selecionado de ofertas; visitante do diretório.

**Passos:** Executar interesse, reserva, combinação e entrega/recebimento de oferta; abrir aviso antigo autorizado; consultar e copiar endereço de local como visitante.

**Resultado esperado:** Quem precisa agir na oferta recebe aviso único; terceiros não recebem dados; link antigo não restaura permissão; consulta e cópia não criam avisos de descarte.

## V21-CT-23 — Indicadores sem resultados fictícios

**Vínculos:** V21-RF-13; V21-RN-19.

**Precondições:** Rascunhos, reservas, declarações e conclusões de doação/venda; locais ativos.

**Passos:** Consultar totais antes/depois de receber doação/venda e repetir comando; abrir diretório e detalhe de local.

**Resultado esperado:** Só conclusões de ofertas aumentam uma vez; consulta de local não altera resultados nem cria aviso; `locais_ativos` aparece separado e não entra em `total`; não mede pagamento ou reciclagem.

## V21-CT-24 — Arquivar e excluir sem apagar histórico

**Vínculos:** V21-RF-14; V21-RN-04, V21-RN-17.

**Precondições:** Oferta disponível com pendentes, reservada e oferta com interesse/histórico referenciado.

**Passos:** Arquivar disponível; tentar arquivar reserva; excluir item referenciado.

**Resultado esperado:** Pendentes encerram com aviso; reserva exige resolver; dependências impedem exclusão; gestão mostra encerrados.

## V21-CT-25 — Conflito preserva formulário

**Vínculos:** V21-RF-03, V21-RF-15; V21-RN-04, V21-RN-20, V21-RN-22.

**Precondições:** Duas sessões editam o mesmo registro.

**Passos:** Salvar em uma, tentar salvar versão antiga na outra.

**Resultado esperado:** 409 legível, nenhuma sobrescrita; texto não enviado preservado até recarregar conscientemente.

## V21-CT-26 — Resposta perdida e consulta de operação

**Vínculos:** V21-RF-07, V21-RF-15; V21-RN-20, V21-RN-22.

**Precondições:** Comando confirmado no servidor com resposta interrompida.

**Passos:** Consultar resultado pela mesma origem/ator/chave; repetir igual; reutilizar com payload diferente.

**Resultado esperado:** Resultado recuperado sem novo efeito; payload distinto conflita; terceiro não consulta resultado alheio.

## V21-CT-27 — Rollback com avisos

**Vínculos:** V21-RF-05, V21-RF-12; V21-RN-20.

**Precondições:** Replica set real, item de oferta e relações isolados.

**Passos:** Injetar falha depois de primeira escrita e antes de todos os avisos; comparar antes/depois.

**Resultado esperado:** Nenhuma mutação parcial em item de oferta, relação, histórico e avisos; sem alegar atomicidade só por mocks.

## V21-CT-28 — Navegação acessível e responsiva

**Vínculos:** V21-RF-15; V21-RN-21, V21-RN-22.

**Precondições:** Chrome em largura pequena e teclado, dados de todas as jornadas.

**Passos:** Abrir diálogos, preencher, voltar, confirmar; simular vazio/erro/carregamento.

**Resultado esperado:** Foco correto, mensagem local, botão não encoberto; erro distinto de vazio; nenhuma conclusão fictícia.

## V21-CT-29 — Proteções comuns preservadas

**Vínculos:** V21-RF-01, V21-RF-11, V21-RF-15; V21-RN-01, V21-RN-21, V21-RN-22.

**Precondições:** Sem sessão, sessão de outro participante, origem inválida.

**Passos:** Chamar comandos/detalhes diretamente, sem depender dos botões.

**Resultado esperado:** Precedência/autorização preservadas nas mutações e dados privados; servidor deriva ator; hash e campos internos ausentes dos DTOs. A leitura pública permitida do diretório não libera gestão ou outras rotas. Detalhes dessa exceção em V21-CT-35, V21-CT-37 e V21-CT-40.

## V21-CT-30 — Três jornadas completas isoladas

**Vínculos:** V21-RF-02, V21-RF-07, V21-RF-11, V21-RF-13; V21-RN-03, V21-RN-09, V21-RN-11, V21-RN-19, V21-RN-20, V21-RN-24.

**Precondições:** Stack e volume próprios de teste; pessoas e pontos sintéticos identificados.

**Passos:** Concluir doação e venda direta pelo navegador; em sessão anônima, buscar local, paginar, ver detalhe e copiar endereço; comparar documentos/indicadores antes e depois da consulta; limpar somente fixtures desta execução.

**Resultado esperado:** Doação/venda concluídas bilateralmente; consulta pública concluída sem item, entrega ou indicador de descarte. Referências válidas e limpeza seletiva comprovada; banco de demonstração não é afetado. O script anterior de três entregas não comprova esta jornada revisada.

## V21-CT-31 — Retirado: Indicar lugar para encerrar item

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-35, V21-CT-44. Evidências antigas permanecem históricas.

## V21-CT-32 — Retirado: Desfazer indicação

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-43. Evidências antigas permanecem históricas.

## V21-CT-33 — Retirado: Validação de indicação privada

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-37, V21-CT-44. Evidências antigas permanecem históricas.

## V21-CT-34 — Retirado: Contagem de recebidos e indicados

O cenário antigo saiu do escopo de descarte como diretório; não deve ser reimplementado nem contado como aceitação do fluxo novo. Critérios relacionados da revisão: V21-CT-42. Evidências antigas permanecem históricas.

## V21-CT-35 — Consulta anônima sem cadastro ou efeitos

**Vínculos:** V21-RF-09; V21-RN-11, V21-RN-24.

**Precondições:** Visitante sem conta/cookie, locais sintéticos ativos, snapshot das coleções de domínio e indicadores.

**Passos:** Abrir “Onde descartar” e chamar diretamente lista e detalhe públicos; filtrar, paginar, recarregar e comparar o snapshot.

**Resultado esperado:** Consulta funciona sem login/item; nenhuma sessão obrigatória, documento de domínio, aviso, evento ou resultado de descarte é criado; não aparece confirmação final.


## V21-CT-36 — Filtros cumulativos e paginação do diretório

**Vínculos:** V21-RF-09, V21-RF-15; V21-RN-11, V21-RN-21.

**Precondições:** Mais locais que o limite por página, várias cidades/categorias, inativos e compatível além dos primeiros 100 registros globais.

**Passos:** Consultar sem filtros, combinar cidade/categoria, variar maiúsculas da cidade, avançar página, abrir detalhe e voltar; alterar filtro.

**Resultado esperado:** API filtra ativos/cidade/categoria antes de paginar, com ordem estável nome/ID; resultado posterior acessível; retorno preserva filtros/página; mudar filtro reinicia paginação; não promete proximidade.


## V21-CT-37 — DTO público não expõe responsável ou dados privados

**Vínculos:** V21-RF-09, V21-RNF-08; V21-RN-21, V21-RN-22.

**Precondições:** Local público associado a operador com endereço pessoal distinto; dados privados da conta na base.

**Passos:** Como visitante e pessoa comum, inspecionar lista/detalhe; tentar acrescentar responsavel_id, item_id, ativo=false e escopo desconhecido à consulta pública.

**Resultado esperado:** Somente id/nome/endereco público/categorias_aceitas/horario_atendimento são retornados. Querys não permitidas são rejeitadas, sem liberar inativos ou dados privados; nenhum dado privado da conta é unido à resposta.


## V21-CT-38 — Vazio, carregamento e erro sem falso resultado

**Vínculos:** V21-RF-09, V21-RF-15; V21-RN-24.

**Precondições:** Cidade/categoria sem resultado; respostas lentas e indisponibilidade de API simuláveis.

**Passos:** Buscar sem resultado; alterar/limpar filtros; atrasar e interromper resposta; tentar novamente.

**Resultado esperado:** Vazio confirmado orienta mudar filtros; carregamento e erro têm mensagens distintas; não exige item, conta ou indicação privada; erro não mostra lista vazia como sucesso nem afirma descarte realizado.


## V21-CT-39 — Detalhe, cópia de endereço e mapa opcional

**Vínculos:** V21-RF-09, V21-RF-15; V21-RN-24.

**Precondições:** Local ativo com endereço contendo caracteres que exigem codificação; navegador com e sem permissão de área de transferência.

**Passos:** Abrir detalhe, voltar, copiar endereço; simular falha de cópia; se houver link de mapa, acioná-lo e bloquear o serviço externo.

**Resultado esperado:** Filtros/página preservados; feedback diz endereço copiado, não equipamento descartado; falha mantém texto selecionável. Link opcional usa só endereço público codificado e não pede localização. Diretório funciona sem mapa e nenhuma ação grava domínio.


## V21-CT-40 — Gestão autenticada e limitada aos próprios locais

**Vínculos:** V21-RF-11; V21-RN-01, V21-RN-16, V21-RN-21, V21-RN-22.

**Precondições:** Visitante, pessoa comum e operadores O1/O2 com mais de uma página de locais, incluindo inativos.

**Passos:** Tentar escopo=meus, detalhe de gestão, criação, edição e ativação sem sessão, como pessoa e como outro operador; O1 gerencia seu local e navega páginas próprias.

**Resultado esperado:** 401 sem sessão e 403 para pessoa nas operações protegidas; recurso alheio negado sem alteração. Restrição ao responsável ocorre antes da paginação; inativos próprios são acessíveis na gestão, nunca como fallback público. Não há fila ou comando de recebimento.


## V21-CT-41 — Inativação e alteração refletidas na consulta

**Vínculos:** V21-RF-09, V21-RF-11; V21-RN-11, V21-RN-14, V21-RN-16.

**Precondições:** Local próprio ativo, visto por visitante antes da alteração; sem vínculo com equipamento.

**Passos:** Atualizar categoria/endereço/horário; refazer busca; inativar, consultar lista e abrir detalhe anterior; reativar e consultar novamente.

**Resultado esperado:** Consultas subsequentes refletem alterações; inativo sai da lista e detalhe público retorna 404 com retorno útil na UI; reativação restaura visibilidade. Nenhum equipamento, aviso ou confirmação de recebimento é gerado.


## V21-CT-42 — Diretório não produz resultados ambientais

**Vínculos:** V21-RF-13; V21-RN-19, V21-RN-24.

**Precondições:** Ofertas concluídas e locais ativos; indicadores-alvo com origens identificadas.

**Passos:** Consultar lista/detalhe, copiar endereço e abrir mapa repetidamente; alterar número de locais ativos; consultar indicadores e concluir uma oferta em cenário separado.

**Resultado esperado:** Navegação repetida não altera doados/vendidos/total, não cria aviso e não muda `locais_ativos`; total considera somente doação/venda confirmadas; consultas não são contadas como entrega ou reciclagem. Evidência real em `tests/test_etapa19_coerencia.py`.


## V21-CT-43 — Retirado: preservação de descarte legado

Sem dados desse fluxo a conservar, não exigir snapshots de descarte, migração ou leitura compatível. A remoção das rotas/campos antigos é validada no contrato executável da Etapa 18; o ID não é reutilizado como novo cenário.


## V21-CT-44 — Entrada de descarte não cria uma oferta

**Vínculos:** V21-RF-03, V21-RF-09; V21-RN-02, V21-RN-04, V21-RN-24.

**Precondições:** Visitante sem item e pessoa autenticada, formulários de doação/venda disponíveis.

**Passos:** Acionar “Quero descartar” nas entradas pública e autenticada; tentar cadastro direto de novo item com modalidade de descarte no contrato-alvo.

**Resultado esperado:** Ambas as entradas levam ao diretório sem formulário de equipamento ou login obrigatório; cadastro direto inválido é rejeitado sem efeitos. Doação/venda continuam com cadastro, interesse e entrega bilateral; não surge endpoint substituto de entrega de descarte.


## Reprodução e critérios ainda não comprovados

Executar a suíte completa, contratos, navegação e jornadas reais; registrar comandos, data e resultado real. Não estimar contagem de testes. Simultaneidade sem intercalação instrumentada não prova todas as ordens; documentar precisamente o que foi exercitado. Índices e permissões devem ser verificados no bootstrap/roteamento reais. Esta revisão não exige nova coleção de descarte; não rodar povoamento ou migração para validar apenas documentos.
