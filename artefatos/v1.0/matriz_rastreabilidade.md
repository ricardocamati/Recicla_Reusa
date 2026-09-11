# Matriz de rastreabilidade da versão 1.0

Esta matriz é bidirecional. A primeira tabela parte de cada requisito/regra e aponta para o símbolo de implementação, o caso e a evidência. A segunda parte de cada caso e aponta para a função automatizada ou para a evidência manual reproduzível. `Automatizado` identifica execução por Pytest/script; `manual` identifica inspeção externa ainda não substituída por teste.

## Requisito/regra → implementação → caso/evidência

| Requisito/regra | Caso(s) | Implementação (arquivo :: símbolo) | Automação/evidência | Tipo/estado |
|---|---|---|---|---|
| V1-RF-01 | V1-CT-01 a V1-CT-04, V1-CT-31 | `app/schemas/usuario.py :: UsuarioCreateRequest`; `app/services/usuario_service.py :: UsuarioService.criar`; `app/provisionar_ponto_coleta.py :: provisionar` | `tests/test_api_usuario.py`; `tests/test_provisionamento_ponto_coleta.py` | automatizado / implementado |
| V1-RF-02, V1-RF-03 | V1-CT-05, V1-CT-29 | `app/api/usuarios.py :: listar/buscar_por_id`; `app/mappers/usuario_mapper.py :: para_resumo/para_resposta` | `tests/test_api_usuario.py::test_listagem_de_terceiros_expoe_somente_resumo_publico` | automatizado / implementado |
| V1-RF-04 | V1-CT-06, V1-CT-12, V1-CT-25 | `app/services/usuario_service.py :: UsuarioService.atualizar`; `app/services/item_service.py :: ItemService.atualizar` | `tests/test_api_usuario.py::test_atualizacao_autenticada_preserva_tipo_e_data_adicao`; `tests/test_item_service.py::test_atualizar_preserva_identidade_proprietario_e_data_adicao` | automatizado / implementado |
| V1-RF-05 | V1-CT-07, V1-CT-25 | `app/api/usuarios.py :: atualizar/excluir`; `app/services/usuario_service.py :: UsuarioService` | `tests/test_api_usuario.py::test_atualizacao_de_outro_usuario_retorna_403`; `tests/test_api_usuario.py::test_exclusao_exige_sessao_e_propriedade` | automatizado / implementado |
| V1-RF-06 | V1-CT-08, V1-CT-09 | `app/api/itens.py :: criar`; `app/services/item_service.py :: ItemService.criar` | `tests/test_api_item.py::test_doador_cadastra_item_valido_e_nao_duplica_endereco`; `tests/test_item_service.py::test_criar_item_define_proprietario_status_e_auditoria` | automatizado / implementado |
| V1-RF-07 | V1-CT-10 | `app/api/itens.py :: listar`; `app/services/item_service.py :: ItemService.listar` | `tests/test_api_item.py::test_listar_filtra_itens_por_categoria_destino_e_status` | automatizado / implementado |
| V1-RF-08 | V1-CT-11 | `app/api/itens.py :: buscar_por_id`; `app/services/item_service.py :: ItemService.buscar_por_id` | `tests/test_api_item.py::test_catalogo_exige_sessao_e_item_invalido_retorna_404` | automatizado / implementado |
| V1-RF-09 | V1-CT-12 | `app/api/itens.py :: atualizar`; `app/services/item_service.py :: ItemService.atualizar` | `tests/test_api_item.py::test_atualizar_e_excluir_item_exigem_o_proprietario`; `tests/test_item_service.py::test_atualizar_preserva_identidade_proprietario_e_data_adicao` | automatizado / implementado |
| V1-RF-10 | V1-CT-13 | `app/api/itens.py :: excluir`; `app/services/item_service.py :: ItemService.excluir` | `tests/test_api_item.py::test_atualizar_e_excluir_item_exigem_o_proprietario` | automatizado / implementado |
| V1-RF-11 | V1-CT-14, V1-CT-15 | `app/schemas/item.py :: ItemCreateRequest`; `app/schemas/item.py :: validar_valor` | `tests/test_api_item.py::test_validacao_de_enums_e_valor_de_revenda` | automatizado / implementado |
| V1-RF-12 | V1-CT-38 | `app/main.py :: criar_app` e geração OpenAPI do FastAPI | `scripts/validar_stack_docker.py` (`/docs` e `/openapi.json`); `docs/http-api.md` | automatizado/script / implementado |
| V1-RF-13 | V1-CT-21, V1-CT-22 | `app/api/usuarios.py :: login`; `app/security/sessions.py :: ArmazenamentoDeSessoes` | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only`; `tests/test_api_usuario.py::test_login_invalido_tem_resposta_generica` | automatizado / implementado |
| V1-RF-14 | V1-CT-24 | `app/api/usuarios.py :: meu_perfil`; `app/services/usuario_service.py :: buscar_por_id` | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado / implementado |
| V1-RF-15 a V1-RF-17 | V1-CT-26, V1-CT-31 | `app/api/itens.py :: exigir_doador`; `app/api/usuarios.py :: criar`; `app/provisionar_ponto_coleta.py` | `tests/test_api_item.py::test_beneficiario_nao_pode_cadastrar_item`; `tests/test_api_item.py::test_ponto_coleta_consulta_mas_nao_cadastra_item`; `tests/test_provisionamento_ponto_coleta.py` | automatizado / implementado |
| V1-RF-18 | V1-CT-23, V1-CT-25, V1-CT-27, V1-CT-37 | `app/api/usuarios.py :: sessao_obrigatoria`; `app/api/itens.py :: sessao_obrigatoria`; `app/main.py :: proteger_mutacao_por_origem` | `tests/test_api_usuario.py`; `tests/test_api_item.py`; `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403` | automatizado / implementado |
| V1-RF-19 | V1-CT-32 a V1-CT-35, V1-CT-39 | `frontend/*.html`; `frontend/js/*.js`; `frontend/styles.css` | `tests/test_frontend.py`; `tests/test_selenium_frontend.py::test_selenium_navega_nas_seis_telas_em_modo_escuro` | automatizado / implementado |
| V1-RF-20 | V1-CT-36 | `app/api/usuarios.py :: logout`; `app/security/sessions.py :: remover` | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado / implementado |
| V1-RN-01 a V1-RN-03 | V1-CT-01, V1-CT-02, V1-CT-31 | `app/schemas/usuario.py :: UsuarioCreateRequest`; `app/provisionar_ponto_coleta.py :: ProvisionamentoRequest` | `tests/test_api_usuario.py`; `tests/test_provisionamento_ponto_coleta.py` | automatizado / implementado |
| V1-RN-04 a V1-RN-06 | V1-CT-01 a V1-CT-04 | `app/schemas/usuario.py :: CamposEndereco`; `app/mappers/usuario_mapper.py :: campos_endereco`; `app/repositories/mongo_usuario_repository.py :: _para_documento/_para_modelo` | `tests/test_api_usuario.py::test_cadastro_persiste_endereco_datas_e_nao_expoe_senha`; `tests/test_usuario_service.py::test_criar_usuario_registra_datas_endereco_e_id`; `tests/test_mongo_usuario_repository.py::test_repositorio_persiste_endereco_datas_e_remove_usuario` | automatizado / implementado |
| V1-RN-07 | V1-CT-01, V1-CT-06, V1-CT-08, V1-CT-12 | `app/services/usuario_service.py`; `app/services/item_service.py`; repositories Mongo | `tests/test_api_usuario.py`; `tests/test_item_service.py`; `tests/test_mongo_*_repository.py` | automatizado / implementado |
| V1-RN-08 | V1-CT-08, V1-CT-09, V1-CT-16 | `app/services/item_service.py :: criar/_obter_doador`; `app/mappers/item_mapper.py` | `tests/test_api_item.py::test_doador_cadastra_item_com_proprietario_da_sessao`; `tests/test_item_service.py::test_criar_item_rejeita_proprietario_inexistente` | automatizado / implementado |
| V1-RN-09 a V1-RN-13 | V1-CT-14, V1-CT-15 | `app/schemas/item.py`; `app/mappers/item_mapper.py` | `tests/test_api_item.py::test_validacao_de_enums_e_valor_de_revenda`; `tests/test_item_service.py::test_criar_item_define_proprietario_status_e_auditoria` | automatizado / implementado |
| V1-RN-14 | V1-CT-06, V1-CT-12 | `app/services/usuario_service.py :: atualizar`; `app/services/item_service.py :: atualizar` | testes de atualização de usuário e item listados acima | automatizado / implementado |
| V1-RN-15 | V1-CT-07, V1-CT-11, V1-CT-13, V1-CT-25, V1-CT-37 | `app/api/usuarios.py :: atualizar/excluir`; `app/services/item_service.py :: _buscar_item`; `app/main.py :: handlers` | `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403`; `tests/test_api_item.py::test_catalogo_exige_sessao_e_item_invalido_retorna_404` | automatizado / precedência documentada |
| V1-RN-16 | V1-CT-16, V1-CT-29 | `app/mappers/item_mapper.py :: para_resposta`; `app/mappers/usuario_mapper.py :: para_resumo` | `tests/test_api_item.py::test_doador_cadastra_item_valido_e_nao_duplica_endereco`; `tests/test_api_usuario.py::test_listagem_de_terceiros_expoe_somente_resumo_publico` | automatizado / implementado |
| V1-RN-17 | V1-CT-20 | `app/services/usuario_service.py :: _verificar_email_disponivel`; `app/repositories/mongo_usuario_repository.py` | `tests/test_api_usuario.py::test_cadastro_rejeita_ponto_de_coleta_e_email_duplicado`; `tests/test_usuario_service.py::test_email_normalizado_nao_pode_ser_repetido` | automatizado / implementado |
| V1-RN-18, V1-RN-19 | V1-CT-19 | `app/schemas/usuario.py`; `app/security/passwords.py :: hash_password/verify_password` | `tests/test_security.py::test_senha_e_armazenada_com_hash_e_verificada_sem_expor_valor`; `tests/test_api_usuario.py::test_cadastro_persiste_endereco_datas_e_nao_expoe_senha` | automatizado / implementado |
| V1-RN-20, V1-RN-21 | V1-CT-21 a V1-CT-23, V1-CT-36, V1-CT-37 | `app/api/usuarios.py :: login/logout`; `app/security/sessions.py` | `tests/test_api_usuario.py`; `tests/test_security.py::test_sessao_expira_em_trinta_minutos` | automatizado / implementado |
| V1-RN-22 | V1-CT-28 | `app/schemas/usuario.py :: UsuarioUpdateRequest`; `app/services/usuario_service.py :: atualizar` | `tests/test_usuario_service.py::test_atualizar_preserva_id_tipo_e_data_adicao_e_altera_modificacao`; `tests/test_api_usuario.py::test_atualizacao_autenticada_preserva_tipo_e_data_adicao` | automatizado / implementado |
| V1-RN-23 | V1-CT-25, V1-CT-27 | `app/api/usuarios.py`; `app/services/item_service.py` | `tests/test_api_usuario.py::test_atualizacao_de_outro_usuario_retorna_403`; `tests/test_api_item.py::test_atualizar_e_excluir_item_exigem_o_proprietario` | automatizado / implementado |
| V1-RN-24 | V1-CT-26 | `app/api/itens.py :: exigir_doador`; `app/api/usuarios.py :: sessao_obrigatoria` | `tests/test_api_item.py::test_beneficiario_nao_pode_cadastrar_item`; `tests/test_api_item.py::test_ponto_coleta_consulta_mas_nao_cadastra_item` | automatizado / implementado |
| V1-RN-25 | V1-CT-23, V1-CT-25, V1-CT-27, V1-CT-37 | `app/main.py :: proteger_mutacao_por_origem`; handlers de autenticação/autorização | `tests/test_api_usuario.py`; `tests/test_api_item.py` | automatizado / implementado |
| V1-RN-26 | V1-CT-24, V1-CT-29 | `app/mappers/usuario_mapper.py :: para_resumo/para_resposta` | `tests/test_api_usuario.py::test_listagem_de_terceiros_expoe_somente_resumo_publico`; `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado / implementado |
| V1-RN-27 | V1-CT-30, V1-CT-37 | `app/config.py :: Settings.origens_cors`; `app/main.py :: CORSMiddleware/proteger_mutacao_por_origem` | `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403`; inspeção do Compose | automatizado + fonte / implementado |
| V1-RN-28, V1-RN-29 | V1-CT-33 a V1-CT-35 | `frontend/js/api.js :: requestApi`; `frontend/js/comum.js :: handleError/loadSession`; autorização nas rotas | `tests/test_frontend.py`; `tests/test_selenium_frontend.py` | automatizado / implementado |
| V1-RN-30 | V1-CT-32 a V1-CT-35, V1-CT-39 | `frontend/index.html`, `cadastro.html`, `login.html`, `perfil.html`, `catalogo.html`, `itens.html` | `tests/test_frontend.py`; `tests/test_selenium_frontend.py` | automatizado / implementado |
| V1-RN-31 | V1-CT-21, V1-CT-37 | `app/api/usuarios.py :: login`; `app/security/origins.py :: origem_permitida/requisicao_com_sessao_mutavel` | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only`; `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403` | automatizado / implementado |
| V1-RN-32 | V1-CT-36 | `app/api/usuarios.py :: logout`; `app/security/sessions.py :: remover` | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado / implementado |
| V1-RNF-01, V1-RNF-02 | V1-CT-16, V1-CT-17, V1-CT-38 | `app/repositories/mongo_usuario_repository.py`; `app/repositories/mongo_item_repository.py`; `app/models/*` | `tests/test_mongo_*_repository.py`; `scripts/validar_stack_docker.py` | automatizado + integração / implementado |
| V1-RNF-03, V1-RNF-04 | V1-CT-16, V1-CT-17 | `app/api`, `app/services`, `app/repositories`, `app/models`, `app/mappers`, `app/schemas` | testes de Service/Repository/API; `docs/architecture.md` | automatizado + fonte / implementado |
| V1-RNF-05, V1-RNF-06 | V1-CT-18, V1-CT-37, V1-CT-39 | `pyproject.toml`; diretório `tests/` | `evidencias/testes.txt`; `evidencias/selenium.txt` | 77 execuções; relatório de cobertura registrado, incluindo `app/main.py` / implementado |
| V1-RNF-07 | V1-CT-38, V1-CT-40 | `README.md`; `HARNESS.md`; `docs/*.md`; `artefatos/v1.0/*` | `artefatos/v1.0/registro_entrega.md`; `evidencias/` | fonte + script / implementado |
| V1-RNF-08 | V1-CT-40 | `artefatos/v1.0/registro_entrega.md` | commit-base verificável e tag local `v1.0`; vídeo ainda não informado | manual / pendente externo |
| V1-RNF-09, V1-RNF-10 | V1-CT-17, V1-CT-38 | `.env.example`; `compose.yaml`; `Dockerfile`; `frontend/Dockerfile` | `scripts/validar_stack_docker.py`; `scripts/smoke_api_docker.py`; `evidencias/docker.txt` | automatizado/script / implementado |
| V1-RNF-11 | V1-CT-19 | `app/security/passwords.py`; `app/schemas/usuario.py` | `tests/test_security.py`; `tests/test_api_usuario.py` | automatizado / implementado |
| V1-RNF-12 | V1-CT-21 a V1-CT-23, V1-CT-36, V1-CT-37 | `app/security/sessions.py`; `app/api/usuarios.py`; `app/security/origins.py` | `tests/test_api_usuario.py`; `tests/test_security.py` | automatizado / implementado |
| V1-RNF-13 | V1-CT-30, V1-CT-37 | `app/config.py`; `app/main.py :: CORSMiddleware/proteger_mutacao_por_origem` | teste de origem autenticada e inspeção de configuração | automatizado + fonte / implementado |
| V1-RNF-14 | V1-CT-19, V1-CT-22, V1-CT-29, V1-CT-30 | DTOs/mappers, handlers e `app/security/passwords.py` | `tests/test_api_usuario.py`; `tests/test_frontend.py`; evidência de logs ainda pendente | automatizado + fonte / parcialmente pendente |
| V1-RNF-15 | V1-CT-32 a V1-CT-35, V1-CT-38, V1-CT-39 | `frontend/`; `frontend/Dockerfile`; `scripts/validar_stack_docker.py` | `tests/test_frontend.py`; `tests/test_selenium_frontend.py`; evidência Docker | automatizado/script / implementado |

## Caso → função automatizada/evidência

| Caso | Teste automatizado ou relatório | Tipo | Resultado/estado |
|---|---|---|---|
| V1-CT-01 | `tests/test_api_usuario.py::test_cadastro_persiste_endereco_datas_e_nao_expoe_senha`; `tests/test_mongo_usuario_repository.py::test_repositorio_persiste_endereco_datas_e_remove_usuario` | automatizado | coberto |
| V1-CT-02 | `tests/test_api_usuario.py::test_cadastro_rejeita_endereco_e_senha_invalidos` | automatizado | coberto |
| V1-CT-03 | `tests/test_api_usuario.py::test_cadastro_aceita_endereco_sem_complemento` | automatizado | coberto |
| V1-CT-04 | `tests/test_mongo_usuario_repository.py::test_repositorio_persiste_endereco_datas_e_remove_usuario` | automatizado | coberto |
| V1-CT-05 | `tests/test_api_usuario.py::test_listagem_de_terceiros_expoe_somente_resumo_publico` | automatizado | coberto |
| V1-CT-06 | `tests/test_api_usuario.py::test_atualizacao_autenticada_preserva_tipo_e_data_adicao` | automatizado | coberto |
| V1-CT-07 | `tests/test_api_usuario.py::test_exclusao_exige_sessao_e_propriedade` | automatizado | coberto |
| V1-CT-08 | `tests/test_api_item.py::test_doador_cadastra_item_valido_e_nao_duplica_endereco` | automatizado | coberto |
| V1-CT-09 | `tests/test_item_service.py::test_criar_item_rejeita_proprietario_inexistente` | automatizado | coberto |
| V1-CT-10 | `tests/test_api_item.py::test_listar_filtra_itens_por_categoria_destino_e_status` | automatizado | coberto |
| V1-CT-11 | `tests/test_api_item.py::test_catalogo_exige_sessao_e_item_invalido_retorna_404` | automatizado | coberto |
| V1-CT-12 | `tests/test_item_service.py::test_atualizar_preserva_identidade_proprietario_e_data_adicao` | automatizado | coberto |
| V1-CT-13 | `tests/test_api_item.py::test_atualizar_e_excluir_item_exigem_o_proprietario` | automatizado | coberto |
| V1-CT-14 | `tests/test_api_item.py::test_validacao_de_enums_e_valor_de_revenda` | automatizado | coberto |
| V1-CT-15 | `tests/test_api_item.py::test_validacao_de_enums_e_valor_de_revenda` | automatizado | coberto |
| V1-CT-16 | `tests/test_api_item.py::test_doador_cadastra_item_valido_e_nao_duplica_endereco` | automatizado | coberto |
| V1-CT-17 | `scripts/validar_stack_docker.py` | automatizado/script | coberto; `evidencias/docker.txt` |
| V1-CT-18 | `evidencias/testes.txt` e comando de cobertura do `pyproject.toml` | automatizado | coberto |
| V1-CT-19 | `tests/test_security.py::test_senha_e_armazenada_com_hash_e_verificada_sem_expor_valor` | automatizado | coberto |
| V1-CT-20 | `tests/test_api_usuario.py::test_cadastro_rejeita_ponto_de_coleta_e_email_duplicado`; `tests/test_usuario_service.py::test_email_normalizado_nao_pode_ser_repetido` | automatizado | coberto |
| V1-CT-21 | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado | coberto |
| V1-CT-22 | `tests/test_api_usuario.py::test_login_invalido_tem_resposta_generica` | automatizado | coberto |
| V1-CT-23 | `tests/test_security.py::test_sessao_expira_em_trinta_minutos`; testes de sessão da API | automatizado | coberto |
| V1-CT-24 | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado | coberto |
| V1-CT-25 | `tests/test_api_usuario.py::test_atualizacao_de_outro_usuario_retorna_403`; `tests/test_api_usuario.py::test_exclusao_exige_sessao_e_propriedade` | automatizado | coberto |
| V1-CT-26 | `tests/test_api_item.py::test_beneficiario_nao_pode_cadastrar_item`; `tests/test_api_item.py::test_ponto_coleta_consulta_mas_nao_cadastra_item` | automatizado | coberto |
| V1-CT-27 | `tests/test_api_item.py::test_atualizar_e_excluir_item_exigem_o_proprietario` | automatizado | coberto |
| V1-CT-28 | `tests/test_usuario_service.py::test_atualizar_preserva_id_tipo_e_data_adicao_e_altera_modificacao` | automatizado | coberto |
| V1-CT-29 | `tests/test_api_usuario.py::test_listagem_de_terceiros_expoe_somente_resumo_publico`; `tests/test_api_item.py::test_doador_cadastra_item_valido_e_nao_duplica_endereco` | automatizado | coberto |
| V1-CT-30 | `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403`; inspeção de arquivos/logs | automatizado + manual | origem coberta; logs específicos pendentes |
| V1-CT-31 | `tests/test_provisionamento_ponto_coleta.py` | automatizado | coberto |
| V1-CT-32 | `tests/test_frontend.py::test_frontend_organiza_telas_separadas`; `scripts/validar_stack_docker.py` | automatizado + script | coberto |
| V1-CT-33 | `tests/test_frontend.py`; smoke de navegador | automatizado estrutural + manual | parcial |
| V1-CT-34 | `tests/test_frontend.py::test_javascript_aplica_permissoes_e_erros_http`; testes de API | automatizado | coberto por camadas |
| V1-CT-35 | `tests/test_frontend.py::test_javascript_nao_persiste_segredos_nem_renderiza_html_da_api`; `test_selenium_frontend.py` | automatizado | coberto por camadas |
| V1-CT-36 | `tests/test_api_usuario.py::test_login_me_logout_e_sessao_http_only` | automatizado | coberto |
| V1-CT-37 | `tests/test_api_usuario.py::test_mutacao_autenticada_valida_origem_e_prioriza_403` | automatizado | coberto |
| V1-CT-38 | `scripts/validar_stack_docker.py`; `evidencias/docker.txt` | automatizado/script | coberto em stack isolada |
| V1-CT-39 | `tests/test_selenium_frontend.py::test_selenium_navega_nas_seis_telas_em_modo_escuro`; `evidencias/selenium.txt` | automatizado, Chrome headless | coberto |
| V1-CT-40 | `artefatos/v1.0/registro_entrega.md`; `git show --no-patch v1.0`; URL do vídeo | manual externo | tag local `v1.0`; vídeo pendente |

## Estado resumido

- **Implementado:** usuários e itens com campos de endereço planos na persistência, auditoria temporal, hash, sessão, autorização, proteção de origem em mutações autenticadas, filtros, frontend modular, Selenium e documentação bidirecional.
- **Concluído na base de backend:** validação dos dois CRUDs contra MongoDB 7.0 real via Docker Compose, incluindo índices e limpeza dos dados de teste — evidência reproduzível em `evidencias/docker.txt`.
- **Concluído no frontend:** telas separadas de cadastro, login, perfil, catálogo e gestão de itens, com smoke test no navegador e validação Selenium em Chrome headless.
- **Pendente externamente:** logs específicos e URL pública do vídeo; a publicação da tag/release no GitHub depende de autorização explícita.
