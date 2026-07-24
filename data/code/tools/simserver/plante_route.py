"""
SYMBIOSE — tools/simserver/plante_route.py
Routage des gestes sur une PLANTE VIVANTE désignée par position continue
(x_cm/y_cm) — extrait du routeur `actions.py` pour le garder court (un fichier =
une responsabilité). Sept verbes, tous résolus sur la même plante-cible :

  - `manger` (organe/fruit ciblé, gain Vigueur ∝ maturité, D19),
  - `recolter` / `deraciner` (récolte, arrachage racinaire),
  - `couper` (geste BRUT au sécateur, ancêtre de `tailler`, D12),
  - `pincer` / `arracher` (gestes MANUELS de BASE, acquisition des moyens d'agir ① :
    `pincer` DOUX auxine↓, `arracher` NET à la main + `erode()` vitalité),
  - `tailler` (coupe nette au segment près, tranche 5).

Validation des désignations ICI (refus → ne coûte rien) ; les façades `sim/actions`
font foi (validité, coût maîtrise × urgence, effet, plafonds). `plant_at` est le
résolveur de plante VIVANTE par position (le `CiblesMixin._plant_at` du serveur),
passé par l'appelant. `bilan(applied, cost, gain, message)` → dict est la fabrique
de réponse JSON commune à tous les gestes.
"""
from __future__ import annotations

from sim import actions as A      # façades des 7 gestes sur plante (foi métier)
from sim import quetes as Q       # hook de comptage des quêtes joueur (D79 ①)

VERBES = ("manger", "recolter", "deraciner", "tailler", "couper",
          "pincer", "arracher")


