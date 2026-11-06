# Modelo de dados — v2.1

## Estrutura implementada

O código das Etapas 9 a 15 utiliza seis coleções. As classes estão em `app/models/`; os repositórios convertem IDs para BSON ObjectId e datas para UTC. O JSON retorna identificadores como strings.

| Coleção | Campos e estruturas presentes |
|---|---|
| `usuarios` | `nome`, `email`, `tipo` (`pessoa`/`ponto_coleta`), `endereco` (`logradouro`, `numero`, `cep`, `cidade`, `complemento`), `senha_hash`, datas |
| `itens` | `titulo`, `descricao`, `categoria`, `marca`, `modelo`, `condicao`, `destino`, `valor`, `status`, `proprietario_id`, `especificacoes`, `historico`, referências de ponto/beneficiário/comprador, `destinacao_informada` e datas |
| `interesses` | `item_id`, `usuario_id`, `status`, `tentativa`, `motivo`, `preco_selecionado`, `resultado`, `combinacao`, `historico` e datas |
| `pontos_coleta` | `nome`, `endereco`, `categorias_aceitas`, `horario_atendimento`, `responsavel_id`, `ativo` e datas |
| `encaminhamentos` | `item_id`, `autor_id`, `ponto_id`, `status`, `motivo`, `historico` e datas |
| `notificacoes` | `usuario_id`, `item_id`, `interesse_id` opcional, `tipo`, `titulo`, `mensagem`, `evento_id`, `link`, `lida`, `data_leitura` e datas |

Histórico do item usa `etapa`, `status`, `data_evento`, `responsavel_id` e `observacao`. Históricos de interesse/encaminhamento usam `status`, `data_evento`, `ator_id` e `motivo`. A combinação contém local textual, previsão/observação opcionais, revisão, proponente/data e aceitante/data. Destinação informada contém tipo de local, textos opcionais e `informado_em`; a autoria é determinada pelo proprietário do item.

A seleção é registrada internamente em `itens.interesse_aceito_id`, preservado pelo repositório e não exposto como campo do modelo de resposta. A tentativa ativa é consultada em `encaminhamentos`, com índice parcial único por item em `entrega_prevista`; não há campo implementado `encaminhamento_ativo_id`. A entrega bilateral fica registrada nos estados e históricos, não em um subdocumento `entrega` do item.

Os nomes executáveis são `destino=revenda`, `status` e `valor` (número representado como float), não `modalidade=venda`, `situacao` e preço decimal. Não há campo genérico `versao`, ledger ou `id_operacao`. O índice de notificação é único por `evento_id`, `usuario_id`, `item_id`; `origem_tipo`/`origem_id` não são campos implementados.

Fontes: [modelos](../../app/models/), [repositórios](../../app/repositories/), [contratos atuais](../../docs/http-api.md) e [OpenAPI](../../docs/openapi.json). Proteções e comportamento precisam ser verificados no código/testes; uma tabela de campos não prova atomicidade de todas as operações.

## Desenho original preservado — não é o esquema executável

As seções abaixo preservam o modelo originalmente aprovado, inclusive campos e garantias ainda não implementados. São referência de projeto, não instrução de migração nem comprovação de entrega. Diferenças permanecem explícitas para não reduzir silenciosamente os critérios ao que o código já faz.

## Princípios

- MongoDB; IDs persistidos como BSON ObjectId, DTOs como strings; datas UTC em precisão BSON de milissegundos.
- `data_adicao` imutável, `data_modificacao` e `versao` controladas pelo servidor.
- Conta operacional é diferente de local físico; pessoa participa de operações sem trocar perfil.
- Separar condição física de situação de negócio; modalidade fixa no ciclo simplificado.
- Coleções propostas: `usuarios`, `itens`, `interesses`, `pontos_coleta`, `notificacoes` e nova `encaminhamentos`.
- Sem coleção de pagamentos, transportes, sessões ou chat. Combinação é subdocumento do interesse selecionado.

## Coleção `usuarios`

