"""
SYMBIOSE — tests/test_courrier_enseigne.py
Les portes de technique POSÉES par le tronçon ② du sprint ACCÈS AUX GESTES
(`docs/joueur/gestes/conception_refonte_palette.md` §3.2-§3.3) : le COURRIER qui
enseigne et les OBSERVATIONS du jardin. Le tronçon ① avait écrit la table des portes
(`PORTES_TECHNIQUE`) ; ici on vérifie que quelqu'un pose réellement les marqueurs
qu'elle lit.

Fichier à part de `tests/test_quetes.py` (qui couvre le moteur de quêtes lui-même et
approche la bande de taille) : une responsabilité, « une lettre ou une observation
ouvre un geste ».

Vérifie :
  A. Lettre → technique → geste ouvert (pots, palissage), avec la notification.
  B. Greffe : la lettre SEULE ne suffit pas, le greffoir SEUL non plus ; les deux,
     dans n'importe quel ordre, ouvrent `greffer`.
  C. Essaim : la lettre ouvre l'apiculture et ne pose AUCUNE ruche.
  D. Bac d'Odette : posséder vaut avoir posé → composter, retourner, epandre.
  E. Aucune lettre ne donne un geste sans désir comblé.
  F. Observation `merle_seme` (journal du tick) → `poser_perchoir`.
  G. Observation `grimpante_sans_appui` (état après tick) → `poser_tuteur`.
  H. Sans joueur ni monde : aucune clé créée (golden neutre).

Usage (depuis data/code/) :
  python3 -m tests.test_courrier_enseigne
"""
from __future__ import annotations

import sys

from plants.base import PlantInstance
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise as M
from sim import outils, quetes as Q, vigueur
from sim.actions import deblocage as D
from sim.growth.phases import grow_plant
from sim.quetes_corpus import QUETES_CORPUS
from tools.simserver import maitrise_pont as MP

_results = []
P = "joueur_test"


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class _Plante:
    """Plante-cible minimale lue par les conditions de quête (duck-typing, comme
    `tests/test_quetes.py`)."""

    def __init__(self, cle, current_height=0.0, floraison=0.0):
        self.plant_class = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}[cle]
        self.is_alive = True
        self.current_height = current_height
        self.floraison = floraison


class _Tuile:
    def __init__(self, plants):
        self.plants = list(plants)


def _combler(gs, qid):
    """Pose la lettre du CORPUS puis comble son désir par le chemin réel de sa
    famille de condition (hook geste, ou lecture du snapshot)."""
    quete = QUETES_CORPUS[qid]
    Q.ajouter_quete(gs, quete)
    cond = quete.condition
    if cond[0] == "recolte_cumulee":
        for _ in range(cond[2]):
            Q.notifier_geste(gs, P, cond[1], _Plante(cond[3]))
    else:
        n = cond[2] if cond[0] != "hauteur_min" else 1
        gs["tiles"] = [_Tuile(_Plante(cond[1], current_height=1000.0, floraison=1.0)
                              for _ in range(int(n)))]
        Q.evaluer_etat(gs)
    return Q.est_accomplie(gs, qid)


def test_lettre_ouvre_un_geste():
    print("\n[A] lettre → technique → geste ouvert")
    gs = {"week": 8, "log": []}
    check("désir d'Amélie comblé", _combler(gs, "lettre_pots_amelie"))
    check("avant la remise, rien n'est ouvert", not D.est_debloque(gs, P, "poser_pot"))
    Q.remettre_recompenses(gs, P)
    check("technique jardinage_hors_sol découverte",
          M.palier(gs, P, "jardinage_hors_sol") == 1)
    check("poser_pot et poser_bac_culture ouverts",
          D.est_debloque(gs, P, "poser_pot") and D.est_debloque(gs, P, "poser_bac_culture"))
    check("gestes rangés pour la notification du pont",
          gs["gestes_debloques_recents"][P] == ["poser_bac_culture", "poser_pot"],
          f"{gs.get('gestes_debloques_recents')}")
    Q.remettre_recompenses(gs, P)
    check("versée une seule fois (idempotent)",
          gs["gestes_debloques_recents"][P] == ["poser_bac_culture", "poser_pot"])

    gs = {"week": 12, "log": []}
    check("désir de Gaston comblé", _combler(gs, "lettre_haricots_rames_gaston"))
    Q.remettre_recompenses(gs, P)
    check("palissage découvert → poser_tuteur ouvert",
          M.palier(gs, P, "palissage") == 1 and D.est_debloque(gs, P, "poser_tuteur"))


