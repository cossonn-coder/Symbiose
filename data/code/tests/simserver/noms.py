"""
SYMBIOSE — tests/simserver/noms.py
Section 25 : noms des espèces en français à l'écran (LISIBILITÉ DU BILAN ②, D141,
protocole 0.6.22).

Règle : tout texte humain passe par le nom AFFICHÉ (`cls.name`, français accentué) ;
`species` (nom de classe) reste l'IDENTIFIANT. On vérifie (a) au catalogue que
chaque espèce a un nom qui ne ressemble pas à un nom de classe, (b) au pont que
chaque plante du snapshot porte `name` = ce nom, (c) que le rapport perf et le
texte de la chronique ne sortent jamais un nom de classe.
"""
import re

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

from .harness import check, ServerProc

# Nom de classe = ASCII sans espace, en CamelCase à au moins deux bosses (OakTree).
_CAMEL = re.compile(r"[A-Z][a-z]+(?:[A-Z][a-z]*)+")


def _ressemble_classe(nom: str) -> bool:
    return " " not in nom and nom.isascii() and bool(_CAMEL.fullmatch(nom))


def test_noms_francais():
    print("[noms français — pont ②, D141]")
    classes = {cls for d in (PLANT_CATALOGUE, PERENNIAL_CATALOGUE) for cls in d.values()}
    fautifs = sorted(c.__name__ for c in classes
                     if not getattr(c, "name", "") or _ressemble_classe(c.name))
    check(f"les {len(classes)} espèces du catalogue ont un nom affiché français",
          not fautifs, f"fautifs={fautifs}")
    noms_classe = {c.__name__ for c in classes}
    nom_de = {c.__name__: c.name for c in classes}

    s = ServerProc()
    s.send(cmd="init", config="full", seed=7)
    snap = None
    for _ in range(3):
        snap = s.send(cmd="step_week")["snapshot"]
    plantes = snap["plants"]
    faux = [(p["species"], p.get("name")) for p in plantes
            if p.get("name") != nom_de.get(p["species"])]
    check("chaque plante porte `name` = nom affiché de son espèce",
          plantes and not faux, f"{len(faux)} écarts, ex. {faux[:3]}")

    rep = s.send(cmd="perf_report")
    dumps = [rep["current"]] + list(rep.get("worst", []))
    cles = {n for d in dumps for n in d.get("par_espece", {})}
    check("rapport perf F4 : `par_espece` en noms affichés, aucun nom de classe",
          # ⊂ noms affichés (« Dactyle » est à la fois classe et nom français)
          cles and cles <= set(nom_de.values())
          and all(not _ressemble_classe(n) for n in cles),
          f"clés={sorted(cles)[:6]}")
    texte = rep.get("chronique", {}).get("texte", "")
    vus = sorted(n for n in noms_classe - set(nom_de.values())
                 if re.search(rf"\b{n}\b", texte))
    check("chronique : le texte ne nomme aucune classe", texte and not vus,
          f"classes vues={vus[:5]}")
    s.send(cmd="quit")
    s.close()

    # Le bilan annuel n'existe qu'en semaine 52 : on éprouve le formateur à part.
    from tools.simserver.chronique import _bloc_annee
    bloc = "\n".join(_bloc_annee({
        "an": 1, "vivants": {"consoude": 3, "chene": 4},
        "morts": {"poivron": {"froid": 1}}, "levees": {"bourse_pasteur": 2},
        "autres": {}, "marquante": False}))
    check("chronique : bilan annuel en noms affichés (Consoude, Chêne, Poivron)",
          all(n in bloc for n in ("Consoude 3", "Chêne 4", "Poivron froid 1",
                                  "Bourse-à-pasteur 2")), bloc)
