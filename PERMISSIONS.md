# Autorisations et accès système VYNEX

VYNEX n’a pas besoin de privilèges administrateur/root pour son usage normal. Il n’utilise pas de caméra, de contacts ni de localisation dans cette version. Les demandes ci-dessous sont facultatives et associées à une action de l’utilisateur.

| Fonction | Quand | Contrôle dans VYNEX | Limites du système |
|---|---|---|---|
| Microphone | Lorsque l’utilisateur démarre la dictée ou la conversation vocale | Confirmation mémorisée ; révocation depuis Paramètres > Données & confidentialité | Windows/macOS peuvent exiger une autorisation OS ; Linux dépend de l’environnement audio et de ses politiques |
| Capture d’écran | Lorsque l’utilisateur clique sur Capture d’écran | Confirmation d’autorisation mémorisée + confirmation pour chaque capture | macOS peut demander l’accès à l’enregistrement de l’écran dans Confidentialité et sécurité |
| Images/fichiers | Après sélection dans une boîte de dialogue de fichiers | L’utilisateur choisit explicitement les éléments | Les permissions de fichiers du système s’appliquent |
| Accès réseau aux moteurs d’IA | Au démarrage et lors des requêtes d’IA | Services par défaut sur l’interface loopback ; avertissement quand un endpoint de chat externe est configuré | Un service local ou tiers installé doit avoir sa propre configuration de sécurité |

## Réglages OS

- **Windows 10/11 :** Paramètres Windows > Confidentialité (ou Confidentialité et sécurité) > Microphone. Vérifiez les réglages applicables aux applications de bureau.
- **macOS :** Réglages Système > Confidentialité et sécurité > Microphone et Enregistrement de l’écran. Les intitulés peuvent varier selon la version de macOS.
- **Linux :** vérifiez les paramètres de votre environnement de bureau et de votre serveur audio (par ex. PipeWire/PulseAudio) si le microphone ne fonctionne pas. Il n’existe pas une boîte de dialogue de permissions uniforme pour tous les environnements Linux.

## Informations de compilation macOS

Le bundle de cette préversion définit les chaînes `NSMicrophoneUsageDescription` et `NSScreenCaptureUsageDescription` dans son `Info.plist`. Apple exige une description de motif pour les applications qui demandent l’accès au microphone ; les autorisations système restent sous le contrôle de l’utilisateur. La préversion demeure non signée/non notariée dans le workflow actuel.

Références officielles :
- Apple — [NSMicrophoneUsageDescription](https://developer.apple.com/documentation/bundleresources/information-property-list/nsmicrophoneusagedescription)
- Apple — [ScreenCaptureKit](https://developer.apple.com/documentation/ScreenCaptureKit)
- Microsoft — [Privacy Policy CSP: access to microphone](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-privacy)
