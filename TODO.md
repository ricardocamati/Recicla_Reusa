# TODO — revisão v2.1: Onde descartar

O trabalho ativo é a **Parte III — descarte como diretório público**, ainda não implementada. As Partes I e II preservam o histórico das Etapas 1 a 15; suas marcações não comprovam os critérios revisados nem tornam obrigatório manter o fluxo de descarte substituído.

- Escopo e critérios atuais: [artefatos/v2.1/](artefatos/v2.1/README.md).
- Requisitos, regras e cenários retirados continuam identificados nos artefatos, sem voltar como tarefas futuras.
- Marco anterior v2.0: [artefatos/v2.0/](artefatos/v2.0/README.md).

Esta atualização é somente planejamento. **Não fazer commit agora:** o TODO revisado deve acompanhar o primeiro commit de implementação da Parte III, com as tarefas efetivamente realizadas e testadas. Não criar commit isolado de planejamento, iniciar implementação ou publicar por causa desta edição.

## Como cada etapa fecha

1. Branch própria a partir da `main` atualizada (`feat/<etapa>`).
2. Commits coerentes — normalmente um, incluindo código, testes e documentação da etapa.
3. Validação local com a suíte completa e o verificador da etapa.
4. Push da branch e abertura do PR; revisão antes do merge.
5. Merge na `main` **somente com autorização explícita**, e só então a próxima branch.

Push, PR e merge não decorrem de autorização para editar ou commitar. Sem force-push e sem commit direto na `main`.

# Parte I — histórico da v2.0

## Etapa 1 — Usuários com endereço aninhado

Referências: V2-RF-01, V2-RF-02, V2-RF-15 · V2-CT-01 a V2-CT-05.

- [x] Migrar o endereço de campos planos para subdocumento em `usuarios`, no modelo, schemas, mapper e repositório.
- [x] Ajustar cadastro, consulta e atualização para o novo contrato, mantendo `tipo` imutável.
- [x] Manter o contrato de sessão, cookie e autorização por identidade sem alteração.
- [x] Atualizar testes de usuários e a documentação HTTP afetada.

## Etapa 2 — Itens: especificações, histórico e consultas

Referências: V2-RF-03, V2-RF-04, V2-RF-05, V2-RF-10 · V2-CT-06 a V2-CT-09, V2-CT-15, V2-CT-16, V2-CT-22.

- [x] Acrescentar `especificacoes` e `historico` aninhados ao item, com datas UTC em precisão de milissegundos.
- [x] Registrar cada transição de status no histórico, sem permitir salto inválido.
- [x] Implementar filtros e paginação do catálogo sem expor endereço do proprietário.
- [x] Proteger atualização e exclusão por propriedade, com conflito explícito quando o status mudou na concorrência.
- [x] Atualizar testes de item, repositório e API.

## Etapa 3 — Pontos de coleta

Referências: V2-RF-08, V2-RF-09 · V2-CT-13, V2-CT-14.

- [x] Criar a coleção `pontos_coleta`, com endereço aninhado, categorias aceitas e horário.
- [x] Expor CRUD autenticado, restrito à conta responsável pelo ponto.
- [x] Garantir que a conta `ponto_coleta` continue provisionada por comando local.
- [x] Impedir exclusão de responsável com ponto vinculado e recusar ponto incompatível no encaminhamento.
- [x] Criar índices e testes de integridade referencial.

## Etapa 4 — Interesses

Referências: V2-RF-06, V2-RF-07 · V2-CT-10, V2-CT-11, V2-CT-12.

- [x] Criar a coleção `interesses` relacionando item e interessado, com status e datas.
- [x] Registrar interesse, listar próprios e recebidos, e permitir decisão do proprietário.
- [x] Impedir interesse do próprio dono e segunda relação para o mesmo par item/pessoa.
- [x] Reservar a doação de forma transacional ao aceitar, com efeito e histórico na mesma unidade.
- [x] Cobrir com testes de API, repositório e concorrência.


