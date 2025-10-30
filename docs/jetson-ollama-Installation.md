# 1. Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Vérifier installation
ollama --version

# 3. Télécharger modèles (choisir selon besoins)

# Llama 3.1 8B (Recommandé - 4.7GB)
ollama pull llama3.1:8b

# Ou version quantifiée plus légère
ollama pull llama3.1:8b-q4_K_M  # ~4.5GB

# Mistral 7B (Alternative rapide)
ollama pull mistral:7b

# Phi-3 Medium (Ultra-léger - 2.3GB)
ollama pull phi3:medium

# Gemma 2 9B (Excellent français)
ollama pull gemma2:9b

# Qwen 2.5 7B (Multilingue excellent)
ollama pull qwen2.5:7b

# 4. Lister modèles installés
ollama list

# 5. Tester un modèle
ollama run llama3.1:8b "Bonjour, comment vas-tu ?"

# 6. Démarrer serveur (si pas déjà lancé)
ollama serve
# Par défaut sur http://localhost:11434

# 7. Configurer pour démarrage automatique
sudo systemctl enable ollama
sudo systemctl start ollama


# Commandes utiles
## Changer de modèle à la volée
curl http://localhost:8000/switch-model -X POST \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b"}'

## Lister modèles disponibles
curl http://localhost:8001/v1/models

## Tester génération
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Bonjour"}],
    "temperature": 0.7
  }'

## Télécharger nouveau modèle
ollama pull gemma2:9b

## Supprimer modèle
ollama rm phi3:medium

## Voir utilisation GPU
nvidia-smi