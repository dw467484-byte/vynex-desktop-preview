# Politique de confidentialité de VYNEX — modèle pour préversion

**Version :** `2026-10-22-v1`  
**Statut :** à vérifier et compléter par le responsable de la publication avant distribution publique. Le comportement réel doit être vérifié sur chaque système et avec chaque moteur optionnel.

## Données stockées localement

Les paramètres, l’historique et des fichiers liés aux pièces jointes sont stockés dans le profil local de l’utilisateur :

- Windows : `%LOCALAPPDATA%\MonIA Lite`
- macOS : `~/Library/Application Support/VYNEX`
- Linux : `${XDG_DATA_HOME:-~/.local/share}/vynex`

Le réglage d’historique permet d’arrêter l’enregistrement des nouvelles conversations. La suppression de l’historique ne supprime pas nécessairement les images, captures d’écran et journaux : ceux-ci doivent être supprimés séparément depuis l’application, le dossier de données ou la bibliothèque correspondante.

## Transmission des données

Dans la configuration par défaut, la conversation se connecte à Ollama sur `127.0.0.1:11434` et l’analyse d’images à un serveur llama.cpp sur `127.0.0.1:9931`. La génération d’images est prévue pour un service local sur `127.0.0.1:7860`. Ces services peuvent être absents et doivent être installés séparément.

Si l’utilisateur configure un serveur de conversation distant, les messages, le contexte et les pièces jointes transmis peuvent quitter l’appareil et être soumis aux pratiques du fournisseur de ce serveur. VYNEX affiche un avertissement lors de l’enregistrement d’une adresse non locale. Une adresse distante en HTTP n’assure pas le chiffrement du trafic.

Le code de cette préversion ne contient pas de télémétrie intégrée connue. Ce constat ne couvre pas les composants tiers, leurs modèles, les systèmes d’exploitation ou des services distants que l’utilisateur configure.

## Autorisations facultatives

- **Microphone :** demandé uniquement lorsque la dictée ou la conversation vocale est lancée, après confirmation de l’utilisateur dans VYNEX. Le système d’exploitation peut présenter sa propre invite ou bloquer l’accès.
- **Capture d’écran :** demandée uniquement à la suite d’une action volontaire, avec confirmation à chaque capture. L’image peut être enregistrée localement puis jointe au message choisi par l’utilisateur.
- **Fichiers et images :** choisis explicitement par l’utilisateur à l’aide du sélecteur de fichiers.
- **Caméra, contacts et localisation :** ne sont pas utilisés par cette version.

Les consentements mémorisés dans VYNEX peuvent être révoqués depuis **Paramètres > Données & confidentialité**. Cette révocation ne réinitialise pas à elle seule les autorisations système de Windows ou macOS.

## Sécurité et conservation

Les données locales restent exposées à toute personne disposant d’un accès au même compte d’utilisateur, au disque ou aux sauvegardes. VYNEX ne chiffre pas l’ensemble des fichiers de données de l’application. Utilisez le chiffrement et les contrôles du système d’exploitation si les données l’exigent. L’utilisateur doit supprimer les fichiers qu’il ne souhaite plus conserver.

## Contact du responsable

**À compléter avant publication :** nom du responsable/distributeur, pays, adresse de contact pour les demandes relatives à la confidentialité et procédure de suppression des données. N’inscrivez pas de coordonnées inventées.
