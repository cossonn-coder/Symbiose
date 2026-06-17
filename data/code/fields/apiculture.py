"""
SYMBIOSE — fields/apiculture.py
Tick de la RUCHE (arc pollinisation ⑥, CONCEPTION §H/§I — couche joueur).

Une `ruche` (structure posable, modèle bac/pile du décompo ⑤) est un HUB abeille :
elle CAPTURE un essaim sauvage existant (elle ne fabrique pas d'abeilles ex nihilo,
philo #1 : il faut d'abord soigner le milieu) puis PRODUIT du miel proportionnel au
nectar mellifère réellement butiné autour d'elle. Deux flux interconnectés (philo #2,
[[regle_interconnexion_acteurs]]) :

  - capture/déclin de l'essaim ← champ `abeille` LOCAL (lui-même nourri par la
    floraison via le registre §E → pas de fleurs = pas d'abeilles = ruche vide) ;
  - miel ← `res_abeille` LOCAL (= floraison × attractivité abeille, la MÊME ressource
    que le champ §C) → le miel est l'intégrale du nectar mellifère (§I.1).

Module PURE & déterministe, duck-typé sur `eco` (miroir de `fields/lifecycle.py` et
`fields/foragers.py`, garde-fou taille) : aucune écriture de champ du sol, aucun RNG,
aucun log. Réutilise le registre des pollinisateurs (`build_pollinator_registry`) pour
la ressource abeille — SOURCE UNIQUE, jamais de duplication d'attractivité. Importe
`population` (registre) mais N'EN EST PAS importé → aucun cycle (population ne connaît
pas l'apiculture ; le bump d'habitat ruche §H.2 vit DANS population, lisant `eco`).

**Golden NEUTRE** (§H.3) : `tick_ruches` RETOURNE IMMÉDIATEMENT si aucune ruche n'est
posée — le smoke n'instancie pas de ruche → zéro lecture de champ, comportement
bit-identique.
"""
from __future__ import annotations

from fields.population import build_pollinator_registry, _make_nectar_grid

# Paramètres apicoles — PLACEHOLDERS NOMMÉS, calibrage post-test (n'affectent ni le
# golden, neutre sans ruche, ni le déterminisme). §H.2 (capture/déclin), §I.1 (miel).
CAPTURE_RATE   = 0.30   # vitesse de peuplement par semaine ∝ abeille locale (saturant)
ESSAIM_MIN     = 0.05   # densité abeille minimale pour qu'une ruche capture un essaim
ESSAIM_FAMINE  = 0.04   # déclin hebdo de l'essaim quand l'abeille locale s'effondre
MIEL_RATE      = 0.30   # miel produit / semaine = MIEL_RATE · essaim · nectar_local
MIEL_MAX       = 10.0   # plafond de réserve d'une ruche


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def tick_ruches(eco, tile, plants) -> None:
    """Maturation hebdomadaire des ruches posées (⑥, §H.2/§I.1).

    Pour chaque ruche de `eco.structures` :
      1. CAPTURE/DÉCLIN de l'essaim ← `abeille` locale. Au-dessus de `ESSAIM_MIN`,
         croissance saturante vers 1.0 (`+= CAPTURE_RATE · abeille · (1−essaim)`) ;
         en-dessous (abeille effondrée — hiver, nectar disparu), déclin géométrique
         (`−= ESSAIM_FAMINE · essaim`). Le déclin nectarifère est PORTÉ par le champ
         abeille (qui dépend déjà de la floraison) → interconnexion, pas de double
         comptage (§H.2).
      2. PRODUCTION de miel ← nectar abeille LOCAL (= `res_abeille`, §C/§I.1),
         `miel += MIEL_RATE · essaim · nectar_local`, plafonné `MIEL_MAX`. Pas de
         fleurs mellifères = nectar 0 = pas de miel (philo #2).

    **No-op STRICT si aucune ruche** (golden §H.3) : retour immédiat AVANT toute
    lecture de champ. Déterministe : ruches dans l'ordre d'insertion, zéro RNG.
    """
    ruches = [s for s in eco.structures if s.kind == "ruche"]
    if not ruches:
        return                                 # aucune ruche → zéro travail (golden NEUTRE)

    abeille = eco.populations.get("abeille")   # champ §E (peut manquer si registre nu)
    spec = next(s for s in build_pollinator_registry() if s.name == "abeille")
    nectar = _make_nectar_grid(spec.attractivite, spec.attractivite_defaut)(eco, tile, plants)

    for ruche in ruches:
        r, c = ruche.plot
        dens = abeille.at_plot(r, c) if abeille is not None else 0.0
        if dens >= ESSAIM_MIN:
            ruche.essaim = _clamp01(ruche.essaim + CAPTURE_RATE * dens * (1.0 - ruche.essaim))
        else:
            ruche.essaim = _clamp01(ruche.essaim - ESSAIM_FAMINE * ruche.essaim)
        if 0 <= r < eco.rows and 0 <= c < eco.cols:
            gain = MIEL_RATE * ruche.essaim * nectar[r][c]
            ruche.miel = min(MIEL_MAX, ruche.miel + gain)
