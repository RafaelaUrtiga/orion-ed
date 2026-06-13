import io
import os
import time
import unicodedata
import re
from pypdf import PdfReader
from minio import Minio
from sentence_transformers import SentenceTransformer


def extrair_texto_pdf(dados):
    leitor = PdfReader(io.BytesIO(dados))
    partes = []
    for pagina in leitor.pages:
        partes.append(pagina.extract_text() or "")
    return "\n".join(partes)


def limpar_texto(texto):
    texto = unicodedata.normalize("NFC", texto)
    limpo = ""
    for ch in texto:
        if ch in "\t\n" or not unicodedata.category(ch).startswith("C"):
            limpo += ch
    texto = limpo
    linhas_limpas = []
    for linha in texto.splitlines():
        linhas_limpas.append(linha.rstrip())
    texto = "\n".join(linhas_limpas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    texto = texto.strip()
    return texto


def fazer_chunks(texto, tamanho=1200, overlap=200):
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        chunks.append(texto[inicio:fim])
        inicio = inicio + tamanho - overlap
    return chunks


print("Carregando o modelo BGE-M3...")
modelo = SentenceTransformer("BAAI/bge-m3", device="cpu")

host = os.environ.get("MINIO_HOST", "localhost:9000")
chave = os.environ.get("MINIO_KEY", "rafa")
segredo = os.environ.get("MINIO_SECRET", "orion2026")
bucket = os.environ.get("MINIO_BUCKET", "dados-brutos")

client = Minio(host, access_key=chave, secret_key=segredo, secure=False)

print("Aguardando o MinIO...")
while True:
    try:
        client.bucket_exists(bucket)
        break
    except Exception:
        time.sleep(1)
print("MinIO pronto.")

todos_os_chunks = []
for obj in client.list_objects(bucket, recursive=True):
    nome = obj.object_name
    resposta = client.get_object(bucket, nome)
    dados = resposta.read()
    resposta.close()
    resposta.release_conn()

    texto = extrair_texto_pdf(dados)
    texto_limpo = limpar_texto(texto)
    chunks = fazer_chunks(texto_limpo)
    todos_os_chunks = todos_os_chunks + chunks
    print(f"{nome}  ({len(texto_limpo)} caracteres -> {len(chunks)} chunks)")

print()
print(f"Total de chunks: {len(todos_os_chunks)}")

print("Vetorizando todos os chunks (pode levar um tempinho no processador)...")
vetores = modelo.encode(todos_os_chunks, show_progress_bar=True)

print(f"Pronto! Foram gerados {len(vetores)} vetores.")
print(f"Cada vetor tem {len(vetores[0])} numeros.")