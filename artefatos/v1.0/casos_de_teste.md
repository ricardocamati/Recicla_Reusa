# Casos de teste da versão 1.0

Os casos abaixo especificam os critérios de aceitação da primeira entrega. Cada cenário informa objetivo, pré-condições, dados, procedimento e resultado observável para permitir execução manual ou automação reproduzível.

> **Estado atual:** o backend executável contém o CRUD de usuários e itens, autenticação básica, autorização por sessão, auditoria temporal e provisionamento controlado de `ponto_coleta`. O frontend e os fluxos de interesse/coleta permanecem fora deste marco.

## Convenções de execução

- Cada caso usa uma base de teste isolada ou dados identificados por prefixo exclusivo.
- Datas são comparadas em UTC e com tolerância apenas quando o relógio não estiver injetado no teste.
- Consultas diretas ao MongoDB servem para comprovar persistência, ausência de gravação parcial e campos não expostos pela API.
- Respostas HTTP devem ser verificadas por status, corpo, cabeçalhos e efeito persistido quando aplicável.
- Os dados criados por testes de integração devem ser removidos ao final.

## V1-CT-01 — Cadastrar usuário com endereço

- **Requisitos:** V1-RF-01, V1-RN-01 a V1-RN-07.
- **Objetivo:** Verificar o cadastro público de usuário com endereço aninhado, CEP normalizado e campos gerados pelo servidor.
- **Pré-condições:** API e MongoDB disponíveis e e-mail de teste ainda não cadastrado.
- **Dados de teste:** `nome: "Ana Souza"`, `email: "ana@example.com"`, `senha: "Senha123"`, `tipo: "doador"` e `endereco: {logradouro: " Rua A ", numero: "12A", complemento: "Apto 3", cep: "87000-000", cidade: " Maringá "}`.
- **Procedimento:**
  1. Enviar `POST /api/usuarios` com os dados de teste e registrar status, corpo e cabeçalho `Location`.
  2. Consultar no MongoDB o documento indicado pelo `id` retornado.
- **Resultado esperado:** A API retorna HTTP `201` e `Location` válido, persiste um usuário com endereço aninhado, CEP `87000000`, espaços externos removidos, `id` e datas UTC iguais na criação, sem expor senha ou hash.

## V1-CT-02 — Rejeitar endereço incompleto

- **Requisitos:** V1-RF-01, V1-RF-11, V1-RN-05.
- **Objetivo:** Confirmar que cada campo obrigatório do endereço é validado sem persistência parcial.
- **Pré-condições:** API e MongoDB disponíveis e quatro e-mails únicos reservados para o teste.
- **Dados de teste:** Quatro cópias de um cadastro válido, omitindo separadamente `logradouro`, `numero`, `cep` e `cidade`.
- **Procedimento:**
  1. Enviar `POST /api/usuarios` para cada uma das quatro variações e registrar as respostas.
  2. Consultar a coleção `usuarios` pelos e-mails usados e comparar sua contagem antes e depois.
- **Resultado esperado:** Cada requisição retorna HTTP `400` indicando o campo ausente, nenhum dos usuários é persistido e a quantidade de documentos permanece inalterada.

## V1-CT-03 — Aceitar endereço sem complemento

- **Requisitos:** V1-RF-01, V1-RN-05.
- **Objetivo:** Verificar que `complemento` é opcional no cadastro do usuário.
- **Pré-condições:** API e MongoDB disponíveis e e-mail de teste não cadastrado.
- **Dados de teste:** Usuário beneficiário válido com `logradouro`, `numero`, `cep` e `cidade`, mas sem a propriedade `complemento`.
- **Procedimento:**
  1. Enviar `POST /api/usuarios` com os dados de teste.
  2. Consultar no MongoDB o documento criado pelo `id` da resposta.
- **Resultado esperado:** A API retorna HTTP `201` e persiste o endereço sem exigir nem inventar conteúdo para `complemento`.

## V1-CT-04 — Normalizar CEP

- **Requisitos:** V1-RN-06.
- **Objetivo:** Verificar que um CEP recebido com hífen é armazenado no formato canônico de oito dígitos.
- **Pré-condições:** Cadastro de usuário disponível e e-mail de teste ainda não utilizado.
- **Dados de teste:** Usuário válido com `endereco.cep: "87000-000"`.
- **Procedimento:**
  1. Cadastrar o usuário por `POST /api/usuarios` e obter seu `id`.
  2. Ler `endereco.cep` diretamente no documento persistido.
- **Resultado esperado:** O cadastro retorna HTTP `201` e o banco contém exatamente `endereco.cep: "87000000"`.

