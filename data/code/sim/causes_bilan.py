"""
SYMBIOSE — sim/causes_bilan.py
CE QUI A MINÉ une plante, en mots (D140 G, sprint stress au bilan ⑤).
Spec : `docs/vegetal/sante/conception_plante_vivante.md` §5 et §9.

📖 Pédagogie — depuis le sprint stress au bilan, un stress ne tue presque plus
directement : le gel, la grêle, le mildiou ou l'eau stagnante RETIRENT des tissus
(feuilles, racines, vaisseaux), et c'est le BILAN carbone qui tue ensuite, quand les
réserves sont vides. Le log du moteur dit donc honnêtement « meurt de faim »… et le
carnet écrivait « s'est épuisée » là où le joueur avait vu le gel noircir la plante.

Ce module relit l'ÉTAT que le stress a laissé sur la plante (marques foliaires,
racines perdues, embolie, facteur limitant du bilan, âge) pour nommer ce qui l'a minée :
  - `cause_amont(plant, eco, saison)` : la cause d'une mort de FAMINE, en clé de
    cause du carnet (`gel`, `grele`, `maladie`, `asphyxie`, `ombre`…), None si rien
    ne se lit (vraie famine sans coupable visible) ;
  - `affiner(evs, morts, ecos)` : remplace la cause `famine` des événements
    `mort` par cette cause amont (carnet, chronique) ;
  - `voix_cause(plant)` : la clé de `signes_corpus.VOIX_CAUSE` pour l'info-bulle
    d'une plante VIVANTE (« desséchée », « gelée au cœur », « racines pourries »,
    « à bout d'âge »), None sinon.

GOLDEN NEUTRE : le log du tick entre dans le golden — on ne le réécrit pas. Tout se
fait HORS tick, par les lecteurs (journal, chronique, pont). Lecture pure, zéro RNG.
Couche `sim` : lit `plants`, `fields` (via semiologie) — jamais `sim.engine`.
"""
from __future__ import annotations

from sim.embolie import SEUIL_EMBOLIE
from sim.semiologie import leaf_symptoms
from sim.tempo import declin_senescent
from fields.ecofields import ASPHYXIE_HEALTH_SEUIL

# Cause de mort du carnet (clés de `carnet.CONCEPT_DE[("mort", …)]`) pour chaque trace
# que le stress laisse sur la plante. Absents : chlorose (carence, ne retire rien),
# sénescence (sa mort a sa propre ligne), acclimatation (une réponse, pas un dégât).
CAUSE_DE_SIGNE: dict[str, str] = {
    "secheresse": "secheresse", "brulure": "secheresse",
    "asphyxie": "asphyxie",
    "maladie": "maladie", "oidium": "maladie",
    "ravageurs": "herbivorie", "rongeur_racinaire": "herbivorie",
    "gel": "gel", "froid": "froid", "grele": "grele",
    "ombre": "ombre",
}
# Facteur limitant du dernier bilan (`plant.limitant`, `sim/bilan.facteur_limitant`)
# → cause : ce qui tenait la production sous l'entretien quand les réserves ont fondu.
CAUSE_DE_LIMITANT: dict[str, str] = {
    "ombre": "ombre", "sec": "secheresse", "chaud": "secheresse",
    "noyé": "asphyxie", "froid": "froid",
}

# Seuils de la voix de la cause (info-bulle) — [réglage F5, non mesurés] :
#   dessechee : la moitié des vaisseaux perdus (la mort est à SEUIL_EMBOLIE) ;
#   gelee     : marque de gel ≥ 0,5 = au moins la moitié du feuillage gelé d'un coup
#               (gain de marque = feuillage perdu / VITALITE_STEP × 0,5, cf. résolution) ;
#   racines   : un quart des racines perdues (pourriture/asphyxie, `eau_percue`) ;
#   age       : seconde moitié du déclin sénescent (production rabotée, entretien majoré).
PART_DESSECHEE = 0.5
SEUIL_GELEE = 0.5
SEUIL_RACINES = 0.25
SEUIL_AGE = 0.5


def cause_amont(plant, eco, saison: str | None = None) -> str | None:
    """Ce qui a retiré à `plant` de quoi vivre, lu sur son état, du plus direct au
    plus diffus (premier qui parle) :
      1. une marque de tissus RETIRÉS (gel, grêle, froid, brûlure, maladie — les
         `PerteTissus` du sprint, décroissantes) ou le feutrage d'oïdium : la plus forte ;
      2. des racines perdues (≥ SEUIL_RACINES) : noyées si le sol l'asphyxie, pourridié
         sinon ; des vaisseaux à moitié embolisés : la soif ;
      3. le facteur limitant de son dernier bilan (ombre, sec, noyé, froid, chaud) ;
      4. un signe chronique encore lisible (morsures, collet rongé…), même tri que
         l'info-bulle.
    None = famine sans coupable lisible (le carnet dit alors « épuisée »). Mesuré au
    banc ⑤ : le poivron à l'ombre porte un signe « collet rongé » plus fort que son
    signe d'ombre (sous seuil) — c'est le limitant du bilan qui dit l'ombre, d'où
    l'ordre. `saison` n'est lue par aucun détecteur (contrat de `leaf_symptoms`)."""
    marques = [(v, c) for c, v in plant.symptom_marks.items() if c in CAUSE_DE_SIGNE]
    if plant.oidium > 0.0:
        marques.append((plant.oidium, "oidium"))
    if marques:
        return CAUSE_DE_SIGNE[max(marques)[1]]
    if plant.pourriture_memory >= SEUIL_RACINES:
        return "asphyxie" if plant.asphyxie_memory > ASPHYXIE_HEALTH_SEUIL else "maladie"
    if plant.embolie >= PART_DESSECHEE * SEUIL_EMBOLIE:
        return "secheresse"
    if plant.limitant in CAUSE_DE_LIMITANT:
        return CAUSE_DE_LIMITANT[plant.limitant]
    for s in leaf_symptoms(plant, eco, saison):
        if s["cause"] in CAUSE_DE_SIGNE:
            return CAUSE_DE_SIGNE[s["cause"]]
    return None


def affiner(evs: list, morts: dict, ecos: dict) -> list:
    """Événements `evs` (`sim.evenements.Evenement`) dont chaque mort de FAMINE prend
    sa cause amont. `morts` = {(tile_id, pos, clé espèce): plante} des plantes mortes
    au tick (le moteur retire une herbacée morte dans le tick même : c'est le lecteur
    qui les a gardées). Une plante introuvable garde « famine »."""
    out = []
    for ev in evs:
        if ev.kind == "mort" and ev.cause == "famine":
            p = morts.get((ev.tile_id, ev.pos, ev.espece))
            amont = p and cause_amont(p, ecos.get(ev.tile_id))
            if amont:
                ev = ev._replace(cause=amont)
        out.append(ev)
    return out


def voix_cause(plant) -> str | None:
    """Clé de `VOIX_CAUSE` pour une plante VIVANTE, par ordre de gravité : vaisseaux
    rompus, bourgeons gelés, racines perdues, grand âge. None si rien ne la mine."""
    if plant.embolie >= PART_DESSECHEE * SEUIL_EMBOLIE:
        return "dessechee"
    if plant.symptom_marks.get("gel", 0.0) >= SEUIL_GELEE:
        return "gelee"
    if plant.pourriture_memory >= SEUIL_RACINES:
        return "racines"
    if declin_senescent(plant) >= SEUIL_AGE:
        return "age"
    return None
