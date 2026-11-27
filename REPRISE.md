# Reprise — Alfred, assistant vocal

Préparée le **6 novembre 2026 — Europe/Paris**.
Dossier Git : branche **master**, **aucun commit**, fichiers du projet non suivis.
Aucun commit de référence. Aucun commit ni publication pour cette reprise.

## 1. Objectif

Assistant vocal domestique francophone autonome : Home Assistant pour la
domotique, les courses et les calendriers, Music Assistant pour la musique,
Command Code pour le dialogue, terminaux ESP32 pour micro et haut-parleur.
Budget supplémentaire visé : **5 €/mois maximum**, hors abonnement Command Code.
Version active vérifiée : **0.6.0**. Ne pas confondre avec le projet Serveur.

## 2. Travail terminé et état actuel

- **Voix retenue : alfred-reference**, Supertonic 3 local, débit **1,242**, sans
  patine. Banque privée sous `.local/data/voice-bank/alfred-reference-20261102/`.
  Profil, paramètres, samples et recette archivés ; intégrité du profil vérifiée.
  Ne pas reprendre les essais de timbre ni changer cette référence.
- Réponses ESP32 progressives : blocs synthétisés pendant la lecture des
  précédents, un encodeur FLAC mono 48 kHz continu, HTTP chunked. Texte et actions
  finalisés avant de parler. Voix verrouillée pendant toute la réponse.
  Navigateur : parcours audio complet habituel.
- Marges silencieuses excessives aux jonctions raccourcies ; début/fin de
  l'énoncé et pauses internes préservés, aucun filtre. Rendu accepté le 5 novembre.
- CPU : quatre threads Supertonic, HighQoS Windows pour le seul processus Alfred
  au lancement ; tâche en priorité normale (6), sans priorité haute, affinité
  imposée ou modification du plan d'alimentation global.
- **STT unique : Parakeet TDT 0.6B v3 INT8**, stack Murmure 1.11.3 autonome
  sur CPU avec dictionnaire/nettoyage/formatage. Moteurs et comparatifs antérieurs
  retirés le 11 novembre. Voir STT.md pour l’état courant et la préparation.
- **Fin de parole ESP32 : Silero VAD v6 local**, modèle ONNX autonome vérifié,
  contexte séparé par prise, fenêtres 32 ms, seuils0,5/0,35 et pause900ms.
  Il remplace le seuil de volume qui attendait l'arrêt du fond musical.
  PCM, pré-capture et gains conservés ; navigateur encore à détection par énergie.
- **Dernier retour : « très bien ça fonctionne nickel ».** Nouveau scénario
  avec musique chantée sur un autre appareil validé ; S20 terminé pour ce cas.
  Le VAD n'identifie pas le locuteur : pas de garantie sur tout chant, TV,
  volume ou distance.
- Diagnostic sans action : « Tester la transcription ESP32 » arme le prochain
  K2 ; **« Tester à distance »** ouvre le test depuis la page, sans K2.
  Aucun appel IA/TTS/HA, aucun audio sauvegardé ; texte en mémoire deux minutes.
  Armement60s : une activation tardive reste un test expiré, jamais une commande.
- Waveshare du bureau : firmware observé **jyoushiki v2.0.0 / ESPHome 2026.9.0**,
  gardé sans flashage. Identité MAC vérifiée avant connexion.
  Pont direct ESPHome TCP6053, retour audio HTTP local8766 limité à la carte,
  jetons90s et deux réponses maximum en mémoire.
- Carte retirée de l'usage HA le 2 novembre : entrée ESPHome et relais Music
  Assistant désactivés, configuration conservée. Ne pas réactiver HA pour les
  essais Alfred. Les connecteurs HA généraux restent en place.
- Conversation et minuteurs depuis le dialogue, lumières directes, courses
  `todo.courses_alfred`, rappels `calendar.personnel` et `calendar.familial`
  ont leurs socles et essais antérieurs. Calendriers HA seuls référentiels de
  rappels ; minuteurs programmés par Alfred, SQLite persistante.
