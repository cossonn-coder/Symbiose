"""
SYMBIOSE — tests/bancs/test_acces_gestes.py
Oracle du banc `acces_gestes` (sprint ACCÈS AUX GESTES ④) : le test DE BOUT EN BOUT
de la refonte (`docs/joueur/gestes/conception_refonte_palette.md` §3).

`tests/test_atteignabilite.py` raisonne sur les TABLES (point fixe symbolique). Ici
on JOUE : un serveur, le banc, et rien que des commandes du pont, dans la forme de
cible que la vue envoie. Partant des seuls gestes de base, tous les gestes du moteur
doivent finir ouverts.

Règle du jeu de l'oracle : `_geste` REFUSE d'envoyer un verbe fermé. Le pont, lui,
l'exécuterait (pas de gating dur) ; la palette ne le propose pas. Sans ce garde, la
preuve serait creuse : `bouturer` envoyé à la main s'ouvrirait tout seul.

Les quatre familles de portes sont franchies :
  A. départ : gestes de base seulement, aucun état de maîtrise ;
  B. geste de base voisin : glaner ×3, stock de feuilles, creuser, pincer + semer ;
  C. Atelier : les neuf outils ;
  D. chaînes internes : poser ouvre l'usage (bac, pile, pot, tuteur), couper, recéper ;
  E. courrier : Gaston comblé à l'ouverture, Augustin (+ greffoir), Bertrand ;
  F. observation : grimpante sans appui (le jasmin, une fois survolé), merle ;
  G. bilan : tout `COUTS` ∪ `GESTE_UNLOCK` ouvert, snapshot d'accord, plus un pressenti ;
  H. les neuf gestes que la vue ne connaissait pas, exécutés avec SES cibles.

Usage (depuis data/code/) : python3 -m tests.bancs.test_acces_gestes
"""
import sys

from bancs import acces_gestes as B
from fields.ecofields import PAILLAGE_DOSE
from sim.actions import deblocage as D
from sim.actions.couts import COUTS
from sim.outils import OUTILS
from tools.simserver.server import SimServer

SEMAINES_MAX = 20           # plafond d'attente du courrier et du merle
PLOT_CM = 50.0
_res = []


def check(nom, ok, info=""):
    _res.append((nom, bool(ok)))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


class Partie:
    """Un serveur monté sur le banc, et les trois façons de désigner de la vue."""

    def __init__(self):
        self.srv = SimServer()
        assert self.srv.cmd_init({"cmd": "init", "config": "acces_gestes", "seed": 42})["ok"]
        self.gs = self.srv.engine.game_state
        self.joueur = self.gs["current_player"]

    def ouverts(self) -> set:
        return set(D.gestes_debloques(self.gs, self.joueur))

    def _geste(self, verbe, cible=None, **params):
        """Envoie un geste OUVERT (cf. en-tête). Renvoie le bilan du pont."""
        assert verbe in self.ouverts(), f"{verbe} est fermé : l'oracle ne triche pas"
        r = self.srv.cmd_action({"cmd": "action", "verb": verbe,
                                 "target": cible, "params": params})
        assert r["ok"], r
        return r["result"]

    def plot(self, verbe, rc, **params):            # kind 'q' : {tile, r, c}
        return self._geste(verbe, {"tile": B.NOM, "r": rc[0], "c": rc[1]}, **params)

    def point(self, verbe, rc, **params):           # kinds 'm' et 'p' : point local
        return self._geste(verbe, {"tile": B.NOM, "x_cm": (rc[1] + 0.5) * PLOT_CM,
                                   "y_cm": (rc[0] + 0.5) * PLOT_CM}, **params)

    def acheter(self, outil):
        r = self.srv.cmd_action({"cmd": "action", "verb": "acheter_outil",
                                 "params": {"outil": outil}})
        return r["result"]["applied"]

    def semaine(self):
        assert self.srv.cmd_step_week({"cmd": "step_week"})["ok"]

    def marqueurs(self) -> set:
        return set(self.gs.get("marqueurs_ecolo", {}).get(self.joueur, ()))

    def attendre(self, marqueur) -> int:
        """Semaines passées jusqu'au marqueur (plafonné) ; -1 s'il n'est pas venu."""
        for n in range(SEMAINES_MAX + 1):
            if marqueur in self.marqueurs():
                return n
            self.semaine()
        return -1


