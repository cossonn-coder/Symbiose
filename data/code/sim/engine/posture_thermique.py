"""
SYMBIOSE — sim/engine/posture_thermique.py
Signes thermiques PAR PALIERS (D139, sprint niche thermique ④).
Spec : `docs/vegetal/genetique/conception_niche_thermique.md` §6.

📖 Pédagogie — une plante MONTRE où elle en est dans sa plage vivable, sans chiffre.
Une seule grandeur continue, la POSTURE THERMIQUE ∈ [−1, 1] :

    −1 ── froid ──────────────── 0 ─────────────── chaud ── +1
    effondré · noirci · translucide · violacé · pendant │ étalé │ replié · flétri à midi · bords jaunis · brûlé

  FROID (nuit la plus froide de la semaine, `plant.t_nuit`) :
    pendant      la nuit approche la 1ʳᵉ limite de lésion (+3 °C → limite) ;
    violacé      même chose, chez une plante qui a ACCUMULÉ le froid (`cold_memory`) ;
    translucide  froid SANS gel : nuit < `lim_froid` (marque `froid`) ;
    noirci       GEL : nuit < `lim_gel` (marque `gel`) ;
    effondré     noirci ET vitalité basse : la plante s'affaisse.
  CONFORT : 0 → feuilles étalées, aucun palier.
  CHAUD (feuille au jour le plus chaud, `plant.t_feuille`) :
    replié       la feuille approche `lim_chaud` (−3 °C → limite) ;
    flétri à midi  même chose chez une plante ASSOIFFÉE (stomates fermés, `soif`) ;
    bords jaunis feuille > `lim_chaud` : la plante ne pousse plus ;
    brûlé        feuille > `lim_brul` (marque `brulure`).

INVARIANT DRY (`sim/semiologie.py` §2.4) : chaque palier de DÉGÂT s'allume au seuil
MÊME du moteur — mêmes méthodes `lim_*` (PlantInstance), même nuit et même T_feuille
que `reponse_thermique.py`, et la rampe est pleine quand le dégât vaut 1 point/semaine
(`1/FROID_LESION_K`, `1/BRULURE_K`, `FROST_SEVERITY_REF`). Les deux paliers d'ANNONCE
(pendant, replié) précèdent le dégât de `MARGE_ANNONCE` °C : la plante prévient.

Bandes : chaque palier occupe un quart de la demi-échelle (0–0,25, 0,25–0,5, 0,5–0,75,
0,75–1) ; l'intensité DANS le palier suit la rampe. Les marques événementielles
(`symptom_marks`) prolongent les paliers de dégât après la nuit : un tissu noirci le
reste tant que la marque n'est pas cicatrisée.

Lecture PURE au snapshot (`tools/simserver/serialize.py`) : n'écrit rien, jamais
appelé par le tick → golden INTACT. Zéro RNG (philo #3).
Couche `sim.engine` : réutilise les pentes de dégât et `soif` du moteur (DRY).
"""
from __future__ import annotations

from fields.ecofields.constants import VITALITE_STEP
from .aleas import FROST_SEVERITY_REF
from .feuille import soif
from .reponse_thermique import FROID_LESION_K, BRULURE_K

# Avance (°C) des paliers d'ANNONCE sur la 1ʳᵉ limite : feuilles pendantes à
# `lim_froid + 3`, repliées à `lim_chaud − 3` (conception §6, valeurs de conception).
MARGE_ANNONCE = 3.0

# Vitalité sous laquelle une plante GELÉE s'effondre : il ne lui reste qu'un « point »
# de `ReduceHealth` (VITALITE_STEP = 1/3) — un gel de plus l'emporte.
VITALITE_EFFONDRE = VITALITE_STEP + 1e-9

# Paliers dans l'ordre de gravité (rang = départage à valeur égale).
PALIERS_FROID = ("pendant", "violace", "froid", "gel", "effondre")
PALIERS_CHAUD = ("replie", "fletri_midi", "bords_jaunis", "brulure")
PALIERS = PALIERS_FROID + PALIERS_CHAUD


