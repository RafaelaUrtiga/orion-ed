from minio import Minio

client = Minio("localhost:9000", access_key="rafa", secret_key="orion2026", secure=False)
bucket = "dados-brutos"

removidos = 0
for obj in client.list_objects(bucket, recursive=True):
    nome = obj.object_name
    if not nome.lower().endswith(".pdf"):
        client.remove_object(bucket, nome)
        print(f"Removido: {nome}")
        removidos += 1

print(f"\nTotal removido: {removidos}")
print("Sobraram apenas os PDFs.")