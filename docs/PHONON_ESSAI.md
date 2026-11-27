# Phonon français — essai local du 11 novembre 2026

Mise en œuvre demandée par l’utilisateur. Deux voix de catalogue sont prêtes dans
Alfred : **Phonon · Arnaud · CPU** et **Phonon · Lucien · CPU**. Le profil exporté
ensuite par l’utilisateur a été ajouté sous **Alfred · Phonon · voix clonée**.
Après un nouvel export, **Dumby · Phonon · CPU** est désormais actif pour essai.
Henri et les anciens profils restent conservés ; aucune voix déclarée définitive.

## Écouter et utiliser

Extraits génériques dans `.local/phonon-trial-20261111/` :

- `phonon-arnaud-long.wav`
- `phonon-lucien-long.wav`
- Les deux fichiers `...-court.wav` et `phonon-premier.wav` complètent le banc.

Texte identique à la comparaison précédente :

> Il est vingt heures quarante-trois. Les enfants ont deux amis. Nous avons un
> rendez-vous. Du pain et un œuf. Il n’y a plus de pâtes. J’en veux plus, ajoute
> une portion.

Pour ses propres phrases : actualiser le laboratoire vocal, sélectionner l’une
des deux voix Phonon, puis utiliser le navigateur ou parler à Jarvis. Le modèle
reste chargé tant que la voix est sélectionnée. Revenir à Henri dans le même menu.
La préférence choisie est persistante ; aucun changement silencieux sur erreur.

Arnaud et Lucien sont des voix françaises masculines du catalogue Gradium : ce
ne sont pas des clones de la référence Alfred. Aucun enregistrement privé ou
sample de la banque d’Alfred n’a été envoyé à Gradium.

## Installation réellement utilisée

- Environnement isolé `.local/phonon-env/` : Python 3.11.15, `ptts` 0.7.0 et
  NumPy 2.4.6 ; sans PyTorch. Runtime Rust natif Windows, CPU explicitement choisi.
- `gradium/phonon-40m-fr`, révision
  `d91086970206b88efd2c88ca971d0628b5968f0f`, poids Q8 `model.q8.gguf`.
- Catalogue `gradium/phonon-voices`, révision
  `0ee17205f254b5abc43b266c8a0f215565c352f7` ; deux fichiers de voix copiés
  dans le dossier local du modèle et un catalogue `voices.jsonl` local.
- Accès au modèle réussi avec la configuration HF existante. Pas d’acceptation
  automatique de conditions ni de création de compte. Le modèle français est
  soumis aux conditions HF et à la licence CC BY-NC 4.0 ; le runtime a sa propre
  licence MIT/Apache. Le checkpoint anglais par défaut n’a pas été substitué.
- L’essai n’utilise ni l’API Gradium, ni un abonnement de synthèse. Poids et voix
  ont été téléchargés pendant la préparation ; les synthèses suivantes sont locales.

## Mesures sur le PC actuel

CPU, quatre threads, modèle Q8 chargé, température 0,3 et graine 42.

| Mesure native Phonon | Arnaud | Lucien |
| --- | --- | --- |
| Génération de la courte phrase sur l’heure | 198 ms | 186 ms |
| Génération du texte comparatif complet | 735 ms | 755 ms |
| Durée d’audio du texte complet | 9,44 s | 9,92 s |
| Premier bloc PCM via streaming natif | 62 ms | 39 ms |
| Tous les blocs de ce streaming natif | 771 ms | 1 471 ms |

Le premier bloc PCM n’est pas une mesure du premier son audible sur l’ESP32,
ni du tour STT/IA/TTS complet. Petit banc exploratoire, pas un p95 ou une garantie
de performance dans la future VM Debian.

Contrôle réel du service HTTP Alfred sur « Il est 20h43. Il n’y a plus de pâtes. » :

| Voix | Premier appel | Deuxième appel | Durée d’audio | Repli |
| --- | --- | --- | --- | --- |
| Arnaud | 308 ms | 244 ms | 3,04 s | Aucun |
| Lucien | 331 ms | 256 ms | 3,12 s | Aucun |

Sélections et synthèses HTTP 200. Henri rétabli après ces contrôles. Jarvis actif,
ESP32 connecté et réception de trames confirmée au contrôle final. Aucune lecture
physique sur le haut-parleur n’a été lancée pour ces mesures techniques.

## Intégration

Les deux voix utilisent le client CPU persistant existant et
`alfred/local_voice_worker.py`. La branche Phonon n’importe pas PyTorch ;
`PhononVoice` de `alfred/local_voice_models.py` utilise les chemins de poids,
voix et catalogue locaux, vérifie le français, force `device=cpu` et quatre threads.

Les requêtes/audio passent par les pipes du processus, sans WAV de conversation
écrit sur disque ni écoute réseau ajoutée. Limites de taille, durée et délai du
worker conservées ; sortie invalide ou timeout signalés sans repli. Les heures
sont développées par Alfred ; les négations « plus » sont laissées au moteur.

L’API native peut streamer par petits blocs. Cette première intégration retourne
un WAV complet par bloc de texte via `speak` / `speak_blocks` ; elle ne transporte
pas encore chaque trame native Phonon jusqu’au haut-parleur. Ne pas utiliser le
TTFB natif comme mesure de la chaîne applicative actuelle.

Les configurations privées sont `.local/data/phonon-arnaud.json` et
`.local/data/phonon-lucien.json`, sans clé API : chemins et nom de voix uniquement.
Les versions, résultats et métadonnées sont conservés dans le dossier du banc.

## Vérifications et limites

479 tests Python réussis, 4 optionnels ignorés ; 38 tests JS réussis. Couverture
des paramètres CPU/français/Q8, absence de substitution anglaise, disponibilité
des fichiers, protocole persistant, choix enregistrés, normales/progressives et
erreurs sans repli. Les versions précédentes des moteurs restent sélectionnables.

