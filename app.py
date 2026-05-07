#!/usr/bin/env python3
"""
MCP Assistant Local - Utilise LMStudio avec support des outils
"""

from openai import OpenAI
from pathlib import Path
import json
import subprocess
import sys
import logging
from typing import List, Tuple
from dotenv import load_dotenv
import os
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Configuration
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
PROJECT = Path(os.getenv("PROJECT_PATH") or Path.cwd())
MAX_TOOL_OUTPUT_CHARS = int(os.getenv("MAX_TOOL_OUTPUT_CHARS") or "3500")
MAX_FILE_OUTPUT_CHARS = int(os.getenv("MAX_FILE_OUTPUT_CHARS") or "4000")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE") or "0.02")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS") or "4096")
LLM_MAX_ITERATIONS = int(os.getenv("LLM_MAX_ITERATIONS") or "25")
LLM_THINKING_STEPS = int(os.getenv("LLM_THINKING_STEPS") or "3")
LLM_TOOL_TIMEOUT_SECONDS = int(os.getenv("LLM_TOOL_TIMEOUT_SECONDS") or "60")
LLM_STRICT_FILE_TASKS = (os.getenv("LLM_STRICT_FILE_TASKS") or "true").lower() in {"1", "true", "yes", "on"}
LLM_PLAN_THEN_ACTION = (os.getenv("LLM_PLAN_THEN_ACTION") or "true").lower() in {"1", "true", "yes", "on"}
LLM_ENRICHED_TASK_MEMORY = (os.getenv("LLM_ENRICHED_TASK_MEMORY") or "true").lower() in {"1", "true", "yes", "on"}

try:
    client = OpenAI(
        base_url=LM_STUDIO_URL,
        api_key=LM_STUDIO_API_KEY
    )
except Exception as e:
    logger.error(f"Erreur de connexion à LMStudio: {str(e)}")
    sys.exit(1)

def resolve_model_name() -> str:
    """Sélectionne automatiquement le modèle chargé dans LM Studio."""
    configured_model = os.getenv("LM_STUDIO_MODEL")
    if configured_model:
        return configured_model

    try:
        models_response = client.models.list()
        models = getattr(models_response, "data", []) or []
        if models:
            first_model = models[0]
            return getattr(first_model, "id", None) or getattr(first_model, "name", None) or ""
    except Exception as exc:
        logger.warning(f"Impossible de détecter automatiquement le modèle: {exc}")

    raise RuntimeError("Aucun modèle LM Studio détecté. Chargez un modèle ou définissez LM_STUDIO_MODEL.")

LM_STUDIO_MODEL = resolve_model_name()

# Définir les outils disponibles pour le modèle
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit le contenu d'un fichier",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du fichier à lire (relatif à PROJECT ou absolu)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Écrit du contenu dans un fichier (crée ou remplace)",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du fichier (relatif à PROJECT ou absolu)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Contenu à écrire"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Exécute une commande bash",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Commande bash à exécuter"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Liste les fichiers dans un dossier",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du dossier (relatif ou absolu)"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

def get_file_path(path: str) -> Path:
    """Résout le chemin (relatif ou absolu)"""
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT / p
    # Sécurité: vérifier que le chemin ne sort pas du PROJECT
    try:
        p.resolve().relative_to(PROJECT.resolve())
    except ValueError:
        logger.warning(f"Tentative d'accès en dehors de PROJECT: {p}")
        raise ValueError(f"Accès refusé: {path} est en dehors du dossier de travail")
    return p

def read_file(path: str) -> str:
    """Lit un fichier avec troncature de sécurité"""
    try:
        file_path = get_file_path(path)
        if not file_path.exists():
            return f"Fichier introuvable: {path}"
        if not file_path.is_file():
            return f"N'est pas un fichier: {path}"
        content = file_path.read_text(encoding='utf-8')
        logger.info(f"Fichier lu: {file_path}")
        if len(content) > MAX_FILE_OUTPUT_CHARS:
            logger.warning(f"Troncature du fichier {file_path} à {MAX_FILE_OUTPUT_CHARS} caractères")
            return (
                content[:MAX_FILE_OUTPUT_CHARS]
                + f"\n\n...[TRONQUÉ: fichier trop long, {len(content)} caractères au total]"
            )
        return content
    except Exception as e:
        return f"Erreur: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Écrit dans un fichier"""
    try:
        file_path = get_file_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Fichier écrit: {file_path}")
        return f"Fichier écrit: {file_path}"
    except Exception as e:
        return f"Erreur: {str(e)}"

