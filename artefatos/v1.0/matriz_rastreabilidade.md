# Matriz de rastreabilidade da versão 1.0

A coluna de evidência distingue a base existente do trabalho necessário para fechar a versão.

| Requisito/regra | Casos | Evidência |
|---|---|---|
| V1-RF-01 | V1-CT-01 a V1-CT-04 | Planejado: schema e API de usuário evoluídos |
| V1-RF-02, V1-RF-03 | V1-CT-05 | Base implementada; resposta ainda precisa migrar para endereço/datas novos |
| V1-RF-04 | V1-CT-06 | Planejado: atualização de auditoria |
| V1-RF-05 | V1-CT-07 | Base implementada |
| V1-RF-06 | V1-CT-08, V1-CT-09 | Planejado: API e coleção `itens` |
| V1-RF-07 | V1-CT-10 | Planejado: listagem e filtros de itens |
| V1-RF-08 | V1-CT-11 | Planejado: consulta de item |
| V1-RF-09 | V1-CT-12 | Planejado: atualização de item |
| V1-RF-10 | V1-CT-13 | Planejado: exclusão de item |
| V1-RF-11 | V1-CT-02, V1-CT-09, V1-CT-14, V1-CT-15 | Schemas e validações planejados |
| V1-RF-12 | — | OpenAPI atual existe; endpoints de itens pendentes |
| V1-RF-13 | V1-CT-21, V1-CT-22 | Planejado: Service e rota de login |
| V1-RF-14 | V1-CT-24 | Planejado: perfil autenticado |
| V1-RF-15 a V1-RF-17 | V1-CT-26, V1-CT-31 | Planejado: autorização por tipo e provisionamento |
| V1-RF-18 | V1-CT-23, V1-CT-25, V1-CT-27 | Planejado: respostas 401 e 403 |
| V1-RF-19 | V1-CT-32 a V1-CT-35 | Planejado: frontend simples separado |
| V1-RF-20 | V1-CT-36 | Planejado: logout e invalidação da sessão |
| V1-RN-01 a V1-RN-03 | V1-CT-01, V1-CT-31 | Tipos, provisionamento e validações básicas |
| V1-RN-04 a V1-RN-06 | V1-CT-01 a V1-CT-04 | Planejado: subdocumento de endereço |
| V1-RN-07 | V1-CT-01, V1-CT-06, V1-CT-08, V1-CT-12 | Planejado: auditoria nas duas coleções |
| V1-RN-08 | V1-CT-08, V1-CT-09, V1-CT-16 | Planejado: referência item/usuário |
| V1-RN-09 a V1-RN-13 | V1-CT-08, V1-CT-14, V1-CT-15 | Planejado: regras do item |
| V1-RN-14 | V1-CT-06, V1-CT-12 | Planejado: atualização e auditoria |
| V1-RN-15 | V1-CT-07, V1-CT-11, V1-CT-13 | Base 404 de usuários existe; itens pendentes |
| V1-RN-16 | V1-CT-16 | Planejado: contrato público de itens |
| V1-RN-17 | V1-CT-20 | Planejado: índice único de e-mail |
| V1-RN-18, V1-RN-19 | V1-CT-19 | Planejado: validação e hash da senha |
| V1-RN-20, V1-RN-21 | V1-CT-21 a V1-CT-23, V1-CT-37 | Planejado: login e sessão temporária |
| V1-RN-22 | V1-CT-28 | Planejado: tipo imutável |
| V1-RN-23 | V1-CT-24, V1-CT-25, V1-CT-27 | Planejado: propriedade do recurso |
| V1-RN-24 | V1-CT-26 | Planejado: permissões por tipo |
| V1-RN-25 | V1-CT-23, V1-CT-25, V1-CT-27 | Planejado: distinção 401/403 |
| V1-RN-26 | V1-CT-24, V1-CT-29 | Planejado: dados públicos/privados |
| V1-RN-27 | V1-CT-30 | Planejado: segredos e CORS |
| V1-RN-28, V1-RN-29 | V1-CT-33 a V1-CT-35 | Planejado: sessão e integração seguras no frontend |
| V1-RN-30 | V1-CT-32 a V1-CT-35 | Planejado: escopo visual mínimo |
| V1-RN-31, V1-RN-32 | V1-CT-36, V1-CT-37 | Planejado: cookie e encerramento da sessão |
| V1-RNF-01, V1-RNF-02 | V1-CT-16, V1-CT-17 | MongoDB validado; segunda coleção e endereço pendentes |
| V1-RNF-03, V1-RNF-04 | todos os casos implementados | Arquitetura atual será replicada para itens |
| V1-RNF-05, V1-RNF-06 | V1-CT-18 | Base atual: 6 testes e 94,44%; nova suíte pendente |
| V1-RNF-07 | — | Artefatos v1.0 atualizados; docs da API pendentes |
| V1-RNF-08 | — | GitHub e identificação por commit/tag pendentes |
| V1-RNF-09, V1-RNF-10 | V1-CT-17, V1-CT-18 | Configuração existente e validada para a base atual |
| V1-RNF-11, V1-RNF-12 | V1-CT-19, V1-CT-21 a V1-CT-23, V1-CT-36, V1-CT-37 | Planejado: hash e sessão |
| V1-RNF-13 | V1-CT-30 | Planejado: CORS e exposição mínima |
| V1-RNF-14 | V1-CT-19, V1-CT-22, V1-CT-29, V1-CT-30 | Planejado: respostas e logs seguros |
| V1-RNF-15 | V1-CT-32 a V1-CT-35 | Planejado: cliente web separado e sem build obrigatório |

## Estado resumido

- **Implementado:** base de CRUD simples de usuários.
- **Planejado para v1.0:** endereço aninhado, auditoria temporal, CRUD de itens, sessão simples, autorização básica e frontend simples.
- **Pendente externamente:** GitHub e identificação da versão.
