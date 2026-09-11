# Requisitos da versão 2.0

## 1. Objetivo

Evoluir a PoC para uma plataforma capaz de relacionar usuários, eletrônicos, interesses, pontos de coleta e notificações, mantendo o ciclo de vida dos itens em documentos MongoDB complexos.

## 2. Requisitos funcionais

### V2-RF-01 — Cadastrar usuário com endereço

Cadastrar usuário com `nome`, `email`, `tipo` e o subdocumento `endereco`.

O endereço contém `logradouro`, `numero`, `complemento`, `cep` e `cidade`. Complemento é opcional; os demais campos são obrigatórios.

### V2-RF-02 — Manter usuários

Listar, consultar, atualizar e excluir usuários, preservando relacionamentos e datas de auditoria conforme as regras do domínio.

### V2-RF-03 — Cadastrar item eletrônico

Cadastrar um item associado a um proprietário existente, informando título, descrição, categoria, marca, modelo, condição e destino.

**Critérios de aceitação:**

- o servidor gera ID, status inicial e datas;
- o cadastro acrescenta o primeiro evento ao histórico;
- revenda exige valor;
- proprietário inexistente é rejeitado.

### V2-RF-04 — Consultar catálogo de itens

Listar e consultar itens, permitindo filtrar por categoria, condição, destino, status e cidade de disponibilidade.

O catálogo público não deve expor o endereço completo do proprietário.

### V2-RF-05 — Atualizar item

Atualizar dados permitidos do item e registrar mudanças de status no histórico. Itens concluídos não podem ser reiniciados em outro fluxo.

### V2-RF-06 — Registrar interesse

Permitir que um usuário demonstre interesse em receber ou comprar um item disponível.

### V2-RF-07 — Gerenciar interesse

Permitir consultar e alterar o interesse entre `pendente`, `aceito`, `recusado` e `cancelado`, respeitando as transições do item.

### V2-RF-08 — Cadastrar ponto de coleta

Cadastrar ponto de coleta com responsável, nome, endereço aninhado, categorias aceitas e informações de atendimento.

### V2-RF-09 — Encaminhar item para descarte

Relacionar um item de descarte a um ponto de coleta compatível e registrar o encaminhamento no histórico.

### V2-RF-10 — Rastrear ciclo de vida

Manter em `itens.historico` uma lista de subdocumentos com etapa, status, data do evento, responsável e observação opcional.

### V2-RF-11 — Controlar doação

Controlar o fluxo `disponivel → reservado → doado`, registrando o beneficiário quando concluído.

### V2-RF-12 — Controlar descarte

Controlar o fluxo `disponivel → encaminhado → coletado`, registrando o ponto de coleta.

### V2-RF-13 — Controlar reaproveitamento/revenda

Controlar o fluxo `disponivel → em_avaliacao → recondicionado → vendido`, registrando avaliação, comprador e valor, sem processar pagamento real.

### V2-RF-14 — Apresentar indicadores

Apresentar separadamente as quantidades de itens doados, coletados para descarte e vendidos após reaproveitamento.

### V2-RF-15 — Manter auditoria temporal

Todos os documentos devem possuir `data_adicao` e `data_modificacao`, geradas e atualizadas pelo servidor em UTC.

### V2-RF-16 — Documentar a API final

Disponibilizar documentação OpenAPI dos endpoints de usuários, itens, interesses, pontos de coleta, notificações, fluxos e indicadores.

### V2-RF-17 — Notificar sobre itens de interesse

Criar notificações internas para o usuário quando ocorrer alteração relevante em um item pelo qual ele demonstrou interesse ou no status do próprio interesse.

**Critérios de aceitação:**

- mudança de status do item gera aviso para os interessados afetados;
- aceite, recusa ou cancelamento do interesse gera aviso ao interessado;
- o usuário pode listar suas notificações e marcá-las como lidas;
- a notificação referencia o usuário, o item e o interesse;
- a primeira implementação é interna à API, sem depender de e-mail ou push externo.

## 3. Requisitos não funcionais

### V2-RNF-01 — Múltiplas coleções

Usar `usuarios`, `itens`, `interesses`, `pontos_coleta` e `notificacoes` como coleções relacionadas.

### V2-RNF-02 — Documentos complexos

Usar subdocumentos em `usuarios.endereco`, `pontos_coleta.endereco`, `itens.especificacoes` e na lista `itens.historico`.

### V2-RNF-03 — Integridade das referências

Validar a existência dos documentos referenciados antes de persistir um relacionamento.

### V2-RNF-04 — Programação orientada a objetos

Manter responsabilidades separadas e aplicar abstrações de fluxo somente quando reduzirem duplicação real.

### V2-RNF-05 — Testes automatizados

Cobrir regras, erros, relacionamentos e fluxos principais com testes executáveis.

### V2-RNF-06 — Cobertura

Manter a cobertura do código apresentado na segunda entrega registrada por testes executáveis.

### V2-RNF-07 — Documentação técnica

Documentar instalação, execução, banco, arquitetura, testes e evolução desde a versão 1.0.

### V2-RNF-08 — Versionamento

Identificar a versão 2.0 por commit, tag ou release e manter histórico compatível com a evolução.

### V2-RNF-09 — Privacidade

Não expor endereço completo de usuários em listagens públicas de itens.

### V2-RNF-10 — Configuração reproduzível

Permitir execução com Python 3.11+, MongoDB 7.0 e Docker Compose.

## 4. Fora do escopo

- pagamentos reais;
- transporte dos equipamentos;
- execução física de reparos;
- validação oficial de pontos de coleta;
- aplicativo móvel nativo;
- envio real por e-mail, SMS ou push externo;
- autenticação avançada, salvo se exigida posteriormente.