def execute_bash(command: str) -> str:
    """Exécute une commande bash avec troncature de sécurité"""
    try:
        # Limiter les commandes dangereuses
        dangerous_commands = ['rm -rf /', 'sudo', ':(){ :|:& };:', 'fork()']
        if any(cmd in command for cmd in dangerous_commands):
            return "Commande refusée (sécurité)"

        result = subprocess.run(
            command,
            shell=True,
            cwd=PROJECT,
            capture_output=True,
            text=True,
            timeout=LLM_TOOL_TIMEOUT_SECONDS
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr.strip()}"
        if len(output) > MAX_TOOL_OUTPUT_CHARS:
            logger.warning(f"Troncature de la sortie bash à {MAX_TOOL_OUTPUT_CHARS} caractères")
            output = output[:MAX_TOOL_OUTPUT_CHARS] + f"\n...[TRONQUÉ: sortie trop longue]"
        logger.info(f"Commande exécutée: {command}")
        return output if output else "OK"
    except subprocess.TimeoutExpired:
        return f"Erreur: Timeout ({LLM_TOOL_TIMEOUT_SECONDS}s)"
    except Exception as e:
        return f"Erreur: {str(e)}"

def list_directory(path: str) -> str:
    """Liste les fichiers dans un dossier avec sortie compacte"""
    try:
        dir_path = get_file_path(path)
        if not dir_path.exists():
            return f"Dossier introuvable: {path}"
        if not dir_path.is_dir():
            return f"N'est pas un dossier: {path}"
        
        items = sorted(dir_path.iterdir())
        if not items:
            return "Dossier vide"
        
        result = ""
        for item in items:
            prefix = "[DIR]" if item.is_dir() else "[FILE]"
            result += f"{prefix} {item.name}\n"
        if len(result) > MAX_TOOL_OUTPUT_CHARS:
            result = result[:MAX_TOOL_OUTPUT_CHARS] + f"\n...[TRONQUÉ: liste trop longue]"
        logger.info(f"Dossier listé: {dir_path}")
        return result.rstrip()
    except Exception as e:
        return f"Erreur: {str(e)}"

def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Exécute l'outil demandé par le modèle"""
    try:
        if tool_name == "read_file":
            return read_file(tool_input.get("path", ""))
        elif tool_name == "write_file":
            return write_file(tool_input.get("path", ""), tool_input.get("content", ""))
        elif tool_name == "execute_bash":
            return execute_bash(tool_input.get("command", ""))
        elif tool_name == "list_directory":
            return list_directory(tool_input.get("path", "."))
        else:
            return f"Outil inconnu: {tool_name}"
    except Exception as e:
        return f"Erreur: {str(e)}"

def parse_pseudo_tool_call(message: str):
    """Interprète un appel d'outil écrit en texte (ex: list_directory(path: "..."))."""
    if not message:
        return None

    text = message.strip()
    text = text.replace("`", "").strip()

    match = re.match(r'^(read_file|write_file|execute_bash|list_directory)\s*\((.*)\)\s*$', text, re.DOTALL)
    if not match:
        return None

    tool_name = match.group(1)
    args_text = match.group(2).strip()

    # Cas simple: outil(path: "...") ou outil("...")
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', args_text)
    value = quoted.group(1) if quoted and quoted.group(1) is not None else (quoted.group(2) if quoted else None)

    if tool_name in ("read_file", "list_directory"):
        if value:
            return tool_name, {"path": value}
    if tool_name == "execute_bash":
        if value:
            return tool_name, {"command": value}

    # Cas write_file simple: write_file(path: "...", content: "...")
    if tool_name == "write_file":
        path_match = re.search(r'path\s*:\s*"([^"]+)"|path\s*:\s*\'([^\']+)\'', args_text)
        content_match = re.search(r'content\s*:\s*"([\s\S]+)"\s*$|content\s*:\s*\'([\s\S]+)\'\s*$', args_text)
        if path_match and content_match:
            path_value = path_match.group(1) or path_match.group(2)
            content_value = content_match.group(1) or content_match.group(2)
            return tool_name, {"path": path_value, "content": content_value}

    return None

