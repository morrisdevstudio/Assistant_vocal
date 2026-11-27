# Comparaison de diction française — 8 novembre 2026

Comparaison autorisée par l’utilisateur après son retour sur les liaisons,
la diction peu naturelle et le s de « plus » avec Supertonic. Aucun moteur,
profil, débit ou service de l’assistant actif n’a été modifié pour ce banc.
Jarvis reste actif. Aucun son n’a été diffusé automatiquement sur la carte.

## Extraits à écouter

Fichiers locaux dans `.local/tts-comparison-20261108/` :

| Repère | Configuration | Fichier |
| --- | --- | --- |
| A | Référence Alfred Supertonic, débit actuel 1,242 | `A-actuel-1.242.wav` |
| B | Même profil et moteur, débit 1,0 | `B-meme-voix-1.0.wav` |
| C | Chatterbox Multilingual v2, français, débit natif | `C-chatterbox-fr.wav` |

Texte identique, transmis en une seule fois sans découpage ni préparation
`prepare_tts_text`, pour entendre les homographes au lieu de les reformuler :

> Il est vingt heures quarante-trois. Les enfants ont deux amis. Nous avons un
> rendez-vous. Du pain et un œuf. Il n’y a plus de pâtes. J’en veux plus, ajoute
> une portion.

Les heures sont déjà écrites en lettres pour tous les candidats. Le test porte
sur la diction, pas sur la capacité propre à développer une heure numérique.
Écouter notamment les liaisons dans « les enfants », « deux amis », « nous avons »
et « un œuf », l’absence de liaison après « et », ainsi que « plus » négatif sans
s et « plus » signifiant davantage.

Retour utilisateur après écoute : **C est nettement meilleur** ; A et B donnent
le même résultat concernant le français. La préférence de diction pour C est
validée sur cet extrait. Le ralentissement de Supertonic ne suffit pas selon cet
essai. Cela ne constitue pas une validation exhaustive du français ni une
acceptation du délai CPU ou un ordre de remplacement du service actif.

## Mesures sur le PC actuel, CPU seulement

| Configuration | Génération du texte complet | Audio produit | Réponse courte, médiane de 3 générations moteur chaud |
| --- | --- | --- | --- |
| A | 2,010 s | 10,449 s | 0,530 s |
| B | 2,466 s | 12,957 s | 0,666 s |
| C | 22,020 s | 7,660 s | 9,826 s |

Réponse courte identique : « Il est vingt heures quarante-trois. »
Ces temps correspondent à la production du WAV complet ; ils ne mesurent ni
le premier son en streaming, ni le STT, le LLM, le réseau ou la lecture ESP32.
Ils ne sont pas des performances garanties sur le futur serveur Pentium.

Modèles chargés séparément : environ 1,006 s pour Supertonic ; 16,198 s pour
Chatterbox avec préparation de la référence. Quatre threads CPU pour chaque
moteur ; pas d’essai GPU. Les trois répétitions courtes utilisent le même texte,
et Chatterbox la même graine. Il s’agit d’un petit banc, pas d’un p95 général.

Chatterbox utilise l’environnement déjà présent, hors ligne, modèle v2 du cache
`5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18` ; ce n’est pas un essai du nouveau
checkpoint v3. La référence vocale est le sample **synthétique** de la banque
Alfred, sans nouvel enregistrement ni envoi de voix privée. Paramètres : français,
exagération 0,5, CFG 0,5, graine 42. Filigrane Perth conservé.

## Vérifications et limites

- Douze WAV mono non vides, valeurs finies, durées et fréquences vérifiées.
- Une transcription Whisper small des trois textes complets et de la réponse
  courte C retrouve les phrases principales. Elle présente des variantes,
  notamment sur B, et ne prouve ni l’exactitude phonétique ni les bonnes liaisons.
- Les avertissements d’arrêt anticipé/répétition de Chatterbox ont motivé ce
  contrôle de couverture ; le retour humain est ensuite favorable à C sur
  l’extrait comparé. Les avertissements restent à surveiller sur un corpus élargi.
- A et B isolent le débit avec le même profil. C compare un autre moteur avec
  conditionnement sur la référence synthétique ; le timbre peut changer.
- Chaque moteur reçoit une phrase complète. Les coupures entre blocs de la
  conversation réelle ne sont donc pas évaluées ici.
- Chatterbox est sensiblement plus lent sur ce CPU dans ce banc ; aucune
  intégration en remplacement du moteur actif n’est réalisée. La préférence
  d’écoute pour C est acquise, mais la latence reste à traiter.

Script et mesures détaillées : `compare.py`, `supertonic-results.json`,
`chatterbox-results.json`, `summary.json` et `transcription-check.json` dans le
dossier local du banc. Aucune dépendance du service principal n’a été changée.

Références officielles consultées :

- [Supertonic 3](https://huggingface.co/Supertone/supertonic-3)
- [Chatterbox : utilisation et français](https://github.com/resemble-ai/chatterbox)
- [Code officiel Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py)
