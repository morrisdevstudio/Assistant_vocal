# ESP32 relié directement à Alfred

**15 novembre 2026 — satellite Wi-Fi sur prise USB adopté.** La carte réelle est
identifiée, l'OTA répond et les redémarrages carte/serveur rétablissent la veille
sans navigateur. Firmware conservé, réveil toujours réglable depuis l'interface.
Voir `docs/ESP32_WIFI_OTA.md` pour l'exploitation actuelle, les commandes de
maintenance et les limites de validation. Les sections datées ci-dessous
conservent les essais historiques ; les voix et moteurs courants sont ceux de
`CADRAGE.md`.

État du 2 novembre 2026 : prototype réseau opérationnel avec la Waveshare et
son firmware **jyoushiki v2.0.0 / ESPHome 2026.9.0**, sans reflasher la carte.
La connexion ESPHome et le relais Music Assistant dans Home Assistant restent
désactivés. Alfred utilise lui-même l'API native ESPHome.

## Essayer

1. Ouvrir ou actualiser l'interface Alfred. Dans le laboratoire vocal, vérifier
   l'état **ESP32 connecté**, puis cliquer **Écouter sur l'ESP32** pour jouer la
   voix de référence sur le haut-parleur de la carte.
2. Pour parler, appuyer sur **K2**, attendre le signal et dire « Bonjour Alfred ».
   La phrase est envoyée après environ 900 ms de silence ; Alfred utilise la
   même transcription, les mêmes outils et la même voix que dans le navigateur.
3. Après la réponse, une reprise de parole de huit secondes est prévue par le
   pont et le protocole du firmware. Le silence ne déclenche aucun appel IA.
   Ce parcours complet et son réglage acoustique restent à valider en personne.
4. K2 permet aussi d'arrêter une demande en cours selon le comportement du
   firmware. BOOT commande le mute matériel ; K1/K3 règlent le volume. Le mot
   de réveil « Alfred » n'est pas installé : utiliser K2 pour ce premier banc.

La voix retenue est `alfred-reference`, débit 1,242, sans patine ni effet. Le
serveur convertit le WAV en **FLAC mono 48 kHz** pour le lecteur du firmware,
avec rééchantillonnage ; le profil et le débit ne changent pas.

### Réponses progressives — 4 novembre

Le terminal reçoit désormais un **flux audio progressif** : dès les premières
phrases synthétisées, la carte peut les lire pendant le calcul des suivantes.
Un seul encodeur FLAC est conservé pour toute la réponse ; les fichiers FLAC ne
sont pas simplement collés. Le profil vocal reste verrouillé pendant tous les
blocs. La ponctuation et les mots sont préservés, aucun silence n'est ajouté.

La réponse de l'IA et les résultats des outils sont finalisés avant de commencer
la voix. Ce mode accélère la partie vocale ; il ne supprime pas la transcription
ni l'attente de l'IA. Le navigateur garde son parcours audio complet habituel.

Sur le PC i7-13700KF, Supertonic utilise quatre threads. Au lancement Windows,
Alfred demande HighQoS pour son seul processus et la tâche est en priorité
normale : pas de priorité haute, pas d'affinité CPU forcée, pas de changement du
plan d'alimentation global. Sur un texte témoin, la synthèse chaude complète a
été mesurée à environ 2,33 s contre 6,4 s avant HighQoS. Ne pas extrapoler au
futur serveur ; des mesures sur cet hôte resteront nécessaires.

Lors du test matériel progressif, la carte a demandé le premier bloc à **2,05 s**,
alors que l'audio complet n'était prêt qu'à **4,48 s**. Quatre blocs, 14,98 s
d'audio, fin de lecture confirmée. Ce diagnostic commence à la synthèse et
n'inclut pas STT/IA ; il ne mesure pas le son au haut-parleur. L'écoute humaine
du 5 novembre confirme une voix propre, avec de petites pauses audibles.
La correction suivante raccourcit seulement l'excédent de silence aux jonctions :
les blocs témoins cumulaient 1 à 1,2 s de silence, contre environ 0,29 s après
correction. Marges protectrices autour de la parole, début et fin de l'énoncé
et pauses internes conservés ; ni timbre, ni vitesse, ni niveau de parole modifiés.
Sur les mêmes quatre blocs, 2,575 s de calme retirées. Le seuil RMS bas et les
marges sont testés sur des consonnes faibles ; aucun filtre ni fondu de voix.
Correction déployée et extrait rejoué : lecture terminée selon la carte, 12,70 s
d'audio, 2,276 s de marges retirées sur cette nouvelle génération. Le compteur
`trimmed_silence_ms` permet de suivre cette correction sans conserver le texte.
Après rejeu, l'utilisateur valide la nouvelle lecture le 5 novembre (« c'est très
bien »). Correction conservée. La latence globale reste à apprécier après une
demande réelle en conversation ; elle n'est pas mesurée par ce sample.

