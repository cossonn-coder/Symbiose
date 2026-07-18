# SYMBIOSE — tools/jardinier_auto/comptabilite.py
# La COMPTABILITÉ commutable de l'automate (§4, tronçon ③) et la collecte des
# CONSÉQUENCES des gestes (§6). Responsabilité unique : tout ce qui touche à la
# Vigueur, au déblocage des gestes et aux conséquences tracées — la boucle
# n'orchestre que l'appel, elle ne connaît pas les règles de comptabilité.
#
# Les trois axes commutables (flags orthogonaux du ProfilAutomate) :
#   - paie_vigueur   : l'automate paie sa Vigueur ET respecte `gestes_debloques`
#                      (un geste verrouillé n'est pas joué → impasse §7). Le budget
#                      lui-même (coupe des gestes trop chers) vit dans `boucle.py`.
#   - credite_maitrise : les conséquences de maîtrise (déverrouillages, paliers)
#                      arrivent VRAIMENT et sont tracées ; sinon on ne mute PAS
#                      l'état de maîtrise du tout (choix sobre du kickoff §6).
#
# VIGUEUR NON BORNÉE en mode libre (kickoff §③, approche « la moins intrusive ») :
# les gestes `sim.actions` appellent `vigueur.spend` en interne et REFUSENT quand
# le solde ne couvre pas — au ① cela noyait le journal LIBRE d'`arroser echec`.
# Plutôt que de re-créditer après coup (gain plafonné → fragile), on INITIALISE le
# solde à une sentinelle géante avant les gestes : `spend` draine `min(cost, solde)`
# et ne tombe jamais à sec dans un tick. On n'écrit que `game_state["vigueur"]`
# (état joueur, opt-in) via l'API publique `ensure_player` — le moteur reste intact.
#
# Déterminisme (philo #3) : tous les diffs passent par des ensembles/dicts triés à
# clé totale ; `evaluer_deblocages` renvoie déjà une liste triée. Zéro RNG.

from __future__ import annotations

from sim import vigueur as V
from sim.actions import evaluer_deblocages, est_debloque

# Solde sentinelle du mode libre : assez grand pour couvrir tous les gestes d'un
# tick sans jamais s'épuiser, sans être infini (évite les NaN/inf dans les calculs
# de ratio de `spend`).
SOLDE_LIBRE = 1e9


def assurer_solde_libre(game_state: dict, player: str) -> None:
    """Mode `paie_vigueur=False` : garantit un solde de Vigueur non borné avant les
    gestes du tick (voir en-tête). Idempotent, appelé une fois par tick — la régen
    passive et le refill de saison peuvent avoir rogné `courante` entre deux passes,
    d'où le rehaussement systématique plutôt qu'une seule fois."""
    st = V.ensure_player(game_state, player)
    if st["courante"] < SOLDE_LIBRE:
        st["courante"] = SOLDE_LIBRE


def separer_verrouilles(game_state: dict, player: str, plans: list):
    """Mode `paie_vigueur=True` : sépare les plans jouables des plans dont le VERBE
    n'est pas dans `gestes_debloques` (geste GATED non acquis). Renvoie
    `(jouables, verrouilles)` — chaque élément est un plan `(cle, tile, eco, plant,
    Plan)`. Les verrouillés ne sont PAS joués : la boucle les consigne en impasse
    `geste_verrouille` (§7 : trou de gameplay = « ce geste n'est pas encore ouvert »).
    En mode libre, la boucle n'appelle pas cette fonction (aucun gating)."""
    jouables, verrouilles = [], []
    for p in plans:
        if est_debloque(game_state, player, p[4].verbe):
            jouables.append(p)
        else:
            verrouilles.append(p)
    return jouables, verrouilles


# --- Snapshots pour le diff des conséquences --------------------------------
def snapshot_paliers(game_state: dict, player: str) -> dict:
    """Paliers de maîtrise courants par objet (lecture PURE, ne crée aucune clé —
    un joueur sans couche maîtrise donne un dict vide). Sert de référence `avant`
    pour détecter les franchissements de palier au fil du tick."""
    objets = game_state.get("maitrise", {}).get(player, {}).get("objets", {})
    return {objet: o["palier"] for objet, o in objets.items()}


def snapshot_vivantes(engine) -> set:
    """Ensemble des plantes VIVANTES (`is_alive`), identifiées par une clé totale
    stable `(tile_id, y_cm, x_cm, name)` — positions continues uniques, pas d'uid
    (§2.1). Sert de référence `avant` pour détecter les morts sur le tick."""
    vivantes = set()
    for tile in engine.tiles:
        for plant in tile.plants:
            if plant.is_alive:
                vivantes.add((tile.tile_id, plant.y_cm, plant.x_cm, plant.name))
    return vivantes


# --- Conséquences (§6), renvoyées comme (type, detail) triés -----------------
def consequences_maitrise(game_state: dict, player: str, paliers_avant: dict) -> list:
    """Déverrouillages de gestes + franchissements de palier (mode `credite_maitrise`
    seulement — l'appelant ne nous invoque pas sinon). `evaluer_deblocages` OUVRE les
    gestes GATED dont une condition est désormais remplie et renvoie les nouveaux
    verbes (triés) ; on les consigne. Puis on diffe les paliers `avant/après` : une
    hausse est un franchissement à tracer. Renvoie `[(type, detail), …]` déterministe."""
    conseq = [("deblocage", verbe) for verbe in evaluer_deblocages(game_state, player)]
    paliers_apres = snapshot_paliers(game_state, player)
    for objet in sorted(paliers_apres):
        avant, apres = paliers_avant.get(objet, 0), paliers_apres[objet]
        if apres > avant:
            conseq.append(("palier", f"{objet}:{avant}->{apres}"))
    return conseq


def consequences_morts(vivantes_avant: set, vivantes_apres: set) -> list:
    """Morts survenues PENDANT les gestes de l'automate (diff `avant - après` des
    plantes vivantes). Corrèle une mort à un geste du même tick — typiquement
    `deraciner` (§6). La mortalité du tick moteur (succession, stress) est le domaine
    du golden, hors de la causalité de l'automate → non tracée ici. Renvoie
    `[("mort", detail), …]` trié par clé totale (déterminisme)."""
    morts = sorted(vivantes_avant - vivantes_apres)
    return [("mort", f"{name}@({tile_id}:{y:.0f},{x:.0f})")
            for (tile_id, y, x, name) in morts]
