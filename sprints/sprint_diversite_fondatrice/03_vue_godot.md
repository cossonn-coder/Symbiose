# Tronçon ③ — Vue Godot : voir les rythmes propres + la catena

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Doc complet :
> `docs/conception/CONCEPTION_DIVERSITE_FONDATRICE.md`. Ce tronçon vient APRÈS ①
> (génétique fondatrice) et ② (catena) : le moteur produit désormais des plantes à
> patrimoine propre et des champs de sol hétérogènes structurés par l'altitude. Ici
> on les REND OBSERVABLES et on re-vérifie l'équilibre de population.

## Objectif
Un **banc F5** qui laisse Nico VOIR de ses yeux les deux acquis du sprint :
1. **Rythmes désynchronisés** — un lot de la même espèce côte à côte lève / grandit
   / fleurit à des vitesses différentes (génétique fondatrice + plasticité au sol).
2. **Mosaïque édaphique** — les heatmaps `FieldOverlay` (F6) montrent le gradient
   catena (NPK/microbiome riches en bas de pente, pauvres en haut ; pH ~homogène).
3. **Survol gènes** — pointer une plante affiche son vecteur de gènes (debug), pour
   corréler « cette plante-ci est en avance » ↔ « ses gènes de rythme ».

Plus un **garde-fou** : re-passer `diag_population` (le sprint « équilibre invasion »
a calibré des plateaux ; la variance fondatrice peut re-déséquilibrer).

## Contexte moteur / vue (déjà en place)
- **Bancs d'essai** (`data/code/bancs/`) : un banc = fabrique `() -> (tiles, ecos,
  house, banque)` qui compose un monde paramétré (aucune mécanique neuve → golden
  NEUTRE, jamais monté pour smoke/full). Registre `bancs/__init__.py:BANCS` ;
  semaine de départ `BANC_WEEK_DEPART` (défaut 1). Brique `bancs/base.py:
  build_banc_tile(name, soil, rows, cols, ox, oy, *, humidite, fertilite,
  microbiome, **champs)` → `(tile, eco)` ; `monde(tiles, ecos, house, banque)`.
  **IMPORTANT** : `build_banc_tile` appelle `init_eco` SANS `heterogene`. Pour ce
  banc il faut l'hétérogénéité → soit passer `heterogene=True` (voir §a), soit
  appeler `init_eco(..., heterogene=True)` directement.
- **`FieldOverlay.cs`** (`visuals/`) : heatmaps debug des champs éco, toggle **F6**.
  Vérifier quels champs sont déjà exposés (n/p/k/microbiome/ph/altitude) et ajouter
  ceux qui manquent pour lire la catena. Les valeurs arrivent par le snapshot du
  pont (`sim_server.py` → `SimBridge`).
- **`PlantRenderer.cs`** : rend les branches ; le rythme (taille/stade/floraison) est
  DÉJÀ rendu — pas de nouveau rendu à écrire, le banc suffit à l'exposer.
- **Survol** : chercher le picking souris existant dans `WorldView` (partial actions
  / caméra). Le snapshot par plante doit exposer `genes` (dict) — VÉRIFIER que
  `sim_server.py` sérialise bien `p.genes` dans le snapshot plante ; l'ajouter si
  absent (petit champ, pas de re-figeage golden — le snapshot n'est pas le golden).
- **`diag_population`** (`data/code/tools/diag_population.py`) : outil d'observation
  des plateaux de population (invasion/équilibre). Se lance en CLI.

## Travail

### a) Banc `diversite_fondatrice` (nouveau, `data/code/bancs/`)
Ajouter une fabrique dans le fichier de banc le plus adapté (probablement un nouveau
`bancs/diversite.py` ou dans `biotique.py` si cohérent) + l'entrée dans
`BANCS`. Le banc :
- une (ou deux) tuile(s) montée(s) avec `heterogene=True` → sol catena + banque-sol
  ensemencée fondatrice ;
- un **lot dense de LA MÊME espèce** cultivée, semé côte à côte (via le helper
  `semer_fondateur` du ① s'il existe, sinon `add_plant` + `founder_genes`), pour que
  la désynchronisation soit LISIBLE ligne à ligne. Choisir une espèce à rythme
  expressif (tournesol/Sunflower : floraison spectaculaire ; ou Phacelia). Éviter la
  tomate (meurt tôt au froid de démarrage — cf. mémoire).
- départ éventuel à mi-printemps (`BANC_WEEK_DEPART`) si l'espèce est frileuse, pour
  voir la croissance tout de suite.
- **Ne force AUCUN champ à la main** (pas de `**champs` uniforme) : ici l'intérêt est
  justement l'hétérogénéité NATURELLE de la catena, pas une condition forcée.

### b) Heatmaps catena (`FieldOverlay.cs`)
S'assurer que F6 permet d'afficher au moins `n`/`p`/`k` (ou un agrégat NPK),
`microbiome` et `altitude` → on doit LIRE le gradient (bas de pente plus foncé/riche).
Si un canal manque dans l'overlay, l'ajouter. Filet compilation : `dotnet build
Symbiose.csproj` (le F5 visuel reste à Nico).

### c) Survol gènes (debug)
Au survol d'une plante, afficher son vecteur de gènes (au moins les gènes de rythme :
`vigueur`, `germination_thermique`, `phenologie_florale`). Réutiliser le picking
existant. Format debug (texte simple, pas de HUD léché — philo #5 : c'est un outil
d'observation, étiqueté debug). Vérifier d'abord que le snapshot expose `genes`.

### d) Garde-fou `diag_population`
Re-lancer `diag_population` APRÈS ①②, comparer les plateaux aux valeurs connues du
sprint « équilibre invasion ». Consigner le résultat dans `00_etat.md` :
- si les plateaux tiennent → RAS, noter « diag_population OK, variance fondatrice
  n'a pas re-déséquilibré » ;
- si ça dérive (une espèce explose/s'effondre) → NE PAS re-calibrer ici ; CONSIGNER
  en dette (DETTE.md) + signaler à Nico. Ce tronçon observe, il ne re-calibre pas.

## Golden
**INTACT.** Un banc ne monte jamais pour smoke/full ; l'ajout d'un champ `genes` au
snapshot du pont ne touche pas le golden (le snapshot n'est pas figé par
`test_golden`). Si un changement fait bouger le golden → tu as touché un chemin
monté par smoke/full : ARRÊTE et reviens en arrière (ce tronçon ne re-fige rien).

## Tests
- Le banc doit se monter sans crash : `init config="diversite_fondatrice"` via le
  pont (ou un petit smoke local qui appelle la fabrique et fait tourner N semaines).
- `dotnet build Symbiose.csproj` vert (filet compilation C#).
- Pas de nouveau test golden. Les tests neufs du sprint sont au ①/②.

## NE PAS faire
- Ne pas re-calibrer les plateaux de population (seulement observer + consigner).
- Ne pas re-figer le golden (aucun re-figeage prévu ici).
- Ne pas monter le banc pour smoke/full (romprait le golden NEUTRE des bancs).
- Ne PAS lancer `test_epaisseur_500ans` (long, inutile — cf. mémoire).

## Fin de tronçon (et de sprint)
Banc monté et confirmé F5 par Nico, `diag_population` re-passé + consigné, golden
INTACT, `00_etat.md` finalisé (sprint clos), DETTE.md/BACKLOG.md/journal.md à jour,
commit. C'est le dernier tronçon : le sprint DIVERSITÉ FONDATRICE est terminé.
