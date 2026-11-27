# Chatterbox : latence et cible AuBox — 8 novembre 2026

## Cible décidée par l’utilisateur

Chuwi AuBox Ryzen 7 8745HS, 32 Go DDR5, SSD 512 Go, Radeon 780M, attendu
prochainement. Proxmox pour le homelab ; Alfred dans une VM Debian. Ce choix
remplace l’hypothèse de la VM Alfred sur le Pentium G7400. La machine n’est
pas encore reçue et aucune VM ni accélération AMD n’a été configurée.

La qualité de français du Chatterbox v2 C du premier banc est préférée à
Supertonic par l’utilisateur. Cela ne valide pas tous les changements de
précision, de moteur d’exécution ou de stratégie de génération.

## Résultats locaux disponibles

PC de développement i7-13700KF, RTX 2060 SUPER 8 Go. Même référence vocale
synthétique, français, exagération 0,5, CFG 0,5 pour PyTorch. Aucun appel payant,
aucun changement du service actif, aucune diffusion sur le terminal.

Médianes de trois générations de la réponse « Il est vingt heures quarante-trois. »,
moteur chargé et référence préparée. Temps du WAV complet, hors STT/IA/réseau,
pas des mesures du premier son en streaming ni de la future VM.

| Variante | Génération médiane | Limites observées |
| --- | --- | --- |
| CPU PyTorch initial, 4 threads, 2.15/Windows Python 3.14 | 9,826 s | Référence du premier banc C |
| CPU PyTorch 2.6, 4 threads, Python 3.11 | 8,749 s | Dérive majeure sur l’essai long |
| CPU PyTorch 2.6, 8 threads, Python 3.11 | 7,979 s | Gain insuffisant ; courts énoncés seulement |
| RTX PyTorch FP32, 4 threads CPU, 2.6/CUDA 12.4 | 1,842 s | Gain réel local ; instabilités de contenu à contrôler |
| RTX avec autocast FP16 | 1,940 s | Pas de gain sur cette carte, mémoire allouée supérieure |
| CPU, quantification dynamique INT8 du transformeur | 15,049 s | Audio de durée différente, pas de gain fiable |
| CPU, export ONNX Q4, ONNX Runtime 1.22.1 | 3,711 s | Courte phrase seulement ; essai long invalide |

Les contextes d’exécution, versions et sorties audio diffèrent : ce tableau
ne mesure pas une accélération à waveform identique. Petit banc exploratoire,
pas une garantie de temps de réponse ou une comparaison de charge contrôlée.

Le contrôle CPU avec PyTorch 2.6 à quatre threads termine le texte long en
129,486 s pour 36,7 s d’audio avec avertissement de répétition. Ce rendu est
beaucoup plus long que le C validé et ne constitue pas un résultat acceptable
pour la conversation. Le début du test à huit threads a chevauché la fin de ce
test long ; ses chiffres sont donc exploratoires. Les échantillons à graines
identiques ne sont pas identiques entre versions/matériels.

Le GPU FP32 produit le texte long en 5,278 s pour 6,86 s d’audio. Environ 3,48 Go
de mémoire GPU sont alloués au maximum selon PyTorch, hors réservations et autres
usages Windows. FP16 atteint environ 4,51 Go dans ce banc, sans amélioration
convaincante du délai court. Le modèle et la référence doivent rester chargés :
le chargement GPU initial prend environ 19 s.

## Qualité et robustesse : points bloquants

- Whisper retrouve les phrases principales du GPU sur le texte long, mais
  reconnaît « 1h43 » au lieu de « 20h43 » sur certains courts essais (graines
  42 et 123). Le test avec la graine 7 retrouve « 20h43 ». Une omission du mot
  « ont » est également possible dans un autre essai selon la transcription.
  Ce sont des alertes de couverture, pas une preuve acoustique définitive :
  écoute humaine nécessaire avant remplacement du moteur actif.
- Les trois répétitions du même texte et de la même graine sont des mesures de
  temps, pas trois validations indépendantes de robustesse.
