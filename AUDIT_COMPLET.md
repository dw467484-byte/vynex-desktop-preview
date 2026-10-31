# Audit complet de VYNEX — préversion 0.1.0-preview.4

Date de l'audit : 28 octobre 2026

## Résumé exécutif

VYNEX dispose d'une base de bureau Tkinter qui peut être empaquetée séparément pour Windows, macOS et Linux. Le projet comprend le logo/robot, une interface de conversation, la suppression individuelle de conversations enregistrées, une page de consentement, un contrôle d'autorisation applicatif pour le microphone et les captures d'écran, un avertissement avant l'envoi vers un serveur de chat distant, des scripts de compilation par système et un workflow GitHub Actions.

**Statut global : préversion technique, pas encore une version publique stable.** Le dépôt GitHub n'a pas été confirmé comme publié, les quatre paquets n'ont pas été générés/testés depuis GitHub Actions dans cet audit et aucun essai manuel n'a été effectué sur de vrais appareils macOS/Linux.

## Défauts trouvés et corrigés dans cette archive

1. **Import absent de `urlparse` (critique).** Le code appelait `urlparse()` avant l'envoi d'un message et dans l'écran Paramètres, mais n'importait pas la fonction. Cela pouvait faire échouer la vérification de l'adresse du serveur avant tout envoi. L'import `from urllib.parse import urlparse` est ajouté.
2. **Chemin runtime Windows non portable.** Le code forçait le dossier `D:\MonIA\MonIA_Lite`, présent seulement sur le PC de développement. Il conserve désormais cet ancien emplacement s'il existe ; sinon, il utilise `%USERPROFILE%\VYNEXRuntime`. `VYNEX_HOME` reste disponible pour configurer explicitement le dossier runtime.
3. **Chemin de modèle manquant peu utile.** Le chemin de secours signale maintenant l'emplacement runtime configuré plutôt que le dossier de l'application.
4. **Régression couverte.** Un test d'exécution vérifie la validation d'une URL locale, le refus d'un serveur distant et la demande/confirmation de consentement à une URL distante.

## Vérifications exécutées sur cette archive

- `python -m py_compile VYNEX.py` : réussi.
- `python -m unittest discover -s tests -v` : **22 tests réussis**.
- Import réel du module et test du consentement serveur sans ouvrir la fenêtre graphique ni effectuer de requête réseau : réussi.
- Analyse syntaxique du workflow YAML : réussi.
- Présence des quatre cibles configurées : Windows x64, Linux x64, macOS ARM64 et macOS Intel.
- Présence des ressources du robot : PNG, ICO, ICNS et écran de démarrage.
- Présence des scripts Windows/macOS/Linux, de l'installateur Linux et des tests de suppression des discussions.

Ces tests ne sont pas un test de lancement graphique, ni la preuve que les binaires finaux fonctionnent sur tous les systèmes.

## Points à régler avant un dépôt public ou une distribution stable

### Bloquants pour la publication

- **Synchroniser le bon dossier source.** Le dernier `git status` partagé ne correspondait pas au contenu de cette archive : il montrait l'ancien `VYNEX.spec`, `spec_safe/` et seulement `tests/test_source_smoke.py`, mais pas tous les scripts Linux/macOS ni les tests `test_delete_conversations.py`, `test_release_packaging.py` et `test_runtime_endpoint_consent.py`. Ne pas valider/pousser cet ancien dossier sans l'actualiser. Extraire cette archive auditée dans un nouveau dossier, vérifier les 22 tests, puis initialiser un nouveau dépôt propre.
- **Choisir une licence.** Aucun fichier `LICENSE` définitif n'est inclus. Il faut confirmer qui détient les droits sur le code et les ressources, puis choisir et ajouter une licence avant de présenter le dépôt comme réutilisable.
- **Compléter les informations du responsable.** `PRIVACY_POLICY.md` et les conditions restent des modèles ; ajouter un vrai contact de confidentialité et les informations exactes du distributeur. Ne pas publier avec des coordonnées fictives.
- **Vérifier les droits des ressources et composants tiers.** Documenter les licences de Pillow, PyInstaller, Ollama, llama.cpp, Vosk, sounddevice, AUTOMATIC1111/Forge, ainsi que de chaque modèle et image que le distributeur décide d'inclure. Les licences des modèles ne sont pas automatiquement les mêmes que celles des moteurs.
- **Pousser le code et attendre le workflow.** Il faut créer un dépôt GitHub, envoyer le contenu de cette archive, vérifier chacun des quatre jobs Actions, puis pousser un tag de préversion. Aucune GitHub Release n'a été créée à ce stade.

### Dépendances runtime non incluses

- Chat : nécessite Ollama installé, lancé et un modèle compatible, actuellement `llama3.2:3b`.
- Analyse d'images : nécessite un binaire `llama-server` compilé pour le système/architecture et les deux fichiers de modèle SmolVLM attendus.
- Génération d'images : nécessite une API locale AUTOMATIC1111/Forge sur le port configuré et un modèle d'image compatible. Le Studio visuel est une interface client ; le moteur et ses poids ne sont pas intégrés.
- Dictée vocale hors ligne : nécessite les dépendances optionnelles `vosk`, `sounddevice` et un modèle Vosk français. Elles ne font pas partie des dépendances de compilation de base.

### Vérifications techniques avant de parler de version stable

- Tester manuellement le chat, le robot, l'historique et la suppression des discussions sur Windows 10/11.
- Tester l'installation, l'affichage de l'icône, la fermeture et les autorisations sur macOS Apple Silicon et Intel ; le paquet macOS n'est pas signé/notarié par les scripts actuels et Gatekeeper peut avertir l'utilisateur.
- Tester le paquet et l'installateur/désinstallateur sur une distribution Linux définie (par exemple Ubuntu LTS).
- Tester que les paramètres, conversations et images sont conservés après mise à jour, et que la suppression d'une discussion n'efface pas accidentellement les autres données. Les fichiers de la bibliothèque d'images ne sont pas supprimés avec une conversation.
- Tester le chat local et le comportement de consentement en cas de serveur distant. Le contrôle de consentement dans VYNEX ne remplace pas les permissions du système d'exploitation.
- Vérifier les avertissements de sécurité Windows, la signature/notarisation macOS, les métadonnées, l'icône et le hachage des archives.

## Ordre conseillé des prochaines étapes

1. Extraire ce pack dans un nouveau dossier séparé pour ne pas mélanger les fichiers avec l'ancien dépôt local.
2. Exécuter la syntaxe et les 22 tests ; examiner le résultat.
3. Ajouter les informations réelles et la licence choisie, après vérification des droits.
4. Créer un dépôt GitHub vide et envoyer cette version du projet.
5. Corriger les erreurs éventuelles du workflow ; ne créer le tag que lorsque les quatre jobs sont verts.
6. Faire les essais manuels par système avant de qualifier la version de stable ou de soumettre des paquets aux boutiques.

## Sources techniques consultées

- PyInstaller explique que la compilation est spécifique au système cible et n'est pas un cross-compiler : https://pyinstaller.org/en/stable/usage.html
- Documentation GitHub des runners et architectures prises en charge : https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
- Documentation Apple sur les descriptions des accès microphone et capture d'écran : https://developer.apple.com/documentation/ScreenCaptureKit
