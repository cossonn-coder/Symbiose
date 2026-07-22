# ⑥ Protocole de délégation DeepSeek

**Préalable** : lire `00_etat.md`. Ce tronçon est **autonome** des cinq autres —
il peut être joué en premier si besoin (il ne dépend que de l'existence de
`docs/meta/agent/`, créé au tronçon ①).

## Livrables

1. `docs/meta/agent/deepseek_protocol.md` — la spec complète.
2. Un **pointeur court** en tête de `CLAUDE.md` (≤ 10 lignes) vers cette spec.

## État vérifié des outils (2026-07-22)

- `~/.local/bin/{ask,write,extract}-deepseek` → symlinks vers
  `~/Nextcloud/projects/aria/bin/*.py`. Présents, `--help` fonctionnel.
- Modèle : `deepseek-v4-flash`, `BASE_URL=https://api.deepseek.com`.
- Clé lue dans `os.environ["DEEPSEEK_API_KEY"]`, posée dans
  `~/.config/deepseek.env` (mode 600), sourcée en tête de `~/.bashrc`.
  **Le fichier doit contenir le mot-clé `export`** — sans lui, la variable
  n'atteint pas les sous-processus Python. Sourcer explicitement en cas de
  doute : `. ~/.config/deepseek.env && ask-deepseek …`.
- Signatures réelles :
  - `ask-deepseek --paths F [F…] --question "…" [--think]`
  - `write-deepseek --spec "…" [--context F [F…]] --target F [--lang L] [--think]`
    (`--lang` défaut `python`)
  - `extract-chat <source> -o <sortie>`

## Rôles (adaptés à Symbiose)

| Outil | Rôle |
|---|---|
| `write-deepseek` | écriture de doc (journal, backlog, dette) + boilerplate (docstrings, scaffolding). Conception et commentaires de code : **après validation Nico**. |
| `ask-deepseek` | lecture/recherche multi-fichiers, cartographie de renvois |
| `extract-chat` | logs **de jeu** uniquement → fichier nommé et daté |

## Adaptations obligatoires au projet — ne pas recopier le brief tel quel

Le protocole d'origine vient d'un autre projet. Quatre points **entrent en
collision** avec les règles de Symbiose et doivent être écrits explicitement :