- **Annonces, rappels et sonneries physiques ne sont pas raccordés au nouveau
  pont direct.** Anciens routages vers la carte retirés. Le lecteur musical
  local de test a aussi été désélectionné car il pointait sur la carte ;
  recontrôler et choisir explicitement un lecteur avant un nouvel essai musique.
- Interface web en huit vues, laboratoire vocal par défaut. Profils expérimentaux,
  mais calibration à deux personnes non validée ; pas une authentification.

## 3. Fichiers concernés

Tous sont non committés, comme le reste du dépôt.

| Fichier | Rôle |
| --- | --- |
| CADRAGE.md, CHECKLIST.md | Décisions, priorités et identifiants stables |
| README.md, STT.md, TERMINAL_DIRECT.md | Lancement et protocoles d'essai |
| alfred/app.py | API, pipeline commun et tests sans action |
| alfred/voice.py | Small/beam5, banque vocale, synthèse et verrou par réponse |
| alfred/speech_activity.py | Silero en continu, état indépendant par prise |
| alfred/terminal.py | Client ESPHome, capture, fin de parole et diagnostics |
| alfred/audio_stream.py | Découpage, marges silencieuses et FLAC continu |
| alfred/runtime.py, alfred/__main__.py | HighQoS et lancement |
| alfred/setup_parakeet.py, setup_vad.py | Préparation du STT retenu et du VAD autonome |
| alfred/static/index.html, terminal-panel.js, voice-controller.js | Contrôles vocaux/STT |
| alfred/static/navigation.js, style.css | Interface par fonction du 4 novembre |
| tests/test_speech_activity.py, test_terminal.py, test_audio_stream.py | Capture, bruit, flux et arrêt |
| tests/test_voice.py, test_conversation.py, test_api.py | Moteurs et API |
| pyproject.toml, requirements.lock.txt | Dépendances épinglées |

Modules calendrier, courses, musique, profils et échéances : voir la checklist.

**Privé :** .local/ et voice/ sont exclus de Git. Ne pas lire ou recopier leurs
secrets, audios, empreintes ou souvenirs pour reprendre. Chemins utiles seulement :
configuration terminal .local/data/terminal.json, choix vocal .local/data/voice.json,
modèles .local/models/, données SQLite .local/data/, certificats .local/https/.
Anciens routages HA et retour arrière : .local/backups/esp32-ha-disconnect-20261102/.
Ancienne tâche : .local/backups/alfred-task-before-latency-20261104.xml.

## 4. Décisions et raisons

- Compréhension prioritaire avant le réveil. Les défauts de base et le scénario
  musical signalés sont acceptés comme corrigés par l'utilisateur ; conserver
  Small et Silero. Mesures plus larges encore ouvertes.
- Conserver voix fixe et débit1,242, flux progressif et marges corrigées.
- Aucun téléchargement pendant une prise ; pas d'audio brut enregistré.
  Résultat de diagnostic temporaire, séparé du statut technique.
- HA fournit domotique et données ; Alfred conduit dialogue, STT/TTS et minuteurs.
  Le terminal utilise l'API native directement.
- Une réponse d'action perdue n'entraîne aucune répétition automatique.
  Un arrêt ne défait pas une action déjà exécutée.
- Rappels HA par UID ; récurrence ambiguë à clarifier. Pas de second calendrier.
- Droits et authentification avant production différés par l'utilisateur :
  ne pas confondre le prototype fonctionnel avec une mise en production.

## 5. Pistes abandonnées ou non retenues

- Piper : mauvaises prononciations d'Alfred et de « majordome ».
- Clone Pocket : rapide, mais timbre/hauteur dérivant ; segments courts perdaient
  le caractère recherché. Ancien candidat conservé, pas le défaut actuel.
- Patine de vieillissement : rejetée pour saturation. Variante « noble » :
  abandonnée explicitement. Ne pas reprendre ces essais.
