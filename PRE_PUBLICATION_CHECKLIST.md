# Liste de contrôle avant publication publique de VYNEX

Cette liste distingue une compilation réussie d'une publication réellement prête pour le public. La présence de documents dans le dépôt ne signifie pas que la conformité légale ou l'approbation d'une boutique est acquise.

## Sécurité et confidentialité avant ouverture du dépôt

- [ ] Faire une sauvegarde complète du dépôt avant de réécrire son historique.
- [ ] Remplacer les adresses personnelles présentes dans **tous** les commits par l'adresse GitHub noreply du propriétaire, puis vérifier les métadonnées de chaque commit, branche et tag.
- [ ] Supprimer les anciennes exécutions GitHub Actions et leurs journaux avant de rendre le dépôt public, après avoir conservé localement les éléments de diagnostic nécessaires.
- [ ] Vérifier les commits, tags, releases, fichiers, captures d'écran et journaux d'actions pour retirer les coordonnées personnelles, secrets, jetons, clés ou données privées.
- [ ] Activer sur GitHub « Keep my email addresses private » et « Block command line pushes that expose my email ».
- [ ] Relire le dépôt complet et vérifier que les modèles IA, runtimes locaux, journaux, fichiers de configuration privés et données d'utilisateurs ne sont pas inclus.
- [ ] Compléter la politique de confidentialité avec un canal de contact dédié au projet. Ne pas publier d'adresse personnelle, de numéro de téléphone ou d'adresse physique.
- [ ] Faire relire les conditions, la politique de confidentialité et les mentions de propriété par un adulte de confiance avant d'accepter des utilisateurs, des paiements ou des demandes contenant des données personnelles.

## Droits et propriété intellectuelle

- [ ] Confirmer que le propriétaire dispose des droits nécessaires sur le code, le robot, les visuels et les autres ressources d'origine.
- [ ] Maintenir la mention propriétaire « tous droits réservés » et préciser que le dépôt n'est pas open source.
- [ ] Vérifier séparément les licences des dépendances, moteurs IA, modèles, bibliothèques, icônes et ressources tierces. La mention propriétaire de VYNEX ne s'applique pas aux composants tiers.
- [ ] Expliquer clairement que la visibilité publique d'un dépôt GitHub autorise les utilisateurs de GitHub à le consulter et à le forker selon les conditions de GitHub ; elle n'accorde pas une licence générale de réutilisation hors de GitHub.

## Validation technique et distribution

- [ ] Reproduire les tests sur de vrais appareils Windows, macOS Intel, macOS Apple Silicon et Linux ; tester refus/acceptation du microphone, capture d'écran, historique et suppression des fichiers.
- [ ] Vérifier qu'aucune donnée ne part vers une adresse distante sans avertissement/consentement ; documenter les services tiers configurés par l'utilisateur.
- [ ] Générer un inventaire complet des dépendances et de leurs licences ; vérifier séparément les licences des modèles d'IA et de toutes les ressources distribuées.
- [ ] Préparer une procédure de mise à jour, de correction de sécurité et de retrait des anciennes versions.
- [ ] Pour macOS en distribution directe : signer/notariser le paquet avec le compte du propriétaire et tester Gatekeeper/TCC. Pour le Mac App Store : adapter au bac à sable, ajouter les entitlements nécessaires et effectuer la soumission/revue Apple.
- [ ] Pour Microsoft Store : préparer le paquet conforme et remplir les déclarations du Store, dont confidentialité et capacités utilisées.
- [ ] Établir les informations de sécurité, âge et données requises par la boutique ciblée ; ne pas déclarer des traitements absents ni omettre les services tiers réellement inclus.

## Nettoyage de l'historique et nouvelle publication

- [ ] Après réécriture de l'historique, vérifier que les anciens commits sensibles ne sont plus référencés par les branches ou tags.
- [ ] Recréer un tag de version propre et relancer les compilations depuis l'historique nettoyé.
- [ ] Vérifier que les nouvelles archives et les sommes SHA-256 correspondent aux fichiers livrés.
- [ ] Ouvrir le dépôt en public uniquement après tous les contrôles ci-dessus.

## État des builds

- [x] Les jobs GitHub Actions Windows x64, Linux x64, macOS Apple Silicon et macOS Intel de la préversion 0.1.0-preview.4 ont terminé avec succès.
- [ ] Tester l'EXE sur Windows, le `.app` sur un Mac Apple Silicon ou Intel selon le paquet, et le binaire sur une distribution Linux prise en charge.
- [ ] Vérifier l'installation/suppression Linux via `install-linux.sh` et `uninstall-linux.sh`.
- [ ] Confirmer que les paquets n'embarquent pas involontairement les répertoires runtime, les modèles locaux, les journaux ou des informations personnelles.

