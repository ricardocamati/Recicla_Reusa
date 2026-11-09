# Modelo de dados — v2.1

## Modelo-alvo revisado — implementação parcial na Etapa 16

Descarte é consulta de `pontos_coleta`, não cadastro ou estado de `itens`. Não criar nova coleção de visitas, intenções, encaminhamentos ou comprovantes para usar o diretório. As estruturas de doação/venda permanecem; os nomes originalmente propostos de oferta continuam distintos dos nomes do runtime, como indicado ao final.

### Coleções participantes do novo fluxo

| Coleção | Papel no alvo |
|---|---|
| `usuarios` | Conta de pessoa/operador; gestão deriva identidade da sessão |
| `itens` | Novas ofertas de doação/venda, com especificações e histórico |
| `interesses` | Relação item/pessoa, seleção, combinação e confirmação de oferta |
| `pontos_coleta` | Diretório de locais mantidos pelo responsável |
| `notificacoes` | Avisos privados das operações de doação/venda |

`encaminhamentos` e os campos de descarte anteriores são **legado preservado**, não uma sexta coleção que o novo diretório precise alimentar. A existência física desses dados não significa que o fluxo retirado continue obrigatório. Este documento não remove coleções ou índices.

### Pontos de coleta e projeções

| Campo persistido | Regra-alvo |
|---|---|
| `_id` | Identidade do local; string `id` no JSON |
| `nome` | Nome público do estabelecimento/local |
| `endereco` | Subdocumento do endereço público do local, não o endereço da conta responsável |
| `categorias_aceitas` | Lista de categorias de eletrônicos aceitas; fonte do filtro por categoria |
| `horario_atendimento` | Horário cadastrado; a interface informa quando não estiver disponível, sem inventar atendimento |
| `responsavel_id` | Referência a `usuarios`; interna à gestão e omitida do DTO público |
| `ativo` | Determina participação no diretório público |
| Datas e `versao` proposta | Auditoria/concorrência das alterações de gestão; não precondições de leitura |

A lista e o detalhe públicos retornam somente `id`, `nome`, `endereco`, `categorias_aceitas` e `horario_atendimento`. Não retornar usuário responsável, e-mail privado, senha/hash, endereço pessoal, equipamentos, histórico de entregas ou indicações legadas. A gestão autenticada pode receber o estado ativo/inativo, datas e a versão que precisar editar.

Filtrar `ativo=true`, cidade e categoria antes da paginação. Ordem estável por nome e `_id`. Índices devem atender consultas por ativo/cidade/categoria e responsável na gestão; confirmar o plano real antes de declarar otimização comprovada. Não armazenar coordenadas ou resultados de distância para essa revisão.

### Ofertas, relações e histórico preservados no desenho

- `usuarios`: nome, e-mail normalizado/único, hash, endereço aninhado e datas; tipos `pessoa`/`ponto_coleta`; não aceitar autoatribuição de operador.
- `itens`: características, condição física, `especificacoes`, modalidade proposta `doacao`/`venda`, situação, preço, proprietário, interesse selecionado, histórico, datas e versão proposta. Descarte deixa de ser uma modalidade de novo cadastro.
- Doação usa preço nulo; venda usa valor positivo. A representação decimal ou em unidade monetária inteira continua uma diferença a fechar no contrato de implementação, não mudança autorizada por esta edição documental.
- `entrega` proposta é de doação/venda: declaração do proprietário e confirmação do selecionado, com atores/datas do servidor. O runtime registra isso nos estados/históricos, não nesse subdocumento.
- `interesses`: unicidade item/pessoa, status, tentativa, motivo, preço selecionado, combinação revisada/aceita e histórico. Proponente/aceitante são derivados da sessão.
- `notificacoes`: destinatário, evento, leitura idempotente e link interno. A origem proposta pode referenciar item/interesse de oferta, mas não gera eventos de descarte por navegação. O desenho de `origem_tipo`/`origem_id` continua distinto do documento executável.
- Índices de e-mail e relação item/pessoa continuam únicos; consultas de ofertas, interesses e avisos mantêm restrição de identidade antes de paginar. Unicidade de eventos deve ser verificada no bootstrap.
- MongoDB usa BSON ObjectId nas referências e datas UTC na precisão de milissegundos; `data_adicao` é imutável.
- Selecionar/liberar e declarar/confirmar entrega de oferta devem preservar atomicidade entre item, interesse, histórico e avisos. A proposta de versões e resultado persistido por `id_operacao` permanece para comandos, não para consultas do diretório; não alegar que já existe no runtime.
- Não copiar endereço pessoal para itens. Combinação permanece privada aos participantes autorizados; crescimento de históricos não equivale a capacidade de produção.

### Legado e transição

`encaminhamentos`, `ponto_coleta_id`, `destinacao_informada` e estados `aguardando_ponto`, `entrega_prevista` e `recebido` podem existir na base atual. Não preencher novos documentos desses tipos por uma consulta. Não apagar, converter em oferta, encerrar ou reinterpretar registros antigos automaticamente.

Na Etapa 16, a política é manter documentos e acessos autorizados anteriores; a nova consulta não une itens/indicações ao ponto. Ausência de `ativo` mantém o padrão verdadeiro já existente no mapper, sem escrita. A apresentação e a descontinuação dos comandos antigos ficam para a Etapa 18, sem quebrar referências. Os indicadores-alvo não somam registros de descarte a doações/vendas, mas isso não autoriza apagar o histórico. Em particular, não transformar `indicados` ou `coletados` antigos em contagem de consultas ao diretório.

## Estrutura persistida de referência — mantida na Etapa 16

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
