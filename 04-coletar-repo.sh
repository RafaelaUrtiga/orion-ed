#!/bin/bash
# 04-coletar-repo.sh

source .env

TIPO="application/pdf"

# Espera o MinIO ficar pronto (mata o erro curl 7/56 de uma vez)
echo "Aguardando o MinIO ficar pronto..."
until curl -s -o /dev/null "http://${MINIO_HOST}/minio/health/live"; do
  sleep 1
done
echo "MinIO pronto."

FILES=$(find ./pdfs -type f -name "*.pdf")
IFS=$'\n'
for FILE in $FILES; do
  OBJETO=$(echo "${FILE#./}" | tr ' ' '_')
  RECURSO="/${MINIO_BUCKET}/${OBJETO}"
  DATA=$(date -R)
  ASSINAR="PUT\n\n${TIPO}\n${DATA}\n${RECURSO}"
  ASSINATURA=$(echo -en "${ASSINAR}" | openssl sha1 -hmac "${MINIO_SECRET}" -binary | base64)
  curl -X PUT -T "${FILE}" \
    -H "Host: ${MINIO_HOST}" \
    -H "Date: ${DATA}" \
    -H "Content-Type: ${TIPO}" \
    -H "Authorization: AWS ${MINIO_KEY}:${ASSINATURA}" \
    "http://${MINIO_HOST}${RECURSO}"
  echo "Enviado: ${OBJETO}"
done