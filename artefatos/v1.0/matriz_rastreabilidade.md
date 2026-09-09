# Matriz de rastreabilidade da versão 1.0

A coluna de evidência distingue o núcleo de usuários já implementado das funcionalidades de itens e frontend ainda necessárias para fechar a versão.

| Requisito/regra | Casos | Evidência |
|---|---|---|
| V1-RF-01 | V1-CT-01 a V1-CT-04 | Implementado no núcleo de usuários; provisionamento controlado de `ponto_coleta` por comando local |
| V1-RF-02, V1-RF-03 | V1-CT-05 | Implementado com resumo público e perfil completo do titular |
| V1-RF-04 | V1-CT-06 | Implementado com `data_adicao` preservada e `data_modificacao` renovada |
| V1-RF-05 | V1-CT-07 | Implementado com autorização pela sessão |
| V1-RF-06 | V1-CT-08, V1-CT-09 | Implementado na coleção `itens` e no `ItemService` |
| V1-RF-07 | V1-CT-10 | Implementado com catálogo e filtros |
| V1-RF-08 | V1-CT-11 | Implementado com consulta e `404` |
| V1-RF-09 | V1-CT-12 | Implementado com preservação de identidade e auditoria |
| V1-RF-10 | V1-CT-13 | Implementado com autorização do proprietário |
| V1-RF-11 | V1-CT-02, V1-CT-09, V1-CT-14, V1-CT-15 | Implementado com validações de usuário e item |
| V1-RF-12 | — | OpenAPI de usuários, autenticação e itens disponível |
| V1-RF-13 | V1-CT-21, V1-CT-22 | Implementado para usuários |
| V1-RF-14 | V1-CT-24 | Implementado em `/api/usuarios/me` |
| V1-RF-15 a V1-RF-17 | V1-CT-26, V1-CT-31 | Autorização por tipo e propriedade implementada; provisionamento controlado de `ponto_coleta` implementado |
| V1-RF-18 | V1-CT-23, V1-CT-25, V1-CT-27 | `401` e `403` implementados para usuários e itens |
| V1-RF-19 | V1-CT-32 a V1-CT-35 | Planejado: frontend simples separado |
| V1-RF-20 | V1-CT-36 | Implementado com remoção da sessão e expiração do cookie |
| V1-RN-01 a V1-RN-03 | V1-CT-01, V1-CT-31 | Tipos de cadastro, validações e provisionamento controlado implementados |
| V1-RN-04 a V1-RN-06 | V1-CT-01 a V1-CT-04 | Implementado no subdocumento de endereço |
| V1-RN-07 | V1-CT-01, V1-CT-06, V1-CT-08, V1-CT-12 | Implementado para usuários e itens |
| V1-RN-08 | V1-CT-08, V1-CT-09, V1-CT-16 | Implementado com referência e validação do proprietário |
| V1-RN-09 a V1-RN-13 | V1-CT-08, V1-CT-14, V1-CT-15 | Implementado com enumerações, valor condicional e campos controlados |
| V1-RN-14 | V1-CT-06, V1-CT-12 | Implementado para usuários e itens |
| V1-RN-15 | V1-CT-07, V1-CT-11, V1-CT-13 | `404` implementado para usuários e itens |
| V1-RN-16 | V1-CT-16 | Implementado com cidade derivada e sem endereço duplicado |
| V1-RN-17 | V1-CT-20 | Implementado com normalização e índice único de e-mail |
| V1-RN-18, V1-RN-19 | V1-CT-19 | Implementado com validação e hash scrypt |
| V1-RN-20, V1-RN-21 | V1-CT-21 a V1-CT-23, V1-CT-37 | Implementado para login e sessão temporária |
| V1-RN-22 | V1-CT-28 | Implementado; `tipo` não está no contrato de atualização |
| V1-RN-23 | V1-CT-24, V1-CT-25, V1-CT-27 | Implementado para usuário e propriedade de item |
| V1-RN-24 | V1-CT-26 | Implementado para consulta, cadastro e gestão de itens |
| V1-RN-25 | V1-CT-23, V1-CT-25, V1-CT-27 | Implementado para autenticação e autorização de usuários |
| V1-RN-26 | V1-CT-24, V1-CT-29 | Implementado nos resumos públicos de usuários |
| V1-RN-27 | V1-CT-30 | CORS configurável e sem origem curinga implementado |
| V1-RN-28, V1-RN-29 | V1-CT-33 a V1-CT-35 | Planejado: frontend simples e integração segura |
| V1-RN-30 | V1-CT-32 a V1-CT-35 | Planejado: escopo visual mínimo |
| V1-RN-31, V1-RN-32 | V1-CT-36, V1-CT-37 | Implementado para cookie e encerramento da sessão |
| V1-RNF-01, V1-RNF-02 | V1-CT-16, V1-CT-17 | MongoDB, duas coleções e endereço de usuário implementados |
| V1-RNF-03, V1-RNF-04 | V1-CT-01 a V1-CT-37 | Arquitetura em camadas implementada para usuários e itens |
| V1-RNF-05, V1-RNF-06 | V1-CT-18 | 39 testes aprovados; cobertura total de 94,28% |
| V1-RNF-07 | — | Artefatos v1.0, contratos HTTP e arquitetura atualizados |
| V1-RNF-08 | — | GitHub e identificação por commit/tag pendentes |
| V1-RNF-09, V1-RNF-10 | V1-CT-17, V1-CT-18 | Configuração segura e compatibilidade da base de usuários |
| V1-RNF-11, V1-RNF-12 | V1-CT-19, V1-CT-21 a V1-CT-23, V1-CT-36, V1-CT-37 | Hash e sessão implementados |
| V1-RNF-13 | V1-CT-30 | CORS e exposição mínima implementados para usuários e itens |
| V1-RNF-14 | V1-CT-19, V1-CT-22, V1-CT-29, V1-CT-30 | Respostas de login e exposição de dados implementadas; logs específicos ainda pendentes |
| V1-RNF-15 | V1-CT-32 a V1-CT-35 | Planejado: cliente web separado e sem build obrigatório |

## Estado resumido

- **Implementado:** usuários e itens com endereço aninhado, auditoria temporal, hash, sessão, autorização, provisionamento controlado, filtros, testes e documentação correspondente.
- **Concluído na base de backend:** validação dos dois CRUDs contra MongoDB 7.0 real via Docker Compose, incluindo índices e limpeza dos dados de teste.
- **Planejado para v1.0:** frontend simples.
- **Pendente externamente:** GitHub e identificação da versão.
