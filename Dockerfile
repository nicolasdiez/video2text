# Imagen base ligera con Python 3.11
FROM python:3.11-slim

# Evitar que Python genere .pyc y usar stdout/stderr sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (ej. gcc si alguna lib lo requiere)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY ./src ./src

# Exponer puerto
EXPOSE 8000

# Comando de arranque (Uvicorn en modo producción)
# ENV PYTHONPATH=/app/src:$PYTHONPATH
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000"]

