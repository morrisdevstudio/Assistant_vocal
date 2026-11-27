# Installer Alfred sur Debian 13 amd64

Le même paquet sert au serveur de dev et à la VM de prod. Il contient le code,
les dépendances Python, le worker Parakeet compilé pour Linux et les fichiers
statiques de la PWA. Les modèles, profils privés, certificats et secrets sont
préparés une fois sur chaque machine.

## Installer avec APT

Le paquet de l’assistant est `alfred-home`. Debian réserve déjà le nom `alfred`
à son service réseau A.L.F.R.E.D.

Ajouter une fois le dépôt de son environnement et la clé **publique** de
signature. Vérifier l’empreinte de la clé auprès de la personne qui administre
le dépôt. L’exemple suppose que le canal `prod` est servi à l’URL indiquée :

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -m 0644 alfred-home.asc /etc/apt/keyrings/alfred-home.asc
sudo tee /etc/apt/sources.list.d/alfred-home.sources >/dev/null <<'EOF'
Types: deb
URIs: https://depot.example.lan/alfred/prod/
Suites: ./
Architectures: amd64
Signed-By: /etc/apt/keyrings/alfred-home.asc
EOF
sudo apt update
sudo apt install alfred-home
```

Utiliser le canal `dev` sur le serveur de dev. On peut également utiliser une
URI `file:///srv/alfred-apt/prod/` si le dépôt est présent sur la VM. APT doit
pouvoir lire ses fichiers et traverser ses répertoires. Configurer un seul
canal Alfred par instance.

Pour mettre à jour Alfred, lancer `sudo apt update` puis `sudo apt install
--only-upgrade alfred-home`. Pour revenir à une version encore disponible
dans le dépôt, utiliser par exemple
`sudo apt install --allow-downgrades alfred-home=0.6.0-1`. La mise à jour et
le retour arrière conservent les données courantes et créent une sauvegarde
avant la bascule. `sudo apt remove alfred-home` arrête et désactive le service
et conserve les données, les réglages, les sauvegardes et les copies locales
des versions sous `/opt/alfred`.

Un `.deb` reçu séparément s’installe avec `sudo apt install ./alfred-home_0.6.0-1_amd64.deb`.
Si une ancienne archive a installé le service local `alfred.service`, arrêter
et désactiver cette unité avant le passage à `alfred-home.service`. Vérifier
qu’elle lance bien l’assistant depuis `/opt/alfred/current` avant d’y toucher.

## Construire le paquet

Sur un poste Debian 13 amd64 équipé de Python 3.13 et `python3-venv`, de Git,
de Rust/Cargo stable, de Node.js 24 et de npm, ainsi que de `build-essential`,
`pkg-config`, `libssl-dev` et `ca-certificates` :

```bash
bash deploy/debian/build.sh HEAD .local/debian-packages 1
```

Remplacer `HEAD` par le tag ou le commit voulu. Le build prend les fichiers
versionnés de cette révision. Le dernier argument est la révision Debian à
augmenter pour chaque nouveau paquet d’une même version d’Alfred. Pour la
version source `0.6.0`, cet exemple produit `alfred-home_0.6.0-1_amd64.deb`.
Le build écrit aussi l’archive autonome et les SHA-256 dans le dossier de
sortie. Pour une version officielle, conserver les fichiers de distribution
dans GitHub Releases.

### Préparer le dépôt signé

Sur la machine qui gère le dépôt, installer `apt-utils` et `gnupg`. Utiliser
une clé GPG de signature détenue par l’administrateur du dépôt. La clé privée
reste dans son trousseau. Avec son empreinte dans `ALFRED_SIGNING_FINGERPRINT` :

```bash
bash deploy/debian/apt-repo.sh /srv/alfred-apt dev "$ALFRED_SIGNING_FINGERPRINT" \
  .local/debian-packages/alfred-home_0.6.0-1_amd64.deb
```

Le script prépare `Packages`, `InRelease` et `alfred-home.asc` dans le canal
choisi. Servir les fichiers du canal en HTTPS ou les copier sur la VM pour
un dépôt local. Une fois la version validée en dev, lancer la même commande
avec `prod` et le **même `.deb`**.

### Distribuer directement avec GitHub Releases

Le dépôt public `morrisdevstudio/Assistant_vocal` peut servir les fichiers APT
comme pièces jointes d’une release. Préparer l’index signé à partir du `.deb`
de la révision destinée à ce tag. La machine de publication utilise `apt-utils`,
`gnupg` et la clé de signature déjà approuvée par les VM :

```bash
bash deploy/debian/github-release-assets.sh "$ALFRED_SIGNING_FINGERPRINT" \
  .local/debian-packages/alfred-home_0.6.0-1_amd64.deb .local/github-apt-v0.6.0
```

Joindre les six fichiers de ce dossier à la release GitHub, dont `InRelease`,
`Packages`, `Packages.gz` et `alfred-home.asc`. Publier d’abord comme
préversion pour les essais dev. Le serveur de dev peut viser le tag exact,
par exemple `https://github.com/morrisdevstudio/Assistant_vocal/releases/download/v0.6.0/`.
APT utilise `Suites: ./` et la clé publique via `Signed-By`, comme dans
l’exemple plus haut.

Sur la VM de prod, configurer une seule fois cette URI :

```text
URIs: https://github.com/morrisdevstudio/Assistant_vocal/releases/latest/download/
```

