# 📱 yt-dl-ios-shortcut

Un serveur léger basé sur FastAPI et `yt-dlp` conçu pour fonctionner en tandem avec l'application Raccourcis (Shortcuts) d'iOS. Il permet de télécharger des vidéos YouTube en arrière-plan depuis un iPhone vers un serveur (Homelab), puis de les rapatrier automatiquement dans la pellicule photo de l'iPhone.

## 🚀 Fonctionnalités

- **Totalement Asynchrone :** Contourne la limite de *timeout* stricte d'Apple. Lance le téléchargement, ferme le raccourci, et récupère la vidéo plus tard.
- **Limitation de qualité :** Télécharge automatiquement la meilleure qualité disponible jusqu'à un maximum de 1080p pour économiser du stockage.
- **Nettoyage automatique :** Le fichier vidéo est supprimé du serveur dès qu'il a été transmis à l'iPhone avec succès.
- **Formatage propre :** Les vidéos sont sauvegardées sous le format `Nom de la vidéo - Nom de la chaîne.mp4`.
- **Intégration Tailscale :** Fonctionne de n'importe où en 4G/5G sans avoir à ouvrir les ports de sa box internet.

## 🏗️ Architecture

Le projet est divisé en trois parties :
1. **L'API FastAPI (Serveur) :** Gère la file d'attente, télécharge via `yt-dlp` et sert le fichier.
2. **Raccourci iOS "Envoi" :** À utiliser depuis le bouton "Partager" de l'application YouTube pour envoyer l'URL au serveur.
3. **Raccourci iOS "Réception" :** À lier à une automatisation iOS (ex: tous les jours à 05h00) pour rapatrier silencieusement les vidéos terminées.

---

## 💻 Installation du Serveur (Homelab)

L'application est conteneurisée et optimisée pour être déployée sur **CasaOS** ou tout autre environnement Docker.

### Via Docker CLI
```bash
docker run -d \
  --name yt-dl-ios-shortcut \
  -p 8007:8007 \
  -v ./downloads:/app/downloads \
  ton-pseudo/yt-dl-ios-shortcut:latest