# Protocole de délégation DeepSeek

**Rôle de ce document** : dire **quand** Claude a le droit de sous-traiter une
tâche à DeepSeek, **quand il ne l'a pas**, et **comment** appeler les outils.
Gravé au tronçon ⑥ du sprint de rangement documentaire (2026-07-22).

**Le principe en une phrase** : *DeepSeek localise, Claude lit et juge.* On
délègue la **fouille** dans un corpus devenu gros (56 conceptions, ~14 000
lignes, 340 fichiers de sprint), jamais la **lecture de fond** ni la décision.

---

## 1. Sécurité — la clé, d'abord

Un incident de fuite a eu lieu le **2026-07-22** : la clé DeepSeek s'est
retrouvée en clair dans un transcript de session. D'où trois règles dures :

1. **Ne jamais afficher la clé.** Pas de `cat ~/.config/deepseek.env`, pas de
   `env | grep DEEPSEEK`, pas d'`echo "$DEEPSEEK_API_KEY"`. Pour vérifier que
   la clé est en place, on teste une **propriété**, jamais la valeur :
   `grep -c '^export DEEPSEEK_API_KEY=' ~/.config/deepseek.env`.
2. **Aucun secret dans un fichier du dépôt**, jamais — ni en exemple, ni en
   commentaire, ni « temporairement ».
3. **Pas de copie de sauvegarde qui traîne** (`*.env.bak`, fichier dans
   `/tmp`) : si un correctif touche le fichier de clé, la copie est supprimée
   dans la même commande.

La clé vit dans `~/.config/deepseek.env` (mode `600`), **hors du dépôt**, et
ce fichier **doit contenir le mot-clé `export`** :

```bash
# forme attendue (valeur non montrée)
export DEEPSEEK_API_KEY=…
```

Sans `export`, la variable reste locale au shell et **n'atteint pas les
sous-processus Python** des outils → erreur « variable non définie ». En cas de
doute, sourcer explicitement avant l'appel : `. ~/.config/deepseek.env`.

**Budget** : la clé est plafonnée (~20 €) et dédiée à cet usage. En
non-thinking, `deepseek-v4-flash` coûte ~0,14 $/M tokens d'entrée et
~0,28 $/M en sortie ; le mode `--think` compte les tokens de raisonnement en
sortie (prévoir large). Deux échecs d'affilée sur une même question →
**on arrête et on remonte à Nico**, on n'insiste pas.

---

## 2. Les outils installés

`~/.local/bin/{ask,write,extract}-deepseek` → symlinks vers
`~/Nextcloud/projects/aria/bin/*.py`. Modèle `deepseek-v4-flash`,
`BASE_URL=https://api.deepseek.com`.

| Outil | Signature réelle |
|---|---|
| `ask-deepseek` | `--paths F [F…] --question "…" [--think] [--allow-missing] [--yes]` |
| `write-deepseek` | `--spec "…" [--context F [F…]] --target F [--lang L] [--think] [--allow-missing] [--force] [--mkdir]` (`--lang` défaut `python`) |
| `extract-chat` | `<fichier.jsonl> [-o sortie] [--last N]` |

