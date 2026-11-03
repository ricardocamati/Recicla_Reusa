# TODO — implementação da segunda entrega e da revisão v2.1

Backlog ativo, em ordem: primeiro a **segunda entrega (v2.0)** inteira, depois a **revisão v2.1** sobre ela. Nada de outras entregas entra aqui.

- Especificação da v2.0: [artefatos/v2.0/](artefatos/v2.0/README.md)
- Proposta v2.1: [artefatos/v2.1/](artefatos/v2.1/README.md)

## Como cada etapa fecha

1. Branch própria a partir da `main` atualizada (`feat/<etapa>`).
2. Commits coerentes — normalmente um, incluindo código, testes e documentação da etapa.
3. Validação local com a suíte completa e o verificador da etapa.
4. Push da branch e abertura do PR; revisão antes do merge.
5. Merge na `main` **somente com autorização explícita**, e só então a próxima branch.

Push, PR e merge não decorrem de autorização para editar ou commitar. Sem force-push e sem commit direto na `main`.

# Parte I — v2.0

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

Validações: [API, MongoDB real e Docker](docs/verificacao-interesses.md).

## Etapa 5 — Fluxos de doação, descarte e revenda

Referências: V2-RF-11, V2-RF-12, V2-RF-13 · V2-CT-17 a V2-CT-21.

- [x] Definir as transições de cada destino e validar saltos e estados terminais.
- [x] Encaminhar descarte para ponto de coleta cadastrado e compatível com a categoria.
- [x] Exigir valor não negativo e restrito à revenda, sem preço em doação ou descarte.
- [x] Concluir doação, descarte e revenda uma única vez, gravando item e histórico na mesma unidade; os indicadores entram na Etapa 7.
- [x] Testar transições inválidas, segunda conclusão e ausência de escrita parcial.

Validações: [fluxos completos em API e MongoDB real](docs/verificacao-fluxos.md).

## Etapa 6 — Notificações

Referências: V2-RF-17 · V2-CT-26 a V2-CT-30.

- [x] Criar a coleção `notificacoes` e o índice único por evento, destinatário e item.
- [x] Emitir avisos na mesma transação da mudança que os origina.
- [x] Expor caixa de entrada com listagem e marcação de leitura, restrita ao destinatário.
- [x] Não notificar quem não tem vínculo com o item nem duplicar aviso do mesmo evento.
- [x] Testar emissão, privacidade, idempotência e rollback.

Validações: [avisos em API e MongoDB real](docs/verificacao-notificacoes.md).

## Etapa 7 — Indicadores e frontend das novas telas

Referências: V2-RF-14, V2-RF-16 · V2-CT-23, V2-CT-24 · [docs/http-api.md](docs/http-api.md).

- [x] Implementar consulta autenticada de indicadores de itens concluídos por destino.
- [x] Criar as telas de interesses, pontos e notificações em HTML e JavaScript modular, sem build.
- [x] Manter `credentials: "include"` e renderização segura de texto.
- [x] Regenerar a OpenAPI do runtime e confrontá-la com a especificação versionada, registrando diferenças.
- [x] Cobrir as telas com Selenium e atualizar os contratos documentados.

Validações: [indicadores, telas e OpenAPI](docs/verificacao-etapa7.md).

## Etapa 8 — Fechamento da v2.0

Referências: V2-RNF-05 a V2-RNF-10, V2-CT-25 · [matriz](artefatos/v2.0/matriz_rastreabilidade.md).

- [x] Rodar a suíte completa e os verificadores de integração em stack e volume isolados.
- [x] Executar as três jornadas (doação, descarte e revenda) pela interface em Docker.
- [x] Validar auditoria temporal e versão em todas as coleções.
- [x] Confirmar que a limpeza de fixtures é seletiva e comprovada.
- [x] Atualizar evidências, matriz, README e registro da entrega; conferir links e identificadores.

# Parte II — v2.1

A v2.1 começa depois do fechamento da Parte I. Cada etapa substitui comportamento entregue na v2.0, conforme [requisitos](artefatos/v2.1/requisitos.md) e [regras](artefatos/v2.1/regras_de_negocio.md).

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

- [ ] Dirigir cada aviso a quem precisa agir, com link interno e sem duplicação por evento.
- [ ] Corrigir indicadores para separar ofertas, pendências e conclusões confirmadas.
- [ ] Mostrar próximas ações por ator, estados vazios úteis, foco acessível e bloqueio de duplo envio.
- [ ] Preservar filtros e página ao voltar do detalhe e oferecer reconciliação quando a resposta se perder.
- [ ] Rodar as três jornadas em stack isolada, atualizar evidências, matriz e contratos.
