"""
SYMBIOSE — tests/test_flore_spontanee.py
Sprint TRÈFLE DOMINANT ② : la sous-sélection d'espèce dans un archétype.
  1. pure et déterministe ; ne bouge pas pour les archétypes sans flore ;
  2. dactyle et ortie seulement sur sol riche, fétuque seulement hors sol riche ;
  3. banque de graines et WEED_CATALOGUE gardent leur forme, le trèfle reste hors levée ;
  4. une espèce hors tête d'archétype lève avec des gènes fondateurs ;
  5. chaque neuve a ses 5 voix.
Lancement depuis data/code/ : python3 -m tests.test_flore_spontanee
"""
from __future__ import annotations

import sys

from fields import SEED_ARCHETYPES, init_eco
from plants import Clover, Nettle, PoaAnnua, Taraxacum, WEED_CATALOGUE, PLANT_CATALOGUE
from plants.catalogue import AZOTE_RICHE, ESPECES_SPONTANEES, FLORE_SPONTANEE
from plants.species import Dactyle, FetuqueRouge, PlantainLanceole
from sim.carnet import CONCEPT_DE, GABARIT
from sim.encyclopedie_corpus import FICHES
from sim.evenements import evenements
from sim.pages_corpus import PAGES
from sim.succession import choisir_espece

ECHECS: list[str] = []
NEUVES = {"dactyle": Dactyle, "fetuque": FetuqueRouge, "plantain": PlantainLanceole}


def check(libelle: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {libelle}" + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        ECHECS.append(libelle)


def _tirages(archetype: str, azote: float) -> set[type]:
    return {choisir_espece(archetype, azote, 42, w, r, c)
            for w in range(1, 53) for r in range(10) for c in range(10)}


def test_selection() -> None:
    print("[1] sous-sélection")
    check("déterministe", choisir_espece("grass", 0.9, 42, 7, 3, 4)
          == choisir_espece("grass", 0.9, 42, 7, 3, 4))
    check("archétype sans flore → sa tête seule",
          _tirages("pioneer", 2.0) == {WEED_CATALOGUE["pioneer"]}
          and _tirages("disease_indicator", 0.0) == {WEED_CATALOGUE["disease_indicator"]})
    check("grass pauvre : pâturin + fétuque", _tirages("grass", AZOTE_RICHE - 0.01)
          == {PoaAnnua, FetuqueRouge})
    check("grass riche : pâturin + dactyle", _tirages("grass", AZOTE_RICHE)
          == {PoaAnnua, Dactyle})
    check("competitor pauvre : pissenlit + plantain", _tirages("competitor", 0.0)
          == {Taraxacum, PlantainLanceole})
    check("competitor riche : les trois + ortie", _tirages("competitor", 1.5)
          == {Taraxacum, PlantainLanceole, Nettle})
    check("azote au-delà de la fixation : pas de trou", _tirages("grass", 9.0)
          == {PoaAnnua, Dactyle})


def test_forme() -> None:
    print("[2] banque et catalogue inchangés")
    check("têtes d'archétype inchangées", WEED_CATALOGUE["grass"] is PoaAnnua
          and WEED_CATALOGUE["competitor"] is Taraxacum)
    check("5 archétypes", len(SEED_ARCHETYPES) == 5)
    check("chaque flore commence par sa tête",
          all(flore[0][0] is WEED_CATALOGUE[a] for a, flore in FLORE_SPONTANEE.items()))
    check("trèfle hors levée spontanée", Clover not in ESPECES_SPONTANEES)
    check("les neuves portent l'archétype de leur flore",
          Dactyle.archetype == FetuqueRouge.archetype == "grass"
          and PlantainLanceole.archetype == "competitor")


def test_genes_hors_tete() -> None:
    print("[3] espèce hors tête : pool vide → {} (le repli fondateur de succession)")
    eco = init_eco("X", 8, 8, heterogene=True)
    check("pool fondateur de la tête présent",
          eco.seed_bank.sample_genes(1, 1, PoaAnnua, 42, 3) != {})
    check("pool d'une neuve vide", eco.seed_bank.sample_genes(1, 1, Dactyle, 42, 3) == {})


def test_voix() -> None:
    print("[4] 5 voix")
    for cle, cls in NEUVES.items():
        check(f"{cle} : encyclopédie 3 niveaux", set(FICHES.get(cle, {})) == {1, 2, 3})
        check(f"{cle} : magazine (catalogue maître + famille)",
              PLANT_CATALOGUE.get(cle) is cls and bool(cls.family))
        evs = evenements(["[T0]", f"🌱 {cls.name}@(1,1) → [semis]"])
        check(f"{cle} : événement de germination",
              len(evs) == 1 and evs[0].kind == "germination" and evs[0].espece == cle)
    for cause in ("sol_riche", "sol_maigre"):
        check(f"carnet : {cause} → azote", CONCEPT_DE.get(("germination", cause)) == "azote")
        check(f"carnet : gabarits {cause}",
              ("germination", cause, "descriptif") in GABARIT
              and ("germination", cause, "interprétatif") in GABARIT)
    cause = lambda n: evenements(["[T0]", f"🌱 {n}@(1,1) → [semis]"])[0].cause
    check("causes des levées", cause("Dactyle") == cause("Ortie") == "sol_riche"
          and cause("Fétuque rouge") == "sol_maigre" and cause("Plantain lancéolé") is None)
    check("page du plantain", PAGES["P48"]["concept"] == "succession")


if __name__ == "__main__":
    test_selection()
    test_forme()
    test_genes_hors_tete()
    test_voix()
    print("ÉCHECS :" if ECHECS else "Tout passe.", *ECHECS)
    sys.exit(1 if ECHECS else 0)
