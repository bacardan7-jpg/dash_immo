FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app/ ./app/
COPY config.py .
# Copier le fichier de configuration Gunicorn
COPY gunicorn_config.py .

# Exposer le port
EXPOSE 8050

# Commande pour démarrer l'application
CMD ["gunicorn", "--config", "gunicorn_config.py", "app.main:server"]