## Configuration et lancement

La configuration du terminal est privée et locale : `.local/data/terminal.json`.
Elle contient `enabled`, `host`, `expected_mac`, `media_host`, `media_port`,
`floor_id` et `room`. `progressive_tts` vaut `true` par défaut ; le mettre à
`false` puis redémarrer revient à la génération complète avant lecture.
La connexion vérifie la MAC attendue avant toute
souscription micro ou commande audio. La carte actuelle utilise l'API native
LAN sans chiffrement de son firmware d'origine ; aucun secret n'est ajouté.

Le service habituel démarre le pont automatiquement :

```powershell
Start-ScheduledTask -TaskName 'Alfred Assistant Vocal'
```

Les dépendances supplémentaires sont épinglées dans `requirements.lock.txt` et
l'extra `terminal` de `pyproject.toml` : aioesphomeapi 46.25.1, soundfile 0.14.0,
scipy 1.18.1. Les moteurs vocaux restent ceux du serveur Alfred.

Pour désactiver le pont sans toucher à la carte, mettre `enabled` à `false` dans
ce fichier puis redémarrer le service. Le firmware reste intact ; l'ancien banc
HA et ses routages ont leur sauvegarde locale du retrait du 2 novembre.

## Transport et diagnostics

- API native du terminal : TCP 6053, connexion initiée par Alfred.
- Retours audio : serveur HTTP local TCP **8766**, exclusivement pour la carte
  configurée. Un jeton aléatoire désigne chaque réponse, valable 90 secondes ;
  l'adresse source doit correspondre à la carte. Aucun accès à un fichier du PC,
  aucun index, deux réponses en mémoire au maximum, prise en charge HTTP Range.
- Le micro utilise `API_AUDIO` sur la connexion TCP : PCM16 mono 16 kHz.
  Pré-capture courte, durée maximale de 30 secondes et détection de parole
  Silero VAD v6 locale depuis le 6 novembre. L'ancien seuil de volume pouvait
  retenir la prise tant qu'un fond musical continuait. Le scénario utilisateur
  avec chant externe est validé après correction ; d'autres chants ou voix de
  télévision peuvent encore être classés comme parole.
  La pièce Bureau correspond au défaut domotique actuellement vérifié ; le
  routage de plusieurs pièces reste à concevoir en T06.
- La voix n'est captée qu'après activation bouton/réveil ou pendant la fenêtre
  de reprise. Ni le PCM entrant, ni les réponses temporaires ne sont écrits.
- `GET /api/terminal/status` publie connexion, phases, compteurs et timings,
  sans transcription, réponse, empreinte vocale ou URL temporaire.
- `POST /api/terminal/test` avec un corps JSON `{}` joue le sample, attend la
  confirmation de fin et indique si la carte l'a téléchargé. Cela ne prouve pas
  qu'une personne l'a entendu.
- `POST /api/terminal/test-microphone` avec `{}` active le micro deux secondes
  pour mesurer le transport, sans transcription, IA ni action. Les octets sont
  comptés puis jetés.
- `POST /api/terminal/test-progressive` avec `{}` lit un extrait en plusieurs
  blocs, sans lancer une conversation après. Les compteurs indiquent combien
  de blocs étaient prêts lors de la demande audio et quand le dernier a été produit.
- Les timings de `/api/terminal/status` incluent transcription/IA, premier bloc
  vocal, génération totale et première demande réseau, sans exposer le texte.
  `speech_detector` indique le détecteur actif et `last_capture.end_reason`
  distingue pause de parole, durée maximale ou arrêt/timeout. Le résultat du
  test de transcription affiche ce motif dans la page.

