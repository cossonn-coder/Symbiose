# ⑤ Interconnexions vivantes + voix narratives + pont snapshot

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_METEO_CHAMPS.md` (§6).
> Dépend de ② (rosée/givre à relier et exposer). Dernier tronçon. Premier geste :
> RE-MESURER les hashs golden.

## Objectif
Relier la rosée aux acteurs vivants (règle « tout coexiste »), lui donner ses **voix
narratives**, et exposer la **carte de condensation** au snapshot pour le rendu Godot.
La part voix/pont est read-only (golden NEUTRE) ; les parts faune/captation touchent le
tick (golden léger, annoncé).

## À faire

### A. Faune abreuvée par la rosée (`fields/population.py`)
- Les semaines à forte rosée, la faune du matin (escargots/limaces/détritivores) gagne
  en activité/survie (l'eau de surface est leur abreuvoir). Terme **sobre**, branché sur
  la dynamique de population existante — **pas de nouvelle guilde**.
- Lire la condensation/humidité de surface du tick. Effet borné, déterministe.

### B. Captation foliaire (`PlantInstance` / uptake)
- Une canopée intercepte la rosée → réduction du **stress hydrique** de la plante.
  Modèle sobre : réduire la mémoire de sécheresse (`drought_memory`) ou compléter
  légèrement l'uptake d'eau les matins de rosée, ∝ surface foliaire/canopée.
- Garder l'effet marginal mais réel (cohérent avec le poids « significatif » de la rosée
  sur le sol, §3.6 du doc).

### C. Voix narratives (modules de données existants, read-only)
- **Encyclopédie** : concept « rosée / micro-cycle de l'eau » + « gelée blanche » →
  entrées dans `sim/encyclopedie_corpus.py` (3 niveaux si applicable, ou concept transversal).
- **Carnet** : `sim/carnet.py::CONCEPT_DE[(kind, cause)]` + gabarits descriptif/
  interprétatif pour les marqueurs `rosée`/`gelée blanche` émis au log (②, parsés par
  `sim/evenements.py`). Bascule interprétatif au seuil météo (D12).
- **Pages secrètes** : 1-2 pages lore (rosée de la Saint-Jean, herbiers anciens) dans
  `sim/pages_corpus.py`. ZÉRO effet mécanique.
- Recopier les corpus éditoriaux (ne pas réinventer le texte) ; cohérent avec le sprint
  voix narratives (`sprints/_clos/` ou `sprint_voix_narratives/`).

### D. Pont snapshot (`tools/simserver/serialize.py`)
- Exposer la **carte de condensation** (rosée/givre par plot) dans le snapshot pour le
  rendu C# (gouttes scintillantes / givre blanc). Read-only, déterministe.
- Bump de version de protocole du pont (suivre la convention `version.py`).

## Couches
A/B touchent `fields`/`plants` (tick). C est niveau `sim` (lecteurs read-only au-dessus
du tick, comme le sprint voix narratives). D est côté `tools/simserver` (driver/pont).

## Définition de done
- Faune abreuvée + captation foliaire branchées (effets sobres, bornés, déterministes).
- Entrées encyclopédie/carnet/pages pour rosée + gelée blanche (corpus recopiés).
- Carte de condensation exposée au snapshot + version protocole bumpée.
- `tests/` : test faune-rosée + test captation (effet présent et borné) ; tests voix
  (entrées présentes, lecteurs read-only no-op golden) ; sérialisation snapshot OK.
- **Golden** : NEUTRE pour C/D (read-only) ; **léger** pour A/B (annoncé) — vérifier que
  la dérive est localisée, recapturer si besoin, **noter dans `00_etat.md`**.
- MAJ `00_etat.md` (⑤ → FAIT + **clôture du sprint** : récap, hashs finaux, dette restante)
  puis commit.

## Pièges
- A/B sont les SEULES parts qui touchent le tick ici → si le golden bouge plus que prévu,
  c'est A ou B (C/D doivent être strictement read-only / hors tick).
- Voix : suivre le patron du sprint voix narratives (opt-in joueur, no-op sans joueur).
- Pont : ne pas casser le protocole existant (snapshot rétrocompatible, champ additif).
- **Rendu C# des gouttes/givre = hors périmètre** (dette D24) : ⑤ expose la donnée, Godot
  l'affichera plus tard. Le F5 visuel reste à Nico.
