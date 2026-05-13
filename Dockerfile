# Image de base légère Python
FROM python:3.11-slim

# Installation de ffmpeg (indispensable pour le 1080p et la fusion audio/vidéo)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Définition du dossier de travail
WORKDIR /app

# Copie et installation des dépendances Python
COPY requirements.txt .
# On force également la mise à jour de yt-dlp vers la toute dernière version
RUN pip install --no-cache-dir -r requirements.txt && pip install -U yt-dlp

# Copie du code source du serveur
COPY server.py .

# Création du dossier qui accueillera les téléchargements temporaires
RUN mkdir -p /app/downloads

# Exposition du port choisi
EXPOSE 8007

# Commande de lancement du serveur
CMD ["python", "server.py"]