Après la recette dev, marquer cette même release stable et **Latest** sur
GitHub pour la rendre disponible à la prod. Garder les releases précédentes.
Pour revenir à une version antérieure dans cette configuration, pointer
temporairement la source APT vers l’URL de son tag, puis lancer `apt update`
et la rétrogradation explicite. Chaque release marquée Latest doit fournir
les fichiers APT si la VM suit cette URL.

## Première installation avec l’archive autonome

Sur la VM Debian, installer les dépendances système puis vérifier et extraire
l’archive à côté de son fichier SHA-256. Remplacer la variable `archive` par le
nom du fichier reçu :

```bash
sudo apt update
sudo apt install python3-venv libsndfile1 libgomp1 ca-certificates curl
archive='alfred-0.6.0-0123456789ab-debian13-amd64.tar.gz'  # adapter le nom
sha256sum -c "$archive.sha256"
tar -xzf "$archive"
sudo python3 "${archive%.tar.gz}/install.py"
```

L’installeur crée le compte `alfred`, installe les dépendances Python du paquet
hors ligne et active `alfred-home.service`. Vérifier l’API depuis la VM :

```bash
curl -fsS http://127.0.0.1:8765/health
sudo journalctl -u alfred-home.service -n 50
```

Pour ouvrir l’interface intégrée depuis un autre ordinateur tout en gardant
l’écoute locale par défaut, utiliser `ssh -L 8765:127.0.0.1:8765 utilisateur@IP_VM`,
puis ouvrir `http://127.0.0.1:8765`.

## Préparer la voix et les intégrations une fois par machine

1. Pour migrer `.local/data` depuis Windows, arrêter la source Windows et le
   service Debian avant la copie finale.
   Copier la base et les réglages utiles dans `/var/lib/alfred/data`, sous le
   compte `alfred`. Exclure les `*.secret` Windows et ressaisir les identifiants
   dans l’interface de cette instance. Utiliser des intégrations de test en dev.
2. Copier `parakeet-murmure-1.11.3` et `silero-v6` de `.local/models` dans
   `/var/lib/alfred/models`. Copier également `stt-murmure.json` dans
   `/var/lib/alfred/data`. Le worker Linux est déjà livré dans le paquet.
   Sélectionner le réveil STT Parakeet pour ce paquet Debian.
3. Copier les poids Phonon français Q8, le catalogue et les profils de voix
   requis vers les dossiers persistants de la cible. Dans le profil
   `phonon-dumby.json` ou le profil choisi, adapter `model_dir`, `voice_file`,
   `python` et `site_packages` aux chemins Debian. Le venv du service utilise
   `/opt/alfred/current/.venv/bin/python` et
   `/opt/alfred/current/.venv/lib/python3.13/site-packages`. Un chemin sous
   `current` suivra les mises à jour.
4. En prod, régler `media_host` de `terminal.json` sur l’IP LAN de la VM et
   vérifier le port TCP 8766 depuis le satellite. Activer ce terminal sur une
   seule instance. Redémarrer `alfred-home.service`, puis vérifier
   `/api/voice/status`, une transcription et une lecture ESP32. `/health`
   contrôle le démarrage et l’ordonnanceur.

Les fichiers de `/var/lib/alfred/data` doivent appartenir à `alfred:alfred`.
Le service doit pouvoir lire les modèles et les certificats, y compris la clé
serveur. Réserver l’accès aux fichiers de secrets et aux clés au propriétaire
et, si nécessaire pour la clé TLS, au groupe du service.

## Accès LAN et PWA

Pour utiliser le micro sur un navigateur via le LAN, fournir un certificat
reconnu par le navigateur pour l’IP utilisée. Placer `server.crt` et `server.key`
dans `/var/lib/alfred/https`, puis ajouter à `/etc/alfred/alfred.env` :

```dotenv
ALFRED_HOST=192.168.1.40
ALFRED_TLS=--https
```

Adapter l’IP. Si le certificat est signé par une autorité privée, indiquer en
plus son fichier public avec `ALFRED_TLS_CA` pour le contrôle de démarrage.
Redémarrer le service et garder l’accès sur le LAN ou le VPN. La protection de
l’accès familial reste à valider avant l’ouverture.

L’interface intégrée est servie par Alfred. Pour la PWA React, l’archive fournit
`/opt/alfred/current/pwa`. Son hébergement demande en plus un serveur HTTPS
statique avec le routage et les restrictions API décrits dans `ui/README.md`
du dépôt. Le service installé ci-dessus ne démarre pas de serveur Vite.

## Mettre à jour depuis l’archive autonome

Vérifier et extraire la nouvelle archive comme pour la première installation,
puis relancer son `install.py`. Le script prépare le venv et contrôle les imports
pendant que la version active tourne. Il arrête ensuite le service, sauvegarde
les données dans `/var/backups/alfred/`, active la version et attend `/health`.
Si le démarrage échoue, il tente de relancer la version précédente.

Pour revenir volontairement à la version précédente :

```bash
sudo python3 /opt/alfred/current/install.py --rollback
```

Le retour arrière bascule le code et conserve l’état courant. Si une migration
rend les données incompatibles, restaurer explicitement la sauvegarde adaptée
après avoir isolé les écritures nouvelles. Conserver aussi une copie de sauvegarde
hors de la VM et vérifier sa restauration sur une instance isolée.
