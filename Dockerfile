# Usar uma imagem base oficial e leve do Python
FROM python:3.10-slim

# Definir variaveis de ambiente basicas
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir o diretorio de trabalho dentro do container
WORKDIR /app

# Copiar os requerimentos do backend primeiro (layer cache otimizado)
COPY backend/requirements.txt /app/backend/

# Instalar dependencias Python (psycopg2 requer dependencias de build do sistema)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar todo o codigo do projeto (Backend e Frontend) para o container
# Observacao: O main.py carrega os arquivos do frontend baseado em paths locais
COPY . /app

# Expor a porta 80 do container
EXPOSE 80

# Usar Uvicorn rodando a main.py do backend na porta 80
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
