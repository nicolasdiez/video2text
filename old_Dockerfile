# Imagen base ligera con Python 3.11 para build (builder stage)
FROM python:3.11-slim AS builder

# Evitar que Python genere .pyc y usar stdout/stderr sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias de compilación (build-essential: gcc, g++, make, libc-dev) — usadas solo para construir binarios en las wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Crear ruedas (whls) para todas las dependencias
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ********** Stage final: imagen de runtime ligera **********
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Solo dependencias necesarias para run (no build deps)
# Si la app necesita alguna librería de sistema en runtime, añádirla aquí.
RUN apt-get update \
  && apt-get install -y --no-install-recommends libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Copiar ruedas desde builder y luego instalarlas
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copiar el código fuente (después de instalar dependencias para aprovechar cache cuando cambie solo el código)
COPY ./src ./src

# Establecer el directorio de trabajo en /app/src para que los imports tipo "from domain..." funcionen
WORKDIR /app/src

# Exponer puerto
EXPOSE 8000

# Comando de arranque (Uvicorn en modo producción)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
