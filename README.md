# VYNEX

<p align="center">
  <img src="assets/VYNEX_icon.png" alt="Logo VYNEX" width="132">
</p>

<h3 align="center">Un assistant IA de bureau, sur plusieurs plateformes.</h3>
<p align="center">Windows · Linux · macOS</p>

<p align="center">
  <a href="https://github.com/dw467484-byte/vynex-desktop-preview/releases/latest"><strong>Télécharger la préversion</strong></a>
  ·
  <a href="https://github.com/dw467484-byte/vynex-desktop-preview/releases">Toutes les versions</a>
  ·
  <a href="https://github.com/dw467484-byte/vynex-desktop-preview/issues">Retours et problèmes</a>
</p>

<p align="center">
  <img alt="Dernière préversion" src="https://img.shields.io/github/v/release/dw467484-byte/vynex-desktop-preview?include_prereleases&label=preview">
  <img alt="Étoiles GitHub" src="https://img.shields.io/github/stars/dw467484-byte/vynex-desktop-preview?style=flat">
  <img alt="Licence propriétaire" src="https://img.shields.io/badge/license-proprietary-informational">
  <img alt="Python" src="https://img.shields.io/badge/Python-desktop-blue">
</p>

> **État du projet : préversion technique.** Les paquets de bureau sont disponibles pour plusieurs plateformes, mais les essais automatisés ne remplacent pas les tests sur chaque ordinateur. Les moteurs IA et les modèles ne sont pas inclus : ils doivent être installés et configurés séparément.

## Qu'est-ce que VYNEX ?

VYNEX est une application de bureau développée en Python qui fournit une interface pour utiliser des assistants IA depuis un ordinateur. Le projet vise une expérience cohérente sur Windows, Linux et macOS, avec une attention particulière portée à l'historique local, à la gestion des conversations et aux moteurs IA installés par l'utilisateur.

VYNEX est un **logiciel propriétaire**. Ce dépôt public sert à présenter le projet et à distribuer ses préversions d'évaluation ; sa visibilité sur GitHub ne donne pas une autorisation générale de réutiliser, modifier, vendre ou redistribuer le logiciel. Consulte [LICENSE](LICENSE).

## Télécharger VYNEX

La version actuellement publiée est **v0.1.0-preview.5**. Télécharge les fichiers uniquement depuis la page officielle des versions :

