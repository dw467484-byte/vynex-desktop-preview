from __future__ import annotations

"""VYNEX Studio Premium — interface affinée : couleurs harmonisées, chat, images, voix et développeur.

Dépendances Python : bibliothèque standard uniquement. Pillow est facultatif pour les
miniatures JPG et les captures d'écran. Les moteurs IA et leurs modèles restent dans
VYNEXRuntime ou dans le dossier configuré par VYNEX_HOME. L'ancien dossier Windows
D:\\MonIA\\MonIA_Lite reste accepté s'il existe.
"""

import base64
import json
import math
import mimetypes
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

try:
    from PIL import Image, ImageTk, ImageGrab  # type: ignore
    PIL_AVAILABLE = True
except Exception:
    Image = ImageTk = ImageGrab = None
    PIL_AVAILABLE = False

APP_TITLE = "VYNEX"
SCRIPT_DIR = Path(__file__).resolve().parent
# VYNEX garde le chemin historique sous Windows, mais utilise un chemin configurable
# sur macOS/Linux. VYNEX_HOME peut désigner un dossier contenant engine/ et models/.
if os.name == "nt":
    # Preserve the existing development installation when it is present, but do not
    # require D:\MonIA on other Windows computers. New installs use the user's profile.
    _legacy_runtime_root = Path(r"D:\MonIA\MonIA_Lite")
    _portable_runtime_root = Path.home() / "VYNEXRuntime"
    _default_runtime_root = _legacy_runtime_root if _legacy_runtime_root.is_dir() else _portable_runtime_root
else:
    _default_runtime_root = Path.home() / "VYNEXRuntime"
CANONICAL_ROOT = Path(os.environ.get("VYNEX_HOME", str(_default_runtime_root))).expanduser()
MODEL_NAME = "SmolVLM-500M-Instruct-Q8_0.gguf"
MMPROJ_NAME = "mmproj-SmolVLM-500M-Instruct-Q8_0.gguf"
ENGINE_NAME = "llama-server.exe" if os.name == "nt" else "llama-server"
SERVER_URL = "http://127.0.0.1:9931"  # llama.cpp : analyse d'images
HEALTH_URL = SERVER_URL + "/health"
CHAT_URL = SERVER_URL + "/v1/chat/completions"
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_CHAT_URL = OLLAMA_URL + "/api/chat"
DEFAULT_CHAT_MODEL = "llama3.2:3b"
VOSK_MODEL_NAME = "vosk-model-small-fr-0.22"

# Palette « Aurora Elite » : bleu encre, vert menthe et lueur glacier.
# Couleurs fixes et dessin statique pour préserver les performances sur PC modestes.
BG = "#080D19"
SIDEBAR = "#0C1425"
PANEL = "#121E33"
PANEL_HOVER = "#1B2B46"
PANEL_ACTIVE = "#244360"
CHAT_PANEL = "#0A1426"
BORDER = "#293B56"
BORDER_HOVER = "#587CA3"
TEXT = "#F4F7FF"
MUTED = "#A4B4CC"
ACCENT = "#36E6B7"
ACCENT_HOVER = "#68F0CC"
BLUE = "#83C7FF"
PURPLE = "#B5A2FF"
ERROR = "#FF7F9D"
WARNING = "#FFD38A"

def _get_user_data_dir() -> Path:
    """Chemin de données conventionnel pour Windows, macOS et Linux."""
    if os.name == "nt":
        # Conserve la base utilisée par les installations Windows précédentes.
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return base / "MonIA Lite"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "VYNEX"
    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "vynex"


