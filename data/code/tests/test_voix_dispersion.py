"""
SYMBIOSE — tests/test_voix_dispersion.py
Zoochorie ⑦ (D42) : les voix de la dispersion.

  (a) parseur : la levée d'un grain sauvage devient `semis_spontane` (espèce +
      origine) ; la levée « (planté) » garde son chemin `germination` ;
  (b) prises du merle / geai / écureuil AGRÉGÉES : un événement par bête et par tick ;
  (c) mulot : seules les semaines où il CACHE donnent un événement (une par tick) ;
  (d) glandée : ligne sans @pos → événement `glandee` (et pas `reproduction`) ;
  (e) carnet : concept `dispersion` (sauf la chute au pied → `reproduction`),
      gabarits descriptif ET interprétatif présents pour chaque paire ;
  (f) `_evenements` historique (maîtrise) ignore les lignes neuves sans @pos.

Lancement (depuis data/code/) :
  python3 -m tests.test_voix_dispersion
"""
import sys

from sim.evenements import evenements, _evenements
from sim import carnet
from sim.journal import consigner

_res = []


def check(nom, ok, info=""):
    _res.append((nom, ok))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


LOG = [
    "[T0]",
    "    🌱 Levée (semé par merle) : Cerisier @(20,6) [niche=0.812]",
    "    🌱 Levée (semé par ceinture) : Chêne @(3,14) [niche=0.700]",
    "    🌱 Levée (planté) : Cerisier @(5,5) [niche=0.900]",
    "    🐦 Merle : 64 fruits pris sur Cerisier@(36, 6)",
    "    🐦 Merle : 12 fruits pris sur Framboisier@(30, 2)",
    "    🐦 Geai : 7 fruits cachés depuis Noyer@(3, 29)",
    "    🐿 Écureuil : 4 fruits cachés depuis Noyer@(3, 38)",
    "    🌰 Glandée : Chêne (année forte)",
    "  🐭 Mulot : 9 graines mangées, 0 cachées (T0)",
    "  🐭 Mulot : 5 graines mangées, 2 cachées (T1)",
    "  🐦 Merle : 3 graine(s) semée(s) sous les perchoirs",
]


def test_parseur():
    evs = evenements(LOG)
    semis = [e for e in evs if e.kind == "semis_spontane"]
    check("(a) deux levées sauvages", len(semis) == 2, str(semis))
    check("(a) espèce + origine", (semis[0].espece, semis[0].cause, semis[0].pos)
          == ("cerisier", "merle", (20, 6)) and semis[1].cause == "ceinture")
    germ = [e for e in evs if e.kind == "germination"]
    check("(a) « planté » garde `germination`", len(germ) == 1)
    frug = [e for e in evs if e.kind == "frugivorie"]
    check("(b) une prise par bête et par tick",
          sorted(e.cause for e in frug) == ["ecureuil", "geai", "merle"], str(frug))
    check("(b) espèce de la 1ʳᵉ plante", next(e for e in frug if e.cause == "merle").espece
          == "cerisier")
    caches = [e for e in evs if e.kind == "cache"]
    check("(c) mulot : un événement, semaine avec cache", len(caches) == 1
          and caches[0].cause == "mulot")
    gl = [e for e in evs if e.kind == "glandee"]
    check("(d) glandée", len(gl) == 1 and gl[0].espece == "chene" and gl[0].pos is None)
    check("(d) pas de reproduction fantôme", not any(e.kind == "reproduction" for e in evs))
    check("(c) semaine sans cache : rien", not any(
        e.kind == "cache" for e in evenements(LOG[:1] + LOG[9:10])))


def test_carnet():
    paires = [("semis_spontane", o) for o in
              ("chute", "merle", "geai", "ecureuil", "mulot", "ceinture")]
    paires += [("frugivorie", b) for b in ("merle", "geai", "ecureuil")]
    paires += [("cache", "mulot"), ("glandee", None)]
    for k, c in paires:
        attendu = "reproduction" if (k, c) == ("semis_spontane", "chute") else "dispersion"
        check(f"(e) concept {k}/{c}", carnet.CONCEPT_DE.get((k, c)) == attendu)
        check(f"(e) gabarits D+I {k}/{c}", all(
            (k, c, reg) in carnet.GABARIT for reg in (carnet._D, carnet._I)))
    gs = {}
    consigner(gs, "j", LOG, 30)
    notes = carnet.carnet_lire(gs, "j", {"concept": "dispersion"})
    check("(e) notes de dispersion au carnet (descriptif au départ)",
          len(notes) >= 5 and all(n["registre"] == carnet._D for n in notes),
          str(len(notes)))
    check("(e) descriptif : « je n'en ai pas semé »",
          any("je n'en ai pas semé" in n["texte"] for n in notes))


def test_historique():
    hist = list(_evenements(LOG))
    check("(f) _evenements : aucune ligne neuve sans @pos lue",
          all(k in ("avance", "stagne", "repro") for k, *_ in hist)
          and not any(k == "repro" for k, *_ in hist))


def main():
    print("=== Voix de la dispersion (zoochorie ⑦) ===")
    test_parseur()
    test_carnet()
    test_historique()
    ok = sum(1 for _n, v in _res if v)
    print(f"RÉSULTAT : {ok}/{len(_res)} vérifications passées")
    return 0 if ok == len(_res) else 1


if __name__ == "__main__":
    sys.exit(main())