def _ouvre(p, nom, avant, attendus):
    neufs = p.ouverts() - avant
    check(nom, set(attendus) <= neufs, f"ouverts : {sorted(neufs)}")


def main():
    p = Partie()

    print("\n[A] départ : rien n'est ouvert d'avance")
    check("gestes ouverts = gestes de base", p.ouverts() == set(D.GESTES_BASE),
          sorted(p.ouverts() - D.GESTES_BASE))
    check("aucune maîtrise, aucun marqueur, aucun outil",
          not p.gs.get("maitrise") and not p.marqueurs()
          and not p.gs.get("actions_faites"))

    print("\n[B] porte « geste de base voisin »")
    avant = p.ouverts()
    for rc in B.LITIERE[:3]:
        check(f"glaner {rc}", p.plot("glaner", rc)["applied"])
    _ouvre(p, "trois glanages → compostage", avant, ("poser_bac", "poser_pile"))
    stock = p.gs.get("mulch_stock", {}).get("feuilles", 0.0)
    _ouvre(p, "stock de feuilles → pailler", avant, ("pailler",))
    check("le stock glané vaut au moins une dose", stock >= PAILLAGE_DOSE, f"{stock:.2f}")
    avant = p.ouverts()
    check("creuser un plot nu", p.plot("creuser", B.PLOT_NU)["applied"])
    _ouvre(p, "creuser → endiguer, dériver", avant, ("endiguer", "deriver"))
    avant = p.ouverts()
    pinces = semis = 0
    while "bouturer" not in p.ouverts() and pinces < 8:
        p.point("pincer", B.LAVANDES[pinces % len(B.LAVANDES)])
        p.point("planter", (9 + semis % 3, 8 + semis // 3), species="tournesol")
        pinces += 1
        semis += 1
    _ouvre(p, "pincer et semer → bouturer", avant, ("bouturer",),)
    print(f"      (taille et semis au palier 2 après {pinces} pincements et {semis} semis)")

    print("\n[C] porte « Atelier »")
    attendu = {
        "secateur": ("couper",), "broyeur": ("broyer",),
        "pots": ("poser_pot", "poser_bac_culture"),
        "tuteurs": ("poser_tuteur", "poser_treillis", "poser_pergola"),
        "voile": ("poser_voile", "poser_cloche", "poser_ombriere"),
        "hache": ("abattre",), "serpe": ("receper",), "pioche": ("entailler",),
        "greffoir": (),                      # il lui faut encore la lettre
    }
    check("l'oracle couvre tous les outils en vente",
          set(attendu) == {o for o, spec in OUTILS.items() if spec.get("offre")},
          sorted(set(OUTILS) ^ set(attendu)))
    for outil, gestes in attendu.items():
        avant = p.ouverts()
        ok = p.acheter(outil)
        check(f"{outil} acheté → {', '.join(gestes) or 'rien encore'}",
              ok and set(gestes) <= p.ouverts() - avant, sorted(p.ouverts() - avant))
    check("greffoir seul : greffer reste fermé", "greffer" not in p.ouverts())

    print("\n[D] chaînes internes : poser ouvre l'usage")
    avant = p.ouverts()
    check("poser_bac", p.plot("poser_bac", (9, 0))["applied"])
    check("poser_pile", p.plot("poser_pile", (10, 0))["applied"])
    _ouvre(p, "bac et pile → composter, retourner, epandre, empiler_bois", avant,
           ("composter", "retourner", "epandre", "empiler_bois"))
    avant = p.ouverts()
    check("couper une lavande", p.point("couper", B.LAVANDES[0])["applied"])
    _ouvre(p, "couper → tailler", avant, ("tailler",))
    avant = p.ouverts()
    r = p._geste("poser_pot", {"x_cm": B.ORIGINE_CM + 475.0, "y_cm": B.ORIGINE_CM + 575.0},
                 substrat="terreau", volume=75.0)
    check("poser_pot (point monde)", r["applied"], r["message"])
    _ouvre(p, "pot → deplacer_pot, planter_conteneur", avant,
           ("deplacer_pot", "planter_conteneur"))
    avant = p.ouverts()
    r = p.point("poser_tuteur", B.JASMIN)
    check("poser_tuteur au pied du jasmin", r["applied"], r["message"])
    _ouvre(p, "tuteur → palisser, poser_perchoir", avant, ("palisser", "poser_perchoir"))
    avant = p.ouverts()
    r = p._geste("receper", {"cote": B.COTE_FORET})
    check("recéper la charmaie qui borde la tuile", r["applied"], r["message"])
    _ouvre(p, "recéper → eteter", avant, ("eteter",))

    print("\n[E] porte « courrier »")
    avant = p.ouverts()
    n = p.attendre("lettre_greffe")
    check("Augustin vient (pommier bien en tige)", n >= 0, f"{n} semaine(s)")
    _ouvre(p, "lettre + greffoir → greffer", avant, ("greffer",))
    avant = p.ouverts()
    n = p.attendre("lettre_essaim")
    check("Bertrand apporte l'essaim (phacélies en fleur)", n >= 0,
          f"{n} semaine(s) de plus [seed 42]")
    _ouvre(p, "essaim → poser_ruche", avant, ("poser_ruche",))
    avant = p.ouverts()
    r = p.plot("poser_ruche", (11, 4))
    check("poser_ruche", r["applied"], r["message"])
    _ouvre(p, "ruche → recolter_miel", avant, ("recolter_miel",))
    lettres = {l["id"]: l for l in p.srv.cmd_courrier({"cmd": "courrier"})["lettres"]}
    check("la lettre de Gaston est comblée (trois haricots)",
          lettres.get("lettre_haricots_rames_gaston", {}).get("accomplie"),
          sorted(lettres))

    print("\n[F] porte « observation »")
    check("jasmin jamais survolé : pas de marqueur",
          "grimpante_sans_appui" not in p.marqueurs())
    # Survol = commande `observer` avec le NOM DE CLASSE, comme la vue.
    assert p.srv.cmd_observer({"cmd": "observer", "species": "Jasmine"})["ok"]
    n = p.attendre("grimpante_sans_appui")
    check("jasmin survolé, tige libre → grimpante_sans_appui", n >= 0, f"{n} semaine(s)")
    n = p.attendre("merle_seme")
    check("le merle prend des cerises → merle_seme", n >= 0,
          f"{n} semaine(s) de plus, semaine {p.gs['week']} [seed 42]")

    print("\n[G] bilan : tout est ouvert")
    tous = set(COUTS) | set(D.GESTE_UNLOCK)
    fermes = tous - p.ouverts()
    check(f"les {len(tous)} gestes du moteur sont ouverts", not fermes, sorted(fermes))
    joueur = p.srv.cmd_snapshot({"cmd": "snapshot"})["snapshot"]["player"]
    check("le snapshot dit la même chose", set(joueur["gestes_debloques"]) == p.ouverts())
    check("plus aucun geste pressenti", joueur["gestes_pressentis"] == [],
          joueur["gestes_pressentis"])
    rangés = {v for f in joueur["familles"]["ordre"] for v in joueur["familles"]["gestes"][f]}
    check("tout geste ouvert a sa famille", p.ouverts() <= rangés,
          sorted(p.ouverts() - rangés))

    print("\n[H] les neuf gestes neufs de la vue, avec ses cibles")
    for verbe, rc in (("poser_treillis", (8, 1)), ("poser_pergola", (8, 2))):
        r = p.point(verbe, rc)
        check(f"{verbe} (point local)", r["applied"], r["message"])
    r = p.point("palisser", B.JASMIN)
    check("palisser le jasmin (plante par position)", r["applied"], r["message"])
    r = p.point("palisser", B.HARICOTS[0])
    check("palisser un haricot → refus motivé, sans coût",
          not r["applied"] and r["cost"] == 0.0, r["message"])
    for verbe, rc in (("poser_voile", (8, 3)), ("poser_cloche", (8, 4)),
                      ("poser_ombriere", (8, 5))):
        r = p.plot(verbe, rc)
        check(f"{verbe} (plot)", r["applied"], r["message"])
    eco = p.gs["eco"][B.NOM]
    ruche = next(i for i, s in enumerate(eco.structures) if s.kind == "ruche")
    r = p._geste("recolter_miel", {"tile": B.NOM, "structure": ruche})
    check("recolter_miel (structure par index) → réponse du moteur",
          isinstance(r["applied"], bool) and r["message"], r["message"])
    r = p.plot("pailler", B.PLOT_NU, nature="feuilles")
    check("pailler avec les feuilles glanées", r["applied"], r["message"])

    ok = sum(1 for _, b in _res if b)
    print(f"\nRÉSULTAT : {ok}/{len(_res)} vérifications passées")
    return 0 if ok == len(_res) else 1


if __name__ == "__main__":
    sys.exit(main())
