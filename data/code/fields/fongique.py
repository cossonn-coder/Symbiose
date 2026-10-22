"""
SYMBIOSE — fields/fongique.py
Registre DATA-DRIVEN du règne fongique (sprint « le sol qui respire » ③, D111 §3.1-3.2)
et choix de l'ESPÈCE d'un carpophore depuis la NICHE locale du plot.

📖 Pédagogie — une fonction, treize visages. Le moteur garde UN seul champ
`mycelium` (la fonction écologique : décomposeur, liant, mycorhize — coût de tick
inchangé). L'ESPÈCE qui fructifie n'est pas un état : elle se DÉDUIT, au moment de
l'échantillonnage (perception, hors tick), de ce que le plot offre :
  - `bois`   : bois mort frais au sol (`eco.bois_fresh_at > 0`) ;
  - `humus`  : sol riche (`om_active` ≥ HUMUS_OM_MIN) ou tas de compost/bois posé ;
  - `racines`: racines VIVANTES d'un hôte listé (famille OU nom d'espèce) qui
               exploitent le plot — mycorhize, prairie de graminées, verger.
Ajouter une espèce = ajouter une entrée ici ; AUCUN hôte n'est codé ailleurs.

Les SOSIES partagent réellement leurs niches (même bois pour pleurote / hypholome /
collybie / armillaire ; mêmes graminées pour rosé / clitocybe ; même Fagacée pour
cèpe / phalloïde) : seul un hash spatial déterministe départage, comme en forêt où
le cèpe et l'amanite poussent sous le même chêne.

Parasites (`parasite=True`) : leur niche `racines` ne s'ouvre que sur un hôte DÉJÀ
AFFAIBLI (D-parasite-faiblesse, Q8) — l'appelant marque ces plots d'un label
`"!" + hôte` (cf. `sim/champignon_role.racines_par_plot`). L'ATTAQUE elle-même est
le tronçon ④ ; ici on ne fait que la rendre visible.

Couche `fields` : données pures + fonction pure, zéro RNG (hash spatial `_hash_noise`),
aucun import de `sim` → golden NEUTRE (personne dans le tick ne lit ce module).
"""
from __future__ import annotations

from dataclasses import dataclass

from fields.noise import _hash_noise

# Comestibilité (tags cumulables : l'amanite tue-mouches est psychédélique ET toxique).
COMESTIBLE, VENENEUX, MORTEL, PSYCHEDELIQUE, IMMANGEABLE = (
    "comestible", "veneneux", "mortel", "psychedelique", "immangeable")

# Substrats-niches lus au plot.
BOIS, HUMUS, RACINES = "bois", "humus", "racines"

# Seuil d'humus « riche » (om_active, même échelle que `fields/ecofields/sol.py`) :
# au-dessus, le coprin trouve son sol gras. Knob de calibrage (mesure ③).
HUMUS_OM_MIN = 0.6

# Canal de hash dédié au choix d'espèce (décorrélé des positions de carpophores).
_SALT_ESPECE = 0x2AF0E5


@dataclass(frozen=True)
class EspeceFongique:
    """Une espèce de champignon — DONNÉE pure (aucun état)."""
    cle: str
    nom: str
    groupe: str                 # bois / humus / prairie / verger / mycorhize / parasite
    substrats: tuple            # niches acceptées ⊂ {BOIS, HUMUS, RACINES}
    hotes: tuple = ()           # familles OU noms d'espèce (niche RACINES)
    fenetres: tuple = ()        # ((sem_debut, sem_fin), …) inclusives, semaine dans l'année
    comestibilite: tuple = ()   # tags (cf. constantes ci-dessus)
    ph: tuple | None = None     # (min, max) éventuel
    parasite: bool = False      # niche RACINES seulement sur hôte affaibli


