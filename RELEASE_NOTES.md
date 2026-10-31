## VYNEX 0.1.0-preview.4

Préversion multiplateforme pour essais communautaires.

### Inclus
- Interface VYNEX et robot logo.
- Historique local avec suppression individuelle des discussions et confirmation.
- Modèles de conditions/confidentialité et consentements intégrés dans l'application.
- Archives de bureau générées pour Windows x64, macOS Apple Silicon, macOS Intel et Linux x64.

### À connaître
- Les moteurs et modèles IA sont séparés et doivent être installés pour activer le chat, la vision et la création d'images.
- macOS n'est pas signé/notarié par défaut ; Windows peut afficher un avertissement SmartScreen.
- Cette préversion nécessite des essais manuels sur les systèmes cibles et ne doit pas être présentée comme stable avant ces vérifications.

## Audit technique — Preview 0.1.0-preview.4

- Corrige l’import `urlparse`, nécessaire aux vérifications du serveur IA avant envoi et dans les paramètres.
- Rend le chemin du runtime Windows portable : privilégie l’ancienne installation si elle existe, sinon `%USERPROFILE%\VYNEXRuntime`, avec surcharge possible par `VYNEX_HOME`.
- Améliore le chemin signalé lorsque les fichiers du modèle sont manquants.
- Ajoute des tests de régression sur l’import et le chemin runtime portable.