**[Ouvrir les téléchargements VYNEX](https://github.com/dw467484-byte/vynex-desktop-preview/releases/latest)**

| Plateforme | Fichier | Architecture |
|---|---|---|
| Windows 10/11 | `VYNEX-windows-x64.zip` | x64 |
| Linux | `VYNEX-linux-x64.tar.gz` | x64 |
| macOS Apple Silicon | `VYNEX-macos-arm64.zip` | ARM64 |
| macOS Intel | `VYNEX-macos-intel.zip` | Intel x64 |

Les sommes de contrôle SHA-256 sont publiées avec chaque version lorsqu'elles sont disponibles. Vérifie le fichier `SHA256SUMS.txt` avant d'utiliser une archive.

### Installation sous Windows

1. Télécharge `VYNEX-windows-x64.zip` depuis la page Releases.
2. Extrais toute l'archive dans un dossier.
3. Ouvre le dossier `VYNEX` extrait.
4. Lance `VYNEX.exe`.

Garde les fichiers extraits ensemble : ne déplace pas uniquement le fichier EXE. Windows peut afficher un avertissement SmartScreen pour une application qui n'a pas encore une réputation établie.

### Linux et macOS

Sous Linux, extrais l'archive et consulte les scripts `install-linux.sh` et `uninstall-linux.sh` fournis. Sous macOS, cette préversion n'est pas signée ni notariée par Apple ; Gatekeeper peut donc afficher un avertissement. Lis les notes de version avant l'installation.

## Fonctionnalités de la préversion

- Interface de discussion de bureau.
- Historique local des conversations et suppression individuelle avec confirmation.
- Sélection de fichiers et d'images.
- Intégration possible avec un moteur de chat local.
- Points d'intégration pour l'analyse d'images et la génération d'images avec des serveurs compatibles installés séparément.
- Fonctions vocales dépendantes du système et des composants optionnels.

La disponibilité réelle dépend de la plateforme, des autorisations du système, des moteurs configurés et des dépendances installées. Certaines fonctions sont encore expérimentales.

## Installer les moteurs IA

L'application et les moteurs IA sont distribués séparément afin de garder les archives de bureau plus légères. Les poids des modèles ne sont pas inclus.

- **Chat local :** installer [Ollama](https://ollama.com/download), puis récupérer le modèle configuré par défaut avec `ollama pull llama3.2:3b`. Le serveur local par défaut est `http://127.0.0.1:11434`.
- **Analyse d'images :** installer un binaire `llama-server` compatible et les fichiers de modèle SmolVLM décrits dans [RUNTIME_SETUP.md](RUNTIME_SETUP.md).
- **Génération d'images :** installer et démarrer un serveur compatible AUTOMATIC1111/Forge, ainsi qu'un modèle compatible. L'adresse par défaut documentée est `http://127.0.0.1:7860`.
- **Voix :** les moteurs et dépendances disponibles varient selon Windows, Linux et macOS.

Guide détaillé : [RUNTIME_SETUP.md](RUNTIME_SETUP.md). Vérifie les licences et conditions des outils et modèles tiers avant tout téléchargement ou redistribution.

## Confidentialité et autorisations

Les conversations sont prévues pour être stockées dans le profil local de l'utilisateur. Si un endpoint distant est configuré, les messages et pièces jointes qui lui sont envoyés peuvent quitter l'ordinateur et être traités par le fournisseur distant.

Le microphone, la capture d'écran et l'accès aux fichiers impliquent des actions de l'utilisateur et les autorisations du système. VYNEX ne chiffre pas à lui seul toutes les données locales. La politique de confidentialité, les autorisations et les conditions restent des documents de prépublication qui doivent être complétés et vérifiés avant une distribution à grande échelle.

- [Politique de confidentialité](PRIVACY_POLICY.md)
- [Autorisations](PERMISSIONS.md)
- [Conditions d'utilisation](TERMS_OF_USE.md)
- [Liste de contrôle avant publication](PRE_PUBLICATION_CHECKLIST.md)

Ne publie jamais de mot de passe, de clé API, de clé privée, d'identifiant personnel, de conversation privée ou de fichier confidentiel dans une issue GitHub.

## État des validations

Le workflow [Build and publish VYNEX desktop preview](https://github.com/dw467484-byte/vynex-desktop-preview/actions/workflows/release.yml) vérifie la syntaxe Python, exécute les tests automatisés et construit les paquets sur des runners Windows, Linux et macOS.

Un workflow réussi confirme que les étapes automatisées ont abouti sur les runners correspondants ; il ne garantit pas le fonctionnement sur chaque ordinateur réel. Des essais manuels restent nécessaires pour l'installation, le microphone, la capture d'écran, la suppression des données, les moteurs IA et les différentes versions des systèmes.

## Retours et suivi du projet

Les retours constructifs aident à prioriser les améliorations. Avant de signaler un problème, vérifie les [versions publiées](https://github.com/dw467484-byte/vynex-desktop-preview/releases) et le guide [RUNTIME_SETUP.md](RUNTIME_SETUP.md).

- [Signaler un bug](https://github.com/dw467484-byte/vynex-desktop-preview/issues/new?template=bug_report.yml)
- [Proposer une amélioration](https://github.com/dw467484-byte/vynex-desktop-preview/issues/new?template=feature_request.yml)
- [Consulter la feuille de route](ROADMAP.md)

Si VYNEX t'intéresse, tu peux ajouter une étoile au dépôt pour le retrouver et suivre son évolution. Tu peux également consulter les nouvelles versions depuis l'onglet Releases.

## English

VYNEX is a Python desktop application that provides an interface for AI assistants across Windows, Linux and macOS. This repository distributes a **technical preview**, not a stable release. AI engines and model weights are not bundled and must be installed separately.

Download the current preview from [GitHub Releases](https://github.com/dw467484-byte/vynex-desktop-preview/releases/latest). Read [RUNTIME_SETUP.md](RUNTIME_SETUP.md) for local AI engine setup, and review the privacy and permission documents before use. Automated builds do not replace hands-on testing on target computers.

VYNEX is proprietary software. Public repository visibility does not grant a general license to reuse, modify, sell or redistribute the software. See [LICENSE](LICENSE).

---

**VYNEX — Technical Preview 0.1.0-preview.5**
