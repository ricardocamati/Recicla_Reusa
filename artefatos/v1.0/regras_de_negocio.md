# Regras de negócio da versão 1.0

> Regras da primeira entrega. O CRUD de itens está implementado; transições de ciclo de vida, interesses e coleta permanecem na v2.0.

## V1-RN-01 — Tipos de usuário

`tipo` aceita somente `doador`, `beneficiario` ou `ponto_coleta`. O cadastro público permite apenas os dois primeiros; `ponto_coleta` é provisionado pelo responsável técnico pelo comando local `python -m app.provisionar_ponto_coleta`, que não aceita o tipo como entrada e solicita a senha sem eco.

## V1-RN-02 — Limites dos dados do usuário

| Campo | Mínimo | Máximo |
|---|---:|---:|
| `nome` | 3 | 120 |
| `email` | 5 | 160 |
| campos textuais do endereço | 1 | 160 |

## V1-RN-03 — Formato do e-mail

O e-mail deve conter `@` e pelo menos um ponto depois do `@`.

## V1-RN-04 — Campos planos do endereço

O contrato HTTP agrupa `logradouro`, `numero`, `complemento`, `cep` e `cidade` em `endereco`, mas o modelo de domínio e o documento MongoDB mantêm esses campos no nível raiz; `usuarios.endereco` não é persistido.

## V1-RN-05 — Obrigatoriedade do endereço

`logradouro`, `numero`, `cep` e `cidade` são obrigatórios; `complemento` é opcional. Espaços externos são removidos antes da gravação dos campos planos.

## V1-RN-06 — CEP e número

CEP aceita entrada com ou sem hífen e é armazenado com oito dígitos. `numero` é texto para aceitar `12A` e `S/N`.

## V1-RN-07 — Datas de auditoria

Todo documento de `usuarios` e `itens` possui `data_adicao` e `data_modificacao`, controladas pelo servidor em UTC. Na criação são iguais; na atualização apenas `data_modificacao` muda.

## V1-RN-08 — Proprietário do item

Todo item referencia um `proprietario_id` existente em `usuarios`. O valor é obtido do usuário autenticado e não aceito do corpo da requisição. O endereço do usuário não é copiado para o item.

## V1-RN-09 — Condições permitidas

`condicao` aceita `funcional`, `funcional_com_defeito`, `reparavel`, `sem_conserto` ou `recondicionado`.

## V1-RN-10 — Destinos permitidos

`destino` aceita `doacao`, `descarte` ou `revenda`.

## V1-RN-11 — Status inicial

Todo item novo começa com `status` igual a `disponivel`.

## V1-RN-12 — Valor

Item de revenda exige `valor` não negativo. Itens de doação ou descarte não possuem preço de venda.

## V1-RN-13 — Campos controlados pelo servidor

Cliente não informa nem altera `id`, datas de auditoria, status inicial ou `proprietario_id`.

## V1-RN-14 — Atualização

Atualização preserva `id`, `data_adicao` e, no item, `proprietario_id`; `data_modificacao` recebe novo instante UTC.

## V1-RN-15 — Recurso inexistente

Consulta, atualização ou exclusão de recurso inexistente retorna HTTP `404` sem criar ou alterar documentos. Exceção de precedência: em `PUT` e `DELETE` de usuário, a sessão e a propriedade são verificadas antes da existência do identificador; uma sessão válida tentando atingir outro identificador recebe `403`, inclusive quando esse identificador não existe, para não revelar dados de terceiros.

## V1-RN-16 — Privacidade

Listagem pública de itens pode apresentar a cidade do proprietário, mas não seu endereço completo.

## V1-RN-17 — E-mail único

O e-mail é normalizado para minúsculas e deve ser único. Tentativa de duplicação retorna HTTP `409`.

## V1-RN-18 — Senha mínima

Senha deve possuir de 8 a 128 caracteres e incluir pelo menos uma letra e um número. Espaços não são removidos silenciosamente.

## V1-RN-19 — Armazenamento da senha

