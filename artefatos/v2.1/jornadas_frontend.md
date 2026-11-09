# Jornadas e funções de frontend — v2.1

Experiência-alvo da revisão de descarte como diretório. A Etapa 16 entrega somente a base HTTP pública e preservação de registros. As telas e controles de J-03 ainda não foram implementados; o frontend mantém o processo antigo até as etapas seguintes. Doação e venda preservam suas jornadas.

## Interface de referência e diferenças para o alvo

- Páginas HTML em `frontend/`, catálogo, gestão de itens, interesses, pontos e avisos, com controles para reserva, combinação, entrega bilateral e indicação de lugar.
- O catálogo carrega até 100 registros sem navegação por páginas. `history.replaceState` preserva filtros; não há página selecionada para restaurar.
- Avisos abrem a tela correspondente, não um deep link garantido para cada item/tentativa.
- O bloqueio de duplo envio existe em controles específicos, não foi aplicado uniformemente a todas as mutações. Erros focam a região de mensagens; isso não é foco automático no primeiro campo inválido.
- Resposta de rede não confirmada orienta recarregar. Não há consulta por `id_operacao` ou reconciliação automática persistida.
- Ponto inativo bloqueia novas previsões; entregas previstas anteriormente continuam concluíveis. Este é o comportamento executável, em divergência com o bloqueio de recebimento descrito no esboço original de J-04.

Ver [contratos atuais](../../docs/http-api.md), [testes de frontend](../../tests/test_frontend.py), [Selenium](../../tests/test_selenium_frontend.py) e [jornadas executáveis](../../scripts/validar_jornadas_v2.py). Esses testes não constituem uma auditoria exaustiva de acessibilidade.

## Experiência-alvo revisada

Os nomes visíveis devem traduzir conceitos de negócio, sem expor códigos internos. Ver [regras](regras_de_negocio.md).


## Mapa de navegação

| Visitante sem sessão | Pessoa autenticada | Operador autenticado |
|---|---|---|
| Início e “Onde descartar” | Catálogo de ofertas e “Onde descartar” | “Onde descartar” e Meus locais |
| Filtros e detalhe de locais ativos | Meus itens e Interesses | Cadastro/edição e ativação/inativação dos próprios locais |
| Copiar endereço; mapa opcional | Avisos e perfil | Perfil e avisos anteriores autorizados, sem fila de descarte |

“Quero descartar” leva ao diretório sem passar por cadastro/login. As entradas “Quero doar” e “Quero vender” mantêm o fluxo autenticado de ofertas. O endereço da página pública deve poder ser aberto diretamente em uma sessão anônima. A consulta não recebe dados pessoais de quem procura o local.

## J-01 — Publicar e explorar

1. Início oferece “Quero doar”, “Quero vender” e “Quero descartar”.
2. Cadastro mostra identificação, categoria, condição e descrição; especificações em pares chave/valor compreensíveis, sem exigir JSON.
3. Venda pede preço positivo; doação não pede preço. Descarte não é modalidade do formulário de item.
4. Revisão mostra salvar rascunho ou publicar oferta. “Quero descartar” abre J-03, sem salvar equipamento. Enquanto rascunho, a pessoa pode corrigir entre doação e venda; depois de publicada, a mudança exige arquivar e cadastrar nova oferta.
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

## J-03 — Onde descartar, sem cadastrar equipamento

1. Visitante abre a entrada pública, sem cookie ou conta. Pessoa já autenticada usa a mesma consulta.
2. A tela apresenta cidade e categoria do eletrônico como filtros opcionais. A cidade pode ser digitada; usar endereço do perfil só pode ser conveniência explícita para pessoa autenticada, nunca precondição ou localização automática.
3. A busca mostra locais ativos que atendem a todos os filtros. Paginação é aplicada pela API e alcançável pela interface; trocar filtro volta à primeira página.
4. Cada cartão mostra nome, endereço público, categorias aceitas e horário informado. Sem horário disponível, informar essa ausência, sem afirmar que o local está aberto agora.
5. “Ver detalhes” abre informação do local; voltar mantém filtros/página. “Copiar endereço” dá feedback de cópia, não de descarte concluído; se não puder copiar, manter o endereço selecionável.
6. Pode haver “Abrir endereço no mapa” como link opcional, montado com endereço público codificado. Abre somente por ação da pessoa; não carrega mapa embutido nem solicita posição, chave de serviço ou cadastro. A consulta continua útil sem esse recurso.
7. Outro local é escolhido simplesmente consultando outro cartão. Não há confirmação final, entrega prevista, troca/cancelamento de tentativa ou recebimento pelo operador.

