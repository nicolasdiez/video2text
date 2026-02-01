# Imagen base ligera con Python 3.11 para build (builder stage)
FROM python:3.11-slim

# Evitar que Python genere .pyc y usar stdout/stderr sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias de compilación (build-essential: gcc, g++, make, libc-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
# COPY requirements.txt .
COPY requirements-lightweight.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements-lightweight.txt

# Copiar el código fuente (después de instalar dependencias para aprovechar cache cuando cambie solo el código)
COPY ./src ./src

# Establecer el directorio de trabajo en /app/src para que los imports tipo "from domain..." funcionen
WORKDIR /app/src

# Exponer puerto
EXPOSE 8081

# Comando de arranque (Uvicorn en modo producción)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
