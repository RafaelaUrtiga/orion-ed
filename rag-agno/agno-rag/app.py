import os

import uvicorn
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.google import Gemini
from agno.os import AgentOS
from agno.vectordb.qdrant import Qdrant
from agno.vectordb.search import SearchType
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Abre o "cofre" e carrega as variaveis do .env
load_dotenv()

# 1. Embedder: traduz texto em vetor, usando o Gemini
embedder = GeminiEmbedder(
    id=os.getenv("GEMINI_EMBEDDING_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY"),
)

# 2. Estante: os vetores ficam no Qdrant
vector_db = Qdrant(
    collection=os.getenv("COLLECTION_OR_TABLE_NAME"),
    url=os.getenv("QDRANT_URL"),
    embedder=embedder,
    search_type=SearchType.hybrid,
)

# 3. Catalogo: o "indice da estante" no Postgres (era o que faltava)
#    E ele que a aba Knowledge gerencia. Mesmo Postgres, tabela propria.
contents_db = PostgresDb(
    db_url=os.getenv("POSTGRES_DB_URL"),
    id="frank_knowledge_db",
    knowledge_table="frank_knowledge_contents",
)

# 4. Base de conhecimento: junta a estante (Qdrant) com o catalogo (Postgres)
knowledge_base = Knowledge(
    name="Base do Frank",
    vector_db=vector_db,
    contents_db=contents_db,
    max_results=4,
)

# 5. Memoria: o "caderno" do historico da conversa no Postgres
db = PostgresDb(db_url=os.getenv("POSTGRES_DB_URL"))

# 6. Modelo: o "cerebro" Gemini
llm = Gemini(
    id=os.getenv("GEMINI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY"),
)

# 7. O agente: junta tudo no "Frank-enstein" do RAG
agent = Agent(
    name="Frank",
    model=llm,
    knowledge=knowledge_base,
    instructions=os.getenv("SYSTEM_PROMPT"),
    search_knowledge=True,
    markdown=True,
    add_history_to_context=True,
    db=db,
)

# 8. Sobe pelo AgentOS. Agora o Knowledge tambem vai registrado (knowledge=)
agent_os = AgentOS(
    agents=[agent],
    knowledge=[knowledge_base],
)
app = agent_os.get_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota simples de "sinal de vida"
@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": agent.name}

# Roda o app FastAPI com Uvicorn - para rodar fora do Docker quando for necessário.
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8008, reload=True)