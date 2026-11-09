# Arquitetura

## Visão geral

PoC em Python/FastAPI e MongoDB, com frontend HTML/CSS e JavaScript modular sem build obrigatório. Doação e venda são ofertas com interesse, combinação de entrega e confirmação bilateral. Descarte é uma consulta pública de locais, independente de usuário ou equipamento.

A Etapa 18 está em validação integrada. O fluxo antigo por equipamento é removido: não há encaminhamentos, destinação informada, aba histórica ou adaptadores de compatibilidade. A alteração de código não executa limpeza nem migração de bancos reais.

## Responsabilidades

- **API (`app/api`)**: transporte HTTP, autorização, validação e projeções de resposta.
- **Schemas (`app/schemas`)**: campos aceitos e DTOs explícitos; itens usam somente doação/revenda.
- **Services (`app/services`)**: regras de ofertas, interesses, conta, avisos e gestão de locais.
- **Models/mappers**: domínio e conversão de subdocumentos de endereço, histórico de ofertas e combinação.
- **Repositories (`app/repositories`)**: persistência, consultas filtradas, índices e guardas de integridade.
- **Frontend (`frontend/`)**: páginas separadas e módulos por responsabilidade; toda autorização é repetida no servidor.
- **Composição (`app/main.py`)**: dependências, sessões em memória, handlers, CORS e bootstrap explícito dos índices.

## Execução integrada

Docker Compose reúne MongoDB, API e frontend. A configuração e os comandos estão no [README](../README.md). Testes usam bases isoladas identificadas e replica set quando exigem transações. Nunca recriar o banco de demonstração para facilitar uma validação.

## Coleções e relações

O runtime revisado utiliza cinco coleções:

- `usuarios`: pessoa/operador, endereço e hash da senha.
- `itens`: ofertas de doação/revenda, proprietário, condição, valor, status, especificações, histórico e referências dos participantes.
- `interesses`: uma relação item/pessoa, tentativas, seleção, preço congelado, combinação revisada e histórico.
- `pontos_coleta`: locais com responsável, endereço público, categorias, horário e situação ativa/inativa; não referenciam equipamentos.
- `notificacoes`: destinatário, evento de oferta, item/interesse, leitura privada e datas.

IDs persistidos são BSON ObjectId e expostos como strings. Datas são UTC com precisão de milissegundos; `data_adicao` é imutável e `data_modificacao` acompanha alterações. Não há coleção de visitas, intenção ou comprovante de descarte.

## Identidade e privacidade

Sessões em memória com cookie HttpOnly, senha com scrypt e sem JWT. O navegador envia `credentials: "include"`. Mutações validam origem, sessão e papel; propriedade/participação vem das relações persistidas. A preautorização de itens e gestão impede que JSON malformado antecipe a decisão de acesso. A sessão exige novo login após reinício do processo.

O catálogo de ofertas exige sessão e não publica endereço pessoal. A combinação é privada aos participantes autorizados. Leitura de notificações não transfere permissão sobre recursos.

## Diretório e gestão

Lista/detalhe de locais ativos são públicos. O DTO público permite apenas `id`, `nome`, `endereco`, `categorias_aceitas` e `horario_atendimento`. Cidade/categoria e visibilidade são filtradas no Mongo antes da paginação; nome/ID determinam ordem estável. Um local inativo não é recuperável pelo detalhe público.

`escopo=meus` escolhe a gestão, não uma projeção pública ampliada por cookie. Só operador consulta/cria e só o responsável edita, altera situação ou exclui seus locais. Operador alheio recebe indisponibilidade sem vazamento; pessoa e visitante não obtêm fallback público dessa operação. A interface “Meus locais” permite paginação, categorias do contrato e edição de endereço completo, preserva o formulário no erro e bloqueia mutações repetidas enquanto pendentes.

A consulta pública “Onde descartar” mantém filtros/página na URL e distingue carregamento, vazio, erro e indisponibilidade do detalhe. Copiar endereço não equivale a registrar descarte. Nenhuma consulta, cópia ou alteração de local cria equipamento, transação de descarte ou aviso desse fluxo.

## Fluxos de ofertas

Rascunho → disponível → reservado → aguardando confirmação → concluído. Arquivamento próprio segue as restrições existentes. Selecionar interesse estabelece reserva; a contraparte aceita a revisão da combinação. Proprietário declara a entrega e somente o selecionado confirma o recebimento. Terceiros não concluem uma oferta.

Histórico, integridade de referências, controle de status e avisos das ofertas permanecem. Versões genéricas e ledger de `id_operacao` descritos no alvo v2.1 não são campos implementados; consultar as diferenças em [contratos](../artefatos/v2.1/contratos_http.md).

## Avisos, indicadores e demonstração

Avisos e resultados pertencem às ofertas, nunca à navegação no diretório. A remoção das dependências do processo antigo faz parte da Etapa 18; a revisão geral de produto/indicadores e enriquecimento da demonstração continua na Etapa 19. O seeder usa somente ofertas e cadastro de locais, com reexecução aditiva e sem aplicar mudanças automaticamente à demonstração real.

## Testabilidade e reprodução

- `tests/`: testes unitários, transporte, MongoDB e Selenium.
- [Contrato HTTP](http-api.md) e [OpenAPI](openapi.md): documentação do executável e snapshot gerado.
- [Casos e matriz](../artefatos/v2.1/matriz_rastreabilidade.md): distinguem evidência atual e trabalho futuro.
- [Verificador de jornadas](../scripts/validar_jornadas_v2.py): a jornada pública completa no verificador será ajustada na Etapa 20; o processo antigo não é evidência atual.

Integrações sem URI de teste são ignoradas e não contam como aprovadas. Relatórios locais ficam em diretório ignorado, sem novos documentos de verificação em `docs/`.