def test_greffe_lettre_et_greffoir():
    print("\n[B] greffe : la lettre ET le greffoir")
    gs = {"week": 22, "log": []}
    vigueur.ensure_player(gs, P)
    check("désir d'Augustin comblé", _combler(gs, "lettre_greffe_augustin"))
    Q.remettre_recompenses(gs, P)
    check("la lettre pose le marqueur `lettre_greffe`", D._a_evenement(gs, P, "lettre_greffe"))
    check("lettre seule : technique inconnue, greffer fermé",
          M.palier(gs, P, "greffe") == 0 and not D.est_debloque(gs, P, "greffer"))
    check("achat du greffoir", outils.acquerir_outil(gs, P, "greffoir"))
    check("lettre + greffoir → greffer ouvert", D.est_debloque(gs, P, "greffer"))
    # Ordre inverse : l'outil d'abord, le savoir ensuite.
    gs = {"week": 22, "log": []}
    vigueur.ensure_player(gs, P)
    outils.acquerir_outil(gs, P, "greffoir")
    check("greffoir seul : greffer fermé", not D.est_debloque(gs, P, "greffer"))
    _combler(gs, "lettre_greffe_augustin")
    Q.remettre_recompenses(gs, P)
    check("greffoir puis lettre → greffer ouvert", D.est_debloque(gs, P, "greffer"))


def _monde():
    """Monde minimal mais réel (tuile + eco), destination des cadeaux matériels."""
    from fields import init_eco
    from world import Tile
    tile = Tile(tile_id="t0", soil_type="terre")
    return {"week": 14, "seed": 42, "log": [], "tiles": [tile],
            "eco": {tile.tile_id: init_eco(tile.tile_id, tile.grid_rows, tile.grid_cols)}}


def test_essaim_et_bac():
    print("\n[C] essaim : l'apiculture s'ouvre, aucune ruche n'est posée")
    gs = _monde()
    eco = gs["eco"]["t0"]
    tuiles = gs["tiles"]
    check("désir de Bertrand comblé", _combler(gs, "lettre_essaim_bertrand"))
    gs["tiles"] = tuiles                     # on rend le vrai monde avant la remise
    Q.remettre_recompenses(gs, P)
    check("apiculture découverte → poser_ruche ouvert",
          M.palier(gs, P, "apiculture") == 1 and D.est_debloque(gs, P, "poser_ruche"))
    check("aucune structure posée par la lettre", list(eco.structures) == [],
          f"{eco.structures}")
    check("recolter_miel attend une ruche posée", not D.est_debloque(gs, P, "recolter_miel"))

    print("\n[D] bac d'Odette : posséder vaut avoir posé")
    gs = _monde()
    check("désir d'Odette comblé", _combler(gs, "lettre_bac_compost_odette"))
    Q.remettre_recompenses(gs, P)
    check("un bac est posé", any(s.kind == "bac" for s in gs["eco"]["t0"].structures))
    check("compostage découvert", M.palier(gs, P, "compostage") == 1)
    check("composter, retourner, epandre ouverts",
          all(D.est_debloque(gs, P, v) for v in ("composter", "retourner", "epandre")))
    # Hors d'un vrai monde le bac n'est pas posé : le marqueur ne l'est pas non plus.
    gs = {"week": 14, "log": []}
    _combler(gs, "lettre_bac_compost_odette")
    Q.remettre_recompenses(gs, P)
    check("pas de bac posé → pas de marqueur (rien d'ouvert à vide)",
          not D.est_debloque(gs, P, "composter"))


def test_jamais_sans_desir():
    print("\n[E] aucune lettre ne donne un geste sans désir comblé")
    enseignent = {qid: q for qid, q in QUETES_CORPUS.items()
                  if q.recompense and q.recompense[0] == "technique"}
    check("quatre lettres enseignent", len(enseignent) == 4, f"{sorted(enseignent)}")
    check("chacune porte un désir atteignable et un jalon de saison",
          all(Q.est_atteignable(q.condition) and q.declencheur
              and q.declencheur[0] == "saison" for q in enseignent.values()))
    gs = {"week": 30, "log": []}
    for q in enseignent.values():
        Q.ajouter_quete(gs, q)               # lettres arrivées, désirs NON comblés
    check("la remise ne verse rien", Q.remettre_recompenses(gs, P) == [])
    check("aucune technique, aucun marqueur, aucun geste",
          "maitrise" not in gs and "marqueurs_ecolo" not in gs
          and "gestes_debloques" not in gs, f"{sorted(gs)}")


