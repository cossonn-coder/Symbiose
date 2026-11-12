# ① Portes des techniques + test d'atteignabilité

**Lire avant** : `CLAUDE.md`, `00_etat.md`, `docs/joueur/gestes/conception_refonte_palette.md` §1 et §3.
**Nature** : Python, état joueur hors tick. **Golden : INTACT** (`b4a921f8…`).

## Objectif
Donner à chaque technique une porte d'entrée qui ne passe pas par ses propres
gestes, et verrouiller le résultat par un test.

## État du code (vérifié le 2026-11-12)
- `sim/actions/deblocage.py` : `GESTES_BASE`, `GESTE_UNLOCK` (verbe → conditions en
  OU), `_cond_remplie` (formes `maitrise`, `action`, `evenement`, `et`),
  `marquer_action` (set `game_state["actions_faites"][player]`),
  `marquer_evenement` (set `game_state["marqueurs_ecolo"][player]`),
  `evaluer_deblocages` (ouvre les verbes, renvoie les nouveaux, triés). Le module
  n'importe que `sim.maitrise` (as `M`).
- Une technique passe au palier 1 seulement par `decouvrir_a_usage`
  (`tools/simserver/maitrise_pont.py`) : au 1er usage réussi d'un geste qui la
  touche (`OBJETS_TOUCHES`, `sim/actions/couts.py`). D'où l'impasse.
- `M.decouvrir(game_state, player, objet)` (pur) fait 0 → 1.
- Le stock de mulch est `game_state["mulch_stock"]` (dict nature → quantité, global
  au profil). `paillage.mulch_stock()` CRÉE la clé à la lecture : ne pas l'appeler
  depuis une condition, lire `game_state.get("mulch_stock")` directement.
  `PAILLAGE_DOSE` vit dans `fields/ecofields.py`.
- Le pont marque et évalue dans `tools/simserver/actions.py` (bloc
  `if result.get("applied")`, vers la ligne 68-92) ; `sim/outils.py::acquerir_outil`
  et `tools/simserver/maitrise_pont.py` appellent aussi `evaluer_deblocages`.

## À faire
1. **Deux formes de condition** dans `_cond_remplie` :
   - `("stock", nature, seuil)` : vrai si le stock de cette nature ≥ `seuil`
     (lecture pure, sans créer de clé) ;
   - `("compte", verbe, n)` : vrai si le joueur a réussi `n` fois ce geste.
     État neuf `game_state["gestes_comptes"][player][verbe]` (opt-in, créé à la
     volée comme `actions_faites`), avec une fonction `compter_geste`. Le pont
     l'incrémente pour les seuls verbes cités par une condition `compte`
     (ensemble dérivé des tables, comme `DECLENCHEURS`).
2. **Table `PORTES_TECHNIQUE`** (technique → conditions en OU), §3.2 du doc :
   - `compostage` : `("compte", "glaner", 3)`, `("action", "poser_bac")`
   - `paillage` : `("stock", "feuilles", PAILLAGE_DOSE)`, `("stock", "paille", PAILLAGE_DOSE)`
   - `jardinage_hors_sol` : `("action", "posseder_pots")`
   - `palissage` : `("action", "posseder_tuteurs")`, `("evenement", "grimpante_sans_appui")`
   - `perchoir` : `("evenement", "merle_seme")`
   - `greffe` : `("et", [("evenement", "lettre_greffe"), ("action", "posseder_greffoir")])`
   - `apiculture` : `("maitrise", "pollinisation", 2)`, `("evenement", "lettre_essaim")`
   - `protection-climatique` : `("action", "posseder_voile")`
   Les marqueurs `posseder_*`, `lettre_*` et d'observation sont POSÉS au tronçon ② ;
   ici on ne fait que les lire (comme `bouture_spontanee` l'a été).
   Vérifier le nom exact de chaque technique dans `OBJETS_TOUCHES` avant de graver.
3. **`evaluer_deblocages`** : avant de parcourir `GESTE_UNLOCK`, découvrir toute
   technique de palier 0 dont une porte est remplie (`M.decouvrir`). Renvoi inchangé
   (liste des verbes neufs). Idempotent.
4. **Retouches de `GESTE_UNLOCK`** :
   - `broyer` : `[("action", "posseder_broyeur")]` (au lieu de `maitrise paillage`) ;
   - `poser_voile`/`poser_cloche`/`poser_ombriere` : ajouter l'alternative
     `("maitrise", "protection-climatique", 1)` à côté de `("maitrise", "météo", 1)` ;
   - le reste ne bouge pas.
5. **Test neuf `tests/test_atteignabilite.py`** : refaire le point fixe sur les
   tables réelles — départ `GESTES_BASE`, marqueurs de `OUTILS` (lus dans
   `sim/outils.py` ; au ① les outils neufs n'y sont pas encore, donc déclarer dans le
   test l'ensemble des marqueurs « promis par ② » et le resserrer au ②), concepts
   découverts par le tick (eau, lumière, météo, pollinisation), événements
   d'observation et de lettre tenus pour atteignables. Le test **échoue** si un verbe
   de `COUTS` n'est ni de base ni atteignable, et si une technique gatante n'a aucune
   porte. Ajouter des cas unitaires pour `stock` et `compte`.

## Vérification
- `python3 -m tests.test_golden` → hash inchangé.
- `python3 -m tests.test_deblocage`, `tests.test_atteignabilite`, `tests.test_palette`,
  `tests.test_acquisition_outils` verts (lancés depuis `data/code/`).

## À ne pas faire
- Ne pas supprimer ni renommer `GESTE_UNLOCK` / `GESTES_BASE` (lus par le pont, les
  tests, l'automate `tools/jardinier_auto/`).
- Ne rien écrire dans le tick ni dans `sim/engine/`.
- Ne pas importer `sim.actions.paillage` ni `sim.outils` depuis `deblocage.py`
  (`outils.py` importe déjà `deblocage` : ce serait un cycle).
- Taille : `deblocage.py` approche la bande ; si > 300 LDC (`tools/compte_ldc.py`),
  sortir les tables dans un module frère `sim/actions/deblocage_tables.py`
  ré-exporté.

## Fin de tronçon
Mettre à jour `00_etat.md` (ligne ①, constats), commit.
