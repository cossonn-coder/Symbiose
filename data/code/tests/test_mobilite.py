"""
SYMBIOSE — tests/test_mobilite.py
Tronçon ④ du sprint pots/bacs : MOBILITÉ des pots + BACS N×M immobiles.

On prouve (CONCEPTION_POTS_BACS_SUBSTRATS §4) :
  - `poser_pot`/`poser_bac` créent un conteneur REMPLI, l'ajoutent à la liste monde
    `game_state["containers"]` et DÉBITENT la Vigueur joueur (binaire) ;
  - `deplacer_pot` change la position → la LUMIÈRE reçue est recalculée au prochain
    tick (un pot déplacé sous l'ombre de la maison reçoit MOINS) ; il coûte de la
    Vigueur AU JOUEUR SEUL, **sans aucun choc/malus sur la plante** (philo #2 : le
    mini-sol et la plante voyagent intacts) ;
  - un BAC refuse le déplacement (immobile) → AUCUNE Vigueur dépensée.

Golden NEUTRE par construction : ces gestes peuplent la liste monde, mais le smoke
n'en pose aucun → la boucle 17b itère `[]`. Ce test vit à part (event-driven).

Lancement : depuis `data/code/`, `python3 -m tests.test_mobilite`.
"""

from __future__ import annotations

from sim import actions as A
from sim import vigueur as V
from world import House


def _gs():
    """game_state minimal pour les gestes Vigueur (joueur + maison)."""
    gs = {"current_player": "joueur_1", "house": House()}
    V.ensure_player(gs, "joueur_1")
    return gs


def test_poser_pot_debite_vigueur_et_remplit_liste():
    """`poser_pot` ajoute un conteneur à la liste monde ET débite la Vigueur."""
    gs = _gs()
    v0 = V.ensure_player(gs, "joueur_1")["courante"]
    ctn = A.poser_pot(gs, "joueur_1", "terreau", 10.0, 1000.0, 400.0)
    assert ctn is not None and ctn.kind == "pot" and ctn.mobile
    assert gs["containers"] == [ctn]
    v1 = V.ensure_player(gs, "joueur_1")["courante"]
    assert v1 < v0, (v0, v1)              # Vigueur débitée (MODÉRÉ)
    print(f"OK poser_pot : conteneur dans la liste, Vigueur {v0:.0f} → {v1:.0f}")


def test_poser_bac_immobile_nxm():
    """`poser_bac` (culture) : conteneur N×M IMMOBILE (mobile=False), grand volume."""
    gs = _gs()
    bac = A.poser_bac_culture(gs, "joueur_1", "compost", 200.0, 800.0, 800.0,
                              rows=2, cols=2)
    assert bac is not None and bac.kind == "bac" and not bac.mobile
    assert bac.eco.rows == 2 and bac.eco.cols == 2
    assert bac.fond_ouvert is True       # couplé tuile dessous par défaut (effet en ⑤)
    print("OK poser_bac : bac 2×2 immobile, fond ouvert stocké")


def test_deplacer_pot_recalcule_lumiere():
    """`deplacer_pot` : la LUMIÈRE reçue suit la nouvelle position (ombre maison).
    Un pot en plein soleil (loin) déplacé au NORD de la maison reçoit MOINS."""
    gs = _gs()
    # Pose en plein soleil, loin de la maison [600,600]→[1400,1400].
    ctn = A.poser_pot(gs, "joueur_1", "terreau", 10.0, 2000.0, 2000.0)
    ctn.tick_chimie("ete", house=gs["house"], nebulosite=0.0)
    light_soleil = ctn.eco.lumiere.at_plot(0, 0)
    # Déplace JUSTE au nord de la maison (ombre portée vers le nord = y faible).
    ok = A.deplacer_pot(gs, "joueur_1", ctn, 1000.0, 400.0)
    assert ok and ctn.x_cm == 1000.0 and ctn.y_cm == 400.0
    ctn.tick_chimie("ete", house=gs["house"], nebulosite=0.0)
    light_ombre = ctn.eco.lumiere.at_plot(0, 0)
    assert light_ombre < light_soleil, (light_soleil, light_ombre)
    print(f"OK deplacer_pot : lumière recalculée {light_soleil:.3f} (soleil) → "
          f"{light_ombre:.3f} (ombre maison)")


