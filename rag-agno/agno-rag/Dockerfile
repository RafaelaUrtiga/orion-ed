FROM python:3.12-slim

WORKDIR /app

# Instala o curl, usado para baixar o instalador do uv
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Baixa e instala o uv (nosso gerenciador de pacotes)
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Deixa o uv acessivel no caminho
ENV PATH="/root/.local/bin:$PATH"

# Copia a lista de compras primeiro (aproveita o cache)
COPY pyproject.toml uv.lock* ./

# Instala as dependencias com o uv
RUN uv sync --frozen --no-dev

# Copia o resto do codigo da aplicacao
COPY . .

EXPOSE 8008

# Comando que sobe o servidor
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8008"]