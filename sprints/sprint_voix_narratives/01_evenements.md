# ① Extraire `sim/evenements.py` (refactor PUR) + élargir le parseur

> Lire d'abord `00_etat.md` + `docs/narration/voix/conception_voix_narratives.md` (§1,
> surtout §1.2). Tronçon **fondation** : on isole le parsing du `log` du tick dans un
> module commun pur, et on l'élargit aux *kinds* dont le carnet aura besoin. **Aucun
> conscommateur neuf branché ici** (ni journal, ni driver). Premier geste : RE-MESURER
> les hashs golden + lancer `test_maitrise_detection` pour partir d'une base sûre.

## Objectif
Extraire `_evenements()` (+ ses regex/helpers) de `sim/maitrise_detection.py` vers un
**nouveau module pur `sim/evenements.py`**, faire ré-importer `maitrise_detection`
depuis ce module (preuve du refactor pur = `test_maitrise_detection` reste VERT), puis
**élargir** le parseur pour couvrir les marqueurs réels du moteur que le carnet doit
consigner. Définir le type partagé `Evenement` (doc §1.2).

## À faire

### A. Créer `sim/evenements.py` et y déplacer le parsing
- Déplacer depuis `sim/maitrise_detection.py` : `_evenements()` + toutes les regex
  (`_POS`, `_RE_TILE`, `_RE_AVANCE`…) + `_raison_stagnation` (et tout helper privé que
  `_evenements` utilise). Garder les noms.
- Dans `sim/maitrise_detection.py` : **supprimer** les définitions déplacées et les
  **ré-importer** depuis `sim.evenements` (`from sim.evenements import evenements, …`).
  But : `maitrise_detection.detecter()` continue de marcher à l'identique.
- `sim/evenements.py` est **pur** (aucun import de couche haute ; ne lit que le `log`
  texte qu'on lui passe). Couches : niveau `sim`, comme `maitrise_detection`.

### B. Type partagé `Evenement` (doc §1.2)
- `Evenement = namedtuple("Evenement", "kind tile_id pos espece cause")`.
- `pos` = tuple `(r, c)` plot-foyer si dispo, sinon `None` ; `tile_id` = id de tuile si
  le marqueur le porte (`[tile]`), sinon `None` ; `espece` = clé catalogue ; `cause` =
  sous-type (string) ou `None`.
- Exposer une fonction publique `evenements(log) -> list[Evenement]` (le nom que
  `maitrise_detection` réimporte).

### C. Élargir le parseur aux *kinds* du carnet — SEULEMENT ce qui existe dans le log
MARQUEURS RÉELS du moteur (déjà grepés). Format des lignes : `🟦 Nom@(r,c) …` ou `[tile]`.
- `🌱 {name}@pos → [STAGE]` = germination/levée (déjà : « avance »).
- `⏸ sec` / `❄ froid` / `🌑 ombre` / `🌊 noyé` = stagnation, `cause` ∈ {sec,froid,ombre,noyé} (déjà).
- `🌰 Reproduction : {cls} @best` = reproduction (`cause` auto/biparental/introgression).
- `🪦 {name}@pos meurt de/…` = mort ; `cause` lue dans le texte (sénescence/asphyxie/gel…).
- `✗ {name}@pos meurt (conflit)` = mort, `cause="conflit"`.
- `🍂 Abscission {name}@pos` = abscission. **⚠ `🍂` sert AUSSI** à « Nécromasse » et
  « Chute fruit » → **disambiguer sur le mot juste après l'emoji**.
- `🍎 Nouaison {name}@pos` = nouaison. **⚠ `🍎` sert aussi** au header « Récolte : » →
  **disambiguer sur « Nouaison »**.
- `🐛 {ravageur} : {desc}` = ravageur.
- `🌸 Floraison :` = **HEADER de section, PAS per-plante** → vérifier s'il existe des
  lignes per-plante en dessous ; sinon **laisser floraison en TODO nommé** (ne pas
  inventer un parsing sans source).
- `acclimatation` : chercher si un marqueur existe (signe diégétique du sprint
  plasticité ⑤). Si présent → kind `acclimatation` ; sinon **TODO nommé**.
- **Règle d'or** : parser SEULEMENT ce qui est présent dans le log réel. Pour tout
  kind sans marqueur, laisser un `# TODO(voix): kind X — pas de marqueur source` au
  lieu de fabriquer.

## Couches
`sim/evenements.py` est au niveau `sim`, **au-dessus du tick** comme `maitrise_detection`.
`engine`/`fields`/`plants` ne l'importent jamais. Aucun RNG, aucun effet de bord.

## Définition de done
- `sim/evenements.py` créé (parsing + `Evenement` + `evenements()`), `maitrise_detection`
  ré-importe et **`tests/test_maitrise_detection.py` reste VERT** (preuve refactor pur).
- `tests/test_evenements.py` (NOUVEAU) : logs jouets → bons `Evenement` (kind/cause/pos)
  pour chaque marqueur géré ; disambiguation `🍂`/`🍎` testée ; parité avec l'ancien
  comportement sur les kinds déjà parsés ; déterminisme.
- **Golden INTACT** : `tests/test_golden.py` + `tests/population_hash.txt` bit-identiques
  (ce tronçon ne touche pas le tick). Si ça bouge → BUG, STOP, analyser (ne pas re-figer).
- MAJ `00_etat.md` (① → FAIT + acquis) puis commit.

## Pièges
- C'est un **refactor pur + extension** : ne change PAS la logique des kinds existants,
  déplace-les tels quels. Le test maîtrise vert le prouve.
- **Ne fabrique aucun parsing** : pas de marqueur réel = TODO nommé, point.
- `🍂` et `🍎` sont **polysémiques** → toujours disambiguer sur le mot qui suit.
- Aucun consommateur ici (journal = ②). Ce module ne fait que **lire et typer** le log.
