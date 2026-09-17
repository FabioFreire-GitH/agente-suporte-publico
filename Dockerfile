# 1. Imagem base oficial do Python 3.12 (versão slim para manter a imagem leve)
FROM python:3.12-slim

# 2. Variáveis de ambiente para o Python e Streamlit
# Impede o Python de gerar arquivos .pyc e força o envio direto de logs para o terminal
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# 3. Diretório de trabalho dentro do container
WORKDIR /app

# 4. Instalação de dependências do sistema necessárias (se aplicável)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalação das dependências Python primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copia todo o código da aplicação (incluindo src/, app.py e a pasta tmp/ com o banco ChromaDB)
COPY . .

# 7. Porta padrão usada pelo Google Cloud Run (o Cloud Run injeta a variável $PORT dinamicamente)
EXPOSE 8080

# 8. Comando para iniciar o Streamlit ouvindo na porta e endereço corretos para a nuvem
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false"]
