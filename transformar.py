import re
import unicodedata
from minio import Minio

def limpar_texto(texto):
    # 1) Padroniza os acentos (forma NFC do Unicode)
    texto = unicodedata.normalize("NFC", texto)

    # 2) Remove caracteres de controle invisiveis (mantem quebra de linha e tab)
    #texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)
    limpo = ""
    for ch in texto:
        if ch in "\t\n" or not unicodedata.category(ch).startswith("C"):
            limpo += ch
    texto = limpo

    # 3) Tira os espacos sobrando no fim de cada linha
    linhas_limpas = []
    for linha in texto.splitlines():
        linhas_limpas.append(linha.rstrip())
    texto = "\n".join(linhas_limpas)

    # 4) Onde houver 3 ou mais linhas em branco seguidas, deixa so uma
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    # 5) Tira espacos em branco no comeco e no fim de tudo
    texto = texto.strip()

    return texto

# ---- Conectar ao MinIO ----
client = Minio(
    "localhost:9000",
    access_key="rafa",       # use o MESMO usuario do docker-compose.yml
    secret_key="orion2026",  # use a MESMA senha do docker-compose.yml
    secure=False,            # False porque e local (http, nao https)
)

# ---- Listar os arquivos do bucket ----
bucket = "dados-brutos"
for obj in client.list_objects(bucket, recursive=True):
    print(obj.object_name)