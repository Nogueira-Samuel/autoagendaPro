# AutoAgenda Pro - Backend Dockerfile
# Multi-stage build para otimizar o tamanho da imagem

# Stage 1: Base com Python 3.11
FROM python:3.11-slim as base

# Variáveis de ambiente para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Stage 2: Builder - Instala dependências Python
FROM base as builder

# Copia apenas requirements.txt primeiro (cache layer)
COPY requirements.txt .

# Instala dependências em um virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 3: Runtime - Imagem final
FROM base as runtime

# Copia o virtual environment do builder
COPY --from=builder /opt/venv /opt/venv

# Ativa o virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copia o código da aplicação
COPY --chown=appuser:appuser ./app /app/app

# Muda para usuário não-root
USER appuser

# Expõe a porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
