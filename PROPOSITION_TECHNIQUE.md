# Alfred — proposition de briques techniques

Date : 26 octobre 2026. Statut : **base de prototype validée sur le principe**.
Cette sélection complète `CADRAGE.md`. Les moteurs proposés sont retenus pour les
premiers essais, sans garantie de performances ni choix définitif de voix, modèle
de langage, réveil, firmware ou hébergement. Premier prototype prévu dans le navigateur.
Mise à jour du 30 octobre : Piper est rejeté après écoute. Pocket TTS 4.0.1 est
retenu pour la voix clonée rapide sur CPU, avec Supertonic 3 en secours ; le timbre
final n'est pas encore validé.

## Base proposée pour le prototype

| Fonction | Candidat initial | Validation nécessaire |
|---|---|---|
| Transcription française | Parakeet TDT 0.6B v3 INT8, stack Murmure 1.11.3 autonome sur CPU, seul STT conservé | Recette sous charge sur la future VM Debian, bruit, distance et voix enfant |
| Synthèse française | Pocket TTS 4.0.1 sur CPU pour la voix clonée privée ; Supertonic 3 (M1–M5) en secours | Timbre et diction à confirmer par écoute ; profil `.safetensors` local ; accès Hugging Face ponctuel pour accepter la licence et télécharger les poids |
| Identification familiale | SpeechBrain ECAPA-TDNN, embeddings locaux et comparaison aux profils | Enrôlement et calibration par personne ; voix inconnues, enfant, phrases courtes, bruit |
| Réveil Alfred | Modèle personnalisé, moteur non figé | Prononciation française et exemples négatifs Fred ; ne pas présumer un modèle prêt à l'emploi |
| Conversation | API Command Code GOAT, client avec réponses en streaming | Tester un modèle rapide inclus et ses appels d'outils ; sélection après mesure, sans abonnement supplémentaire présumé |
| Coordination | Service Python / FastAPI, sessions par terminal et locuteur | Interfaces audio et intégration à préciser |
| Persistance initiale | SQLite, données séparées par profil et maison | Contrôle d'accès applicatif, purge historique, sauvegarde ; pas de base vectorielle dédiée initialement |
| Déploiement | Conteneurs sur une machine Linux du serveur Proxmox | Choisir l'hôte après mesure des ressources libres ; Pi 4 non privilégié pour cumuler les modèles |
| Firmware autonome | Évaluer ESP-IDF + ESP-SR pour audio et annulation d'écho | Brochage et codecs de la carte, duplex audio, charge CPU, interruption ; aucune implémentation présumée |

Pocket TTS a été retenu après comparaison : il clone sur CPU et génère plus vite
que le temps réel sur ce PC. Qwen3-TTS GGUF et Chatterbox ont été écartés pour la
voix interactive à cause de leur latence CPU. Le profil vocal et la référence sont
privés, et toute voix source devra être utilisée avec l'accord de la personne.

La disponibilité des capacités ESP-SR n'est pas une preuve que notre carte et
notre firmware les exploitent correctement. Le banc d'essai ESPHome/Assist décrit
dans `PROTOCOLE_TEST_AUDIO.md` reste distinct du firmware autonome de production.

## Flux proposé

1. Réveil et acquisition audio ; atténuer la musique concernée.
2. Transcrire et identifier le locuteur en parallèle autant que possible.
3. Appliquer les permissions et sélectionner les mémoires selon l'identité obtenue,
   avant tout accès personnel ou action ; inconnu = invité selon le cadrage.
4. Traiter directement les commandes simples reconnues avec certitude (lumières,
   minuteurs, courses), sans appel LLM systématique. Demander une précision si besoin.
5. Utiliser Command Code pour les demandes ouvertes ou complexes, avec des outils
   contrôlés par Alfred. Chaque appel d'outil repasse par les permissions.
6. Synthétiser la réponse, reprendre l'écoute huit secondes et rétablir le volume
   selon la fin d'interaction ; interruptions et changements de locuteur à tester.

Le module de recherche Internet doit rester séparé et remplaçable : ni accès web
ni prix de recherche ne sont garantis par la seule présence du modèle Command Code.
La liste de courses HA et l'exposition à HA des fonctions personnelles restent à
spécifier conformément au cadrage.

## Budget et mesures avant adoption

- Objectif : aucun nouveau service vocal payant pour le prototype. Coûts électriques,
  ressources serveur et consommation du quota GOAT restent présents.
- Les 5 €/mois supplémentaires sont une enveloppe maximale, pas un coût prédit.
  Ne sélectionner une API vocale de secours qu'après vérification de ses tarifs et
  mesure du volume d'usage ; aucune bascule payante automatique sans réglage explicite.
- Comparer `base` et `small` sur le même corpus français ; mesurer fin de parole →
  première réponse audio, erreurs, CPU et RAM, avec le serveur dans son usage normal.
- Tester séparément reconnaissance des profils sur phrases courtes et voix enfant.
  Les performances VoxCeleb publiées ne prédisent pas celles de cette famille.
- Tester Alfred/Fred et interruption avec musique avant adoption du réveil/firmware.
- Prévoir un test depuis un navigateur pour valider le service sans ESP32 branché ;
  cela ne valide pas l'acoustique ni le firmware de la carte.

## Sources primaires consultées

- Stack STT retenue, source Murmure 1.11.3 : <https://github.com/Kieirra/murmure/tree/1.11.3>.
- Pocket TTS, modèle français local et licence CC BY 4.0 :
  <https://huggingface.co/kyutai/pocket-tts>.
- Supertonic 3, modèle ONNX local et licence OpenRAIL-M :
  <https://huggingface.co/Supertone/supertonic-3>.
- ECAPA, embeddings et limites de généralisation :
  <https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb>.
- openWakeWord : <https://github.com/dscripka/openWakeWord>. Le projet documente
  actuellement le support de l'anglais et recommande microWakeWord pour les
  microcontrôleurs ; ne pas le retenir sans essai pour Alfred en français.
- ESP-SR AFE (annulation d'écho, détection de parole, réduction de bruit) :
  <https://github.com/espressif/esp-sr/blob/master/README.md>.
- API Command Code, streaming et outils exécutés par le client :
  <https://commandcode.ai/docs/provider>.
