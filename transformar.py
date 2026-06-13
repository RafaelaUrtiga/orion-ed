import io
import os
import time
import unicodedata
import re
from pypdf import PdfReader
from minio import Minio
from sentence_transformers import SentenceTransformer
import psycopg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


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


# Configuracoes (vem do ambiente, com padrao local)
MINIO_HOST = os.environ.get("MINIO_HOST", "localhost:9000")
MINIO_KEY = os.environ.get("MINIO_KEY", "rafa")
MINIO_SECRET = os.environ.get("MINIO_SECRET", "orion2026")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "dados-brutos")

PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_USER = os.environ.get("POSTGRES_USER", "rafa")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "orion2026")
PG_DB = os.environ.get("POSTGRES_DB", "orion")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


# Etapa 3: ler PDFs do MinIO, limpar, fatiar e vetorizar
print("Carregando o modelo BGE-M3...")
modelo = SentenceTransformer("BAAI/bge-m3", device="cpu")

client = Minio(MINIO_HOST, access_key=MINIO_KEY, secret_key=MINIO_SECRET, secure=False)

print("Aguardando o MinIO...")
while True:
    try:
        client.bucket_exists(MINIO_BUCKET)
        break
    except Exception:
        time.sleep(1)
print("MinIO pronto.")

registros = []  # cada item: (documento, texto_do_chunk)
for obj in client.list_objects(MINIO_BUCKET, recursive=True):
    nome = obj.object_name
    resposta = client.get_object(MINIO_BUCKET, nome)
    dados = resposta.read()
    resposta.close()
    resposta.release_conn()

    texto = extrair_texto_pdf(dados)
    texto_limpo = limpar_texto(texto)
    for chunk in fazer_chunks(texto_limpo):
        registros.append((nome, chunk))
    print(f"{nome}  ({len(texto_limpo)} caracteres)")

print()
print(f"Total de chunks: {len(registros)}")

textos = [r[1] for r in registros]
print("Vetorizando todos os chunks...")
vetores = modelo.encode(textos, show_progress_bar=True)
print(f"Foram gerados {len(vetores)} vetores de {len(vetores[0])} numeros.")


# Etapa Ouro: textos no Postgres, vetores no Qdrant (ligados pelo mesmo id)
print("Aguardando o Postgres...")
while True:
    try:
        conexao = psycopg.connect(
            host=PG_HOST, port=PG_PORT, user=PG_USER,
            password=PG_PASS, dbname=PG_DB
        )
        break
    except Exception:
        time.sleep(1)
print("Postgres pronto.")

cur = conexao.cursor()
cur.execute("DROP TABLE IF EXISTS chunks")
cur.execute("""
    CREATE TABLE chunks (
        id INTEGER PRIMARY KEY,
        documento TEXT,
        texto TEXT
    )
""")
for i, (documento, texto) in enumerate(registros):
    cur.execute(
        "INSERT INTO chunks (id, documento, texto) VALUES (%s, %s, %s)",
        (i, documento, texto),
    )
conexao.commit()
cur.close()
conexao.close()
print(f"Salvos {len(registros)} textos no PostgreSQL.")

print("Aguardando o Qdrant...")
while True:
    try:
        qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        qdrant.get_collections()
        break
    except Exception:
        time.sleep(1)
print("Qdrant pronto.")

if qdrant.collection_exists("chunks"):
    qdrant.delete_collection("chunks")
qdrant.create_collection(
    collection_name="chunks",
    vectors_config=VectorParams(size=len(vetores[0]), distance=Distance.COSINE),
)

pontos = []
for i, (documento, texto) in enumerate(registros):
    pontos.append(
        PointStruct(id=i, vector=vetores[i].tolist(), payload={"documento": documento})
    )
qdrant.upsert(collection_name="chunks", points=pontos)
print(f"Salvos {len(pontos)} vetores no Qdrant.")

print()
print("Etapa Ouro concluida: texto no Postgres e vetor no Qdrant, ligados pelo mesmo id.")