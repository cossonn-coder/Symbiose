"""
SYMBIOSE — sim/bilan.py
Le BILAN CARBONE hebdomadaire d'une plante (D140 G, sprint plante vivante ①,
`docs/vegetal/sante/conception_plante_vivante.md` §1).

📖 Pédagogie — une plante n'a pas de « points de vie » : elle vit de ce qu'elle
produit. Chaque semaine, en semaines d'entretien de la plante elle-même :

    P   = photo_max × feuillage × présence_phéno × f_lum × f_eau × f_T × f_nut × f_allelo
    E   = Q10^((T − 15)/10) × (DORMANCE si elle dort)          # respiration d'entretien
    X   = K_EXSUD × P × mycorhization                           # part racinaire (sucres
                                                                #  donnés au sol/champignons)
    net = P − E − X

Si `net ≥ 0` la plante remplit ses réserves ; sinon elle y puise. Une plante qui a
perdu des feuilles les refait en saison, payées sur ses réserves. Ici, les facteurs
sont des RAMPES (au lieu des booléens `ok_hum`/`ok_temp` de l'avancement de stade) :
la photosynthèse baisse progressivement, elle ne s'éteint pas d'un coup.

`croissance._update_physiology` appelle `semaine_bilan` après avoir calculé ses
facteurs (lumière effective, nutrition, allélopathie : RÉUTILISÉS, pas recalculés).
Depuis le ② ces états FONT la vie : `vitalite` en est la lecture, `reserves = 0` =
famine, le surplus pilote la croissance et le facteur limitant nomme la stagnation.

Fonctions PURES (sauf `maj_bilan`, qui écrit les 3 champs de la plante), zéro RNG
(philo #3). Couche `sim` : lit `plants` et `fields` (constantes), jamais `sim.engine`.
"""

from __future__ import annotations

from fields import HUM_NOYE
from plants.physiologie import parametres_bilan, capacite_reserve

# --- Entretien ---------------------------------------------------------------
Q10 = 2.0              # la respiration double tous les 10 °C (ordre de grandeur classique)
T_REF = 15.0           # °C où l'entretien vaut 1 (définition de l'unité)
DORMANCE = 0.1         # une plante qui dort (bourgeons fermés, souche) respire ~10 fois moins
# --- Production --------------------------------------------------------------
# La photosynthèse SATURE bien avant le plein soleil (une feuille de lumière sature
# vers 30-50 % du plein soleil) : au-delà de cette lumière effective (lumière reçue ×
# tolérance d'ombre), plus de lumière ne gagne rien. 0,4 mesuré au ① (0,6 laissait
# les plantes de mi-ombre du monde `full` en déficit tout l'été).
LUM_SATURATION = 0.4
T_RAMPE_FROID = 8.0    # °C entre `temp_min_growth` (P = 0) et l'optimum (P plein)
SEC_RAMPE = 2.0        # P plein à SEC_RAMPE × seuil sec (`0,15/tolerance_secheresse`)
HUM_SATURE = 3.0       # sol saturé (borne haute du champ d'humidité)
# --- Part racinaire et refeuillaison ------------------------------------------
K_EXSUD = 0.10         # ~10 % de la production part en exsudats + paiement mycorhizien
REFEUIL_MAX = 0.15     # part du feuillage refaite au plus par semaine (× gène `repousse`)
# Au plus cette part des réserves COURANTES engagée par semaine dans la refeuillaison
# (②) : une plante ne se tue pas à refaire ses feuilles. Mesuré au ② : sans borne, une
# bourse-à-pasteur broutée vidait ses réserves d'un coup (bilan pourtant positif).
REFEUIL_PART_RESERVES = 0.5


def _rampe(x: float, x0: float, x1: float) -> float:
    """0 en x0, 1 en x1, linéaire entre (x1 > x0)."""
    return max(0.0, min(1.0, (x - x0) / (x1 - x0)))


