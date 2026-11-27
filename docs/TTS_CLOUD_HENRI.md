# Essai Henri via Home Assistant Cloud — 8 novembre 2026

Après le rejet utilisateur de la lenteur Chatterbox CPU, réutilisation du TTS
Home Assistant Cloud déjà présent : `tts.home_assistant_cloud`, français
`fr-FR`, voix masculine `HenriNeural`. L’utilisateur confirme que son abonnement
Cloud est déjà payé. Aucun nouvel abonnement, achat, compte ou clé.

## État actif

Voix d’essai `ha-cloud-henri` sélectionnée dans Alfred. Jarvis reste le mot de
réveil, traité localement ; la conversation Command Code, la transcription locale
et le transport ESP32 direct sont conservés. Seule la synthèse de la réponse
passe par Home Assistant Cloud. Le pipeline Assist existant n’a pas été modifié.

La voix de référence Supertonic reste sélectionnable pour revenir en arrière.
Chatterbox CPU est conservé dans les sources mais arrêté et rejeté pour l’usage
courant. Retour humain suivant : l’utilisateur trouve Henri bien mais souhaite une
personnalisation plus proche d’Alfred. La voix reste provisoire.

## Mesures réelles

Trois phrases courtes distinctes, sans cache permanent demandé : **265, 297 et
295 ms**, depuis la requête TTS jusqu’au WAV prêt dans Alfred. Texte de comparaison
complet : **1 783 ms** pour **13,25 s d’audio**. Fichiers d’écoute et résultats sous
`.local/tts-cloud-comparison-20261108/`.

Le contrôle HTTP du service Alfred après intégration produit une phrase inédite
« Il est 22h29. Non, il n’y a plus de pâtes. » en **1 020 ms** pour **5,02 s d’audio**,
statut 200, moteur `ha_cloud`, aucun repli. Ces mesures comprennent la récupération
et la conversion audio, pas les étapes STT/IA, la lecture ESP32 ou toutes les
conditions réseau. Aucune lecture sur les appareils n’a été lancée pour ces mesures.

## Fonctionnement

`alfred/home_cloud_tts.py` réutilise le `HomeStore` déjà protégé d’Alfred. Il demande
la génération via `POST /api/tts_get_url` puis récupère `/api/tts_proxy/...` sur le
**même Home Assistant**. Aucun jeton n’est mis dans l’URL ou affiché. Les URL externes,
autres chemins et redirections sont refusés. Taille encodée et durée PCM bornées,
délais réseau définis, erreurs publiques sans contenu privé.

`cache=false` évite de demander une conservation durable dans le cache TTS de HA.
Alfred convertit l’audio en WAV mono PCM16 24 kHz, uniquement en mémoire pour les
conversations. Cela ne constitue pas une garantie sur les traitements ou la
rétention internes du fournisseur cloud. Les fichiers d’essai génériques ont été
écrits explicitement pour la comparaison.

Les heures sont développées en lettres. Les négations avec « plus » ne sont pas
réécrites pour ce moteur. La même voix est utilisée pour les blocs progressifs.
En cas d’indisponibilité du Cloud, le service signale l’erreur ; pas de substitution
silencieuse. Le moteur Cloud n’est jamais choisi implicitement comme repli lorsque
les modèles locaux manquent.

## Vérifications et suite

443 tests Python réussis, 4 optionnels ignorés ; 32 tests JavaScript réussis.
Couverture des requêtes sans lecture, décodage mono/rééchantillonnage, conservation
du choix vocal, texte des négations, blocs progressifs, refus des redirections et
URL externes, absence de jeton dans les erreurs, absence de sélection Cloud implicite.
Santé du service, sélection Cloud, synthèse réelle et flux Jarvis contrôlés.

Restent à valider par l’utilisateur : diction et timbre Henri, liaisons, heures et
« plus », délai complet en conversation, conditions réseau et future VM Debian.
Le texte comparatif générique est disponible dans `henri-long.wav` ; ce texte
n’affirme rien sur le stock réel de la maison.

## Sources

- [Home Assistant : API TTS](https://www.home-assistant.io/integrations/tts/)
- [Nabu Casa : synthèse vocale Cloud](https://support.nabucasa.com/hc/en-us/articles/25619386304541-Text-to-speech-TTS)
- [Nabu Casa : prestations incluant STT/TTS](https://www.nabucasa.com/link/)
- [Code officiel de l’intégration Cloud TTS](https://github.com/home-assistant/core/blob/dev/homeassistant/components/cloud/tts.py)

Le connecteur et son guide Home Assistant ont servi à l’inventaire en lecture
seule ; aucun pipeline, abonnement ou appareil HA n’a été reconfiguré.

## Premiers essais de personnalisation, non activés

Le connecteur Cloud officiel expose le choix de voix, les styles éventuellement
proposés et le format audio ; il ne propose pas de réglage libre de hauteur, de
débit, de timbre ni de clonage. Des traitements après synthèse restent possibles.

Deux fichiers d’écoute séparés sous `.local/henri-tuning-20261108/` :

- `henri-pose.wav` : rubberband, tempo 0,96, hauteur inchangée.
- `henri-pose-grave.wav` : tempo 0,96, hauteur 0,94, formants préservés.

La source est le texte comparatif déjà synthétisé, sans nouvel appel Cloud.
Durée de chaque WAV : 13,8 s ; traitement mesuré à 146/144 ms sur le PC actuel.
Contrôles PCM mono 24 kHz et pics sans écrêtage. Le service conserve Henri original.
Retour utilisateur : **les deux variantes sont rejetées** (« c’est mauvais »).
Aucun traitement n’est retenu ou à intégrer ; Henri reste original, sans effet.
La personnalisation vers Alfred reste non résolue. Ne pas relancer ces variantes
sans nouvelle demande. Changer la hauteur ne transforme pas cette voix en identité
vocale d’Alfred.
Ces essais ne modifient ni la référence archivée ni les anciennes patines rejetées.