Une nouvelle activation ou un arrêt annule le traitement serveur encore en
cours. Une action déjà exécutée n'est pas annulée ni rejouée automatiquement.
Les garanties d'interruption acoustique, l'arbitrage multi-terminaux, la diffusion
des échéances et les profils restent dans leurs tâches ouvertes. Les sonneries
et annonces autrefois routées via HA vers cette carte ne sont pas réactivées
par ce prototype conversationnel.

## Mot d'appel « Hé Alfred » — 6 novembre

**Banc temporaire actuel au 8 novembre : « Jarvis »**, modèle fourni par
l’utilisateur dans `docs/jarvisse_20260916_004415.onnx`. Version ONNX chargée
sur le PC, seuil 0,5, vérificateur STT du mot désactivé. Le fichier TFLite
fourni reste disponible dans `docs/` ; aucun flashage nécessaire.

Dans `.local/data/terminal.json` : `wake_model=jarvisse_20260916_004415.onnx`,
`wake_name=jarvis`, `wake_verify=false`, `wake_threshold=0.5`.
Après redémarrage, ouvrir le laboratoire vocal et cliquer **Activer « Jarvis »**
si la veille est inactive. Attendre « Veille active », puis dire naturellement
« Jarvis, quelle heure est-il ? ». Essayer aussi une commande après huit secondes
sans parler pour vérifier un nouveau réveil. Jarvis/Jarvisse sont retirés du début
des commandes directes. L’assistant conserve son nom Alfred.

La configuration précédente Alexa est sauvegardée dans
`.local/data/terminal.before-jarvis.json`. Pour restaurer « Hé Alfred », remettre
`wake_model=alfred-he.onnx`, `wake_name=alfred`, `wake_verify=true` et
`wake_threshold=0.25`, puis redémarrer le service. Les instructions ci-dessous
concernent le mode « Hé Alfred » ; pour le banc actuel remplacer le mot par Jarvis.

Le mot d'appel est détecté **sur le PC**, pas sur la carte. Aucun firmware n'a été
flashé : la binaire installée (ESPHome 2026.9.0, projet `jyoushiki.waveshare-voice`
v2.0.0) ne contient aucun modèle `micro_wake_word`, et le générateur utilisé produit
un modèle ONNX openWakeWord, inutilisable sur un microcontrôleur.

### Essayer

1. Vérifier que `wake_word` vaut `true` dans `.local/data/terminal.json`, puis
   redémarrer le service.
2. Dans le laboratoire vocal, cliquer **Activer « Hé Alfred »**. La ligne d'état
   indique la veille active seulement si des trames audio arrivent, avec le seuil
   et les compteurs. Sinon elle indique une reprise en cours ou une erreur.
3. Dire « Hé Alfred allume la lumière du salon » d'une traite. La veille ne fait
   que déclencher ; la commande est ensuite traitée comme au clavier. Le préfixe
   parlé est retiré : « hé / eh / hey / et / alors / euh » devant « Alfred » sont
   tous acceptés par les commandes de lumière, de minuteur, de musique et de courses.
4. **Arrêter la veille** coupe la détection. **Faux réveil** incrémente le
   compteur de faux déclenchements, utile pendant la recette.

Sans le bouton, K2 reste utilisable et la veille n'écoute pas. La veille est
volontairement opt-in : elle maintient la carte en train de streamer.

### Faisabilité et mode audio

La veille utilise le même mécanisme que la conversation : `start_va`, puis le
client Python répond par `VoiceAssistantResponse(port=0)`. Le firmware ne passe
en `STREAMING_MICROPHONE` qu'après cette réponse ; sans elle il démarre le micro,
rapporte `failed_to_start` et n'envoie aucune trame. Vérifié sur la carte réelle le
6 novembre : `handle_start` doit retourner 0 et le client envoie la réponse.

Mesure de tenue : **32 Ko/s exactement**, soit PCM16 mono 16 kHz, sans trou ni
erreur sur plus de dix minutes. La carte borne chaque session ; Alfred la
renouvelle tous les `wake_session_seconds - 10` et la relance après chaque
réponse.

