#!/usr/bin/env bash
set -euo pipefail

# Chave interna do replica set local. Nunca grava a chave no repositório.
chave=/data/configdb/recicla-keyfile
if [ ! -s "$chave" ]; then
    umask 077
    openssl rand -base64 756 > "$chave"
fi
chown mongodb:mongodb "$chave"
chmod 400 "$chave"
exec /usr/local/bin/docker-entrypoint.sh mongod --replSet rs0 --keyFile "$chave" --bind_ip_all