### Estados da consulta

- **Carregando:** mostrar andamento sem apagar filtros ou afirmar resultado vazio.
- **Vazio:** “Nenhum local encontrado para estes filtros. Tente outra cidade ou categoria.” Oferecer limpar/alterar filtros; não oferecer cadastro de equipamento ou indicação privada como fallback.
- **Erro:** explicar que a consulta não foi concluída e permitir tentar novamente; não mostrar “nenhum ponto” como se fosse um resultado confirmado.
- **Local inativado após a listagem:** ao atualizar/abrir o detalhe, informar indisponibilidade e voltar à lista preservando filtros. O diretório não garante capacidade ou aceite de um atendimento físico.

Lista, detalhe, filtros, cópia e mapa não criam documento de domínio, aviso ou indicador. Não usar “Recebemos seu equipamento”, “Entrega prevista”, “Reciclado” ou equivalente como resultado de navegação.

## J-04 — Operador mantém seus locais

1. Operador entra com sessão e abre “Meus locais”. A gestão não é liberada junto com a leitura pública.
2. Lista paginada contém somente locais próprios, incluindo inativos quando solicitado; a API restringe responsável antes da paginação.
3. Cadastra ou edita nome, endereço público, categorias aceitas e horário. O responsável vem da sessão; dados privados da conta não são copiados para o diretório.
4. Ativa/inativa local com efeito explicado: entrar/sair das consultas públicas subsequentes. Não aparece confirmação de recebimento, impossibilidade de descarte nem fila de equipamentos.
5. Conflito ou falha mantém o formulário para reconciliação/recarga, sem anunciar sucesso indevido. Referências antigas não são removidas para permitir a edição.

A estratégia de compatibilidade de registros legados deverá ser definida antes da implementação; esta jornada não manda concluir ou cancelar tentativas antigas.

## J-05 — Avisos e indicadores

Avisos ativos de doação/venda apontam para item ou negociação. Consulta e gestão do diretório não disparam avisos de descarte; avisos legados não ganham acesso público. Ao abrir registro encerrado, mostrar o que ocorreu e somente informações autorizadas. Não reconstruir ação antiga com base no texto do aviso.

Início da pessoa apresenta pendências antes dos indicadores: “Você precisa confirmar recebimento”, “Há interessados na sua oferta”. Operador vê a gestão dos locais, sem pendências de descarte decorrentes da nova consulta.

Rótulos-alvo de resultado: “Doações recebidas” e “Vendas concluídas com recebimento confirmado”. Eventual quantidade de locais ativos é informação do diretório, separada de equipamentos. Não apresentar consulta, cópia de endereço ou mapa como entrega/reciclagem; não somar descarte legado ao total novo de ofertas.

## Padrões obrigatórios de usabilidade

- Só esconder campo dependente depois de preservar seu significado; não manter preço de venda oculto vazando para doação; não pedir características do item na consulta de descarte.
- Validar junto do campo e manter conteúdo em erro; mover foco para primeiro erro.
- Durante envio bloquear repetição e mostrar andamento; ao falhar, restaurar ação quando seguro.
- Em resposta perdida, consultar resultado pela chave de operação antes de repetir com chave nova.
- `409`: explicar que registro mudou, oferecer recarga e preservar texto não enviado quando possível; não sobrescrever versão automaticamente.
- Vazio, erro e carregamento são estados diferentes; erro não deve aparecer como “nenhum item”.
- Paginar resultados de consultas e listas de gestão; manter ordenação estável, filtros e página ao voltar. A consulta pública não é uma fila de entregas.
- Diálogo acessível por teclado, foco devolvido ao acionador, rótulos e região de mensagens legíveis; cabeçalho fixo não pode bloquear clique ou foco.
- Testar largura pequena e jornada completa sem depender de tabela larga ou hover.

## Esboço textual do cartão de local

```text
Onde descartar
Cidade: [____________]  Categoria: [Todas / tipo de eletrônico]
[Buscar] [Limpar filtros]

Ponto Centro
Endereço público do local • Cidade
Aceita: monitores, notebooks
Atendimento: horário cadastrado / não informado
[Ver detalhes] [Copiar endereço] [Abrir endereço no mapa — opcional]

[Anterior] [Próxima]
```

Esboço de especificação, não tela já implementada. Não mostra equipamento do visitante, estado de entrega nem confirmação. Informação do diretório não é certificação de descarte realizado.
