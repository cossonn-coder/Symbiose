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
2. **Suspension étendue aux skills.** Le brief suspend `ask-deepseek` sur les
   tours d'audit pré-fix. Étendre la suspension à **`/audit-projet`,
   `/refactor`, `/sprint-auto` et `/conception`** : ces skills lisent massivement
   et par construction, et leur jugement doit porter sur le **contenu brut**, pas
   sur un résumé de 400 tokens. Un audit qui délègue sa lecture n'audite rien.
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
exemples (`docs/champs/eau/dette_hydrologie.md`, etc.).

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