def test_observation_merle():
    print("\n[F] observation : le merle prend des fruits → perchoir")
    gs = {"week": 30, "log": []}
    MP.observer_apres_tick(gs, P, ["    🌱 rien de spécial"])
    check("sans merle : pas de marqueur", not D._a_evenement(gs, P, "merle_seme"))
    # Ligne EXACTE du tick (`sim/zoochorie.merle_prend`).
    MP.observer_apres_tick(gs, P, ["    🐦 Merle : 3 fruits pris sur Cerisier@(2, 4)"])
    check("la ligne du merle pose `merle_seme`", D._a_evenement(gs, P, "merle_seme"))
    check("technique perchoir découverte → poser_perchoir ouvert",
          M.palier(gs, P, "perchoir") == 1 and D.est_debloque(gs, P, "poser_perchoir"))
    check("notification rangée",
          gs.get("gestes_debloques_recents", {}).get(P) == ["poser_perchoir"])
    gs = {"week": 30, "log": []}
    MP.observer_apres_tick(gs, P, ["    🐦 Geai : 2 fruits cachés depuis Chêne@(1, 1)"])
    check("le geai ne pose pas le marqueur du merle",
          not D._a_evenement(gs, P, "merle_seme"))


def _haricot(semaines=30):
    """Un vrai haricot poussé par le vrai chemin de croissance, sans appui."""
    plant = PlantInstance(plant_class=PLANT_CATALOGUE["haricot"], position=(0, 0))
    plant.form_seed = 7
    for w in range(semaines):
        grow_plant(plant, 42, w)
    return plant


def test_observation_grimpante():
    print("\n[G] observation : une grimpante connue pousse sans appui → palissage")
    haricot = _haricot()
    gs = {"week": 30, "log": [], "tiles": [_Tuile([haricot])]}
    check("espèce jamais survolée : rien", not MP._grimpante_sans_appui(gs, P))
    M.decouvrir(gs, P, "haricot")            # le joueur a survolé un haricot
    check("espèce connue, tige libre et trop haute : vu",
          MP._grimpante_sans_appui(gs, P))
    haricot.support = (object(), 180.0)
    check("accrochée à un appui : rien", not MP._grimpante_sans_appui(gs, P))
    haricot.support = None
    gs["tiles"] = [_Tuile([_haricot(semaines=3)])]
    check("encore assez courte pour tenir seule : rien",
          not MP._grimpante_sans_appui(gs, P))
    # Le hook complet tourne sur un vrai monde (la détection de maîtrise le balaie).
    gs = _monde()
    gs["tiles"][0].plants.append(haricot)
    M.decouvrir(gs, P, "haricot")
    MP.observer_apres_tick(gs, P, [])
    check("le hook pose `grimpante_sans_appui`",
          D._a_evenement(gs, P, "grimpante_sans_appui"))
    check("palissage découvert → poser_tuteur ouvert",
          M.palier(gs, P, "palissage") == 1 and D.est_debloque(gs, P, "poser_tuteur"))
    check("marqueur acquis : le balayage ne tourne plus",
          not MP._grimpante_sans_appui(gs, P))


def test_noop_golden():
    print("\n[H] sans joueur ni monde : aucune clé créée")
    gs = {}
    check("lecture pure sur un game_state vide",
          not MP._grimpante_sans_appui(gs, P) and gs == {}, f"{sorted(gs)}")
    check("les deux marqueurs d'observation sont au registre",
          MP.MARQUEURS_OBSERVATION == {"merle_seme", "grimpante_sans_appui"})


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Le courrier enseigne, le jardin montre (accès aux gestes ②)")
    print("=" * 60)
    test_lettre_ouvre_un_geste()
    test_greffe_lettre_et_greffoir()
    test_essaim_et_bac()
    test_jamais_sans_desir()
    test_observation_merle()
    test_observation_grimpante()
    test_noop_golden()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)
