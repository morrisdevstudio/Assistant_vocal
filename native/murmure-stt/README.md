# Moteur STT autonome d'Alfred, stack Murmure 1.11.3

Ce worker reprend le moteur Rust Parakeet, le dictionnaire et les règles de
formatage de [Murmure](https://github.com/Kieirra/murmure), tag `1.11.3`, commit
`7c10b78c2284aad37c815ba1d216c95ebd0ee47c`. Sources et licence AGPL conservées
dans ce dossier ; provenance et empreintes des modules dans `UPSTREAM.json`.

Les modules `engine`, `dictionary.rs`, `vad.rs` et les fonctions de formatage
proviennent de cette révision. `clean.rs` extrait les fonctions pures de
nettoyage ; `pipeline.rs` adapte la segmentation de l'API sans Tauri, UI,
historique ou LLM. `main.rs` est l'adaptateur stdio d'Alfred. La limite de
30 secondes rend inutile la branche d'origine de coupure forcée à 60 secondes.
Les fenêtres 33 ms, silence de 500 ms après 15 secondes, remplissage de 250 ms,
boost/correction du dictionnaire et ordre nettoyage/formatage sont conservés.
La fin de prise ESP32 reste gérée par le Silero VAD existant dans Alfred.

Stack épinglée dans `Cargo.lock` : `ort`/`ort-sys` `2.0.0-rc.10` (ORT 1.22.0),
CPUExecutionProvider, `tokenizers` 0.23.1, `text2num` 2.6.5 et les versions
utilisées par le lock de Murmure 1.11.3 pour les dépendances directes.
Le paquet ORT Windows inclut des objets DirectML nécessitant les bibliothèques
Windows SDK au lien ; les sessions restent explicitement sur CPU.

## Préparation

Depuis la racine, avec Rust/Cargo, le compilateur natif du système et le venv :

```powershell
.\.venv\Scripts\python.exe -m alfred.setup_parakeet --murmure-settings "$env:APPDATA/com.al1x-ai.murmure"
```

Cette commande copie les modèles **installés** de Murmure, leur tokenizer et les
réglages de dictée dans `.local`, compile le worker et vérifie le silence.
Parakeet est le seul STT d'Alfred. Elle ne lit ni clé, ni connexion LLM, ni historique.
Les réglages sont une copie indépendante : les modifications futures dans
Murmure ne sont pas synchronisées. Aucun modèle n'est téléchargé pendant une
prise ; Cargo peut télécharger ses dépendances à cette préparation explicite.
Relancer Alfred après préparation ; Murmure peut rester fermé pour la conversation.
Le détecteur de fin de parole Silero v6 est préparé séparément, avec empreinte
vérifiée, sans dépendance à un autre moteur STT. `python -m alfred.setup_vad`
permet aussi de le préparer seul ; aucun téléchargement pendant une prise.

Si le téléchargement ORT par Cargo échoue, `--ort-lib-location` accepte le
dossier du paquet ORT 1.22.0 préchargé (contenant `lib`). Le cache local
`.local/ort-1.22.0/onnxruntime` est reconnu automatiquement. Il n'est pas requis
de conserver le compilateur ou l'archive de compilation pour exécuter le worker.

## Déploiement Debian à recetter

Copier les ressources locales `models/parakeet-murmure-1.11.3` et le fichier
`data/stt-murmure.json` dans l'emplacement `.local` choisi sur la cible.
Ne pas copier les autres secrets ou données privées sans migration dédiée.
Installer Rust/Cargo et les outils de compilation natifs, puis :

```sh
.venv/bin/python -m alfred.setup_parakeet --assets .local/models/parakeet-murmure-1.11.3
```

Le binaire est recompilé pour Linux. Pas de Tauri, desktop, CUDA ou application
Murmure à installer. La compilation et les performances Debian ne sont pas
encore vérifiées ; aucune performance de VM ne doit être déduite du test Windows.

## Protocole et exploitation

`alfred/parakeet_stt.py` lance le binaire local en fenêtre masquée sur Windows,
précharge une fois les modèles et le garde en mémoire. Les requêtes/réponses
JSON sont précédées d'une taille uint32 little-endian. Le PCM16 mono 16 kHz est
envoyé en base64 dans le pipe ; aucun chemin audio n'est accepté. Limites :
30 secondes et 1,4 Mo par trame. Pas de serveur réseau, fichier WAV temporaire,
statistique ou transcription dans les logs. Timeout/erreur ferme le processus ;
l'appel suivant peut le relancer, sans relancer une commande de maison.

Le STT est fixe : Parakeet. Aucun sélecteur de moteur, variable d'environnement
de bascule, ancien modèle ou comparatif n'est conservé depuis le nettoyage du
11 novembre. La configuration `.local/data/stt-murmure.json` contient uniquement
les réglages de dictionnaire/formatage. Pas de repli automatique en cas d'erreur.
La parité avec Murmure a été vérifiée sur 28 prises à l'intégration ; les bancs
temporaires ont été retirés ensuite. Les tests du worker et du diagnostic restent.

## Sources et attributions

- [Murmure 1.11.3](https://github.com/Kieirra/murmure/tree/1.11.3), auteurs du
  projet Murmure, code AGPL-3.0-or-later ; licence complète dans `LICENSE`.
- [Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3),
  NVIDIA, CC BY 4.0. Les fichiers INT8 sont ceux distribués avec Murmure 1.11.3,
  copiés sans modification et identifiés par SHA-256 dans le `source.json` local.
- [ONNX Runtime](https://github.com/microsoft/onnxruntime/tree/v1.22.0), Microsoft,
  MIT ; licence conservée dans `ONNXRUNTIME-LICENSE`.

Le code d'intégration ajouté à ce worker est également AGPL-3.0-or-later.
Les sources correspondantes sont fournies ici, avec instructions de compilation
et changements décrits ; ni modèles binaires ni dictionnaire personnel dans Git.
