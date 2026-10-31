# VYNEX

<p align="center">
  <img src="assets/VYNEX_icon.png" alt="Logo VYNEX" width="140">
</p>

<p align="center">
  <strong>Assistant IA de bureau multiplateforme</strong><br>
  <em>Windows · macOS · Linux</em>
</p>

<p align="center">
  <a href="https://github.com/dw467484-byte/vynex-desktop-preview/releases/latest">Télécharger VYNEX</a>
  ·
  <a href="https://github.com/dw467484-byte/vynex-desktop-preview/issues">Signaler un problème</a>
</p>

> **Statut : préversion technique.** VYNEX est compilé pour plusieurs systèmes, mais les archives ne remplacent pas les essais sur chaque ordinateur. Les moteurs et modèles IA ne sont pas inclus et doivent être installés séparément.

## Présentation

VYNEX est une application de bureau conçue pour fournir une interface d'assistant IA sur Windows, macOS et Linux. Cette préversion comprend notamment une interface de discussion, l'historique local des conversations, des fonctions de gestion des discussions et des points d'intégration pour des moteurs IA installés par l'utilisateur.

VYNEX est un logiciel **propriétaire**. Le dépôt est destiné à la présentation et à l'évaluation du projet ; sa visibilité publique ne constitue pas une autorisation générale de réutiliser son code.

## Télécharger

Les versions officielles sont publiées dans [GitHub Releases](https://github.com/dw467484-byte/vynex-desktop-preview/releases).

| Système | Archive | Architecture |
|---|---|---|
| Windows 10/11 | `VYNEX-windows-x64.zip` | x64 |
| Linux | `VYNEX-linux-x64.tar.gz` | x64 |
| macOS Apple Silicon | `VYNEX-macos-arm64.zip` | ARM64 |
| macOS Intel | `VYNEX-macos-intel.zip` | Intel x64 |

### Installation rapide sous Windows

1. Télécharge `VYNEX-windows-x64.zip` depuis la page Releases.
2. Extrais **tout** le contenu de l'archive dans un même dossier.
3. Ouvre le dossier `VYNEX`.
4. Lance `VYNEX.exe`.

Ne déplace pas le seul fichier EXE hors de son dossier. Windows peut afficher un avertissement SmartScreen pour une application qui n'est pas encore largement reconnue.

Pour Linux, consulte les scripts `install-linux.sh` et `uninstall-linux.sh` fournis dans l'archive. Sur macOS, cette préversion n'est pas signée ni notariée par Apple ; Gatekeeper peut afficher un avertissement.

## Fonctions présentes dans la préversion

- Interface de discussion de bureau VYNEX.
- Historique local et suppression individuelle des discussions avec confirmation.
- Sélection de fichiers et d'images dans l'application.
- Préparations pour la dictée et la lecture vocale selon le système.
- Points d'intégration pour le chat local, l'analyse d'images et la génération d'images lorsqu'un moteur compatible est installé.
- Modèles de conditions, confidentialité et autorisations à compléter avant une distribution générale.

La disponibilité de chaque fonction dépend de la plateforme, des autorisations du système, des composants optionnels installés et de la configuration.

## Installer les moteurs IA

L'application de bureau et les moteurs IA sont distribués séparément. VYNEX ne contient pas les poids des modèles.

- **Chat local :** Ollama et un modèle compatible. Le modèle configuré par défaut est `llama3.2:3b` ; le serveur local par défaut est `http://127.0.0.1:11434`.
- **Analyse d'images :** un binaire llama.cpp/llama-server adapté au système, plus les fichiers de modèle SmolVLM indiqués dans [RUNTIME_SETUP.md](RUNTIME_SETUP.md).
- **Génération d'images :** un serveur local compatible AUTOMATIC1111/Forge et un modèle installé séparément.
- **Voix :** dépend des fonctions vocales disponibles sur le système ; la dictée hors ligne peut demander des composants optionnels.

Consulte [RUNTIME_SETUP.md](RUNTIME_SETUP.md) avant de configurer ces composants. Vérifie les licences et conditions des moteurs et modèles tiers avant de les télécharger ou de les redistribuer.

## Confidentialité et autorisations

Les données de conversation sont prévues pour être stockées dans le profil local de l'utilisateur. Toutefois, si un utilisateur configure un endpoint distant, les messages ou pièces jointes envoyés à cet endpoint peuvent quitter son ordinateur et être traités par le fournisseur correspondant.

Le microphone, la capture d'écran et la sélection de fichiers sont des fonctions soumises à des actions de l'utilisateur et aux autorisations du système. VYNEX ne chiffre pas à lui seul l'ensemble des données locales. Lis [PRIVACY_POLICY.md](PRIVACY_POLICY.md) et [PERMISSIONS.md](PERMISSIONS.md) avant utilisation.

**Cette politique est encore un modèle de prépublication.** Les coordonnées du responsable, les procédures de contact et les vérifications réelles par système doivent être complétées avant une distribution publique à grande échelle. Ne transmets jamais de mot de passe, de clé privée ou d'information sensible dans les Issues publiques.

## Retours et problèmes

Les retours non sensibles et les rapports de bugs peuvent être déposés dans [GitHub Issues](https://github.com/dw467484-byte/vynex-desktop-preview/issues). Pour ta sécurité, n'inclus aucune donnée personnelle, identifiant, mot de passe, clé API, conversation privée ou fichier confidentiel dans un rapport public.

## État de validation

Les workflows GitHub Actions vérifient la syntaxe, exécutent les tests automatisés et construisent les archives sur des runners Windows, Linux et macOS. Cela ne prouve pas à lui seul que chaque paquet fonctionne sur toutes les versions de ces systèmes. Des essais manuels restent nécessaires, notamment pour le microphone, la capture d'écran, l'installation, la suppression des données et la configuration des moteurs.

Consulte [PRE_PUBLICATION_CHECKLIST.md](PRE_PUBLICATION_CHECKLIST.md) pour connaître les vérifications restantes.

## English

VYNEX is a cross-platform desktop AI assistant interface for Windows, macOS and Linux. This is a **technical preview**, not a stable release. AI engines and model weights are not bundled and must be installed separately. See [Releases](https://github.com/dw467484-byte/vynex-desktop-preview/releases) for official packages and [RUNTIME_SETUP.md](RUNTIME_SETUP.md) for setup instructions.

VYNEX is proprietary software. Public visibility of this repository is not a general permission to reuse, modify or redistribute its source code. See [LICENSE](LICENSE).

## Licence et propriété

VYNEX est un logiciel propriétaire, tous droits réservés, sous réserve des droits techniques accordés par les conditions de GitHub pour consulter et forker un dépôt public. Aucun droit général d'utiliser, modifier, vendre ou redistribuer le logiciel hors de ce cadre n'est accordé. Consulte [LICENSE](LICENSE). Les composants tiers restent soumis à leurs propres licences.

---

**VYNEX — Technical Preview 0.1.0-preview.5**
