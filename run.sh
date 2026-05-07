#!/bin/bash
# Script de lancement rapide

cd "$(dirname "$0")" || exit

if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "Exécutez d'abord: bash setup.sh"
    exit 1
fi

source venv/bin/activate
python app.py
