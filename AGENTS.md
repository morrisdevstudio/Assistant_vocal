# Mémoire du projet Alfred

## GitHub Actions artifact policy (morrisdevstudio)

Applies to every existing and future repository owned by `morrisdevstudio`.
Minimize Actions storage without compromising tests, debugging, or official releases.

| Artifact purpose | Retention |
| --- | --- |
| Useful development builds (commits and pull requests) | 2 days |
| Test reports, exported diagnostic logs, screenshots | 7 days |
| Intermediate files needed by other jobs | 1 day fallback; delete after their last successful use |
| Official installers and distribution archives | GitHub Releases |
| Temporary files after successful publication | Delete when no consumer or recovery step needs them |

- Do not upload files without an identified download, diagnostic, or cross-job transfer need. Keep files local when all consumers run in the same job.
- Every `actions/upload-artifact` step must set an explicit `retention-days`. Upload only the required files, not an entire output directory by default.
- Preserve useful failure diagnostics for 7 days. Use `if: failure()` for failure-only diagnostics; retain successful test reports too when required for analysis or coverage.
- Publish official `.exe`, `.msi`, `.zip`, and other release assets directly to GitHub Releases. Preserve existing approved distribution/update channels; this storage policy does not authorize a production deployment.
- Do not retain redundant installer copies in Actions after successful publication. Never alter or delete assets already published in GitHub Releases as part of storage cleanup.
- Before changing a workflow, inspect producer/consumer jobs, reusable workflows, publication scripts, environment approvals, and retry/recovery behavior. If a necessary approval or recovery window exceeds 1 day, document and use the shortest sufficient intermediate retention.
- Delete intermediate artifacts only after successful publication and their last consumer. Restrict cleanup to exact artifact IDs or known names in the current run; never delete files still needed by queued, running, or failed jobs awaiting diagnosis/retry.
- On adoption, review existing artifacts separately: retention changes do not shorten existing expiry dates. Preserve necessary diagnostics and development downloads still within their useful window.
- Before finishing, validate workflow syntax, dependencies, explicit retention, and cleanup ordering. Check official assets remain available and report any execution checks that could not be run. Do not trigger a release merely to test retention.
- Review unnecessary repeated builds, but preserve required checks and deployment behavior. Actions caches have a separate allowance; do not purge useful dependency caches to fix the artifact quota.
- For every newly created repository, add this policy to its root `AGENTS.md`, configure the repository retention fallback to 7 days, and apply explicit 2/7-day artifact retention from the first workflow. The repository fallback also governs logs and run/check history, so explain this effect when setting it.

Actions builds and tests; GitHub Releases distributes and preserves official versions.

## Source de référence

- Lire `CADRAGE.md` avant de poursuivre le cadrage ou l'implémentation.
- Lire aussi `CHECKLIST.md` pour connaître les tâches, dépendances et points différés.
- Maintenir `CHECKLIST.md` au fil de la discussion sans demande supplémentaire :
  ajouter chaque nouveau travail identifié, ses contraintes et prérequis ; mettre
  à jour son état et les dépendances affectées. Conserver les identifiants stables.
- Ne cocher un point qu'après décision ou vérification effective ; distinguer les
  propositions, les essais restant à faire et les points différés par l'utilisateur.
- `CADRAGE.md` contient les décisions fonctionnelles validées, les contraintes,
  les faits techniques connus et les questions ouvertes du projet.
- Mettre à jour ce document au fil de la discussion dès qu'une décision est
  validée ou corrigée, sans attendre une demande supplémentaire de l'utilisateur.
- Distinguer explicitement décisions validées, propositions non validées et
  informations techniques à vérifier. Ne pas transformer une suggestion en accord.
- Lorsqu'une décision change, modifier la règle existante pour éviter les
  contradictions et ajouter une entrée concise au journal des décisions.
- Une nouvelle instruction de l'utilisateur prévaut sur la mémoire existante.

## Façon de travailler

- Échanger en français et avancer par questions utiles pour cadrer le projet.
- Rechercher dans les documents disponibles les informations déjà connues plutôt
  que demander à l'utilisateur de les répéter.
- L'utilisateur a confirmé le 26 octobre être rentré chez lui et avoir branché
  l'ESP32. Vérifier la détection et l'état réel avant toute opération matérielle.
- Ne jamais enregistrer de clés API, mots de passe ou autres secrets dans ces
  documents. Les souvenirs des utilisateurs et profils vocaux n'ont pas leur
  place dans la documentation versionnée du projet.
- Vérifier la documentation officielle actuelle avant de figer les composants,
  leur compatibilité, leurs tarifs ou leurs capacités.

## État initial

- Architecture autonome et base du prototype validées ; socle local FastAPI et
  échéances SQLite implémentés, interface locale sur 127.0.0.1:8765. Voir `README.md`
  pour lancer et tester. v0.2 ajoute un banc micro navigateur et STT/TTS locaux
  (Whisper base/Piper Tom), sans IA ni action ; essai micro navigateur validé par
  l'utilisateur. Choix de voix définitif et essais ESP32/serveur restent ouverts.
  v0.3 ajoute le connecteur Command Code texte/voix et la saisie de clé locale
  protégée ; fonctionnement conversationnel réel validé par retour utilisateur.
  Mesures de performances et outils IA restent à réaliser. Ne jamais lire,
  afficher ou demander la clé dans le chat. Profils, HA et ESP32 restent à raccorder.
  v0.4 ajoute la reprise conversationnelle navigateur : huit secondes après la
  lecture, envoi après pause, arrêt et silence sans appel IA. Boucle testée avec
  micro artificiel ; essai humain, réglage de détection, profils et barge-in ouverts.
  v0.5 ajoute les lumières Home Assistant (jeton local protégé, commandes directes
  sans IA). Testé contre un HA simulé uniquement ; la connexion réelle, les
  permissions par profil et les exclusions de lampes restent à faire. Panneau et
  connexion réelle validés par l'utilisateur ; basculement d'une lampe à confirmer.
  Essais Assist existants sur la carte ; suite audio différée. État et progression
  dans `CHECKLIST.md` et `CADRAGE.md`.
  Le 30 octobre, l'utilisateur rejette Piper (Alfred et majordome mal prononcés).
  Supertonic 3 local assure cinq voix masculines M1 à M5. Pocket TTS est retenu
  pour la voix clonée rapide sur CPU, avec M3 en secours ; le choix et le repli
  sont intégrés. Le profil de la référence nettoyée est exporté et actif sous
  `.local`, avec 600 ms de médiane et 655 ms au p95 sur des réponses courtes.
  La similarité de locuteur progresse face à M3 et au profil non nettoyé, mais le
  timbre et la diction restent à valider par écoute humaine.
- Le projet concerne l'assistant vocal Alfred et son intégration au Home Assistant
  existant. Ne pas confondre avec l'assistant de maintenance du projet Serveur.