def f_lum(light_eff: float) -> float:
    """Lumière : `light_eff` (déjà calculé par la physiologie) saturé à LUM_SATURATION."""
    return min(1.0, light_eff / LUM_SATURATION)


def f_eau(plant, hum_percue: float) -> float:
    """Eau : rampe par le BAS sur le seuil sec du gène `tolerance_secheresse` (même
    seuil que `ok_hum`), par le HAUT au-delà de `HUM_NOYE` (sol noyé), amortie par
    les tolérances à l'asphyxie (gène × constitution d'espèce : l'aulne y tient)."""
    seuil_sec = 0.15 / plant.expressed_gene("tolerance_secheresse")
    f = _rampe(hum_percue, seuil_sec, SEC_RAMPE * seuil_sec)
    if hum_percue > HUM_NOYE:
        tol = (plant.expressed_gene("tolerance_asphyxie")
               * plant.plant_class.asphyxie_tolerance_base)
        exces = (hum_percue - HUM_NOYE) / (HUM_SATURE - HUM_NOYE) / tol
        f *= max(0.0, 1.0 - exces)
    return f


def f_temp(plant, temp: float, t_feuille: float) -> float:
    """Chaleur : rampe de `temp_min_growth` à l'optimum (T ressentie, comme `ok_temp`),
    plateau, puis fermeture de la feuille entre `lim_chaud` et `lim_brul` (plage D139).
    Pourquoi jusqu'à `lim_brul` et pas un arrêt net à `lim_chaud` : `t_feuille` est le
    PIC du jour le plus chaud de la semaine ; à ce pic la feuille ferme ses stomates
    aux heures chaudes, pas toute la semaine. Mesuré au ① (full, seed 42) : un arrêt
    net à `lim_chaud` éteignait la production de la plupart des herbacées tout l'été
    (pic de feuille 29-30 °C, `lim_chaud` 28-30 °C)."""
    froid, chaud = rampes_thermiques(plant, temp, t_feuille)
    return froid * chaud


def rampes_thermiques(plant, temp: float, t_feuille: float) -> tuple[float, float]:
    """Les deux bords de `f_temp`, séparés (le plus bas nomme la stagnation, ②)."""
    t_min = plant.plant_class.temp_min_growth
    return (_rampe(temp, t_min, t_min + T_RAMPE_FROID),
            1.0 - _rampe(t_feuille, plant.lim_chaud(), plant.lim_brul()))


def entretien(t_air: float, dormante: bool, presence: float = 1.0) -> float:
    """E en semaines d'entretien : Q10 autour de T_REF, réduit en dormance. Hors
    dormance, l'activité suit la part de feuillage EN PLACE (② : un arbre qui
    débourre n'a pas encore les feuilles à entretenir — mesuré au ②, sans cela un
    semis de pommier ou un trèfle se vidaient pendant les semaines de débourrement,
    production × présence mais entretien plein) : de DORMANCE (nu) à 1 (feuillé)."""
    e = Q10 ** ((t_air - T_REF) / 10.0)
    if dormante:
        return e * DORMANCE
    return e * (DORMANCE + (1.0 - DORMANCE) * presence)


def bilan(plant, presence: float, f_l: float, f_e: float, f_t: float,
          f_nut: float, f_allelo: float, t_air: float, dormante: bool) -> float:
    """Solde net P − E − X de la semaine (semaines d'entretien). PUR."""
    p = (parametres_bilan(plant.plant_class)["photo_max"] * plant.feuillage
         * presence * f_l * f_e * f_t * f_nut * f_allelo)
    x = K_EXSUD * p * plant.gene("mycorhization")
    return p - entretien(t_air, dormante, presence) - x


