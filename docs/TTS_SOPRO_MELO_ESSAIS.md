# Sopro et MeloTTS + OpenVoice — essais locaux du 9 novembre 2026

Mise en œuvre autorisée par l’utilisateur pour comparer les deux solutions.
Les voix sont disponibles dans le laboratoire ; **Henri reste actif** jusqu’au
choix humain. Aucun abonnement, envoi de référence audio ou synthèse cloud pour
ces deux moteurs. CPU explicite, quatre threads, modèles et références locaux.

## Essayer

Actualiser la page du laboratoire vocal, puis choisir :

- **Alfred · Sopro · CPU** (`sopro-cpu`).
- **Alfred · MeloTTS + OpenVoice · CPU** (`melo-openvoice-cpu`).

Le choix charge un processus séparé qui reste prêt pour les demandes suivantes.
L’autre processus local est fermé au changement de voix. Utiliser le bouton
d’échantillon ou la conversation navigateur ; revenir à Henri dans le même menu.
La préférence choisie est enregistrée. Une erreur de synthèse est affichée sans
changer silencieusement de moteur.

ESP32 non joignable au contrôle : l’utilisateur préfère commencer par les fichiers
et le navigateur. Aucun test de micro/haut-parleur ESP32 n’est déclaré réalisé.

## Échantillons et mesures

Sous `.local/local-tts-comparison-20261109/` :

| Fichier | Génération | Audio produit |
| --- | --- | --- |
| `sopro-court.wav` | 820 ms | 1,333 s |
| `sopro-long.wav` | 3 178 ms | 10,229 s |
| `sopro-negation.wav` | 804 ms | 1,250 s |
| `melo-openvoice-court.wav` | 4 352 ms, premier appel | 1,660 s |
| `melo-openvoice-long.wav` | 8 629 ms | 8,824 s |
| `melo-openvoice-negation.wav` | 1 871 ms | 1,730 s |

Même texte comparatif :

> Il est vingt heures quarante-trois. Les enfants ont deux amis. Nous avons un
> rendez-vous. Du pain et un œuf. Il n’y a plus de pâtes. J’en veux plus, ajoute
> une portion.

Contrôle réel via `/api/voice/config` et `/api/voice/speak`, sur la même requête
« Il est 20h43. Il n’y a plus de pâtes. » :

| Voix | Premier appel | Deuxième appel | Repli |
| --- | --- | --- | --- |
| Sopro CPU | 1 264 ms | 1 244 ms | Aucun |
| MeloTTS + OpenVoice CPU | 3 373 ms | 1 801 ms | Aucun |

Les moteurs sont chargés avant ces appels. Mesures exploratoires sur le PC de
développement, pas sur la future VM Ryzen. Elles portent sur le WAV complet,
pas sur le premier paquet du streaming natif Sopro ni sur le tour STT/IA/lecture.
Les réponses longues demandent davantage de calcul, surtout avec Melo/OpenVoice.

## Référence et versions

Référence commune : sample **synthétique** déjà accepté dans la banque Alfred,
`sample-long.wav`, durée 12,4 s. La banque archivée est lue, jamais modifiée.
Cela permet une première comparaison de clonage/transfert sans nouvel enregistrement
et sans prétendre reproduire exactement le personnage souhaité.

- Sopro 2.2.0, Python 3.11.15, PyTorch/torchaudio 2.6.0 CPU. Langue `fr`, graine 42,
  réglages de génération d’origine, référence préencodée en mémoire. Les 300 ms
  annoncées par l’auteur sur M3 ne sont pas utilisées comme résultat local.
- MeloTTS français et OpenVoice V2, Python 3.10.20, PyTorch/torchaudio 2.2.2 CPU,
  NumPy 1.22.4, transformers 4.27.4, librosa 0.9.1. Débit 1,0, conversion native,
  source vocale française officielle et empreinte cible calculée en mémoire.
  Filigrane OpenVoice conservé ; la bibliothèque signale parfois qu’un extrait
  court n’est pas assez long pour l’insérer.

Révisions :

| Source | Révision |
| --- | --- |
| Sopro V2 Turbo | `c12d0dc7c4a33b3cb6ea3d11ceb70bc60c7c6312` |
| MeloTTS français, poids | `1e9bf590262392d8bffb679b0a3b0c16b0f9fdaf` |
| OpenVoice V2, poids | `f36e7edfe1684461a8343844af60babc2efbb727` |
| BERT français Europeana | `b895c3cf291f7bf4c15639078a6bee0b3e272c5b` |
| MeloTTS, sources | `209145371cff8fc3bd60d7be902ea69cbdb7965a` |
| OpenVoice, sources | `74a1d147b17a8c3092dd5430504bd83ef6c7eb23` |

Poids du filigrane WavMark préparés explicitement dans le cache local. Sources
officielles conservées sous `.local/local-tts-sources/` avec licences et révisions.

## Adaptation du runtime français

Pour éviter de télécharger/importer les modèles des autres langues, la copie
isolée de MeloTTS charge uniquement `french` dans `melo/text/cleaner.py` et
`french_bert` dans `melo/text/__init__.py`. Les modules français lisent le chemin
local BERT via `ALFRED_MELO_BERT_DIR`. La phonémisation, les poids et les calculs
de synthèse ne sont pas changés. Cette copie sert uniquement au français.

Les deux sources sont référencées par `alfred-local-sources.pth` dans le venv
Melo/OpenVoice. Les dépendances des deux venvs sont figées dans les fichiers
`sopro-environment.txt` et `melo-environment.txt` du dossier de comparaison.
La dépendance de production Alfred n’est pas remplacée par ces bibliothèques.

## Intégration et vérification

`alfred/local_voice_cpu.py` réutilise le protocole stdio borné du client CPU,
avec un worker distinct `alfred/local_voice_worker.py`. Les implémentations sont
dans `alfred/local_voice_models.py`. Les fichiers de configuration privés sont
`.local/data/sopro.json` et `.local/data/melo-openvoice.json` : chemins locaux,
pas de clé. GPU masqué et `device=cpu`, mode hors ligne après préparation, réglage
Windows HighQoS pour les processus cachés, aucune écoute réseau supplémentaire.

Le worker renvoie un WAV en mémoire : pas de fichier temporaire de conversation.
OpenVoice reçoit sa source de conversion via `BytesIO`. Limites de requête, de
durée et de délai conservées. Seuls les extraits génériques explicitement préparés
pour l’écoute sont écrits dans le dossier du banc.

460 tests Python réussis, 4 optionnels ignorés ; 36 tests JS réussis. Les contrôles
couvrent disponibilité des assets, sélection persistante, réutilisation/fermeture
du worker, mode CPU/hors ligne, erreurs sans repli, synthèse normale et progressive
et les choix dans l’interface. Sept WAV mono PCM16 vérifiés, sans écrêtage.

Whisper retrouve les phrases principales des deux moteurs. Sur Melo, il transcrit
« deux années » pour « deux amis » : doute de prononciation à écouter. Ce contrôle
ne valide pas le timbre, les liaisons ou le s de « plus ». Acceptation humaine,
stabilité sur d’autres phrases et mesures dans la VM Debian restent ouvertes.

## Sources officielles

- [Sopro](https://github.com/samuel-vitorino/sopro)
- [Modèle Sopro V2 Turbo](https://huggingface.co/samuel-vitorino/sopro-v2-turbo)
- [MeloTTS](https://github.com/myshell-ai/MeloTTS)
- [OpenVoice : installation et usage V2](https://github.com/myshell-ai/OpenVoice/blob/main/docs/USAGE.md)
