# v2.1 — Coerência de negócio e usabilidade

**Natureza:** especificação proposta; não implementada. **Base de referência:** v2.0, também especificada e ainda não implementada. **Preparação:** 2 de novembro de 2026. **Decisões de produto aceitas** pelo usuário na mesma data, sem pendências de decisão.

A v2.1 revisa jornadas e regras, não apenas o visual. Esta pasta é o local canônico da proposta: o documento de discussão que a originou foi substituído por estes artefatos e não é mantido em paralelo.

## Objetivo

Permitir que pessoas ofereçam eletrônicos para doação/venda e organizem a entrega de descartes em pontos físicos, sabendo quem deve agir, o efeito de cada ação e como cancelar uma tentativa ainda não concluída.

## Documentos e autoridade

| Documento | Responsabilidade |
|---|---|
| [Requisitos](requisitos.md) | Capacidades e fronteira do incremento |
| [Regras de negócio](regras_de_negocio.md) | Atores, estados, permissões e invariantes |
| [Jornadas e frontend](jornadas_frontend.md) | Telas, linguagem, feedback e recuperação |
| [Modelo de dados](modelo_dados.md) | Estrutura proposta, referências e índices |
| [Contratos HTTP](contratos_http.md) | Operações propostas e fronteira com a v2.0 |
| [Casos de teste](casos_de_teste.md) | Critérios verificáveis ainda não executados |
| [Matriz](matriz_rastreabilidade.md) | Requisito → regra → cenário → superfície técnica |

Em conflito: requisitos delimitam escopo; regras definem comportamento; os demais documentos devem ser ajustados para corresponder. Decisão pendente não pode virar comportamento de produção sem aceite.

## Situação centralizada

| Frente | Situação |
|---|---|
| Pacote documental v2.1 | Preparado para revisão |
| Decisões de produto | Aceitas em 2 de novembro de 2026 e incorporadas aos documentos desta pasta |
| Implementação de backend/frontend v2.1 | Não iniciada por esta tarefa |
| Testes de aceitação v2.1 | Escritos; não executados como evidência de implementação |
| Dados de demonstração | Não inspecionados nesta reorganização; nenhuma exclusão autorizada |
| Povoamento reproduzível da demonstração | Não existe no repositório: o script anterior foi descartado com a implementação da v2.0 e será reescrito quando houver contrato executável |
| Evidências v2.0 | Não existem: a pasta [v2.0](../v2.0/README.md) contém apenas especificação nesta reorganização; nada aqui prova a v2.1 |

A restauração destes documentos é um commit documental próprio, em branch local, sem alteração de código, banco ou publicação. O TODO executável da v2.0 não é reaberto nem marcado como v2.1 implementada.

## Diferenças principais

- Conta de pessoa pode oferecer e receber/comprar; operador continua separado.
- Catálogo contém ofertas, não descartes; condição física não é disponibilidade comercial.
- Venda direta de usado, sem recondicionamento obrigatório.
- Reserva e combinação da entrega explícitas; confirmação bilateral proposta para doação/venda.
- Descarte significa levar ao ponto: seleção → entrega prevista → recebimento pelo operador.
- Cancelamento, nova escolha de ponto, indisponibilidade e não comparecimento têm saída compreensível.
- Avisos são dirigidos a quem precisa agir; indicadores não confundem recebimento com reciclagem.

## Exclusões

Pagamentos, transporte/retirada domiciliar, mapas externos, chat em tempo real, fotos/upload, certificação e infraestrutura para internet não integram esta versão proposta. O tópico I da discussão (segurança técnica do equipamento e procedimentos sobre dados pessoais nele armazenados) foi excluído a pedido do usuário. Login e proteções básicas já existentes são preservados; não se propõe removê-los.

## Porta de entrada para a implementação futura

1. Conferir requisitos e regras, que já incorporam as decisões aceitas.
2. Conferir requisitos, transições e contratos entre si.
3. Aprovar protótipos das jornadas, sobretudo descarte e confirmação bilateral.
4. Definir tratamento dos dados fictícios existentes, sem apagar o banco por conveniência.
5. Só então abrir o incremento de implementação, com testes e evidências próprios.