## Etapa 5 — Fluxos de doação, descarte e revenda

Referências: V2-RF-11, V2-RF-12, V2-RF-13 · V2-CT-17 a V2-CT-21.

- [x] Definir as transições de cada destino e validar saltos e estados terminais.
- [x] Encaminhar descarte para ponto de coleta cadastrado e compatível com a categoria.
- [x] Exigir valor não negativo e restrito à revenda, sem preço em doação ou descarte.
- [x] Concluir doação, descarte e revenda uma única vez, gravando item e histórico na mesma unidade; os indicadores entram na Etapa 7.
- [x] Testar transições inválidas, segunda conclusão e ausência de escrita parcial.


## Etapa 6 — Notificações

Referências: V2-RF-17 · V2-CT-26 a V2-CT-30.

- [x] Criar a coleção `notificacoes` e o índice único por evento, destinatário e item.
- [x] Emitir avisos na mesma transação da mudança que os origina.
- [x] Expor caixa de entrada com listagem e marcação de leitura, restrita ao destinatário.
- [x] Não notificar quem não tem vínculo com o item nem duplicar aviso do mesmo evento.
- [x] Testar emissão, privacidade, idempotência e rollback.


## Etapa 7 — Indicadores e frontend das novas telas

Referências: V2-RF-14, V2-RF-16 · V2-CT-23, V2-CT-24 · [docs/http-api.md](docs/http-api.md).

- [x] Implementar consulta autenticada de indicadores de itens concluídos por destino.
- [x] Criar as telas de interesses, pontos e notificações em HTML e JavaScript modular, sem build.
- [x] Manter `credentials: "include"` e renderização segura de texto.
- [x] Regenerar a OpenAPI do runtime e confrontá-la com a especificação versionada, registrando diferenças.
- [x] Cobrir as telas com Selenium e atualizar os contratos documentados.


## Etapa 8 — Fechamento da v2.0

Referências: V2-RNF-05 a V2-RNF-10, V2-CT-25 · [matriz](artefatos/v2.0/matriz_rastreabilidade.md).

- [x] Rodar a suíte completa e os verificadores de integração em stack e volume isolados.
- [x] Executar as três jornadas (doação, descarte e revenda) pela interface em Docker.
- [x] Validar auditoria temporal e versão em todas as coleções.
- [x] Confirmar que a limpeza de fixtures é seletiva e comprovada.
- [x] Atualizar evidências, matriz, README e registro da entrega; conferir links e identificadores.

# Parte II — histórico da implementação inicial v2.1

As Etapas 9 a 15 registram o desenho implementado antes da revisão do descarte. Suas referências e caixas são históricas; requisitos/casos agora retirados não voltam como trabalho ativo. A Parte III substitui somente as frentes indicadas no [escopo revisado](artefatos/v2.1/README.md), preservando doação/venda e os dados anteriores.

## Etapa 9 — Conta única de pessoa

Referências: V21-RF-01 · V21-CT-01, V21-CT-29.

- [x] Substituir os perfis públicos de doador e beneficiário por uma conta de pessoa, com operador separado.
- [x] Ajustar autorização por operação, mantendo o operador restrito aos próprios locais.
- [x] Migrar interesses e itens existentes para a nova regra de papéis, preservando histórico.
- [x] Atualizar testes de permissão e a documentação de contratos.

## Etapa 10 — Catálogo de ofertas e cadastro por intenção

Referências: V21-RF-02, V21-RF-03, V21-RF-14 · V21-CT-02, V21-CT-03, V21-CT-04, V21-CT-24.

- [x] Separar modalidade de condição física e fixar a modalidade no ciclo do item.
- [x] Publicar catálogo apenas com ofertas disponíveis, excluindo descarte, rascunho, arquivado e concluído.
- [x] Guiar o cadastro em intenção, características e revisão, com rascunho e publicação.
- [x] Exibir Ativos, Em andamento e Encerrados, com arquivamento sem apagar referências.
- [x] Atualizar testes de catálogo, cadastro e arquivamento.

