# Casos de teste da versão 2.0

Os casos desta pasta especificam a segunda entrega e deverão ser automatizados à medida que as funcionalidades forem implementadas.

## V2-CT-01 — Cadastrar usuário com endereço

- **Requisitos:** V2-RF-01, V2-RN-01 a V2-RN-05
- **Passos:** cadastrar usuário com endereço completo.
- **Resultado esperado:** usuário persistido com subdocumento, CEP normalizado e datas iguais na criação.

## V2-CT-02 — Rejeitar endereço incompleto

- **Requisitos:** V2-RF-01 e V2-RN-02
- **Passos:** omitir separadamente logradouro, número, CEP e cidade.
- **Resultado esperado:** cada requisição é rejeitada sem persistência.

## V2-CT-03 — Aceitar endereço sem complemento

- **Requisitos:** V2-RF-01 e V2-RN-02
- **Resultado esperado:** cadastro concluído sem `complemento`.

## V2-CT-04 — Normalizar CEP

- **Requisito:** V2-RN-03
- **Dados:** `87000-000`.
- **Resultado esperado:** valor armazenado como `87000000`.

## V2-CT-05 — Atualizar data de modificação

- **Requisitos:** V2-RF-02, V2-RF-15 e V2-RN-05
- **Passos:** alterar usuário e comparar as datas.
- **Resultado esperado:** `data_adicao` preservada e `data_modificacao` posterior.

## V2-CT-06 — Cadastrar item

- **Requisitos:** V2-RF-03, V2-RN-06 a V2-RN-09
- **Resultado esperado:** item associado ao proprietário, disponível, com datas e primeiro evento.

## V2-CT-07 — Rejeitar proprietário inexistente

- **Requisitos:** V2-RF-03 e V2-RN-06
- **Resultado esperado:** item não é persistido.

## V2-CT-08 — Consultar catálogo sem expor endereço

- **Requisitos:** V2-RF-04, V2-RNF-09 e V2-RN-18
- **Resultado esperado:** catálogo apresenta cidade, mas não logradouro, número, complemento ou CEP.

## V2-CT-09 — Filtrar catálogo

- **Requisito:** V2-RF-04
- **Passos:** consultar filtros de categoria, condição, destino e status.
- **Resultado esperado:** somente itens compatíveis são retornados.

## V2-CT-10 — Registrar interesse válido

- **Requisitos:** V2-RF-06 e V2-RN-12
- **Resultado esperado:** interesse referencia item e usuário existentes.

## V2-CT-11 — Rejeitar interesse do proprietário

- **Requisito:** V2-RN-12
- **Resultado esperado:** nenhum interesse é criado.

## V2-CT-12 — Aceitar interesse e reservar doação

- **Requisitos:** V2-RF-07, V2-RF-11 e V2-RN-13
- **Resultado esperado:** interesse aceito, item reservado e evento registrado.

## V2-CT-13 — Cadastrar ponto de coleta

- **Requisitos:** V2-RF-08, V2-RN-01 a V2-RN-05
- **Resultado esperado:** ponto persistido com endereço aninhado e categorias aceitas.

## V2-CT-14 — Rejeitar ponto incompatível

- **Requisitos:** V2-RF-09 e V2-RN-14
- **Resultado esperado:** item não é encaminhado a ponto que não aceita sua categoria.

## V2-CT-15 — Registrar histórico acumulativo

- **Requisitos:** V2-RF-10 e V2-RN-11
- **Passos:** realizar duas transições válidas.
- **Resultado esperado:** novos eventos são acrescentados sem apagar os anteriores.

## V2-CT-16 — Impedir salto de status

- **Requisito:** V2-RN-10
- **Passos:** tentar pular uma etapa em cada fluxo.
- **Resultado esperado:** todas as transições inválidas são rejeitadas.

## V2-CT-17 — Concluir doação

- **Requisitos:** V2-RF-11, V2-RN-10, V2-RN-13 e V2-RN-16
- **Resultado esperado:** item termina como `doado` com beneficiário e histórico.

## V2-CT-18 — Concluir descarte

- **Requisitos:** V2-RF-12, V2-RN-10, V2-RN-14 e V2-RN-16
- **Resultado esperado:** item termina como `coletado` com ponto e histórico.

## V2-CT-19 — Concluir revenda

- **Requisitos:** V2-RF-13, V2-RN-10, V2-RN-15 e V2-RN-16
- **Resultado esperado:** item termina como `vendido` com comprador, valor e histórico.

## V2-CT-20 — Rejeitar revenda sem valor

- **Requisito:** V2-RN-15
- **Resultado esperado:** item de revenda não é criado ou concluído sem valor válido.

## V2-CT-21 — Impedir segunda conclusão

- **Requisito:** V2-RN-16
- **Resultado esperado:** item concluído não ingressa em outro fluxo.

## V2-CT-22 — Não duplicar endereço no item

- **Requisito:** V2-RN-17
- **Resultado esperado:** item possui referências, mas não contém cópia do endereço completo.

## V2-CT-23 — Calcular indicadores

- **Requisitos:** V2-RF-14 e V2-RN-20
- **Resultado esperado:** totais separados e somente itens concluídos contabilizados.

## V2-CT-24 — Verificar datas em todas as coleções

- **Requisitos:** V2-RF-15 e V2-RN-05
- **Resultado esperado:** documentos das quatro coleções possuem datas válidas.

## V2-CT-25 — Verificar cobertura final

- **Requisitos:** V2-RNF-05 e V2-RNF-06
- **Resultado esperado:** suíte completa aprovada com cobertura mínima de 70%.

## V2-CT-26 — Notificar mudança do item de interesse

- **Requisitos:** V2-RF-17, V2-RN-21 e V2-RN-22
- **Passos:** registrar interesse e alterar de forma relevante o status do item.
- **Resultado esperado:** notificação não lida é criada para o interessado, referenciando o item.

## V2-CT-27 — Notificar decisão sobre interesse

- **Requisitos:** V2-RF-17, V2-RN-21 e V2-RN-22
- **Passos:** aceitar e, em outro cenário, recusar um interesse.
- **Resultado esperado:** o interessado recebe a notificação correspondente a cada decisão.

## V2-CT-28 — Listar e marcar notificação como lida

- **Requisitos:** V2-RF-17, V2-RN-23 e V2-RN-25
- **Resultado esperado:** somente notificações do usuário são listadas; ao ler, `lida` fica verdadeira, `data_leitura` é registrada e `data_modificacao` muda.

## V2-CT-29 — Impedir notificação duplicada

- **Requisitos:** V2-RF-17 e V2-RN-24
- **Passos:** processar novamente o mesmo evento de domínio.
- **Resultado esperado:** permanece apenas uma notificação equivalente para o destinatário.

## V2-CT-30 — Não notificar usuário sem interesse

- **Requisitos:** V2-RF-17 e V2-RN-21
- **Resultado esperado:** usuário sem interesse associado não recebe notificação sobre o item.

## Critérios de saída

- fluxos principais executáveis;
- referências inválidas rejeitadas;
- histórico preservado;
- notificações de interesse criadas sem duplicação e com controle de leitura;
- endereço privado não exposto no catálogo;
- todas as coleções com auditoria temporal;
- cobertura mínima de 70%;
- evidências reproduzíveis e documentação atualizada.
