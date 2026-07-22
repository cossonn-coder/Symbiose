"""
SYMBIOSE — fields/population/perception.py
Perception PURE & déterministe : échantillonnage des sprites de faune
(`sample_sprites`) et des carpophores (`sample_carpophores`) depuis les champs,
avec leurs constantes propres. Extrait de `population.py` (scission /refactor
2026-06-30).
"""
import heapq
from dataclasses import dataclass

from fields.noise import _hash_noise
from fields.population.field import PopulationField


# ---------------------------------------------------------------------------
# CONSTANTES DE PERCEPTION (échantillonnage sprite — §3)
# ---------------------------------------------------------------------------

# Un sprite = un quantum de densité. Calé sur la plage de densité ÉMERGENTE en
# climat tempéré (pic saisonnier observé ~0.2 ; cf. trace de calibrage) : un
# quantum de 0.06 fait apparaître les sprites un à un au fil de la montée
# estivale (0→4 sur la saison) et disparaître l'hiver. Knob de calibrage (§8).
DENSITE_PAR_SPRITE = 0.06
SPRITES_PAR_PLOT_MAX = 4    # cap par plot (les sprites saturent, le champ garde le vrai nombre)

# Cap GLOBAL du monde (toutes tuiles × toutes espèces confondues). Le cap par
# plot ci-dessus borne la SATURATION LOCALE ; celui-ci borne la CHARGE TOTALE de
# rendu/pont/diff : avec 10 espèces × ~1188 plots, le total grimpe à ~14 000
# sprites (le catalogue faune enrichi a multiplié les émetteurs), inutilement
# lourd à sérialiser/transférer/différencier à chaque snapshot. Au-delà de ce
# plafond, `cap_sprites_global` ne garde que les plus DENSES (les hotspots restent
# fournis, les zones éparses s'effacent d'abord). Knob de calibrage : monter la
# valeur si le jardin paraît trop vide de faune au zoom serré (§8).
SPRITES_MONDE_MAX = 5000

# Décalage du canal _hash_noise pour la coordonnée Y (décorrèle X et Y).
_SLOT_Y_OFFSET = 0x40


# ---------------------------------------------------------------------------
# PERCEPTION — échantillonnage sprite (fonction PURE, §3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpriteSample:
    """Un sprite échantillonné — donnée de rendu, ne porte AUCUNE Vigueur."""
    guild: str
    row: int
    col: int
    slot: int          # index du quantum dans le plot (0..cap-1)
    x_frac: float      # position dans le plot ∈ [0,1], INDÉPENDANTE de la semaine
    y_frac: float
    activite: float    # vitesse d'animation / errance (pur rendu)
    densite: float     # densité locale du plot — priorité du cap global (§ cap)


def sample_sprites(field: PopulationField, seed: int,
                   densite_par_sprite: float = DENSITE_PAR_SPRITE,
                   cap: int = SPRITES_PAR_PLOT_MAX) -> list[SpriteSample]:
    """
    Règle d'échantillonnage densité → entités (docs/faune/vie_macro/conception_vie_macro.md §3).
    PURE & déterministe : aucun spawn par RNG vivant, aucun feedback vers la sim
    → golden-neutre (les sprites lisent le champ, ne le modifient pas).

      nombre   = min(cap, floor(densité / densite_par_sprite))
      position = _hash_noise(seed, salt+slot, r, c) — INDÉPENDANTE de la semaine
                 → un slot occupe TOUJOURS le même point ; il bascule seulement
                   visible/caché quand la densité franchit son seuil.
      activite = field.activite(r, c) (pur rendu).
    """
    spec = field.spec
    sprites: list[SpriteSample] = []
    for r in range(field.rows):
        for c in range(field.cols):
            d = field.at_plot(r, c)
            n = min(cap, int(d / densite_par_sprite))
            if n <= 0:
                continue
            act = field.activite(r, c)
            for slot in range(n):
                x = _hash_noise(seed, spec.salt + slot, r, c)
                y = _hash_noise(seed, spec.salt + _SLOT_Y_OFFSET + slot, r, c)
                sprites.append(SpriteSample(
                    guild=spec.name, row=r, col=c, slot=slot,
                    x_frac=x, y_frac=y, activite=act, densite=d,
                ))
    return sprites