## V1-CT-05 — Listar e consultar usuários

- **Requisitos:** V1-RF-02, V1-RF-03.
- **Objetivo:** Validar a listagem pública resumida e a consulta completa do próprio usuário.
- **Pré-condições:** Usuários A e B cadastrados, com A autenticado e ambos os identificadores conhecidos.
- **Dados de teste:** A é doador de Maringá e B é beneficiário de Londrina, ambos com e-mail e endereço completos.
- **Procedimento:**
  1. Enviar `GET /api/usuarios` e verificar os registros de A e B, repetindo em base vazia para validar a lista vazia.
  2. Na sessão de A, consultar `GET /api/usuarios/{id_de_A}` e `GET /api/usuarios/{id_de_B}`.
- **Resultado esperado:** Todas as consultas retornam HTTP `200`, a listagem e o acesso a B expõem somente `id`, `nome`, `tipo` e cidade, o acesso próprio de A inclui seus dados completos exceto senha/hash e a base vazia produz `[]`.

## V1-CT-06 — Atualizar usuário e datas

- **Requisitos:** V1-RF-04, V1-RN-07, V1-RN-14.
- **Objetivo:** Confirmar a alteração dos campos permitidos e a preservação dos campos imutáveis e de auditoria.
- **Pré-condições:** Usuário autenticado como dono do perfil e valores originais de `id`, `tipo`, `data_adicao` e `data_modificacao` registrados.
- **Dados de teste:** Novo `nome` e nova cidade, acompanhados de valores adulterados para `id`, `tipo` e `data_adicao`.
- **Procedimento:**
  1. Enviar `PUT /api/usuarios/{id}` com os dados de teste na sessão do próprio usuário.
  2. Consultar o usuário pela API e no MongoDB e comparar os valores anteriores e posteriores.
- **Resultado esperado:** A atualização tem sucesso, altera apenas os campos permitidos, preserva `id`, `tipo` e `data_adicao` e grava `data_modificacao` UTC posterior à anterior.

## V1-CT-07 — Excluir usuário

- **Requisitos:** V1-RF-05, V1-RN-15.
- **Objetivo:** Verificar a exclusão do próprio cadastro e o tratamento posterior do recurso inexistente.
- **Pré-condições:** Usuário cadastrado e autenticado como dono do perfil.
- **Dados de teste:** `id` do usuário autenticado.
- **Procedimento:**
  1. Enviar `DELETE /api/usuarios/{id}` e registrar status e corpo.
  2. Consultar o mesmo `id` pela API e diretamente na coleção `usuarios`.
- **Resultado esperado:** A exclusão retorna HTTP `204` com corpo vazio, a consulta posterior retorna HTTP `404` e o documento não existe mais no banco.

## V1-CT-08 — Cadastrar item válido

- **Requisitos:** V1-RF-06, V1-RN-08 a V1-RN-13.
- **Objetivo:** Validar o cadastro de item por doador autenticado com proprietário, estado inicial e auditoria controlados pelo servidor.
- **Pré-condições:** Doador existente e autenticado e API e MongoDB disponíveis.
- **Dados de teste:** Item `Notebook usado`, categoria `Informática`, marca e modelo preenchidos, condição `funcional`, destino `doacao` e sem `valor`, incluindo valores falsos para campos controlados.
- **Procedimento:**
  1. Enviar `POST /api/itens` com os dados e registrar status, corpo e `Location`.
  2. Consultar no MongoDB o item pelo `id` retornado.
- **Resultado esperado:** A API retorna HTTP `201` e `Location` válido, persiste um item com `proprietario_id` da sessão, `status: "disponivel"`, datas UTC iguais e campos controlados gerados pelo servidor, sem preço de venda.

## V1-CT-09 — Rejeitar proprietário inexistente

- **Requisitos:** V1-RF-06, V1-RF-11, V1-RN-08.
- **Objetivo:** Garantir que nenhum item seja criado para um proprietário ausente de `usuarios`.
- **Pré-condições:** Ambiente isolado capaz de simular contexto autenticado de doador cujo `id` não exista na coleção `usuarios`.
- **Dados de teste:** Contexto com `id: "usuario-inexistente"` e um item de doação válido.
- **Procedimento:**
  1. Confirmar no banco que o proprietário não existe e enviar `POST /api/itens` no contexto preparado.
  2. Consultar `itens` pelo conteúdo enviado e comparar a contagem antes e depois.
- **Resultado esperado:** A requisição retorna HTTP `404` com indicação de proprietário inexistente, nenhum item é retornado como criado e a coleção permanece inalterada.

## V1-CT-10 — Listar e filtrar itens

