import unicodedata
import re
from minio import Minio
from sentence_transformers import SentenceTransformer


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

client = Minio("localhost:9000", access_key="rafa", secret_key="orion2026", secure=False)
bucket = "dados-brutos"

todos_os_chunks = []
for obj in client.list_objects(bucket, recursive=True):
    nome = obj.object_name
    resposta = client.get_object(bucket, nome)
    conteudo = resposta.read().decode("utf-8", errors="ignore")
    resposta.close()
    resposta.release_conn()
    texto_limpo = limpar_texto(conteudo)
    chunks = fazer_chunks(texto_limpo)
    todos_os_chunks = todos_os_chunks + chunks
    print(f"{nome}  ({len(texto_limpo)} caracteres -> {len(chunks)} chunks)")

print()
print(f"Total de chunks: {len(todos_os_chunks)}")

print("Vetorizando todos os chunks (pode levar um tempinho no processador)...")
vetores = modelo.encode(todos_os_chunks, show_progress_bar=True)

print(f"Pronto! Foram gerados {len(vetores)} vetores.")
print(f"Cada vetor tem {len(vetores[0])} numeros.")