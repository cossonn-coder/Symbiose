"""
SYMBIOSE — sim/reproduction.py
Héritage génétique biparental (D22).

À la production de graines sur une plante mère fécondée :
  - on cherche un PÈRE compatible (même famille) à portée de pollinisation ;
  - gène_enfant = moyenne(mère, père) + BRASSAGE ½σ_A²(1−F̄) + filet de mutation
    (modèle infinitésimal, D139 ②, cf. `heredite`) ;
  - pas de partenaire / espèce autogame / tirage contre le gène `autofecondation`
    → AUTOFÉCONDATION (F de l'enfant = (1+F_mère)/2 : la lignée se fixe).

Pollinisation par espèce : `pollination_mode` (wind/insect/self) +
`pollination_radius_cm`. En mode insecte, les rondelles `pollinisateur` et
`auxiliaire` de la tuile élargissent le rayon → favoriser les auxiliaires =
plus de brassage = meilleures graines (mécanique permaculture).

Introgression : un père d'une AUTRE espèce de la même famille décale les gènes
de l'enfant, qui garde l'espèce de la MÈRE — aucune nouvelle espèce générée.

Déterministe : appariement et mutation via les hash (_hash_noise / hash_gauss).
Aucun RNG live (règle de design #3).
"""
from __future__ import annotations
import math
import zlib

from plants import (species_compatible, GENE_NAMES, borne, neutre, sigma_a, H_MUT,
                    ADAPTOGENIC_GENES, PRIMING_FRAC)
from fields import _hash_noise, hash_gauss
from sim import weather as _weather   # normales climatiques (même couche, sans cycle)

# Modulation insecte du rayon de croisement (mode "insect" uniquement).
INSECT_BASE_REACH   = 0.5   # rayon effectif sans pollinisateurs (× rayon nominal)
INSECT_FULL_BONUS   = 1.0   # bonus de rayon à saturation du champ pollinisateur
POLLINATOR_SAT      = 0.40  # densité du champ pollinisateur saturant le bonus (knob, D31.2)
SELFING_SIGMA_RATIO = 0.5   # OBSOLÈTE depuis D139 ② (l'autofécondation réduit le
                            # brassage via F, cf. `heredite`) — conservé, plus lu.
# Canaux de hash de l'hérédité (D139 ②). Décalage de la coordonnée `r` : sépare le
# tirage du FILET de mutation (z₂) et le choix croisé/autofécondé du canal historique
# z₁ (`week*29 + i`, k = 4i), sans collision avec une vraie position (r < 100).
_CANAL_FILET = 100_003
_CANAL_CHOIX = 200_003


def is_seed_bearing(plant) -> bool:
    """La plante est-elle en âge/stade de porter des graines ?"""
    cls = plant.plant_class
    if hasattr(cls, "age_curve"):        # pérenne ligneuse (courbe d'âge)
        return plant.age_years >= getattr(cls, "maturity_years", 0.0)
    return plant.current_stage >= len(cls.growth_stages) - 1


def graine_fertile(cls) -> bool:
    """La graine de l'espèce est-elle FERTILE sous le climat courant ? (relève
    ligneuse ③, D130). Vrai si l'espèce ne déclare aucune condition
    (`graine_si_hiver_min_c` None), sinon si le mois le plus froid des normales
    (`T_MOY − T_AMP`, `sim.weather`) atteint le seuil — l'hiver où son pollinisateur
    obligatoire survit (figuier ↔ blastophage). Lu via le MODULE (pas copié à
    l'import) → un autre climat le change. NE gate PAS `is_seed_bearing` : la
    plante fleurit et fructifie quand même, seule la graine est stérile."""
    seuil = getattr(cls, "graine_si_hiver_min_c", None)
    if seuil is None:
        return True
    return _weather.T_MOY - _weather.T_AMP >= seuil


def recrue_par_fruits(cls) -> bool:
    """La relève de l'espèce passe-t-elle par ses VRAIS fruits ? (zoochorie ②, D42).

    Vrai pour un fruitier PÉRENNE à graine fertile : ses graines naissent des fruits
    qui tombent (`decompo.semer_chute`, grains sauvages au pied), et le tirage
    abstrait de `_reproduction` est coupé pour lui. Faux pour le figuier (graine
    stérile : rejets seuls), les annuelles fruitières (tomate, courgette) et tout
    non-fruitier (chemin `_reproduction` inchangé). Prédicat UNIQUE lu aux deux bouts."""
    return (getattr(cls, "fruitier", False) and cls.life_cycle == "perennial"
            and graine_fertile(cls))


