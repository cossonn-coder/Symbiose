"""
SYMBIOSE — tests/simserver/supports.py
Section 24 : accès aux gestes ③ au pont (protocole 0.6.12).

  24a. Les deux blocs neufs du bloc `player` : `gestes_pressentis` ([{verbe,
       phrase}], calculé) et `familles` ({ordre, gestes}, statique).
  24b. Routes des SUPPORTS (`poser_tuteur`/`treillis`/`pergola`, + `poser_perchoir`
       déménagé dans `supports_route.py`) : point tuile-local, refus sans coût hors
       tuile, support visible au snapshot.
  24c. Routes des COUVERTURES (`poser_voile`/`cloche`/`ombriere`) : plot {r,c},
       refus sans coût hors tuile.
  24d. `palisser` : plante par position — refus sans coût si rien à portée ou si la
       plante n'est pas un sarmenteux, réussite une fois un tuteur planté à côté.

Banc `liane_relais` : il porte un jasmin LIBRE (sarmenteux sans appui) et un lierre.
"""
from .harness import check, ServerProc

T = "LIANES"


def _pressentis(snap) -> dict:
    return {p["verbe"]: p["phrase"] for p in snap["player"]["gestes_pressentis"]}


def test_supports_pont():
    print("\n[24] accès aux gestes ③ : pressentis, familles, supports, couvertures")
    s = ServerProc()
    s.send(cmd="init", config="liane_relais", seed=42)
    snap = s.send(cmd="snapshot")["snapshot"]
    pl = snap["player"]

    # --- 24a : forme des deux blocs ------------------------------------------
    check("player porte `gestes_pressentis` (liste) et `familles`",
          isinstance(pl.get("gestes_pressentis"), list) and "familles" in pl,
          sorted(pl.keys()))
    fam = pl["familles"]
    check("familles = {ordre: 8 familles, gestes: {famille: [verbes]}}",
          len(fam["ordre"]) == 8 and set(fam["gestes"]) == set(fam["ordre"])
          and fam["ordre"][0] == "main" and fam["ordre"][-1] == "paysage")
    check("l'ordre interne d'une famille survit au JSON (liste)",
          fam["gestes"]["taille"] == ["pincer", "arracher", "couper", "tailler"],
          fam["gestes"]["taille"])
    tous = [v for f in fam["ordre"] for v in fam["gestes"][f]]
    check("tout geste ouvert a une famille",
          set(pl["gestes_debloques"]) <= set(tous))

    # --- 24b : supports -------------------------------------------------------
    n0 = len(snap["supports"][T])
    v0 = pl["vigueur"]
    r = s.send(cmd="action", verb="poser_treillis",
               target={"tile": T, "x_cm": -5.0, "y_cm": 20.0})
    check("poser_treillis hors tuile → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v0,
          r["result"]["message"])
    r = s.send(cmd="action", verb="poser_tuteur", target={"tile": "NULLE"})
    check("poser_tuteur tuile inconnue → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v0)
    types = []
    for verbe, x in (("poser_treillis", 60.0), ("poser_pergola", 110.0),
                     ("poser_perchoir", 160.0)):
        r = s.send(cmd="action", verb=verbe,
                   target={"tile": T, "x_cm": x, "y_cm": 1375.0})
        check(f"{verbe} → applied, coût > 0",
              r["result"]["applied"] and r["result"]["cost"] > 0.0,
              r["result"]["message"])
        types = [sup["type"] for sup in r["snapshot"]["supports"][T]]
    check("les trois supports sont au snapshot",
          len(types) == n0 + 3
          and types[-3:] == ["treillis", "pergola", "perchoir"], types[-3:])

    # --- 24d : palisser -------------------------------------------------------
    libre = next(p for p in snap["plants"]
                 if p["species"] == "Jasmine" and p.get("support") is None)
    cible = {"tile": T, "x_cm": libre["x_cm"], "y_cm": libre["y_cm"]}
    v1 = r["result"]["vigueur"]
    r = s.send(cmd="action", verb="palisser", target=cible)
    check("palisser sans support à portée → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v1
          and "portée" in r["result"]["message"], r["result"]["message"])
    lierre = next(p for p in snap["plants"] if p["species"] == "Ivy")
    r = s.send(cmd="action", verb="palisser",
               target={"tile": lierre["tile"], "x_cm": lierre["x_cm"],
                       "y_cm": lierre["y_cm"]})
    check("palisser un lierre → refus sans coût (il s'accroche seul)",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v1,
          r["result"]["message"])
    r = s.send(cmd="action", verb="palisser",
               target={"tile": T, "x_cm": 1.0, "y_cm": 1.0})
    check("palisser dans le vide → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v1)
    r = s.send(cmd="action", verb="poser_tuteur",
               target={"tile": T, "x_cm": libre["x_cm"] + 20.0,
                       "y_cm": libre["y_cm"]})
    check("poser_tuteur près du jasmin → applied", r["result"]["applied"],
          r["result"]["message"])
    check("poser_tuteur est un déclencheur : palisser s'ouvre",
          "palisser" in r["result"].get("debloques", []),
          r["result"].get("debloques"))
    r = s.send(cmd="action", verb="palisser", target=cible)
    check("palisser avec un tuteur à portée → applied",
          r["result"]["applied"] and r["result"]["cost"] > 0.0,
          r["result"]["message"])
    attache = next(p for p in r["snapshot"]["plants"]
                   if p["species"] == "Jasmine" and p["x_cm"] == libre["x_cm"]
                   and p["y_cm"] == libre["y_cm"])
    check("le jasmin porte son support au snapshot (tuteur)",
          (attache.get("support") or {}).get("type") == "tuteur",
          attache.get("support"))
    r = s.send(cmd="action", verb="palisser", target=cible)
    check("palisser une plante déjà attachée → refus",
          r["result"]["applied"] is False and "déjà" in r["result"]["message"])

    # --- 24a (suite) : le pressenti vit avec l'état du joueur -----------------
    # Les poses ont fait découvrir `palissage` (à l'usage) : ce qui reste fermé de
    # la technique serait pressenti ; ici tout est ouvert ou va l'être. On vérifie
    # la FORME sur ce que le banc donne et le contrat « jamais un geste ouvert ».
    pl = r["snapshot"]["player"]
    pres = _pressentis(r["snapshot"])
    check("aucun geste ouvert n'est pressenti",
          not (set(pres) & set(pl["gestes_debloques"])), sorted(pres))
    check("chaque pressenti a une phrase non vide",
          all(isinstance(ph, str) and ph for ph in pres.values()))

    # --- 24c : couvertures ----------------------------------------------------
    v2 = r["result"]["vigueur"]
    r = s.send(cmd="action", verb="poser_voile",
               target={"tile": T, "r": -1, "c": 0})
    check("poser_voile hors tuile → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v2,
          r["result"]["message"])
    r = s.send(cmd="action", verb="poser_cloche",
               target={"tile": T, "r": True, "c": 0})
    check("poser_cloche r booléen → refus sans coût",
          r["result"]["applied"] is False and r["result"]["vigueur"] == v2)
    for verbe, rc in (("poser_voile", (2, 2)), ("poser_cloche", (5, 5)),
                      ("poser_ombriere", (8, 8))):
        r = s.send(cmd="action", verb=verbe,
                   target={"tile": T, "r": rc[0], "c": rc[1]})
        check(f"{verbe} → applied, coût > 0",
              r["result"]["applied"] and r["result"]["cost"] > 0.0,
              r["result"]["message"])
    # Le voile de l'Atelier est un objet touché par `poser_voile` : sa technique est
    # découverte à l'usage, les deux gestes frères restent ouverts ou pressentis.
    pl = r["snapshot"]["player"]
    pres = _pressentis(r["snapshot"])
    check("après un voile : cloche et ombrière ouvertes ou pressenties",
          all(v in pl["gestes_debloques"] or v in pres
              for v in ("poser_cloche", "poser_ombriere")),
          sorted(pres))

    s.send(cmd="quit")
    check("quit supports → exit 0", s.close() == 0)
