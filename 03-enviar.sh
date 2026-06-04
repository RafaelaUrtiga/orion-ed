#!/bin/bash
# obsoleto, usando o 04-coletar-repo.sh para enviar os arquivos de texto para o MinIO
arquivo="$file"
bucket="dados-brutos"
objeto="${file#./}"
host="localhost:9000"
chave="rafa"
segredo="orion2026"
recurso="/${bucket}/${objeto}"
tipo="application/octet-stream"
data=$(date -R)
assinar="PUT\n\n${tipo}\n${data}\n${recurso}"
assinatura=$(echo -en "${assinar}" | openssl sha1 -hmac "${segredo}" -binary | base64)
curl -X PUT -T "${arquivo}" \
  -H "Host: ${host}" \
  -H "Date: ${data}" \
  -H "Content-Type: ${tipo}" \
  -H "Authorization: AWS ${chave}:${assinatura}" \
  "http://${host}${recurso}"
echo "Envio concluido. Confira em http://localhost:9001 (bucket ${bucket})."
