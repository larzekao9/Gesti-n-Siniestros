# Stage 1: builder — instala dependencias en entorno limpio
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias de sistema necesarias solo para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalar en directorio local para copiar al runtime stage
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────
# Stage 2: runtime — imagen mínima sin herramientas de build
FROM python:3.12-slim AS runner

# Instalar solo las libs de runtime necesarias (libpq para asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root con UID/GID explícitos
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /bin/false appuser

WORKDIR /app

# Copiar dependencias instaladas desde el builder stage
COPY --from=builder /install /usr/local

# Copiar código fuente con ownership correcto
COPY --chown=appuser:appgroup . .

USER 1001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