- L’export ONNX communautaire utilise une génération gloutonne et une pénalité
  de répétition 1,2, différente du sampling et du CFG du banc C. La courte phrase
  est reconnue correctement ; sur le texte long, le modèle atteint la limite
  de 600 tokens sans fin normale : 43,254 s de génération, 24,02 s d’audio,
  transcription ne retrouvant que les trois premières phrases. Variante non
  retenue pour le service dans cet état.
- Initialisation du décodeur ONNX très longue avec ORT 1.31.0/1.31.1 sous Windows,
  avec ou sans optimisation de graphe. Essai terminé avec ORT 1.22.1 et optimisation
  du décodeur désactivée : environ 61,8 s de chargement/préparation. Ce problème
  Windows n’est pas une mesure ni une preuve d’échec sous Debian.
- Aucune de ces variantes accélérées n’est encore validée à l’écoute humaine.

## Conséquences pour la VM Debian

Le temps RTX ne s’applique pas à la Radeon 780M. CUDA n’est pas le moteur
d’exécution de cette cible AMD. DirectML est une piste Windows, donc hors du
choix utilisateur Proxmox/VM Debian.

La documentation AMD consultée décrit des APU Radeon 780M dans certaines
configurations ROCm récentes ; elle ne valide pas à elle seule la combinaison
exacte **8745HS + passthrough Proxmox + VM Debian + Chatterbox**. Ne pas annoncer
le GPU inutilisable ni promettre son accélération avant vérification.

À réception, prévoir une recette dans la VM réelle :

1. Relever CPU et instructions visibles, version Debian/noyau, mémoire libre,
   topologie RAM, contraintes thermiques et autres charges du homelab.
2. Mesurer le moteur d’origine chargé en permanence à 2, 4 puis 8 threads, sans
   supposer qu’un plus grand nombre de threads améliore les délais. Dimensionnement
   VM et éventuel type CPU `host` restent des paramètres à valider, pas appliqués.
3. Comparer courts énoncés, phrases longues et plusieurs graines ; vérifier mots
   omis, nombres, liaisons et « plus », avec écoute humaine et mesure de temps.
4. Examiner l’accès à la Radeon séparément si nécessaire : IOMMU/groupes PCI,
   passthrough, pilote et runtime compatibles dans l’invité. Aucune modification
   Proxmox réalisée.
5. Mesurer ensuite le premier son et la réponse complète dans la chaîne Alfred,
   y compris STT, IA, synthèse et lecture ESP32. Garder le modèle et le conditionnement
   vocal en mémoire ; le découpage en phrases n’annule pas le coût d’une réponse
   courte et ne corrige pas un moteur plus lent que le son qu’il produit.

## Banc reproductible

`scripts/bench_chatterbox.py` est indépendant d’Alfred. Il prend une référence
audio locale et des poids locaux (ou le cache HF déjà rempli), fonctionne hors
ligne, conserve le filigrane et écrit uniquement des WAV et un rapport JSON dans
le dossier de sortie choisi. Aucun accès à HA, à l’IA ou au terminal.

Exemple sous Debian, depuis le projet, **avec un environnement de banc isolé
déjà préparé** et les fichiers privés transférés volontairement :

```bash
python scripts/bench_chatterbox.py --device cpu --precision fp32 --threads 4 \
  --model-dir /chemin/local/chatterbox-v2 \
  --reference /chemin/local/reference-synthetique.wav \
  --output-dir .local/bench-debian-cpu4
```

Le dossier de poids v2 doit contenir `ve.pt`, `t3_mtl23ls_v2.safetensors`,
`s3gen.pt`, `grapheme_mtl_merged_expanded_v1.json` et les fichiers de configuration
optionnels du checkpoint. Révision utilisée :
`5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`.

