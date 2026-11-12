# ③ Pressentis, familles, routes manquantes au pont

**Lire avant** : `CLAUDE.md`, `00_etat.md`, le doc de conception §3.4, §3.5.
**Nature** : Python + pont. **Golden : INTACT**. **Pont : bump** (`ENGINE_VERSION`
dans `tools/simserver/version.py`, aujourd'hui `0.6.11`, avec son paragraphe
d'historique comme les précédents).

## Objectif
Exposer à la vue ce qu'il lui faut pour la future palette : gestes pressentis avec
leur phrase, famille de chaque geste ; et router les gestes que le pont ignore.

## État du code (vérifié le 2026-11-12)
- Snapshot : bloc `player` construit dans `tools/simserver/serialize.py` (vers la
  ligne 738-765) : `gestes_debloques`, `debloques_recents`, `palette`…
- Dispatch des verbes : `tools/simserver/actions.py::_do_action`. `poser_perchoir`
  y est routé (cible `{tile, x_cm, y_cm}` locale, patron `planter`), avec la note
  « poser_tuteur/treillis/pergola n'ont pas encore de route : même branche ».
- Façades : `sim/actions/supports.py` — `poser_tuteur/treillis/pergola(gs, player,
  tile, x_cm, y_cm)` → `Support | None` ; `palisser(gs, player, plant, tile)` →
  bool. `sim/actions/couvertures.py` — `poser_voile/cloche/ombriere(gs, player,
  eco, r, c)` → bool. Ruche : déjà routée (`structures_route.py`).
- Les supports posés et les couvertures sont déjà sérialisés au snapshot.
- Fiches des gestes : `sim/geste_corpus.py` (`FICHES_GESTE`, module pur).
- Suite du pont : `tests/test_sim_server.py` (+ `tests/simserver/`).

## À faire
1. **`FAMILLE_GESTE`** (verbe → famille) et `FAMILLES` (ordre d'affichage), §3.5 du
   doc, dans un module pur de `sim/actions/` (ou à côté de `geste_corpus.py`).
   Test : tout verbe de `COUTS` a exactement une famille connue.
2. **`gestes_pressentis(game_state, player)`** — lecture PURE, calculée, jamais
   stockée, triée. Un geste fermé est pressenti si sa technique (1er élément
   « technique » d'`OBJETS_TOUCHES`, ou table explicite geste → technique si
   l'ordre des tuples n'est pas fiable : le vérifier) est découverte, ou si un
   indice de `INDICES_TECHNIQUE` (même grammaire que les portes) est vrai.
   Indices de départ :
   - compostage : `("compte", "glaner", 1)` ;
   - paillage : `("compte", "glaner", 1)` ;
   - broyage : `("maitrise", "taille", 1)` ;
   - jardinage_hors_sol, palissage, greffe, protection-climatique : une lettre
     ACTIVE de cette technique (reçue, pas encore comblée) ; pour greffe aussi
     `bouturer` ouvert ; pour palissage aussi une espèce grimpante découverte ;
   - apiculture : `("maitrise", "pollinisation", 1)` ;
   - perchoir : `("action", "poser_tuteur")` ou le merle découvert.
   La forme « lettre active » demande une condition neuve ou un marqueur
   d'événement posé à l'ouverture de la lettre : choisir le plus simple au vu de
   `sim/quetes.py`, sans faire importer `sim.quetes` par `deblocage`.
3. **`PHRASE_PRESSENTI`** : une phrase par technique gatante, voix intérieure à la
   première personne, français accentué, **aucune consigne ni lieu** (« Ces feuilles
   que je ramasse, il doit bien y avoir mieux à en faire qu'un tas. »). Test : toute
   technique citée par `PORTES_TECHNIQUE` a sa phrase.
4. **Snapshot `player`** : ajouter `gestes_pressentis` = liste de
   `{verbe, phrase}` et `familles` = `{ordre: [...], de: {verbe: famille}}` (ou forme
   équivalente compacte ; `familles` est statique : l'envoyer une fois à l'init si le
   protocole le permet, sinon à chaque snapshot, c'est quelques centaines d'octets).
5. **Routes** dans le pont :
   - `poser_tuteur`, `poser_treillis`, `poser_pergola` : même branche que
     `poser_perchoir` ;
   - `palisser` : plante désignée par position continue comme les gestes plante
     (`_plant_at`) ;
   - `poser_voile`, `poser_cloche`, `poser_ombriere` : plot `{tile, r, c}`, patron
     `glaner`/`creuser` ;
   chacune avec refus sans coût hors tuile, coût via `A.cout_action`, message
   diagnostic. `actions.py` est long : mettre ces routes dans un module de route
   dédié (`supports_route.py`, sur le modèle de `structures_route.py`) et y déplacer
   `poser_perchoir` si cela simplifie.
   Vérifier que chaque geste routé est bien refusé quand il n'est pas débloqué (lire
   comment le pont applique `est_debloque` aujourd'hui et suivre le même chemin).
6. Tests du pont : un cas par route neuve ; présence et forme des deux blocs neufs.

## Vérification
`python3 -m tests.test_golden` inchangé ; `tests.test_sim_server` et suites
voisines vertes ; `tools/compte_ldc.py` sur les fichiers touchés.

## À ne pas faire
- Aucune phrase qui dise où aller ou quoi acheter.
- Ne pas stocker les pressentis dans la save.
- Ne pas toucher à la vue C# (tronçon ④).
