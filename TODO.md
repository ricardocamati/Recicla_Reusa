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

**Concluir a etapa quando:** V2-CT-01 a V2-CT-05 passarem, a suíte completa estiver verde e nenhuma resposta pública expuser e-mail, endereço completo ou hash.

**Situação:** concluída em 2 de novembro de 2026 — 79 testes aprovados e validação em replica set real. Documentos antigos com endereço plano continuam legíveis; migração fica para quando houver dados a converter.

## Etapa 2 — Itens: especificações, histórico e consultas

Referências: V2-RF-03, V2-RF-04, V2-RF-05, V2-RF-10 · V2-CT-06 a V2-CT-09, V2-CT-15, V2-CT-16, V2-CT-22.

- [x] Acrescentar `especificacoes` e `historico` aninhados ao item, com datas UTC em precisão de milissegundos.
- [x] Registrar cada transição de status no histórico, sem permitir salto inválido.
- [x] Implementar filtros e paginação do catálogo sem expor endereço do proprietário.
- [x] Proteger atualização e exclusão por propriedade, com conflito explícito quando o status mudou na concorrência.
- [x] Atualizar testes de item, repositório e API.

**Concluir a etapa quando:** V2-CT-06 a V2-CT-09, V2-CT-15, V2-CT-16 e V2-CT-22 passarem, a alteração concorrente retornar conflito em vez de sobrescrever, e o item não duplicar endereço.

**Situação:** concluída em 2 de novembro de 2026 — 88 testes aprovados e validação em replica set real. A concorrência usa o status esperado como precondição atômica, sem campo de versão exposto. A tela de catálogo pede o limite máximo da API enquanto não houver navegação por páginas.

## Etapa 3 — Pontos de coleta

Referências: V2-RF-08, V2-RF-09 · V2-CT-13, V2-CT-14.

- [x] Criar a coleção `pontos_coleta`, com endereço aninhado, categorias aceitas e horário.
- [x] Expor CRUD autenticado, restrito à conta responsável pelo ponto.
- [x] Garantir que a conta `ponto_coleta` continue provisionada por comando local.
- [x] Impedir exclusão de responsável com ponto vinculado e recusar ponto incompatível no encaminhamento.
- [x] Criar índices e testes de integridade referencial.

**Concluir a etapa quando:** V2-CT-13 e V2-CT-14 passarem, a disputa entre criar ponto e excluir responsável terminar sem registro órfão e os índices existirem no banco real.

**Situação:** concluída em 2 de novembro de 2026 — 103 testes aprovados e validação em MongoDB real. A exclusão de responsável com ponto vinculado é recusada; sem transações no Compose atual, a corrida foi observada com resultado consistente, mas não prova todas as ordens. O encaminhamento de item usa o validador de compatibilidade na etapa 5.

## Etapa 4 — Interesses

Referências: V2-RF-06, V2-RF-07 · V2-CT-10, V2-CT-11, V2-CT-12.

- [ ] Criar a coleção `interesses` relacionando item e interessado, com status e datas.
- [ ] Registrar interesse, listar próprios e recebidos, e permitir decisão do proprietário.
- [ ] Impedir interesse do próprio dono e segunda relação para o mesmo par item/pessoa.
- [ ] Reservar a doação de forma transacional ao aceitar, com efeito e histórico na mesma unidade.
- [ ] Cobrir com testes de API, repositório e concorrência.

**Concluir a etapa quando:** V2-CT-10 a V2-CT-12 passarem, dois aceites simultâneos produzirem um vencedor e um conflito, e o cancelamento devolver o item a disponível.

## Etapa 5 — Fluxos de doação, descarte e revenda

Referências: V2-RF-11, V2-RF-12, V2-RF-13 · V2-CT-17 a V2-CT-21.

- [ ] Definir as transições de cada destino e validar saltos e estados terminais.
- [ ] Encaminhar descarte para ponto de coleta ativo e compatível.
- [ ] Exigir valor positivo apenas na revenda.
- [ ] Concluir doação, descarte e revenda uma única vez, atualizando item, histórico e indicador na mesma transação.
- [ ] Testar transições inválidas, segunda conclusão e rollback.

**Concluir a etapa quando:** V2-CT-17 a V2-CT-21 passarem, a segunda conclusão for recusada sem efeito parcial e o histórico refletir cada passo.

## Etapa 6 — Notificações