- Qwen3-TTS GGUF CPU et Chatterbox : trop lents pour le dialogue sur ce PC.
- Extraction d'un style privé Supertonic : outil essayé exigeant un GPU et
  démonstrations instables ; ne pas relancer par défaut.
- HA Assist comme cœur du dialogue et ancien banc ESP32 HA : non retenus.
  Firmware conservé, interface native réutilisée.
- Seuil de volume seul sur ESP32 : retenait la musique ; remplacé par VAD.
- Ancien ordonnanceur local de rappels suspendu, données conservées.
  Modification d'une série HA entière encore refusée par le code.

## 6. Vérifications effectuées et limites

**Pendant l'implémentation, avant cette note :**

- Dernière suite Python : **303 réussis, 4 optionnels ignorés**.
- Tests speech_activity exécutés avec ALFRED_TEST_SPEECH_VAD=1 : **4 réussis**,
  dont parole TTS sur fond instrumental synthétique continu. Fin avec musique
  maintenue et début de phrase préservé.
- Dernière recette JavaScript complète connue : **29 tests réussis**.
  Syntaxe de terminal-panel.js vérifiée après le dernier libellé.
- Banc STT synthétique de sept phrases : WER normalisé base/beam1 **19,7 %**
  contre small/beam5 **6,1 %**, médianes **487 / 1 096 ms**. Pas un WER humain.
- HighQoS : même texte témoin, TTS chaud environ6,4s →2,33s.
- Flux : premier bloc demandé avant génération totale, fin de lecture confirmée.
  Mesure réseau, pas mesure du premier son acoustique.
- Jonctions : environ1–1,2s →0,29s sur mêmes blocs, parole conservée bit à bit
  dans les tests. Rendu corrigé accepté à l'écoute.
- Retours humains : voix et rendu progressif acceptés ; conversation K2
  fonctionnelle ; STT sans erreur perceptible sur l'essai ; fond chanté corrigé.
  Ne pas extrapoler à une recette familiale ou acoustique exhaustive.

**Contrôle léger du 6 novembre pour cette reprise :**

- /health : status=ok, version0.6.0.
- /api/voice/status : small, beam5, alfred-reference, vitesse1,242.
- /api/terminal/status : connecté, idle, aucune erreur, silero-v6 ;
  dernier motif speech_pause, prise **5 432 ms**. Aucun texte privé consulté.
- Tâche Windows présente, priorité6, dernier résultat0, lanceur wscript.exe.
  Elle affiche **Ready alors que le serveur répond** : ce statut ne prouve
  pas l'arrêt du processus enfant.
- Git master sans commit, fichiers non suivis.

Aucun long test, lancement, redémarrage, installation, commit ou publication
effectué uniquement pour rédiger cette note. Les sondes HTTPS ont ignoré la
validation du certificat auto-signé : elles ne prouvent pas sa confiance client.
A08 concerne le certificat initial expiré ; renouvellement/confiance actuels
non vérifiés lors de cette reprise.

## 7. Problèmes encore ouverts

- S03 : acoustique/charge plus larges et hôte cible. S20 terminé pour le cas
  utilisateur, pas un filtre universel du chant ou de la télévision.
- S19 : délai complet après une vraie demande micro à apprécier après optimisation.
- T03 : réveil **« Alfred » seul** non installé. Prévenir les faux réveils sur
  **Fred**, conversation et TV/musique. Méthode d'installation et performances
  du futur modèle : non déterminées.
- T02/T05 : essais approfondis mute, LED, duplex, écho, reconnexion en panne réelle
  et interruption de la réponse. Arrêt logiciel ne vaut pas barge-in acoustique.
- T06/T07 : plusieurs terminaux, sonneries, annonces et rappels à raccorder au
  nouveau pont, puis valider sur haut-parleur.
- I02 : deuxième personne pour calibration. I03/I04/I05 : droits, mémoires
  séparées et historique selon les règles du projet.