Preservar nome, email normalizado/único, hash, endereço e auditoria. `tipo` proposto: `pessoa` ou `ponto_coleta`. Não aceitar atribuição pública de operador. Participação é derivada de proprietario_id/usuario_id/responsavel_id.

Não converter automaticamente doador/beneficiario existentes nesta preparação. Manter hash fora de DTOs. Não acrescentar tratamento avançado de conta/privacidade ao escopo local.

## Coleção `itens`

| Campo | Tipo/propósito |
|---|---|
| `_id`, `proprietario_id` | Identidade e dono |
| `titulo`, `descricao`, `categoria`, `marca`, `modelo`, `especificacoes` | Características preservadas |
| `condicao` | Estado físico, independente da disponibilidade |
| `modalidade` | doacao, venda ou descarte |
| `situacao` | Estado permitido pela modalidade, conforme regras |
| `preco` | Decimal representado consistentemente ou unidade monetária inteira a fechar no contrato técnico; positivo para venda, null nas demais |
| `interesse_selecionado_id` | Relação ativa de oferta; null no descarte/sem seleção |
| `encaminhamento_ativo_id` | Tentativa ativa de descarte; null nas demais situações |
| `destinacao_informada` | Lugar indicado pelo autor (tipo_local, nome, cidade, observacao, autor e data); mutuamente exclusiva com tentativa ativa e visível apenas ao autor |
| `entrega` | Declaração do proprietário e recebimento do selecionado; null antes de ocorrerem |
| `historico` | Eventos acumulativos com ator, etapa, data e referências de origem |
| `versao`, datas | CAS e auditoria |

`entrega` contém quem declarou, quando, quem recebeu, quando e interesse de origem. Não receber esses atores/datas do cliente. Venda conserva preço selecionado no interesse; `preco` do item não muda durante reserva. Conclusão de descarte referencia a tentativa recebida no histórico, sem simular comprador/beneficiário.

Estados de oferta: rascunho/disponivel/reservado/aguardando_confirmacao/concluido/arquivado. Estados de descarte: aguardando_ponto/entrega_prevista/recebido/destinacao_informada/arquivado. Modalidade e estado são validados conjuntamente.

`destinacao_informada.tipo_local` aceita `ecoponto`, `cooperativa`, `comercio` ou `outro`; nome, cidade e observação são opcionais e livres. Esse subdocumento não é ponto de coleta: não recebe identificador de local, não entra em consultas de diretório, não é projetado em DTO de terceiro ou de operador e não alimenta o indicador de recebimentos. O autor pode removê-lo enquanto o item não estiver arquivado, mantendo evento no histórico. Registro de tentativa e indicação não coexistem no mesmo item.

Enquanto `situacao=rascunho`, a modalidade pode ser corrigida pelo proprietário, com evento de histórico. Depois de publicada, ou existindo interesse ou vínculo de descarte, a troca exige arquivar e cadastrar nova intenção; conviver com modalidade alterada e vínculo antigo não é permitido.

Não adicionar coleção de anúncios neste incremento. `oferta` é uma visão de item com modalidade apropriada e publicação. O identificador público permanece item_id.

## Coleção `interesses`

Uma relação por item/pessoa, preservando índice único. Campos: item_id, usuario_id, status, tentativa (inteiro positivo), preco_selecionado (venda), combinacao, historico, versao e datas.

Estados: pendente, selecionado, recusado, cancelado, encerrado. `resultado` distingue encerramento por conclusão ou arquivamento. Nova tentativa reutiliza relação, incrementa tentativa e preserva eventos antigos. Sem multiplicar interesses ativos para a mesma pessoa/item.

`combinacao`: revisao, local_texto, previsao opcional, observacao, proposto_por, proposto_em, aceito_por/aceito_em opcionais. Proponente/aceitante vêm da sessão. Revisão nova invalida aceite. Valores antigos ficam no histórico pertinente, não acessíveis como combinação atual de outro participante.

## Coleção `pontos_coleta`

Preservar nome, responsavel_id, endereco público do local, categorias_aceitas, horario_atendimento, auditoria. Acrescentar `ativo` booleano, padrão true no cadastro válido. Inativar não apaga local ou tentativas.