- **Requisitos:** V1-RF-07.
- **Objetivo:** Verificar a listagem e os filtros independentes e combinados de categoria, condição, destino e status.
- **Pré-condições:** Catálogo com itens de combinações conhecidas e usuário autorizado a consultá-lo.
- **Dados de teste:** Itens A `Informática/funcional/doacao/disponivel`, B `Telefonia/reparavel/revenda/disponivel` e C `Informática/sem_conserto/descarte/disponivel`.
- **Procedimento:**
  1. Enviar `GET /api/itens` sem filtros e depois com cada filtro isolado.
  2. Enviar filtros combinados que retornem somente C e uma combinação sem correspondência.
- **Resultado esperado:** Todas as requisições retornam HTTP `200`, cada lista contém somente itens compatíveis, o filtro combinado seleciona apenas C e a combinação sem correspondência retorna `[]`.

## V1-CT-11 — Consultar item

- **Requisitos:** V1-RF-08, V1-RN-15.
- **Objetivo:** Validar a consulta de item existente e o tratamento de identificadores inexistente e inválido.
- **Pré-condições:** Um item existente com `id` conhecido e acesso ao catálogo autorizado.
- **Dados de teste:** Um `id` existente, um `id` inexistente em formato válido e `abc` como identificador inválido.
- **Procedimento:**
  1. Enviar `GET /api/itens/{id}` para o identificador existente.
  2. Repetir a consulta para os identificadores inexistente e inválido.
- **Resultado esperado:** O item existente retorna HTTP `200` com os dados corretos e os dois demais identificadores retornam HTTP `404` sem alterar o banco.

## V1-CT-12 — Atualizar item e datas

- **Requisitos:** V1-RF-09, V1-RN-14.
- **Objetivo:** Confirmar que o proprietário altera campos permitidos sem mudar identidade, propriedade ou data de criação do item.
- **Pré-condições:** Item existente, doador proprietário autenticado e campos originais registrados.
- **Dados de teste:** Novos título, descrição e condição, acompanhados de valores adulterados para `id`, `proprietario_id` e `data_adicao`.
- **Procedimento:**
  1. Enviar `PUT /api/itens/{id}` com os dados na sessão do proprietário.
  2. Consultar o item pela API e no MongoDB e comparar os valores anteriores e posteriores.
- **Resultado esperado:** A atualização tem sucesso, altera os campos permitidos, preserva `id`, `proprietario_id` e `data_adicao` e grava `data_modificacao` UTC posterior à anterior.

## V1-CT-13 — Excluir item

- **Requisitos:** V1-RF-10, V1-RN-15.
- **Objetivo:** Verificar a exclusão de item pelo proprietário e sua ausência após a operação.
- **Pré-condições:** Doador proprietário autenticado e item existente com `id` conhecido.
- **Dados de teste:** `id` do item pertencente ao usuário da sessão.
- **Procedimento:**
  1. Enviar `DELETE /api/itens/{id}` e registrar status e corpo.
  2. Consultar o mesmo `id` pela API e diretamente na coleção `itens`.
- **Resultado esperado:** A exclusão retorna HTTP `204` com corpo vazio, a consulta posterior retorna HTTP `404` e o documento não existe mais no banco.

## V1-CT-14 — Validar condição e destino

- **Requisitos:** V1-RF-11, V1-RN-09, V1-RN-10.
- **Objetivo:** Garantir que somente condições e destinos pertencentes às enumerações sejam aceitos.
- **Pré-condições:** Doador autenticado, item base válido e quantidade inicial de itens registrada.
- **Dados de teste:** Variações inválidas `condicao: "novo"` e `destino: "troca"`, além de casos parametrizados com todos os valores permitidos.
- **Procedimento:**
  1. Enviar cada variação inválida por `POST /api/itens` e verificar a coleção.
  2. Enviar casos válidos com `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto`, `recondicionado`, `doacao`, `descarte` e `revenda` coerente.
- **Resultado esperado:** As variações inválidas retornam HTTP `400` sem persistência e todos os valores enumerados são aceitos quando os demais dados são válidos.

## V1-CT-15 — Validar valor de revenda

- **Requisitos:** V1-RF-11, V1-RN-12.
- **Objetivo:** Validar a obrigatoriedade e o limite do valor na revenda e a ausência de preço nos demais destinos.
- **Pré-condições:** Doador autenticado e item base válido.
- **Dados de teste:** Revenda sem `valor`, revenda com `-0.01`, revenda com `0`, doação com `100` e descarte com `100`.
- **Procedimento:**
  1. Enviar separadamente os cinco cadastros por `POST /api/itens`.
  2. Consultar no banco os documentos aceitos e confirmar a ausência dos rejeitados.