def cap_sprites_global(candidats, cap: int = SPRITES_MONDE_MAX):
    """
    Borne le NOMBRE TOTAL de sprites du monde à `cap`, en gardant les plus DENSES
    (perception §cap). PURE & déterministe → golden-NEUTRE (aucune lecture par la
    sim, aucun RNG).

      candidats : itérable de tuples `(porteur, SpriteSample)` — `porteur` est
                  opaque ici (côté serveur = `(tile_id, espèce)`), simplement
                  transporté ; la sélection ne regarde QUE le `SpriteSample`.
      priorité  : (densité locale, x_frac) décroissante. La densité fait remonter
                  les hotspots ; `x_frac` (déjà un hash spatial déterministe,
                  indépendant de la semaine) départage → sélection STABLE dans le
                  temps (deux plots de même densité ne clignotent pas d'une semaine
                  à l'autre).

    Sous le plafond : renvoie tout tel quel (ordre préservé). Au-dessus : les `cap`
    meilleurs. `heapq.nlargest` = O(n·log cap), négligeable sur ~14 000 candidats.
    """
    candidats = list(candidats)
    if len(candidats) <= cap:
        return candidats
    return heapq.nlargest(
        cap, candidats, key=lambda pc: (pc[1].densite, pc[1].x_frac))


# ---------------------------------------------------------------------------
# PERCEPTION — carpophores échantillonnés (sprint mycélium ④, CONCEPTION §1.1)
# ---------------------------------------------------------------------------
# Les carpophores (champignons VISIBLES) sont de la PERCEPTION PURE, dérivée du
# champ `mycelium` — AUCUN état propre, recalculés à chaque snapshot (comme la vie
# macro). Ils apparaissent là où le réseau est DENSE + le sol HUMIDE (après pluie)
# + en SAISON favorable (automne). Zéro RNG (hash spatial déterministe), zéro
# retour sur la simulation → golden-NEUTRES (le CHAMP fait tout, le carpophore ne
# nourrit ni ne décompose — piège du kickoff §pièges).

_SALT_CARPOPHORE = 0x2AF001       # canal _hash_noise dédié (décorrélé des guildes)
CARPO_MYCEL_MIN  = 0.30           # seuil de densité mycélienne sous lequel rien ne fructifie
CARPO_HUMIDE_MIN = 1.5            # humidité (échelle [0,3]) sous laquelle pas de fructification
CARPO_PAR_PLOT   = 3              # nb max de carpophores par plot (saturation visuelle)
CARPO_DENS_REF   = 0.70           # densité mycélienne au-delà de laquelle le plot est plein
# Fenêtre AUTOMNE (semaines dans l'année) — dupliquée ici plutôt qu'importée de
# `sim.engine.calendrier` (couche `fields` n'importe JAMAIS `sim`, règle de couches).
# Miroir de SAISONS["automne"] = range(27, 40) ; constante simple, pas de cycle.
_CARPO_AUTOMNE = range(27, 40)


@dataclass(frozen=True)
class Carpophore:
    """Un carpophore échantillonné — donnée de RENDU pure (aucun état moteur)."""
    row: int
    col: int
    slot: int          # index dans le plot (0..n-1)
    x_frac: float      # position dans le plot ∈ [0,1], INDÉPENDANTE de la semaine
    y_frac: float
    densite: float     # densité mycélienne locale [0,1] (pilote la taille du sprite)


def sample_carpophores(eco, seed: int, week_in_year: int) -> list[Carpophore]:
    """
    Échantillonne les carpophores VISIBLES du champ `mycelium` (perception §1.1).
    PURE & déterministe : lecture seule du champ, positions par hash spatial
    indépendant de la semaine → golden-NEUTRE.

    Conditions de fructification, par plot :
      - réseau DENSE          : mycelium ≥ CARPO_MYCEL_MIN ;
      - sol HUMIDE (pluie)    : humidite ≥ CARPO_HUMIDE_MIN ;
      - SAISON favorable      : automne (saison_de(week_in_year) == "automne").
    Nombre de carpophores = floor(CARPO_PAR_PLOT × min(1, mycelium / CARPO_DENS_REF)).
    Liste VIDE si mycélium nul / sol sec / hors automne → pont neutre.
    """
    mycel = getattr(eco, "mycelium", None)
    # Saison non favorable ou pas de champ → aucun carpophore (perception muette).
    if mycel is None or week_in_year not in _CARPO_AUTOMNE:
        return []
    carpos: list[Carpophore] = []
    for r in range(eco.rows):
        for c in range(eco.cols):
            d = mycel.at_plot(r, c)
            if d < CARPO_MYCEL_MIN:
                continue
            if eco.humidite.at_plot(r, c) < CARPO_HUMIDE_MIN:
                continue
            n = int(CARPO_PAR_PLOT * min(1.0, d / CARPO_DENS_REF))
            for slot in range(n):
                x = _hash_noise(seed, _SALT_CARPOPHORE + slot, r, c)
                y = _hash_noise(seed, _SALT_CARPOPHORE + _SLOT_Y_OFFSET + slot, r, c)
                carpos.append(Carpophore(
                    row=r, col=c, slot=slot, x_frac=x, y_frac=y, densite=d))
    return carpos
