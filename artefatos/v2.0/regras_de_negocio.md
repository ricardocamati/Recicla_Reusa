# Regras de negócio da versão 2.0

## V2-RN-01 — Endereço aninhado

Usuários e pontos de coleta possuem um subdocumento `endereco` com `logradouro`, `numero`, `complemento`, `cep` e `cidade`.

## V2-RN-02 — Campos obrigatórios do endereço

`logradouro`, `numero`, `cep` e `cidade` são obrigatórios. `complemento` é opcional.

## V2-RN-03 — CEP

O CEP aceita entrada com ou sem hífen, mas é armazenado com exatamente oito dígitos.

## V2-RN-04 — Número do endereço

`numero` é texto para aceitar números simples, valores alfanuméricos e `S/N`.

## V2-RN-05 — Datas de auditoria

Todos os documentos possuem `data_adicao` e `data_modificacao` controladas pelo servidor em UTC. Na criação são iguais; na atualização somente `data_modificacao` muda.

## V2-RN-06 — Proprietário obrigatório

Todo item referencia um `proprietario_id` existente na coleção `usuarios`.

## V2-RN-07 — Destino único

Cada item possui um destino atual: `doacao`, `descarte` ou `revenda`.

## V2-RN-08 — Condições permitidas

A condição deve ser uma entre `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto` ou `recondicionado`.

## V2-RN-09 — Status inicial

Todo item novo começa como `disponivel`, salvo regra futura explicitamente documentada.

## V2-RN-10 — Transições de status

| Destino | Sequência permitida |
|---|---|
| Doação | `disponivel → reservado → doado` |
| Descarte | `disponivel → encaminhado → coletado` |
| Revenda | `disponivel → em_avaliacao → recondicionado → vendido` |

Saltos e estados de outro fluxo são rejeitados.

## V2-RN-11 — Histórico acumulativo

Cada mudança relevante acrescenta um subdocumento em `itens.historico` com `etapa`, `status`, `data_evento`, `responsavel_id` e `observacao` opcional. Eventos anteriores não são apagados.

## V2-RN-12 — Interesse válido

Interesse referencia item e usuário existentes. O proprietário não pode demonstrar interesse no próprio item.

## V2-RN-13 — Reserva de doação

Um item de doação só pode ser reservado para um interesse aceito. Ao reservar um interessado, os demais não podem concluir o mesmo item.

## V2-RN-14 — Compatibilidade do ponto de coleta

Um item só pode ser encaminhado para ponto que aceite sua categoria.

## V2-RN-15 — Valor de revenda

Itens de revenda exigem valor não negativo. Doação e descarte não devem possuir preço de venda.

## V2-RN-16 — Conclusão única

Item em `doado`, `coletado` ou `vendido` está concluído e não pode ingressar em outro fluxo.

## V2-RN-17 — Endereço não duplicado no item

O item guarda referências ao proprietário e, quando aplicável, ao ponto de coleta. O endereço completo permanece no documento referenciado e não é copiado para o item.

## V2-RN-18 — Privacidade do catálogo

O catálogo pode apresentar a cidade de disponibilidade, mas não logradouro, número, complemento ou CEP do proprietário.

## V2-RN-19 — Especificações flexíveis

`itens.especificacoes` é um subdocumento flexível, pois categorias diferentes possuem características diferentes.

## V2-RN-20 — Indicadores

Somente itens concluídos entram nos totais finais: `doado`, `coletado` ou `vendido`.

## V2-RN-21 — Destinatário da notificação

Somente o usuário associado a um interesse válido recebe notificações sobre aquele interesse ou item.

## V2-RN-22 — Eventos notificáveis

São notificáveis: interesse `aceito`, `recusado` ou `cancelado`; mudança relevante do status do item; e conclusão como `doado`, `coletado` ou `vendido` quando afetar o interessado.

## V2-RN-23 — Estado de leitura

Toda notificação começa com `lida: false`. Somente o destinatário pode marcá-la como lida, registrando `data_leitura`.

## V2-RN-24 — Notificação única por evento

O mesmo evento de domínio não pode gerar duas notificações equivalentes para o mesmo usuário, item e interesse.

## V2-RN-25 — Auditoria da notificação

Notificações possuem `data_adicao` e `data_modificacao`; marcar como lida preserva a primeira data e atualiza a segunda.