## Etapa 11 — Interesse, retomada e reserva

Referências: V21-RF-04, V21-RF-05 · V21-CT-05 a V21-CT-08.

- [x] Permitir retomada de interesse cancelado pelo autor, com histórico, sem contornar recusa.
- [x] Garantir uma relação por par item/pessoa e exibir interessados nas próprias ofertas.
- [x] Tornar a reserva explícita, única e reversível antes da declaração de entrega.
- [x] Tratar desistência e não comparecimento liberando o item.
- [x] Cobrir concorrência de reserva e conflitos com testes reais.

## Etapa 12 — Combinação, entrega bilateral e venda

Referências: V21-RF-06, V21-RF-07, V21-RF-08 · V21-CT-09 a V21-CT-12.

- [x] Oferecer combinação estruturada (local, previsão opcional e observação) com novo aceite a cada alteração.
- [x] Implementar declaração de entrega e confirmação de recebimento como duas etapas distintas.
- [x] Permitir venda direta de usado, congelando o preço no aceite e exigindo liberação para alterá-lo.
- [x] Atualizar indicadores apenas na confirmação, contando uma vez por item.
- [x] Testar pendência sem confirmação, terceiro não autorizado e reenvio da mesma operação.

## Etapa 13 — Descarte guiado e operação do ponto

Referências: V21-RF-09, V21-RF-10, V21-RF-11 · V21-CT-13 a V21-CT-21.

- [x] Guiar a escolha do ponto por cidade e categoria, sem prometer proximidade.
- [x] Registrar entrega prevista somente após confirmação, mantendo o cadastro salvo quando não houver ponto compatível.
- [x] Permitir cancelar e trocar ponto antes do recebimento, preservando tentativas anteriores.
- [x] Dar ao operador filas de previstas e recebidas, com filtro por local, paginação e motivo de impossibilidade.
- [x] Tratar inativação de ponto com previsões ativas e disputa entre previsão e mudança de categoria.

## Etapa 14 — Indicação de lugar pelo autor

Referências: V21-RF-16, V21-RNF-07 · V21-CT-31 a V21-CT-34.

- [x] Permitir indicar lugar não cadastrado com tipo de local estruturado e dados opcionais.
- [x] Encerrar o item como destinação informada, sem confirmação de terceiro e sem criar ponto de coleta.
- [x] Restringir a indicação ao autor, sem exposição a operadores ou terceiros.
- [x] Permitir desfazer enquanto o item não estiver arquivado, sem perder histórico.
- [x] Separar, nos indicadores, recebimento no ponto de destinação apenas informada.

## Etapa 15 — Avisos, navegação e fechamento da v2.1

Referências: V21-RF-12, V21-RF-13, V21-RF-15 · V21-CT-22, V21-CT-23, V21-CT-25 a V21-CT-28, V21-CT-30 · [matriz](artefatos/v2.1/matriz_rastreabilidade.md).

- [x] Dirigir cada aviso a quem precisa agir, com link interno e sem duplicação por evento.
- [x] Corrigir indicadores para separar ofertas, pendências e conclusões confirmadas.
- [x] Mostrar próximas ações por ator, estados vazios úteis, foco acessível e bloqueio de duplo envio.
- [x] Preservar filtros e página ao voltar do detalhe e oferecer reconciliação quando a resposta se perder.
- [x] Rodar as três jornadas em stack isolada, atualizar evidências, matriz e contratos.

# Parte III — v2.1: descarte como diretório público

Executar em ordem, sem reabrir as etapas históricas. A especificação desta parte já está nos [artefatos v2.1](artefatos/v2.1/README.md); os itens abaixo são implementação e validação ainda pendentes. Não marcar tarefa concluída por existir texto de requisito, cenário escrito ou teste do descarte antigo.

