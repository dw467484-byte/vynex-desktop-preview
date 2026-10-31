# Préparer les moteurs IA pour VYNEX

Les paquets de bureau VYNEX ne comprennent pas les poids des modèles ni les serveurs IA. Cette séparation évite de produire des installateurs très lourds et les modèles/moteurs doivent être compatibles avec le système et le processeur de l'ordinateur.

## Chat local

1. Installer Ollama pour le système concerné depuis le site officiel : https://ollama.com/download
2. Démarrer Ollama et télécharger le modèle configuré par défaut : `ollama pull llama3.2:3b`
3. Dans VYNEX, vérifier que l'adresse du serveur reste `http://127.0.0.1:11434` et tester le chat.

## Analyse locale d'images

Installer ou compiler une version de `llama-server` de llama.cpp qui correspond à l'OS et à l'architecture. Créer le dossier runtime suivant :

- Windows : par défaut `%USERPROFILE%\VYNEXRuntime\engine` et `%USERPROFILE%\VYNEXRuntime\models`. Si l'ancien dossier de développement `D:\MonIA\MonIA_Lite` existe, VYNEX le conserve pour rétrocompatibilité.
- macOS/Linux : `~/VYNEXRuntime/engine` et `~/VYNEXRuntime/models`.
- Pour tout système, la variable d'environnement `VYNEX_HOME` peut désigner un autre dossier contenant `engine/` et `models/`.

Placer le binaire du moteur dans `engine/` (`llama-server.exe` sous Windows, `llama-server` sous macOS/Linux) et les deux fichiers de modèle dans `models/` :

- `SmolVLM-500M-Instruct-Q8_0.gguf`
- `mmproj-SmolVLM-500M-Instruct-Q8_0.gguf`

Pour utiliser un runtime ailleurs, définir `VYNEX_HOME` avant de lancer l'app. Les modèles ne sont pas fournis dans cette archive : vérifier leurs licences et la compatibilité avant de télécharger ou redistribuer.

## Création d'images

Le Studio visuel communique avec une API locale AUTOMATIC1111/Forge (par défaut `http://127.0.0.1:7860`). Il ne comprend pas le serveur de génération ni un modèle Stable Diffusion. La génération réelle fonctionne seulement lorsque le serveur et un modèle compatible sont installés et démarrés.

## Voix

- Windows : la lecture vocale s'appuie sur PowerShell / System.Speech selon la configuration du système.
- macOS : VYNEX utilise la commande système `say` si disponible.
- Linux : VYNEX cherche `espeak-ng`, `espeak` ou `spd-say`.
- Dictée hors ligne : Vosk, sounddevice et le modèle français sont des dépendances optionnelles ; testez le microphone et les autorisations du système.

Ne publiez pas de modèle/binaire tiers dans la distribution de VYNEX sans vérifier sa licence. Les moteurs externes restent mis à jour et pris en charge séparément.