**Durcissement du 2026-07-22** (après le 1er test grandeur nature — voir
[`note_test_delegation_20260722.md`](note_test_delegation_20260722.md)) : les
deux outils DeepSeek **refusent de tourner** si un fichier passé en `--paths` /
`--context` est introuvable, affichent le **volume envoyé et le coût réel**, et
**signalent toute troncature** (`write-deepseek` n'écrit alors rien). En plus,
`write-deepseek` n'**écrase** pas une cible sans `--force` et ne **crée** pas de
répertoire parent sans `--mkdir`. `extract-chat` **refuse en dur** tout chemin
résolu sous `~/.claude/` (§6.2 n'est plus seulement une consigne écrite).

| Outil | Rôle sur Symbiose |
|---|---|
| `ask-deepseek` | **Lecture / recherche multi-fichiers**, cartographie de renvois. C'est l'outil principal. |
| `write-deepseek` | Écriture de **doc** (journal, fragments de backlog, de dette) et **boilerplate** (docstrings, scaffolding d'outil). Conception et commentaires de code : **seulement après validation de Nico**. |
| `extract-chat` | Logs **produits par le jeu** uniquement — voir §6, l'outil est de fait inutilisé ici. |

---

## 3. La règle de partage : par **nature de tâche**, pas par skill

Arbitrage de Nico (2026-07-22) : on ne dit pas « DeepSeek autorisé dans tel
skill, interdit dans tel autre ». On regarde **ce que la tâche demande**.

### ✅ Repérage factuel → `ask-deepseek`

Question à réponse **vérifiable**, dont le coût est de *parcourir* beaucoup de
fichiers :

- **inventaire d'ouverture** : « quels docs et quels sprints touchent déjà ce
  sujet ? »
- **anti-doublon** : « ce gène / ce champ / cet effet existe-t-il déjà ? »
  Garde-fou réel : l'incident `resilience_base` du sprint santé était
  exactement un doublon non détecté.
- **cartographie de couplages** : « quels modules lisent le champ
  `humidite` ? »
- **voix narratives** : « l'espèce Y a-t-elle ses 5 entrées ? » (règle projet
  « toute plante ajoutée = toutes ses voix », très coûteuse à vérifier à la
  main).

### ❌ Jugement → Claude lit le texte brut

- les **2-3 documents qui font l'objet** du travail en cours ;
- toute question de **jugement écologique** ou de **philo de design #1-#7** —
  DeepSeek ne connaît ni la philo ni le moteur, il répondrait du plausible
  invérifiable ;
- « quel **trou** vois-tu dans cette mécanique ? » — un trou de conception se
  voit dans l'interstice entre deux phrases, pas dans un résumé de 400 tokens ;
- les tours d'**audit pré-fix**, et `/audit-projet` dans sa **phase de
  verdict**.

### Les deux garde-fous

**(a) Pipeline en deux temps.** DeepSeek *localise* (fichier + section),
Claude *lit* le passage trouvé. On délègue la fouille, jamais la lecture de
fond.

**(b) Revérification de tout ce qui se grave.** Une information issue
d'`ask-deepseek` qui va **influencer une décision inscrite dans un kickoff, un
`00_etat.md`, `DETTE.md` ou `BACKLOG.md`** est revérifiée par `grep` ou par
lecture ciblée. Motif : une réponse DeepSeek n'est ni reproductible ni
traçable, et le projet est **déterministe par principe** (règle de design #3).

---

## 4. Cas `/conception` — gain maximal

C'est là que la délégation rapporte le plus : le corpus est large et on ignore
*où* le sujet vit. L'inventaire d'ouverture, l'anti-doublon et la carte des
couplages passent par `ask-deepseek`. Les documents que la conception va
**durcir**, eux, sont lus en clair par Claude.

## 5. Cas `/sprint-auto` — bien plus restrictif

Raison structurelle : `/conception` **cherche** (corpus large, cible inconnue)
tandis que `/sprint-auto` **modifie** (fichiers déjà désignés par le kickoff —
et pour éditer il faut le **texte exact**, un résumé est inutilisable pour un
`Edit`).

**✅ Autorisé** : cartographie d'**impact imprévue** (« qui d'autre lit ce
champ ? », effet de bord découvert en cours de tronçon) ; vérification de
correspondance **Python ↔ C#** au tronçon « vue Godot ».

**❌ Interdit** :

- lire le code que le tronçon va **modifier** ;
- **générer du code moteur via `write-deepseek`** — `data/code/` est la source
  de vérité écologique et le golden est un **hash** : du code non relu ligne à
  ligne mais tenu de préserver un hash exact, c'est le scénario qui casse le
  golden, pour zéro gain de contexte ;
- **diagnostiquer** un golden qui a bougé ou un test rouge — c'est du jugement.

**Capteur** : un sous-agent qui *a besoin* de fouiller révèle un **kickoff
incomplet**, au même titre qu'un fichier trop gros révèle une dette de
refactor. On le **consigne dans `00_etat.md`** au lieu de l'absorber en
silence.

**Plafond budget** : les appels sont réservés à l'**orchestrateur**. Les
sous-agents n'y recourent que pour la cartographie d'impact, jamais en routine
d'ouverture — l'orchestrateur ne voit pas leur consommation et la clé est
plafonnée.

---

## 6. Interdictions particulières

### 6.1 Les tests moteur ne sont **pas** du boilerplate

`tests/test_golden.py` et les 11 suites ciblées sont du **code de vérité
écologique** : ils encodent le déterminisme (règle de design #3). Ils restent
**écrits par Claude**, ligne à ligne. `write-deepseek` ne génère que des tests
**périphériques** (outils, parsing, scripts d'analyse hors `data/code/`).

### 6.2 `extract-chat` ne vise **jamais** `~/.claude/projects/`

Les transcripts de session peuvent contenir des secrets — c'est arrivé le
2026-07-22. `extract-chat` est réservé aux logs **produits par le jeu**.

> Conséquence pratique, à connaître : l'outil ne sait lire qu'un **transcript
> Claude Code `.jsonl`**, c'est-à-dire précisément la source interdite. Le jeu
> ne produit rien dans ce format aujourd'hui → **`extract-chat` est de fait
> inutilisé sur Symbiose**. S'il devait servir un jour, ce serait sur un log de
> jeu converti, jamais sur un fichier de `~/.claude/`.

### 6.3 Français forcé

Rien ne garantit que le modèle réponde en français. Toute `--question` et toute
`--spec` **exigent explicitement** : « en français, accents et diacritiques
corrects ». Les noms de fichiers restent en `snake_case` **sans** accents
(convention `docs/ARBORESCENCE.md`).

---

## 7. Syntaxe et exemples (chemins post-rangement)

Toujours sourcer la clé d'abord.

**Inventaire d'ouverture de conception** :

```bash
. ~/.config/deepseek.env
ask-deepseek --paths $(find docs -name 'conception_*.md') \
  --question "En français, accents corrects : quels documents parlent déjà de \
ruissellement de surface ? Donne fichier + titre de section, sans interpréter."
```

**Anti-doublon avant d'ajouter un gène** :

```bash
ask-deepseek --paths $(find data/code/plants -name '*.py') \
  --question "En français : existe-t-il déjà un gène qui module la tolérance à \
la sécheresse ? Cite le nom exact et le fichier, ne propose rien."
```

**Cartographie de couplage (impact imprévu, `/sprint-auto`)** :

```bash
ask-deepseek --paths $(grep -rIl 'humidite' data/code --include='*.py') \
  --question "En français : quels modules LISENT humidite, et lesquels \
l'ÉCRIVENT ? Liste fichier + fonction, rien d'autre."
```

**Mise à jour d'un fragment de doc** :

```bash
write-deepseek --lang markdown \
  --spec "En français, accents et diacritiques corrects. Ajoute au tableau une \
ligne pour <sujet>, même format que les lignes existantes, sans rien réécrire." \
  --context docs/champs/eau/dette_eau.md \
  --target  docs/champs/eau/dette_eau.md
```

**Après chaque appel `ask-deepseek`** : ouvrir le fichier cité et **lire le
passage**. La réponse seule ne fonde aucune décision (§3, garde-fou b).

### 7.1 Les deux modes de défaillance observés (2026-07-22)

**(a) `ask-deepseek` n'est pas exhaustif sur un gros corpus.** Sur 36 fichiers /
8 247 lignes, ses citations étaient **exactes au mot près** — il lit vraiment, il
ne brode pas — mais il a produit un **doublon**, **manqué les deux seules entrées
qui comptaient**, et conclu « aucun autre » sans réserve. Son mode de défaillance
est le **rappel partiel présenté comme complet**.

> Conséquence pratique : ne jamais lui confier un « liste TOUT ce qui… » sur un
> large corpus. Faire le **balayage** soi-même (`grep -l`, `grep -c` sur un
> marqueur) et ne déléguer que la **lecture des candidats**. Une question du type
> « voici 5 fichiers, dis-moi X pour chacun » lui réussit ; « trouve tous les X
> parmi 36 fichiers » non. Le prompt système exige désormais l'aveu d'incertitude,
> ce qui **atténue** le défaut sans le supprimer.

**(b) `write-deepseek` privé de contexte fabriquait tout.** Un `--target`/`--context`
mal expansé (variable de shell échappée) → aucun fichier de référence lisible →
il a produit une note d'apparence sérieuse, **entièrement inventée** (un cycle de
dépendances entre trois dettes qui n'existe nulle part), sans un mot
d'avertissement, et a créé au passage un répertoire parasite dans le dépôt.
**Corrigé dans l'outil** : c'est maintenant une erreur fatale, avant tout appel
API. La leçon qui reste : **toujours vérifier ses chemins** (`ls`) et **relire le
fichier produit en entier** — l'aperçu de 30 lignes affiché ne remplace pas la
relecture (règle « zéro perte », §8.4).

### 7.2 Rangement des notes produites

Toute note de synthèse issue de `write-deepseek` qu'on décide de garder est
**rangée dans l'arborescence** (`docs/<type>/<theme>/`) avec un **en-tête de
provenance** : outil utilisé, sources, et mention que Claude l'a revérifiée.
Une note d'agent non tracée est indiscernable d'un document écrit à la main.

---

## 8. Workflow de mise à jour de la doc après session

Sans `extract-chat` (cf. §6.2) :

1. **Claude** rédige la synthèse de la session et identifie **le thème**
   (les 8 types × thèmes de `docs/ARBORESCENCE.md`).
2. `write-deepseek --spec "<synthèse>" --context <fragment> --target <fragment>`
   sur le fragment du thème.
3. Répercussion sur `backlog_<theme>.md` et `dette_<theme>.md` du **même**
   thème ; `journal/`, `DETTE.md` et `BACKLOG.md` restent canoniques.
4. **Relecture par Claude** du diff produit — `write-deepseek` écrit le fichier
   entier, une génération non relue peut en perdre une partie (règle « zéro
   perte »).

---

## 9. Aide-mémoire

| Question posée | Qui répond |
|---|---|
| « Où vit ce sujet dans les 56 docs ? » | `ask-deepseek` |
| « Ce gène / champ / effet existe-t-il déjà ? » | `ask-deepseek`, puis `grep` de confirmation |
| « Qui lit ce champ ? » | `ask-deepseek` |
| « Ce qui est écrit là est-il juste écologiquement ? » | **Claude** |
| « Quel trou reste-t-il dans cette mécanique ? » | **Claude** |
| « Pourquoi le golden a-t-il bougé ? » | **Claude** |
| « Écris ce patch dans `data/code/` » | **Claude** |
| « Ajoute cette ligne au fragment de backlog » | `write-deepseek`, diff relu |