Referências: V2-RF-17 · V2-CT-26 a V2-CT-30.

- [ ] Criar a coleção `notificacoes` e o índice único por evento, destinatário e item.
- [ ] Emitir avisos na mesma transação da mudança que os origina.
- [ ] Expor caixa de entrada com listagem e marcação de leitura, restrita ao destinatário.
- [ ] Não notificar quem não tem vínculo com o item nem duplicar aviso do mesmo evento.
- [ ] Testar emissão, privacidade, idempotência e rollback.

**Concluir a etapa quando:** V2-CT-26 a V2-CT-30 passarem, reenvio da mesma operação não criar aviso novo e nenhum destinatário receber dado de terceiro.

## Etapa 7 — Indicadores e frontend das novas telas

Referências: V2-RF-14, V2-RF-16 · V2-CT-23, V2-CT-24 · [docs/http-api.md](docs/http-api.md).

- [ ] Implementar consulta autenticada de indicadores de itens concluídos por destino.
- [ ] Criar as telas de interesses, pontos e notificações em HTML e JavaScript modular, sem build.
- [ ] Manter `credentials: "include"` e renderização segura de texto.
- [ ] Regenerar a OpenAPI do runtime e confrontá-la com a especificação versionada, registrando diferenças.
- [ ] Cobrir as telas com Selenium e atualizar os contratos documentados.

**Concluir a etapa quando:** V2-CT-23 e V2-CT-24 passarem, as três telas funcionarem em navegador real e o contrato gerado tiver teste de correspondência.

## Etapa 8 — Fechamento da v2.0

Referências: V2-RNF-05 a V2-RNF-10, V2-CT-25 · [matriz](artefatos/v2.0/matriz_rastreabilidade.md).

- [ ] Rodar a suíte completa e os verificadores de integração em stack e volume isolados.
- [ ] Executar as três jornadas (doação, descarte e revenda) pela interface em Docker.
- [ ] Validar auditoria temporal e versão em todas as coleções.
- [ ] Confirmar que a limpeza de fixtures é seletiva e comprovada.
- [ ] Atualizar evidências, matriz, README e registro da entrega; conferir links e identificadores.

**Concluir a etapa quando:** V2-CT-25 passar, as três jornadas terminarem verdes em execuções repetidas, a matriz vincular cada requisito a teste e evidência, e a árvore do repositório estiver limpa.

# Parte II — v2.1

A v2.1 começa depois do fechamento da Parte I. Cada etapa substitui comportamento entregue na v2.0, conforme [requisitos](artefatos/v2.1/requisitos.md) e [regras](artefatos/v2.1/regras_de_negocio.md).

## Etapa 9 — Conta única de pessoa

Referências: V21-RF-01 · V21-CT-01, V21-CT-29.

- [ ] Substituir os perfis públicos de doador e beneficiário por uma conta de pessoa, com operador separado.
- [ ] Ajustar autorização por operação, mantendo o operador restrito aos próprios locais.
- [ ] Migrar interesses e itens existentes para a nova regra de papéis, preservando histórico.
- [ ] Atualizar testes de permissão e a documentação de contratos.

**Concluir a etapa quando:** V21-CT-01 e V21-CT-29 passarem, a mesma sessão oferecer e manifestar interesse sem trocar de perfil, e nenhum operador receber comando de compra.

## Etapa 10 — Catálogo de ofertas e cadastro por intenção

Referências: V21-RF-02, V21-RF-03, V21-RF-14 · V21-CT-02, V21-CT-03, V21-CT-04, V21-CT-24.

- [ ] Separar modalidade de condição física e fixar a modalidade no ciclo do item.
- [ ] Publicar catálogo apenas com ofertas disponíveis, excluindo descarte, rascunho, arquivado e concluído.
- [ ] Guiar o cadastro em intenção, características e revisão, com rascunho e publicação.
- [ ] Exibir Ativos, Em andamento e Encerrados, com arquivamento sem apagar referências.
- [ ] Atualizar testes de catálogo, cadastro e arquivamento.

**Concluir a etapa quando:** V21-CT-02 a V21-CT-04 e V21-CT-24 passarem, preço não aparecer em doação nem descarte, e editar não alterar estado por campo genérico.

## Etapa 11 — Interesse, retomada e reserva

Referências: V21-RF-04, V21-RF-05 · V21-CT-05 a V21-CT-08.

