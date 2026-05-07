# 🚀 MCP Assistant Local

Assistant de développement intelligent utilisant **LMStudio** et le **Model Context Protocol (MCP)** pour modifier vos fichiers.

Ce dépôt vise surtout les modèles d'IA exécutés en local, avec des configurations adaptées aux machines faibles, moyennes, puissantes et ultra puissantes.

## 📋 Prérequis

- **Python 3.8+**
- **LMStudio** en cours d'exécution sur `http://127.0.0.1:1234/v1`
- Un modèle chargé dans LMStudio

## 🔧 Installation

### 1. Créer l'environnement virtuel (déjà fait)
```bash
cd /home/skjuve/Documents/testsmcp
source venv/bin/activate
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Vérifier la configuration
Éditer le fichier `.env` si nécessaire:
```bash
# .env
LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=
PROJECT_PATH=/home/skjuve/Documents/testsmcp
```

Si `LM_STUDIO_MODEL` est vide, l'application essaie de détecter automatiquement le modèle chargé dans LM Studio.

## 🚀 Démarrage

```bash
source venv/bin/activate
python app.py
```

Sous Windows:

```bat
setup.bat
run.bat
```

## 📚 Utilisation

L'assistant dispose de 4 outils et choisit lui-même quand les utiliser:

### 1. **read_file** - Lire un fichier
```
>>> Lis le contenu de app.py
>>> Quels fichiers sont dans ce dossier?
```

### 2. **write_file** - Créer/modifier un fichier
```
>>> Crée un fichier test.py qui affiche "Hello World"
>>> Ajoute une fonction hello() au fichier main.py
```

### 3. **execute_bash** - Exécuter une commande
```
>>> Exécute ls -la
>>> Installe les dépendances avec pip
>>> Compte combien de fichiers Python sont dans le dossier
```

### 4. **list_directory** - Lister un dossier
```
>>> Qu'y a-t-il dans le dossier?
>>> Liste les fichiers Python
```

## 💡 Exemples d'utilisation

### Créer une structure de projet
```
>>> Crée une structure de projet Python avec:
    - un dossier src/
    - un dossier tests/
    - un fichier main.py avec une fonction hello()
    - un fichier requirements.txt
    - un fichier README.md
```

### Modifier du code
```
>>> Ouvre main.py, ajoute une fonction calculate(a, b) qui retourne a + b
```

### Analyser des fichiers
```
>>> Compte combien de lignes de code Python sont dans le dossier
>>> Cherche les erreurs Python dans main.py
```

## ⚠️ Restrictions de sécurité

- ✅ Accès autorisé uniquement au dossier `PROJECT_PATH`
- ❌ Commandes dangereuses refusées (`rm -rf`, `sudo`, etc.)
- ⏱️ Timeout des commandes: 30 secondes
- 🔄 Limite d'itérations: 4

## 🤖 Mode autonome

L'application essaie de décider seule quand lire, écrire ou exécuter une commande.
Si une demande est claire, elle peut aller directement au résultat sans passer par plusieurs allers-retours inutiles.

## 🤝 Contribution

Le guide de contribution est disponible dans [CONTRIBUTING.md](CONTRIBUTING.md).

## 🐛 Dépannage

### LMStudio ne répond pas
```bash
# Vérifier que LMStudio est lancé
curl http://127.0.0.1:1234/v1/models

# Ou relancer LMStudio
```

### Erreur "Outil inconnu"
- Vérifier que l'assistant utilise bien l'outil demandé
- Les modèles plus petits peuvent avoir du mal à utiliser les outils

### Commande expirée
- Réduire la complexité de la tâche
- Exécuter plusieurs commandes simples au lieu d'une complexe

## 📝 Fichiers du projet

```
testsmcp/
├── venv/              # Environnement virtuel
├── app.py             # Application principale
├── requirements.txt   # Dépendances
├── .env              # Configuration
├── .env.example       # Exemple de configuration partageable
├── CONTRIBUTING.md    # Guide de contribution
└── README.md         # Ce fichier
```

## 🔄 Configuration avancée

### Changer le modèle
Éditer `.env`:
```bash
LM_STUDIO_MODEL=llama2
```

### Changer le dossier de travail
```bash
LM_STUDIO_PROJECT_PATH=/chemin/vers/projet
```

### Activer le logging détaillé
```python
# Dans app.py
logging.basicConfig(level=logging.DEBUG)
```

## 📄 Licence

Ce projet est fourni à titre d'exemple.

## 🤝 Support

Pour les problèmes:
1. Vérifiez que LMStudio est en cours d'exécution
2. Consultez les logs dans le terminal
3. Essayez une tâche plus simple
