# ⑥ Voix narratives — le saule, les gestes, les techniques, le bocage

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` + ①→⑤.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §7 +
> `docs/narration/voix/conception_voix_narratives.md`.
>
> **Golden attendu : INCHANGÉ.** Corpus narratifs et catalogue opt-in.

## Objectif

Donner leurs voix aux gestes, techniques et outils du sprint — et ajouter **une seule
espèce**, le saule, sans laquelle `eteter` reste une abstraction.

## A. Le saule (décision D-5)

Règle « le catalogue grandit avec les idées » — **application signalée**. Une espèce, pas
trois. Justification : le sprint invente `eteter`, il lui faut son incarnation ; le
**saule têtard** est l'archétype de la trogne et l'essence normande du bocage ; et il
**se bouture spontanément**, ce qui croise l'événement rare « bouture » et le canal
d'acquisition #2 **déjà en place**.

Noisetier et prunellier/ronce sont **écartés** (portés par le charme et le bouleau côté
agrégat) → au BACKLOG.

`data/code/plants/species.py` + `catalogue.py`, sur le patron des ligneux existants
(`hetre` → `BeechTree`, `charme` → `HornbeamTree`, `aulne` → `Alder`) : Salicaceae,
croissance rapide, port souple, affinité hydrique forte (ripisylve), **rejette de
souche** — il doit figurer dans `ESSENCES_QUI_REJETTENT` du ④.

**Règle « toute plante ajoutée = toutes ses voix »** — les 5 dispositifs, sans exception :

| Voix | Fichier | Contenu |
|---|---|---|
| Encyclopédie | `sim/encyclopedie_corpus.py` | fiche 3 niveaux (vue / cycle complet / effets écosystémiques) |
| Carnet | `sim/concept_corpus.py` (`CONCEPT_DE`) | concepts que le saule illustre : `rejet_de_souche`, bord d'eau |
| Pages secrètes | `sim/pages_corpus.py` | la chouette dans le saule creux |
| Magazine | `sim/magazine.py` | rattachement famille / offre |
| Événements | ledger | marqueurs de cycle de vie |

## B. Gestes, techniques, outils

- **Gestes** (`sim/geste_corpus.py`) : `abattre` · `receper` · `eteter` · `endiguer` ·
  `deriver` · `entailler`. Trois niveaux — 1 descriptif, 3 énonce la **conséquence**
  (vent, lumière, érosion) une fois la maîtrise acquise. C'est le dispositif qui préserve
  la méthode scientifique (#6) : on décrit avant de comprendre.
- **Technique `taillis`** (`sim/technique_corpus.py`) : « couper pour que ça repousse plus
  fort. La souche a de la mémoire ; l'arbre étêté vit plus vieux que l'arbre libre. »
  Ajouter aussi `trogne` et `essartage`.
- **Outils** (`sim/outil_corpus.py`) : hache, serpe, pioche — patron du sécateur et du bac.
- **Concepts carnet** (`CONCEPT_DE`) : `lisiere`, `brise_vent`, `erosion`,
  `rejet_de_souche`.

## C. Pages secrètes — le gisement

`sim/pages_corpus.py`. C'est le sujet le plus riche en lore de tout le projet ; le
registre est celui des voix multiples (extraits poétiques, savoirs paysans, herbiers) —
**jamais un narrateur omniscient**, jamais un PNJ.

- **Le bocage et le remembrement** — le maillage de haies n'était pas un décor mais une
  **infrastructure agricole** : brise-vent, bois de chauffe, fourrage, drainage, limite
  de propriété. Le XXᵉ siècle l'a arasé ; l'érosion et le vent ont suivi. C'est
  exactement la leçon que le sprint fait vivre sans un mot de tutoriel.
- **L'essartage** — défricher pour cultiver, l'autre réponse de la même culture paysanne.
- **La trogne** — « l'arbre que l'on coupe pour qu'il dure ».
- **Le meunier et le droit d'eau** — qui possède une rivière ? (résonne avec `endiguer`)
- **La chouette dans le saule creux** — le tronc qui se creuse devient un habitat.

## D. Événements au ledger

Marqueurs (`sim/evenements.py`) : 1ʳᵉ clairière ouverte · 1ᵉʳ rejet de souche · rupture
de barrage · 1ᵉʳ éboulis.

## E. Quêtes (D79) — rien à coder

« Ouvrir une clairière », « rendre la mare aux libellules » sont des objectifs à
condition d'état **déjà supportés** par `sim/quetes.py`. Ajoute au plus des lettres au
corpus (`sim/quetes_corpus.py`) si la voix épistolaire s'y prête. **Ne touche pas le
moteur de quêtes.**

## Tests

1. **Complétude des voix** — le saule a bien ses 5 entrées (un test qui parcourt les
   registres ; s'il en existe déjà un pour les autres espèces, étends-le).
2. **Gestes** — chaque geste du ④/⑤ a ses 3 niveaux d'encyclopédie.
3. **Neutralité** — corpus non chargés sans joueur ⇒ golden intact.
4. Suites existantes du catalogue et des voix : **vertes**.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ**. Le saule n'est semé nulle part dans
`build_world()` ; ajouter une espèce au catalogue ne change aucun digest.

⚠️ Si le digest bouge, c'est que le saule a été semé quelque part par inadvertance, ou
qu'un registre est parcouru dans le tick. **Annuler, ne pas figer.**

## Ce qu'il NE faut PAS faire

- **N'ajoute pas noisetier / prunellier / ronce** : écartés, au BACKLOG.
- **Pas de narrateur externe omniscient, pas de PNJ** — voix diégétiques uniquement.
- **Ne révèle pas au niveau 1** ce que le niveau 3 doit apprendre (#6) : le fait que le
  hêtre ne rejette pas est une **découverte**, pas une consigne.
- **Ne touche pas le moteur de quêtes** (D79 est clos).
- **N'exécute JAMAIS** `test_epaisseur_500ans`.