- **Resultado esperado:** Revenda sem valor ou com valor negativo retorna HTTP `400` sem persistência, revenda com zero retorna HTTP `201` mantendo `0` e doação ou descarte não mantêm preço de venda.

## V1-CT-16 — Não duplicar endereço no item

- **Requisitos:** V1-RNF-02, V1-RN-08.
- **Objetivo:** Confirmar que o item referencia o proprietário sem copiar seu endereço.
- **Pré-condições:** Doador com endereço completo cadastrado e autenticado.
- **Dados de teste:** Item de doação válido sem propriedades de endereço no corpo.
- **Procedimento:**
  1. Cadastrar o item por `POST /api/itens` e obter seu `id`.
  2. Inspecionar diretamente o documento correspondente na coleção `itens`.
- **Resultado esperado:** O documento contém somente a referência `proprietario_id` e não contém `endereco`, `logradouro`, `numero`, `complemento` nem `cep`, ainda que a resposta pública derive a cidade do proprietário.

## V1-CT-17 — Executar CRUDs com MongoDB real

- **Requisitos:** V1-RNF-01, V1-RNF-09, V1-RNF-10.
- **Objetivo:** Comprovar os dois CRUDs contra MongoDB 7.0 real configurado por Docker Compose e remover os dados de teste.
- **Pré-condições:** Docker Compose disponível, `.env` local baseado em `.env.example` e ambiente exclusivo de teste.
- **Dados de teste:** Um doador e um item de doação identificados por prefixo único de execução.
- **Procedimento:**
  1. Iniciar o Compose, confirmar MongoDB `7.0.x` e executar criar, listar, consultar, atualizar e excluir usuários e itens pela API.
  2. Remover dados auxiliares e consultar `usuarios` e `itens` pelo prefixo da execução.
- **Resultado esperado:** Todas as operações produzem os status e efeitos previstos nas coleções reais `usuarios` e `itens`, a conexão vem do ambiente e nenhum dado marcado permanece ao final.

## V1-CT-18 — Verificar cobertura

- **Requisitos:** V1-RNF-05, V1-RNF-06.
- **Objetivo:** Verificar de modo reproduzível que a suíte é aprovada com cobertura mínima de 70%.
- **Pré-condições:** Python 3.11 ou superior, dependências de desenvolvimento instaladas e ambiente de teste configurado.
- **Dados de teste:** Suíte automatizada completa da v1.0 e configuração oficial de cobertura do projeto.
- **Procedimento:**
  1. Executar na raiz o comando de testes com cobertura documentado pelo projeto e limiar de falha de 70%.
  2. Registrar código de saída, totais de testes e percentual global informado.
- **Resultado esperado:** O processo termina com código `0`, sem falhas ou erros, e o relatório apresenta cobertura total igual ou superior a `70%`, falhando automaticamente abaixo desse limite.

## V1-CT-19 — Cadastrar usuário com senha segura

- **Requisitos:** V1-RF-01, V1-RNF-11, V1-RN-18 e V1-RN-19.
- **Objetivo:** Verificar que uma senha válida é transformada em hash forte sem ser exposta ou persistida em texto puro.
- **Pré-condições:** API e banco de teste estão disponíveis, a coleção `usuarios` está vazia e o documento persistido pode ser inspecionado.
- **Dados de teste:** Usuário `Ana Souza`, e-mail `ana.ct19@example.com`, senha `Recicla2026`, tipo `doador` e endereço válido.
- **Procedimento:**
  1. Enviar `POST /api/usuarios` com os dados de teste e consultar o recurso pelo cabeçalho `Location`.
  2. Inspecionar o documento em `usuarios` e verificar a senha informada contra `senha_hash` com a biblioteca adotada.
- **Resultado esperado:** O cadastro retorna HTTP `201`, respostas não contêm `senha` nem `senha_hash`, o banco contém somente um hash diferente da senha original e sua verificação criptográfica é bem-sucedida.

## V1-CT-20 — Rejeitar e-mail duplicado

- **Requisitos:** V1-RF-11 e V1-RN-17.
- **Objetivo:** Confirmar a unicidade do e-mail após normalização para minúsculas.
- **Pré-condições:** API e banco de teste estão disponíveis e não há usuário com o e-mail do teste.
- **Dados de teste:** Primeiro cadastro com `Pessoa.Teste@Example.com` e segundo com `pessoa.teste@example.com`, ambos com demais campos válidos.
- **Procedimento:**
  1. Cadastrar o primeiro usuário por `POST /api/usuarios` e repetir com o segundo e-mail.
  2. Consultar `usuarios` pelo e-mail normalizado `pessoa.teste@example.com`.
