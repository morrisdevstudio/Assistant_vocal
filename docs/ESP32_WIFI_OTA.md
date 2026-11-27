# Satellite Alfred en Wi-Fi et maintenance OTA

## Fonctionnement retenu — 15 novembre 2026

La Waveshare du bureau fonctionne sur une prise USB, sans liaison USB au PC.
L'utilisateur confirme cette alimentation ; la carte est identifiée sur le LAN.
Alfred reste nécessaire : réveil STT/openWakeWord, transcription, dialogue et voix
tournent sur le serveur. Le navigateur peut être fermé. Le choix du moteur, du
modèle, de la phrase STT et du seuil reste dans l'interface, sans OTA.

État vérifié : firmware jyoushiki **v2.0.0**, ESPHome **2026.9.0**, hôte
`waveshare-voice-eb05fc.local`, adresse observée `192.168.1.180`. Le pont résout
ce nom à chaque reconnexion et vérifie la MAC attendue. Aucune réservation DHCP
n'a été ajoutée au routeur. Le serveur reste sur `192.168.1.23` ; un changement
d'hôte exige d'adapter `media_host` dans la configuration privée du terminal.

Les connexions utiles restent l'API ESPHome TCP 6053, l'audio de retour TCP 8766
sur Alfred et la maintenance OTA TCP 3232 sur la carte. Aucun port Internet ajouté.
La connexion de cette carte à Home Assistant reste désactivée.

## Démarrage et reprise de veille

- Activer la veille ESP32 dans l'interface mémorise sa reprise au prochain
  démarrage du service. La carte peut être absente au démarrage : Alfred attend
  son retour et réarme le flux.
- Arrêter volontairement cette veille, ou activer la veille navigateur, annule
  cette reprise. Fermer le navigateur ne réactive pas l'ESP32.
- Les anciens réglages sans préférence de reprise restent arrêtés jusqu'à une
  activation explicite. La source active de cette installation a été conservée
  lors de l'adoption. Le marqueur `resume_esp32` est privé, dans
  `.local/data/wake-settings.json`, à côté des réglages des deux sources.
- La tâche Windows **Alfred Assistant Vocal** démarre à l'ouverture de session.
  Le lanceur masqué attend désormais le service et transmet son code de sortie ;
  la tâche prévoit trois reprises sur échec, espacées d'une minute, sans limite
  de durée. Le PC doit rester allumé avec la session démarrée ; une migration
  vers la VM Debian sera traitée séparément.

Sauvegardes antérieures du lanceur et de la tâche :
`.local/backups/satellite-20261115/`. Les réglages vocaux présents sont conservés.

## Couleurs de l’anneau

Dans la PWA, ouvrir **Paramètres → Voix et conversation → LED du satellite ESP32**.
Chaque état peut recevoir une couleur, être éteint et mémoriser un effet.
Sur la Waveshare, choisir Fixe, Rotation, Comète, Respiration ou Balayage.
L’effet s’applique quand les LED sont allumées. La palette est partagée entre navigateurs et reste enregistrée sur Alfred. L’anneau s’éteint en veille
par défaut, même lorsque le mot d’appel est actif. Les signaux natifs du micro
coupé, du volume, du minuteur et de la déconnexion sont gérés par la carte.

## Vérifier sans flasher

Depuis la racine du projet, sous PowerShell :

```powershell
.venv\Scripts\python.exe scripts\esp32_satellite.py
```

Le script vérifie d'abord la MAC via l'API, puis négocie le protocole OTA.
Il ferme la connexion **avant tout envoi de taille ou de firmware**, sans
préparer ni effacer de partition. La carte répond en OTA version deux, sans
authentification OTA dans son firmware actuel ; aucun mot de passe n'est inventé.
Ce contrôle ne prouve pas à lui seul un transfert et un démarrage après OTA.

Pour un redémarrage ciblé, hors conversation ou sonnerie :

```powershell
.venv\Scripts\python.exe scripts\esp32_satellite.py --restart
```

La MAC est également vérifiée avant cette commande. Un redémarrage réel a montré
les transitions déconnecté → connecté → réception micro, veille toujours armée.
Le redémarrage du serveur a aussi repris le flux sans ouverture du navigateur.
La lecture d'un extrait Phonon a été téléchargée et sa fin confirmée par la carte ;
l'écoute humaine de cet essai reste distincte de cette confirmation technique.

## Préparer une future mise à jour

Aucun flashage nécessaire pour l'usage sur prise USB : l'OTA est déjà présent.
Les mises à jour du logiciel serveur Alfred ne demandent généralement pas de
mise à jour du firmware ESP32.

