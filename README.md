# VYNEX — application de bureau multiplateforme

**Préversion de bureau.** Le projet vise Windows, macOS et Linux avec la même interface Tkinter et le robot VYNEX comme identité visuelle. Cette archive est prête à être poussée vers GitHub afin que GitHub Actions construise les paquets sur des machines natives pour chaque système.

## Paquets produits

- Windows x64 (runner Windows Server 2022, pour une meilleure compatibilité Windows 10) : `VYNEX-windows-x64.zip`, contenant `VYNEX.exe` et son dossier d'exécution.
- macOS Apple Silicon : `VYNEX-macos-arm64.zip`, contenant `VYNEX.app`.
- macOS Intel : `VYNEX-macos-intel.zip`, contenant `VYNEX.app`.
- Linux x64 : `VYNEX-linux-x64.tar.gz`, contenant le binaire et un installateur local.

Pour obtenir ces quatre paquets depuis un ordinateur Windows, le projet configure `.github/workflows/release.yml`. Il faut envoyer le code vers un dépôt GitHub, attendre que tous les jobs finissent, puis pousser un tag `v0.1.0-preview.4` pour créer une GitHub Release.

## Construction locale

- Windows : `powershell.exe -ExecutionPolicy Bypass -File .\BUILD_WINDOWS_SAFE.ps1`
- macOS : `bash ./BUILD_MACOS.sh`
- Linux : `bash ./BUILD_LINUX.sh` (voir les dépendances Tkinter dans `BUILD_AND_PUBLISH.md`).

Les scripts de compilation utilisent des dossiers horodatés afin de préserver les anciennes constructions et d'éviter les erreurs de suppression dues à des DLL bloquées.

## Important : moteurs IA séparés

VYNEX est l'interface ; les poids et serveurs IA ne sont pas inclus à l'installateur. Le chat local nécessite Ollama avec un modèle compatible, par défaut `llama3.2:3b`. L'analyse locale d'images nécessite un binaire llama.cpp compatible avec l'OS, ainsi que `SmolVLM-500M-Instruct-Q8_0.gguf` et `mmproj-SmolVLM-500M-Instruct-Q8_0.gguf`. La création d'images nécessite en plus une API locale AUTOMATIC1111/Forge et un modèle adapté. Voir `RUNTIME_SETUP.md`.

## Identité, droits et confidentialité

Le robot est fourni sous `assets/` dans les formats PNG, ICO et ICNS. Les conditions, avis de confidentialité et autorisations sont des modèles à relire avant une publication définitive : `TERMS_OF_USE.md`, `PRIVACY_POLICY.md`, `PERMISSIONS.md` et `PRE_PUBLICATION_CHECKLIST.md`. La préversion macOS n'est pas signée/notariée ; Windows peut afficher SmartScreen.

Consulte `BUILD_AND_PUBLISH.md` pour les étapes détaillées de construction et de publication. Les tests exécutés dans l'environnement de préparation valident la syntaxe et la suppression individuelle des discussions ; ils ne remplacent pas un test manuel sur les trois systèmes.