- S07/S08 : recherche Internet, compteurs et plafonds de coûts.
- P04/A02/A03/A04 : hôte durable, ressources, sauvegarde/restauration et recette
  bureau/salon. A08 : HTTPS de développement à régulariser.
- Rappels : série entière et marquage des événements créés depuis HA.
- T09 : Echo Show 5 H23K37 disponible, pistes TECHO5 / Fire OS discutées ;
  aucun choix ni flashage à considérer comme réalisé.

Une case ouverte peut correspondre à une recette restante, pas à un socle absent.

## 8. Prochaine action proposée

Les derniers défauts STT signalés sont validés comme corrigés.
**Ne pas redemander le même test musical ni modifier de nouveau la voix.**

Au retour, choisir le chantier suivant. Suite proposée : **T03, réveil Alfred**.
Première étape : lire les références actuelles de micro_wake_word et inspecter
en lecture seule les possibilités du firmware/API native, puis préparer un essai
réversible tenant compte de Fred. K2 reste la référence. Aucun modèle, flashage
ou outil de formation choisi par cette proposition. Les sonneries/annonces
du pont direct constituent l'autre priorité fonctionnelle.

Avant toute opération sur la carte, vérifier sa détection et sa connexion dans
/api/terminal/status. Ne pas réactiver HA pour simplifier un essai.

## 9. Dossier à rouvrir et relance

**Dossier : D:\App en dev\Assistant_vocal**
Interface : **https://192.168.1.23:8765/#voice**.
Service actif et terminal connecté au contrôle de reprise. Ne pas lancer une
deuxième instance : le verrou est volontaire.

Depuis PowerShell, si le service n'est pas déjà actif :

```powershell
cd "D:\App en dev\Assistant_vocal"
Start-ScheduledTask -TaskName 'Alfred Assistant Vocal'
```

La tâche a été utilisée pour les relances de développement. Lanceur courant :
wscript.exe ; Ready possible avec un serveur enfant actif. Après un arrêt,
vérifier les anciens processus et le verrou avant relance. Journal privé :
.local/alfred-task.log, sans copier son contenu sensible.

Contrôle des processus en lecture seule :

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'Python314\\python\.exe.*-m alfred' } |
  Select-Object ProcessId, ExecutablePath
```

Lancement manuel, après arrêt vérifié de l'instance existante :

```powershell
cd "D:\App en dev\Assistant_vocal"
.\.venv\Scripts\python.exe -m alfred --host 192.168.1.23 --https
```

Commande supportée par alfred/__main__.py, non réexécutée pour cette note.
La tâche utilise le Python système et les dépendances du venv pour le pare-feu ;
ne pas supposer une validation LAN fraîche du lancement manuel. Un banc HTTP
localhost est possible avec -m alfred sans options, mais reste exclusif de
l'autre instance et de son verrou.

Prérequis : Python3.12+, .venv, requirements.lock.txt, modèles et banque vocale
locaux, configuration/données privées, certificat et clé HTTPS déjà préparés.
Configurer les secrets dans les formulaires locaux, **jamais dans le chat**.
HA et Command Code servent leurs fonctions, pas d'intermédiaires audio ESP32.

Ne préparer des modèles que s'ils manquent. STT public :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_parakeet --assets .local/models/parakeet-murmure-1.11.3
```

Cette commande a été exécutée pendant le chantier STT, pas pour la reprise.
Ne pas relancer Pocket ni la préparation de la référence acceptée.

Tests ultérieurs depuis le dossier, non relancés pour la note :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
$alfredJsTests = @(rg --files tests -g '*.test.mjs')
node --test $alfredJsTests
```

Banc VAD réel optionnel, avec modèles déjà présents, sans action de maison :

```powershell
$env:ALFRED_TEST_SPEECH_VAD = "1"
.\.venv\Scripts\python.exe -m pytest -q tests/test_speech_activity.py
```

La note ne contient que paramètres et chemins techniques. Aucun secret, contenu
vocal privé, empreinte ou souvenir personnel n'y est recopié.