def extract_requested_files(message: str) -> List[str]:
    matches = re.findall(r'([\w./-]+\.[A-Za-z0-9]+)', message)
    unique_files = []
    seen = set()
    for file_name in matches:
        if file_name not in seen:
            unique_files.append(file_name)
            seen.add(file_name)
    return unique_files

def has_write_intent(message: str) -> bool:
    normalized = message.lower()
    keywords = [
        "create", "crée", "cree", "generate", "write", "écris", "ecris",
        "modifie", "modifier", "update", "refais", "convert", "transform",
    ]
    return any(keyword in normalized for keyword in keywords)

def has_improve_intent(message: str) -> bool:
    normalized = message.lower()
    keywords = ["ameliore", "améliore", "improve", "optimize", "optimise", "mieux", "perfectionne"]
    return any(keyword in normalized for keyword in keywords)

def improve_bat_content(file_name: str, content: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    lines = content.splitlines()

    if not lines:
        lines = ["@echo off"]
        notes.append("Ajout de @echo off")

    if lines and lines[0].strip().lower() != "@echo off":
        lines.insert(0, "@echo off")
        notes.append("Ajout de @echo off en tête")

    has_setlocal = any(line.strip().lower() == "setlocal enabledelayedexpansion" for line in lines)
    if not has_setlocal:
        insert_idx = 1 if len(lines) > 1 else len(lines)
        lines.insert(insert_idx, "setlocal enabledelayedexpansion")
        notes.append("Ajout de setlocal enabledelayedexpansion")

    has_cd = any('cd /d "%~dp0"' in line.lower() for line in lines)
    if not has_cd:
        insert_idx = 2 if len(lines) > 2 else len(lines)
        lines.insert(insert_idx, "cd /d \"%~dp0\" || exit /b 1")
        notes.append("Ajout de la navigation vers le dossier du script")

    lower_name = file_name.lower()
    if lower_name == "run.bat":
        has_activate = any("call venv\\scripts\\activate.bat" in line.lower() for line in lines)
        has_python = any(line.strip().lower() == "python app.py" for line in lines)
        if not has_activate:
            lines.append("call venv\\Scripts\\activate.bat")
            notes.append("Ajout de l'activation du venv")
        if not has_python:
            lines.append("python app.py")
            notes.append("Ajout du lancement de app.py")

    return "\n".join(lines) + "\n", notes

def enforce_file_task_completion(
    user_message: str,
    requested_files: List[str],
    messages: List[dict],
    assistant_message: str,
) -> Tuple[bool, str]:
    """Vérifie qu'une tâche de fichiers est réellement terminée, puis améliore si demandé."""
    if not LLM_STRICT_FILE_TASKS or not requested_files or not has_write_intent(user_message):
        return False, assistant_message

    missing_files = []
    for file_name in requested_files:
        try:
            target = get_file_path(file_name)
        except Exception:
            continue
        if not target.exists():
            missing_files.append(file_name)

    if missing_files:
        messages.append({
            "role": "system",
            "content": (
                "La tâche n'est pas terminée: les fichiers suivants manquent encore: "
                + ", ".join(missing_files)
                + ". Utilise write_file maintenant et termine la tâche."
            ),
        })
        return True, assistant_message

    if has_improve_intent(user_message):
        improvements = []
        for file_name in requested_files:
            try:
                target = get_file_path(file_name)
            except Exception:
                continue
            if target.exists() and target.is_file() and target.suffix.lower() == ".bat":
                original = target.read_text(encoding="utf-8")
                improved, notes = improve_bat_content(file_name, original)
                if notes and improved != original:
                    target.write_text(improved, encoding="utf-8")
                    improvements.append(f"{file_name}: " + "; ".join(notes))

        if improvements:
            extra = "\nAméliorations automatiques appliquées:\n- " + "\n- ".join(improvements)
            assistant_message = (assistant_message + extra).strip()

    return False, assistant_message

def build_task_state_note(user_message: str, tool_name: str, tool_input: dict, tool_result: str) -> str:
    """Construit un rappel compact de l'état courant pour le modèle."""
    if not LLM_ENRICHED_TASK_MEMORY:
        return (
            "Outil exécuté: "
            + tool_name
            + "\nRésultat utile: "
            + tool_result[:250].replace("\n", " ").strip()
        )

    parts = [
        "État de la tâche:",
        f"- Demande initiale: {user_message}",
        f"- Outil exécuté: {tool_name}",
    ]

    if tool_name in {"read_file", "list_directory", "execute_bash"}:
        parts.append("- Ce résultat doit être considéré comme appris pour la suite de la tâche.")

    if tool_name == "write_file":
        parts.append(f"- Fichier modifié/créé: {tool_input.get('path', '')}")

    short_result = tool_result[:500].replace("\n", " ").strip()
    parts.append(f"- Résultat utile: {short_result}")
    parts.append("- Prochaine action attendue: utiliser ce qui a déjà été appris, éviter de relire la même chose, et terminer la tâche si c'est suffisant.")
    return "\n".join(parts)

def build_plan_instruction(user_message: str) -> str:
    if not LLM_PLAN_THEN_ACTION:
        return "Réponds directement ou exécute l'action utile sans plan écrit."

    return (
        "Mode plan puis action: "
        "1) Fais une mini-stratégie en une ou deux phrases max. "
        "2) Puis exécute immédiatement les outils utiles. "
        "3) Termine avec une réponse finale concise qui confirme le résultat."
    )

def chat_with_tools(user_message: str):
    """Boucle conversationnelle avec support des outils"""
    thinking_guidance = "\n".join([
        "Avant d'agir, réfléchis brièvement à la meilleure stratégie.",
        "Si la demande est complexe, fais d'abord une synthèse mentale courte.",
        "N'utilise les outils que si cela aide vraiment à résoudre la tâche.",
        "Quand tu as assez d'informations, exécute la meilleure action sans détour.",
    ])

    messages = [
        {
            "role": "system",
            "content": f"""Tu es un assistant de développement autonome, précis et concis.

📁 Dossier de travail: {PROJECT}

🔧 Outils disponibles:
- read_file(path) → Lire un fichier
- write_file(path, content) → Créer/modifier un fichier
- execute_bash(command) → Exécuter une commande
- list_directory(path) → Lister un dossier

⚡ RÈGLES STRICTES:
1. Décide toi-même des outils à utiliser selon la demande
2. Utilise les outils uniquement si c'est utile à la tâche
3. Si une tâche implique de créer ou modifier un fichier, écris le fichier directement
4. Si tu as assez d'information, n'utilise aucun outil et réponds directement
5. Après les outils, réponds brièvement et clairement
6. Si le projet doit être compris, lis seulement ce qui est nécessaire puis conclus
7. Réfléchis un peu plus longtemps si cela améliore la qualité, mais sans bavarder inutilement

❌ INTERDICTIONS:
- Pas d'accès en dehors de {PROJECT}
- Pas rm -rf, sudo, ou commandes dangereuses
- Timeout: {LLM_TOOL_TIMEOUT_SECONDS} secondes

🧠 CONSIGNE DE RÉFLEXION:
{thinking_guidance}

🧭 MODE D'EXÉCUTION:
{build_plan_instruction(user_message)}

📝 EXEMPLE:
Demande: "crée un fichier test.py avec hello()"
→ Appelle write_file("test.py", "def hello():...")
→ Réponds: "Fichier test.py créé"
(PAS d'appels supplémentaires)"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    logger.info(f"Requête utilisateur: {user_message}")
    requested_files = extract_requested_files(user_message)
    tool_calls_count = 0
    max_iterations = LLM_MAX_ITERATIONS
    called_tools = set()
    repeated_call_detected = False
    finalization_mode = False

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        try:
            tool_choice = "auto"

            if iteration <= LLM_THINKING_STEPS:
                messages.append({
                    "role": "system",
                    "content": "Prends quelques secondes de plus pour raisonner. Ne réponds pas vite: choisis l'action la plus pertinente et ne lance un outil que si nécessaire."
                })

            if finalization_mode:
                messages.append({
                    "role": "system",
                    "content": "Tu es en phase de clôture. N'utilise plus d'outil. Termine la tâche maintenant avec une réponse finale utile, concise et complète. Si le travail est déjà fait, résume le résultat exact."
                })
                tool_choice = "none"

            response = client.chat.completions.create(
                model=LM_STUDIO_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice=tool_choice,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
            )

            # Vérifier si le modèle demande l'utilisation d'outils
            tool_calls = response.choices[0].message.tool_calls
            assistant_message = response.choices[0].message.content or ""

            if not tool_calls:
                pseudo_call = parse_pseudo_tool_call(assistant_message)
                if pseudo_call:
                    tool_name, tool_input = pseudo_call
                    logger.warning(f"Pseudo outil detecte dans la reponse texte: {tool_name}")
                    pseudo_result = process_tool_call(tool_name, tool_input)
                    tool_calls_count += 1
                    print(f"\n🔧 Exécution (récupération):")
                    short_result = pseudo_result[:120].replace('\n', ' ')
                    if len(pseudo_result) > 120:
                        short_result += "..."
                    print(f"   • {tool_name}: {short_result}")

                    messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    messages.append({
                        "role": "tool",
                        "tool_use_id": f"pseudo-{iteration}-{tool_calls_count}",
                        "name": tool_name,
                        "content": pseudo_result
                    })
                    continue

                should_continue, assistant_message = enforce_file_task_completion(
                    user_message=user_message,
                    requested_files=requested_files,
                    messages=messages,
                    assistant_message=assistant_message,
                )
                if should_continue:
                    continue

                if assistant_message:
                    print(f"\n🤖 {assistant_message}")
                logger.info(f"Réponse terminée après {tool_calls_count} outil(s)")
                break

            # Ajouter le message du modèle
            messages.append({
                "role": "assistant",
                "content": assistant_message or ""
            })

            # Traiter les appels d'outils
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Vérifier si l'outil a déjà été appelé
                tool_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
                if tool_key in called_tools:
                    logger.warning(f"Outil redondant détecté: {tool_name}")
                    repeated_call_detected = True
                    result = "Outil déjà utilisé. Réponds maintenant de façon concise avec ce qui a déjà été appris."
                else:
                    called_tools.add(tool_key)
                    tool_calls_count += 1
                    result = process_tool_call(tool_name, tool_input)
                    logger.info(f"Outil: {tool_name} - {len(result)} chars")

                tool_results.append((tool_name, result))

                # Ajouter le résultat à la conversation
                messages.append({
                    "role": "tool",
                    "tool_use_id": tool_call.id,
                    "name": tool_name,
                    "content": result
                })

                messages.append({
                    "role": "system",
                    "content": build_task_state_note(user_message, tool_name, tool_input, result),
                })

            # Afficher les outils exécutés
            if tool_results:
                print(f"\n🔧 Exécution:")
                for tool_name, result in tool_results:
                    result_short = result[:120].replace('\n', ' ')
                    if len(result) > 120:
                        result_short += "..."
                    print(f"   • {tool_name}: {result_short}")

            if repeated_call_detected:
                logger.warning("Arrêt après détection d'un appel répété; réponse finale forcée")
                finalization_mode = True
                repeated_call_detected = False
                messages.append({
                    "role": "system",
                    "content": "Évite toute répétition. Termine immédiatement la tâche avec le meilleur résultat final possible en une seule réponse, sans nouveau tool call."
                })
                continue

        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            print(f"\n❌ {str(e)}")
            break

    if iteration >= max_iterations:
        logger.warning("Limite d'itérations atteinte")
        print(f"\n⚠️ Limite atteinte - réponse finale forcée")

# Boucle principale
def main():
    """Boucle principale de l'application"""
    print("\n" + "="*60)
    print("🚀 MCP Assistant Local - Powered by LMStudio")
    print("="*60)
    print(f"📁 Travail dans: {PROJECT}")
    print(f"🤖 Modèle: {LM_STUDIO_MODEL}")
    print("\n💡 Commandes: tapez 'exit', 'help', ou 'clear'")
    print("="*60 + "\n")

    try:
        while True:
            try:
                prompt = input(">>> ").strip()
                
                if not prompt:
                    continue
                
                if prompt.lower() in ["exit", "quit"]:
                    print("👋 Terminé!")
                    logger.info("Arrêt de l'application")
                    break
                
                if prompt.lower() == "clear":
                    os.system("clear" if os.name == "posix" else "cls")
                    continue
                
                if prompt.lower() == "help":
                    print("\n📚 Outils disponibles:")
                    print("  • read_file: Lire un fichier")
                    print("  • write_file: Créer/modifier un fichier")
                    print("  • execute_bash: Exécuter une commande")
                    print("  • list_directory: Lister un dossier\n")
                    continue

                # Traiter la demande
                chat_with_tools(prompt)

            except KeyboardInterrupt:
                print("\n⚠️ Interruption")
                logger.info("Interruption utilisateur (Ctrl+C)")
                continue
            except EOFError:
                print("\n👋 Au revoir!")
                break

    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        print(error_msg, file=sys.stderr)
        logger.critical(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()