- **Resultado esperado:** O primeiro cadastro retorna HTTP `201`, o segundo retorna HTTP `409` e existe somente um documento com o e-mail normalizado.

## V1-CT-21 — Autenticar com credenciais válidas

- **Requisitos:** V1-RF-13, V1-RNF-12, V1-RN-20 e V1-RN-21.
- **Objetivo:** Verificar a criação de sessão temporária no servidor e seu envio em cookie inacessível ao JavaScript.
- **Pré-condições:** O usuário `login.ct21@example.com` com senha `Acesso2026` está cadastrado e o armazenamento de sessões em memória está vazio.
- **Dados de teste:** Login com e-mail `LOGIN.CT21@EXAMPLE.COM` e senha `Acesso2026`.
- **Procedimento:**
  1. Enviar `POST /api/auth/login` e inspecionar corpo e cabeçalho `Set-Cookie`.
  2. Confirmar a associação da sessão em memória ao usuário e executar `document.cookie` no navegador.
- **Resultado esperado:** A API retorna HTTP `200`, cria uma sessão em memória e envia `recicla_sessao` com `HttpOnly`, sem expor seu identificador no corpo ou em `document.cookie`.

## V1-CT-22 — Rejeitar credenciais inválidas sem revelar cadastro

- **Requisitos:** V1-RF-13, V1-RNF-14 e V1-RN-20.
- **Objetivo:** Garantir que falhas de login não revelem se um e-mail está cadastrado.
- **Pré-condições:** O usuário `login.ct22@example.com` está cadastrado com senha `Correta2026` e não há sessões ativas.
- **Dados de teste:** Tentativa A com o e-mail cadastrado e senha `Errada2026` e tentativa B com `inexistente.ct22@example.com` e a mesma senha.
- **Procedimento:**
  1. Enviar `POST /api/auth/login` para as duas tentativas e comparar status, estrutura e mensagem.
  2. Verificar cabeçalhos e armazenamento de sessões após as chamadas.
- **Resultado esperado:** Ambas retornam HTTP `401` com a mesma mensagem genérica, sem `Set-Cookie` válido e sem criar sessão.

## V1-CT-23 — Rejeitar sessão ausente, inválida ou expirada

- **Requisitos:** V1-RF-18, V1-RNF-12, V1-RN-21 e V1-RN-25.
- **Objetivo:** Verificar que uma rota protegida aceita somente sessões existentes e dentro dos 30 minutos de validade.
- **Pré-condições:** Há um usuário cadastrado e uma sessão expirada preparada no armazenamento em memória.
- **Dados de teste:** `GET /api/usuarios/me` sem cookie, com `recicla_sessao=invalida` e com o identificador expirado.
- **Procedimento:**
  1. Chamar a rota separadamente nos três cenários de sessão.
  2. Verificar as respostas e o estado da sessão expirada no servidor.
- **Resultado esperado:** Cada chamada retorna HTTP `401` sem dados do usuário e a sessão expirada é removida do armazenamento do servidor.

## V1-CT-24 — Consultar o próprio perfil

- **Requisitos:** V1-RF-14, V1-RN-23 e V1-RN-26.
- **Objetivo:** Confirmar que o usuário autenticado obtém seu perfil completo permitido sem dados de credencial.
- **Pré-condições:** Um usuário com endereço completo está cadastrado e possui sessão válida.
- **Dados de teste:** `GET /api/usuarios/me` com o cookie desse usuário.
- **Procedimento:**
  1. Enviar a requisição autenticada e comparar os campos retornados com o cadastro.
  2. Procurar no corpo os campos `senha`, `senha_hash` e qualquer identificador de sessão.
- **Resultado esperado:** A resposta retorna HTTP `200` com ID, nome, e-mail, tipo, endereço e datas do próprio usuário, sem senha, hash ou identificador de sessão.

## V1-CT-25 — Impedir alteração de outro usuário

- **Requisitos:** V1-RF-04, V1-RF-05, V1-RF-18 e V1-RN-23.
- **Objetivo:** Garantir que uma identidade autenticada não atualize nem exclua o cadastro de outra pessoa.
- **Pré-condições:** Os usuários A e B estão cadastrados, A possui sessão válida e o estado original de B foi registrado.
- **Dados de teste:** `PUT /api/usuarios/{id_b}` com nome alterado e `DELETE /api/usuarios/{id_b}`, ambos com a sessão de A.
- **Procedimento:**
  1. Enviar a atualização e a exclusão de B usando o cookie de A.
  2. Consultar diretamente o documento de B após as tentativas.
