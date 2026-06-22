import io
import os
import re
import time
import uuid
import unicodedata

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import psycopg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Config (ambiente, com padrao local)
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_USER = os.environ.get("POSTGRES_USER", "rafa")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "orion2026")
PG_DB = os.environ.get("POSTGRES_DB", "orion")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLECAO = "chunks"

# Carrega o modelo uma vez (na subida do servidor)
print("Carregando o modelo BGE-M3...")
modelo = SentenceTransformer("BAAI/bge-m3", device="cpu")


def conectar_postgres():
    while True:
        try:
            return psycopg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER,
                                   password=PG_PASS, dbname=PG_DB)
        except Exception:
            time.sleep(1)


def conectar_qdrant():
    while True:
        try:
            c = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            c.get_collections()
            return c
        except Exception:
            time.sleep(1)


# Prepara os bancos (espera ficarem prontos)
print("Aguardando o Qdrant...")
qdrant = conectar_qdrant()
if not qdrant.collection_exists(COLECAO):
    qdrant.create_collection(
        collection_name=COLECAO,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

print("Aguardando o Postgres...")
con = conectar_postgres()
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, fonte TEXT, texto TEXT)")
con.commit()
cur.close()
con.close()
print("Bancos prontos.")


def limpar_texto(texto):
    texto = unicodedata.normalize("NFC", texto)
    limpo = "".join(ch for ch in texto if ch in "\t\n" or not unicodedata.category(ch).startswith("C"))
    linhas = [l.rstrip() for l in limpo.splitlines()]
    texto = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def fazer_chunks(texto, tamanho=1200, overlap=200):
    chunks, inicio = [], 0
    while inicio < len(texto):
        chunks.append(texto[inicio:inicio + tamanho])
        inicio += tamanho - overlap
    return chunks


def processar_e_salvar(texto, fonte):
    texto = limpar_texto(texto)
    pedacos = fazer_chunks(texto)
    if not pedacos:
        return 0
    vetores = modelo.encode(pedacos)
    con = conectar_postgres()
    cur = con.cursor()
    pontos = []
    for pedaco, vetor in zip(pedacos, vetores):
        ident = str(uuid.uuid4())
        cur.execute("INSERT INTO chunks (id, fonte, texto) VALUES (%s, %s, %s)",
                    (ident, fonte, pedaco))
        pontos.append(PointStruct(id=ident, vector=vetor.tolist(), payload={"fonte": fonte}))
    con.commit()
    cur.close()
    con.close()
    qdrant.upsert(collection_name=COLECAO, points=pontos)
    return len(pedacos)


app = FastAPI(title="Orion RAG API")


class SiteRequest(BaseModel):
    url: str


@app.get("/")
def raiz():
    return {"status": "ok", "rotas": ["/pdf", "/site"]}


@app.post("/pdf")
async def receber_pdf(file: UploadFile = File(...)):
    dados = await file.read()
    leitor = PdfReader(io.BytesIO(dados))
    texto = "\n".join((p.extract_text() or "") for p in leitor.pages)
    qtd = processar_e_salvar(texto, file.filename)
    return {"fonte": file.filename, "chunks_salvos": qtd}


@app.post("/site")
def receber_site(req: SiteRequest):
    resp = requests.get(req.url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    sopa = BeautifulSoup(resp.text, "html.parser")
    for tag in sopa(["script", "style"]):
        tag.decompose()
    texto = sopa.get_text(separator="\n")
    qtd = processar_e_salvar(texto, req.url)
    return {"fonte": req.url, "chunks_salvos": qtd}