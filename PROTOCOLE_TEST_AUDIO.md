# Essai de réception — Waveshare ESP32-S3-AUDIO-Board

Préparé le 26 octobre 2026. Exécution partielle rapportée par l'utilisateur :
carte connectée à Home Assistant et contrôle des lumières réussi. Firmware,
moteurs initialement non précisés ; retour suivant : STT Home Assistant Cloud,
réveil plutôt satisfaisant au calme mais compréhension médiocre à débit naturel
ou rapide (« salon » devient « service »). Avec musique, environ une réussite sur
quatre estimée même en parlant très fort. Précision suivante : environ 1,50 m,
musique de fond jugée peu forte sur l'ampli externe, mot de réveil non reconnu.
Niveau sonore non mesuré ; réponse parlée restant à préciser.
Firmware confirmé ensuite : projet de jyoushiki,
installé depuis <https://jyoushiki.github.io/esphome-waveshare-esp32-s3-audio-va/> ;
version annoncée 2.0, suffixe exact et canal non inspectés. Cause non diagnostiquée.
Objectif : tester l'exemplaire reçu et la chaîne vocale, sans figer la pile Alfred.
Retour après déclenchement par bouton : STT jugé utilisable, à condition de bien
articuler ; résultat qualitatif, sans comptage ni transcription exacte relevés.
Sensibilité ensuite passée à `Moderately sensitive` (vérifiée via MCP HA), gain
resté à 13 : réveil jugé meilleur par l'utilisateur, sans mesures chiffrées.
Prévoir une première séance d'installation, puis environ 20 minutes de mesures.

## 1. Matériel

- Carte sur table, micros dégagés ; haut-parleur du kit branché, carte hors tension.
- Câble USB-C de données, PC avec Chrome ou Edge, Wi-Fi 2,4 GHz accessible à HA.
- Une lampe déjà commandable dans HA. Tester d'abord son bouton dans HA.
- Commencer à volume modéré. Ne pas supposer qu'une batterie ou une carte microSD
  est nécessaire au test Assist.
- Brancher et observer le comportement existant avant tout flashage. Noter s'il
  y a déjà une démo. Le flashage remplace le programme présent.

## 2. Préparer Home Assistant

Proposition locale, sans abonnement supplémentaire : Speech-to-Phrase pour les
commandes domotiques, Piper pour parler, agent de conversation Home Assistant.
Sur HAOS, installer et démarrer les apps Speech-to-Phrase et Piper depuis
Paramètres > Applications, puis ajouter les services Wyoming découverts dans
Paramètres > Appareils et services. Choisir le français et une voix française.
Si des moteurs sont déjà configurés, les essayer avant d'en ajouter.

Dans Paramètres > Assistants vocaux, créer « Test audio » : français, agent Home
Assistant, reconnaissance Speech-to-Phrase et synthèse Piper. Exposer la lampe
à Assist ; utiliser son nom exact dans les phrases ci-dessous. Tester dans Assist
en texte « Allume [nom de la lampe] », puis « Éteins [nom de la lampe] ».
Passer à la carte seulement lorsque le contrôle textuel fonctionne.

Source : https://www.home-assistant.io/voice_control/voice_remote_local_assistant/

## 3. Installer le satellite

Firmware communautaire spécifique au modèle, proposé comme banc d'essai :
https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va

Dans Chrome/Edge, ouvrir :
https://jyoushiki.github.io/esphome-waveshare-esp32-s3-audio-va/

Choisir Stable (v2.0.0 lors de la consultation), connecter le port série et suivre
l'installation. Reconnecter si demandé pour configurer le Wi-Fi. Ajouter le
satellite découvert via l'intégration ESPHome dans HA et sélectionner « Test audio ».
L'installation précompilée ne demande pas ESPHome Device Builder ni compilation.
Documentation : https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va/blob/main/docs/INSTALLATION.md

## 4. Essais progressifs

Réveiller avec « OK Nabu », attendre le signal d'écoute, puis parler normalement.
K2 peut aussi démarrer Assist au repos : utile pour distinguer un souci de réveil
d'un souci de transcription. K1/K3 règlent le volume ; BOOT coupe/rétablit le micro
dans ce firmware. Ne pas toucher à tous les réglages avant la première mesure.

