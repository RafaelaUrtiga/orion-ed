#!/bin/bash
# 04-coletar-repo.sh

# 1) Clonar o repositório (só se ainda não existir)
if [ ! -d ./prompts ]; then
  git clone https://github.com/sandeco/prompts
fi

# 2) Configurações fixas do MinIO
host="localhost:9000"
chave="rafa"
segredo="orion2026"
bucket="dados-brutos"
tipo="text/plain"

# 3) Achar todos os .txt
FILES=$(find ./prompts -type f -name "*.txt")

# 4) Cortar só por quebra de linha (e não por espaço)
IFS=$'\n'

# 5) Enviar cada arquivo
for file in $FILES; do
  arquivo="$file"
  objeto=$(echo "${file#./}" | tr ' ' '_')
  recurso="/${bucket}/${objeto}"
  data=$(date -R)
  assinar="PUT\n\n${tipo}\n${data}\n${recurso}"
  assinatura=$(echo -en "${assinar}" | openssl sha1 -hmac "${segredo}" -binary | base64)
  curl -sS -X PUT -T "${arquivo}" \
    -H "Host: ${host}" -H "Date: ${data}" \
    -H "Content-Type: ${tipo}" \
    -H "Authorization: AWS ${chave}:${assinatura}" \
    "http://${host}${recurso}"
  echo "Enviado: ${objeto}"
done