def route_plante(gs: dict, player: str, verb: str,
                 target: dict, params: dict, bilan, plant_at):
    """Aiguille un geste sur plante. Résout la tuile + la plante, délègue aux façades."""
    tiles = {t.tile_id: t for t in gs["tiles"]}
    tile = tiles.get(target.get("tile"))
    if tile is None:
        return bilan(False, 0.0, 0.0,
                     f"tuile introuvable : {target.get('tile')!r}")
    eco = gs["eco"][tile.tile_id]
    plant = plant_at(tile, target.get("x_cm"), target.get("y_cm"))
    if plant is None:
        return bilan(False, 0.0, 0.0,
                     "aucune plante vivante à cette position")
    # Hook QUÊTES (D79 ①) : on ENROBE `bilan` pour notifier le système de quêtes
    # APRÈS un geste RÉUSSI (applied truthy). Rebind LOCAL du nom → toutes les
    # branches ci-dessous appellent la version enrobée SANS changer une ligne (les
    # deux retours d'échec au-dessus ont déjà utilisé le `bilan` brut, avant que
    # `plant` existe). `notifier_geste` est un no-op strict tant qu'aucune quête
    # n'est active (opt-in) → golden intact. Le verbe transmis est le verbe JOUEUR
    # (ex. `couper`), même quand la façade retombe sur `tailler` en interne.
    _bilan_brut = bilan

    def bilan(applied, cost, gain, message):
        if applied:
            Q.notifier_geste(gs, player, verb, plant)
        return _bilan_brut(applied, cost, gain, message)
    # Coût nominal AVANT le geste (cout_action est une lecture pure —
    # le geste recalcule le même en interne) : pour l'affichage HUD.
    cost = A.cout_action(gs, player, verb, A._objets_action(verb, plant))
    if verb == "manger":
        # Fruit ciblé (③, D19) : index dans plant.fruits du snapshot.
        # Validé AVANT la façade — un index invalide ne mange rien (et,
        # côté actions, retombe sur le mode générique). NB : bool < int.
        fidx = target.get("fruit")
        if fidx is not None:
            if not isinstance(fidx, int) or isinstance(fidx, bool):
                return bilan(False, 0.0, 0.0,
                             f"fruit non entier : {fidx!r}")
            if not 0 <= fidx < len(plant.fruits):
                return bilan(False, 0.0, 0.0,
                             f"fruit hors structure : {fidx} "
                             f"(la plante porte {len(plant.fruits)} fruits)")
        g = A.manger(gs, player, plant, eco, fruit_index=fidx)
        # Gain nominal DANS le message (retour F5 Nico : « rien ne se
        # passe » = organe immature, gain ≈ 0 — qu'on le LISE).
        cible = f"fruit #{fidx}" if fidx is not None else plant.name
        return bilan(True, 0.0, g,
                     f"mangé : {cible} (+{g:.1f} Vigueur — "
                     f"gain ∝ maturité de l'organe)")
    if verb == "recolter":
        ratio = A.recolter(gs, player, plant, eco)
        msg = ("récolté : " + plant.name if ratio >= 1.0
               else f"récolte partielle ({ratio:.0%}) : {plant.name}")
        return bilan(ratio > 0.0, cost, 0.0, msg)
    if verb == "deraciner":
        ok = A.deraciner(gs, player, plant, eco)
        return bilan(ok, cost, 0.0,
                     "déraciné : " + plant.name if ok
                     else "Vigueur insuffisante — rien déraciné")
    # couper (geste BRUT, D12 — ancêtre de tailler) : coupe SANS choisir le
    # segment (pas de `target.segment`). Réutilise le seam `tailler` avec la
    # cible par défaut (apex) → façade fait foi (validité/coût/effet). Coût
    # propre `couper` (= tailler). Marque l'action (ouvre `tailler` par la
    # chaîne sécateur→couper→tailler) + réévalue les déblocages.
    if verb == "couper":
        cost = A.cout_action(gs, player, "couper",
                             A._objets_action("couper", plant))
        ok = A.tailler(gs, player, plant, eco, cible="apex", segment_id=None)
        return bilan(ok, cost, 0.0,
                     f"branche coupée : {plant.name}" if ok
                     else "Vigueur insuffisante — rien coupé")

    # Gestes MANUELS de BASE (acquisition des moyens d'agir ①) : `pincer`
    # (DOUX — auxine ↓, aucun retrait, débourrement émergent) et `arracher`
    # (NET à la main — écime + litière `bois` + `erode()` la vitalité, le
    # différenciateur main/outil). Même désignation que `tailler` (cible
    # apex/branche + segment cliqué validé en amont), coûts propres FAIBLE/
    # ELEVE via la façade. La façade fait foi (seam, dépôt, érosion).
    if verb in ("pincer", "arracher"):
        cible = params.get("cible", "apex")
        if cible not in ("apex", "branche"):
            return bilan(False, 0.0, 0.0,
                         f"cible inconnue : {cible!r}")
        seg = target.get("segment")
        if seg is not None:
            if not isinstance(seg, int) or isinstance(seg, bool):
                return bilan(False, 0.0, 0.0, f"segment non entier : {seg!r}")
            if not 0 <= seg < len(plant.segments):
                return bilan(False, 0.0, 0.0,
                             f"segment hors structure : {seg} "
                             f"(plante à {len(plant.segments)} segments)")
            if plant.segments[seg].parent is None:
                return bilan(False, 0.0, 0.0,
                             "le collet est protégé — rien à retirer ici")
        cost = A.cout_action(gs, player, verb, A._objets_action(verb, plant))
        geste = A.pincer if verb == "pincer" else A.arracher
        ok = geste(gs, player, plant, eco, cible=cible, segment_id=seg)
        if verb == "pincer":
            msg = (f"pincé : {plant.name}" if ok
                   else "Vigueur insuffisante — rien pincé")
        else:
            msg = (f"branche arrachée à la main : {plant.name}" if ok
                   else "Vigueur insuffisante — rien arraché")
        return bilan(ok, cost, 0.0, msg)

    # tailler
    cible = params.get("cible", "apex")
    if cible not in ("apex", "branche"):
        return bilan(False, 0.0, 0.0,
                     f"cible de taille inconnue : {cible!r}")
    # Segment explicite (tranche 5, la branche cliquée) : validé AVANT
    # la façade — un refus de désignation ne draine pas la Vigueur.
    # NB : bool est un sous-type d'int en Python → exclu explicitement.
    seg = target.get("segment")
    if seg is not None:
        if not isinstance(seg, int) or isinstance(seg, bool):
            return bilan(False, 0.0, 0.0,
                         f"segment non entier : {seg!r}")
        if not 0 <= seg < len(plant.segments):
            return bilan(False, 0.0, 0.0,
                         f"segment hors structure : {seg} "
                         f"(plante à {len(plant.segments)} segments)")
        if plant.segments[seg].parent is None:
            return bilan(False, 0.0, 0.0,
                         "le collet est protégé — rien à couper ici")
    ok = A.tailler(gs, player, plant, eco, cible=cible, segment_id=seg)
    quoi = f"segment {seg}" if seg is not None else cible
    return bilan(ok, cost, 0.0,
                 f"taillé ({quoi}) : {plant.name}" if ok
                 else "Vigueur insuffisante — rien taillé")
