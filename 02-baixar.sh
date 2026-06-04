#!/bin/bash
# obsoleto, usando o github.com/sandeco/prompts para baixar os arquivos de texto
URL="https://books.toscrape.com/"
SAIDA="livros.html"
curl -o "${SAIDA}" "${URL}"
echo "Download concluido: ${SAIDA}"
ls -lh "${SAIDA}"
