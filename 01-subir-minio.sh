#!/bin/bash
# obsoleto, usando o docker-compose.yml para subir o MinIO
docker rm -f minio 2>/dev/null
docker run -d --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -v minio-data:/data \
  -e "MINIO_ROOT_USER=rafa" \
  -e "MINIO_ROOT_PASSWORD=orion2026" \
  minio/minio server /data --console-address ":9001"
echo "MinIO iniciado. Painel: http://localhost:9001 (rafa / orion2026)"