- **Resultado esperado:** As duas operações retornam HTTP `403` e o documento de B continua existente e idêntico ao estado original, inclusive em `data_modificacao`.

## V1-CT-26 — Aplicar permissões por tipo

- **Requisitos:** V1-RF-15 a V1-RF-17 e V1-RN-24.
- **Objetivo:** Validar a matriz de permissões da v1.0 para doador, beneficiário e ponto de coleta.
- **Pré-condições:** Há uma conta autenticável de cada tipo, dados válidos para um item e ao menos um item de descarte no catálogo.
- **Dados de teste:** `POST /api/itens`, `GET /api/itens`, filtro `destino=descarte` e chamadas a operações futuras de interesse e coleta.
- **Procedimento:**
  1. Com cada perfil, consultar e filtrar o catálogo e tentar cadastrar um item válido.
  2. Tentar acessar por chamada direta as operações de interesse e confirmação de coleta da v2.0.
- **Resultado esperado:** Os três perfis consultam e filtram com HTTP `200`, somente o doador cria com HTTP `201`, os outros recebem HTTP `403` na criação e as rotas ainda inexistentes da v2.0 retornam HTTP `404`.

## V1-CT-27 — Impedir alteração de item alheio

- **Requisitos:** V1-RF-09, V1-RF-10, V1-RF-18 e V1-RN-23.
- **Objetivo:** Verificar a autorização por propriedade na atualização e exclusão de itens.
- **Pré-condições:** Os doadores A e B existem, há um item de B e A possui sessão válida.
- **Dados de teste:** `PUT /api/itens/{id_item_b}` com título alterado e `DELETE /api/itens/{id_item_b}`, ambos com a sessão de A.
- **Procedimento:**
  1. Enviar a atualização e a exclusão do item de B com o cookie de A.
  2. Consultar diretamente o documento do item após as tentativas.
- **Resultado esperado:** As operações retornam HTTP `403` e o item permanece existente e inalterado, inclusive em `proprietario_id` e `data_modificacao`.

## V1-CT-28 — Impedir alteração do tipo

- **Requisitos:** V1-RF-04 e V1-RN-22.
- **Objetivo:** Impedir elevação de permissão pela atualização comum do próprio usuário.
- **Pré-condições:** Um usuário `beneficiario` está cadastrado, autenticado e confirmado no banco.
- **Dados de teste:** `PUT /api/usuarios/{id}` com `tipo: "doador"` e os demais campos exigidos pelo contrato.
- **Procedimento:**
  1. Enviar a atualização com a sessão do beneficiário e consultar `/api/usuarios/me`.
  2. Conferir o tipo persistido e tentar uma operação exclusiva de doador.
- **Resultado esperado:** A atualização com `tipo` retorna HTTP `400`, `tipo` permanece `beneficiario` no banco e a operação exclusiva de doador retorna HTTP `403`.

## V1-CT-29 — Proteger dados na listagem

- **Requisitos:** V1-RF-02, V1-RF-03, V1-RNF-14 e V1-RN-26.
- **Objetivo:** Confirmar que dados de terceiros são reduzidos ao resumo público permitido.
- **Pré-condições:** Os usuários A e B possuem e-mail, endereço completo e hash, e A está autenticado.
- **Dados de teste:** `GET /api/usuarios` e `GET /api/usuarios/{id_b}` com a sessão de A.
- **Procedimento:**
  1. Listar usuários e consultar individualmente B com a sessão de A.
  2. Inspecionar todos os campos retornados para B nas duas respostas.
- **Resultado esperado:** As respostas retornam HTTP `200` e B contém somente `id`, `nome`, `tipo` e cidade, sem e-mail, endereço completo, senha, hash ou identificador de sessão.

## V1-CT-30 — Restringir CORS e proteger segredos

- **Requisitos:** V1-RNF-09, V1-RNF-13 e V1-RN-27.
- **Objetivo:** Verificar que cookies são aceitos somente de origens configuradas e que segredos não aparecem em arquivos rastreáveis ou logs.
- **Pré-condições:** A API permite `http://localhost:5500`, os logs podem ser capturados e os arquivos do projeto podem ser inspecionados.
- **Dados de teste:** Requisições das origens permitida e `https://origem-nao-permitida.example` e buscas por credenciais, senha/hash e `recicla_sessao`.
- **Procedimento:**
  1. Enviar preflight e requisição com cookie a partir de cada origem e inspecionar os cabeçalhos CORS.
  2. Examinar arquivos rastreáveis e logs gerados durante cadastro e login, desconsiderando valores fictícios de `.env.example`.