Nesta revisão, descarte não exige conta ou item. Não recriar entrega prevista, troca/cancelamento de tentativa, recebimento pelo operador ou indicação privada como alternativa, endurecimento ou etapa posterior. Não incluir pagamentos, transporte, agendamento, mapa embutido ou geolocalização.

## Etapa 16 — Consulta pública e proteção dos dados anteriores

Referências: V21-RF-09, V21-RNF-01, V21-RNF-08 · V21-RN-11, V21-RN-21, V21-RN-24, V21-RN-25 · V21-CT-35, V21-CT-36, V21-CT-37, V21-CT-43 · [modelo](artefatos/v2.1/modelo_dados.md), [contratos](artefatos/v2.1/contratos_http.md).

- [x] Definir o tratamento dos itens de descarte, encaminhamentos, indicações e referências existentes, separando seu histórico da experiência nova, sem excluir, converter em oferta ou concluir registros automaticamente.
- [x] Liberar lista e detalhe de locais ativos sem sessão, mantendo gestão e demais rotas protegidas; local inexistente ou inativo não é exposto pelo detalhe público.
- [x] Criar projeção pública com apenas identificador, nome, endereço do local, categorias e horário; excluir responsável, endereço pessoal, equipamentos e dados legados das respostas públicas.
- [x] Aplicar cidade, categoria e situação ativa antes da paginação, com ordenação estável por nome/ID e validação de filtros; não permitir revelar inativos por parâmetros públicos.
- [x] Garantir que lista, detalhe e filtros não criem documento de domínio, aviso ou resultado de descarte, nem dependam de ID de equipamento.
- [x] Adicionar testes de API e MongoDB real para leitura anônima, projeção, filtros, paginação e preservação de snapshots/referências em bancos próprios de teste.

## Etapa 17 — Tela pública “Onde descartar”

Referências: V21-RF-03, V21-RF-09, V21-RF-15, V21-RNF-03 · V21-RN-24 · V21-CT-35, V21-CT-36, V21-CT-38, V21-CT-39, V21-CT-44 · [jornada J-03](artefatos/v2.1/jornadas_frontend.md).

- [x] Criar a entrada pública e autenticada de “Onde descartar”, acessível por endereço direto sem redirecionar ao login ou formulário de item.
- [x] Implementar filtros opcionais e cumulativos por cidade/categoria, controles de paginação e detalhe com retorno preservando filtros/página; trocar filtro reinicia a paginação.
- [x] Exibir nome, endereço público, categorias aceitas e horário informado; não inventar horário de atendimento, proximidade ou garantia de recebimento.
- [x] Oferecer cópia de endereço com feedback correto e texto selecionável quando a cópia não estiver disponível. Se houver link opcional de mapa, usar somente o endereço público codificado e manter toda a consulta funcional sem serviço externo.
- [x] Distinguir carregamento, resultado vazio, erro e local que ficou indisponível; oferecer nova tentativa ou mudança de filtros sem cadastro ou indicação privada como fallback.
- [x] Validar a consulta por Selenium em sessão anônima, teclado e telas pequenas, incluindo resultados em páginas posteriores e ausência de efeitos persistidos.

## Etapa 18 — Gestão dos locais e retirada do processo antigo

Referências: V21-RF-03, V21-RF-11, V21-RF-14, V21-RNF-08 · V21-RN-14, V21-RN-16, V21-RN-17, V21-RN-22, V21-RN-25 · V21-CT-04, V21-CT-24, V21-CT-29, V21-CT-40, V21-CT-41, V21-CT-43, V21-CT-44.

