# Construire et publier VYNEX pour Windows, macOS et Linux

## Ce qu'on fabrique

Le dépôt inclut des scripts locaux et un workflow GitHub Actions. Les paquets visés sont :

- Windows x64 : `VYNEX-windows-x64.zip` (dossier `.exe` + fichiers d'exécution).
- macOS Apple Silicon : `VYNEX-macos-arm64.zip` (app `.app` compressée).
- macOS Intel : `VYNEX-macos-intel.zip` (app `.app` compressée).
- Linux x64 : `VYNEX-linux-x64.tar.gz` (application et scripts d'installation locale).

Les compilations doivent se faire sur un runner du système cible. Un EXE Windows ne peut pas être transformé localement en app macOS/Linux en changeant simplement l'extension.

## Compilation locale

### Windows

Ouvre PowerShell dans le dossier extrait du projet et exécute :

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\BUILD_WINDOWS_SAFE.ps1
```

Le script crée de nouveaux dossiers horodatés et n'efface pas un ancien dossier `dist` qui pourrait contenir une DLL verrouillée. Il affiche le chemin de `VYNEX.exe` et de l'archive ZIP finale.

### macOS

Installe Python 3.10+ avec Tkinter, ouvre Terminal dans le dossier projet et exécute :

```bash
bash ./BUILD_MACOS.sh
```

Le résultat est un `.app` zippé. Il n'est pas signé/notarié par Apple par défaut et peut afficher un avertissement Gatekeeper.

### Linux

Sur Ubuntu/Debian, installe les prérequis avec `sudo apt install python3-tk python3-venv python3-pip`. Puis exécute :

```bash
bash ./BUILD_LINUX.sh
```

Le `.tar.gz` généré contient `install-linux.sh`. Après extraction, `bash ./VYNEX/install-linux.sh` installe VYNEX dans `~/.local/opt/vynex` et ajoute un raccourci au menu des applications. Pour retirer l'application sans supprimer les conversations, lance `bash ~/.local/opt/vynex/uninstall-linux.sh`.

## Générer les quatre paquets automatiquement depuis Windows (recommandé)

Le PC Windows ne peut pas construire localement le bundle `.app` macOS ou le binaire Linux. Le workflow `.github/workflows/release.yml` utilise les runners officiels Windows, Linux, macOS ARM64 et macOS Intel de GitHub Actions. Le projet ne sera pas publié tant qu'il n'est pas envoyé à un dépôt GitHub.

1. Crée un nouveau dépôt vide sur https://github.com/new. Un nom possible est `vynex-desktop`. Ne coche pas l'ajout automatique d'un README ou d'une licence : le pack en a déjà un.
2. Installe Git pour Windows si `git --version` ne fonctionne pas.
3. Extrais le pack dans un dossier stable, par exemple `D:\MonIA\VYNEX_CrossPlatform_Release`.
4. Dans PowerShell, passe dans le dossier extrait. Exécute les commandes ci-dessous, en remplaçant `TON-COMPTE` par le nom du compte GitHub et l'URL si tu as choisi un autre nom de dépôt :

```powershell
git init
git add .
git commit -m "Prepare VYNEX multiplatform preview"
git branch -M main
git remote add origin https://github.com/TON-COMPTE/vynex-desktop.git
git push -u origin main
```

Si Git demande de configurer `user.name` ou `user.email`, utilise le nom et l'adresse associés à ton compte. L'authentification GitHub peut s'ouvrir dans le navigateur.

5. Sur GitHub, ouvre le dépôt puis l'onglet **Actions**. Le workflow démarre automatiquement sur `main`. Vérifie que les quatre jobs ont réussi. Les artefacts de test sont temporaires.
6. Quand les builds sont verts, crée la release officielle de préversion en poussant un tag :

```powershell
git tag v0.1.0-preview.4
git push origin v0.1.0-preview.4
```

7. Ouvre l'onglet **Actions** jusqu'à la fin du workflow. Quand toutes les compilations réussissent, l'onglet **Releases** doit contenir les archives Windows, macOS ARM64, macOS Intel et Linux. Si un job échoue, ne partage pas de lien de téléchargement comme si les paquets étaient prêts ; ouvre les logs de ce job et corrige l'erreur.

## Limites à connaître avant de distribuer

- GitHub Releases distribue les fichiers, ce n'est pas la même chose qu'une publication dans Microsoft Store, Apple Mac App Store ou un dépôt Linux officiel.
- L'application macOS n'est pas signée/notariée dans cette première préversion. Windows peut afficher SmartScreen ; macOS peut afficher Gatekeeper.
- Les dépendances système, modèles et moteurs IA ne sont pas empaquetés. Voir `RUNTIME_SETUP.md`.
- Les paquets n'ont pas encore été testés manuellement sur chaque système. Le workflow vérifie syntaxe/tests et construction du paquet, mais il faut faire des essais sur les vrais OS avant de qualifier la version de stable.
- Les politiques de confidentialité et conditions sont des modèles de prépublication ; compléter les coordonnées réelles et vérifier les licences des modèles/moteurs avant toute diffusion publique.
