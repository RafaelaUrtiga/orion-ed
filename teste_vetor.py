#obsoleto, confirmar que o modelo carrega e devolve um vetor do tamanho esperado, sem erros.

from sentence_transformers import SentenceTransformer

print("Carregando o modelo BGE-M3...")
modelo = SentenceTransformer("BAAI/bge-m3", device="cpu")

vetor = modelo.encode("Este e um texto de teste.")
print("Tamanho do vetor:", len(vetor))
print("Primeiros numeros:", vetor[:8])