La recette `firmware/waveshare.yaml` reprend les sources v2.0.0 au commit
`c86ecd3c5124db85181c03ad35aec6578b82b849`, ESP-IDF 5.5.5 et ESP-SR 2.5.5.
La pile audio amont est référencée par le tag v2026.10.2, vérifié au commit
`0482d741a938378ef948e3b8f3dd31536f9f2cc9` ; vérifier cette référence avant une
future reconstruction. Les manifests de réveil et les sons sont épinglés par
l'amont. Cette base conserve codecs, boutons, LED et services utilisés par Alfred.

Environnement de maintenance **Windows**, séparé du serveur :

```powershell
uv venv --python 3.13 .local/esphome-env
uv pip install --python .local/esphome-env/Scripts/python.exe -r firmware/toolchain-requirements.txt
.local\esphome-env\Scripts\python.exe -m esphome config firmware\waveshare.yaml
.local\esphome-env\Scripts\python.exe -m esphome compile firmware\waveshare.yaml
```

ESPHome 2026.9.0 et les dépendances Python de cet environnement sont verrouillés.
Validation du 15 novembre : configuration et compilation complètes réussies ;
binaires `firmware.ota.bin` et `firmware.factory.bin` produits dans
`firmware/.local/esp32-build/build/`. Application d'environ 2,6 Mo pour une
partition de 8,1 Mo. Aucun de ces binaires n'a été transféré à la carte.
Ce verrou Windows comprend des paquets propres à Windows ; il ne constitue pas
une recette d'installation Debian. Les caches et sorties de compilation sous
`firmware/.esphome/` et `firmware/.local/` sont exclus de Git.

Pour une mise à jour nécessaire : compiler d'abord, arrêter la veille depuis
l'interface, vérifier l'identité avec le script, puis transférer :

```powershell
.venv\Scripts\python.exe scripts\esp32_satellite.py
.local\esphome-env\Scripts\python.exe -m esphome upload firmware\waveshare.yaml --device waveshare-voice-eb05fc.local
```

Réactiver ensuite la veille dans l'interface et vérifier version, micro,
haut-parleur, boutons et sonneries. Le Wi-Fi provisionné est réutilisé lors d'une
OTA sans effacement ; aucun identifiant Wi-Fi n'est inscrit dans cette recette.
Tout ajout futur d'authentification OTA doit utiliser un secret local exclu de Git.

## Récupération

Les binaires officiels v2.0.0 OTA et factory sont conservés sous
`.local/esp32-recovery/v2.0.0/`, avec leurs SHA-256 vérifiés et leurs URL dans
`checksums.json`. Ne jamais envoyer le binaire factory par OTA.

Le mode de secours ESPHome conserve réseau et OTA après des échecs de démarrage.
Il ne garantit pas la récupération si le Wi-Fi est inaccessible et ne constitue
pas un retour automatique à l'ancien firmware. Garder un accès physique USB.

En récupération USB : arrêter la veille, connecter la carte au PC, identifier son
port et passer en mode téléchargement selon la documentation matérielle. Le
manifest officiel place le binaire factory à l'adresse zéro. Exemple, en
remplaçant `COMx` par le port réellement identifié :

```powershell
.local\esphome-env\Scripts\python.exe -m esptool --chip esp32s3 --port COMx write-flash 0x0 .local\esp32-recovery\v2.0.0\waveshare-voice-esp32s3.factory.bin
```

Reprovisionner le Wi-Fi par Improv série si nécessaire, puis vérifier l'identité,
la connexion et réactiver la veille. Aucune récupération USB ni OTA réelle n'a
été exécutée pendant l'adoption.

Références : [OTA ESPHome](https://esphome.io/components/ota/esphome/),
[mode de secours](https://esphome.io/components/safe_mode/),
[version amont v2.0.0](https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va/releases/tag/v2.0.0),
[carte Waveshare](https://docs.waveshare.com/ESP32-S3-AUDIO-Board).

Restent à recetter : coupure réelle du point d'accès Wi-Fi, conversation humaine
après déplacement, et transfert OTA lors d'une mise à jour utile.

Non-régression du serveur : **810 tests Python réussis, deux tests optionnels
ignorés ; 43 tests JavaScript réussis**. Les cas ajoutés couvrent la migration
des préférences, la reprise avant disponibilité réseau et après deux démarrages,
les deux commandes d'arrêt et l'absence de reprise après transfert navigateur.