- [ ] Separar consulta pública da gestão autenticada de locais próprios, inclusive inativos; restringir responsável antes da paginação e não fazer fallback público quando a autorização falhar.
- [ ] Manter cadastro, edição e ativação/inativação pelo responsável, com identidade derivada da sessão; refletir alterações nas consultas seguintes sem remover referências antigas.
- [ ] Retirar descarte das opções de novo cadastro de item na interface e na API, direcionando “Quero descartar” ao diretório e preservando cadastro/gestão de doação e venda.
- [ ] Retirar do novo produto filas e ações de entrega prevista, troca, cancelamento, recebimento e destinação informada; descontinuar os comandos antigos conforme o tratamento de legado definido na Etapa 16, sem substituí-los por outro rastreamento de descarte.
- [ ] Preservar consulta histórica autorizada dos registros anteriores conforme a estratégia definida, sem publicar indicações privadas ou simular operações para encerrá-las.
- [ ] Testar negação de gestão sem sessão, por pessoa comum e por operador alheio, visibilidade ativo/inativo, proteção do legado e regressão de arquivamento/entrega bilateral das ofertas.

## Etapa 19 — Avisos, indicadores e demonstração coerentes

Referências: V21-RF-07, V21-RF-12, V21-RF-13 · V21-RN-18, V21-RN-19, V21-RN-24, V21-RN-25 · V21-CT-22, V21-CT-23, V21-CT-35, V21-CT-42, V21-CT-43.

- [ ] Retirar emissão de avisos do fluxo de descarte descontinuado e garantir que consulta, cópia, mapa e gestão do diretório não produzam esses avisos; preservar a privacidade dos avisos históricos.
- [ ] Ajustar contrato e consumidores dos indicadores para resultados de doação/venda confirmadas; total de conclusões não soma descarte legado nem contagem de consultas.
- [ ] Retirar da experiência nova rótulos de equipamento recebido/indicado/reciclado a partir do diretório. Se houver quantidade de locais ativos, apresentá-la separada de resultados de equipamentos.
- [ ] Adaptar o script de demonstração e seus testes para os cenários novos de locais consultáveis e ofertas, sem exigir recriar banco ou encerrar ciclos antigos. Aplicação sobre demonstração existente continua dependente de autorização própria.
- [ ] Testar navegação repetida sem alteração de resultados, confirmação única de doação/venda e reexecução aditiva da demonstração em banco de teste, sem duplicação ou modificação de documentos anteriores.

## Etapa 20 — Validação integrada e documentação do executável

Referências: V21-RNF-02, V21-RNF-03, V21-RNF-04, V21-RNF-05, V21-RNF-06, V21-RNF-08 · V21-CT-28, V21-CT-29, V21-CT-30, V21-CT-35, V21-CT-36, V21-CT-37, V21-CT-38, V21-CT-39, V21-CT-40, V21-CT-41, V21-CT-42, V21-CT-43, V21-CT-44 · [matriz](artefatos/v2.1/matriz_rastreabilidade.md).

- [ ] Adaptar o verificador das três jornadas para doação, venda e consulta anônima de descarte, sem confirmação de recebimento em ponto na terceira jornada.
- [ ] Executar as jornadas em stack/volume próprios, conferir dados e indicadores antes/depois da consulta e comprovar limpeza seletiva das fixtures.
- [ ] Rodar a suíte completa com integração real, Selenium e medição configurada; distinguir cenários realmente executados de ignorados e preservar as evidências em local ignorado, sem novos relatórios de verificação em `docs/`.
- [ ] Atualizar README principal, arquitetura, contratos, OpenAPI gerada e instruções de demonstração para o comportamento efetivamente implementado, sem reapresentar campos/rotas planejados como executáveis.
- [ ] Conciliar os artefatos e a matriz com código e testes finais, preservando limites não comprovados e os IDs retirados, sem reutilizar evidência do fluxo anterior como aprovação desta revisão.
- [ ] Marcar somente tarefas comprovadas e incluir o TODO no respectivo commit de implementação; publicação e merge continuam separados e sujeitos a autorização explícita.