1. **Les tests moteur ne sont PAS du boilerplate.** Le brief dit « ne jamais
   générer soi-même de tests ». Chez Symbiose, `tests/test_golden.py` et les 11
   suites ciblées sont du **code de vérité écologique** : ils encodent le
   déterminisme (règle de design #3). Ils restent **écrits par Claude**.
   `write-deepseek` ne génère que des tests **périphériques** (outils, parsing).
2. **Suspension par NATURE DE TÂCHE, pas par skill** (arbitrage Nico, 2026-07-22).
   Découper ainsi, et l'écrire tel quel dans la spec :

   **✅ Repérage factuel → `ask-deepseek`**, y compris et surtout dans
   `/conception` (c'est là que le gain est maximal : 56 docs, 13 954 lignes) :
   - inventaire d'ouverture : « quels docs/sprints touchent déjà ce sujet ? »
   - **anti-doublon** : « ce gène / ce champ / cet effet existe-t-il déjà ? »
     (garde-fou réel : l'incident `resilience_base` du sprint santé était
     exactement un doublon non détecté)
   - cartographie de couplages : « quels modules lisent le champ `humidite` ? »
   - **voix narratives** : « l'espèce Y a-t-elle ses 5 entrées ? » (règle projet
     « toute plante ajoutée = toutes ses voix », coûteuse à vérifier à la main)

   **❌ Jugement → Claude lit le texte brut** :
   - les 2-3 docs qui **font l'objet** du travail de conception
   - toute question de jugement écologique ou de philo #1-#7 — DeepSeek ne
     connaît ni la philo ni le moteur, il répondrait du plausible invérifiable
   - « quel trou vois-tu dans cette mécanique ? » : un trou de conception se voit
     dans l'interstice entre deux phrases, pas dans un résumé de 400 tokens
   - les tours d'**audit pré-fix**, et `/audit-projet` dans sa phase de verdict

   **Deux garde-fous** : (a) **pipeline en deux temps** — DeepSeek *localise*,
   Claude lit le passage trouvé ; on délègue la fouille, jamais la lecture de
   fond. (b) Toute information issue d'`ask-deepseek` qui va **influencer une
   décision gravée** dans un kickoff est **revérifiée** par `grep` ou lecture
   ciblée : une réponse DeepSeek n'est ni reproductible ni traçable, et le
   projet est déterministe par principe (règle de design #3).

2bis. **Cas `/sprint-auto`** (arbitrage Nico, 2026-07-22) — bien plus restrictif
   que `/conception`, pour une raison structurelle : `/conception` **cherche**
   (corpus large, on ignore où ça vit) tandis que `/sprint-auto` **modifie**
   (fichiers déjà désignés par le kickoff, et il faut le **texte exact** pour
   éditer — un résumé est inutilisable pour un `Edit`).

   **✅ Autorisé** : cartographie d'**impact imprévue** (« qui d'autre lit ce
   champ ? », effet de bord découvert en cours de tronçon) ; vérification de
   correspondance **Python ↔ C#** au tronçon « vue Godot ».

   **❌ Interdit** : lire le code que le tronçon va modifier ; **générer du code
   moteur via `write-deepseek`** (`data/code/` est la source de vérité
   écologique et le golden est un hash — du code non relu ligne à ligne qui doit
   préserver un hash exact est le scénario qui casse le golden, pour zéro gain
   de contexte) ; diagnostiquer un golden qui a bougé ou un test rouge (jugement).

   **Capteur** : un sous-agent qui a besoin de fouiller révèle un **kickoff
   incomplet** — au même titre que la taille d'un fichier révèle une dette de
   refactor. Le consigner dans `00_etat.md` au lieu de l'absorber en silence.

   **Plafond budget** : appels DeepSeek réservés à l'**orchestrateur** ; les
   sous-agents n'y recourent que pour la cartographie d'impact, jamais en
   routine d'ouverture. L'orchestrateur ne voit pas la consommation de ses
   sous-agents et la clé est plafonnée (~20 €).
3. **`extract-chat` ne doit JAMAIS viser `~/.claude/projects/`.** Les transcripts
   de session peuvent contenir des secrets (c'est déjà arrivé le 2026-07-22 : la
   clé DeepSeek a fuité dans un transcript). `extract-chat` est réservé aux logs
   **produits par le jeu**. Écrire cette interdiction en toutes lettres.
4. **Français forcé.** Les `--spec` doivent exiger explicitement « en français,
   accents et diacritiques corrects » — c'est un garde-fou projet, et rien ne
   garantit que le modèle le fasse par défaut.

## Contenu de la spec

Reprendre la structure du brief amont (rôles, déclencheurs, syntaxe, exemples,
répartition des responsabilités, interdictions) **en y intégrant les 4
adaptations ci-dessus**, et en utilisant les chemins **post-rangement** dans les
exemples (`docs/champs/eau/dette_eau.md`, etc.).

Workflow de MàJ doc après session (sans `extract-chat`) :
1. Claude rédige la synthèse et identifie **le thème**.
2. `write-deepseek --spec "<synthèse>" --context <fragment> --target <fragment>`.
3. Répercussion sur `backlog_<theme>.md` / `dette_<theme>.md` du même thème.

## Vérification

- `docs/meta/agent/deepseek_protocol.md` existe, en français, et contient les 4
  adaptations.
- Le pointeur en tête de `CLAUDE.md` fait ≤ 10 lignes et cite le bon chemin.
- Test de bout en bout, **sur une cible jetable** (pas un fichier du dépôt) :
  ```bash
  . ~/.config/deepseek.env
  ask-deepseek --paths CLAUDE.md --question "En une phrase : quel est ce projet ?"
  ```
  Si erreur de clé → vérifier le `export`. Ne pas insister au-delà de 2 essais,
  remonter à Nico (budget limité : ~20 € sur la clé, dédiée à cette tâche).
- `cd data/code && python3 -m tests.test_golden` → **inchangé**.

## Commit

`docs(rangement) ⑥ : protocole de délégation DeepSeek + pointeur CLAUDE.md`

Puis cocher ⑥ dans `00_etat.md` et clore le sprint (journal + BACKLOG).