Cinq WAV mono PCM16 24 kHz vérifiés, sans écrêtage. Whisper retrouve toutes les
phrases principales des deux extraits longs ; cette vérification ne valide pas
les liaisons, la prononciation de « plus », le timbre ni la similarité au personnage.
Retour humain et choix de voix encore attendus. Aucune voix personnalisée n’a été
créée ; une création/export Studio pourra être étudiée séparément.

## Sources officielles

- [Phonon, présentation](https://gradium.ai/phonon)
- [Runtime et modèles](https://github.com/gradium-ai/xn-ptts)
- [Bindings Python](https://github.com/gradium-ai/xn-ptts/blob/main/ptts-pyo3/README.md)
- [Checkpoint français](https://huggingface.co/gradium/phonon-40m-fr)
- [Catalogue de voix](https://huggingface.co/gradium/phonon-voices)

## Retour utilisateur

Après présentation des deux voix, retour : « vraiment rapide ». La réactivité
est appréciée qualitativement. La voix concernée et le contexte exact ne sont
pas précisés ; diction, timbre et choix final restent à recueillir. Aucun
changement automatique de la voix active par ce retour.

## Profil personnalisé fourni ensuite

Le fichier de voix .safetensors fourni par l’utilisateur dans docs a été copié
et vérifié dans `.local/data/voice-bank/gradium-alfred/voice.safetensors`, sans
modification de l’original ni exposition de son contenu. Les .safetensors de docs
sont exclus de Git ; aucun de ces profils n’était suivi. Pas de fichier vocal,
empreinte biométrique ou tenseur ajouté à la documentation versionnée.

Choix actif d’essai : `phonon-alfred-cpu` ; configuration privée
`.local/data/phonon-alfred.json`. Même modèle français Q8 et runtime CPU existants,
voix chargée par `add_voice`. Aucun nouvel envoi Cloud, clonage ou achat par l’agent.

Mesures natives : présentation de 4,24 s en 369 ms, texte comparatif de 10,32 s
en 794 ms. Contrôle du service : HTTP 200, 395 puis 330 ms, moteur Phonon, pas de
repli. Jarvis actif, carte connectée et trames reçues. 82 tests Python ciblés et
39 tests JS réussis. Échantillons `phonon-alfred-court.wav` /
`phonon-alfred-long.wav` dans le dossier privé du banc. Transcription retrouvant
les phrases principales ; diction, timbre et ressemblance encore à juger par
l’utilisateur. Ce profil est actif pour essai, pas déclaré voix définitive.

## Second profil personnalisé, version active d’essai

Nouvel export fourni par l’utilisateur et différent du fichier courant : copie
vérifiée dans `.local/data/voice-bank/gradium-alfred/voice-v2.safetensors`.
Le premier fichier et `config-before-v2.json` restent présents dans ce même
stockage privé. La configuration active `phonon-alfred.json` pointe sur la version 2.
Les deux exports sources de docs sont conservés et exclus de Git.

Le worker a été fermé puis rouvert pour charger ce nouveau fichier ; le menu
conserve le nom **Alfred · Phonon · voix clonée**. Aucun nouveau code, appel de
clonage, compte ou envoi Cloud. Test natif long : 849 ms pour 10,32 s d’audio,
échantillon `phonon-alfred-v2-long.wav`. Service : HTTP 200, 391/341 ms pour une
présentation de 3,92 s, Phonon et aucun repli. Jarvis actif, ESP32 connecté et
trames reçues après activation. Qualité et préférence face à la version 1
restent à juger à l’écoute. Les suites de code n’ont pas été répétées pour ce
remplacement de données, validé par chargement et synthèse réels.

## Nouveau profil Dumby, choix actif

L’utilisateur trouve le profil précédent moins adapté et fournit un nouvel export
à nommer Dumby. Copie privée vérifiée sous
`.local/data/voice-bank/gradium-dumby/voice.safetensors`, sans modifier les profils
Alfred 1/2. Configuration `.local/data/phonon-dumby.json`, voix `phonon-dumby-cpu`
sélectionnée et persistée ; menu **Dumby · Phonon · CPU**. Le nom de l’assistant
et le mot d’appel restent Alfred et Jarvis. Aucun clonage/transfert Cloud réalisé.

Test natif : 956 ms pour le texte comparatif de 11,36 s ; fichier
`phonon-dumby-long.wav` dans le dossier privé du banc. Contrôle HTTP : 323 puis
244 ms pour 3,2 s d’audio, moteur Phonon et aucun repli. 83 tests Python ciblés
et 40 tests JS réussis. Terminal connecté et veille Jarvis reçue après activation.
Dumby est activé pour l’essai demandé ; le jugement humain reste à recueillir.

## Nettoyage : Phonon seul

À la demande de l’utilisateur, le service et le sélecteur ne contiennent plus
que Dumby, Alfred cloné, Arnaud et Lucien. Dumby reste actif/par défaut. Tous les
identifiants non Phonon sont refusés par l’API ; aucun repli non Phonon. Les anciens
moteurs ne sont plus chargés ou utilisés par VoiceService. Les sources d’essai
sauvegardées et les références historiques sous .local restent des archives,
pas des choix de l’application. Les comptes et intégrations HA existants n’ont
pas été supprimés. Actualiser le navigateur pour voir le sélecteur nettoyé.

Validation : 480 tests Python réussis, 2 optionnels ignorés ; 34 tests JS. Liste
réelle du service limitée aux quatre profils et refus 422 des anciennes voix.
Dumby : HTTP 200, 307 ms pour 3,2 s d’audio, sans repli ; Jarvis et carte connectés.
