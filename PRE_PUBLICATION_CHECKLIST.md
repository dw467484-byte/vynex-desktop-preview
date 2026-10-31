# Liste de contrôle avant publication publique de VYNEX

Les contrôles ci-dessous restent à effectuer par le propriétaire du logiciel. La présence de ces fichiers ne signifie pas que la conformité légale ou l’approbation d’une boutique est acquise.

- [ ] Confirmer qui est le responsable de la publication et ajouter un moyen de contact réel dans la politique de confidentialité.
- [ ] Faire relire et adapter les conditions d’utilisation et la politique de confidentialité au pays, à l’âge du public visé et aux données réellement traitées.
- [ ] Choisir la licence du code et ajouter le fichier de licence approprié.
- [ ] Générer un inventaire complet des dépendances et de leurs licences ; vérifier séparément les licences des modèles d’IA et de toutes les ressources distribuées.
- [ ] Reproduire les tests sur de vrais appareils Windows, macOS Intel, macOS Apple Silicon et Linux ; tester refus/acceptation du microphone, capture d’écran, historique et suppression des fichiers.
- [ ] Vérifier qu’aucune donnée ne part vers une adresse distante sans avertissement/consentement ; documenter les services tiers configurés par l’utilisateur.
- [ ] Pour macOS en distribution directe : signer/notariser le paquet avec le compte du propriétaire et tester Gatekeeper/TCC. Pour le Mac App Store : adapter au bac à sable, ajouter les entitlements nécessaires et effectuer la soumission/revue Apple.
- [ ] Pour Microsoft Store : préparer le paquet conforme et remplir les déclarations du Store, dont confidentialité et capacités utilisées.
- [ ] Établir les informations de sécurité, âge et données requises par la boutique ciblée ; ne pas déclarer des traitements absents ni omettre les services tiers réellement inclus.
- [ ] Préparer une procédure de mise à jour, de correction de sécurité et de retrait des anciennes versions.
- [ ] Publier une version uniquement après réussite des compilations, tests d’installation et vérifications d’autorisations sur toutes les plateformes annoncées.

## Publication multiplateforme finale
- [ ] Sur GitHub Actions, les jobs Windows x64, Linux x64, macOS Apple Silicon et macOS Intel se terminent tous avec succès.
- [ ] Tester l'EXE sur Windows, le `.app` sur un Mac Apple Silicon ou Intel selon le paquet, et le binaire sur une distribution Linux prise en charge.
- [ ] Vérifier l'installation/suppression Linux via `install-linux.sh` et `uninstall-linux.sh`.
- [ ] Compléter le responsable et les coordonnées réelles dans la politique de confidentialité et les conditions.
- [ ] Confirmer les licences/permissions de chaque modèle, moteur et ressource réellement redistribué.
- [ ] Signer/notarier le bundle macOS si on vise une distribution grand public sans avertissement Gatekeeper.
- [ ] Confirmer que les paquets n'embarquent pas involontairement les répertoires runtime, les modèles locaux, les journaux ou des informations personnelles.