- [ ] Permitir retomada de interesse cancelado pelo autor, com histórico, sem contornar recusa.
- [ ] Garantir uma relação por par item/pessoa e exibir interessados nas próprias ofertas.
- [ ] Tornar a reserva explícita, única e reversível antes da declaração de entrega.
- [ ] Tratar desistência e não comparecimento liberando o item.
- [ ] Cobrir concorrência de reserva e conflitos com testes reais.

**Concluir a etapa quando:** V21-CT-05 a V21-CT-08 passarem, dois pedidos simultâneos produzirem uma única reserva e a liberação devolver o item a disponível sem apagar histórico.

## Etapa 12 — Combinação, entrega bilateral e venda

Referências: V21-RF-06, V21-RF-07, V21-RF-08 · V21-CT-09 a V21-CT-12.

- [ ] Oferecer combinação estruturada (local, previsão opcional e observação) com novo aceite a cada alteração.
- [ ] Implementar declaração de entrega e confirmação de recebimento como duas etapas distintas.
- [ ] Permitir venda direta de usado, congelando o preço no aceite e exigindo liberação para alterá-lo.
- [ ] Atualizar indicadores apenas na confirmação, contando uma vez por item.
- [ ] Testar pendência sem confirmação, terceiro não autorizado e reenvio da mesma operação.

**Concluir a etapa quando:** V21-CT-09 a V21-CT-12 passarem, declaração sozinha não concluir, e o preço reservado não puder mudar sem liberação e novo aceite.

## Etapa 13 — Descarte guiado e operação do ponto

Referências: V21-RF-09, V21-RF-10, V21-RF-11 · V21-CT-13 a V21-CT-21.

- [ ] Guiar a escolha do ponto por cidade e categoria, sem prometer proximidade.
- [ ] Registrar entrega prevista somente após confirmação, mantendo o cadastro salvo quando não houver ponto compatível.
- [ ] Permitir cancelar e trocar ponto antes do recebimento, preservando tentativas anteriores.
- [ ] Dar ao operador filas de previstas e recebidas, com filtro por local, paginação e motivo de impossibilidade.
- [ ] Tratar inativação de ponto com previsões ativas e disputa entre previsão e mudança de categoria.

**Concluir a etapa quando:** V21-CT-13 a V21-CT-21 passarem, troca de ponto ser atômica, recebimento ocorrer uma única vez e inativação não apagar histórico.

## Etapa 14 — Indicação de lugar pelo autor

Referências: V21-RF-16, V21-RNF-07 · V21-CT-31 a V21-CT-34.

- [ ] Permitir indicar lugar não cadastrado com tipo de local estruturado e dados opcionais.
- [ ] Encerrar o item como destinação informada, sem confirmação de terceiro e sem criar ponto de coleta.
- [ ] Restringir a indicação ao autor, sem exposição a operadores ou terceiros.
- [ ] Permitir desfazer enquanto o item não estiver arquivado, sem perder histórico.
- [ ] Separar, nos indicadores, recebimento no ponto de destinação apenas informada.

**Concluir a etapa quando:** V21-CT-31 a V21-CT-34 passarem, nenhuma indicação aparecer no diretório nem contar como recebimento, e a validação recusar coordenadas e arquivos.

## Etapa 15 — Avisos, navegação e fechamento da v2.1

Referências: V21-RF-12, V21-RF-13, V21-RF-15 · V21-CT-22, V21-CT-23, V21-CT-25 a V21-CT-28, V21-CT-30 · [matriz](artefatos/v2.1/matriz_rastreabilidade.md).

- [ ] Dirigir cada aviso a quem precisa agir, com link interno e sem duplicação por evento.
- [ ] Corrigir indicadores para separar ofertas, pendências e conclusões confirmadas.
- [ ] Mostrar próximas ações por ator, estados vazios úteis, foco acessível e bloqueio de duplo envio.
- [ ] Preservar filtros e página ao voltar do detalhe e oferecer reconciliação quando a resposta se perder.
- [ ] Rodar as três jornadas em stack isolada, atualizar evidências, matriz e contratos.

**Concluir a etapa quando:** V21-CT-22, V21-CT-23, V21-CT-25 a V21-CT-28 e V21-CT-30 passarem, as jornadas terminarem verdes em execuções repetidas e nenhum indicador misturar previsão, recebimento e reciclagem.