### Contrat de la veille

- La veille passe par **la connexion ESPHome d'Alfred**, jamais par un second
  client. Vérifié le 6 novembre : le firmware n'accepte qu'un seul client Voice
  Assistant à la fois et ignore un `start_va` reçu d'un autre client, qui ne
  reçoit alors aucune trame (« Client attempting to unsubscribe that is not the
  current API Client » dans le code du composant). Une mesure tentée depuis un
  second processus a rendu 0 octet en onze minutes ; c'est une contrainte du
  firmware, pas un défaut d'Alfred.
- Les 2 s avant le déclenchement et jusqu'à 2 s supplémentaires servent en mémoire
  à vérifier localement le nom « Alfred » avant tout traitement. La prise de
  commande conserve son pré-roll de 0,6 s. Aucun audio n'est enregistré.
- Aucune trame n'est écrite, aucun texte n'est produit, aucun score ne quitte le
  processus : `status()` ne publie que des compteurs.
- La détection est ignorée pendant une prise et pendant la lecture, pour que le
  haut-parleur de la carte ne se déclenche pas lui-même.
- La carte borne ses sessions : Alfred la renouvelle avant expiration et la
  relance après chaque réponse, sans second départ utilisateur.
- Un déclenchement n'exécute aucune action à lui seul ; la phrase est ensuite
  traitée normalement, commande directe ou conversation.

### Réglages

Dans `.local/data/terminal.json` :

- `wake_word` : `false` par défaut ; `true` active la veille.
- `wake_model` : `alfred-he.onnx` par défaut.
- `wake_threshold` : `0.25` par défaut, strictement entre 0 et 1.
- `wake_session_seconds` : `900` par défaut, entre 30 et 3600.