| Essai | Manipulation | À noter |
|---|---|---|
| Proche, au calme | À 50 cm : allumer puis éteindre la lampe, 5 cycles | Réveil, bonne action, réponse audible, coupures |
| Distance | À 1 m puis 3 m : 5 commandes à chaque distance | Nombre de réussites et délai après la fin de phrase |
| Orientation | 3 commandes de face puis de côté | Différence de compréhension |
| Bruit ambiant | À 2 m, TV ou musique sur un autre appareil, 5 commandes | Niveau sonore, réussites, répétitions nécessaires |
| Haut-parleur | Écouter les confirmations à plusieurs volumes modérés | Intelligibilité, souffle, grésillement, saturation |
| Autre personne | Faire répéter 5 commandes au même endroit | Compréhension ; ceci ne teste pas une identité vocale |
| Faux réveils | 10 minutes de conversation/TV, sans appel volontaire | Activations spontanées |
| Stabilité | Débrancher/rebrancher une fois et refaire 3 commandes | Retour sur le réseau, réglages conservés |

Option : lancer une lecture sur le lecteur de la carte si disponible dans HA,
puis prononcer le mot de réveil pendant cette lecture. Distinguer ce test d'écho
de celui du bruit externe. Noter si la carte entend, baisse la musique et reprend
correctement. Un réveil pendant la lecture ne prouve pas à lui seul une interruption
conversationnelle complète.

Repères proposés, non contractuels : 9 commandes sur 10 réussies à 1 m au calme,
4 sur 5 à 3 m, réponses compréhensibles à 2 m et aucun redémarrage spontané.
Chronométrer de la fin de phrase à l'action et au début de réponse ; viser moins
de 3 secondes au calme comme première cible, sans garantie sur la VM actuelle.

## 5. Questions et limites

Demander d'abord « Est-ce que [nom de la lampe] est allumée ? » pour obtenir une
réponse vocale sur la maison. Les questions générales nécessitent un agent IA ;
Whisper permet une transcription ouverte, mais ne fournit pas l'intelligence de
conversation. Speech-to-Phrase est limité à des phrases de domotique prises en
charge. Ajouter une IA n'est pas nécessaire pour juger ce premier banc d'essai.

Le mot « Alfred », la confusion avec « Fred », les profils, les souvenirs, la
fenêtre de 8 secondes et l'interruption finale seront des tests distincts.

En cas d'échec : consulter le débogage de l'assistant dans HA. Pas de réveil :
contrôler mute et essai K2 ; mauvaise transcription : distance/bruit/moteur STT ;
texte correct mais mauvaise action : nom/exposition de la lampe ; action réussie
mais silence : volume, haut-parleur, Piper et URL locale HA accessible à la carte.
Source : https://www.home-assistant.io/voice_control/troubleshooting/

## Relevé sans audio brut ni données de profils

Firmware : ____ ; moteurs : ____ ; pièce : ____ ; volume : ____

| Distance/bruit | Réveils réussis / essais | Actions correctes / essais | Délai action / parole | Qualité et anomalies |
|---|---|---|---|---|
| 50 cm, calme | | | | |
| 1 m, calme | | | | |
| 3 m, calme | | | | |
| 2 m, TV/musique externe | | | | |
| Lecture sur la carte | | | | |

## Latence d’allumage sur Alfred

Lancer le banc sur le PC qui héberge Alfred, avec le terminal ESP32 connecté et en
veille. Exemple avec la lampe du plan de travail et les deux lumières principales
de la cuisine, relevées dans le catalogue réel d’Alfred.

```powershell
.\.venv\Scripts\python.exe -m alfred.light_benchmark `
  --url https://192.168.1.23:8765 --ca .local/https/server.crt `
  --lampe "la lumière plan de travail" --entite light.plan_de_travail_cuisine `
  --piece Cuisine --du "de la cuisine" --dans "dans la cuisine" `
  --entites-piece light.plan_de_travail_cuisine light.plafonnier_cuisine
```

Le banc propose cinq formulations, trois fois chacune, en alternant les cas.
Éteindre les cibles avant l’armement et attendre la veille. Après l’invite,
prononcer le mot de réveil suivi de la phrase, une seule fois. Indiquer ensuite
si toutes les lampes attendues se sont physiquement allumées et si la demande
a abouti du premier coup. Inclure les ratés et les demandes de précision. Si le
terminal attend une précision, le laisser revenir en veille avant l’essai suivant.

Après chaque essai, le banc écrit `essais.csv`, `bilan.md` et `traces.json`
dans un dossier horodaté sous `.local/light-benchmark/`. Les balises du serveur
utilisent un temps relatif à la fermeture de la capture. Le dernier bloc détecté
comme parlé donne une estimation de la fin de phrase. Les durées de catalogue
sont incluses dans les étapes qui les déclenchent. Un état `on` est relevé au
moment de sa lecture par Alfred. Le premier son audible et l’instant physique
d’allumage peuvent être chronométrés séparément par enregistrement externe.

Les traces exportées contiennent les phrases de test prévues, les cibles, les
durées et les statuts. La transcription réelle peut être consultée dans les
diagnostics existants d’Alfred via l’identifiant de l’échange.
