# v2.1 — Coerência de negócio e usabilidade

## Revisão aprovada: descarte como diretório

**“Onde descartar” passa a ser uma consulta pública de locais, sem login nem cadastro de item.** Doação e venda continuam centradas no equipamento: publicação, interesse, reserva, combinação e confirmação bilateral. O operador mantém o cadastro dos próprios locais, sem fila ou confirmação de entregas no novo fluxo de descarte.

**Implementação parcial da revisão: Etapas 16 e 17 concluídas.** A base anterior é `f216802`, integração do PR #25 com os ajustes do PR #26. Lista e detalhe de pontos ativos agora são públicos, com DTO reduzido, filtros/paginação e escopo de gestão protegido. A tela pública está implementada em `frontend/onde-descartar.html` (Etapa 17), com entradas pública e autenticada, filtros/paginação, detalhe e cópia de endereço. A retirada do processo por item (Etapa 18) e a revisão de avisos/indicadores/demonstração (Etapa 19) continuam pendentes. Dados anteriores não são migrados, convertidos ou excluídos: mantêm suas referências e permissões; as rotas antigas continuam até a descontinuação coordenada.

## Documentos e autoridade

| Documento | Responsabilidade |
|---|---|
| [Requisitos](requisitos.md) | Escopo e aceitação da revisão |
| [Regras de negócio](regras_de_negocio.md) | Acesso, invariantes e exclusões |
| [Jornadas e frontend](jornadas_frontend.md) | Navegação, filtros, cartões e estados |
| [Modelo de dados](modelo_dados.md) | Modelo-alvo e registros legados |
| [Contratos HTTP](contratos_http.md) | Consultas propostas e diferenças do runtime |
| [Casos de teste](casos_de_teste.md) | Critérios escritos, não resultados de execução |
| [Matriz](matriz_rastreabilidade.md) | Rastreabilidade, código existente e implementação pendente |

Requisitos delimitam escopo; regras definem comportamento; os demais artefatos devem corresponder a ambos. Para o programa existente, continuam valendo o [contrato atual](../../docs/http-api.md) e a [OpenAPI gerada](../../docs/openapi.md).

## Experiência recomendada

1. Abrir “Onde descartar” pela entrada do site, sem conta ou item.
2. Filtrar por cidade e tipo/categoria do eletrônico; filtros opcionais e cumulativos.
3. Consultar locais ativos, com paginação, nome, endereço público, categorias aceitas e horário quando disponível.
4. Abrir detalhes ou copiar o endereço. Um link opcional pode abrir o endereço público em mapa externo por ação explícita, sem mapa embutido, API geográfica ou geolocalização.
5. Sem resultados, alterar/limpar filtros, sem registrar descarte ou exigir cadastro.

Consulta, detalhe, cópia de endereço e abertura de mapa não comprovam entrega, recebimento ou reciclagem e não geram indicadores desses acontecimentos. A consulta deve funcionar sem serviço externo.

## O que sai do escopo

- Cadastro de equipamento para localizar um ponto.
- Registro, troca e cancelamento de entrega prevista.
- Confirmação ou impossibilidade de recebimento pelo operador.
- Indicação privada de outro lugar como encerramento de um item.
- Avisos e indicadores decorrentes de operações de descarte.

Identificadores retirados permanecem marcados, sem reutilização para outros significados nem transformação em pendências futuras. O desenho anterior fica no histórico Git, não como uma segunda alternativa normativa.

## Implementação e evidências

| Frente | Código de referência | Alvo revisado |
|---|---|---|
| Descarte | Item, encaminhamento ou destinação informada | Diretório independente de item |
| Consulta | Etapas 16–17: API pública e tela “Onde descartar”, filtros/paginação e detalhe | Gestão revisada e retirada do processo anterior pendentes |
| Operador | Locais e entregas | Gestão autenticada dos próprios locais |
| Indicadores | Incluem recebidos e indicados | Resultados de doação/venda separados de informações do diretório |
| Dados | Seis coleções, inclusive `encaminhamentos` | Preservar documentos e referências anteriores |

Testes e jornadas anteriores não comprovam o novo diretório. Os novos casos começam em V21-CT-35; os casos de descarte retirados mantêm seus IDs. A Etapa 16 entrega leitura e testes em `tests/test_diretorio_publico.py` e `tests/test_diretorio_runtime.py`. A Etapa 17 tem testes de interface em `tests/test_onde_descartar_selenium.py` e jornada anônima com HTTP/API/MongoDB reais em `tests/test_onde_descartar_browser_runtime.py`, incluindo snapshots. Retirada do processo antigo e indicadores continuam pendentes; essa evidência não aprova toda a revisão.

## Preservação e exclusões

Nenhuma migração, conversão de item, povoamento ou exclusão é executada por esta revisão. Política da Etapa 16: manter documentos anteriores e permissões originais; a nova consulta não projeta itens/indicações privadas. A apresentação do histórico na descontinuação fica para a Etapa 18; não limpar o banco por conveniência.

Permanecem fora do incremento: pagamentos, transporte domiciliar, agendamento/capacidade, chat em tempo real, fotos/upload, certificação, mapas embutidos e APIs geográficas, infraestrutura de publicação na internet e o tópico I já excluído. Consulta sem login não implica implantação pública nem remoção da autorização de gestão.

Os critérios mais amplos de doação/venda, versões e recuperação por chave continuam separados do runtime; esta mudança não os declara implementados. O [README do projeto](../../README.md) descreve a leitura entregue; o TODO mantém as etapas posteriores pendentes.
