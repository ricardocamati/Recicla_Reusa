# Matriz de rastreabilidade da versão 2.0

Todas as evidências desta matriz são esperadas para a segunda entrega até que o código correspondente seja implementado e validado.

| Requisito/regra | Casos de teste | Evidência esperada |
|---|---|---|
| V2-RF-01 | V2-CT-01 a V2-CT-04 | schemas, API e Repository de usuários evoluídos |
| V2-RF-02 | V2-CT-05 | CRUD de usuários com auditoria |
| V2-RF-03 | V2-CT-06, V2-CT-07 | coleção e API de itens |
| V2-RF-04 | V2-CT-08, V2-CT-09 | catálogo e filtros |
| V2-RF-05 | V2-CT-15, V2-CT-16, V2-CT-21 | Service de itens e histórico |
| V2-RF-06 | V2-CT-10, V2-CT-11 | coleção de interesses |
| V2-RF-07 | V2-CT-12 | transições de interesse |
| V2-RF-08 | V2-CT-13 | coleção de pontos de coleta |
| V2-RF-09 | V2-CT-14, V2-CT-18 | relação item/ponto |
| V2-RF-10 | V2-CT-15 | lista `historico` |
| V2-RF-11 | V2-CT-12, V2-CT-17 | fluxo de doação |
| V2-RF-12 | V2-CT-14, V2-CT-18 | fluxo de descarte |
| V2-RF-13 | V2-CT-19, V2-CT-20 | fluxo de revenda |
| V2-RF-14 | V2-CT-23 | indicadores |
| V2-RF-15 | V2-CT-05, V2-CT-24 | auditoria temporal |
| V2-RF-16 | — | OpenAPI final |
| V2-RF-17 | V2-CT-26 a V2-CT-30 | coleção, Service e API de notificações |
| V2-RN-01 a V2-RN-04 | V2-CT-01 a V2-CT-04, V2-CT-13 | endereço aninhado |
| V2-RN-05 | V2-CT-01, V2-CT-05, V2-CT-24 | datas em UTC |
| V2-RN-06 a V2-RN-09 | V2-CT-06, V2-CT-07 | criação de item |
| V2-RN-10 | V2-CT-16 a V2-CT-19 | transições válidas |
| V2-RN-11 | V2-CT-15 | histórico acumulativo |
| V2-RN-12, V2-RN-13 | V2-CT-10 a V2-CT-12 | interesses e reserva |
| V2-RN-14 | V2-CT-14, V2-CT-18 | compatibilidade do ponto |
| V2-RN-15 | V2-CT-19, V2-CT-20 | valor de revenda |
| V2-RN-16 | V2-CT-17 a V2-CT-21 | conclusão única |
| V2-RN-17, V2-RN-18 | V2-CT-08, V2-CT-22 | privacidade do endereço |
| V2-RN-19 | V2-CT-06 | especificações flexíveis |
| V2-RN-20 | V2-CT-23 | indicadores concluídos |
| V2-RN-21, V2-RN-22 | V2-CT-26, V2-CT-27, V2-CT-30 | destinatários e eventos notificáveis |
| V2-RN-23, V2-RN-25 | V2-CT-28 | leitura e auditoria da notificação |
| V2-RN-24 | V2-CT-29 | deduplicação por evento |
| V2-RNF-01 a V2-RNF-03 | V2-CT-06 a V2-CT-30 | múltiplas coleções e referências |
| V2-RNF-04 | todos os casos implementados | arquitetura e código final |
| V2-RNF-05, V2-RNF-06 | V2-CT-25 | Pytest e cobertura |
| V2-RNF-07 | — | documentação final |
| V2-RNF-08 | — | commit, tag ou release v2.0 |
| V2-RNF-09 | V2-CT-08, V2-CT-22 | catálogo sem endereço privado |
| V2-RNF-10 | V2-CT-24, V2-CT-25 | ambiente reproduzível |

## Evidências externas necessárias

- quadro de tarefas/metodologia;
- URL do GitHub;
- identificação da versão 2.0;
- demonstração da evolução em relação à versão 1.0.
