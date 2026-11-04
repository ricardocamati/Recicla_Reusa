# v2.1 — Coerência de negócio e usabilidade

A revisão v2.1 tem implementação nas Etapas 9 a 15, sobre o marco v2.0 (`71e8dfa`, PR #18). O fechamento funcional está no commit `1f36c2b` (PR #25). Isso identifica o código analisado, não declara que o PR foi integrado nem que todos os critérios do desenho original foram comprovados.

## Objetivo

Permitir que pessoas ofereçam eletrônicos para doação/venda e organizem a entrega de descartes em pontos físicos, sabendo quem deve agir e como cancelar uma tentativa ainda não concluída. O autor também pode informar outro lugar, sem verificação externa.

## Documentos e autoridade

| Documento | Responsabilidade |
|---|---|
| [Requisitos](requisitos.md) | Escopo e critérios de aceitação; não constituem resultado de teste |
| [Regras de negócio](regras_de_negocio.md) | Regras de produto e transições do desenho aprovado |
| [Jornadas e frontend](jornadas_frontend.md) | Experiência desejada e limites da interface entregue |
| [Modelo de dados](modelo_dados.md) | Estrutura executável, diferenças e desenho original preservado |
| [Contratos HTTP](contratos_http.md) | Diferenças entre operações implementadas e contrato originalmente planejado |
| [Casos de teste](casos_de_teste.md) | Cenários escritos; comprovação depende da automação correspondente |
| [Matriz](matriz_rastreabilidade.md) | Requisito → regra → cenário → código/testes e limites |

Para executar a aplicação, use o [README](../../README.md), o [contrato HTTP atual](../../docs/http-api.md) e a [OpenAPI](../../docs/openapi.md). O desenho de produto não deve ser apresentado como contrato implementado quando houver diferença explícita.

## Implementação e evidências

- Conta única de pessoa, catálogo de ofertas e cadastro por intenção.
- Interesse com retomada/reabertura, seleção única e reserva reversível.
- Combinação revisada, declaração de entrega e confirmação bilateral; venda direta de usado.
- Encaminhamentos com histórico e operação do ponto, ou destinação informada apenas pelo autor.
- Avisos com links internos e indicadores de ofertas, pendências e conclusões.
- Filtros do catálogo preservados no endereço e tratamento de erros/rede.

A execução funcional da Etapa 15 aprovou 201 testes e três jornadas em stack isolada, sem medição de cobertura nessa execução. Reprodução: [testes](../../tests/), [jornadas](../../scripts/validar_jornadas_v2.py) e comandos do README. Não são mantidos relatórios de verificação separados.

## Limites que não devem ser tratados como concluídos

- O contrato genérico de `id_operacao`, versões esperadas e recuperação persistida por chave não foi implementado. A revisão da combinação e verificações de estado não equivalem a esse mecanismo.
- O catálogo da interface carrega até 100 registros, sem navegação por páginas. Filtros são preservados no endereço; paginação da API não comprova paginação da interface.
- Links dos avisos abrem a tela de ação, não necessariamente um registro específico. Existência de link não comprova emissão de aviso para cada evento previsto.
- Os cenários escritos são critérios, não uma declaração de que cada passo foi automatizado. A matriz delimita a evidência disponível.
- Integração do marco final, medição de cobertura e vídeo são passos próprios da entrega acadêmica.

## Preservação dos dados e exclusões

A migração de perfis está em `scripts/migrar_papeis_v2_1.py`: simula por padrão e aplica somente com `--aplicar`. Esta documentação não autoriza migração, exclusão ou recriação do banco de demonstração.

Pagamentos, transporte/retirada domiciliar, mapas externos, chat em tempo real, fotos/upload, certificação e infraestrutura para internet ficam fora do incremento. O tópico I da discussão foi excluído pelo usuário; login e proteções básicas são preservados.