def _ramp(mesure: float, apparition: float, plein: float) -> float:
    """Rampe bornée [0,1] de `semiologie._ramp` (même forme ; recopiée pour ne pas
    importer une voix depuis le moteur)."""
    if mesure <= apparition:
        return 0.0
    if plein <= apparition:
        return 1.0
    return min(1.0, (mesure - apparition) / (plein - apparition))


def _froid(plant) -> tuple[float, str | None]:
    """(intensité [0,1], palier) côté froid."""
    cands = [(0.0, None)]
    marks = plant.symptom_marks
    nuit = plant.t_nuit
    l_froid, l_gel = plant.lim_froid(), plant.lim_gel()
    gele = nuit is not None and nuit < l_gel
    if nuit is not None:
        # Annonce : 1ʳᵉ limite de lésion rencontrée en refroidissant (froid ou gel).
        seuil = max(l_froid, l_gel)
        pend = _ramp(-nuit, -(seuil + MARGE_ANNONCE), -seuil)
        if pend > 0.0:
            v = 0.25 * pend * (1.0 + plant.cold_memory)       # pendant → violacé
            cands.append((v, "violace" if v > 0.25 else "pendant"))
        if nuit < l_froid:                                    # seuil de `_tick_nuit_froide`
            cands.append((0.5 + 0.25 * _ramp(l_froid - nuit, 0.0, 1.0 / FROID_LESION_K),
                          "froid"))
        if gele:                                              # seuil de `frost_sev`
            cands.append((0.75 + 0.25 * _ramp(l_gel - nuit, 0.0, FROST_SEVERITY_REF),
                          "gel"))
    if marks.get("froid", 0.0) > 0.0:
        cands.append((0.5 + 0.25 * marks["froid"], "froid"))
    if gele or marks.get("gel", 0.0) > 0.0:
        cands.append((0.75 + 0.25 * marks.get("gel", 0.0), "gel"))
        if plant.vitalite <= VITALITE_EFFONDRE:
            cands.append((0.75 + 0.25 * (1.0 - plant.vitalite), "effondre"))
    return max(cands, key=lambda c: (c[0], _rang(c[1])))


def _chaud(plant, eco) -> tuple[float, str | None]:
    """(intensité [0,1], palier) côté chaud."""
    cands = [(0.0, None)]
    tf = plant.t_feuille
    l_chaud, l_brul = plant.lim_chaud(), plant.lim_brul()
    if tf is not None:
        rep = _ramp(tf, l_chaud - MARGE_ANNONCE, l_chaud)
        if rep > 0.0:
            v = 0.25 * rep * (1.0 + soif(plant, eco))           # replié → flétri à midi
            cands.append((v, "fletri_midi" if v > 0.25 else "replie"))
        if tf > l_chaud:                                      # seuil de la stagnation
            cands.append((0.5 + 0.25 * _ramp(tf, l_chaud, l_brul), "bords_jaunis"))
        if tf > l_brul:                                       # seuil de `_tick_brulure`
            cands.append((0.75 + 0.25 * _ramp(tf - l_brul, 0.0, 1.0 / BRULURE_K),
                          "brulure"))
    if plant.symptom_marks.get("brulure", 0.0) > 0.0:
        cands.append((0.75 + 0.25 * plant.symptom_marks["brulure"], "brulure"))
    return max(cands, key=lambda c: (c[0], _rang(c[1])))


def _rang(palier: str | None) -> int:
    return -1 if palier is None else PALIERS.index(palier)


def etat_thermique(plant, eco) -> tuple[float, str | None]:
    """(posture ∈ [−1, 1], palier ou None) : négatif = froid, positif = chaud,
    0 / None = confort (feuilles étalées). Le côté le plus marqué l'emporte.
    Arrondi à 3 décimales pour un diff snapshot stable (philo #3)."""
    c, pc = _froid(plant)
    h, ph = _chaud(plant, eco)
    if h > c:
        return round(min(1.0, h), 3), ph
    if c > 0.0:
        return round(-min(1.0, c), 3), pc
    return 0.0, None