def maj_bilan(plant, net: float, en_vegetation: bool) -> float:
    """Applique le solde : réserves ± net/C (bornées [0, 1]), puis refeuillaison
    payée sur les réserves si du feuillage manque et que la plante est en saison.
    Renvoie le SURPLUS (semaines d'entretien) : ce qui reste du solde positif une
    fois les réserves remplies — c'est lui qui nourrit la croissance (②)."""
    cap = max(1e-6, capacite_reserve(plant))
    plant.bilan_net = net
    avant = plant.reserves
    plant.reserves = max(0.0, min(1.0, plant.reserves + net / cap))
    surplus = max(0.0, net - (plant.reserves - avant) * cap)
    if en_vegetation and plant.feuillage < 1.0 and plant.reserves > 0.0:
        cout = parametres_bilan(plant.plant_class)["cout_feuillage"]
        d = min(1.0 - plant.feuillage, REFEUIL_MAX * plant.gene("repousse"),
                REFEUIL_PART_RESERVES * plant.reserves * cap / cout)   # sans s'épuiser
        plant.feuillage += d
        plant.reserves = max(0.0, plant.reserves - cout * d / cap)
    return surplus


def facteur_limitant(f_l: float, f_e: float, froid: float, chaud: float,
                     hum_percue: float) -> str:
    """Nom du facteur de production le plus BAS (log « stagne (…) » de l'avancement
    de stade) : ombre / froid / chaud / sec / noyé ; "" si aucun ne limite (toutes
    les rampes pleines). À égalité, le premier dans cet ordre (une feuille à 54 °C sur
    sol sec stagne « chaud »). Pur."""
    eau = "noyé" if hum_percue > HUM_NOYE else "sec"
    val, nom = min(((f_l, "ombre"), (froid, "froid"), (chaud, "chaud"), (f_e, eau)),
                   key=lambda t: t[0])
    return nom if val < 1.0 else ""


def semaine_bilan(plant, *, saison: str, presence: float, light_eff: float,
                  hum_percue: float, temp: float, t_feuille: float, t_air: float,
                  f_nut: float, f_allelo: float, declin: bool = False) -> float | None:
    """Une semaine de bilan pour `plant`, à partir des lectures DÉJÀ faites par la
    physiologie. Dormante = plus de feuilles (caduc nu) ou vivace qui dort l'hiver ;
    en végétation = hors hiver, feuillage en place, éveillée.

    `declin` (② — horloge interne de fin de vie : fin de cycle d'une annuelle, sa
    production part dans ses GRAINES ; vieux sujet en sénescence avancée) : plus
    rien ne REMPLIT les réserves (seul un déficit les touche) — sans quoi les crans
    de fin de vie (`mortalite`, retraits de réserves) seraient rendus chaque semaine
    par la photosynthèse et la plante ne finirait jamais.

    Renvoie le SURPLUS de croissance, ou None hors végétation (la croissance est
    gelée : un arbre ne « rapetisse » pas l'hiver). Mémorise le facteur limitant."""
    f_l, f_e = f_lum(light_eff), f_eau(plant, hum_percue)
    froid, chaud = rampes_thermiques(plant, temp, t_feuille)
    # Dormante : caduc nu, vivace qui dort l'hiver, OU (②) QUIESCENTE PAR LE FROID —
    # sous sa température de croissance, la plante ne produit rien et ralentit son
    # métabolisme (elle attend). Mesuré au ② : sans elle, un persistant (thym) se
    # vidait l'hiver et un semis de printemps froid mourait de faim la 1re semaine.
    dormante = (presence <= 0.0 or froid <= 0.0
                or (saison == "hiver" and plant.plant_class.winter_strategy == "dormant"))
    plant.limitant = facteur_limitant(f_l, f_e, froid, chaud, hum_percue)
    net = bilan(plant, presence, f_l, f_e, froid * chaud, f_nut, f_allelo, t_air, dormante)
    if declin:
        net = min(net, 0.0)
    en_veg = saison != "hiver" and not dormante
    surplus = maj_bilan(plant, net, en_vegetation=en_veg)
    return surplus if en_veg else None