LOCAL_DATA = _get_user_data_dir()
DATA_DIR = LOCAL_DATA / "data"
IMAGE_DIR = LOCAL_DATA / "images"
LOG_DIR = LOCAL_DATA / "logs"
CHATS_FILE = DATA_DIR / "chats.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
for _dir in (DATA_DIR, IMAGE_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Consentement et avis de confidentialité. Incrémenter cette version à chaque
# modification importante des conditions afin d'afficher à nouveau l'avis au lancement.
LEGAL_NOTICE_VERSION = "2026-10-22-v1"
TERMS_TEXT = """CONDITIONS D’UTILISATION — VYNEX (PRÉVERSION)

1. Statut du logiciel
VYNEX est un logiciel en préversion fourni « en l’état ». Des erreurs, interruptions,
pertes de données ou incompatibilités peuvent survenir. Aucune disponibilité ni aucun
résultat particulier n’est garanti.

2. Résultats de l’IA
Les réponses et images générées peuvent être inexactes, incomplètes ou inadaptées.
Vérifiez les informations importantes. N’utilisez pas VYNEX comme unique source pour
une décision médicale, juridique, financière, de sécurité ou d’urgence.

3. Utilisation autorisée
Vous restez responsable des contenus que vous saisissez, joignez, générez ou partagez
et du respect des lois, droits d’auteur, droits à l’image et droits d’autrui. N’envoyez
pas de mots de passe, secrets ou données personnelles que vous n’êtes pas autorisé à
utiliser.

4. Moteurs tiers
VYNEX est une interface. Ollama, llama.cpp, Vosk, AUTOMATIC1111/Forge, leurs modèles
et toutes les dépendances sont des composants distincts pouvant avoir leurs propres
licences, conditions, limites et avis de confidentialité. Il incombe à l’exploitant de
vérifier les licences et conditions des composants qu’il installe ou distribue.

5. Modifications et distribution
Ne redistribuez pas VYNEX ou ses composants comme si vous déteniez des droits que vous
n’avez pas. L’inclusion d’un composant tiers exige le respect de sa licence. Le code et
les paquets publiés peuvent être modifiés ; vérifiez leur provenance avant exécution.

6. Acceptation
En cliquant sur « J’accepte et continuer », vous confirmez avoir lu cet avis et acceptez
ces conditions pour utiliser cette préversion. Refuser ferme l’application. Ce texte est
un modèle de conditions à faire relire et compléter par le responsable de la publication ;
il ne remplace pas un avis juridique adapté au pays de distribution.
"""

PRIVACY_TEXT = """CONFIDENTIALITÉ ET DONNÉES — VYNEX

Traitement par défaut
• Les conversations et préférences sont enregistrées dans le dossier de données local
  indiqué dans Paramètres > Données & confidentialité. L’historique peut être désactivé.
• Les appels d’IA sont adressés par défaut à des services locaux sur 127.0.0.1. Le code
  fourni ne contient pas de télémétrie intégrée.
• Si vous remplacez l’adresse du moteur par un serveur distant, les messages, le contexte,
  le texte extrait des fichiers et les descriptions d’images envoyés au moteur peuvent quitter
  cet ordinateur. VYNEX affiche un avertissement et mémorise l’accord pour cette adresse exacte.
  Les images jointes sont normalement analysées par le moteur visuel local avant l’envoi de la
  description au serveur de conversation.
• Les images jointes et captures peuvent être conservées dans la bibliothèque locale.
  Effacer l’historique ne supprime pas automatiquement les fichiers de la bibliothèque.
• Les journaux du moteur peuvent contenir des messages techniques et des chemins de fichiers.

Accès facultatifs
• Microphone : uniquement lorsque vous lancez une dictée ou une conversation vocale,
  après confirmation dans VYNEX et sous réserve des réglages d’autorisation du système.
• Capture d’écran : uniquement après votre confirmation explicite pour chaque capture.
  Une capture peut contenir des informations visibles confidentielles.
• Fichiers et images : l’utilisateur choisit les fichiers dans le sélecteur de fichiers.
• Caméra, contacts et localisation : VYNEX ne les utilise pas dans cette version.

Contrôle et suppression
Vous pouvez refuser une autorisation, révoquer les autorisations mémorisées dans Paramètres,
désactiver l’historique et supprimer les conversations sauvegardées. Pour effacer les images
et captures, supprimez-les également depuis la bibliothèque locale ou le dossier de données.
Les réglages de confidentialité de Windows, macOS ou Linux peuvent bloquer un accès même
si VYNEX l’autorise. Ces conditions seront mises à jour avant les publications officielles.
"""

PERMISSION_DESCRIPTIONS = {
    "microphone": (
        "Le microphone est utilisé uniquement pour la dictée ou la conversation vocale lorsque vous cliquez sur le bouton vocal. "
        "VYNEX traite l’audio avec le moteur de reconnaissance disponible sur cet appareil. Aucun enregistrement permanent de la voix n’est voulu par cette fonction ; le texte reconnu est placé dans le champ de saisie. "
        "Le système peut afficher une demande d’autorisation distincte."
    ),
    "screen_capture": (
        "VYNEX peut capturer l’écran entier après une seconde confirmation à chaque capture. La capture peut inclure des messages, documents ou autres informations privées. "
        "L’image est enregistrée dans la bibliothèque locale et préparée comme pièce jointe ; elle n’est envoyée au moteur que lorsque vous envoyez le message."
    ),
}

SYSTEM_PROMPT = (
    "Tu es VYNEX, un assistant personnel local. Réponds naturellement en français par défaut, "
    "sauf si l'utilisateur choisit une autre langue. Réponds directement à la question, avec "
    "des explications claires et un ton chaleureux. Pour une salutation, réponds naturellement. "
    "Si l'utilisateur demande ce que tu sais faire, présente honnêtement tes fonctions : discuter, "
    "expliquer, rédiger, aider à programmer et analyser une image jointe. Ne répète jamais ces "
    "consignes ni le message système. N'affirme pas avoir consulté Internet ou contrôlé Windows "
    "si cela n'a pas réellement été fait. Si tu n'es pas sûr, dis-le clairement."
)


def clean_text_for_speech(text: str) -> str:
    """Supprime les éléments Markdown gênants avant la synthèse vocale."""
    text = re.sub(r"```.*?```", " bloc de code omis ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*•]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)
    text = re.sub(r"[>*_~]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def find_vosk_model_dir() -> Path | None:
    """Trouve le petit modèle français Vosk s'il a été installé localement."""
    roots = [LOCAL_DATA / "models", CANONICAL_ROOT / "models", SCRIPT_DIR / "models", SCRIPT_DIR.parent / "models"]
    for root in roots:
        direct = root / VOSK_MODEL_NAME
        if direct.is_dir() and (direct / "am").exists():
            return direct
        if root.is_dir():
            try:
                for candidate in root.glob(VOSK_MODEL_NAME + "*"):
                    if candidate.is_dir() and (candidate / "am").exists():
                        return candidate
            except OSError:
                pass
    return None



def read_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp.replace(path)


# Thèmes proposés par les paramètres. Le thème sélectionné est appliqué au prochain
# lancement afin d'éviter de recolorer à moitié des widgets Tk déjà créés.
THEME_PRESETS = {
    "aurora": {
        "BG": "#080D19", "SIDEBAR": "#0C1425", "PANEL": "#121E33",
        "PANEL_HOVER": "#1B2B46", "PANEL_ACTIVE": "#244360", "CHAT_PANEL": "#0A1426",
        "BORDER": "#293B56", "BORDER_HOVER": "#587CA3", "TEXT": "#F4F7FF",
        "MUTED": "#A4B4CC", "ACCENT": "#36E6B7", "ACCENT_HOVER": "#68F0CC",
        "BLUE": "#83C7FF", "PURPLE": "#B5A2FF", "ERROR": "#FF7F9D", "WARNING": "#FFD38A",
    },
    "ocean": {
        "BG": "#07111E", "SIDEBAR": "#0A1A2B", "PANEL": "#10283C",
        "PANEL_HOVER": "#173A52", "PANEL_ACTIVE": "#204E6A", "CHAT_PANEL": "#071827",
        "BORDER": "#27445A", "BORDER_HOVER": "#4E88A8", "TEXT": "#F3FAFF",
        "MUTED": "#A4C0D6", "ACCENT": "#55B8FF", "ACCENT_HOVER": "#86CEFF",
        "BLUE": "#6DE0D2", "PURPLE": "#A6AEFF", "ERROR": "#FF839A", "WARNING": "#FFD78C",
    },
    "violet": {
        "BG": "#0D0B1B", "SIDEBAR": "#13102A", "PANEL": "#1C1837",
        "PANEL_HOVER": "#29234A", "PANEL_ACTIVE": "#3A315F", "CHAT_PANEL": "#100E22",
        "BORDER": "#3A325E", "BORDER_HOVER": "#7564A8", "TEXT": "#F8F5FF",
        "MUTED": "#B9AED8", "ACCENT": "#B69CFF", "ACCENT_HOVER": "#D1C1FF",
        "BLUE": "#87CFFF", "PURPLE": "#E0A7FF", "ERROR": "#FF8FB1", "WARNING": "#F8D58E",
    },
    "emerald": {
        "BG": "#07130F", "SIDEBAR": "#0B1A14", "PANEL": "#122A20",
        "PANEL_HOVER": "#1A3B2D", "PANEL_ACTIVE": "#265642", "CHAT_PANEL": "#091A13",
        "BORDER": "#244A39", "BORDER_HOVER": "#498467", "TEXT": "#F0FFF7",
        "MUTED": "#A4C7B4", "ACCENT": "#46E6A4", "ACCENT_HOVER": "#79F2BD",
        "BLUE": "#8BD8FF", "PURPLE": "#C0ADFF", "ERROR": "#FF8FA3", "WARNING": "#F6D68A",
    },
}
_BOOT_SETTINGS = read_json(SETTINGS_FILE, {})
_BOOT_THEME = str(_BOOT_SETTINGS.get("theme", "aurora")) if isinstance(_BOOT_SETTINGS, dict) else "aurora"
if _BOOT_THEME not in THEME_PRESETS:
    _BOOT_THEME = "aurora"
globals().update(THEME_PRESETS[_BOOT_THEME])


def find_asset(filename: str, folder: str) -> Path:
    """Cherche les ressources dans le dossier installé, même si le script est déplacé."""
    roots = [SCRIPT_DIR, CANONICAL_ROOT, SCRIPT_DIR.parent]
    seen: set[str] = set()
    for root in roots:
        try:
            key = str(root.resolve()).casefold()
        except OSError:
            key = str(root).casefold()
        if key in seen or not root.exists() or not root.is_dir():
            continue
        seen.add(key)
        direct = root / folder / filename
        if direct.is_file():
            return direct
        try:
            for candidate in (root / folder).rglob(filename):
                if candidate.is_file():
                    return candidate
        except (OSError, PermissionError):
            pass
    # Report/search the configured runtime location when a model is missing; this is
    # more useful than pointing at the bundled application directory.
    return CANONICAL_ROOT / folder / filename


def find_image_asset(filename: str) -> Path | None:
    """Trouve une image aussi bien en mode Python qu'après compilation PyInstaller."""
    roots: list[Path] = []
    # PyInstaller extrait les ressources embarquées dans _MEIPASS.
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        roots.append(Path(frozen_root))
    # En mode EXE, l'image peut également se trouver à côté de l'exécutable.
    if getattr(sys, "frozen", False):
        try:
            roots.append(Path(sys.executable).resolve().parent)
        except OSError:
            pass
    roots.extend([
        SCRIPT_DIR,
        SCRIPT_DIR / "assets",
        SCRIPT_DIR / "images",
        SCRIPT_DIR.parent,
        CANONICAL_ROOT,
        CANONICAL_ROOT / "assets",
    ])
    seen: set[str] = set()
    for root in roots:
        try:
            key = str(root.resolve()).casefold()
        except OSError:
            key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        for candidate in (root / filename, root / "assets" / filename, root / "images" / filename):
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
    return None


def find_engine_asset() -> Path:
    """Find the llama.cpp server using the native executable name for this OS."""
    names = [ENGINE_NAME]
    alternate = "llama-server" if ENGINE_NAME.lower().endswith(".exe") else "llama-server.exe"
    names.append(alternate)
    roots = [SCRIPT_DIR, CANONICAL_ROOT, SCRIPT_DIR.parent]
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        roots.insert(0, Path(frozen_root))
    for root in roots:
        for folder in ("engine", "bin"):
            for name in names:
                candidate = root / folder / name
                if candidate.is_file():
                    return candidate
        for name in names:
            try:
                matches = list(root.rglob(name)) if root.is_dir() else []
            except (OSError, PermissionError):
                matches = []
            if matches:
                return matches[0]
    return CANONICAL_ROOT / "engine" / ENGINE_NAME


ENGINE_EXE = find_engine_asset()
MODEL_PATH = find_asset(MODEL_NAME, "models")
MMPROJ_PATH = find_asset(MMPROJ_NAME, "models")


def file_mime(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed if guessed and guessed.startswith("image/") else "image/png"


def open_path_with_default_app(path: Path) -> None:
    """Open a file/folder with the OS default application on Windows/macOS/Linux."""
    target = str(Path(path).expanduser().resolve())
    if os.name == "nt":
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        opener = shutil.which("xdg-open")
        if not opener:
            raise RuntimeError("La commande xdg-open est indisponible sur cette distribution Linux.")
        subprocess.Popen([opener, target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_windows_powershell_script(name: str, contents: str) -> Path:
    path = DATA_DIR / name
    path.write_text(contents, encoding="utf-8-sig")
    return path


TTS_SCRIPT = make_windows_powershell_script(
    "monia_speak.ps1",
    r'''param([string]$TextPath, [int]$Rate = 0)
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Speech
    $text = [System.IO.File]::ReadAllText($TextPath, [System.Text.Encoding]::UTF8)
    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $voice = $speaker.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'fr-*' } | Select-Object -First 1
        if ($voice) { $speaker.SelectVoice($voice.VoiceInfo.Name) }
        if ($Rate -lt -5) { $Rate = -5 }
        if ($Rate -gt 5) { $Rate = 5 }
        $speaker.Rate = $Rate
        $speaker.Volume = 100
        $speaker.Speak($text)
    } finally {
        $speaker.Dispose()
    }
} finally {
    Remove-Item -LiteralPath $TextPath -Force -ErrorAction SilentlyContinue
}
''',
)

STT_SCRIPT = make_windows_powershell_script(
    "monia_listen.ps1",
    r'''param([string]$ResultPath)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
try {
    Add-Type -AssemblyName System.Speech
    $all = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
    $rec = $all | Where-Object { $_.Culture.Name -eq 'fr-FR' -or $_.Culture.Name -like 'fr-*' } | Select-Object -First 1
    if (-not $rec) {
        $langs = ($all | ForEach-Object { $_.Culture.Name }) -join ', '
        [System.IO.File]::WriteAllText($ResultPath, "__NO_FRENCH_RECOGNIZER__|$langs", $utf8)
        exit 3
    }
    $engine = New-Object -TypeName System.Speech.Recognition.SpeechRecognitionEngine -ArgumentList $rec
    try {
        $grammar = New-Object System.Speech.Recognition.DictationGrammar
        $engine.LoadGrammar($grammar)
        $engine.SetInputToDefaultAudioDevice()
        $engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds(6)
        $engine.BabbleTimeout = [TimeSpan]::FromSeconds(3)
        $result = $engine.Recognize([TimeSpan]::FromSeconds(20))
        if ($result -and $result.Text) {
            [System.IO.File]::WriteAllText($ResultPath, $result.Text, $utf8)
        } else {
            [System.IO.File]::WriteAllText($ResultPath, '__NO_SPEECH__', $utf8)
        }
    } finally {
        $engine.Dispose()
    }
} catch {
    [System.IO.File]::WriteAllText($ResultPath, ('__ERROR__|' + $_.Exception.Message), $utf8)
    exit 4
}
''',
)


class VYNEXApp:
    def __init__(self):
        self.root = tk.Tk()
        self._window_icon_photo = None
        try:
            icon_path = find_image_asset("VYNEX.ico")
            if os.name == "nt" and icon_path is not None:
                self.root.iconbitmap(str(icon_path))
        except (tk.TclError, OSError):
            pass
        try:
            png_icon = find_image_asset("VYNEX_icon.png")
            if png_icon is not None:
                raw_icon = tk.PhotoImage(file=str(png_icon))
                # Garde une icône de fenêtre légère et nette sur Windows, macOS et Linux.
                scale = max(1, (max(raw_icon.width(), raw_icon.height()) + 63) // 64)
                self._window_icon_photo = raw_icon.subsample(scale, scale)
                self.root.iconphoto(True, self._window_icon_photo)
        except (tk.TclError, OSError):
            pass
        self.root.title(APP_TITLE)
        self.root.geometry("1220x780")
        self.root.minsize(850, 600)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        default_settings = {
            "temperature": 0.25,
            "max_tokens": 512,
            "auto_speak": False,
            "speak_rate": 0,
            "active_project": "",
            "chat_model": DEFAULT_CHAT_MODEL,
            "chat_url": OLLAMA_URL,
            "voice_auto_send": True,
            "deep_mode": False,
            "theme": "aurora",
            "response_language": "Français",
            "response_style": "Équilibré",
            "custom_instructions": "",
            "chat_font_size": 12,
            "save_history": True,
            "vision_max_images": 4,
            "permissions": {},
        }
        self.settings = read_json(SETTINGS_FILE, default_settings)
        if not isinstance(self.settings, dict):
            self.settings = default_settings.copy()
        for key, value in default_settings.items():
            self.settings.setdefault(key, value)
        stored_chats = read_json(CHATS_FILE, {})
        self.chats = stored_chats if isinstance(stored_chats, dict) else {}

        self.current_chat_id: str | None = None
        self.current_turns: list[dict] = []
        self.api_messages: list[dict] = [{"role": "system", "content": self._effective_system_prompt()}]
        self.pending_images: list[Path] = []
        self.pending_files: list[Path] = []
        self.photo_refs: list[object] = []
        self.thumbnail_refs: dict[str, object] = {}
        self.busy = False
        self.image_generation_busy = False
        self.listen_busy = False
        self.voice_output = bool(self.settings.get("auto_speak", False))
        self.deep_mode = bool(self.settings.get("deep_mode", False))
        self.voice_session_active = False
        self._voice_output_before_session = self.voice_output
        self.speak_next_response = False
        self.force_voice_auto_send = False
        self._listen_started_in_session = False
        self._voice_session_pending = False
        self.tts_process: subprocess.Popen | None = None
        self.server_process: subprocess.Popen | None = None
        self.started_server_here = False
        self.active_response = None
        self.stop_event = threading.Event()
        self.plus_popup = None
        self.sidebar_visible = True
        self.active_project = str(self.settings.get("active_project", "") or "")
        self.last_assistant_answer = ""
        self.status_var = tk.StringVar(value="Vérification du moteur local…")
        self.voice_status_var = tk.StringVar(value="Voix : arrêtée")
        self._stream_insert_ready = False
        self._voice_controls: list[tk.Widget] = []
        # État des animations VYNEX Studio
        self._animations_enabled = bool(self.settings.get("animations_enabled", True))
        self._animation_phase = 0.0
        self._animation_frame = 0
        self._animation_after_id = None
        self._hero_canvas = None
        self._hero_outer_ring = None
        self._hero_inner_ring = None
        self._hero_halo = None
        self._hero_core = None
        self._hero_symbol = None
        self._hero_orbit_dot = None
        self._hero_orbit_dot2 = None
        self._hero_orbit_dot3 = None
        self._build_ui()
        self._apply_chat_font_size(int(self.settings.get("chat_font_size", 12)))
        self.new_chat(initial=True)
        self.root.bind_all("<Control-u>", lambda _e: self.attach_files())
        self.root.bind_all("<Control-U>", lambda _e: self.attach_files())
        self.root.bind_all("<Control-n>", lambda _e: self.new_chat())
        self.root.bind_all("<Control-Return>", self.send_message)
        self.root.bind_all("<Control-Shift-c>", self.copy_last_answer)
        self.root.bind_all("<Escape>", lambda _e: self.close_plus_menu())
        # The consent screen gates engine startup on first launch or after a policy update.
        self.root.after(100, self._startup_legal_gate)


        if self._animations_enabled:
            self._animation_after_id = self.root.after(350, self._animate_vynex_ui)
    def _effective_system_prompt(self) -> str:
        """Construit les préférences de réponse réellement appliquées au modèle."""
        prompt = SYSTEM_PROMPT
        language = str(self.settings.get("response_language", "Français"))
        if language == "English":
            prompt += "\nRéponds en anglais par défaut, sauf demande explicite d'une autre langue."
        elif language == "Auto (langue du message)":
            prompt += "\nRéponds dans la langue utilisée par l'utilisateur dans son dernier message."
        else:
            prompt += "\nRéponds en français par défaut, sauf demande explicite d'une autre langue."

        style = str(self.settings.get("response_style", "Équilibré"))
        if style == "Concis":
            prompt += "\nPréférence de style : réponse directe et concise, sans détails superflus."
        elif style == "Détaillé":
            prompt += "\nPréférence de style : explique étape par étape, ajoute des exemples utiles et précise les limites."
        else:
            prompt += "\nPréférence de style : équilibre la clarté et le détail ; développe lorsque le sujet le nécessite."

        custom = str(self.settings.get("custom_instructions", "")).strip()
        if custom:
            prompt += "\nPréférences personnelles fournies par l'utilisateur :\n" + custom[:2000]
        return prompt

    def _startup_legal_gate(self) -> None:
        """Show the current terms/privacy notice before starting local AI services."""
        if self.settings.get("accepted_legal_notice_version") == LEGAL_NOTICE_VERSION:
            self.root.after(100, self._startup_server)
            return

        win = tk.Toplevel(self.root)
        win.title("Conditions, confidentialité et autorisations · VYNEX")
        win.configure(bg=BG)
        win.geometry("760x660")
        win.minsize(620, 520)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: self._decline_legal_notice(win))
        tk.Label(
            win, text="Avant de commencer", bg=BG, fg=TEXT,
            font=("Segoe UI", 21, "bold")
        ).pack(anchor="w", padx=22, pady=(20, 4))
        tk.Label(
            win,
            text="Lis les conditions et les accès facultatifs. Tu peux refuser et fermer VYNEX.",
            bg=BG, fg=MUTED, font=("Segoe UI", 10), wraplength=700, justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 12))
        text_frame = tk.Frame(win, bg=PANEL)
        text_frame.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        view = tk.Text(
            text_frame, wrap="word", bg=PANEL, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 10), padx=14, pady=12, relief="flat", bd=0,
            state="normal"
        )
        scroll = tk.Scrollbar(text_frame, command=view.yview, bg=PANEL, troughcolor=BG)
        view.configure(yscrollcommand=scroll.set)
        view.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        view.insert("1.0", TERMS_TEXT + "\n\n" + PRIVACY_TEXT)
        view.configure(state="disabled")
        row = tk.Frame(win, bg=BG)
        row.pack(fill="x", padx=22, pady=(0, 18))
        self._button(row, "Refuser et quitter", lambda: self._decline_legal_notice(win), compact=True).pack(side="right")

        def accept_notice():
            self.settings["accepted_legal_notice_version"] = LEGAL_NOTICE_VERSION
            self.settings["accepted_legal_notice_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
            self.settings.setdefault("permissions", {})
            write_json(SETTINGS_FILE, self.settings)
            try:
                win.grab_release()
            except tk.TclError:
                pass
            win.destroy()
            self.root.after(100, self._startup_server)

        self._button(row, "J’accepte et continuer", accept_notice, primary=True, compact=True).pack(side="right", padx=(0, 8))
        win.grab_set()
        win.focus_force()

    def _decline_legal_notice(self, win) -> None:
        try:
            win.grab_release()
        except tk.TclError:
            pass
        try:
            win.destroy()
        except tk.TclError:
            pass
        self.close()

    def _show_policy_document(self, title: str, content: str) -> None:
        """Display a read-only terms/privacy document from the app's own settings."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG)
        win.geometry("760x620")
        win.minsize(600, 480)
        win.transient(self.root)
        tk.Label(win, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(18, 10))
        frame = tk.Frame(win, bg=PANEL)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        view = tk.Text(frame, wrap="word", bg=PANEL, fg=TEXT, font=("Segoe UI", 10), padx=13, pady=12, relief="flat", bd=0)
        scroll = tk.Scrollbar(frame, command=view.yview, bg=PANEL, troughcolor=BG)
        view.configure(yscrollcommand=scroll.set)
        view.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        view.insert("1.0", content)
        view.configure(state="disabled")
        self._button(win, "Fermer", win.destroy, compact=True).pack(anchor="e", padx=20, pady=(0, 16))

    def _permission_grants(self) -> dict:
        value = self.settings.get("permissions", {})
        if not isinstance(value, dict):
            value = {}
            self.settings["permissions"] = value
        return value

    def _ensure_feature_permission(self, key: str, *, force_prompt: bool = False) -> bool:
        """Ask for explicit app-level consent before a sensitive feature is used."""
        if key not in PERMISSION_DESCRIPTIONS:
            return False
        grants = self._permission_grants()
        if grants.get(key) is True and not force_prompt:
            return True
        title = "Autorisation : " + ("microphone" if key == "microphone" else "capture d’écran")
        accepted = messagebox.askyesno(
            title,
            PERMISSION_DESCRIPTIONS[key] + "\n\nAutoriser cette fonction dans VYNEX et mémoriser ce choix ? "
            "Vous pourrez le révoquer depuis Paramètres > Données & confidentialité.",
            parent=self.root,
        )
        if accepted:
            grants[key] = True
            write_json(SETTINGS_FILE, self.settings)
        elif force_prompt:
            grants.pop(key, None)
            write_json(SETTINGS_FILE, self.settings)
        return bool(accepted)

    def _revoke_feature_permission(self, key: str) -> None:
        grants = self._permission_grants()
        grants.pop(key, None)
        write_json(SETTINGS_FILE, self.settings)
        messagebox.showinfo(
            APP_TITLE,
            "Autorisation mémorisée révoquée. VYNEX vous redemandera votre choix la prochaine fois que vous utiliserez cette fonction.",
            parent=self.root,
        )

    def _ensure_chat_endpoint_consent(self) -> bool:
        """Warn before sending prompts/context to a non-loopback chat server."""
        base_url = str(self.settings.get("chat_url", OLLAMA_URL) or OLLAMA_URL).rstrip("/")
        try:
            parsed = urlparse(base_url)
            hostname = (parsed.hostname or "").casefold()
        except ValueError:
            messagebox.showwarning(APP_TITLE, "L’adresse du serveur configuré est invalide.", parent=self.root)
            return False
        if parsed.scheme not in {"http", "https"} or not hostname:
            messagebox.showwarning(APP_TITLE, "L’adresse du serveur doit être une URL HTTP ou HTTPS valide.", parent=self.root)
            return False
        if hostname in {"localhost", "127.0.0.1", "::1"}:
            return True
        if self.settings.get("approved_remote_endpoint") == base_url:
            return True
        transport_note = "\n\nAttention : cette adresse utilise HTTP sans chiffrement." if parsed.scheme == "http" else ""
        accepted = messagebox.askyesno(
            "Confirmer l’envoi au serveur distant",
            f"Le moteur de conversation est configuré sur {hostname}, qui n’est pas l’ordinateur local. "
            "Le message, le contexte de conversation, les textes de fichiers et les descriptions d’images peuvent être transmis à ce serveur. "
            "Vérifie que tu lui fais confiance et que tu as le droit de transmettre ces informations."
            + transport_note + "\n\nAutoriser et mémoriser cet accord pour cette adresse exacte ?",
            parent=self.root,
        )
        if not accepted:
            return False
        self.settings["approved_remote_endpoint"] = base_url
        write_json(SETTINGS_FILE, self.settings)
        return True

    def _apply_chat_font_size(self, size: int) -> None:
        """Ajuste les polices de la conversation sans reconstruire l'interface."""
        size = max(10, min(16, int(size)))
        if not hasattr(self, "transcript"):
            return
        try:
            self.transcript.configure(font=("Segoe UI", size))
            self.transcript.tag_configure("user", font=("Segoe UI", max(9, size - 1), "bold"))
            self.transcript.tag_configure("assistant", font=("Segoe UI", max(9, size - 1), "bold"))
            self.transcript.tag_configure("body_user", font=("Segoe UI", size))
            self.transcript.tag_configure("body_assistant", font=("Segoe UI", size))
            self.transcript.tag_configure("muted", font=("Segoe UI", max(9, size - 1), "italic"))
            self.transcript.tag_configure("muted_user", font=("Segoe UI", max(9, size - 1), "italic"))
            self.transcript.tag_configure("muted_assistant", font=("Segoe UI", max(9, size - 1), "italic"))
            self.transcript.tag_configure("md_h1", font=("Segoe UI", size + 4, "bold"))
            self.transcript.tag_configure("md_h2", font=("Segoe UI", size + 2, "bold"))
            self.transcript.tag_configure("md_h3", font=("Segoe UI", size, "bold"))
            self.transcript.tag_configure("md_bold", font=("Segoe UI", size, "bold"))
            self.transcript.tag_configure("md_italic", font=("Segoe UI", size, "italic"))
            self.transcript.tag_configure("md_inline_code", font=("Consolas", max(9, size - 1)))
            self.transcript.tag_configure("md_code_block", font=("Consolas", max(9, size - 1)))
            self.transcript.tag_configure("md_quote", font=("Segoe UI", size, "italic"))
        except tk.TclError:
            pass

    # ---------------------------- interface ----------------------------
    def _button(self, parent, text, command, *, primary=False, compact=False, anchor="center", disabled=False):
        # Boutons homogènes : contraste élevé, contour discret et retour visuel au survol.
        bg = ACCENT if primary else PANEL
        fg = BG if primary else TEXT
        btn = tk.Button(
            parent, text=text, command=command, anchor=anchor,
            bg=bg, fg=fg, activebackground=ACCENT_HOVER if primary else PANEL_HOVER,
            activeforeground=BG if primary else TEXT, disabledforeground="#7183A0",
            font=("Segoe UI", 10 if compact else 11, "bold"),
            relief="flat", bd=0, overrelief="flat", highlightthickness=1,
            highlightbackground=ACCENT if primary else BORDER,
            highlightcolor=ACCENT_HOVER if primary else BLUE,
            padx=12 if compact else 16, pady=7 if compact else 10,
            cursor="hand2", takefocus=True,
            state="disabled" if disabled else "normal",
        )
        normal_bg = bg
        hover_bg = ACCENT_HOVER if primary else PANEL_HOVER
        normal_outline = ACCENT if primary else BORDER
        hover_outline = ACCENT_HOVER if primary else BORDER_HOVER
        btn.bind("<Enter>", lambda _e: btn.configure(bg=hover_bg, highlightbackground=hover_outline) if str(btn["state"]) != "disabled" else None)
        btn.bind("<Leave>", lambda _e: btn.configure(bg=normal_bg, highlightbackground=normal_outline) if str(btn["state"]) != "disabled" else None)
        return btn

    def _animate_vynex_ui(self):
        """Anime doucement l'orbe d'accueil et l'indicateur d'activité."""
        if not getattr(self, "_animations_enabled", False):
            self._animation_after_id = None
            return
        try:
            self._animation_phase = (self._animation_phase + 0.105) % (2 * math.pi)
            phase = self._animation_phase
            hero = getattr(self, "_hero_canvas", None)

            # L'orbe respire; trois petits points suivent des orbites décalées.
            if hero is not None and hero.winfo_exists() and getattr(self, "is_home", True):
                breath = (math.sin(phase) + 1.0) / 2.0
                outer = getattr(self, "_hero_outer_ring", None)
                inner = getattr(self, "_hero_inner_ring", None)
                halo = getattr(self, "_hero_halo", None)
                core = getattr(self, "_hero_core", None)
                symbol = getattr(self, "_hero_symbol", None)
                dot1 = getattr(self, "_hero_orbit_dot", None)
                dot2 = getattr(self, "_hero_orbit_dot2", None)
                dot3 = getattr(self, "_hero_orbit_dot3", None)
                if outer is not None:
                    rx, ry = 57 + 2.2 * breath, 38 + 1.5 * breath
                    hero.coords(outer, 70-rx, 50-ry, 70+rx, 50+ry)
                    hero.itemconfigure(outer, outline="#%02x%02x%02x" % (
                        int(28 + 15 * breath), int(67 + 50 * breath), int(86 + 45 * breath)))
                if inner is not None:
                    rx, ry = 48 + 1.4 * breath, 33 + 1.0 * breath
                    hero.coords(inner, 70-rx, 50-ry, 70+rx, 50+ry)
                if halo is not None:
                    radius = 31 + 3.0 * breath
                    hero.coords(halo, 70-radius, 50-radius*0.82, 70+radius, 50+radius*0.82)
                if core is not None:
                    radius = 24 + 1.4 * breath
                    hero.coords(core, 70-radius, 50-radius*0.86, 70+radius, 50+radius*0.86)
                if symbol is not None:
                    hero.itemconfigure(symbol, fill=ACCENT_HOVER if breath > 0.42 else ACCENT)
                if dot1 is not None:
                    x, y = 70 + 49 * math.cos(phase), 50 + 29 * math.sin(phase)
                    hero.coords(dot1, x-3.2, y-3.2, x+3.2, y+3.2)
                if dot2 is not None:
                    p = phase * -0.73 + 1.6
                    x, y = 70 + 43 * math.cos(p), 50 + 25 * math.sin(p)
                    hero.coords(dot2, x-2.2, y-2.2, x+2.2, y+2.2)
                if dot3 is not None:
                    p = phase * 0.53 + 3.2
                    x, y = 70 + 36 * math.cos(p), 50 + 20 * math.sin(p)
                    hero.coords(dot3, x-1.6, y-1.6, x+1.6, y+1.6)

            # Le texte d'état provient de status_var : le spinner ne masque pas les informations.
            status = getattr(self, "status_dot", None)
            status_var = getattr(self, "status_var", None)
            if status is not None and status_var is not None and status.winfo_exists():
                status_text = str(status_var.get())
                active_words = ("charg", "prépare", "analyse", "interromp", "vérification")
                active = bool(getattr(self, "busy", False)) or any(word in status_text.lower() for word in active_words)
                if active:
                    frames = ("◴", "◷", "◶", "◵")
                    glyph = frames[self._animation_frame % len(frames)]
                    status.configure(text=f"{glyph} {status_text}", fg=BLUE if self._animation_frame % 2 else ACCENT_HOVER)
                    self._animation_frame += 1
                else:
                    resting = f"● {status_text}"
                    if str(status.cget("text")) != resting:
                        status.configure(text=resting)

            self._animation_after_id = self.root.after(55, self._animate_vynex_ui)
        except tk.TclError:
            # Normal si la fenêtre est fermée alors qu'un rappel d'animation attend.
            self._animation_after_id = None
        except (AttributeError, TypeError, ValueError):
            # Un widget facultatif absent ne doit jamais faire planter VYNEX.
            try:
                self._animation_after_id = self.root.after(100, self._animate_vynex_ui)
            except tk.TclError:
                self._animation_after_id = None

    def _build_ui(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(shell, bg=SIDEBAR, width=258, highlightthickness=1, highlightbackground=BORDER)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        sidebar_top = tk.Frame(self.sidebar, bg=SIDEBAR)
        sidebar_top.pack(fill="x", padx=14, pady=(16, 18))
        self._vynex_logo_photo = None
        try:
            sidebar_logo_path = find_image_asset("VYNEX_icon.png")
            if sidebar_logo_path is None:
                raise FileNotFoundError("VYNEX_icon.png introuvable")
            raw_logo = tk.PhotoImage(file=str(sidebar_logo_path))
            # Le même robot sert de logo, quelle que soit la résolution du PNG source.
            logo_scale = max(1, (max(raw_logo.width(), raw_logo.height()) + 49) // 50)
            self._vynex_logo_photo = raw_logo.subsample(logo_scale, logo_scale)
            logo = tk.Label(sidebar_top, image=self._vynex_logo_photo, bg=SIDEBAR, bd=0)
            logo.pack(side="left", padx=(0, 10))
        except (tk.TclError, OSError):
            logo = tk.Canvas(sidebar_top, width=50, height=50, bg=SIDEBAR, bd=0, highlightthickness=0)
            logo.pack(side="left", padx=(0, 10))
            logo.create_polygon(*self._rounded_points(1, 1, 49, 49, 15, 10), fill="#172840", outline="#405A7A", width=1)
            logo.create_oval(8, 8, 42, 42, outline="#285164", width=1)
            logo.create_oval(12, 12, 38, 38, outline=ACCENT, width=2)
            logo.create_oval(16, 16, 34, 34, fill="#194255", outline="#348D84", width=1)
            logo.create_text(25, 24, text="✦", fill=ACCENT_HOVER, font=("Segoe UI Symbol", 16, "bold"))
            logo.create_oval(34, 33, 39, 38, fill=BLUE, outline=BLUE)
        brand = tk.Frame(sidebar_top, bg=SIDEBAR)
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(brand, text="VYNEX", bg=SIDEBAR, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(brand, text="ASSISTANT PERSONNEL LOCAL", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(1, 4))
        tk.Label(brand, text="●  LOCAL · PRIVÉ", bg=SIDEBAR, fg=ACCENT_HOVER,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")

        self._button(self.sidebar, "＋   Nouvelle discussion", self.new_chat, primary=True, anchor="w").pack(fill="x", padx=12, pady=(0, 9))
        for label, action in (
            ("⌕   Rechercher une discussion", self.search_chats),
            ("◷   Historique", self.open_history),
            ("▧   Bibliothèque d’images", self.open_library),
            ("◷   Ajouter un rappel", self.add_reminder),
            ("⚙   Paramètres", self.open_settings),
        ):
            self._button(self.sidebar, label, action, anchor="w").pack(fill="x", padx=12, pady=3)

        separator = tk.Frame(self.sidebar, bg=BORDER, height=1)
        separator.pack(fill="x", padx=14, pady=(18, 12))
        tk.Label(self.sidebar, text="DISCUSSIONS RÉCENTES", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(0, 8))
        self.recent_list = tk.Listbox(
            self.sidebar, bg=SIDEBAR, fg="#D9E5F7", selectbackground="#1A5A4B",
            selectforeground="#FFFFFF", relief="flat", bd=0, highlightthickness=0,
            activestyle="none", font=("Segoe UI", 10), height=8,
        )
        self.recent_list.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.recent_list.bind("<Double-Button-1>", self._open_recent_selection)
        self.recent_list.bind("<Button-3>", self._recent_context_menu)
        self.recent_list.bind("<Button-2>", self._recent_context_menu)
        self.recent_list.bind("<Control-Button-1>", self._recent_context_menu)
        self.recent_list.bind("<Delete>", self._delete_selected_recent_chat)
        tk.Label(self.sidebar, textvariable=self.status_var, bg=SIDEBAR, fg=MUTED,
                 wraplength=200, justify="left", font=("Segoe UI", 9)).pack(fill="x", padx=16, pady=(0, 15))

        self.content = tk.Frame(shell, bg=BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(1, weight=1)
        self.content.columnconfigure(0, weight=1)

        # Barre de commande : navigation stylée, identité, état du moteur et accès au studio visuel.
        topbar = tk.Frame(self.content, bg=BG, height=82)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)

        menu_canvas = tk.Canvas(
            topbar, width=52, height=44, bg=BG, bd=0, highlightthickness=0, cursor="hand2"
        )
        menu_canvas.pack(side="left", padx=(18, 13), pady=(10, 12))
        def draw_navigation_icon(hover=False):
            menu_canvas.delete("all")
            bg = PANEL_HOVER if hover else PANEL
            outline = BORDER_HOVER if hover else BORDER
            menu_canvas.create_polygon(*self._rounded_points(1, 1, 51, 43, 10, 7), fill=bg, outline=outline, width=1)
            # Icône de panneau latéral + chevron : plus distinctive que trois traits génériques.
            menu_canvas.create_polygon(*self._rounded_points(8, 9, 25, 35, 4, 5), fill="#1A3850", outline="#37647B", width=1)
            menu_canvas.create_line(13, 15, 20, 15, fill=ACCENT_HOVER, width=2, capstyle=tk.ROUND)
            menu_canvas.create_line(13, 21, 20, 21, fill=ACCENT_HOVER, width=2, capstyle=tk.ROUND)
            menu_canvas.create_line(13, 27, 18, 27, fill=ACCENT_HOVER, width=2, capstyle=tk.ROUND)
            menu_canvas.create_line(31, 17, 36, 22, 31, 27, fill=BLUE, width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        draw_navigation_icon()
        menu_canvas.bind("<Button-1>", lambda _event: self.toggle_sidebar())
        menu_canvas.bind("<Enter>", lambda _event: draw_navigation_icon(True))
        menu_canvas.bind("<Leave>", lambda _event: draw_navigation_icon(False))
        menu_canvas.bind("<FocusIn>", lambda _event: draw_navigation_icon(True))
        menu_canvas.bind("<FocusOut>", lambda _event: draw_navigation_icon(False))

        brand = tk.Frame(topbar, bg=BG)
        brand.pack(side="left", fill="y", pady=(11, 8))
        title_row = tk.Frame(brand, bg=BG)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="VYNEX", bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(side="left")
        tk.Label(title_row, text="  /  ESPACE INTELLIGENT", bg=BG, fg="#8CA4C4",
                 font=("Segoe UI", 10, "bold")).pack(side="left", pady=(3, 0))
        tk.Label(brand, text="CONVERSATION  ·  VISION  ·  ASSISTANCE LOCALE", bg=BG, fg="#6E88A8",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(3, 0))

        header_actions = tk.Frame(topbar, bg=BG)
        header_actions.pack(side="right", padx=(8, 18), pady=(13, 14))
        self.status_dot = tk.Label(header_actions, text="● Vérification…", bg="#102335", fg=WARNING,
                                   font=("Segoe UI", 9, "bold"), padx=10, pady=7)
        self.status_dot.pack(side="right", padx=(8, 0))
        self._button(header_actions, "Tester le moteur", self.test_server, compact=True).pack(side="right", padx=(6, 0))
        self._button(header_actions, "✧  Studio visuel", self.open_image_studio, compact=True).pack(side="right", padx=(0, 6))

        rule = tk.Canvas(topbar, height=2, bg=BG, bd=0, highlightthickness=0)
        rule.pack(side="bottom", fill="x")
        def draw_header_rule(event=None):
            rule.delete("all")
            rw = max(1, rule.winfo_width())
            accent_width = min(rw, max(112, int(rw * 0.22)))
            rule.create_rectangle(0, 0, accent_width, 2, fill=ACCENT, outline="")
            rule.create_rectangle(accent_width, 0, rw, 2, fill=BORDER, outline="")
        rule.bind("<Configure>", draw_header_rule)

        self.main_area = tk.Frame(self.content, bg=BG)
        self.main_area.grid(row=1, column=0, sticky="nsew")
        self.main_area.rowconfigure(0, weight=1)
        self.main_area.columnconfigure(0, weight=1)

        self.home_view = tk.Frame(self.main_area, bg=BG)
        self.home_view.grid(row=0, column=0, sticky="nsew")
        self.home_view.rowconfigure(0, weight=1)
        self.home_view.columnconfigure(0, weight=1)

        self.home_center = tk.Frame(self.home_view, bg=BG)
        self.home_center.place(relx=0.5, rely=0.49, anchor="center", relwidth=0.95)

        # Sphère statique dessinée au Canvas : identité distinctive sans image lourde ni boucle d'animation.
        # Orbe VYNEX : halo doux, noyau lumineux et satellites orbitaux.
        # Tout est dessiné avec Canvas : aucun fichier image ni paquet à installer.
        hero = tk.Canvas(self.home_center, width=140, height=100, bg=BG,
                         bd=0, highlightthickness=0, relief="flat")
        hero.pack(pady=(0, 3))
        self._hero_canvas = hero
        self._hero_outer_ring = hero.create_oval(13, 12, 127, 88, outline="#21465B", width=1)
        self._hero_inner_ring = hero.create_oval(22, 17, 118, 83, outline="#286C76", width=1)
        self._hero_halo = hero.create_oval(38, 22, 102, 78, fill="#0D2134", outline="#24566A", width=1)
        self._hero_core = hero.create_oval(44, 27, 96, 73, fill="#1C4A5B", outline=ACCENT, width=2)
        self._hero_symbol = hero.create_text(70, 50, text="✦", fill=ACCENT_HOVER,
                                             font=("Segoe UI Symbol", 23, "bold"))
        self._hero_orbit_dot = hero.create_oval(109, 46, 115, 52, fill=BLUE, outline=BLUE)
        self._hero_orbit_dot2 = hero.create_oval(0, 0, 4, 4, fill=ACCENT_HOVER, outline=ACCENT_HOVER)
        self._hero_orbit_dot3 = hero.create_oval(0, 0, 3, 3, fill=PURPLE, outline=PURPLE)
        hero.create_oval(30, 21, 34, 25, fill="#3A6E83", outline="")
        hero.create_oval(105, 72, 109, 76, fill="#3A6E83", outline="")
        badge = tk.Frame(self.home_center, bg="#13283B", highlightthickness=1, highlightbackground="#2C667C")
        tk.Label(badge, text="✦   IA LOCALE   ·   CONFIDENTIELLE   ·   LÉGÈRE", bg="#13283B", fg=ACCENT_HOVER,
                 font=("Segoe UI", 9, "bold"), padx=13, pady=6).pack()
        badge.pack(pady=(0, 14))
        tk.Label(self.home_center, text="Ton assistant.\nTes idées, sans limites.", bg=BG, fg=TEXT,
                 font=("Segoe UI", 25, "bold"), justify="center").pack(pady=(0, 8))
        tk.Label(self.home_center, text="Écris, programme, analyse une image ou démarre une conversation vocale.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 11), wraplength=690).pack(pady=(0, 15))

        feature_row = tk.Frame(self.home_center, bg=BG)
        feature_row.pack(pady=(0, 14))
        for label, color in (("◈  CODE", BLUE), ("▧  VISION", PURPLE), ("♫  VOCAL", ACCENT_HOVER), ("⌘  LOCAL", "#B7C8E0")):
            chip = tk.Frame(feature_row, bg="#111E32", highlightthickness=1, highlightbackground=BORDER)
            tk.Label(chip, text=label, bg="#111E32", fg=color, font=("Segoe UI", 9, "bold"), padx=10, pady=5).pack()
            chip.pack(side="left", padx=4)

        # Cartes d'action : remplissent l'accueil et donnent un accès immédiat aux tâches principales.
        workspace_cards = tk.Frame(self.home_center, bg=BG)
        workspace_cards.pack(fill="x", padx=18, pady=(0, 12))
        for card_column in range(4):
            workspace_cards.columnconfigure(card_column, weight=1, uniform="workspace")
        workspace_actions = [
            ("✎", "Écriture", "Rédiger, corriger, résumer", BLUE,
             lambda: self.quick_prompt("Aide-moi à rédiger ou améliorer ce contenu de façon claire et professionnelle : ")),
            ("⌘", "Code & technique", "Comprendre et déboguer", ACCENT_HOVER,
             lambda: self.quick_prompt("Aide-moi à comprendre ou corriger ce code, étape par étape : ")),
            ("◈", "Vision", "Analyser une image jointe", PURPLE,
             lambda: (self.quick_prompt("Analyse l’image que je vais joindre. Décris ce qui est réellement visible et les détails importants."), self.attach_images())),
            ("✧", "Studio visuel", "Créer une image par IA", "#F4C77B", self.open_image_studio),
        ]
        for column, (symbol, title, detail, tint, action) in enumerate(workspace_actions):
            card = tk.Frame(workspace_cards, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, cursor="hand2")
            card.grid(row=0, column=column, sticky="nsew", padx=4, pady=2)
            head = tk.Frame(card, bg=PANEL)
            head.pack(fill="x", padx=11, pady=(9, 3))
            tk.Label(head, text=symbol, bg=PANEL, fg=tint, font=("Segoe UI Symbol", 15, "bold")).pack(side="left")
            tk.Label(head, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(7, 0))
            tk.Label(card, text=detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 8),
                     anchor="w", justify="left", wraplength=185).pack(fill="x", padx=12, pady=(0, 10))
            def bind_card_hover(widget, is_hover, widgets=(card, head)):
                color = PANEL_HOVER if is_hover else PANEL
                border = BORDER_HOVER if is_hover else BORDER
                try:
                    widgets[0].configure(bg=color, highlightbackground=border)
                    widgets[1].configure(bg=color)
                    for child in widgets[1].winfo_children():
                        child.configure(bg=color)
                    for child in widgets[0].winfo_children():
                        if child is not widgets[1]:
                            child.configure(bg=color)
                except tk.TclError:
                    pass
            for widget in (card, *card.winfo_children(), *head.winfo_children()):
                widget.bind("<Button-1>", lambda _event, callback=action: callback(), add="+")
                widget.bind("<Enter>", lambda _event, target=card, header=head: bind_card_hover(target, True, (target, header)), add="+")
                widget.bind("<Leave>", lambda _event, target=card, header=head: bind_card_hover(target, False, (target, header)), add="+")

        self.home_composer = self._create_composer(self.home_center, home=True)
        self.home_composer["frame"].pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(self.home_center, text="ENTRÉE POUR ENVOYER     ·     MAJ + ENTRÉE POUR UNE NOUVELLE LIGNE",
                 bg=BG, fg="#7890B0", font=("Segoe UI", 8, "bold")).pack(pady=(0, 7))
        self._make_suggestions(self.home_center).pack(pady=(0, 2))


        # Ecran de bienvenue superpose a l'ancienne page.
        self._welcome_splash = tk.Frame(self.home_view, bg=BG)
        self._welcome_splash.place(
            relx=0, rely=0, relwidth=1, relheight=1
        )
        self._welcome_splash.lift()

        welcome_center = tk.Frame(self._welcome_splash, bg=BG)
        welcome_center.place(relx=0.5, rely=0.49, anchor="center")

        self._welcome_robot_photo = None
        self._welcome_robot_canvas = None
        self._welcome_robot_image_id = None

        robot_canvas = tk.Canvas(
            welcome_center, width=200, height=200, bg=BG,
            bd=0, highlightthickness=0, relief="flat"
        )
        robot_canvas.pack(pady=(0, 18))
        self._welcome_robot_canvas = robot_canvas

        # L'image est recherchée dans les ressources embarquées, près de l'application et dans le runtime.
        # Elle sera aussi intégrée au paquet PyInstaller avec --add-data.
        robot_image_path = find_image_asset("VYNEX_splash.png")
        if robot_image_path is None:
            robot_image_path = find_image_asset("VYNEX_icon.png")
        if robot_image_path is not None:
            try:
                logo = tk.PhotoImage(file=str(robot_image_path))
                facteur = max(1, (max(logo.width(), logo.height()) + 199) // 200)
                self._welcome_robot_photo = logo.subsample(facteur, facteur)
                self._welcome_robot_image_id = robot_canvas.create_image(
                    100, 100, image=self._welcome_robot_photo, anchor="center"
                )

                # Petit mouvement vertical, sans dessin superposé sur le visage.
                def animer_sourire(etape=0):
                    canvas = self._welcome_robot_canvas
                    splash = self._welcome_splash
                    if not splash.winfo_exists() or not canvas.winfo_exists():
                        return
                    decalages = [0, -1, -2, -1, 0, 1, 2, 1]
                    y = 100 + decalages[etape % len(decalages)]
                    if self._welcome_robot_image_id is not None:
                        canvas.coords(self._welcome_robot_image_id, 100, y)
                    canvas.after(120, lambda: animer_sourire(etape + 1))

                animer_sourire()
            except (tk.TclError, OSError):
                self._welcome_robot_photo = None
                self._welcome_robot_image_id = None

        if self._welcome_robot_image_id is None:
            # Robot vectoriel de secours, centré sur le même canvas de 200 px.
            c = robot_canvas
            c.create_oval(15, 12, 185, 181, outline="#21465B", width=2)
            c.create_oval(25, 22, 175, 171, outline="#286C76", width=1)
            c.create_line(100, 34, 100, 20, fill=ACCENT, width=3)
            c.create_oval(92, 11, 108, 27, fill=ACCENT, outline=ACCENT)
            c.create_oval(35, 62, 53, 107, fill="#183A55", outline="#4A7899", width=2)
            c.create_oval(147, 62, 165, 107, fill="#183A55", outline="#4A7899", width=2)
            c.create_polygon(*self._rounded_points(41, 43, 159, 140, 23),
                              fill="#18334D", outline="#6BADC8", width=2)
            c.create_polygon(*self._rounded_points(50, 52, 150, 132, 18),
                              fill="#10253B", outline="#2F667E", width=1)
            c.create_oval(62, 74, 84, 96, fill=ACCENT_HOVER, outline=ACCENT)
            c.create_oval(116, 74, 138, 96, fill=ACCENT_HOVER, outline=ACCENT)
            c.create_oval(70, 81, 77, 88, fill="#FFFFFF", outline="")
            c.create_oval(123, 81, 130, 88, fill="#FFFFFF", outline="")
            c.create_arc(77, 92, 123, 119, start=205, extent=130,
                         style="arc", outline=BLUE, width=3)
            c.create_oval(95, 116, 105, 126, fill=ACCENT, outline=ACCENT)

        tk.Label(
            welcome_center,
            text="Bienvenue sur VYNEX",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 25, "bold")
        ).pack()

        # Apres 5 secondes, seule la page d'accueil classique reste visible.
        self._welcome_splash.after(
            5000,
            lambda: self._welcome_splash.destroy()
            if self._welcome_splash.winfo_exists() else None
        )

        self.chat_view = tk.Frame(self.main_area, bg=BG)
        self.chat_view.grid(row=0, column=0, sticky="nsew")
        self.chat_view.rowconfigure(0, weight=1)
        self.chat_view.columnconfigure(0, weight=1)
        transcript_wrap = tk.Frame(self.chat_view, bg=CHAT_PANEL, highlightthickness=1, highlightbackground=BORDER)
        transcript_wrap.grid(row=0, column=0, sticky="nsew", padx=20, pady=(16, 12))
        transcript_wrap.rowconfigure(0, weight=1)
        transcript_wrap.columnconfigure(0, weight=1)
        self.transcript = tk.Text(
            transcript_wrap, wrap="word", bg=CHAT_PANEL, fg=TEXT, relief="flat", bd=0,
            font=("Segoe UI", 12), padx=18, pady=16, insertbackground=TEXT,
            selectbackground="#1A5A4B", selectforeground=TEXT,
            highlightthickness=0, spacing1=4, spacing3=10, state="disabled",
        )
        sb = tk.Scrollbar(transcript_wrap, command=self.transcript.yview, relief="flat", bd=0,
                          bg=PANEL, troughcolor=CHAT_PANEL, activebackground=BORDER_HOVER)
        self.transcript.configure(yscrollcommand=sb.set)
        self.transcript.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        # Alignement façon messagerie : utilisateur à droite, VYNEX à gauche.
        # Des marges internes gardent les messages lisibles sur les fenêtres étroites.
        self.transcript.tag_configure(
            "user", foreground=BLUE, font=("Segoe UI", 11, "bold"),
            spacing1=22, spacing3=3, justify="right", rmargin=12,
        )
        self.transcript.tag_configure(
            "assistant", foreground=ACCENT_HOVER, font=("Segoe UI", 11, "bold"),
            spacing1=20, spacing3=3, justify="left", lmargin1=10, lmargin2=10,
        )
        self.transcript.tag_configure(
            "body_user", foreground=TEXT, font=("Segoe UI", 11), justify="right",
            lmargin1=54, lmargin2=54, rmargin=14, spacing1=3, spacing3=10,
        )
        self.transcript.tag_configure(
            "body_assistant", foreground=TEXT, font=("Segoe UI", 11), justify="left",
            lmargin1=12, lmargin2=12, rmargin=54, spacing1=3, spacing3=10,
        )
        self.transcript.tag_configure(
            "muted", foreground=MUTED, font=("Segoe UI", 10, "italic"),
            lmargin1=10, lmargin2=10,
        )
        self.transcript.tag_configure(
            "muted_user", foreground=MUTED, font=("Segoe UI", 10, "italic"),
            justify="right", lmargin1=54, lmargin2=54, rmargin=12,
        )
        self.transcript.tag_configure(
            "muted_assistant", foreground=MUTED, font=("Segoe UI", 10, "italic"),
            justify="left", lmargin1=10, lmargin2=10, rmargin=54,
        )
        # Mise en forme native des réponses : titres, listes, citations et blocs de code.
        # Ces tags restent légers et n'ajoutent aucune dépendance externe.
        self.transcript.tag_configure("md_h1", foreground=ACCENT_HOVER,
                                      font=("Segoe UI", 16, "bold"), spacing1=10, spacing3=5)
        self.transcript.tag_configure("md_h2", foreground=BLUE,
                                      font=("Segoe UI", 14, "bold"), spacing1=8, spacing3=4)
        self.transcript.tag_configure("md_h3", foreground=PURPLE,
                                      font=("Segoe UI", 12, "bold"), spacing1=6, spacing3=3)
        self.transcript.tag_configure("md_bold", font=("Segoe UI", 11, "bold"))
        self.transcript.tag_configure("md_italic", font=("Segoe UI", 11, "italic"))
        self.transcript.tag_configure("md_inline_code", foreground=ACCENT_HOVER,
                                      background="#172B42", font=("Consolas", 10))
        self.transcript.tag_configure("md_code_block", foreground="#E1ECFA",
                                      background="#101D31", font=("Consolas", 10),
                                      lmargin1=20, lmargin2=20, rmargin=20, spacing1=1, spacing3=1)
        self.transcript.tag_configure("md_language", foreground=BLUE,
                                      font=("Segoe UI", 9, "bold"), spacing1=5, spacing3=2)
        self.transcript.tag_configure("md_quote", foreground="#B9CADF",
                                      background="#101D31", font=("Segoe UI", 11, "italic"),
                                      lmargin1=22, lmargin2=22, rmargin=24)
        self.transcript.tag_configure("md_list_marker", foreground=ACCENT_HOVER,
                                      font=("Segoe UI", 11, "bold"))
        self.transcript.tag_configure("md_rule", foreground=BORDER)
        self.chat_composer = self._create_composer(self.chat_view, home=False)
        self.chat_composer["frame"].grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        footer = tk.Frame(self.content, bg=BG)
        footer.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        footer_line = tk.Frame(footer, bg=BG)
        footer_line.pack(anchor="center")
        tk.Label(footer_line, text="●", bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(footer_line, text="LOCAL PAR DÉFAUT   ·   TES CONVERSATIONS RESTENT SUR CET APPAREIL",
                 bg=BG, fg="#8397B5", font=("Segoe UI", 8, "bold")).pack(side="left")
        self.show_home()
        self._refresh_recent_list()

    def _make_suggestions(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        rows = (tk.Frame(wrap, bg=BG), tk.Frame(wrap, bg=BG))
        rows[0].pack(anchor="center", pady=(0, 2))
        rows[1].pack(anchor="center", pady=(2, 0))
        suggestions = [
            ("≡  Résumer un texte", "Aide-moi à résumer ce texte : "),
            ("{ }  Écrire du code", "Aide-moi à écrire ou corriger ce code : "),
            ("▧  Analyser une photo", "Analyse la photo que je vais joindre et explique ce qu’on y voit."),
            ("✧  Expliquer un concept", "Explique-moi simplement ce concept : "),
            ("⌘  Aide Windows", "Aide-moi à comprendre ou résoudre ce problème sur Windows : "),
        ]
        for index, (label, prompt) in enumerate(suggestions):
            row = rows[0] if index < 3 else rows[1]
            self._button(row, label, lambda p=prompt: self.quick_prompt(p), compact=True).pack(side="left", padx=3, pady=3)
        return wrap

    @staticmethod
    def _rounded_points(x1, y1, x2, y2, radius, steps=8):
        radius = max(2, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        corners = [
            (x2 - radius, y1 + radius, -90, 0),
            (x2 - radius, y2 - radius, 0, 90),
            (x1 + radius, y2 - radius, 90, 180),
            (x1 + radius, y1 + radius, 180, 270),
        ]
        points = []
        for cx, cy, a1, a2 in corners:
            for i in range(steps + 1):
                angle = math.radians(a1 + (a2 - a1) * i / steps)
                points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return points

    def _composer_text(self, composer):
        if composer.get("placeholder_active"):
            return ""
        return composer["input"].get("1.0", "end-1c").strip()

    def _set_composer_placeholder(self, composer):
        widget = composer["input"]
        widget.delete("1.0", "end")
        widget.insert("1.0", composer["placeholder"])
        widget.configure(fg=MUTED)
        composer["placeholder_active"] = True
        self._refresh_composer_primary_state(composer["home"])

    def _clear_composer_placeholder(self, composer):
        if composer.get("placeholder_active"):
            widget = composer["input"]
            widget.delete("1.0", "end")
            widget.configure(fg=TEXT)
            composer["placeholder_active"] = False

    def _draw_analyser(self, composer):
        """Redessine le bouton d'analyse selon sa largeur réelle, sans changer la géométrie."""
        canvas = composer["analyser"]
        canvas.delete("all")
        width = int(composer.get("analyser_width", 144))
        height = 42
        compact = width < 120
        active = bool(self.deep_mode)
        hover = bool(composer.get("analyser_hover", False))
        fill = "#1A3E5C" if active else (PANEL_HOVER if hover else PANEL)
        outline = BLUE if active else (BORDER_HOVER if hover else BORDER)
        text_color = "#E0F0FF" if active else "#D5E2F4"
        points = self._rounded_points(1, 1, width - 2, height - 2, height / 2, 7)
        canvas.create_polygon(*points, fill=fill, outline=outline, width=1)
        icon_x = 17 if compact else 27
        text_x = 58 if compact else 88
        canvas.create_text(icon_x, height / 2, text="✧", fill=BLUE if active else "#9FBDE3",
                           font=("Segoe UI Symbol", 14 if compact else 16, "bold"))
        canvas.create_text(text_x, height / 2, text="Analyser", fill=text_color,
                           font=("Segoe UI", 10 if compact else 11, "bold" if active else "normal"))

    def _draw_primary_action(self, composer):
        """Bouton rond compact et stable : flèche d’envoi ou onde vocale."""
        canvas = composer["send"]
        canvas.delete("all")
        has_content = bool(self._composer_text(composer) or self.pending_images or self.pending_files)
        in_voice = bool(self.voice_session_active and not has_content)
        hover = bool(composer.get("primary_hover"))
        ring = ACCENT_HOVER if hover or in_voice else (BLUE if not has_content else ACCENT)
        try:
            size = min(int(canvas.cget("width")), int(canvas.cget("height")))
        except (TypeError, ValueError, tk.TclError):
            size = 48
        scale = size / 54.0
        def q(value):
            return value * scale
        fill = ACCENT if has_content else ("#17494A" if in_voice else PANEL_HOVER)
        icon_colour = BG if has_content else (ACCENT_HOVER if in_voice else BLUE)
        canvas.create_oval(q(1), q(1), q(53), q(53), fill="#123442", outline="#2A6370", width=1)
        canvas.create_oval(q(3), q(3), q(51), q(51), fill=fill, outline=ring, width=2)
        if has_content:
            canvas.create_line(q(27), q(38), q(27), q(16), fill=BG, width=2.8, capstyle=tk.ROUND)
            canvas.create_line(q(18), q(25), q(27), q(16), fill=BG, width=2.8, capstyle=tk.ROUND)
            canvas.create_line(q(36), q(25), q(27), q(16), fill=BG, width=2.8, capstyle=tk.ROUND)
        else:
            heights = [10, 18, 27, 17, 11]
            xs = [15, 21, 27, 33, 39]
            for x, height in zip(xs, heights):
                canvas.create_line(q(x), q(27 - height / 2), q(x), q(27 + height / 2),
                                  fill=icon_colour, width=2.5, capstyle=tk.ROUND)
        composer["has_content_for_action"] = has_content

    def _refresh_composer_primary_state(self, home=None):
        for composer in (getattr(self, "home_composer", None), getattr(self, "chat_composer", None)):
            if not composer:
                continue
            if home is not None and composer["home"] != home:
                continue
            self._draw_primary_action(composer)

    def _refresh_analyser_buttons(self):
        for composer in (getattr(self, "home_composer", None), getattr(self, "chat_composer", None)):
            if composer:
                self._draw_analyser(composer)

    def toggle_analysis_mode(self):
        if self.busy:
            return
        self.deep_mode = not self.deep_mode
        self.settings["deep_mode"] = self.deep_mode
        write_json(SETTINGS_FILE, self.settings)
        self._refresh_analyser_buttons()
        if self.deep_mode:
            self.status_var.set("Mode Analyser actif · réponse plus approfondie et structurée")
        else:
            self.status_var.set("Mode Analyser désactivé · réponses standard")

    def _composer_primary_action(self, home):
        if self.busy:
            return
        composer = self.home_composer if home else self.chat_composer
        if self._composer_text(composer) or self.pending_images or self.pending_files:
            self.send_message(home=home)
        else:
            self.toggle_voice_conversation()

    def _create_composer(self, parent, home: bool):
        # A single wide composer inspired by the reference: +, message, Analyse,
        # microphone, then a round voice/send control at the far right.
        frame = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        previews = tk.Frame(frame, bg=BG)
        previews.pack(fill="x", padx=12, pady=(0, 5))
        previews.pack_forget()

        # Hauteur fixe : la barre ne saute pas vers le haut ou le bas quand on ajoute des lignes.
        bar = tk.Canvas(frame, height=72, bg=BG, bd=0, highlightthickness=0, relief="flat")
        bar.pack(fill="x", expand=True)

        plus = tk.Button(
            bar, text="+", command=lambda h=home: self.open_plus_menu(h),
            bg=PANEL, fg=ACCENT_HOVER, activebackground=PANEL_HOVER, activeforeground=ACCENT_HOVER,
            relief="flat", bd=0, highlightthickness=0, cursor="hand2",
            font=("Segoe UI", 23, "normal"), padx=0, pady=0,
        )
        input_text = tk.Text(
            bar, height=2, wrap="word", bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, font=("Segoe UI", 12), padx=3, pady=3,
            highlightthickness=0, undo=True,
        )
        analyser = tk.Canvas(bar, width=144, height=42, bg=PANEL, bd=0, highlightthickness=0, cursor="hand2")
        mic = tk.Button(
            bar, text="🎙", command=self.start_voice_chat,
            bg=PANEL, fg=BLUE, activebackground=PANEL_HOVER, activeforeground=ACCENT_HOVER,
            relief="flat", bd=0, highlightthickness=0, cursor="hand2",
            font=("Segoe UI Symbol", 16), padx=0, pady=0,
        )
        mic.bind("<Enter>", lambda _e: mic.configure(bg=PANEL_HOVER), add="+")
        mic.bind("<Leave>", lambda _e: mic.configure(bg=PANEL), add="+")
        send = tk.Canvas(bar, width=50, height=50, bg=PANEL, highlightthickness=0,
                         bd=0, cursor="hand2")

        plus_win = bar.create_window(38, 36, window=plus, width=44, height=44, anchor="center")
        input_win = bar.create_window(70, 36, window=input_text, width=220, height=52, anchor="w")
        analyser_win = bar.create_window(0, 36, window=analyser, width=144, height=42, anchor="center")
        mic_win = bar.create_window(0, 36, window=mic, width=40, height=42, anchor="center")
        send_win = bar.create_window(0, 36, window=send, width=50, height=50, anchor="center")

        voice_text = tk.StringVar(value="Réponse vocale : ON" if self.voice_output else "Réponse vocale : OFF")
        # These controls remain available to Settings/compatibility code; the visual bar stays uncluttered.
        voice_btn = self._button(frame, voice_text.get(), self.toggle_voice_output, compact=True)
        voice_read = self._button(frame, "Lire la réponse", self.read_last_answer, compact=True)
        voice_stop = self._button(frame, "Arrêter la voix", self.stop_voice, compact=True)
        stop_reply = self._button(frame, "Arrêter la réponse", self.stop_generation, compact=True, disabled=True)

        # Barre d'outils rapides : icônes dédiées, commandes réelles et infobulles.
        # Elle reste séparée de la zone de saisie afin de conserver sa hauteur fixe.
        tools = tk.Frame(frame, bg=BG)
        tools.pack(fill="x", padx=15, pady=(3, 0))
        tools_inner = tk.Frame(tools, bg=BG)
        tools_inner.pack(anchor="w")
        tk.Label(tools_inner, text="OUTILS", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 7))

        tool_actions = [
            ("▧", "Joindre une image", self.attach_images, ACCENT_HOVER),
            ("⌁", "Joindre un fichier texte ou code", self.attach_files, BLUE),
            ("▣", "Capturer l’écran", self.capture_screenshot, PURPLE),
            ("</>", "Ouvrir le Mode Développeur", self.open_developer_tools, BLUE),
            ("◇", "Ajouter au projet actif", self.add_to_project, PURPLE),
            ("✧", "Ouvrir le Studio visuel de création d’images", self.open_image_studio, "#F4C77B"),
            ("✦", "Ouvrir les Skills et modèles de consigne", self.open_skills, ACCENT_HOVER),
            ("◉", "Démarrer ou arrêter la discussion vocale continue", self.toggle_voice_conversation, ACCENT),
            ("♫", "Lire la dernière réponse à voix haute", self.read_last_answer, BLUE),
            ("▤", "Copier la dernière réponse", self.copy_last_answer, ACCENT_HOVER),
            ("■", "Arrêter la voix", self.stop_voice, ERROR),
            ("⏹", "Arrêter la génération en cours", self.stop_generation, ERROR),
            ("⚙", "Ouvrir les paramètres de VYNEX", self.open_settings, MUTED),
            ("⌘", "Ouvrir les connecteurs", self.open_connectors, PURPLE),
        ]
        composer_tool_buttons = []
        for glyph, description, callback, icon_color in tool_actions:
            button = tk.Button(
                tools_inner, text=glyph, command=callback, width=3, height=1,
                bg=PANEL, fg=icon_color, activebackground=PANEL_HOVER,
                activeforeground=ACCENT_HOVER, relief="flat", bd=0,
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=ACCENT, cursor="hand2",
                font=("Segoe UI Symbol", 12, "bold"), padx=1, pady=1,
            )
            button.pack(side="left", padx=2, pady=1)
            base_color = icon_color
            button.bind("<Enter>", lambda _e, b=button: b.configure(bg=PANEL_HOVER, highlightbackground=BORDER_HOVER))
            button.bind("<Leave>", lambda _e, b=button: b.configure(bg=PANEL, highlightbackground=BORDER))
            tip_state = {"window": None, "after": None}

            def show_tooltip(widget=button, text=description, state=tip_state):
                state["after"] = None
                try:
                    if not widget.winfo_exists():
                        return
                    tip = tk.Toplevel(self.root)
                    tip_state_local = state
                    tip.overrideredirect(True)
                    tip.configure(bg=BORDER)
                    label = tk.Label(
                        tip, text=text, bg=PANEL, fg=TEXT, padx=9, pady=5,
                        font=("Segoe UI", 9), relief="flat", bd=0,
                    )
                    label.pack(padx=1, pady=1)
                    tip.update_idletasks()
                    x = widget.winfo_rootx() + (widget.winfo_width() - tip.winfo_reqwidth()) // 2
                    y = widget.winfo_rooty() - tip.winfo_reqheight() - 7
                    x = max(6, min(x, self.root.winfo_screenwidth() - tip.winfo_reqwidth() - 6))
                    tip.geometry(f"+{x}+{max(6, y)}")
                    state["window"] = tip
                except tk.TclError:
                    pass

            def schedule_tooltip(_event, state=tip_state, callback=show_tooltip):
                if state["window"] is not None:
                    try:
                        state["window"].destroy()
                    except tk.TclError:
                        pass
                    state["window"] = None
                if state["after"] is not None:
                    try:
                        self.root.after_cancel(state["after"])
                    except tk.TclError:
                        pass
                state["after"] = self.root.after(500, callback)

            def hide_tooltip(_event, state=tip_state):
                if state["after"] is not None:
                    try:
                        self.root.after_cancel(state["after"])
                    except tk.TclError:
                        pass
                    state["after"] = None
                if state["window"] is not None:
                    try:
                        state["window"].destroy()
                    except tk.TclError:
                        pass
                    state["window"] = None

            button.bind("<Enter>", schedule_tooltip, add="+")
            button.bind("<Leave>", hide_tooltip, add="+")
            composer_tool_buttons.append(button)

        status = tk.Label(frame, textvariable=self.voice_status_var, bg=BG, fg=MUTED,
                          font=("Segoe UI", 9), anchor="e")
        status.pack(fill="x", padx=16, pady=(2, 0))

        composer = {
            "frame": frame, "previews": previews, "input": input_text, "plus": plus,
            "analyser": analyser, "mic": mic, "send": send, "voice_btn": voice_btn,
            "voice_text": voice_text, "voice_read": voice_read, "voice_stop": voice_stop,
            "stop_reply": stop_reply, "status": status, "tools": tools,
            "tool_buttons": composer_tool_buttons, "home": home,
            "placeholder": "Demander à VYNEX…", "placeholder_active": True,
            "analyser_hover": False, "primary_hover": False, "analyser_width": 144,
            "bar": bar, "windows": (plus_win, input_win, analyser_win, mic_win, send_win),
        }
        input_text.insert("1.0", composer["placeholder"])
        input_text.configure(fg=MUTED)

        bar_background = None
        bar_glow = None

        def draw_bar(event=None):
            nonlocal bar_background, bar_glow
            w = max(300, int(bar.winfo_width()))
            h = 72
            outer_points = self._rounded_points(1, 1, w - 2, h - 2, h / 2, 12)
            inner_points = self._rounded_points(3, 3, w - 4, h - 4, h / 2 - 2, 12)
            # Deux couches statiques créent un contour premium sans animation ni changement de hauteur.
            if bar_glow is None:
                bar_glow = bar.create_polygon(*outer_points, fill="#1A4255", outline="#2E7B86", width=1)
                bar_background = bar.create_polygon(*inner_points, fill=PANEL, outline=BORDER, width=1)
                bar.tag_lower(bar_background)
                bar.tag_lower(bar_glow)
            else:
                bar.coords(bar_glow, *outer_points)
                bar.coords(bar_background, *inner_points)

            # Disposition adaptative : conserve des espaces entre les controles.
            compact = w < 600
            plus_x = 29 if compact else 38
            plus_width = 36 if compact else 44
            input_x = 52 if compact else 70
            send_size = 44 if compact else 50
            send_x = w - send_size / 2 - 12
            mic_width = 32 if compact else 40
            mic_x = send_x - send_size / 2 - mic_width / 2 - 8
            analyser_width = 96 if compact else 144
            analyser_x = mic_x - mic_width / 2 - analyser_width / 2 - 8

            # Evite que le champ de saisie empiète sur les boutons.
            input_right = analyser_x - analyser_width / 2 - 8
            input_width = max(24, int(input_right - input_x))

            bar.coords(plus_win, plus_x, h / 2)
            bar.itemconfigure(plus_win, width=plus_width, height=44)
            bar.coords(input_win, input_x, h / 2)
            bar.itemconfigure(input_win, width=input_width, height=52)
            bar.coords(analyser_win, analyser_x, h / 2)
            bar.itemconfigure(analyser_win, width=analyser_width, height=42)
            bar.coords(mic_win, mic_x, h / 2)
            bar.itemconfigure(mic_win, width=mic_width, height=40)
            bar.coords(send_win, send_x, h / 2)
            bar.itemconfigure(send_win, width=send_size, height=send_size)
            composer["analyser_width"] = analyser_width
            self._draw_analyser(composer)
            self._draw_primary_action(composer)

        bar.bind("<Configure>", draw_bar)
        analyser.bind("<Button-1>", lambda _e: self.toggle_analysis_mode())
        analyser.bind("<Enter>", lambda _e: (composer.__setitem__("analyser_hover", True), self._draw_analyser(composer)))
        analyser.bind("<Leave>", lambda _e: (composer.__setitem__("analyser_hover", False), self._draw_analyser(composer)))
        send.bind("<Button-1>", lambda _e, h=home: self._composer_primary_action(h))
        send.bind("<Enter>", lambda _e: (composer.__setitem__("primary_hover", True), self._draw_primary_action(composer)))
        send.bind("<Leave>", lambda _e: (composer.__setitem__("primary_hover", False), self._draw_primary_action(composer)))

        def clear_placeholder_on_key(event):
            if composer.get("placeholder_active") and event.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
                self._clear_composer_placeholder(composer)
            return None

        def restore_placeholder(_event=None):
            if not self._composer_text(composer):
                self._set_composer_placeholder(composer)

        input_text.bind("<KeyPress>", clear_placeholder_on_key, add="+")
        input_text.bind("<FocusOut>", restore_placeholder, add="+")
        # Seule l'icône d'envoi est rafraîchie à la frappe : aucune redimension périodique.
        input_text.bind("<KeyRelease>", lambda _e, h=home: self._refresh_composer_primary_state(h), add="+")
        input_text.bind("<Return>", lambda e, h=home: self._enter_to_send(e, h))
        self._voice_controls.append(voice_btn)
        self._draw_analyser(composer)
        self._draw_primary_action(composer)
        return composer

    def start_voice_chat(self):
        """One-turn voice chat: dictate a request and read its answer aloud."""
        if self.busy or self.listen_busy:
            return
        self.start_voice_input(force_voice_response=True, force_auto_send=True)

    def toggle_voice_conversation(self):
        """Toggle hands-free voice conversation; click waveform again to stop."""
        if self.voice_session_active:
            self._end_voice_conversation()
            return
        if self.busy or self.listen_busy:
            self.voice_status_var.set("Termine d'abord la demande en cours.")
            return
        self._voice_output_before_session = self.voice_output
        self.voice_session_active = True
        self.voice_output = True
        self.voice_status_var.set("Discussion vocale active · clique sur l'onde pour arrêter")
        self._refresh_composer_primary_state()
        self.start_voice_input(force_voice_response=False)
        if not self.listen_busy:
            # No recognizer/device: restore a safe inactive state if the listener could not start.
            self._end_voice_conversation(restore_status=False)

    def _end_voice_conversation(self, restore_status=True):
        self.voice_session_active = False
        self.speak_next_response = False
        self.force_voice_auto_send = False
        self.stop_voice(silent=True)
        self.voice_output = bool(self._voice_output_before_session)
        self._refresh_composer_primary_state()
        if restore_status:
            self.voice_status_var.set("Discussion vocale arrêtée")

    def _continue_voice_conversation(self):
        if self.voice_session_active and not self.busy and not self.listen_busy:
            self.start_voice_input(force_voice_response=False)

    def _enter_to_send(self, event, home: bool):
        if event.state & 0x0001:  # Maj+Entrée : nouvelle ligne
            return None
        self.send_message(home=home)
        return "break"

    def active_composer(self):
        return self.home_composer if self.is_home else self.chat_composer

    def _refresh_attachment_previews(self):
        for composer in (self.home_composer, self.chat_composer):
            box = composer["previews"]
            for child in box.winfo_children():
                child.destroy()
            all_items = [(p, "image") for p in self.pending_images] + [(p, "file") for p in self.pending_files]
            if not all_items:
                box.pack_forget()
                continue
            if not box.winfo_manager():
                box.pack(fill="x", padx=12, pady=(10, 0))
            for path, kind in all_items:
                chip = tk.Frame(box, bg=PANEL_HOVER, highlightthickness=1, highlightbackground=BORDER)
                chip.pack(side="left", padx=(0, 8), pady=2)
                photo = self._thumbnail(path, (78, 56)) if kind == "image" else None
                if photo is not None:
                    image_label = tk.Label(chip, image=photo, bg=PANEL_HOVER)
                    image_label.image = photo
                    image_label.pack(side="left", padx=(4, 2), pady=4)
                else:
                    tk.Label(chip, text="▧" if kind == "image" else "▤", bg=PANEL_HOVER, fg=BLUE,
                             font=("Segoe UI Symbol", 19)).pack(side="left", padx=(7, 4), pady=3)
                short_name = path.name
                if len(short_name) > 27:
                    short_name = short_name[:24] + "…"
                tk.Label(chip, text=short_name, bg=PANEL_HOVER, fg=TEXT,
                         font=("Segoe UI", 9), anchor="w").pack(side="left", padx=4)
                remove = tk.Label(chip, text="×", bg=PANEL_HOVER, fg=MUTED,
                                  font=("Segoe UI", 16), cursor="hand2")
                remove.pack(side="left", padx=(5, 7))
                remove.bind("<Button-1>", lambda _e, p=path: self.remove_attachment(p))
        self._refresh_composer_primary_state()

    def _thumbnail(self, path: Path, size=(160, 110)):
        key = f"{path.resolve()}|{size[0]}x{size[1]}"
        if key in self.thumbnail_refs:
            return self.thumbnail_refs[key]
        photo = None
        try:
            if PIL_AVAILABLE:
                with Image.open(path) as im:
                    im.thumbnail(size)
                    photo = ImageTk.PhotoImage(im.copy())
            else:
                photo = tk.PhotoImage(file=str(path))
                factor = max(1, (photo.width() + size[0] - 1) // size[0], (photo.height() + size[1] - 1) // size[1])
                if factor > 1:
                    photo = photo.subsample(factor, factor)
        except Exception:
            photo = None
        if photo is not None:
            self.thumbnail_refs[key] = photo
        return photo

    # ---------------------------- conversation ----------------------------
    def show_home(self):
        self.is_home = True
        self.chat_view.grid_remove()
        self.home_view.grid()
        self.root.focus_set()

    def show_chat(self):
        self.is_home = False
        self.home_view.grid_remove()
        self.chat_view.grid()
        self.chat_composer["input"].focus_set()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_remove()
            self.sidebar_visible = False
        else:
            self.sidebar.grid()
            self.sidebar_visible = True

    def quick_prompt(self, prompt: str):
        self.show_home() if self.is_home else None
        composer = self.active_composer()
        current = self._composer_text(composer)
        composer["input"].delete("1.0", "end")
        composer["placeholder_active"] = False
        composer["input"].configure(fg=TEXT)
        composer["input"].insert("1.0", (current + "\n" if current else "") + prompt)
        composer["input"].focus_set()
        self._refresh_composer_primary_state(composer["home"])

    def new_chat(self, initial=False):
        if not initial:
            self.save_chat()
        self.current_chat_id = str(uuid.uuid4())
        self.current_turns = []
        self.api_messages = [{"role": "system", "content": self._effective_system_prompt()}]
        self.pending_images.clear()
        self.pending_files.clear()
        for composer in getattr(self, "home_composer", {}), getattr(self, "chat_composer", {}):
            if composer and "input" in composer:
                self._set_composer_placeholder(composer)
        if hasattr(self, "transcript"):
            self._clear_transcript()
        if hasattr(self, "home_composer"):
            self._refresh_attachment_previews()
        self.show_home()
        if not initial:
            self.status_var.set("Nouvelle discussion")
        self._refresh_recent_list()

    def _clear_transcript(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")
        self.photo_refs.clear()

    def _insert_transcript(self, role: str, text: str, images=None, muted=False):
        self.transcript.configure(state="normal")
        is_user = role in ("Vous", "user", "Utilisateur")
        role_tag = "user" if is_user else "assistant"
        body_tag = "muted_user" if (is_user and muted) else (
            "muted_assistant" if muted else ("body_user" if is_user else "body_assistant")
        )
        # Avatars de conversation : robot 🤖 pour VYNEX, silhouette 👤 pour l'utilisateur.
        # L'emoji reste du texte Unicode : aucune image ni dépendance supplémentaire n'est nécessaire.
        if is_user:
            self.transcript.insert("end", "Vous\n", role_tag)
        else:
            avatar = getattr(self, "_vynex_logo_photo", None)
            if avatar is not None:
                self.transcript.image_create("end-1c", image=avatar, padx=3, pady=1)
                self.transcript.insert("end-1c", "  VYNEX\n", role_tag)
            else:
                self.transcript.insert("end", "◈  VYNEX\n", role_tag)
        for path_text in (images or []):
            path = Path(path_text)
            photo = self._thumbnail(path, (240, 180)) if path.is_file() else None
            if photo is not None:
                # Taguer l'image incorporée permet au paragraphe de suivre le même alignement.
                image_start = self.transcript.index("end-1c")
                self.transcript.image_create("end-1c", image=photo, padx=2, pady=4)
                image_end = self.transcript.index("end-1c")
                if image_start != image_end:
                    self.transcript.tag_add(role_tag, image_start, image_end)
                self.photo_refs.append(photo)
                self.transcript.insert("end-1c", "\n", body_tag)
            elif path.is_file():
                image_note_tag = "muted_user" if is_user else "muted_assistant"
                self.transcript.insert("end-1c", f"[Image jointe : {path.name}]\n", image_note_tag)
        if text:
            self._insert_markdown(text, body_tag)
            self.transcript.insert("end-1c", "\n\n", body_tag)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _insert_markdown_inline(self, line: str, body_tag: str) -> None:
        """Affiche quelques marqueurs Markdown sans bibliothèque externe."""
        token_re = re.compile(r"(`[^`]+`|\*\*.+?\*\*|__.+?__|(?<!\*)\*(?!\s).+?(?<!\s)\*(?!\*)|(?<!_)_(?!\s).+?(?<!\s)_(?!_))")
        cursor = 0
        for match in token_re.finditer(line):
            if match.start() > cursor:
                self.transcript.insert("end-1c", line[cursor:match.start()], body_tag)
            token = match.group(0)
            if token.startswith("`") and token.endswith("`"):
                value, tag = token[1:-1], "md_inline_code"
            elif (token.startswith("**") and token.endswith("**")) or (token.startswith("__") and token.endswith("__")):
                value, tag = token[2:-2], "md_bold"
            else:
                value, tag = token[1:-1], "md_italic"
            self.transcript.insert("end-1c", value, (body_tag, tag))
            cursor = match.end()
        if cursor < len(line):
            self.transcript.insert("end-1c", line[cursor:], body_tag)

    def _insert_markdown(self, text: str, body_tag: str) -> None:
        """Rendu Markdown léger pour les réponses finales et l'historique."""
        lines = text.splitlines()
        if not lines:
            return
        in_code = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            fence = stripped.startswith("```")
            if fence:
                if not in_code:
                    in_code = True
                    language = stripped[3:].strip()
                    if language:
                        self.transcript.insert("end-1c", f"  {language.upper()}\n", (body_tag, "md_language"))
                else:
                    in_code = False
                continue

            if in_code:
                self.transcript.insert("end-1c", line + "\n", (body_tag, "md_code_block"))
                continue

            heading = re.match(r"^\s*(#{1,3})\s+(.+?)\s*#*\s*$", line)
            bullet = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            numbered = re.match(r"^(\s*)(\d+)[.)]\s+(.+)$", line)
            quote = re.match(r"^\s*>\s?(.*)$", line)
            rule = bool(re.match(r"^\s*(?:-{3,}|_{3,}|\*{3,})\s*$", line))

            if heading:
                level = len(heading.group(1))
                tag = f"md_h{level}"
                self.transcript.insert("end-1c", heading.group(2), (body_tag, tag))
            elif rule:
                self.transcript.insert("end-1c", "────────────────────────", (body_tag, "md_rule"))
            elif quote:
                self.transcript.insert("end-1c", "│ ", (body_tag, "md_quote"))
                self._insert_markdown_inline(quote.group(1), "md_quote")
            elif bullet:
                self.transcript.insert("end-1c", bullet.group(1) + "  •  ", (body_tag, "md_list_marker"))
                self._insert_markdown_inline(bullet.group(2), body_tag)
            elif numbered:
                self.transcript.insert("end-1c", f"{numbered.group(1)}  {numbered.group(2)}. ", (body_tag, "md_list_marker"))
                self._insert_markdown_inline(numbered.group(3), body_tag)
            else:
                self._insert_markdown_inline(line, body_tag)

            if index < len(lines) - 1:
                self.transcript.insert("end-1c", "\n", body_tag)

    def render_turns(self):
        self._clear_transcript()
        for turn in self.current_turns:
            role = turn.get("role", "VYNEX")
            if role in ("MonIA", "VYNEX"):
                role = "VYNEX"
            text = str(turn.get("text", ""))
            images = turn.get("image_paths", [])
            self._insert_transcript(role, text, images)
        self.show_chat() if self.current_turns else self.show_home()

    def remove_attachment(self, path: Path):
        self.pending_images = [p for p in self.pending_images if p != path]
        self.pending_files = [p for p in self.pending_files if p != path]
        self._refresh_attachment_previews()

    def _copy_to_library(self, source: Path) -> Path:
        try:
            if source.resolve().parent == IMAGE_DIR.resolve():
                return source
        except OSError:
            pass
        suffix = source.suffix.lower() or ".png"
        safe_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:5]}{suffix}"
        target = IMAGE_DIR / safe_name
        try:
            shutil.copy2(source, target)
            return target
        except OSError:
            return source

    def attach_images(self):
        paths = filedialog.askopenfilenames(
            parent=self.root, title="Choisir des images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("Tous les fichiers", "*.*")],
        )
        if not paths:
            return
        for item in paths:
            path = Path(item)
            if not path.is_file():
                continue
            saved = self._copy_to_library(path)
            if saved not in self.pending_images and len(self.pending_images) < 4:
                self.pending_images.append(saved)
        if len(paths) > 4:
            messagebox.showinfo(APP_TITLE, "VYNEX limite à 4 images par message pour préserver la mémoire.", parent=self.root)
        self._refresh_attachment_previews()
        self._close_plus_menu()

    def attach_files(self):
        paths = filedialog.askopenfilenames(
            parent=self.root, title="Joindre des fichiers texte",
            filetypes=[("Fichiers texte", "*.txt *.md *.csv *.json *.py *.html *.css *.js *.log"), ("Tous les fichiers", "*.*")],
        )
        if not paths:
            return
        allowed = {".txt", ".md", ".csv", ".json", ".py", ".html", ".css", ".js", ".log", ".xml", ".yaml", ".yml"}
        for item in paths:
            path = Path(item)
            if path.suffix.lower() not in allowed:
                messagebox.showwarning(APP_TITLE, f"Le format {path.suffix or '(sans extension)'} n'est pas encore pris en charge comme texte.", parent=self.root)
                continue
            if path.is_file() and path not in self.pending_files and len(self.pending_files) < 5:
                self.pending_files.append(path)
        self._refresh_attachment_previews()
        self._close_plus_menu()

    def capture_screenshot(self):
        self._close_plus_menu()
        if not PIL_AVAILABLE:
            messagebox.showwarning(APP_TITLE, "La capture d’écran nécessite Pillow. Installe cette dépendance et réessaie.", parent=self.root)
            return
        if not self._ensure_feature_permission("screen_capture"):
            self.status_var.set("Autorisation de capture d’écran refusée")
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "Capturer tout l’écran et préparer l’image comme pièce jointe ? Vérifie qu’aucune information privée n’est visible. L’image n’est envoyée au moteur que si tu envoies ensuite le message.",
            parent=self.root,
        ):
            return
        try:
            self.root.iconify()
            self.root.after(650, lambda: self._capture_screenshot_after_minimize())
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Capture impossible : {exc}", parent=self.root)

    def _capture_screenshot_after_minimize(self):
        try:
            shot = ImageGrab.grab()
            out = IMAGE_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S}.png"
            shot.save(out)
            self.pending_images.append(out)
            self.root.deiconify()
            self.root.lift()
            self._refresh_attachment_previews()
            self.status_var.set("Capture d'écran ajoutée au message")
        except Exception as exc:
            self.root.deiconify()
            messagebox.showerror(APP_TITLE, f"Capture impossible : {exc}", parent=self.root)

    # ---------------------------- plus menu ----------------------------
    def open_plus_menu(self, home=False):
        if self.plus_popup and self.plus_popup.winfo_exists():
            self.close_plus_menu()
            return
        self.close_plus_menu()
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg=BORDER)
        popup.attributes("-topmost", True)
        self.plus_popup = popup
        outer = tk.Frame(popup, bg=PANEL, highlightthickness=1, highlightbackground=BORDER_HOVER)
        outer.pack(fill="both", expand=True, padx=1, pady=1)
        rows = [
            ("⌁", "Importer ou ajouter des fichiers…", "Ctrl+U", self.attach_files),
            ("▧", "Ajouter une photo", "", self.attach_images),
            ("▣", "Prendre une capture d’écran", "", self.capture_screenshot),
            ("◇", "Ajouter au projet", "›", self.add_to_project),
            ("</>", "Mode Développeur", "", self.open_developer_tools),
            (None, None, None, None),
            ("✧", "Skills", "›", self.open_skills),
            ("♫", "Lire la dernière réponse", "", self.read_last_answer),
            ("■", "Arrêter la voix", "", self.stop_voice),
            ("▦", "Ajouter un connecteur", "›", self.open_connectors),
            ("◉", "Système de design", "›", self.open_settings),
            ("⌘", "Plugins locaux", "›", self.open_plugins),
            (None, None, None, None),
            ("◎", "Recherche web", "", self.web_search_unavailable),
        ]
        for icon, label, hint, action in rows:
            if label is None:
                tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", padx=10, pady=6)
                continue
            row = tk.Frame(outer, bg=PANEL, cursor="hand2")
            row.pack(fill="x", padx=5, pady=1)
            left = tk.Label(row, text=icon, width=3, bg=PANEL, fg=TEXT, font=("Segoe UI Symbol", 13))
            left.pack(side="left", padx=(6, 3), pady=7)
            title = tk.Label(row, text=label, bg=PANEL, fg=TEXT, anchor="w", font=("Segoe UI", 11))
            title.pack(side="left", fill="x", expand=True, padx=3, pady=7)
            hint_label = None
            if hint:
                hint_label = tk.Label(row, text=hint, bg=PANEL, fg=MUTED, font=("Segoe UI", 10))
                hint_label.pack(side="right", padx=(8, 12))
            row_widgets = tuple(w for w in (row, left, title, hint_label) if w is not None)
            def set_row_hover(_event, widgets=row_widgets, colour=PANEL_HOVER):
                for widget in widgets:
                    try:
                        widget.configure(bg=colour)
                    except tk.TclError:
                        pass
            def run_row_action(_event, callback=action):
                callback()
            for w in row_widgets:
                w.bind("<Enter>", set_row_hover)
                w.bind("<Leave>", lambda _e, widgets=row_widgets: [item.configure(bg=PANEL) for item in widgets])
                w.bind("<Button-1>", run_row_action)
        popup.update_idletasks()
        anchor = self.active_composer()["plus"]
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() - popup.winfo_reqheight() - 8
        x = max(8, min(x, self.root.winfo_screenwidth() - popup.winfo_reqwidth() - 8))
        y = max(8, y)
        popup.geometry(f"{popup.winfo_reqwidth()}x{popup.winfo_reqheight()}+{x}+{y}")
        popup.bind("<FocusOut>", lambda _e: self.root.after(150, self._close_plus_if_outside))
        popup.focus_force()

    def _close_plus_if_outside(self):
        popup = self.plus_popup
        if not popup or not popup.winfo_exists():
            return
        try:
            focused = self.root.focus_get()
            if focused is None or str(focused).startswith(str(popup)):
                return
        except tk.TclError:
            pass
        self.close_plus_menu()

    def _close_plus_menu(self):
        popup, self.plus_popup = self.plus_popup, None
        if popup:
            try:
                popup.destroy()
            except tk.TclError:
                pass

    close_plus_menu = _close_plus_menu

    def add_to_project(self):
        self._close_plus_menu()
        name = simpledialog.askstring(APP_TITLE, "Nom du projet local :", initialvalue=self.active_project, parent=self.root)
        if name is None:
            return
        self.active_project = name.strip()
        self.settings["active_project"] = self.active_project
        write_json(SETTINGS_FILE, self.settings)
        if self.active_project:
            self.status_var.set(f"Projet actif : {self.active_project}")

    def open_developer_tools(self):
        """Ouvre un éditeur local léger. Le code est affiché/enregistré, jamais exécuté automatiquement."""
        self._close_plus_menu()
        win = tk.Toplevel(self.root)
        win.title("VYNEX · Mode Développeur")
        win.configure(bg=BG)
        win.geometry("980x700")
        win.minsize(700, 500)
        win.transient(self.root)

        tk.Label(win, text="✦  Mode Développeur", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(win, text="Écris, importe, copie ou enregistre du code. VYNEX ne l'exécutera pas automatiquement.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10), wraplength=850, justify="left").pack(anchor="w", padx=18, pady=(0, 12))

        toolbar = tk.Frame(win, bg=BG)
        toolbar.pack(fill="x", padx=18, pady=(0, 8))
        language_var = tk.StringVar(value="Python")
        tk.Label(toolbar, text="Langage :", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        language_menu = tk.OptionMenu(toolbar, language_var, "Python", "HTML", "CSS", "JavaScript", "JSON", "Texte")
        language_menu.configure(bg=PANEL, fg=TEXT, activebackground=PANEL_HOVER, activeforeground=TEXT,
                                relief="flat", highlightthickness=0, font=("Segoe UI", 10))
        language_menu["menu"].configure(bg=PANEL, fg=TEXT, activebackground=ACCENT, activeforeground="white")
        language_menu.pack(side="left")

        editor_wrap = tk.Frame(win, bg=BORDER, padx=1, pady=1)
        editor_wrap.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        editor = tk.Text(editor_wrap, wrap="none", undo=True, bg="#101A2E", fg="#ECF3FF",
                         insertbackground=TEXT, selectbackground="#1A5A4B", relief="flat", bd=0,
                         font=("Consolas", 10), padx=12, pady=10, tabs=(32,))
        yscroll = tk.Scrollbar(editor_wrap, orient="vertical", command=editor.yview)
        xscroll = tk.Scrollbar(editor_wrap, orient="horizontal", command=editor.xview)
        editor.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        editor.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        editor_wrap.rowconfigure(0, weight=1)
        editor_wrap.columnconfigure(0, weight=1)

        status = tk.StringVar(value="Prêt · aucun code exécuté")
        tk.Label(win, textvariable=status, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 4))

        def extension_for_language():
            return {"Python": ".py", "HTML": ".html", "CSS": ".css", "JavaScript": ".js", "JSON": ".json", "Texte": ".txt"}.get(language_var.get(), ".txt")

        def put_code(code, note):
            editor.delete("1.0", "end")
            editor.insert("1.0", code)
            editor.edit_modified(False)
            status.set(note)

        def copy_code():
            code = editor.get("1.0", "end-1c")
            if not code.strip():
                messagebox.showinfo(APP_TITLE, "L'éditeur est vide.", parent=win)
                return
            try:
                win.clipboard_clear()
                win.clipboard_append(code)
                win.update_idletasks()
                status.set("Code copié dans le presse-papiers")
            except tk.TclError as exc:
                messagebox.showerror(APP_TITLE, f"Copie impossible : {exc}", parent=win)

        def save_code():
            code = editor.get("1.0", "end-1c")
            if not code.strip():
                messagebox.showinfo(APP_TITLE, "Écris ou importe du code avant l'enregistrement.", parent=win)
                return
            ext = extension_for_language()
            filters = [(f"Fichier {language_var.get()} (*{ext})", f"*{ext}"), ("Tous les fichiers", "*.*")]
            path = filedialog.asksaveasfilename(parent=win, title="Enregistrer le code sous…",
                                                defaultextension=ext, filetypes=filters)
            if not path:
                return
            destination = Path(path)
            try:
                destination.write_text(code, encoding="utf-8", newline="\n")
                status.set(f"Enregistré : {destination.name}")
                messagebox.showinfo(APP_TITLE, f"Fichier enregistré :\n{destination}", parent=win)
            except OSError as exc:
                messagebox.showerror(APP_TITLE, f"Enregistrement impossible : {exc}", parent=win)

        def open_code_file():
            path = filedialog.askopenfilename(parent=win, title="Ouvrir un fichier de code",
                filetypes=[("Code et texte", "*.py *.html *.css *.js *.json *.txt *.md *.csv *.xml *.yaml *.yml"), ("Tous les fichiers", "*.*")])
            if not path:
                return
            selected = Path(path)
            try:
                if selected.stat().st_size > 1_500_000:
                    messagebox.showwarning(APP_TITLE, "Ce fichier dépasse 1,5 Mo. Choisis un fichier plus petit pour préserver la mémoire.", parent=win)
                    return
                code = selected.read_text(encoding="utf-8", errors="replace")
                suffix_to_language = {".py": "Python", ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".js": "JavaScript", ".json": "JSON"}
                if selected.suffix.lower() in suffix_to_language:
                    language_var.set(suffix_to_language[selected.suffix.lower()])
                put_code(code, f"Fichier ouvert : {selected.name}")
            except OSError as exc:
                messagebox.showerror(APP_TITLE, f"Ouverture impossible : {exc}", parent=win)

        def recover_last_code():
            answer = str(getattr(self, "last_assistant_answer", "") or "")
            blocks = list(re.finditer(r"```\s*([\w+#.-]*)\s*\n(.*?)```", answer, flags=re.DOTALL))
            if not blocks:
                messagebox.showinfo(APP_TITLE, "Aucun bloc de code clôturé (``` ... ```) dans la dernière réponse.", parent=win)
                return
            block = blocks[-1]
            language = block.group(1).lower()
            lang_map = {"py": "Python", "python": "Python", "html": "HTML", "htm": "HTML", "css": "CSS", "js": "JavaScript", "javascript": "JavaScript", "json": "JSON", "txt": "Texte", "text": "Texte"}
            language_var.set(lang_map.get(language, language_var.get()))
            put_code(block.group(2).rstrip(), "Dernier bloc de code récupéré depuis la réponse de VYNEX")

        def ask_for_correction():
            code = editor.get("1.0", "end-1c").strip()
            if not code:
                messagebox.showinfo(APP_TITLE, "Écris ou importe d'abord du code.", parent=win)
                return
            if len(code) > 26000:
                messagebox.showwarning(APP_TITLE, "Le code est trop long pour une demande unique. Réduis le fichier à 26 000 caractères ou moins.", parent=win)
                return
            language = language_var.get()
            request = (
                f"Mode Développeur — langage : {language}. Analyse le code ci-dessous. "
                "Explique brièvement les problèmes, puis propose une version corrigée complète dans un bloc de code. "
                "N'affirme pas avoir exécuté ni testé le programme. Préserve le comportement existant autant que possible.\n\n"
                f"```{language.lower()}\n{code}\n```"
            )
            win.destroy()
            self.quick_prompt(request)
            self.status_var.set("Code préparé pour analyse · clique sur Envoyer")

        buttons = tk.Frame(win, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 16))
        self._button(buttons, "Ouvrir…", open_code_file, compact=True).pack(side="left", padx=(0, 6))
        self._button(buttons, "Récupérer le dernier code", recover_last_code, compact=True).pack(side="left", padx=3)
        self._button(buttons, "Copier", copy_code, compact=True).pack(side="left", padx=3)
        self._button(buttons, "Enregistrer sous…", save_code, compact=True).pack(side="left", padx=3)
        self._button(buttons, "Demander une correction", ask_for_correction, primary=True, compact=True).pack(side="right", padx=(6, 0))

    def open_skills(self):
        self._close_plus_menu()
        win = tk.Toplevel(self.root)
        win.title("Skills VYNEX")
        win.configure(bg=BG)
        win.geometry("450x400")
        tk.Label(win, text="Compétences locales", bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(18, 8))
        tk.Label(win, text="Choisis une aide pour préparer ton message.", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 12))
        items = [
            ("Aide informatique Windows", "Aide-moi à résoudre ce problème Windows, étape par étape : "),
            ("Rédaction et correction", "Aide-moi à rédiger ou corriger ce texte, clairement et professionnellement : "),
            ("Apprentissage", "Explique-moi cette notion simplement, avec un exemple : "),
            ("Programmation", "Aide-moi à comprendre ou corriger ce code, sans inventer les résultats : "),
        ]
        for label, prompt in items:
            self._button(win, label, lambda p=prompt: (win.destroy(), self.quick_prompt(p)), anchor="w").pack(fill="x", padx=20, pady=4)

    def open_connectors(self):
        self._close_plus_menu()
        messagebox.showinfo(APP_TITLE, "Aucun connecteur externe n'est configuré. VYNEX Lite reste locale : elle peut utiliser le modèle installé, les images jointes et les fichiers choisis explicitement.", parent=self.root)

    def open_plugins(self):
        self._close_plus_menu()
        messagebox.showinfo(APP_TITLE, "Modules disponibles : discussion locale, analyse d'images, lecture vocale, dictée vocale (si la reconnaissance française Windows est installée), historique, bibliothèque et rappels.", parent=self.root)

    def web_search_unavailable(self):
        self._close_plus_menu()
        messagebox.showinfo(APP_TITLE, "La recherche Web n'est pas active dans cette version hors ligne. VYNEX ne consultera pas Internet sans une future intégration explicite.", parent=self.root)

    # ---------------------------- send message / model ----------------------------
    def send_message(self, event=None, home=None):
        if self.busy:
            return "break" if event else None
        if home is None:
            home = self.is_home
        composer = self.home_composer if home else self.chat_composer
        text = self._composer_text(composer)
        if not text and not self.pending_images and not self.pending_files:
            return "break" if event else None
        # Also protect legacy settings files that might already contain a remote endpoint.
        # Check before reading/clearing attachments or altering the conversation.
        if not self._ensure_chat_endpoint_consent():
            return "break" if event else None

        text_file_data = []
        for path in list(self.pending_files):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")[:25000]
                text_file_data.append(f"\n\n--- Fichier : {path.name} ---\n{content}")
            except OSError as exc:
                text_file_data.append(f"\nImpossible de lire {path.name} : {exc}")
        prompt = text or "Analyse les fichiers ou images joints et explique les éléments importants."
        if self.active_project:
            prompt = f"[Projet local : {self.active_project}]\n" + prompt
        if text_file_data:
            prompt += "\n\nFichiers texte joints :" + "".join(text_file_data)

        image_paths = list(self.pending_images)
        max_images = max(1, min(4, int(self.settings.get("vision_max_images", 4))))
        if len(image_paths) > max_images:
            prompt += f"\n\nNote : {len(image_paths)} images sont jointes, mais les paramètres limitent l'analyse aux {max_images} premières."
        attachment_names = [p.name for p in image_paths] + [p.name for p in self.pending_files]
        self.pending_images.clear()
        self.pending_files.clear()
        self._refresh_attachment_previews()
        composer["input"].delete("1.0", "end")
        self._set_composer_placeholder(composer)
        self.show_chat()
        self.busy = True
        self.stop_event.clear()
        self._button_state_send(False)
        self._insert_transcript("Vous", prompt, [str(p) for p in image_paths])
        self.current_turns.append({"role": "Vous", "text": prompt, "image_paths": [str(p) for p in image_paths], "attachments": attachment_names, "time": datetime.now().isoformat(timespec="seconds")})

        api_user_content = prompt
        self.api_messages.append({"role": "user", "content": api_user_content})
        system_content = self._effective_system_prompt()
        if self.deep_mode:
            system_content += (
                "\nMode Analyser activé : donne une réponse particulièrement précise et structurée. "
                "Vérifie les hypothèses, sépare les faits des incertitudes, détaille les étapes utiles et "
                "ajoute un exemple si cela aide. Ne prétends pas avoir vérifié ce que tu n'as pas vérifié. "
                "Fournis une explication claire et synthétique, sans exposer de raisonnement interne privé."
            )
        request_messages = [{"role": "system", "content": system_content}]
        if self.active_project:
            request_messages.append({"role": "system", "content": f"Projet actif : {self.active_project}. Tiens compte de ce contexte si utile."})
        recent = self.api_messages[1:][-8:]
        request_messages.extend([dict(m) for m in recent])
        if image_paths:
            image_content = [{"type": "text", "text": prompt}]
            try:
                for path in image_paths[:max_images]:
                    mime = file_mime(path)
                    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                    image_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})
            except OSError as exc:
                self.busy = False
                self._button_state_send(True)
                self._insert_transcript("VYNEX", f"Impossible de lire l’image jointe : {exc}")
                self.status_var.set("Erreur de lecture d'image")
                self._stream_insert_ready = False
                try:
                    self.save_chat()
                except Exception:
                    pass
                return "break" if event else None
            request_messages[-1]["content"] = image_content

        self._begin_stream_display()
        self.status_var.set("VYNEX prépare une réponse…")
        threading.Thread(target=self._request_answer, args=(request_messages,), daemon=True).start()
        return "break" if event else None

    def _button_state_send(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for composer in (self.home_composer, self.chat_composer):
            composer["send"].configure(state=state)
            composer["mic"].configure(state=state, text=("🎙" if enabled else "…"))
            composer["stop_reply"].configure(state=("disabled" if enabled else "normal"))
        self._refresh_composer_primary_state()

    def _begin_stream_display(self):
        self.transcript.configure(state="normal")
        avatar = getattr(self, "_vynex_logo_photo", None)
        if avatar is not None:
            self.transcript.image_create("end-1c", image=avatar, padx=3, pady=1)
            self.transcript.insert("end-1c", "  VYNEX\n", "assistant")
        else:
            self.transcript.insert("end-1c", "◈  VYNEX\n", "assistant")
        self._stream_insert_ready = True
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _append_stream_chunk(self, chunk: str):
        if not chunk:
            return
        self.transcript.configure(state="normal")
        self.transcript.insert("end-1c", chunk, "body_assistant")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _request_answer(self, request_messages):
        """Route text to a stronger local chat model and photos to the local vision model."""
        chat_model = str(self.settings.get("chat_model", DEFAULT_CHAT_MODEL) or DEFAULT_CHAT_MODEL).strip()
        text_url = str(self.settings.get("chat_url", OLLAMA_URL) or OLLAMA_URL).rstrip("/") + "/api/chat"
        messages = [dict(message) for message in request_messages]
        current_content = messages[-1].get("content", "") if messages else ""
        phase = "conversation"
        try:
            if isinstance(current_content, list):
                phase = "analyse visuelle"
                # Vision input uses the image-capable local llama.cpp server.
                image_parts = current_content
                prompt_text = next((str(part.get("text", "")).strip()
                                    for part in image_parts
                                    if isinstance(part, dict) and part.get("type") == "text"), "")
                vision_payload = {
                    "model": MODEL_PATH.name,
                    "messages": [
                        {"role": "system", "content": (
                            "Tu es le module visuel de VYNEX. Décris en français les éléments réellement visibles, "
                            "le texte lisible et les détails importants. Ne devine pas ce qui est incertain. "
                            "N'écris pas de consignes internes." )},
                        {"role": "user", "content": image_parts},
                    ],
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 220,
                }
                vision_req = urllib.request.Request(
                    CHAT_URL,
                    data=json.dumps(vision_payload, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    method="POST",
                )
                self.root.after(0, lambda: self.status_var.set("VYNEX analyse l’image localement…"))
                with urllib.request.urlopen(vision_req, timeout=300) as vision_response:
                    self.active_response = vision_response
                    vision_result = json.loads(vision_response.read().decode("utf-8", errors="replace"))
                self.active_response = None
                choices = vision_result.get("choices") or []
                vision_description = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
                if not vision_description:
                    raise RuntimeError("Le modèle visuel n’a renvoyé aucune description. Essaie une image plus nette ou plus petite.")
                enriched_prompt = (
                    (prompt_text or "Analyse l’image jointe et explique les éléments importants.")
                    + "\n\nDescription visuelle générée localement (elle peut contenir des erreurs) :\n"
                    + vision_description
                    + "\n\nRéponds à la demande de l’utilisateur en tenant compte de cette description."
                )
                messages[-1] = {"role": "user", "content": enriched_prompt}
                # Preserve the visual summary for follow-up questions in this session.
                for item in reversed(self.api_messages):
                    if item.get("role") == "user" and item.get("content") == prompt_text:
                        item["content"] = enriched_prompt
                        break

            phase = "conversation"
            clean_messages = []
            for message in messages:
                role = message.get("role")
                content = message.get("content", "")
                if role not in ("system", "user", "assistant"):
                    continue
                if isinstance(content, list):
                    content = "[Image jointe précédemment, description non disponible dans cet historique.]"
                clean_messages.append({"role": role, "content": str(content)})

            payload = {
                "model": chat_model,
                "messages": clean_messages,
                "stream": True,
                "keep_alive": "5m",
                "options": {
                    "temperature": float(self.settings.get("temperature", 0.35)),
                    "num_ctx": 2048,
                    "num_predict": int(self.settings.get("max_tokens", 512)),
                    "top_p": 0.9,
                    "repeat_penalty": 1.08,
                },
            }
            req = urllib.request.Request(
                text_url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            collected = []
            try:
                with urllib.request.urlopen(req, timeout=300) as response:
                    self.active_response = response
                    for raw in response:
                        if self.stop_event.is_set():
                            break
                        line = raw.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        try:
                            packet = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if packet.get("error"):
                            raise RuntimeError(str(packet["error"]))
                        part = packet.get("message", {}).get("content", "")
                        if isinstance(part, str) and part:
                            collected.append(part)
                            self.root.after(0, self._append_stream_chunk, part)
                        if packet.get("done"):
                            break
            except (urllib.error.URLError, urllib.error.HTTPError) as ollama_error:
                # Si Ollama ou son modèle texte est absent, le même modèle visuel local
                # peut encore assurer le chat, sans télécharger de deuxième gros modèle.
                if collected:
                    raise
                self.active_response = None
                self.root.after(0, self.status_var.set, "Ollama indisponible · essai avec le modèle local déjà chargé…")
                try:
                    ready = False
                    for _ in range(10):
                        if self.stop_event.is_set():
                            break
                        if self.server_ready():
                            ready = True
                            break
                        time.sleep(0.5)
                    if not ready:
                        raise RuntimeError("Le moteur local de secours n’est pas encore prêt. Attends l’état ‘Vision locale prête’, puis réessaie.")
                    fallback_answer = self._stream_local_chat(clean_messages)
                    if self.stop_event.is_set():
                        self.root.after(0, self._finish_answer, fallback_answer, "Réponse interrompue à ta demande.")
                    elif not fallback_answer:
                        self.root.after(0, self._finish_answer, "", "Le modèle local de secours n’a renvoyé aucun texte.")
                    else:
                        self.root.after(0, self._finish_answer, fallback_answer, None)
                except Exception as fallback_error:
                    self.root.after(
                        0, self._finish_answer, "",
                        "Le chat Ollama est indisponible et le modèle local de secours a échoué. "
                        f"Erreur Ollama : {ollama_error}. Erreur locale : {fallback_error}",
                    )
                return
            self.active_response = None
            answer = "".join(collected).strip()
            if self.stop_event.is_set():
                self.root.after(0, self._finish_answer, answer, "Réponse interrompue à ta demande.")
            elif not answer:
                self.root.after(0, self._finish_answer, "", "Le modèle n’a renvoyé aucun texte. Vérifie qu’Ollama fonctionne et que le modèle est installé.")
            else:
                self.root.after(0, self._finish_answer, answer, None)
        except urllib.error.HTTPError as exc:
            try:
                details = exc.read().decode("utf-8", errors="replace")[:1200]
            except Exception:
                details = str(exc)
            if exc.code == 404 and phase == "conversation":
                error = (f"Le modèle '{chat_model}' est introuvable dans Ollama. Ouvre PowerShell, vérifie avec `ollama list`, "
                         f"puis si nécessaire exécute : ollama pull {chat_model}.\n\n{details}")
            elif phase == "analyse visuelle":
                error = f"Le module d'analyse d'image local a renvoyé une erreur ({exc.code}) : {details}"
            else:
                error = f"Erreur du moteur local ({exc.code}) : {details}"
            self.root.after(0, self._finish_answer, "", error)
        except urllib.error.URLError as exc:
            self.active_response = None
            message = ("Impossible de joindre Ollama sur 127.0.0.1:11434. Lance Ollama depuis le menu Démarrer, "
                       "puis réessaie. Le serveur llama.cpp sur le port 9931 sert à analyser les images.")
            self.root.after(0, self._finish_answer, "", message + f"\nDétail : {exc}")
        except Exception as exc:
            self.active_response = None
            self.root.after(0, self._finish_answer, "", f"Erreur du moteur local : {exc}")
        finally:
            self.active_response = None

    def _stream_local_chat(self, messages) -> str:
        """Chat de secours avec le llama-server déjà lancé et le modèle SmolVLM local."""
        local_messages = [dict(item) for item in messages if isinstance(item, dict)]
        system_instruction = (
            "Tu es VYNEX, un assistant personnel utile et précis. "
            "Réponds toujours en français, sauf si l'utilisateur demande une autre langue. "
            "Explique clairement les choses, reconnais les incertitudes et n'invente pas de faits."
        )
        system_index = next(
            (i for i, item in enumerate(local_messages) if item.get("role") == "system"),
            None,
        )
        if system_index is None:
            local_messages.insert(0, {"role": "system", "content": system_instruction})
        else:
            existing = str(local_messages[system_index].get("content", "")).strip()
            local_messages[system_index]["content"] = (
                existing + "\n\n" + system_instruction
            ).strip()

        payload = {
            "model": MODEL_PATH.name,
            "messages": local_messages,
            "stream": True,
            "temperature": float(self.settings.get("temperature", 0.25)),
            "max_tokens": int(self.settings.get("max_tokens", 512)),
            "top_p": 0.9,
        }
        req = urllib.request.Request(
            CHAT_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        chunks = []
        with urllib.request.urlopen(req, timeout=300) as response:
            self.active_response = response
            for raw in response:
                if self.stop_event.is_set():
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                # llama.cpp emploie le format SSE « data: {...} ».
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    packet = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if packet.get("error"):
                    raise RuntimeError(str(packet["error"]))
                choices = packet.get("choices") or []
                part = ""
                if choices and isinstance(choices[0], dict):
                    delta = choices[0].get("delta") or {}
                    part = delta.get("content", "") or choices[0].get("text", "")
                if isinstance(part, str) and part:
                    chunks.append(part)
                    self.root.after(0, self._append_stream_chunk, part)
        self.active_response = None
        return "".join(chunks).strip()

    def _finish_answer(self, answer: str, error: str | None):
        self.busy = False
        self._button_state_send(True)
        self._stream_insert_ready = False
        self.transcript.configure(state="normal")

        if error:
            self.transcript.insert("end-1c", "\n\n" + error + "\n\n", "muted_assistant")
            if answer:
                self.last_assistant_answer = answer
                self.api_messages.append({"role": "assistant", "content": answer})
                self.current_turns.append({
                    "role": "VYNEX",
                    "text": answer,
                    "time": datetime.now().isoformat(timespec="seconds"),
                })
            self.status_var.set(error[:100])
        else:
            self.transcript.insert("end", "\n\n")
            self.last_assistant_answer = answer
            self.api_messages.append({"role": "assistant", "content": answer})
            self.current_turns.append({
                "role": "VYNEX",
                "text": answer,
                "time": datetime.now().isoformat(timespec="seconds"),
            })
            self.status_var.set("Réponse reçue · local")

        self.transcript.configure(state="disabled")
        self.transcript.see("end")
        # Après le flux brut, redessine l'échange avec la mise en forme Markdown.
        if not error:
            self.render_turns()
        self.save_chat()

        speak_this_answer = bool(self.voice_output or self.speak_next_response)
        self.speak_next_response = False
        if not error and answer and speak_this_answer:
            self.speak_text(answer)
    def stop_generation(self):
        if not self.busy:
            return
        self.stop_event.set()
        self.status_var.set("Arrêt demandé…")
        try:
            if self.active_response:
                self.active_response.close()
        except Exception:
            pass

    # ---------------------------- speech ----------------------------
    def toggle_voice_output(self):
        self.voice_output = not self.voice_output
        self.settings["auto_speak"] = self.voice_output
        write_json(SETTINGS_FILE, self.settings)
        label = "Réponse vocale : ON" if self.voice_output else "Réponse vocale : OFF"
        for composer in (self.home_composer, self.chat_composer):
            composer["voice_btn"].configure(text=label)
        self.voice_status_var.set("Lecture auto activée" if self.voice_output else "Lecture auto désactivée")

    def _powershell(self) -> str | None:
        candidates = [
            shutil.which("powershell.exe"),
            str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
        return None

    def read_last_answer(self):
        if not self.last_assistant_answer:
            messagebox.showinfo(APP_TITLE, "VYNEX n'a pas encore donné de réponse à lire.", parent=self.root)
            return
        self.speak_text(self.last_assistant_answer)

    def copy_last_answer(self, _event=None):
        """Copie la dernière réponse de VYNEX dans le presse-papiers Windows."""
        answer = str(getattr(self, "last_assistant_answer", "") or "").strip()
        if not answer:
            self.status_var.set("Aucune réponse à copier pour le moment")
            return "break" if _event is not None else None
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(answer)
            self.root.update_idletasks()
            self.status_var.set("Dernière réponse copiée · Ctrl+Maj+C")
        except tk.TclError:
            self.status_var.set("Copie impossible : presse-papiers indisponible")
        return "break" if _event is not None else None

    def speak_text(self, text: str):
        """Lit la réponse avec le moteur vocal système de chaque plateforme."""
        text = clean_text_for_speech(text)
        if not text:
            return

        speech_file: Path | None = None
        rate_setting = max(-5, min(5, int(self.settings.get("speak_rate", 0))))
        if os.name == "nt":
            powershell = self._powershell()
            if not powershell:
                messagebox.showwarning(APP_TITLE, "PowerShell Windows est introuvable ; la lecture vocale ne peut pas démarrer.", parent=self.root)
                return
            speech_file = DATA_DIR / f"speak_{uuid.uuid4().hex}.txt"
            speech_file.write_text(text, encoding="utf-8")
            command = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TTS_SCRIPT), str(speech_file), str(rate_setting)]
        elif sys.platform == "darwin":
            say = shutil.which("say")
            if not say:
                messagebox.showwarning(APP_TITLE, "Le moteur vocal macOS (say) est introuvable.", parent=self.root)
                return
            command = [say, "-r", str(175 + 12 * rate_setting), text]
        else:
            espeak = shutil.which("espeak-ng") or shutil.which("espeak")
            spd_say = shutil.which("spd-say")
            if espeak:
                command = [espeak, "-s", str(175 + 15 * rate_setting), text]
            elif spd_say:
                command = [spd_say, "-w", "-r", str(12 * rate_setting), text]
            else:
                messagebox.showwarning(APP_TITLE, "Aucun moteur vocal détecté. Installe espeak-ng ou speech-dispatcher pour activer la lecture vocale sous Linux.", parent=self.root)
                return

        self.stop_voice(silent=True)
        try:
            log_path = LOG_DIR / "voice-output.log"
            with open(log_path, "ab") as log_file:
                kwargs = {"stdout": log_file, "stderr": subprocess.STDOUT}
                if os.name == "nt":
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                self.tts_process = subprocess.Popen(command, **kwargs)
            self.voice_status_var.set("Lecture vocale en cours…")
            process = self.tts_process
            threading.Thread(target=self._wait_tts, args=(process, speech_file), daemon=True).start()
        except Exception as exc:
            if speech_file:
                speech_file.unlink(missing_ok=True)
            messagebox.showerror(APP_TITLE, f"Impossible de démarrer la voix : {exc}", parent=self.root)

    def _wait_tts(self, process, text_path):
        try:
            process.wait(timeout=600)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
        if text_path is not None:
            text_path.unlink(missing_ok=True)
        try:
            self.root.after(0, self._tts_finished, process)
        except tk.TclError:
            pass

    def _tts_finished(self, process):
        if self.tts_process is process:
            self.tts_process = None
            if self.voice_session_active:
                self.voice_status_var.set("Discussion vocale active · je t'écoute…")
                self.root.after(450, self._continue_voice_conversation)
            else:
                self.voice_status_var.set("Lecture vocale terminée")

    def stop_voice(self, silent=False):
        process, self.tts_process = self.tts_process, None
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        if not silent:
            self.voice_status_var.set("Lecture vocale arrêtée")

    def start_voice_input(self, force_voice_response=False, force_auto_send=False):
        if self.listen_busy or self.busy:
            return
        powershell = self._powershell()
        vosk_ready = find_vosk_model_dir() is not None
        if not powershell and not vosk_ready:
            messagebox.showwarning(APP_TITLE, "Aucun moteur de dictée n’est configuré. Installe Vosk + sounddevice et ajoute le modèle français local au dossier models de VYNEXRuntime (ou active la reconnaissance vocale native de Windows).", parent=self.root)
            return
        if not self._ensure_feature_permission("microphone"):
            self.voice_status_var.set("Accès au microphone non autorisé dans VYNEX")
            return
        self.speak_next_response = bool(force_voice_response)
        self.force_voice_auto_send = bool(force_auto_send)
        self._listen_started_in_session = bool(self.voice_session_active)
        self.listen_busy = True
        self.voice_status_var.set("Écoute hors ligne… parle puis fais une courte pause (max. 22 s)")
        for composer in (self.home_composer, self.chat_composer):
            composer["mic"].configure(state="disabled", text="…")
        result_path = DATA_DIR / f"voice_result_{uuid.uuid4().hex}.txt"
        threading.Thread(target=self._listen_worker, args=(powershell, result_path), daemon=True).start()

    def _listen_worker(self, powershell, result_path):
        """Reconnaissance française Vosk hors ligne en priorité, avec repli Windows."""
        result, stderr = "", ""
        try:
            model_dir = find_vosk_model_dir()
            if model_dir is not None:
                try:
                    import sounddevice as sd  # type: ignore
                    from vosk import KaldiRecognizer, Model, SetLogLevel  # type: ignore
                    SetLogLevel(-1)
                    if getattr(self, "_vosk_model_path", None) != str(model_dir):
                        self._vosk_model_instance = Model(str(model_dir))
                        self._vosk_model_path = str(model_dir)
                    recognizer = KaldiRecognizer(self._vosk_model_instance, 16000)
                    audio_queue: queue.Queue[bytes] = queue.Queue()

                    def callback(indata, frames, time_info, status):
                        try:
                            audio_queue.put(bytes(indata))
                        except Exception:
                            pass

                    self.root.after(0, lambda: self.voice_status_var.set("Écoute hors ligne… parle, puis fais une courte pause."))
                    found = ""
                    started = time.monotonic()
                    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype="int16", channels=1, callback=callback):
                        while time.monotonic() - started < 22:
                            try:
                                audio = audio_queue.get(timeout=1.0)
                            except queue.Empty:
                                continue
                            if recognizer.AcceptWaveform(audio):
                                piece = json.loads(recognizer.Result()).get("text", "").strip()
                                if piece:
                                    found = piece
                                    break
                        if not found:
                            found = json.loads(recognizer.FinalResult()).get("text", "").strip()
                    result = found or "__NO_SPEECH__"
                except ImportError:
                    # Si les bibliothèques Python de Vosk manquent, tente le moteur vocal Windows.
                    # Cela évite de bloquer le microphone juste parce que Vosk est incomplet.
                    if powershell:
                        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        result_path.unlink(missing_ok=True)
                        proc = subprocess.run(
                            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(STT_SCRIPT), str(result_path)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=26, creationflags=flags,
                        )
                        result = result_path.read_text(encoding="utf-8", errors="replace").strip() if result_path.exists() else ""
                        stderr = proc.stderr.decode("utf-8", errors="replace")[-700:] if proc.stderr else ""
                    else:
                        result = "__VOSK_NOT_INSTALLED__"
                except Exception as exc:
                    result = "__ERROR__|Reconnaissance Vosk : " + str(exc)
            elif powershell:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                result_path.unlink(missing_ok=True)
                proc = subprocess.run(
                    [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(STT_SCRIPT), str(result_path)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=26, creationflags=flags,
                )
                result = result_path.read_text(encoding="utf-8", errors="replace").strip() if result_path.exists() else ""
                stderr = proc.stderr.decode("utf-8", errors="replace")[-700:] if proc.stderr else ""
            else:
                result = "__NO_VOICE_ENGINE__"
        except subprocess.TimeoutExpired:
            result, stderr = "__TIMEOUT__", ""
        except Exception as exc:
            result, stderr = "__ERROR__|" + str(exc), ""
        finally:
            result_path.unlink(missing_ok=True)
        try:
            self.root.after(0, self._listen_finished, result, stderr)
        except tk.TclError:
            pass

    def _listen_finished(self, result: str, stderr: str):
        self.listen_busy = False
        from_voice_session = bool(self._listen_started_in_session)
        force_auto_send = bool(self.force_voice_auto_send)
        self.force_voice_auto_send = False
        self._listen_started_in_session = False
        for composer in (self.home_composer, self.chat_composer):
            composer["mic"].configure(state="normal", text="🎙")
        if from_voice_session and not self.voice_session_active:
            self.voice_status_var.set("Discussion vocale arrêtée")
            return
        if result == "__VOSK_NOT_INSTALLED__":
            if self.voice_session_active:
                self._end_voice_conversation(restore_status=False)
            self.speak_next_response = False
            self.voice_status_var.set("Vosk n’est pas installé")
            messagebox.showinfo(APP_TITLE, "Pour activer la dictée hors ligne, installe les dépendances Python : python -m pip install vosk sounddevice. Ajoute ensuite le modèle français Vosk dans le dossier models de VYNEXRuntime.", parent=self.root)
            return
        if result == "__NO_VOICE_ENGINE__":
            if self.voice_session_active:
                self._end_voice_conversation(restore_status=False)
            self.speak_next_response = False
            self.voice_status_var.set("Moteur vocal indisponible")
            messagebox.showinfo(APP_TITLE, "Installe Vosk avec son modèle français local, puis réessaie.", parent=self.root)
            return
        if result.startswith("__NO_FRENCH_RECOGNIZER__"):
            if self.voice_session_active:
                self._end_voice_conversation(restore_status=False)
            self.speak_next_response = False
            languages = result.split("|", 1)[1] if "|" in result else "aucune"
            self.voice_status_var.set("Reconnaissance française Windows indisponible")
            messagebox.showinfo(
                APP_TITLE,
                "La dictée hors ligne nécessite un moteur de reconnaissance vocale français installé dans Windows.\n\n"
                f"Langues détectées : {languages or 'aucune'}\n\n"
                "Tu peux déjà utiliser la lecture vocale. Pour activer la dictée, vérifie les paramètres Windows de langue et de reconnaissance vocale, ou nous pourrons ajouter Vosk en local.",
                parent=self.root,
            )
            return
        if result == "__NO_SPEECH__" or not result:
            if self.voice_session_active:
                self.voice_status_var.set("Discussion vocale active · je t'écoute…")
                self.root.after(350, self._continue_voice_conversation)
            else:
                self.speak_next_response = False
                self.voice_status_var.set("Aucune parole reconnue")
                messagebox.showinfo(APP_TITLE, "Aucune parole n'a été reconnue. Vérifie le microphone et réessaie.", parent=self.root)
            return
        if result == "__TIMEOUT__":
            if self.voice_session_active:
                self.voice_status_var.set("Discussion vocale active · je t'écoute…")
                self.root.after(350, self._continue_voice_conversation)
            else:
                self.speak_next_response = False
                self.voice_status_var.set("Délai d'écoute dépassé")
                messagebox.showinfo(APP_TITLE, "La dictée a dépassé le délai. Réessaie et parle juste après avoir cliqué sur Parler.", parent=self.root)
            return
        if result.startswith("__ERROR__|"):
            if self.voice_session_active:
                self._end_voice_conversation(restore_status=False)
            self.speak_next_response = False
            detail = result.split("|", 1)[1]
            self.voice_status_var.set("Erreur de dictée")
            messagebox.showerror(APP_TITLE, "La dictée vocale n'a pas pu démarrer. Vérifie les autorisations du microphone dans Windows.\n\n" + detail, parent=self.root)
            return
        composer = self.active_composer()
        target = composer["input"]
        existing = self._composer_text(composer)
        target.delete("1.0", "end")
        composer["placeholder_active"] = False
        target.configure(fg=TEXT)
        target.insert("1.0", (existing + " " if existing else "") + result)
        target.focus_set()
        self._refresh_composer_primary_state(composer["home"])
        if self.voice_session_active or force_auto_send or self.settings.get("voice_auto_send", True):
            self.voice_status_var.set("Texte reconnu · envoi automatique…")
            self.root.after(250, lambda: self.send_message(home=self.is_home))
        else:
            self.voice_status_var.set("Texte reconnu · vérifie puis envoie")

    # ---------------------------- plus/files ----------------------------
    def quick_test_prompt(self):
        self.quick_prompt("Réponds en français en deux phrases. Présente-toi et indique tes capacités locales.")
        self.send_message(home=self.is_home)

    # ---------------------------- saving/history/library ----------------------------
    def save_chat(self):
        if not bool(self.settings.get("save_history", True)):
            return
        if not self.current_chat_id or not self.current_turns:
            return
        first = next((t.get("text", "") for t in self.current_turns if t.get("role") == "Vous"), "Discussion")
        title = str(first).splitlines()[0][:58] or "Discussion"
        self.chats[self.current_chat_id] = {
            "id": self.current_chat_id,
            "title": title,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "turns": self.current_turns,
        }
        write_json(CHATS_FILE, self.chats)
        self._refresh_recent_list()

    def _refresh_recent_list(self):
        if not hasattr(self, "recent_list"):
            return
        self.recent_list.delete(0, "end")
        records = sorted(self.chats.values(), key=lambda x: x.get("updated", ""), reverse=True)[:12]
        self._recent_records = records
        for record in records:
            label = str(record.get("title", "Discussion"))
            if len(label) > 28:
                label = label[:25] + "…"
            self.recent_list.insert("end", label)

    def _open_recent_selection(self, _event=None):
        selected = self.recent_list.curselection()
        if selected and selected[0] < len(getattr(self, "_recent_records", [])):
            self._load_chat_record(self._recent_records[selected[0]])

    def _recent_context_menu(self, event):
        """Menu contextuel pour ouvrir ou supprimer une discussion récente."""
        if not self.recent_list.size():
            return "break"
        index = self.recent_list.nearest(event.y)
        if index < 0:
            return "break"
        self.recent_list.selection_clear(0, "end")
        self.recent_list.selection_set(index)
        self.recent_list.activate(index)
        menu = tk.Menu(
            self.root, tearoff=0, bg=PANEL, fg=TEXT,
            activebackground=PANEL_HOVER, activeforeground=TEXT,
            disabledforeground=MUTED, bd=0,
        )
        menu.add_command(label="Ouvrir la discussion", command=self._open_recent_selection)
        menu.add_separator()
        menu.add_command(
            label="Supprimer cette discussion…",
            command=self._delete_selected_recent_chat,
            foreground=ERROR,
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except tk.TclError:
                pass
        return "break"

    def _delete_selected_recent_chat(self, _event=None):
        selected = self.recent_list.curselection()
        records = getattr(self, "_recent_records", [])
        if selected and selected[0] < len(records):
            self._delete_chat_record(records[selected[0]], parent=self.root)
        else:
            messagebox.showinfo(APP_TITLE, "Sélectionne d’abord une discussion à supprimer.", parent=self.root)
        return "break" if _event is not None else None

    def _delete_chat_record(self, record, parent=None) -> bool:
        """Supprime une conversation choisie, en persistant le changement avant de l'oublier en mémoire."""
        parent = parent or self.root
        chat_id = str(record.get("id", ""))
        title = str(record.get("title", "Discussion")) or "Discussion"
        if not chat_id or chat_id not in self.chats:
            messagebox.showinfo(APP_TITLE, "Cette discussion n’existe plus dans l’historique.", parent=parent)
            self._refresh_recent_list()
            return False
        if chat_id == self.current_chat_id and (
            getattr(self, "busy", False)
            or getattr(self, "listen_busy", False)
            or getattr(self, "voice_session_active", False)
        ):
            messagebox.showwarning(
                APP_TITLE,
                "Une génération ou une session vocale est encore active dans cette discussion. Arrête-la avant de la supprimer.",
                parent=parent,
            )
            return False
        if not messagebox.askyesno(
            "Supprimer cette discussion ?",
            f"Supprimer définitivement « {title} » de l’historique enregistré sur cet appareil ?\n\n"
            "Cette action est irréversible. Les fichiers de la bibliothèque d’images ne sont pas supprimés.",
            parent=parent,
        ):
            return False

        remaining = dict(self.chats)
        removed = remaining.pop(chat_id, None)
        if removed is None:
            self._refresh_recent_list()
            return False
        try:
            write_json(CHATS_FILE, remaining)
        except Exception as exc:
            messagebox.showerror(
                APP_TITLE,
                f"La discussion n’a pas pu être supprimée du fichier d’historique :\n{exc}",
                parent=parent,
            )
            return False

        self.chats = remaining
        if chat_id == self.current_chat_id:
            # Important : réinitialiser l'identifiant et les tours empêche close()/save_chat()
            # de recréer par accident la conversation que l'utilisateur vient d'effacer.
            self.current_chat_id = str(uuid.uuid4())
            self.current_turns = []
            self.api_messages = [{"role": "system", "content": self._effective_system_prompt()}]
            self.last_assistant_answer = ""
            self.pending_images.clear()
            self.pending_files.clear()
            if hasattr(self, "transcript"):
                self._clear_transcript()
            for composer in (getattr(self, "home_composer", None), getattr(self, "chat_composer", None)):
                if composer and "input" in composer:
                    self._set_composer_placeholder(composer)
            self._refresh_attachment_previews()
            self.show_home()

        self._refresh_recent_list()
        self.status_var.set(f"Discussion supprimée : {title[:48]}")
        return True

    def search_chats(self):
        self.save_chat()
        query = simpledialog.askstring(APP_TITLE, "Rechercher dans les titres ou les messages :", parent=self.root)
        if not query:
            return
        q = query.casefold()
        found = []
        for rec in self.chats.values():
            title = str(rec.get("title", ""))
            turns = rec.get("turns", [])
            if q in title.casefold() or any(q in str(turn.get("text", "")).casefold() for turn in turns):
                found.append(rec)
        if not found:
            messagebox.showinfo(APP_TITLE, "Aucune discussion correspondante.", parent=self.root)
            return
        self._show_history_window(found)

    def open_history(self):
        self.save_chat()
        records = sorted(self.chats.values(), key=lambda x: x.get("updated", ""), reverse=True)
        self._show_history_window(records)

    def _show_history_window(self, records):
        # Copie locale : supprimer une ligne dans cette fenêtre ne modifie pas directement
        # la collection utilisée par d'autres éléments de l'interface.
        records = list(records)
        win = tk.Toplevel(self.root)
        win.title("Historique des discussions")
        win.configure(bg=BG)
        win.geometry("720x540")
        win.minsize(560, 420)
        win.transient(self.root)
        tk.Label(win, text="Historique des discussions", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(win, text="Double-clique pour ouvrir. Sélectionne une discussion pour l’ouvrir ou la supprimer.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9), wraplength=675, justify="left").pack(anchor="w", padx=18, pady=(0, 8))

        list_wrap = tk.Frame(win, bg=BG)
        list_wrap.pack(fill="both", expand=True, padx=18, pady=(4, 10))
        listing = tk.Listbox(
            list_wrap, bg=PANEL, fg=TEXT, selectbackground="#1A5A4B", selectforeground="#FFFFFF",
            relief="flat", bd=0, font=("Segoe UI", 11), activestyle="none",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        scrollbar = tk.Scrollbar(list_wrap, command=listing.yview, bg=PANEL, troughcolor=BG,
                                 activebackground=BORDER_HOVER, relief="flat", bd=0)
        listing.configure(yscrollcommand=scrollbar.set)
        listing.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        empty_hint = tk.Label(list_wrap, text="Aucune discussion enregistrée.", bg=PANEL, fg=MUTED,
                              font=("Segoe UI", 11), padx=20, pady=24)

        def refresh_window_list():
            listing.delete(0, "end")
            for item in records:
                listing.insert("end", f"{item.get('updated', '')}   ·   {item.get('title', 'Discussion')}")
            if records:
                empty_hint.pack_forget()
                listing.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
            else:
                listing.pack_forget()
                scrollbar.pack_forget()
                empty_hint.pack(fill="both", expand=True)

        def selected_record():
            selection = listing.curselection()
            if not selection or selection[0] >= len(records):
                messagebox.showinfo(APP_TITLE, "Sélectionne d’abord une discussion.", parent=win)
                return None, None
            index = selection[0]
            return index, records[index]

        def open_selected(_event=None):
            index, record = selected_record()
            if record is not None:
                self._load_chat_record(record)
                win.destroy()
            return "break" if _event is not None else None

        def delete_selected():
            index, record = selected_record()
            if record is None:
                return
            if self._delete_chat_record(record, parent=win):
                records.pop(index)
                refresh_window_list()
                if records:
                    next_index = min(index, len(records) - 1)
                    listing.selection_set(next_index)
                    listing.activate(next_index)
                    listing.see(next_index)

        refresh_window_list()
        listing.bind("<Double-Button-1>", open_selected)
        listing.bind("<Return>", open_selected)
        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=18, pady=(0, 18))
        self._button(actions, "Ouvrir la sélection", open_selected, primary=True, compact=True).pack(side="left", padx=(0, 8))
        delete_button = tk.Button(
            actions, text="Supprimer la sélection", command=delete_selected,
            bg="#48202B", fg=ERROR, activebackground="#622839", activeforeground="#FFFFFF",
            disabledforeground=MUTED, relief="flat", bd=0, highlightthickness=1,
            highlightbackground="#79404E", highlightcolor=ERROR, cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=12, pady=8,
        )
        delete_button.pack(side="left")
        self._button(actions, "Fermer", win.destroy, compact=True).pack(side="right")

    def _load_chat_record(self, record):
        self.save_chat()
        self.current_chat_id = record.get("id", str(uuid.uuid4()))
        self.current_turns = list(record.get("turns", []))
        self.last_assistant_answer = next((str(turn.get("text", "")) for turn in reversed(self.current_turns) if turn.get("role") in ("MonIA", "VYNEX")), "")
        self.api_messages = [{"role": "system", "content": self._effective_system_prompt()}]
        for turn in self.current_turns:
            text = str(turn.get("text", ""))
            role = "user" if turn.get("role") == "Vous" else "assistant"
            self.api_messages.append({"role": role, "content": text})
        self.pending_images.clear()
        self.pending_files.clear()
        self._refresh_attachment_previews()
        self.render_turns()
        self._refresh_recent_list()

    def open_image_studio(self):
        """Studio de création relié à une API locale AUTOMATIC1111/Forge, sans prétendre simuler une génération."""
        self._close_plus_menu()
        win = tk.Toplevel(self.root)
        win.title("Studio visuel · VYNEX")
        win.configure(bg=BG)
        win.geometry("760x700")
        win.minsize(650, 600)
        win.transient(self.root)

        header = tk.Frame(win, bg=BG)
        header.pack(fill="x", padx=24, pady=(22, 8))
        tk.Label(header, text="STUDIO VISUEL", bg=BG, fg=ACCENT_HOVER,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(header, text="Donne forme à ton idée", bg=BG, fg=TEXT,
                 font=("Segoe UI", 23, "bold")).pack(anchor="w", pady=(3, 2))
        tk.Label(header, text="Génération locale via AUTOMATIC1111 / Forge si un moteur et un modèle d’image sont installés.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10), wraplength=690, justify="left").pack(anchor="w")

        body = tk.Frame(win, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=(10, 12))
        tk.Label(body, text="DESCRIPTION DE L’IMAGE", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(15, 6))
        prompt = tk.Text(body, height=5, wrap="word", bg="#0B1727", fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, font=("Segoe UI", 11), padx=10, pady=9,
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
        prompt.pack(fill="x", padx=16)
        prompt.insert("1.0", "Un robot assistant futuriste élégant, bleu nuit et menthe, éclairage cinématographique, détails fins, composition professionnelle")

        tk.Label(body, text="ÉLÉMENTS À ÉVITER (FACULTATIF)", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 5))
        negative = tk.Entry(body, bg="#0B1727", fg=TEXT, insertbackground=TEXT, relief="flat",
                            font=("Segoe UI", 10), highlightthickness=1, highlightbackground=BORDER)
        negative.pack(fill="x", padx=16, ipady=8)
        negative.insert(0, "flou, basse qualité, texte déformé, artefacts")

        options = tk.Frame(body, bg=PANEL)
        options.pack(fill="x", padx=16, pady=(13, 6))
        tk.Label(options, text="Format", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        size_var = tk.StringVar(value="Carré · 512 × 512")
        sizes = {"Carré · 512 × 512": (512, 512), "Paysage · 768 × 512": (768, 512), "Portrait · 512 × 768": (512, 768)}
        size_menu = tk.OptionMenu(options, size_var, *sizes.keys())
        size_menu.configure(bg=PANEL_HOVER, fg=TEXT, activebackground=PANEL_ACTIVE, activeforeground=TEXT,
                            relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER,
                            font=("Segoe UI", 9), padx=8, pady=4)
        size_menu["menu"].configure(bg=PANEL, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        size_menu.pack(side="left", padx=(9, 18))
        tk.Label(options, text="Qualité", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        steps_var = tk.IntVar(value=20)
        step_spin = tk.Spinbox(options, from_=10, to=30, increment=2, textvariable=steps_var, width=5,
                               bg="#0B1727", fg=TEXT, buttonbackground=PANEL_HOVER, relief="flat",
                               font=("Segoe UI", 10), insertbackground=TEXT)
        step_spin.pack(side="left", padx=(8, 0))
        tk.Label(body, text="Les options de taille et d’itérations influencent le temps et la mémoire utilisés.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=(2, 12))

        status = tk.Label(body, text="Moteur d’image : non vérifié", bg=PANEL, fg=WARNING,
                          font=("Segoe UI", 9, "bold"), anchor="w", wraplength=670, justify="left")
        status.pack(fill="x", padx=16, pady=(0, 9))

        footer = tk.Frame(win, bg=BG)
        footer.pack(fill="x", padx=24, pady=(0, 20))

        def generate():
            description = prompt.get("1.0", "end-1c").strip()
            if self.busy:
                messagebox.showinfo(APP_TITLE, "Termine d’abord la réponse en cours : cela évite de saturer la mémoire du PC.", parent=win)
                return
            if not description:
                messagebox.showinfo(APP_TITLE, "Décris d’abord l’image à créer.", parent=win)
                return
            if self.image_generation_busy:
                messagebox.showinfo(APP_TITLE, "Une génération d’image est déjà en cours.", parent=win)
                return
            try:
                steps = max(10, min(30, int(steps_var.get())))
            except (ValueError, tk.TclError):
                steps = 20
            width, height = sizes.get(size_var.get(), (512, 512))
            negative_prompt = negative.get().strip()
            status.configure(text="Connexion au moteur d’image local…", fg=BLUE)
            generate_button.configure(state="disabled", text="Génération…")
            self.image_generation_busy = True

            def worker():
                try:
                    payload = {
                        "prompt": description,
                        "negative_prompt": negative_prompt,
                        "width": width, "height": height,
                        "steps": steps, "cfg_scale": 7,
                        "sampler_name": "DPM++ 2M Karras",
                        "batch_size": 1, "n_iter": 1,
                        "restore_faces": False, "save_images": False,
                    }
                    req = urllib.request.Request(
                        "http://127.0.0.1:7860/sdapi/v1/txt2img",
                        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=600) as response:
                        result = json.loads(response.read().decode("utf-8", errors="replace"))
                    images = result.get("images") or []
                    if not images:
                        raise RuntimeError("Le moteur n’a renvoyé aucune image.")
                    encoded_image = images[0]
                    if isinstance(encoded_image, str) and encoded_image.startswith("data:") and "," in encoded_image:
                        encoded_image = encoded_image.split(",", 1)[1]
                    raw = base64.b64decode(encoded_image)
                    target = IMAGE_DIR / f"VYNEX_image_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}.png"
                    target.write_bytes(raw)
                    try:
                        self.root.after(0, on_success, target, width, height, description)
                    except tk.TclError:
                        pass
                except urllib.error.URLError as exc:
                    detail = (
                        "Moteur d’image local introuvable sur http://127.0.0.1:7860. "
                        "VYNEX ne dispose pas actuellement d’un modèle de génération d’images intégré. "
                        "Pour générer réellement des images, il faut installer et lancer AUTOMATIC1111/Forge "
                        "avec un modèle compatible et son API activée. Ces modèles sont généralement bien "
                        "plus volumineux que la limite de 2 Go de ton projet."
                    )
                    try:
                        self.root.after(0, on_error, detail)
                    except tk.TclError:
                        pass
                except Exception as exc:
                    try:
                        self.root.after(0, on_error, f"La génération a échoué : {exc}")
                    except tk.TclError:
                        pass

            def on_success(path, width, height, original_prompt):
                self.image_generation_busy = False
                if not win.winfo_exists():
                    return
                status.configure(text=f"Image créée : {width} × {height} · enregistrée dans la bibliothèque", fg=ACCENT_HOVER)
                generate_button.configure(state="normal", text="Générer l’image")
                self.current_turns.append({
                    "role": "VYNEX",
                    "text": f"Image générée localement ({width} × {height}).\n\nPrompt : {original_prompt}",
                    "image_paths": [str(path)],
                    "time": datetime.now().isoformat(timespec="seconds"),
                })
                self.render_turns()
                self.save_chat()
                self.status_var.set("Image créée · conservée localement")

            def on_error(detail):
                self.image_generation_busy = False
                if win.winfo_exists():
                    status.configure(text="Moteur d’image indisponible ou erreur de génération.", fg=ERROR)
                    generate_button.configure(state="normal", text="Générer l’image")
                    messagebox.showwarning(APP_TITLE, detail, parent=win)

            threading.Thread(target=worker, daemon=True).start()

        generate_button = self._button(footer, "✧  Générer l’image", generate, primary=True)
        generate_button.pack(side="right")
        self._button(footer, "Ouvrir la bibliothèque", lambda: (win.destroy(), self.open_library())).pack(side="left")
        self._button(footer, "Fermer", win.destroy, compact=True).pack(side="left", padx=8)

    def open_library(self):
        win = tk.Toplevel(self.root)
        win.title("Bibliothèque d'images")
        win.configure(bg=BG)
        win.geometry("740x540")
        tk.Label(win, text="Bibliothèque d'images", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(win, text=str(IMAGE_DIR), bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 8))
        listing = tk.Listbox(win, bg=PANEL, fg=TEXT, selectbackground="#1A5A4B", selectforeground=TEXT,
                             relief="flat", bd=0, font=("Segoe UI", 11), activestyle="none")
        listing.pack(fill="both", expand=True, padx=18, pady=8)
        files = sorted([p for p in IMAGE_DIR.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files:
            listing.insert("end", path.name)
        def open_selected(_event=None):
            indices = listing.curselection()
            if not indices:
                messagebox.showinfo(APP_TITLE, "Sélectionne une image.", parent=win)
                return
            try:
                open_path_with_default_app(files[indices[0]])
            except Exception as exc:
                messagebox.showerror(APP_TITLE, str(exc), parent=win)
        listing.bind("<Double-Button-1>", open_selected)
        buttons = tk.Frame(win, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 18))
        self._button(buttons, "Ouvrir l'image", open_selected, primary=True).pack(side="left")
        self._button(buttons, "Ouvrir le dossier", lambda: open_path_with_default_app(IMAGE_DIR)).pack(side="left", padx=8)
        self._button(buttons, "Ajouter au message", lambda: (win.destroy(), self.attach_images())).pack(side="right")

    # ---------------------------- reminder/settings ----------------------------
    def add_reminder(self):
        title = simpledialog.askstring(APP_TITLE, "Que veux-tu te rappeler ?", parent=self.root)
        if not title:
            return
        minutes = simpledialog.askinteger(APP_TITLE, "Dans combien de minutes afficher le rappel ? (1 à 10080)",
                                          parent=self.root, minvalue=1, maxvalue=10080)
        if not minutes:
            return
        self.root.after(minutes * 60_000, lambda t=title: self.show_reminder(t))
        self.status_var.set(f"Rappel dans {minutes} minute(s)")
        messagebox.showinfo(APP_TITLE, f"Rappel programmé : {title}\nVYNEX doit rester ouvert pour l'afficher.", parent=self.root)

    def show_reminder(self, title):
        win = tk.Toplevel(self.root)
        win.title("Rappel VYNEX")
        win.configure(bg=PANEL)
        win.attributes("-topmost", True)
        win.geometry("380x190")
        tk.Label(win, text="Rappel VYNEX", bg=PANEL, fg=ACCENT_HOVER, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(18, 8))
        tk.Label(win, text=title, bg=PANEL, fg=TEXT, wraplength=335, justify="left", font=("Segoe UI", 12)).pack(anchor="w", padx=18, pady=(0, 16))
        row = tk.Frame(win, bg=PANEL)
        row.pack(fill="x", padx=18)
        self._button(row, "Ignorer", win.destroy).pack(side="right")
        self._button(row, "Ouvrir VYNEX", lambda: (self.root.deiconify(), self.root.lift(), win.destroy()), primary=True).pack(side="right", padx=8)

    def open_settings(self):
        """Centre de paramètres avec catégories séparées et options reliées au comportement réel."""
        self._close_plus_menu()
        win = tk.Toplevel(self.root)
        win.title("Paramètres · VYNEX")
        win.configure(bg=BG)
        win.geometry("980x750")
        win.minsize(840, 620)
        win.transient(self.root)

        shell = tk.Frame(win, bg=BG)
        shell.pack(fill="both", expand=True)
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(1, weight=1)

        nav = tk.Frame(shell, bg=SIDEBAR, width=205, highlightthickness=1, highlightbackground=BORDER)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_propagate(False)
        tk.Label(nav, text="VYNEX", bg=SIDEBAR, fg=TEXT, font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=18, pady=(22, 2))
        tk.Label(nav, text="CENTRE DE RÉGLAGES", bg=SIDEBAR, fg=ACCENT_HOVER,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(0, 22))

        content = tk.Frame(shell, bg=BG)
        content.grid(row=0, column=1, sticky="nsew")
        content.rowconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)
        header = tk.Frame(content, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 12))
        header.columnconfigure(0, weight=1)
        page_title = tk.Label(header, text="Général", bg=BG, fg=TEXT, font=("Segoe UI", 20, "bold"))
        page_title.grid(row=0, column=0, sticky="w")
        page_subtitle = tk.Label(header, text="Personnalise les réponses de VYNEX.", bg=BG, fg=MUTED,
                                 font=("Segoe UI", 10), justify="left", wraplength=680)
        page_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        page_host = tk.Frame(content, bg=BG)
        page_host.grid(row=1, column=0, sticky="nsew", padx=(18, 10))
        page_host.rowconfigure(0, weight=1)
        page_host.columnconfigure(0, weight=1)
        footer = tk.Frame(content, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 14))

        controls = {}
        pages = {}
        nav_buttons = {}
        descriptions = {
            "Général": "Définis la langue, le style de réponse et tes consignes personnelles.",
            "Personnalisation": "Adapte les couleurs et la lisibilité de la conversation.",
            "Voix": "Configure la lecture à voix haute et le comportement de la dictée.",
            "Modèle IA": "Choisis le modèle local et règle la génération des réponses.",
            "Images & fichiers": "Règle le nombre d'images analysées et consulte les formats compatibles.",
            "Données & confidentialité": "Contrôle l'enregistrement local des conversations et des données.",
            "Diagnostic": "Vérifie la disponibilité des moteurs locaux et de la voix.",
        }

        def make_card(parent, title, detail=""):
            card = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=4, pady=(0, 12))
            tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(13, 2))
            if detail:
                tk.Label(card, text=detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
                         wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 8))
            return card

        def add_label(parent, label, detail=None):
            tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(7, 3))
            if detail:
                tk.Label(parent, text=detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
                         wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 3))

        def styled_option(parent, variable, options):
            menu = tk.OptionMenu(parent, variable, *options)
            menu.configure(bg=PANEL_HOVER, fg=TEXT, activebackground=PANEL_ACTIVE, activeforeground=TEXT,
                           relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER,
                           font=("Segoe UI", 10), padx=9, pady=5, cursor="hand2")
            menu["menu"].configure(bg=PANEL, fg=TEXT, activebackground=ACCENT, activeforeground=BG,
                                   font=("Segoe UI", 10), relief="flat", bd=0)
            menu.pack(fill="x", padx=16, pady=(0, 9))
            return menu

        def check_row(parent, label, variable, detail=None):
            row = tk.Frame(parent, bg=PANEL)
            row.pack(fill="x", padx=14, pady=5)
            check = tk.Checkbutton(row, text=label, variable=variable, bg=PANEL, fg=TEXT,
                                   activebackground=PANEL, activeforeground=TEXT, selectcolor=SIDEBAR,
                                   font=("Segoe UI", 10), relief="flat", bd=0, cursor="hand2")
            check.pack(anchor="w")
            if detail:
                tk.Label(row, text=detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
                         wraplength=640, justify="left").pack(anchor="w", padx=(27, 0), pady=(0, 2))
            return check

        # Each section is independently scrollable; this stays usable on smaller screens.
        def create_page(key, builder):
            holder = tk.Frame(page_host, bg=BG)
            holder.grid(row=0, column=0, sticky="nsew")
            holder.rowconfigure(0, weight=1)
            holder.columnconfigure(0, weight=1)
            canvas = tk.Canvas(holder, bg=BG, highlightthickness=0, bd=0)
            scroll = tk.Scrollbar(holder, orient="vertical", command=canvas.yview, bg=PANEL,
                                  troughcolor=BG, activebackground=BORDER_HOVER, relief="flat", bd=0)
            canvas.configure(yscrollcommand=scroll.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            scroll.grid(row=0, column=1, sticky="ns")
            inner = tk.Frame(canvas, bg=BG)
            inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda _e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.bind("<Configure>", lambda e, c=canvas, item=inner_id: c.itemconfigure(item, width=e.width))
            canvas.bind("<MouseWheel>", lambda e, c=canvas: c.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            builder(inner)
            pages[key] = holder

        # General
        def build_general(parent):
            card = make_card(parent, "Langue des réponses", "Cette préférence concerne les réponses de l'IA, pas la langue des menus Windows.")
            controls["language"] = tk.StringVar(value=str(self.settings.get("response_language", "Français")))
            styled_option(card, controls["language"], ["Français", "English", "Auto (langue du message)"])
            card = make_card(parent, "Style des réponses", "Choisis la quantité de détails attendue par défaut.")
            controls["style"] = tk.StringVar(value=str(self.settings.get("response_style", "Équilibré")))
            styled_option(card, controls["style"], ["Concis", "Équilibré", "Détaillé"])
            card = make_card(parent, "Consignes personnelles", "VYNEX ajoutera ces consignes aux prochaines demandes. Ne mets pas de mots de passe ni d'informations sensibles.")
            instructions = tk.Text(card, height=5, wrap="word", bg=CHAT_PANEL, fg=TEXT, insertbackground=TEXT,
                                   selectbackground="#1A5A4B", relief="flat", bd=0, font=("Segoe UI", 10), padx=10, pady=9)
            instructions.pack(fill="x", padx=16, pady=(0, 15))
            instructions.insert("1.0", str(self.settings.get("custom_instructions", "")))
            controls["instructions"] = instructions

        # Personalisation
        def build_personalization(parent):
            card = make_card(parent, "Palette de couleurs", "Les changements de palette seront appliqués après le redémarrage de VYNEX, afin d'éviter une interface partiellement recolorée.")
            theme_names = {"Aurora · menthe": "aurora", "Ocean · glacier": "ocean", "Violet · néon doux": "violet", "Emerald · forêt": "emerald"}
            reverse_names = {v: k for k, v in theme_names.items()}
            controls["theme_names"] = theme_names
            controls["theme"] = tk.StringVar(value=reverse_names.get(str(self.settings.get("theme", "aurora")), "Aurora · menthe"))
            styled_option(card, controls["theme"], list(theme_names.keys()))
            tk.Label(card, text="Aperçu des accents :  ● Menthe   ● Glacier   ● Lavande", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 13))
            card = make_card(parent, "Taille du texte du chat", "Le réglage est appliqué immédiatement et conservé pour les prochaines ouvertures.")
            controls["font_size"] = tk.IntVar(value=max(10, min(16, int(self.settings.get("chat_font_size", 12)))))
            scale = tk.Scale(card, from_=10, to=16, orient="horizontal", variable=controls["font_size"],
                             bg=PANEL, fg=TEXT, activebackground=ACCENT, troughcolor=SIDEBAR,
                             highlightthickness=0, showvalue=True, resolution=1, font=("Segoe UI", 9),
                             command=lambda value: self._apply_chat_font_size(int(float(value))))
            scale.pack(fill="x", padx=16, pady=(0, 14))

            card = make_card(parent, "Animations de l’interface", "Animations vectorielles légères, sans téléchargement ni bibliothèque supplémentaire.")
            controls["animations"] = tk.BooleanVar(value=bool(self.settings.get("animations_enabled", True)))
            check_row(card, "Activer les animations réalistes", controls["animations"],
                      "Désactive cette option pour réduire davantage l’activité graphique.")

        # Voice
        def build_voice(parent):
            card = make_card(parent, "Lecture vocale", "Utilise la synthèse vocale de Windows quand elle est disponible.")
            controls["auto_speak"] = tk.BooleanVar(value=bool(self.settings.get("auto_speak", False)))
            check_row(card, "Lire automatiquement les réponses de VYNEX", controls["auto_speak"])
            controls["speak_rate"] = tk.IntVar(value=max(-5, min(5, int(self.settings.get("speak_rate", 0)))))
            add_label(card, "Vitesse de lecture", "De -5 (plus lent) à +5 (plus rapide).")
            rate = tk.Scale(card, from_=-5, to=5, orient="horizontal", variable=controls["speak_rate"],
                            bg=PANEL, fg=TEXT, activebackground=ACCENT, troughcolor=SIDEBAR,
                            highlightthickness=0, showvalue=True, resolution=1, font=("Segoe UI", 9))
            rate.pack(fill="x", padx=16, pady=(0, 12))
            self._button(card, "▶  Tester la voix", self.test_voice, compact=True).pack(anchor="w", padx=16, pady=(0, 14))
            card = make_card(parent, "Dictée vocale", "Le microphone utilise la reconnaissance française Windows ou le petit modèle Vosk s'il est déjà installé.")
            controls["voice_auto_send"] = tk.BooleanVar(value=bool(self.settings.get("voice_auto_send", True)))
            check_row(card, "Envoyer automatiquement après la dictée", controls["voice_auto_send"],
                      "Désactive cette option pour relire et modifier le texte reconnu avant l'envoi.")

        # AI model
        def build_ai(parent):
            card = make_card(parent, "Moteur de conversation", "Adresse locale d'Ollama, généralement http://127.0.0.1:11434. Ne change-la que si ton serveur écoute ailleurs.")
            add_label(card, "Adresse du serveur")
            controls["chat_url"] = tk.Entry(card, bg=CHAT_PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
            controls["chat_url"].pack(fill="x", padx=16, pady=(0, 9), ipady=7)
            controls["chat_url"].insert(0, str(self.settings.get("chat_url", OLLAMA_URL)))
            add_label(card, "Nom du modèle", "Exemple : llama3.2:3b. Le modèle doit déjà être installé localement.")
            controls["model"] = tk.Entry(card, bg=CHAT_PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
            controls["model"].pack(fill="x", padx=16, pady=(0, 12), ipady=7)
            controls["model"].insert(0, str(self.settings.get("chat_model", DEFAULT_CHAT_MODEL)))
            card = make_card(parent, "Qualité et longueur", "Une température basse est plus régulière. Les réponses longues peuvent prendre davantage de temps et de mémoire.")
            add_label(card, "Créativité / température (0,0 à 1,0)")
            controls["temperature"] = tk.DoubleVar(value=max(0.0, min(1.0, float(self.settings.get("temperature", 0.25)))))
            tk.Scale(card, from_=0, to=1, resolution=0.05, orient="horizontal", variable=controls["temperature"],
                     bg=PANEL, fg=TEXT, activebackground=ACCENT, troughcolor=SIDEBAR, highlightthickness=0,
                     showvalue=True, font=("Segoe UI", 9)).pack(fill="x", padx=16, pady=(0, 10))
            add_label(card, "Longueur maximale de réponse")
            controls["max_tokens"] = tk.StringVar(value=str(self.settings.get("max_tokens", 512)))
            styled_option(card, controls["max_tokens"], ["128", "256", "384", "512", "768", "1024"])
            controls["deep_mode"] = tk.BooleanVar(value=bool(self.deep_mode))
            check_row(card, "Activer le mode Analyser par défaut", controls["deep_mode"],
                      "Ajoute des consignes pour obtenir des réponses plus approfondies et structurées. Cela ne change pas la puissance du modèle installé.")
            self._button(card, "⌕  Tester la connexion au chat local", self.test_ollama_chat, compact=True).pack(anchor="w", padx=16, pady=(0, 14))

        # Vision & attachments
        def build_vision(parent):
            card = make_card(parent, "Analyse des images", "VYNEX peut joindre plusieurs images à un message. Réduire ce nombre aide à préserver la mémoire disponible sur un PC de 8 Go de RAM.")
            controls["vision_max_images"] = tk.StringVar(value=str(max(1, min(4, int(self.settings.get("vision_max_images", 4))))))
            add_label(card, "Nombre maximal d'images analysées par message")
            styled_option(card, controls["vision_max_images"], ["1", "2", "3", "4"])
            tk.Label(card, text="Formats pris en charge : PNG, JPG, JPEG, WEBP, BMP et GIF. La bibliothèque d'images reste locale.",
                     bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 14))
            card = make_card(parent, "Fichiers texte et code", "Les fichiers joints sont lus comme du texte pour contextualiser une question. VYNEX ne les exécute pas automatiquement.")
            tk.Label(card, text="Formats courants : TXT, MD, CSV, JSON, PY, HTML, CSS, JS et LOG.",
                     bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 14))

        # Data & privacy
        def clear_saved_history():
            if not messagebox.askyesno("Effacer l'historique", "Supprimer toutes les conversations enregistrées localement ? Cette action est irréversible.", parent=win):
                return
            self.chats = {}
            write_json(CHATS_FILE, self.chats)
            self._refresh_recent_list()
            messagebox.showinfo("Historique effacé", "Les conversations enregistrées ont été supprimées.", parent=win)

        def build_data(parent):
            card = make_card(parent, "Historique local", "Les conversations sont conservées dans le profil Windows local de VYNEX, pas envoyées à un compte en ligne par cette application.")
            controls["save_history"] = tk.BooleanVar(value=bool(self.settings.get("save_history", True)))
            check_row(card, "Enregistrer les conversations sur cet ordinateur", controls["save_history"],
                      "Si désactivé, les prochaines conversations ne seront pas ajoutées à l'historique enregistré. Les anciennes restent présentes jusqu'à leur suppression.")
            self._button(card, "Supprimer tout l'historique enregistré…", clear_saved_history, compact=True).pack(anchor="w", padx=16, pady=(8, 14))
            card = make_card(parent, "Autorisations facultatives", "VYNEX ne demande pas le microphone ni une capture d’écran au démarrage. Chaque accès est demandé lorsqu’une fonction le nécessite. Le système d’exploitation peut également bloquer cet accès.")

            def add_permission_row(key, label, detail):
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill="x", padx=16, pady=(4, 8))
                tk.Label(row, text=label, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w")
                status_label = tk.Label(
                    row,
                    text="Autorisation mémorisée" if self._permission_grants().get(key) is True else "Non autorisée / demande au premier usage",
                    bg=PANEL, fg=ACCENT_HOVER if self._permission_grants().get(key) is True else MUTED,
                    font=("Segoe UI", 9),
                )
                status_label.pack(anchor="w", pady=(1, 3))
                tk.Label(row, text=detail, bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=610, justify="left").pack(anchor="w", pady=(0, 5))
                actions = tk.Frame(row, bg=PANEL)
                actions.pack(anchor="w")

                def refresh_status():
                    granted = self._permission_grants().get(key) is True
                    status_label.configure(
                        text="Autorisation mémorisée" if granted else "Non autorisée / demande au premier usage",
                        fg=ACCENT_HOVER if granted else MUTED,
                    )

                self._button(actions, "Demander l’autorisation", lambda k=key: (self._ensure_feature_permission(k, force_prompt=True), refresh_status()), compact=True).pack(side="left", padx=(0, 7))
                self._button(actions, "Révoquer", lambda k=key: (self._revoke_feature_permission(k), refresh_status()), compact=True).pack(side="left")

            add_permission_row("microphone", "Microphone / dictée", PERMISSION_DESCRIPTIONS["microphone"])
            add_permission_row("screen_capture", "Capture d’écran", PERMISSION_DESCRIPTIONS["screen_capture"])

            card = make_card(parent, "Conditions et politique de confidentialité", "Consulte les informations sur les résultats IA, les traitements locaux, les autorisations facultatives et les composants tiers.")
            row = tk.Frame(card, bg=PANEL)
            row.pack(fill="x", padx=16, pady=(3, 14))
            self._button(row, "Lire les conditions d’utilisation", lambda: self._show_policy_document("Conditions d’utilisation · VYNEX", TERMS_TEXT), compact=True).pack(side="left", padx=(0, 7))
            self._button(row, "Lire la confidentialité", lambda: self._show_policy_document("Confidentialité · VYNEX", PRIVACY_TEXT), compact=True).pack(side="left")

            card = make_card(parent, "Pièces jointes", "Les images et captures peuvent rester dans le dossier local même après l’effacement de l’historique. Supprime-les aussi depuis la bibliothèque locale ou ce dossier si nécessaire.")
            tk.Label(card, text=str(IMAGE_DIR), bg=PANEL, fg=ACCENT_HOVER, font=("Consolas", 9), wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 13))

        # Diagnostics
        def build_diagnostics(parent):
            card = make_card(parent, "État des moteurs", "Les tests vérifient l’accès aux services configurés ; ils n’installent rien et ne téléchargent aucun modèle.")
            vision_ok = ENGINE_EXE.is_file() and MODEL_PATH.is_file() and MMPROJ_PATH.is_file()
            chat_url = str(self.settings.get("chat_url", OLLAMA_URL) or OLLAMA_URL)
            rows = [
                ("Conversation Ollama", "Adresse : " + chat_url),
                ("Modèle configuré", str(self.settings.get("chat_model", DEFAULT_CHAT_MODEL))),
                ("Analyse d'images", "Fichiers présents" if vision_ok else "Fichiers du moteur ou du modèle à vérifier"),
                ("Reconnaissance Vosk", "Modèle français détecté" if find_vosk_model_dir() else "Modèle Vosk non détecté ; reconnaissance Windows éventuelle"),
                ("Synthèse vocale", "Windows: System.Speech ; macOS: say ; Linux: espeak/spd-say si installés"),
                ("Conditions", "Acceptées" if self.settings.get("accepted_legal_notice_version") == LEGAL_NOTICE_VERSION else "À examiner au prochain démarrage"),
            ]
            for label, value in rows:
                line = tk.Frame(card, bg=PANEL)
                line.pack(fill="x", padx=16, pady=4)
                tk.Label(line, text=label, bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w")
                tk.Label(line, text=value, bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=640, justify="left").pack(anchor="w", pady=(1, 2))
            row = tk.Frame(card, bg=PANEL)
            row.pack(fill="x", padx=16, pady=(10, 14))
            self._button(row, "Tester le chat", self.test_ollama_chat, compact=True).pack(side="left", padx=(0, 7))
            self._button(row, "Tester la vision", self.test_server, compact=True).pack(side="left", padx=(0, 7))
            self._button(row, "Tester la voix", self.test_voice, compact=True).pack(side="left")

        creators = {
            "Général": build_general,
            "Personnalisation": build_personalization,
            "Voix": build_voice,
            "Modèle IA": build_ai,
            "Images & fichiers": build_vision,
            "Données & confidentialité": build_data,
            "Diagnostic": build_diagnostics,
        }
        for key, builder in creators.items():
            create_page(key, builder)

        def show_section(name):
            for key, page in pages.items():
                if key == name:
                    page.tkraise()
            page_title.configure(text=name)
            page_subtitle.configure(text=descriptions[name])
            for key, button in nav_buttons.items():
                active = key == name
                button.configure(bg=PANEL_ACTIVE if active else SIDEBAR,
                                 fg=ACCENT_HOVER if active else TEXT,
                                 highlightbackground=ACCENT if active else SIDEBAR)

        for name in creators:
            btn = tk.Button(nav, text=name, anchor="w", command=lambda n=name: show_section(n),
                            bg=SIDEBAR, fg=TEXT, activebackground=PANEL_HOVER, activeforeground=TEXT,
                            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=14, pady=10,
                            highlightthickness=1, highlightbackground=SIDEBAR, cursor="hand2")
            btn.pack(fill="x", padx=9, pady=2)
            nav_buttons[name] = btn
        tk.Label(nav, text="RÉGLAGES LOCAUX", bg=SIDEBAR, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side="bottom", anchor="w", padx=16, pady=16)

        def save_settings():
            try:
                temp = float(controls["temperature"].get())
                tokens = int(controls["max_tokens"].get())
                font_size = int(controls["font_size"].get())
                speak_rate = int(controls["speak_rate"].get())
                model = controls["model"].get().strip()
                base_url = controls["chat_url"].get().strip().rstrip("/")
                custom = controls["instructions"].get("1.0", "end-1c").strip()
                if not 0 <= temp <= 1:
                    raise ValueError("La température doit être comprise entre 0 et 1.")
                if tokens not in (128, 256, 384, 512, 768, 1024):
                    raise ValueError("Choisis une longueur de réponse proposée dans la liste.")
                if not 10 <= font_size <= 16:
                    raise ValueError("La taille du texte doit être comprise entre 10 et 16.")
                if not -5 <= speak_rate <= 5:
                    raise ValueError("La vitesse de voix doit être comprise entre -5 et +5.")
                if not model or any(ch.isspace() for ch in model):
                    raise ValueError("Le nom du modèle doit être un identifiant sans espace, par exemple llama3.2:3b.")
                if not (base_url.startswith("http://") or base_url.startswith("https://")):
                    raise ValueError("L'adresse du serveur doit commencer par http:// ou https://.")
                parsed_endpoint = urlparse(base_url)
                if not parsed_endpoint.hostname:
                    raise ValueError("L'adresse du serveur doit contenir un nom d’hôte valide.")
                endpoint_is_local = parsed_endpoint.hostname.casefold() in {"localhost", "127.0.0.1", "::1"}
                approved_remote_endpoint = ""
                if not endpoint_is_local:
                    already_approved = self.settings.get("approved_remote_endpoint") == base_url
                    if not already_approved:
                        if parsed_endpoint.scheme == "http":
                            message = (
                                f"Le serveur {parsed_endpoint.hostname} n’est pas local. Les messages, le contexte et le texte transmis au moteur peuvent quitter cet appareil. "
                                "La connexion HTTP ne chiffre pas le trafic ; préfère HTTPS pour un service distant.\n\n"
                                "Veux-tu vraiment enregistrer cette adresse et mémoriser ton accord pour elle ?"
                            )
                        else:
                            message = (
                                f"Le serveur {parsed_endpoint.hostname} n’est pas local. Les messages, le contexte et le texte transmis au moteur peuvent quitter cet appareil. "
                                "Vérifie que tu fais confiance à ce service et que tu as le droit d’y transmettre ces informations.\n\n"
                                "Veux-tu enregistrer cette adresse et mémoriser ton accord pour elle ?"
                            )
                        if not messagebox.askyesno("Attention : serveur externe", message, parent=win):
                            return
                    approved_remote_endpoint = base_url
                if len(custom) > 2000:
                    raise ValueError("Les consignes personnelles sont limitées à 2 000 caractères.")
            except (ValueError, KeyError) as exc:
                messagebox.showwarning("Paramètres VYNEX", str(exc), parent=win)
                return

            old_theme = str(self.settings.get("theme", "aurora"))
            selected_theme = controls["theme_names"][controls["theme"].get()]
            self.settings.update({
                "chat_model": model,
                "chat_url": base_url,
                "approved_remote_endpoint": approved_remote_endpoint,
                "temperature": temp,
                "max_tokens": tokens,
                "auto_speak": bool(controls["auto_speak"].get()),
                "speak_rate": speak_rate,
                "voice_auto_send": bool(controls["voice_auto_send"].get()),
                "deep_mode": bool(controls["deep_mode"].get()),
                "theme": selected_theme,
                "animations_enabled": bool(controls["animations"].get()),
                "response_language": controls["language"].get(),
                "response_style": controls["style"].get(),
                "custom_instructions": custom,
                "chat_font_size": font_size,
                "save_history": bool(controls["save_history"].get()),
                "vision_max_images": int(controls["vision_max_images"].get()),
            })
            self.deep_mode = bool(controls["deep_mode"].get())
            self.voice_output = bool(controls["auto_speak"].get())
            self._animations_enabled = bool(controls["animations"].get())
            if self._animations_enabled:
                if self._animation_after_id is None:
                    self._animation_after_id = self.root.after(100, self._animate_vynex_ui)
            else:
                try:
                    if self._animation_after_id is not None:
                        self.root.after_cancel(self._animation_after_id)
                except tk.TclError:
                    pass
                self._animation_after_id = None
            self._apply_chat_font_size(font_size)
            self._refresh_analyser_buttons()
            write_json(SETTINGS_FILE, self.settings)
            self.api_messages = [{"role": "system", "content": self._effective_system_prompt()}] + [m for m in self.api_messages[1:]]
            for composer in (self.home_composer, self.chat_composer):
                try:
                    composer["voice_btn"].configure(text="Réponse vocale : ON" if self.voice_output else "Réponse vocale : OFF")
                except (KeyError, tk.TclError):
                    pass
            self._refresh_recent_list()
            win.destroy()
            theme_note = " Redémarre VYNEX pour appliquer la nouvelle palette." if selected_theme != _BOOT_THEME else ""
            self.status_var.set("Paramètres enregistrés")
            messagebox.showinfo("Paramètres enregistrés", "Les préférences ont été enregistrées." + theme_note, parent=self.root)

        def reset_defaults():
            if not messagebox.askyesno("Réglages recommandés", "Restaurer les paramètres recommandés ? Les conversations ne seront pas supprimées.", parent=win):
                return
            controls["language"].set("Français")
            controls["style"].set("Équilibré")
            controls["instructions"].delete("1.0", "end")
            controls["theme"].set("Aurora · menthe")
            controls["animations"].set(True)
            controls["font_size"].set(12)
            controls["auto_speak"].set(False)
            controls["speak_rate"].set(0)
            controls["voice_auto_send"].set(True)
            controls["model"].delete(0, "end")
            controls["model"].insert(0, DEFAULT_CHAT_MODEL)
            controls["chat_url"].delete(0, "end")
            controls["chat_url"].insert(0, OLLAMA_URL)
            controls["temperature"].set(0.25)
            controls["max_tokens"].set("512")
            controls["save_history"].set(True)
            controls["vision_max_images"].set("4")
            controls["deep_mode"].set(False)

        self._button(footer, "Restaurer par défaut", reset_defaults, compact=True).pack(side="left", padx=10, pady=9)
        self._button(footer, "Tester le chat", self.test_ollama_chat, compact=True).pack(side="left", padx=(0, 8), pady=9)
        self._button(footer, "Enregistrer les paramètres", save_settings, primary=True).pack(side="right", padx=10, pady=9)
        show_section("Général")

    def test_ollama_chat(self):
        base = str(self.settings.get("chat_url", OLLAMA_URL) or OLLAMA_URL).rstrip("/")
        def worker():
            try:
                req = urllib.request.Request(base + "/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
                names = [item.get("name", "") for item in data.get("models", [])]
                model = str(self.settings.get("chat_model", DEFAULT_CHAT_MODEL))
                if not any(name == model or name.startswith(model + ":") for name in names):
                    text = f"Ollama fonctionne, mais '{model}' n'est pas dans la liste. Modèles trouvés : {', '.join(names) or 'aucun'}. Si nécessaire : ollama pull {model}"
                else:
                    text = f"Ollama fonctionne. Modèle de conversation trouvé : {model}"
                self.root.after(0, lambda: messagebox.showinfo(APP_TITLE, text, parent=self.root))
            except Exception as exc:
                text = f"Ollama ne répond pas à {base}. Lance Ollama puis réessaie. Détail : {exc}"
                self.root.after(0, lambda: messagebox.showwarning(APP_TITLE, text, parent=self.root))
        threading.Thread(target=worker, daemon=True).start()

    # ---------------------------- engine ----------------------------
    def server_ready(self) -> bool:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1.0) as response:
                if response.status != 200:
                    return False
                try:
                    body = json.loads(response.read().decode("utf-8", errors="replace"))
                    return body.get("status") == "ok" or response.status == 200
                except Exception:
                    return True
        except Exception:
            return False

    def _startup_server(self):
        if self.server_ready():
            self._set_status(True, "Vision locale prête · chat via Ollama")
            return
        missing = []
        for label, path in (("Moteur", ENGINE_EXE), ("Modèle", MODEL_PATH), ("Composant visuel", MMPROJ_PATH)):
            if not path.is_file():
                missing.append(f"{label} : {path}")
        if missing:
            self._set_status(False, "Fichiers du moteur manquants")
            messagebox.showwarning(
                APP_TITLE,
                "VYNEX n'a pas trouvé tous les fichiers locaux nécessaires :\n\n" + "\n".join(missing) +
                "\n\nPlace llama-server dans le dossier engine et les fichiers du modèle dans models, sous le dossier indiqué par VYNEX_HOME (ou VYNEXRuntime dans ton dossier utilisateur).",
                parent=self.root,
            )
            return
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            with open(LOG_DIR / "llama-server.log", "ab") as log:
                self.server_process = subprocess.Popen(
                    [str(ENGINE_EXE), "--model", str(MODEL_PATH), "--mmproj", str(MMPROJ_PATH),
                     "--host", "127.0.0.1", "--port", "9931", "--ctx-size", "2048", "--threads", "4", "--no-mmproj-offload"],
                    cwd=str(ENGINE_EXE.parent), stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                )
            self.started_server_here = True
            self.status_var.set("Chargement du modèle local…")
            self.status_dot.configure(text="● Chargement…", fg=WARNING)
            threading.Thread(target=self._wait_server_ready, daemon=True).start()
        except Exception as exc:
            self._set_status(False, "Démarrage impossible")
            messagebox.showerror(APP_TITLE, f"Impossible de démarrer le moteur local : {exc}", parent=self.root)

    def _wait_server_ready(self):
        for _ in range(90):
            if self.server_ready():
                self.root.after(0, self._set_status, True, "Vision locale prête · chat via Ollama")
                return
            if self.server_process and self.server_process.poll() is not None:
                break
            time.sleep(1)
        self.root.after(0, self._set_status, False, "Moteur non démarré · voir les journaux")

    def _set_status(self, ready, text):
        self.status_var.set(text)
        self.status_dot.configure(text=("● " if ready else "● ") + text,
                                   fg=ACCENT_HOVER if ready else (WARNING if "charg" in text.lower() else ERROR))

    def test_server(self):
        if self.server_ready():
            self._set_status(True, "Vision locale prête · chat via Ollama")
            messagebox.showinfo(APP_TITLE, "Le moteur visuel répond sur le port 9931. La conversation utilise Ollama sur le port 11434.", parent=self.root)
        else:
            self._set_status(False, "Module visuel local indisponible")
            self._startup_server()

    # ---------------------------- voice buttons / controls ----------------------------
    def test_voice(self):
        self.speak_text("Bonjour ! Je suis VYNEX. La lecture vocale locale est activée.")

    def close(self):
        self.voice_session_active = False
        self.speak_next_response = False
        self.force_voice_auto_send = False
        try:
            self.save_chat()
        except Exception:
            pass
        self.stop_voice(silent=True)
        try:
            if self.started_server_here and self.server_process and self.server_process.poll() is None:
                self.server_process.terminate()
        except Exception:
            pass
        self._animations_enabled = False
        try:
            if self._animation_after_id is not None:
                self.root.after_cancel(self._animation_after_id)
        except (tk.TclError, AttributeError):
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = VYNEXApp()
    app.run()
