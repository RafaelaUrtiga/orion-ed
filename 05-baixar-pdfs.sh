#!/bin/bash
# 05-baixar-pdfs.sh
# Baixa varios PDFs do arXiv automaticamente (texto nativo, sem OCR)

mkdir -p pdfs

# Quantos artigos e de qual area (cs.IR = recuperacao de informacao, bem ligado a RAG)
QUANTIDADE=20
CATEGORIA="cs.IR"

# Pega a lista de IDs pela API do arXiv
URL="http://export.arxiv.org/api/query?search_query=cat:${CATEGORIA}&start=0&max_results=${QUANTIDADE}"
IDS=$(curl -s "$URL" | grep -oP '<id>http://arxiv.org/abs/\K[^<]+')

for ID in $IDS; do
  NOME=$(echo "$ID" | tr '/' '_')
  curl -L -o "pdfs/${NOME}.pdf" "https://arxiv.org/pdf/${ID}.pdf"
  echo "Baixado: pdfs/${NOME}.pdf"
done