# Transcription locale d’Alfred

Dernière mise à jour : 23 novembre 2026 (Europe/Paris).

## Solution unique retenue

**Parakeet TDT 0.6B v3 INT8 avec la chaîne de Murmure 1.11.3**, entièrement
locale sur CPU. Le navigateur et l’ESP32 utilisent cette même chaîne :

1. Conversion WAV mono PCM16 en signal 16 kHz.
2. Reconnaissance Parakeet, code Rust et modèles ONNX de Murmure 1.11.3.
3. Boost/correction par dictionnaire, nettoyage des hésitations et répétitions.
4. Règles de formatage importées localement de Murmure.

Aucun LLM de reformulation, STT distant, moteur de secours ou dépendance à
l’application Murmure ouverte. Le modèle est fixe : aucune sélection de moteur
ni variable de bascule. Les réglages de dictée restent dans
`.local/data/stt-murmure.json`, hors Git, sans synchronisation ultérieure avec
Murmure. La synthèse vocale et le dialogue restent des fonctions distinctes.

Le worker est préchargé au démarrage, reste en mémoire et échange le PCM par
pipes. Aucun serveur HTTP interne ni WAV temporaire. Une erreur ou un timeout
ferme le processus ; l’appel suivant peut le relancer sans répéter une action.
Les transcriptions ne sont pas enregistrées dans les logs du STT.

## Préparation

Avec l’installation locale de Murmure et Rust/Cargo :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_parakeet --murmure-settings "$env:APPDATA/com.al1x-ai.murmure"
```

Cette préparation explicite copie les modèles et les réglages, compile le
worker, prépare Silero et vérifie le silence. Elle ne lit ni historique ni clé
ou configuration LLM. Aucun téléchargement/build pendant une prise.
Pour une migration, `--assets` accepte les ressources Parakeet déjà copiées ;
voir [le worker natif](native/murmure-stt/README.md). La VM Debian reste à recetter.

## Fin de parole ESP32

**Silero VAD v6** reste utilisé pour terminer la prise, indépendamment du STT.
Le même fichier ONNX est désormais autonome dans `.local/models/silero-v6`,
avec SHA-256 vérifié et provenance conservée. Chargement direct ONNX Runtime
CPU ; mêmes options, contexte séparé par prise, fenêtres 512 échantillons à
16 kHz, hystérésis 0,5/0,35 et pause 900 ms. Aucun changement des gains, du PCM
ou du réveil. Le navigateur conserve sa détection par niveau.

Préparation indépendante, si nécessaire :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_vad
```

Le découpage interne du worker reste celui de Murmure pour les prises bornées
à 30 s : fenêtres 33 ms, coupure après 500 ms de silence une fois 15 s atteintes,
250 ms de silence ajoutées aux extrémités des segments. Il ne remplace pas le
VAD de fin de prise et ne reconnaît pas l’identité du locuteur.

## Diagnostic sans action

**ESP32 :** « Tester la transcription ESP32 », puis K2 et une phrase ; ou
« Tester à distance », attendre le signal puis parler sans K2. Le résultat et
le délai apparaissent sans conversation IA, lecture vocale ou commande de maison.
Armement 60 secondes ; un test activé tardivement reste un test expiré, jamais
une commande. Texte en mémoire et affichage effacés après deux minutes.

Pour l’essai du dictionnaire du 23 novembre, tester « Allume la lumière de la
cuisine », « Tu peux allumer la lumière dans la cuisine ? » et « Il y a de la
fumée dans le salon ». Vérifier la transcription du nom de pièce et des mots
voisins avant de rejouer le banc d’allumage. Le vocabulaire testé ajoute
uniquement « cuisine » au dictionnaire existant.

**Navigateur :** le mode « Test audio » transcrit avec Parakeet et peut relire
le texte avec la voix courante. Le mode « Conversation » traite les demandes
normalement. Les contrôles de comparaison ont été supprimés.

## Validation et nettoyage

À l’intégration : 28 sorties sur 28 identiques à Murmure sur 14 fichiers
synthétiques, dont silence, parole faible et prise de 19,54 s avec pause.
L’utilisateur juge ensuite la chaîne meilleure et plus rapide sur téléphone
et ESP32, puis « vraiment très bien » après intégration. Aucun taux de précision
humaine ni garantie en bruit/distance déduit de ces retours qualitatifs.

Le 11 novembre, à la demande de l’utilisateur : code, options, routes, tests
et scripts des anciens moteurs/comparatifs supprimés ; paquets STT obsolètes
désinstallés du venv ; anciens modèles, corpus et sources d’étude temporaires
placés dans la Corbeille. Sources, modèles, dictionnaire et formatage de la
solution retenue conservés. Un seul WAV public synthétique demeure dans
`.local/stt-smoke` pour vérifier la chaîne sans ouvrir de micro.

Après nettoyage : 480 tests Python réussis (2 optionnels ignorés) et 17 tests
JavaScript ciblés réussis, dont diagnostic sans action, expiration du texte,
états du VAD et rejet réel d’un fond instrumental synthétique. Les sources Rust
retenues sont inchangées depuis leurs 96 tests réussis. La relance du service
et les contrôles réels finaux sont consignés dans CADRAGE.md et CHECKLIST.md.

Restent : recette sur Debian, charge/mémoire simultanées, bruit et distance
approfondis. Le nettoyage ne valide pas ces points.