# Calendrier moteur : printemps 1-13 · été 14-26 · automne 27-39 · hiver 40-52.
# Fenêtres (conception §3.2) : la collybie est SEULE au cœur de l'hiver (sem. 44-52
# et 1-4, après les premiers gels), la morille SEULE au printemps (sem. 5-13) ; le
# reste fructifie de l'été à la fin novembre (sem. 43).
REGISTRE_FONGIQUE: dict[str, EspeceFongique] = {e.cle: e for e in (
    # --- Bois mort (saprophytes) : les trois sosies + le pleurote ---------------
    EspeceFongique("pleurote", "Pleurote en huître", "bois", (BOIS,),
                   fenetres=((30, 43),), comestibilite=(COMESTIBLE,)),
    EspeceFongique("hypholome", "Hypholome en touffes", "bois", (BOIS,),
                   fenetres=((20, 43),), comestibilite=(VENENEUX,)),
    EspeceFongique("collybie", "Collybie à pied velouté", "bois", (BOIS,),
                   fenetres=((40, 52), (1, 4)), comestibilite=(COMESTIBLE,)),
    # --- Humus : répond aux gestes (compost, sol riche) -------------------------
    EspeceFongique("coprin", "Coprin chevelu", "humus", (HUMUS,),
                   fenetres=((16, 43),), comestibilite=(COMESTIBLE,)),
    # --- Prairie : graminées vivantes (laisser l'herbe) -------------------------
    EspeceFongique("rose_des_pres", "Rosé des prés", "prairie", (RACINES,),
                   hotes=("Poaceae",), fenetres=((22, 40),),
                   comestibilite=(COMESTIBLE,)),
    EspeceFongique("clitocybe", "Clitocybe blanchâtre", "prairie", (RACINES,),
                   hotes=("Poaceae",), fenetres=((22, 40),),
                   comestibilite=(MORTEL,)),
    EspeceFongique("psilocybe", "Psilocybe lancéolé", "prairie", (RACINES,),
                   hotes=("Poaceae",), fenetres=((30, 43),),
                   comestibilite=(PSYCHEDELIQUE,)),
    # --- Verger : seul champignon de printemps ---------------------------------
    EspeceFongique("morille", "Morille", "verger", (RACINES,),
                   hotes=("Pommier", "Cerisier"), fenetres=((5, 13),),
                   comestibilite=(COMESTIBLE,)),
    # --- Mycorhiziens : hôtes vivants ------------------------------------------
    EspeceFongique("cepe", "Cèpe", "mycorhize", (RACINES,),
                   hotes=("Fagaceae",), fenetres=((18, 40),),
                   comestibilite=(COMESTIBLE,)),
    EspeceFongique("amanite_phalloide", "Amanite phalloïde", "mycorhize", (RACINES,),
                   hotes=("Fagaceae",), fenetres=((18, 40),),
                   comestibilite=(MORTEL,)),
    EspeceFongique("amanite_tue_mouches", "Amanite tue-mouches", "mycorhize",
                   (RACINES,), hotes=("Bouleau", "Pinaceae"), fenetres=((27, 43),),
                   comestibilite=(PSYCHEDELIQUE, VENENEUX)),
    # --- Parasites : hôte affaibli (racines) puis souche (bois) ----------------
    EspeceFongique("armillaire", "Armillaire couleur de miel", "parasite",
                   (BOIS, RACINES), hotes=("Pommier", "Cerisier", "Fagaceae"),
                   fenetres=((32, 43),), comestibilite=(COMESTIBLE,), parasite=True),
    EspeceFongique("polypore_bouleau", "Polypore du bouleau", "parasite", (RACINES,),
                   hotes=("Bouleau",), fenetres=((20, 43),),
                   comestibilite=(IMMANGEABLE,), parasite=True),
)}

# Ordre STABLE du départage (indépendant de l'ordre d'insertion du dict).
_CLES_TRIEES = tuple(sorted(REGISTRE_FONGIQUE))


def en_saison(esp: EspeceFongique, week_in_year: int) -> bool:
    """Vrai si `week_in_year` tombe dans une fenêtre de fructification de l'espèce."""
    return any(a <= week_in_year <= b for a, b in esp.fenetres)


def especes_de_saison(week_in_year: int) -> tuple:
    """Clés (triées) des espèces qui peuvent fructifier cette semaine."""
    return tuple(k for k in _CLES_TRIEES if en_saison(REGISTRE_FONGIQUE[k], week_in_year))


def _hote_present(esp: EspeceFongique, labels) -> bool:
    """Un hôte de l'espèce exploite le plot (affaibli exigé pour un parasite)."""
    pre = "!" if esp.parasite else ""
    return any(pre + h in labels for h in esp.hotes)


def candidates_du_plot(eco, r: int, c: int, labels, cles_saison: tuple,
                       plots_tas=frozenset()) -> list:
    """Clés des espèces (parmi `cles_saison`) dont la niche est offerte au plot.
    `labels` = familles/noms des racines vivantes exploitant le plot (`"!"`-préfixés
    pour un hôte affaibli) ; ensemble vide si aucune racine. `plots_tas` = plots
    d'ancrage des structures posées (bac/pile : humus du compost), calculé une fois."""
    bois = eco.bois_fresh_at(r, c) > 0.0
    humus = (r, c) in plots_tas or eco.om_active.at_plot(r, c) >= HUMUS_OM_MIN
    ph = None
    out = []
    for k in cles_saison:
        esp = REGISTRE_FONGIQUE[k]
        ok = ((BOIS in esp.substrats and bois)
              or (HUMUS in esp.substrats and humus)
              or (RACINES in esp.substrats and labels and _hote_present(esp, labels)))
        if ok and esp.ph is not None:
            if ph is None:
                ph = eco.ph.at_plot(r, c)
            ok = esp.ph[0] <= ph <= esp.ph[1]
        if ok:
            out.append(k)
    return out


def choisir_espece(candidates: list, seed: int, r: int, c: int) -> str | None:
    """Départage DÉTERMINISTE (hash spatial, indépendant de la semaine) entre les
    espèces candidates d'un plot. Liste vide → None (le plot ne fructifie pas)."""
    if not candidates:
        return None
    i = int(_hash_noise(seed, _SALT_ESPECE, r, c) * len(candidates))
    return candidates[min(i, len(candidates) - 1)]