- **Resultado esperado:** Somente a origem configurada recebe autorização explícita com credenciais, nunca há origem `*` com cookies e nenhum segredo real, senha, hash ou identificador de sessão aparece nos arquivos ou logs.

## V1-CT-31 — Impedir autoatribuição de ponto de coleta

- **Requisitos:** V1-RF-01, V1-RF-17 e V1-RN-01.
- **Objetivo:** Garantir que o perfil `ponto_coleta` não possa ser obtido pelo cadastro público.
- **Pré-condições:** A API e o banco estão disponíveis e o comando local `python -m app.provisionar_ponto_coleta` está disponível ao responsável técnico.
- **Dados de teste:** Cadastro público com `tipo: "ponto_coleta"` e conta provisionada `coleta.ct31@example.com` com senha válida.
- **Procedimento:**
  1. Tentar o cadastro público e confirmar que nenhum documento foi criado.
  2. Executar o comando local de provisionamento, fornecer a senha no prompt e confirmar o documento criado com `tipo: "ponto_coleta"`.
  3. Autenticar com a conta provisionada e consultar `/api/usuarios/me`.
- **Resultado esperado:** O cadastro público retorna HTTP `400` sem persistência, enquanto a conta provisionada autentica com HTTP `200` e apresenta `tipo: "ponto_coleta"`.

## V1-CT-32 — Abrir frontend sem etapa de build

- **Requisitos:** V1-RF-19 e V1-RNF-15.
- **Objetivo:** Confirmar que o cliente separado funciona diretamente como arquivos estáticos sem compilação.
- **Pré-condições:** O conteúdo de `frontend/` está disponível e a API está em execução.
- **Dados de teste:** Servidor `python -m http.server 5500` iniciado em `frontend/` e URL `http://localhost:5500`.
- **Procedimento:**
  1. Servir `frontend/` sem instalar ou executar ferramenta de build e abrir a URL no navegador.
  2. Navegar por cadastro, login, perfil e catálogo enquanto se inspecionam console e rede.
- **Resultado esperado:** HTML, CSS e JavaScript carregam com sucesso, sem erro de sintaxe ou recurso obrigatório ausente, e as telas básicas consomem a API pública configurada.

## V1-CT-33 — Cadastrar e autenticar pelo frontend

- **Requisitos:** V1-RF-13, V1-RF-19 e V1-RN-28.
- **Objetivo:** Validar cadastro e login no navegador sem exposição ou armazenamento indevido de senha e sessão.
- **Pré-condições:** O frontend está em origem permitida, a API está disponível e os armazenamentos do navegador estão vazios.
- **Dados de teste:** Usuário `Frontend CT33`, e-mail `frontend.ct33@example.com`, senha `Tela2026`, tipo `doador` e endereço válido.
- **Procedimento:**
  1. Cadastrar o usuário e realizar login pelos formulários do frontend.
  2. Inspecionar DOM, cookies, `localStorage`, `sessionStorage` e uma requisição protegida posterior.
- **Resultado esperado:** Cadastro e login funcionam, a senha não é reexibida nem retida, `recicla_sessao` é `HttpOnly`, nenhum identificador de sessão aparece nos armazenamentos JavaScript e o cookie segue automaticamente nas chamadas protegidas.

## V1-CT-34 — Aplicar perfil na interface e no backend

- **Requisitos:** V1-RF-15 a V1-RF-19 e V1-RN-24, V1-RN-29.
- **Objetivo:** Verificar que a interface reflete as permissões sem substituir a autorização do backend.
- **Pré-condições:** Frontend e API estão ativos e existem contas de doador, beneficiário e ponto de coleta.
- **Dados de teste:** Controles de criação e gestão, filtro de descarte e chamada manual `POST /api/itens` com dados válidos.
- **Procedimento:**
  1. Entrar com cada perfil e verificar os controles exibidos e as ações permitidas.
  2. Nas sessões sem permissão, enviar manualmente `POST /api/itens` fora dos controles da interface.
- **Resultado esperado:** O doador vê e usa a gestão dos próprios itens, beneficiário e ponto de coleta veem somente ações compatíveis e suas chamadas manuais de criação retornam HTTP `403`.

## V1-CT-35 — Renderizar dados e erros com segurança

