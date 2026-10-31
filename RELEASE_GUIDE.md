# Guide de publication VYNEX

1. Vérifier la liste prépublication (`PRE_PUBLICATION_CHECKLIST.md`) et les dépendances (`RUNTIME_SETUP.md`).
2. Créer un dépôt GitHub vide et y pousser ce dossier. Guide détaillé dans `BUILD_AND_PUBLISH.md`.
3. Dans l'onglet Actions, vérifier que la compilation Windows, Linux, macOS ARM64 et macOS Intel réussit.
4. Lorsque les quatre jobs sont verts, envoyer un tag `v0.1.0-preview.3`. Le workflow crée alors une GitHub Release avec les quatre archives.
5. Tester les téléchargements sur de vrais ordinateurs Windows, Mac Intel/Apple Silicon et Linux avant d'annoncer une version stable.

Le paquet macOS n'est pas signé/notarié. Les archives ne contiennent ni Ollama, ni llama.cpp, ni les modèles IA. Une GitHub Release ne signifie pas que VYNEX est publié dans Microsoft Store ou Mac App Store.
