"""
SYMBIOSE — sim/aide.py
L'AIDE au jardinier (retour F5 Nico, « debug d'abord ») : pour une espèce, ses
PROBLÈMES récents (stress consignés au ledger) et le REMÈDE de chacun.

⚠️ TENSION PHILO ASSUMÉE (#5 indices > conseils, #6 pas de tutoriel imposé) : le
carnet interprétatif révèle la CAUSE ; l'aide, elle, donne l'ACTION. On l'introduit
d'abord comme OUTIL DEBUG (toujours visible), mais STRUCTURÉE pour un futur gating
de jeu : chaque remède porte son `concept`-gate et un flag `debloque` (concept
maîtrisé ≥ seuil du carnet). Le mode debug montre tout ; un mode jeu futur ne
montrera que les remèdes `debloque` (le savoir se mérite, comme l'interprétatif).

GARDE-FOU DE COUCHE (identique à `carnet`/`journal`/`maitrise`) : `aide` est au
niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants` ne l'importent
JAMAIS.** Lecture pure du ledger ② + `maitrise.palier` (D12). Aucun RNG. Pas de
joueur / pas de ledger → `[]` (no-op golden, jamais de crash).

REMEDE = LIVRABLE ÉDITORIAL : table de données (action par type de problème),
pas de la logique. Le gating (quel concept, quel seuil) réutilise le carnet
(`_concept_de`, `_seuil`) — jamais dupliqué.
"""
from __future__ import annotations

from sim import maitrise
from sim.carnet import _concept_de, _seuil

# --- Corpus des remèdes (retour F5) ------------------------------------------
# Clé = (kind, cause) d'un événement-PROBLÈME (mêmes clés que le carnet). Seuls
# les stress/accidents ont un remède ; les faits positifs (germination, floraison,
# nouaison, reproduction, acclimatation) n'en portent pas → pas d'entrée ici.
REMEDE: dict[tuple[str, str | None], str] = {
    ("stagnation", "sec"):    "Arroser, et pailler pour retenir l'humidité.",
    ("stagnation", "noyé"):   "Améliorer le drainage, alléger le sol.",
    ("stagnation", "ombre"):  "Éclaircir l'ombrage alentour pour dégager la lumière.",
    ("stagnation", "froid"):  "Protéger du froid (voile) ou attendre la chaleur.",
    ("ravageur", None):       "Favoriser les auxiliaires ; retirer les nuisibles à la main au besoin.",
    ("mort", "asphyxie"):     "Drainer d'urgence : l'excès d'eau prolongé étouffe les racines.",
    ("mort", "gel"):          "Protéger du gel les espèces peu rustiques.",
    ("mort", "conflit"):      "Éclaircir : trop de concurrence pour la lumière et les ressources.",
    # Causes lues dans `[raison]` (chronique des espèces ①). Gestes de MILIEU
    # (philo #1). Pas de remède pour la fin de cycle, la sénescence, l'usure (aléa
    # de fond) ni `autre` (cause inconnue) : rien à corriger.
    ("mort", "herbivorie"):   "Accueillir les auxiliaires (haie, abris, fleurs) pour tenir les brouteurs en respect.",
    ("mort", "maladie"):      "Aérer, ne pas mouiller le feuillage, tourner les familles sur ce sol.",
    ("mort", "grele"):        "Pailler et poser un voile sur les semis tendres quand le ciel menace.",
    ("mort", "vent"):         "Abriter derrière une haie ou un brise-vent ; laisser les semis s'endurcir au vent doux.",
    ("mort", "secheresse"):   "Pailler et couvrir le sol pour qu'il garde son eau ; arroser en profondeur.",
    ("mort", "ombre"):        "Éclaircir le couvert alentour ou semer cette espèce plus au soleil.",
}


def aide_espece(game_state: dict, player: str, espece: str) -> list[dict]:
    """Remèdes des problèmes RÉCENTS d'une espèce (clé catalogue). Parcourt le
    ledger du joueur, retient les événements-problèmes de cette espèce (clé dans
    REMEDE), dédupliqués par (kind, cause) dans l'ordre de première apparition.
    Chaque remède porte son `concept`-gate et `debloque` (concept maîtrisé ≥ seuil).
    PUR (lecture seule). Sans ledger / sans joueur → `[]` (golden-safe)."""
    journal = game_state.get("journal")
    if not journal:
        return []
    st = journal.get(player)
    if not st:
        return []
    seuil = _seuil(game_state, player)
    vus: set[tuple[str, str | None]] = set()
    out: list[dict] = []
    for e in st["entries"]:
        if e["espece"] != espece:
            continue
        cle = (e["kind"], e["cause"])
        if cle not in REMEDE or cle in vus:
            continue
        vus.add(cle)
        concept = _concept_de(e["kind"], e["cause"])
        out.append({
            "concept": concept,
            "remede": REMEDE[cle],
            "debloque": maitrise.palier(game_state, player, concept) >= seuil,
        })
    return out
