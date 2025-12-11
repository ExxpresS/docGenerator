Voici la commande pour télécharger le modèle qwen3:4b dans votre
conteneur Ollama :

docker exec workflow-ollama ollama pull qwen3:4b

Pour vérifier que le modèle a bien été téléchargé :

docker exec workflow-ollama ollama list

Si vous voulez ensuite utiliser ce modèle dans votre chat, vous
devrez mettre à jour la configuration :

Option 1 : Modifier le fichier .env
# Changer la ligne
OLLAMA_MODEL=qwen2.5:7b
# En
OLLAMA_MODEL=qwen3:4b

Option 2 : Via docker-compose avec variable d'environnement
# Puis redémarrer le backend
docker compose up -d --build backend

Option 3 : Directement dans le code backend/app/config.py (ligne
18)
OLLAMA_MODEL: str = "qwen3:4b"

Puis reconstruire le backend :
docker compose up -d --build backend

Le modèle qwen3:4b est plus léger que qwen2.5:7b (environ 2.3 GB
vs 4.7 GB), donc les réponses seront plus rapides mais
potentiellement un peu moins précises.