- **Requisitos:** V1-RF-19, V1-RNF-14 e V1-RN-28, V1-RN-29.
- **Objetivo:** Confirmar que dados da API não executam código e que falhas relevantes geram mensagens compreensíveis.
- **Pré-condições:** Frontend e API estão ativos e respostas controladas e indisponibilidade temporária podem ser simuladas.
- **Dados de teste:** Texto `<img src=x onerror="window.ct35Executou=true">` e cenários HTTP `401`, `403`, `404` e falha de conexão.
- **Procedimento:**
  1. Exibir o texto de teste vindo da API e verificar o DOM e `window.ct35Executou`.
  2. Provocar os quatro cenários de falha e observar as mensagens da interface.
- **Resultado esperado:** O conteúdo aparece como texto literal sem executar código, e a interface distingue login necessário, ação proibida, recurso inexistente e API indisponível sem revelar dados internos.

## V1-CT-36 — Encerrar sessão

- **Requisitos:** V1-RF-20, V1-RNF-12 e V1-RN-32.
- **Objetivo:** Verificar que o logout invalida a sessão em memória e expira o cookie do navegador.
- **Pré-condições:** Um usuário está autenticado e `/api/usuarios/me` retorna HTTP `200` antes do teste.
- **Dados de teste:** `POST /api/auth/logout` com o cookie atual e reutilização posterior do mesmo identificador.
- **Procedimento:**
  1. Enviar o logout e inspecionar `Set-Cookie` e o armazenamento de sessões.
  2. Repetir `GET /api/usuarios/me` com o identificador anteriormente emitido.
- **Resultado esperado:** O logout retorna sucesso, remove a sessão em memória, expira `recicla_sessao` e a chamada protegida posterior retorna HTTP `401`.

## V1-CT-37 — Validar atributos do cookie

- **Requisitos:** V1-RF-13, V1-RNF-12, V1-RN-21 e V1-RN-31.
- **Objetivo:** Confirmar os atributos e a validade máxima do cookie de sessão em HTTP local e HTTPS.
- **Pré-condições:** Um usuário válido pode autenticar em ambientes de teste HTTP e HTTPS com relógios sincronizados.
- **Dados de teste:** Cabeçalhos `Set-Cookie` de logins válidos nos dois ambientes e operação de alteração originada de domínio não permitido.
- **Procedimento:**
  1. Autenticar em HTTP e HTTPS e conferir nome, `HttpOnly`, `SameSite`, `Path`, `Secure` e expiração do cookie.
  2. Comparar a validade com a sessão no servidor e tentar a alteração a partir da origem não permitida.
- **Resultado esperado:** `recicla_sessao` possui `HttpOnly`, `SameSite=Lax`, `Path=/` e duração máxima de 30 minutos, recebe `Secure` em HTTPS, não excede a validade do servidor e não autoriza alteração de origem não permitida.

## Evidência de automação

| Evidência atual | Escopo comprovado | Resultado verificado |
|---|---|---|
| `tests/test_api_usuario.py` | cadastro com endereço/auditoria, resumos públicos, atualização autorizada, login, logout, sessão, validações, e-mail único e exclusão autorizada | 9 testes aprovados |
| `tests/test_usuario_service.py` | criação, hash de senha, atualização temporal, unicidade, autenticação e recurso inexistente | 5 testes aprovados |
| `tests/test_mongo_usuario_repository.py` | persistência, endereço, auditoria, índice único, consulta e exclusão com `mongomock` | 2 testes aprovados |
| `tests/test_security.py` | hash scrypt e expiração de sessão em 30 minutos | 2 testes aprovados |
| `tests/test_api_item.py` | cadastro, filtros, validação, privacidade, autorização e CRUD HTTP de itens | 8 testes aprovados |
| `tests/test_item_service.py` | proprietário, auditoria, filtros, atualização, autorização e recurso inexistente | 6 testes aprovados |
| `tests/test_mongo_item_repository.py` | persistência, filtros, índice, conversão de ID, precisão temporal e exclusão com `mongomock` | 3 testes aprovados |
| `tests/test_provisionamento_ponto_coleta.py` | tipo controlado, hash, duplicidade, rejeição de tipo no corpo e comando administrativo | 4 testes aprovados |
| Suíte atual | CRUD de usuários e itens, autenticação, autorização, provisionamento e auditoria executáveis; frontend ainda pendente | 39 testes aprovados; cobertura total de 94,28% |

A automação atual comprova o CRUD de usuários e itens, endereço, auditoria, privacidade, login, sessão, filtros, autorização por proprietário e provisionamento controlado. A integração real também foi executada contra MongoDB 7.0 no Docker Compose, com ping, índices, CRUD dos dois recursos e limpeza dos dados temporários aprovados. O frontend, os fluxos de interesse/coleta e as demais capacidades administrativas da v2.0 continuam planejados; a cobertura permanece igual ou superior a 70%.