# Glandée (masting, zoochorie ②) : part d'une année MAIGRE dans la nouaison d'une
# espèce à masting. Les années fortes nouent pleinement (×1). Un chêne nourrit tous
# ses consommateurs une année, les affame les suivantes : les prédateurs de graines
# (mulot ⑥) ne suivent pas, et la relève passe les années fortes [ordre de grandeur].
GLANDEE_MAIGRE = 0.15
# Canal de hash propre à la glandée (r de `_hash_noise`) — l'année tient la place de
# `week`, l'espèce celle de `c` : aucun canal `week * N` n'y collisionne.
_CANAL_GLANDEE = 7907


def facteur_glandee(cls, annee: int, seed: int) -> float:
    """Facteur de nouaison de l'année pour l'espèce (1,0 ou GLANDEE_MAIGRE). PUR.

    `glandee_periode_ans` None → 1,0 (pas de masting). Sinon année forte avec une
    probabilité 1/période. Le hash ne dépend QUE de (seed, année, espèce) → tous les
    pieds de l'espèce sont SYNCHRONES, comme une vraie glandée. Espèce identifiée par
    un CRC de son nom (stable d'un process à l'autre, contrairement à `hash()`)."""
    periode = getattr(cls, "glandee_periode_ans", None)
    if periode is None:
        return 1.0
    id_espece = zlib.crc32(cls.name.encode("utf-8")) & 0xFFFF
    forte = _hash_noise(seed, annee, _CANAL_GLANDEE, id_espece) < 1.0 / periode
    return 1.0 if forte else GLANDEE_MAIGRE


def _euclid2(a, b) -> float:
    return (a.x_cm - b.x_cm) ** 2 + (a.y_cm - b.y_cm) ** 2


def pollinator_reach(mother, tile, eco) -> float:
    """
    Rayon de croisement effectif (cm). Anémophile/autogame : rayon nominal.
    Insecte : modulé par la DENSITÉ LOCALE du champ `pollinisateur` (D31.2) —
    saturation à POLLINATOR_SAT. Sans pollinisateur → rayon réduit → autofécondation.

    Câblage D31.2 (docs/faune/vie_macro/conception_vie_macro.md §2.2 #3) : ce sont désormais les
    pollinisateurs VISIBLES qui élargissent le brassage. Les rondelles
    `pollinisateur`/`auxiliaire` ne modulent plus ICI ; elles restent terme-source
    d'HABITAT du champ (cf. `_pollinisateur_habitat_grid`/`_stability_grid`), donc
    favoriser les auxiliaires nourrit toujours le brassage — via le champ, pas en
    double.

    ───────── SUPPLANTÉ D31.2 — conservé pour mémoire ─────────
    # Ancienne modulation directe par les rondelles (saturation ~6 rondelles cumulées) :
    # sat = min(1.0, (tile.get_rondelle_count("pollinisateur")
    #                 + tile.get_rondelle_count("auxiliaire")) / 6.0)
    ───────────────────────────────────────────────────────────
    """
    cls = mother.plant_class
    if cls.pollination_mode != "insect":
        return cls.pollination_radius_cm
    r, c = mother.position
    # Densité pollinisatrice TOTALE = somme des types (abeille/syrphe/papillon,
    # arc pollinisation §C/§E ; remplace l'ancien champ agrégé `pollinisateur`).
    dens = eco.pollinator_density(r, c) if eco else 0.0
    sat = min(1.0, dens / POLLINATOR_SAT)
    return cls.pollination_radius_cm * (INSECT_BASE_REACH + INSECT_FULL_BONUS * sat)


def find_father(mother, plants, tile, eco, seed, week):
    """
    Père compatible (même famille) à portée, en âge de fleurir, le plus proche
    prioritaire (tie-break déterministe par hash). None si la mère est autogame
    ou si aucun partenaire n'est à portée → autofécondation.
    """
    if mother.plant_class.pollination_mode == "self":
        return None
    reach2 = pollinator_reach(mother, tile, eco) ** 2
    candidates = []
    for p in plants:
        if p is mother or not p.is_alive:
            continue
        if not species_compatible(mother.plant_class, p.plant_class):
            continue
        if not is_seed_bearing(p):
            continue
        d2 = _euclid2(mother, p)
        if d2 <= reach2:
            candidates.append((d2, p))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    nearest = candidates[0][0]
    tied = [p for d2, p in candidates if d2 <= nearest * 1.0001]
    if len(tied) == 1:
        return tied[0]
    r, c = mother.position
    idx = int(_hash_noise(seed, week * 23, r, c) * len(tied)) % len(tied)
    return tied[idx]