Le modèle et ses deux modèles de prétraitement vivent sous
`.local/models/wake-word/`, hors Git. Préparation explicite :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_wake_word
.\.venv\Scripts\python.exe -m alfred.setup_wake_word --model .\output\alfred-he.onnx
```

Le prétraitement public est vérifié par SHA-256 ; un fichier altéré est refusé.
Le modèle entraîné porte une licence CC BY-NC-SA 4.0 (usage non commercial), et
son empreinte SHA-256 est enregistrée à côté du fichier.

La détection ajoute une dépendance Python verrouillée : `openwakeword==0.6.0`,
avec `scikit-learn`, `narwhals` et `threadpoolctl`, sur l'`onnxruntime` déjà
présent. Aucun PyTorch n'est requis côté Alfred : l'entraînement reste dans son
conteneur WSL séparé.

### Diagnostics

`GET /api/terminal/status` publie `wake_word` avec `enabled`, `armed`,
`detections`, `last_wake_at`, `threshold`, `false_alarms` et `error`. Aucun texte,
aucun audio, aucune empreinte. Routes de commande :
`POST /api/terminal/wake-word/start`, `.../stop`, `.../false-alarm`.

### Mesures de recette (voix de synthèse non vues)

Ces mesures utilisent **Supertonic M1–M5**, moteur et locuteurs distincts des voix
Piper qui ont servi à l'entraînement. Ce ne sont pas des voix humaines : la
recette à la voix réelle reste ouverte, mais ces chiffres sont le meilleur
contrôle de généralisation possible sans personne devant la carte.

- **Détection du mot, par prononciation** : « Hé Alfred » / « Et Alfred » donnent
  **14/15 (93 %)** sur les cinq voix ; la graphie anglaise « Hey Alfred », qui
  n'est pas la prononciation visée, tombe à 2/5. La phrase réellement dite est
  est détectée sur ces échantillons synthétiques ; cela ne prédit pas le taux
  de réussite sur une voix humaine. Les seuls échecs sont M3 sur « hé Alfrede ».
- **Effet du seuil** : à 0,5, M3 sur « Hé Alfred » plafonnait à 0,301 et échouait ;
  à 0,25 il passe à 0,502 et détecte. Le seuil ne sert pas qu'aux cas marginaux,
  il récupère une voix entière.
- **Faux réveils sur mots proches** : 0/27, « Fred » compris.
- **Faux réveils sur parole continue** : 0/12.
- **Flux continu d'une heure** : 0 déclenchement sur 60 minutes de parole
  enchaînée, puis 0 sur 60 minutes avec fond musical continu (accord tenu avec
  vibrato). Score maximal observé 0,020 contre 0,117 pour le négatif le plus
  proche en clip isolé.
- **Latence ajoutée** : 0 ms. La décision survient *pendant* l'énoncé ; la phrase
  dure 1,32 à 1,46 s et la détection tombe avant sa fin. Cette latence est celle
  du détecteur seul, pas du tour complet.
- **Séparation des scores** : médiane des positifs 0,963, maximum des négatifs
  0,117. Le seuil 0,25 se place dans un large vide, ce qui explique l'absence de
  faux réveil.

Le seuil par défaut est passé de 0,5 à **0,25** sur cette base : deux détections
gagnées, aucun faux réveil créé.

### Limites connues

Le détecteur ne distingue pas les locuteurs. La télévision, un chant ou une
conversation proche restent des sources possibles de faux réveils ; le compteur
`false_alarms` est là pour les mesurer. Un vérificateur en seconde passe
(transcrire les deux secondes par le STT et vérifier « Alfred ») n'est pas
engagé : il ne sera ajouté que si les mesures le justifient.


## Vérifications réelles effectuées

- Carte détectée en LAN et identité MAC vérifiée, firmware/version interrogés.
- Veille « Hé Alfred » validée le 6 novembre sur la carte réelle : `phase=waking`,
  **32 Ko/s** exactement (PCM16 mono 16 kHz), aucun trou ni erreur sur plus de
  dix minutes. Le firmware exige un `VoiceAssistantResponse(port=0)` pour passer
  en `STREAMING_MICROPHONE` ; sans lui il rapporte `failed_to_start` et n'envoie
  aucune trame. Un seul client Voice Assistant est accepté : la mesure depuis un
  second processus rend 0 octet.
- Modèle `alfred-he.onnx` (205 430 octets) entraîné en WSL Ubuntu avec Docker
  natif sur la RTX 2060 SUPER. Contrôle sur 40 clips de validation jamais vus :
  score maximal 0,970, 31/40 au-dessus du seuil, négatifs 0/40 (max 0,002).
  Ce contrôle reste synthétique : il ne vaut pas essai à la voix.
- Sample téléchargé une fois après correction du format et fin de lecture
  signalée par le terminal. Nouvel essai rejoué à la demande de l'utilisateur,
  fin également confirmée ; 2 327 ms de synthèse sur ce dernier essai.
- Connexion directe persistante, sans réactiver Home Assistant et sans flashage.
- Sample téléchargé une fois après correction du format et fin de lecture
  signalée par le terminal. Nouvel essai rejoué à la demande de l'utilisateur,
  fin également confirmée ; 2 327 ms de synthèse sur ce dernier essai.
- Test du micro : **62 976 octets**, soit **1,97 s** de PCM reçus, sans traitement
  sémantique ni sauvegarde. L'utilisateur confirme ensuite que l'écoute du
  sample fonctionne et lui convient. La conversation humaine complète reste
  à confirmer.
- Recette du 5 novembre : **294 tests Python réussis, 3 réels optionnels ignorés ; 29 tests
  JavaScript réussis**. Transport, expiration, accès par IP, Range, conversion,
  silence, arrêt et passage par le pipeline existant couverts automatiquement.
  Le flux continu, la conservation des mots, l'ordre des blocs et la libération
  de la voix à l'annulation sont également couverts.

## Références techniques consultées

- [Client natif officiel aioesphomeapi](https://github.com/esphome/aioesphomeapi).
- [Configuration du firmware installé, tag v2.0.0](https://github.com/jyoushiki/esphome-waveshare-esp32-s3-audio-va/blob/v2.0.0/waveshare-va.yaml).
- [Composant voice_assistant ESPHome](https://esphome.io/components/voice_assistant/).
- [Implémentation du protocole de la version ESPHome installée](https://github.com/esphome/esphome/blob/2026.9.0/esphome/components/voice_assistant/voice_assistant.cpp).
- [Réglage HighQoS d'un processus Windows](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation).