Somente `senha_hash` é persistida, usando scrypt com salt aleatório. Senha e hash nunca aparecem em respostas ou logs.

## V1-RN-20 — Login

Login compara a senha com o hash e retorna mensagem genérica para credenciais inválidas, sem confirmar se o e-mail existe.

## V1-RN-21 — Sessão temporária

O login cria um identificador aleatório de alta entropia associado no servidor ao ID e ao tipo do usuário. A sessão expira 30 minutos após o login e é removida no logout ou na reinicialização da aplicação.

## V1-RN-22 — Perfil imutável pelo usuário

O campo `tipo` é definido no cadastro ou provisionamento e não pode ser alterado pela atualização comum, evitando elevação de permissão.

## V1-RN-23 — Propriedade do recurso

Atualização e exclusão de usuário exigem que o usuário da sessão corresponda ao recurso. Atualização e exclusão de item exigem correspondência com `proprietario_id`.

## V1-RN-24 — Permissões por tipo

| Operação | doador | beneficiario | ponto_coleta |
|---|:---:|:---:|:---:|
| Consultar catálogo | sim | sim | sim |
| Cadastrar item | sim | não | não |
| Alterar/excluir item próprio | sim | não | não |
| Filtrar itens para descarte | sim | sim | sim |
| Registrar interesse | v2.0 | v2.0 | não |
| Confirmar coleta | v2.0 | não | v2.0 |

## V1-RN-25 — Falhas de autenticação e autorização

Sessão ausente, inválida ou expirada gera HTTP `401`. Em mutações com cookie de sessão, origem ausente ou não permitida também gera HTTP `403`. Usuário autenticado sem perfil ou propriedade gera HTTP `403`. Para usuários, a propriedade é verificada antes da existência do ID; por isso, `PUT`/`DELETE` de outro ID retornam `403` mesmo quando o recurso não existe. Para itens, o Service busca o item antes da propriedade: item inexistente retorna `404`, item existente de outro proprietário retorna `403`.

## V1-RN-26 — Dados públicos de usuário

Resumo público contém somente `id`, `nome`, `tipo` e cidade. E-mail, endereço completo, senha e hash são privados.

## V1-RN-27 — Configuração de segurança

Credenciais do banco ficam em variáveis de ambiente. CORS aceita somente origens explicitamente configuradas, permite credenciais apenas para essas origens e nunca usa origem curinga com cookies. Além do CORS, o backend valida `Origin` ou `Referer` em toda mutação que carrega o cookie de sessão; ausência ou divergência é rejeitada com `403`.

## V1-RN-28 — Segurança do frontend

O frontend não armazena senha, hash ou identificador de sessão. O navegador envia automaticamente o cookie HttpOnly usando `credentials: "include"`; JavaScript não consegue lê-lo. Dados vindos da API são inseridos no DOM como texto, sem interpretar HTML fornecido pelo usuário.

## V1-RN-29 — Interface não substitui autorização

Ocultar um botão conforme o perfil melhora a experiência, mas toda permissão continua validada no backend. Resposta `401` leva novamente ao login; `403` informa que a ação não é permitida.

## V1-RN-30 — Escopo visual mínimo

O frontend da v1.0 cobre cadastro, login, perfil, catálogo, filtros e gestão de itens próprios. Interesses, notificações, pontos de coleta detalhados e fluxos completos permanecem fora da interface da v1.0.

## V1-RN-31 — Cookie da sessão

O cookie `recicla_sessao` usa `HttpOnly`, `SameSite=Lax`, `Path=/` e duração máxima de 30 minutos. Em ambiente HTTPS também usa `Secure`. Toda operação mutável que carrega esse cookie precisa apresentar `Origin` ou `Referer` configurado; a própria origem da API também é aceita para chamadas same-origin.

## V1-RN-32 — Encerramento da sessão

`POST /api/auth/logout` remove a sessão no servidor e expira o cookie no navegador. Como as sessões da v1.0 ficam em memória, reiniciar a API encerra todas as sessões, limitação aceitável para a PoC.