def test_deplacer_pot_cout_joueur_sans_choc_plante():
    """Philo #2 : déplacer coûte de la Vigueur JOUEUR, mais NE TOUCHE PAS la plante
    (aucun choc/malus). On capture l'état complet de la plante avant/après le seul
    déplacement (pas de tick entre les deux) : il est IDENTIQUE."""
    gs = _gs()
    Tomato = __import__("plants").PLANT_CATALOGUE["tomate"]
    from world import planter_dans
    ctn = A.poser_pot(gs, "joueur_1", "terreau", 10.0, 2000.0, 2000.0)
    plant = planter_dans(ctn, Tomato)
    # Empreinte de l'état plante AVANT déplacement (les attributs susceptibles d'un choc).
    avant = (plant.current_height, plant.is_alive, plant.x_cm, plant.y_cm,
             plant.shade_memory, plant.drought_memory, plant.growth_factor,
             len(plant.segments))
    v0 = V.ensure_player(gs, "joueur_1")["courante"]
    ok = A.deplacer_pot(gs, "joueur_1", ctn, 1000.0, 400.0)
    v1 = V.ensure_player(gs, "joueur_1")["courante"]
    apres = (plant.current_height, plant.is_alive, plant.x_cm, plant.y_cm,
             plant.shade_memory, plant.drought_memory, plant.growth_factor,
             len(plant.segments))
    assert ok and v1 < v0                 # Vigueur joueur débitée
    assert avant == apres, (avant, apres)  # AUCUN choc plante (philo #2)
    print(f"OK philo #2 : Vigueur joueur {v0:.0f}→{v1:.0f}, état plante INCHANGÉ")


def test_bac_refuse_deplacement_zero_vigueur():
    """Un BAC est immobile : `deplacer_pot` refuse EN AMONT → AUCUNE Vigueur dépensée
    (modèle `epandre` jauge vide)."""
    gs = _gs()
    bac = A.poser_bac_culture(gs, "joueur_1", "terreau", 200.0, 800.0, 800.0)
    v0 = V.ensure_player(gs, "joueur_1")["courante"]
    ok = A.deplacer_pot(gs, "joueur_1", bac, 100.0, 100.0)
    v1 = V.ensure_player(gs, "joueur_1")["courante"]
    assert ok is False
    assert v1 == v0, (v0, v1)             # refus en amont → rien débité
    assert bac.x_cm == 800.0 and bac.y_cm == 800.0   # position intacte
    print(f"OK bac immobile : refus sans coût (Vigueur {v0:.0f} == {v1:.0f})")


def test_deplacer_pot_vigueur_insuffisante():
    """Vigueur épuisée → le pot N'est PAS déplacé (geste binaire, position intacte)."""
    gs = _gs()
    ctn = A.poser_pot(gs, "joueur_1", "terreau", 10.0, 500.0, 500.0)
    V.ensure_player(gs, "joueur_1")["courante"] = 1.0   # quasi vide
    ok = A.deplacer_pot(gs, "joueur_1", ctn, 1000.0, 400.0)
    assert ok is False
    assert ctn.x_cm == 500.0 and ctn.y_cm == 500.0
    print("OK Vigueur insuffisante : pot non déplacé, position intacte")


def test_determinisme():
    """Deux séquences identiques (pose + déplacement) → même état (zéro RNG)."""
    def seq():
        gs = _gs()
        ctn = A.poser_pot(gs, "joueur_1", "terreau", 10.0, 2000.0, 2000.0)
        A.deplacer_pot(gs, "joueur_1", ctn, 1000.0, 400.0)
        ctn.tick_chimie("ete", house=gs["house"], nebulosite=0.0)
        return (ctn.x_cm, ctn.y_cm, ctn.eco.lumiere.at_plot(0, 0),
                V.ensure_player(gs, "joueur_1")["courante"])
    assert seq() == seq()
    print("OK déterminisme : deux séquences identiques → même état")


if __name__ == "__main__":
    test_poser_pot_debite_vigueur_et_remplit_liste()
    test_poser_bac_immobile_nxm()
    test_deplacer_pot_recalcule_lumiere()
    test_deplacer_pot_cout_joueur_sans_choc_plante()
    test_bac_refuse_deplacement_zero_vigueur()
    test_deplacer_pot_vigueur_insuffisante()
    test_determinisme()
    print("\n=== test_mobilite : TOUS OK ===")