Environnement GPU local de test : Python 3.11.15, PyTorch 2.6.0+cu124,
torchaudio 2.6.0+cu124, Chatterbox 0.1.7, transformers 5.2.0, NumPy 1.26.4,
setuptools 80.10.2 pour le filigrane Perth. Cet environnement Windows/CUDA
ne doit pas être copié comme environnement de production Debian. Les bibliothèques
CPU compatibles devront être installées dans l’environnement de banc Debian.

Mesures et scripts exploratoires privés : `.local/tts-latency-20261108/`.
Les échantillons initiaux validés C restent dans `.local/tts-comparison-20261108/`.
La référence et la préférence vocale du service Alfred sont conservées.

## Essai conversationnel CPU réalisé puis rejeté

À la demande explicite de l’utilisateur, Chatterbox v2 est maintenant sélectionné
comme voix d’essai dans Alfred, sur le **CPU du PC actuel**, sans attendre l’AuBox.
**Retour suivant : trop lent, essai rejeté.** Chatterbox CPU est arrêté ; Henri via
Home Assistant Cloud est maintenant la voix d’essai active. Voir S24 et
`docs/TTS_CLOUD_HENRI.md`.
L’environnement CPU d’origine du banc C est réutilisé, pas l’environnement CUDA.

- Choix : `chatterbox-cpu`, visible dans le laboratoire vocal ; français, quatre
  threads CPU, mêmes poids/référence, graine 42 et paramètres exagération/CFG 0,5.
- `alfred/chatterbox_cpu.py` pilote `alfred/chatterbox_worker.py`, processus local
  sans fenêtre et conservé en mémoire. Communication stdio bornée, aucune écoute
  réseau ajoutée, GPU masqué, modèle chargé localement, aucun téléchargement.
- Le moteur reçoit les heures développées en lettres ; les négations contenant
  « plus » ne sont pas réécrites pour cette voix. WAV mono en mémoire seulement.
- Erreur ou génération dépassant le délai de 60 s : arrêt du worker et message
  d’échec, pas de bascule silencieuse vers Supertonic ni nouvelle action exécutée
  par le moteur TTS. Un nouveau tour peut relancer le worker.
- Contrôle CPU autonome : modèle chargé en 12,88 s ; heure en 9,770 s puis négation
  en 10,741 s avec le même worker ; fermeture vérifiée.
- Dans le service masqué Windows : un premier essai prend 40,115 s. Application
  du réglage HighQoS déjà utilisé par Alfred au worker enfant : essai suivant en
  9,096 s pour « Il est 20h43. », WAV valide de 2,94 s, HTTP 200 et métadonnées
  Chatterbox sans repli. Aucun son diffusé pour ces contrôles techniques.
- Vérification : 430 tests Python réussis, 4 optionnels ignorés ; 30 tests JS réussis.
  Après HighQoS : cinq tests ciblés et nouvelle synthèse réelle réussis.

Essai utilisateur : parler avec Jarvis comme d’habitude. Le délai CPU reste de
l’ordre de dix secondes sur une réponse courte, auquel s’ajoutent les autres
étapes ; naturel et réponses longues restent à valider en vraie conversation.

Pour revenir à la référence précédente, sélectionner **Alfred · référence validée**
dans la liste des voix du laboratoire. La préférence antérieure est aussi sauvegardée
localement dans `.local/data/voice.before-chatterbox-cpu.json`. Les paramètres privés
CPU sont sous `.local/data/chatterbox.json`, sans secret. L’environnement du service
principal, le firmware et la configuration du mot Jarvis sont conservés.

## Sources officielles et exporteur

- [AMD Ryzen 7 8745HS](https://www.amd.com/en/products/processors/laptop/ryzen/8000-series/amd-ryzen-7-8745hs.html)
- [Matrice de compatibilité ROCm](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html)
- [DirectML : Windows et DirectX 12](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)
- [Versions et roues PyTorch 2.6](https://docs.pytorch.org/get-started/previous-versions/)
- [Chatterbox officiel](https://github.com/resemble-ai/chatterbox)
- [Export ONNX communautaire et algorithme d’inférence](https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX)
