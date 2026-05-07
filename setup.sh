#!/bin/bash
# Script de setup pour MCP Assistant Local

set -e  # Exit on error

echo "📦 MCP Assistant Local - Setup"
echo "================================"

# Vérifier Python
echo "✓ Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "  ✓ Python $PYTHON_VERSION trouvé"

# Créer venv si nécessaire
if [ ! -d "venv" ]; then
    echo "✓ Création de l'environnement virtuel..."
    python3 -m venv venv
    echo "  ✓ Environnement virtuel créé"
fi

# Activer venv
echo "✓ Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "✓ Installation des dépendances..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "  ✓ Dépendances installées"

# Vérifier la configuration
echo "✓ Vérification de la configuration..."
if [ ! -f ".env" ]; then
    echo "  ⚠️ Fichier .env non trouvé (créé avec valeurs par défaut)"
else
    echo "  ✓ Fichier .env trouvé"
fi

# Afficher les instructions
echo ""
echo "✅ Setup terminé!"
echo ""
echo "🚀 Pour démarrer l'application:"
echo ""
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "📚 Plus d'informations dans README.md"
echo ""
