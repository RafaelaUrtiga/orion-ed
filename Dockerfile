# SO base: Python ja vem com Linux por baixo
FROM python:3.12-slim

# Pasta de trabalho dentro do container
WORKDIR /app

# Instala as dependencias (copiado primeiro pra aproveitar cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo da aplicacao
COPY transformar.py .

# Comando que executa a aplicacao
CMD ["python", "transformar.py"]