def heredite(mother, father, seed, week) -> tuple:
    """
    Hérédité INFINITÉSIMALE (D139 ②, conception §4) → `(gènes, F)` de l'enfant.

    Croisé ou autofécondé ? Graine par graine, par hash contre le gène
    `autofecondation` de la mère : même avec un père à portée, une tomate
    (≈ 0,95) se féconde presque toujours elle-même. Sans père (espèce autogame,
    pas de partenaire à portée — repli de `find_father`) → autofécondation.

    Par caractère (σ_A = diversité additive de l'espèce MÈRE) :
      croisé       : â = (a_m + a_p')/2 ; σ_s² = ½·σ_A²·(1 − (F_m+F_p)/2) ; F = 0
      autofécondé  : â = a_m            ; σ_s² = ½·σ_A²·(1 − F_m)         ; F = (1+F_m)/2
      a = borne(â + z₁·σ_s + z₂·√H_MUT·σ_A)
    σ_s = BRASSAGE (échantillonnage mendélien) : il s'éteint quand la lignée se
    fixe (F → 1) ; le FILET de mutation, lui, ne s'éteint jamais.

    Introgression (père d'une AUTRE espèce de la même famille, l'enfant reste de
    l'espèce de la mère) : le père contribue par son ÉCART à SON neutre, ajouté au
    neutre de la mère — a_p' = neutre_m + (a_p − neutre_p). Pour un père de même
    espèce, a_p' = a_p. Elle peut pousser un caractère hors de la plage normale
    (vigueur hybride) ; seule `borne` tient les limites dures.
    """
    r, c = mother.position
    if father is not None and _hash_noise(seed, week, r + _CANAL_CHOIX, c) \
            < mother.gene("autofecondation"):
        father = None                    # autofécondation malgré un père à portée
    cls_m, F_m = mother.plant_class, mother.F
    if father is None:
        F_enfant, brassage = 0.5 * (1.0 + F_m), 0.5 * (1.0 - F_m)
    else:
        cls_p = father.plant_class
        F_enfant, brassage = 0.0, 0.5 * (1.0 - 0.5 * (F_m + father.F))
    genes = {}
    for i, g in enumerate(GENE_NAMES):
        n_m, s_a = neutre(g, cls_m), sigma_a(g, cls_m)
        a_m = mother.gene(g)
        if father is None:
            base = a_m
        else:
            base = 0.5 * (a_m + n_m + father.gene(g) - neutre(g, cls_p))
        z1 = hash_gauss(seed, week * 29 + i, r, c, k=4 * i)
        z2 = hash_gauss(seed, week * 29 + i, r + _CANAL_FILET, c, k=4 * i)
        genes[g] = borne(g, base + s_a * (z1 * math.sqrt(brassage)
                                          + z2 * math.sqrt(H_MUT)))
    return genes, F_enfant


def child_genes(mother, father, seed, week) -> dict:
    """Vecteur de gènes de l'enfant seul (cf. `heredite`, qui rend aussi son F).
    Gardé pour les lecteurs qui n'ont pas besoin de la consanguinité."""
    return heredite(mother, father, seed, week)[0]


def child_expression(mother) -> dict:
    """
    Priming transgénérationnel (sprint plasticité ④ — conception §2.5, P2).
    L'enfant n'hérite PAS du génotype seul : il naît avec un ÉTAT D'EXPRESSION
    initial transmis par la MÈRE SEULE (épigénétique maternelle ; le père est
    souvent None en autofécondation, et la voie maternelle domine chez les
    plantes). Le génotype reste géré par `child_genes` — ceci est orthogonal.

        child.expression[g] = 1.0 + PRIMING_FRAC × (mother.expression[g] − 1.0)

    `PRIMING_FRAC < 1` atténue l'alerte à chaque transmission → moteur de l'OUBLI
    ÉMERGENT (cf. §2.5) : sans stress, la lignée retombe au neutre en 2-3
    générations ; sous stress persistant, chaque génération recharge sa mémoire
    et le priming tient. Mère neutre (expression toute à 1.0) ⇒ enfant neutre.
    Ne porte QUE les gènes adaptogènes (les seuls dotés d'une expression plastique).
    """
    return {g: 1.0 + PRIMING_FRAC * (mother.expression.get(g, 1.0) - 1.0)
            for g in ADAPTOGENIC_GENES}
