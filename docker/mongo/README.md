# MongoDB local e reserva de interesses

A Etapa 4 usa transações para aceitar um interesse, reservar o item e acrescentar seu histórico como uma única operação. O Compose inicializa automaticamente um replica set de um nó (`rs0`) com autenticação interna por keyfile gerado no container.

- `entrypoint.sh` mantém o ponto de entrada da imagem oficial e prepara a chave em `/data/configdb`.
- `healthcheck.js` aguarda a criação do administrador, inicializa o conjunto somente se ainda não existir e exige PRIMARY.
- A conexão do backend usa o nome `mongo:27017` dentro da rede Compose.
- Para Python executado no host, use a URI da `.env.example`, com `directConnection=true`; isso evita tentar resolver o nome interno `mongo` fora da rede Docker.

## Dados já existentes

Não apagar o volume para habilitar transações. O mesmo diretório de dados pode ser iniciado com `--replSet`; o healthcheck inicializa o conjunto sem remover coleções. Credenciais existentes precisam corresponder à configuração — variáveis de inicialização não alteram a senha de um banco já criado. Um volume que já pertença a outro replica set exige conferência manual; o healthcheck não o reconfigura.

A implantação deve ser feita conscientemente na stack desejada. Os testes da etapa usam projeto, portas e volume próprios, sem reiniciar a demonstração.

## Validação reproduzível

```bash
# Stack nova de testes; não usar o volume da demonstração.
export MONGO_DATA_VOLUME=recicla_interesses_teste_mongo_data
export MONGO_PORT=27109 BACKEND_PORT=8019 FRONTEND_PORT=8099 MONGO_EXPRESS_PORT=18099
docker compose --env-file .env.example -p recicla_interesses_teste up -d --build --wait

# A URI deve apontar para esse Mongo de testes, com autenticação,
# replicaSet=rs0 e directConnection=true, sem imprimir credenciais.
export INTERESSES_TEST_MONGO_URI='<URI do Mongo de testes>'
.venv/Scripts/python.exe -m pytest tests/test_interesses_runtime.py -q --no-cov -o addopts=''
```

Os testes criam bancos com UUID e removem somente o banco criado por cada caso, em `finally`. Sem `INTERESSES_TEST_MONGO_URI`, os testes de integração são explicitamente pulados; isso não conta como validação de transações.