Mudança de endereço/horário com previsões ativas gera aviso. Referência aponta para o local atual; para registro histórico de recebimento, evento pode conter snapshot do nome/endereço público do ponto na confirmação, nunca endereço privado da pessoa. Isso é uma mudança explícita frente à preferência v2.0 de referência sem cópia: o snapshot é só evidência histórica pública, não fonte para escolha futura.

## Coleção `encaminhamentos`

| Campo | Regra |
|---|---|
| `_id`, `item_id`, `ponto_id`, `autor_id` | Referências a equipamento, local e proprietário |
| `status` | entrega_prevista, recebido, cancelado ou nao_recebido |
| `motivo` | Obrigatório ao cancelar/trocar/não receber |
| `substitui_id` | Tentativa anterior quando criada por troca |
| `recebido_por`, `recebido_em` | Somente confirmação do operador |
| `historico`, `versao`, datas | Eventos e controle de concorrência |

Cada troca produz tentativa nova; item aponta só para a ativa. Cancelar/receber limpa vínculo ativo; histórico preserva o identificador final. Identidade do autor é derivada do item e da sessão. Não criar campos de motorista/frete/agendamento.

## Coleção `notificacoes`

Preservar conteúdo gerado pelo servidor, destinatário, evento e leitura idempotente. Relação de origem não depende mais de todo aviso possuir interesse: adicionar `origem_tipo` (interesse, item, encaminhamento, ponto), `origem_id` e referências opcionais correspondentes.

A chave lógica é evento_id + usuario_id + origem_tipo + origem_id. Substitui o pressuposto de que aviso sempre nasce de interesse; definir conversão de índices somente na implementação. Link interno é montado por tipo/id, nunca URL arbitrária enviada pelo usuário.

## Índices e atomicidade propostos

- usuarios: email único.
- itens: proprietário/situação; modalidade/situação/data/ID para catálogo; interesses e tentativas apontadas indexadas conforme consultas.
- interesses: `(item_id, usuario_id)` único; consultas por autor/status e item/status.
- encaminhamentos: índice único parcial em item_id para `status=entrega_prevista`; filas por ponto/status/data/ID; histórico por item/data/ID.
- pontos: responsável/ativo; categorias e cidade conforme consultas normalizadas.
- notificações: tupla lógica única; destinatário/lida/data/ID.

Selecionar, declarar/confirmar entrega, liberar reserva, criar/trocar/cancelar/receber tentativa e emitir avisos devem usar unidade transacional com CAS. Criar previsão deve disputar escrita no item e no ponto contra recebimento/inativação/alteração de categorias; leitura de snapshot sozinha não é prova suficiente.

`id_operacao` de comandos tem chave por item + ator + operação, ou ponto + ator + operação para ativação/inativação, e fingerprint do payload. Evento persistido no agregado registra resultado mínimo para consulta/reenvio. Troca deixa a chave também no evento do item. Não usar memória do processo como fonte de idempotência. Se o desenho final exigir ledger separado, revisar a decisão sobre a coleção de tentativas e o número de coleções antes de implementar, não acrescentar uma sétima implicitamente.

Arrays de histórico já são uma escolha da PoC; crescimento ilimitado é limite reconhecido, não prometer escala de produção. Paginação de filas não pode depender de carregar arrays/listas globais no frontend.

## DTOs e acesso

Catálogo inclui características e cidade, não combinação ou endereço pessoal. Gestão do próprio item é completa; negociação selecionada acessa combinação; fila do operador contém apenas tentativas dos seus locais. Não revelar dados de interessados concorrentes. Eventos antigos precisam de projeção reduzida quando o acesso especial termina.

## Dados v2.0 e implantação

`destino=revenda` não é o novo nome `modalidade=venda`; `status=recondicionado` não é `situacao=disponivel` sem avaliar seleção/entrega existentes. Definir mapeamento e casos de teste antes da conversão. Nenhum script desta preparação altera o banco populado. Recriação seletiva de demonstração também exige autorização.
