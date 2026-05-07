# Contributing Guide

## Objectif du projet

Ce projet est un assistant local pour piloter des modèles d'IA en local via LM Studio, avec des outils contrôlés pour lire, modifier et écrire dans le dépôt courant.

L'objectif est de garder un agent léger, utile et sûr pour travailler sur des fichiers locaux sans dépendre d'un service distant.

## Principes

- Garder les changements simples et vérifiables.
- Favoriser des comportements autonomes, mais contrôlés.
- Préserver la compatibilité Windows et Linux quand c'est possible.
- Éviter les sorties inutiles, les boucles et les lectures répétées.
- Utiliser des sorties d'outils courtes et exploitables.

## Profils de machine recommandés

### Machine faible

Pour une machine avec peu de RAM ou un CPU modeste:

- `LLM_TEMPERATURE=0.0`
- `LLM_MAX_TOKENS=1536`
- `LLM_MAX_ITERATIONS=12`
- `LLM_THINKING_STEPS=1`
- `LLM_TOOL_TIMEOUT_SECONDS=30`
- Garder les sorties d'outils courtes.
- Préférer des tâches simples, séquentielles, avec peu de fichiers à la fois.

### Machine moyenne

Pour un usage quotidien équilibré:

- `LLM_TEMPERATURE=0.02`
- `LLM_MAX_TOKENS=3072`
- `LLM_MAX_ITERATIONS=20`
- `LLM_THINKING_STEPS=2`
- `LLM_TOOL_TIMEOUT_SECONDS=45`
- Convient pour de la lecture, des petites modifications et des vérifications limitées.

### Machine puissante

Pour une machine avec plus de RAM et un meilleur CPU/GPU:

- `LLM_TEMPERATURE=0.02`
- `LLM_MAX_TOKENS=4096`
- `LLM_MAX_ITERATIONS=25`
- `LLM_THINKING_STEPS=3`
- `LLM_TOOL_TIMEOUT_SECONDS=60`
- Bon équilibre pour analyser plusieurs fichiers et enchaîner les actions.

### Machine ultra puissante

Pour une machine très confortable:

- `LLM_TEMPERATURE=0.02`
- `LLM_MAX_TOKENS=6144`
- `LLM_MAX_ITERATIONS=35`
- `LLM_THINKING_STEPS=4`
- `LLM_TOOL_TIMEOUT_SECONDS=90`
- Utile pour des tâches longues ou multi-fichiers.

## Configuration locale

Copie `.env.example` vers `.env` puis adapte les valeurs à ton environnement local.

Exemple:

```bash
cp .env.example .env
```

## Flux de travail recommandé

1. Lire les fichiers concernés.
2. Comprendre le but de la tâche.
3. Modifier le minimum nécessaire.
4. Vérifier la syntaxe ou le résultat.
5. Résumer clairement ce qui a changé.

## Contribution de code

- Faire des modifications ciblées.
- Éviter les refactorings de large portée sans besoin.
- Garder les fichiers générés ou spécifiques à l'environnement hors du dépôt si ce n'est pas utile.
- Ne pas écraser les fichiers de configuration d'exemple.

## Vérifications avant commit

- `python -m py_compile app.py`
- Vérifier les scripts de lancement.
- Vérifier que les nouveaux fichiers de configuration sont documentés.

## Style

- Privilégier le concret et le lisible.
- Éviter les réponses verbeuses dans l'agent.
- Préférer des chemins et des messages clairs.

## Remarques

Le projet est destiné à être un assistant local pour les modèles d'IA en local. Toute contribution doit rester alignée avec cet objectif: utilité, autonomie, contrôle et compatibilité avec des machines de puissances différentes.
