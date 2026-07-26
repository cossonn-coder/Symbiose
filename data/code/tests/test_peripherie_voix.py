"""
SYMBIOSE — tests/test_peripherie_voix.py
Tests du tronçon ⑥ du sprint PÉRIPHÉRIE (D73) : les VOIX du paysage.
Spec : `sprints/champs/peripherie/sprint_peripherie/06_voix_narratives.md` +
`docs/narration/voix/conception_voix_narratives.md`.

Un fichier par tronçon (comme ④ `test_peripherie_gestes.py` et ⑤
`test_peripherie_eau_roche.py`) : ici, aucune écologie — de la DONNÉE éditoriale et
un PARSEUR. Cinq suites :

  Y  — le SAULE a ses CINQ voix (encyclopédie · carnet · pages · magazine · ledger) ;
  Z  — les gestes/techniques/outils du ④/⑤ ont leurs fiches à 3 niveaux, et la
       CLASSIFICATION les range dans le bon onglet ;
  AA — le PARSEUR reconnaît les quatre marqueurs 🪓 ⛏ 🚧 🪨, et ses tables de
       libellés sont le MIROIR EXACT de celles de l'émetteur (`actions/paysage`) ;
  AB — le CARNET rend une note lisible de chaque fait de paysage (slots remplis,
       jamais « sur None »), descriptive avant maîtrise, interprétative après ;
  AC — NEUTRALITÉ : corpus read-only, parseur pur, et le saule n'entre dans AUCUN
       chemin du monde du golden (ni banque-sol, ni archétype de succession).

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie_voix
"""
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE, WEED_CATALOGUE
from fields.peripherie import (ESSENCES_QUI_REJETTENT, ESSENCES_RIPISYLVE,
                               MARQUEUR_RUPTURE)
from fields.ecofields.bordure import MARQUEUR_EBOULIS
from sim import carnet, encyclopedie, evenements, journal, magazine, maitrise
from sim import encyclopedie_types as ET
from sim.actions import paysage
from sim.encyclopedie_corpus import FICHES
from sim.geste_corpus import FICHES_GESTE
from sim.outil_corpus import FICHES_OUTIL
from sim.pages_corpus import PAGES
from sim.quetes_corpus import QUETES_CORPUS
from sim.seeds import PlayerSeedBank
from sim.technique_corpus import FICHES_TECHNIQUE

_results = []

GESTES_SPRINT = ("abattre", "receper", "eteter", "endiguer", "deriver", "entailler")
TECHNIQUES_SPRINT = ("essartage", "taillis", "trogne", "terrassement")
OUTILS_SPRINT = ("hache", "serpe", "pioche")


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _log_coupe(verbe="abattre", essence="saule", cote=0):
    """Une ligne de log de coupe, produite par le VRAI émetteur (`_consigner`) —
    aucun format recopié à la main : si le libellé change, ce test suit."""
    gs = {"log": []}
    secteur = {"cote": cote, "type": "foret", "essence": essence,
               "souche_memory": "vivante"}
    paysage._consigner(gs, verbe, secteur, verbe)
    return gs["log"]


def _log_terre(verbe="endiguer", cote=2):
    gs = {"log": []}
    secteur = {"cote": cote, "type": "riviere"}
    paysage._consigner_terre(gs, verbe, secteur, "ligne d'eau 30 cm")
    return gs["log"]


# ---------------------------------------------------------------------------
# Y. Le saule et ses CINQ voix (règle « toute plante ajoutée = toutes ses voix »)
# ---------------------------------------------------------------------------

def test_saule_cinq_voix():
    cat = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}
    check("saule au catalogue (pérenne ligneuse)", cat.get("saule") is not None)
    check("saule = famille Salicaceae NEUVE",
          cat["saule"].family == "Salicaceae"
          and [c for c in cat.values() if c.family == "Salicaceae"] == [cat["saule"]])
    # 1. ENCYCLOPÉDIE — fiche 3 niveaux, servie au bon palier
    f = FICHES.get("saule")
    check("voix 1/5 encyclopédie : 3 niveaux non vides",
          f is not None and set(f) == {1, 2, 3}
          and all(f[n].strip() for n in (1, 2, 3)))
    gs = {}
    maitrise.decouvrir(gs, "j1", "saule")
    gs["maitrise"]["j1"]["objets"]["saule"]["palier"] = 3
    fiche = encyclopedie.encyclopedie_lire(gs, "j1", "saule")
    check("encyclopédie : le saule se lit, tagué plante",
          fiche is not None and fiche["type"] == "plante"
          and set(fiche["niveaux"]) == {1, 2, 3})
    # 2. CARNET — le saule illustre le rejet de souche (concept du ⑥) ET porte le
    #    geste `eteter` ; la chaîne de la ceinture le référençait déjà sans lui.
    check("voix 2/5 carnet : concept `rejet_de_souche` tabulé",
          carnet.CONCEPT_DE.get(("coupe", "receper")) == "rejet_de_souche")
    check("saule dans ESSENCES_QUI_REJETTENT et ESSENCES_RIPISYLVE",
          "saule" in ESSENCES_QUI_REJETTENT and "saule" in ESSENCES_RIPISYLVE)
    notes = _notes_du_log(_log_coupe("receper", "saule"))
    check("carnet : une note nomme le saule recépé",
          len(notes) == 1 and notes[0]["concept"] == "rejet_de_souche"
          and "saule" in notes[0]["texte"], f"{notes}")
    # 3. PAGES SECRÈTES — au moins une page parle du saule (le tronc creux)
    pages_saule = [p for p, v in PAGES.items() if "saule" in v["texte"].lower()]
    check("voix 3/5 pages secrètes : le saule a sa page", pages_saule != [],
          f"{pages_saule}")
    # 4. MAGAZINE — fiche produit + offre effective (rattachement famille)
    check("voix 4/5 magazine : fiche produit servie",
          magazine.magazine_fiche("saule") is not None)
    gsm = {"player_seed_bank": PlayerSeedBank()}
    maitrise.decouvrir(gsm, "j1", "saule")
    gsm["maitrise"]["j1"]["objets"]["saule"]["palier"] = magazine.SEUIL_MAGAZINE
    check("magazine : le saule est offrable à la maîtrise de sa famille",
          "saule" in magazine.magazine_offres(gsm, "j1"),
          f"{magazine.magazine_offres(gsm, 'j1')}")
    # 5. ÉVÉNEMENTS / LEDGER — un fait de cycle de vie du saule entre au ledger
    gsj = {}
    ajoutes = journal.consigner(gsj, "j1", _log_coupe("eteter", "saule"), 12)
    entree = gsj["journal"]["j1"]["entries"][0]
    check("voix 5/5 ledger : le fait est consigné (kind/cause/espèce)",
          ajoutes == 1 and entree["kind"] == "coupe"
          and entree["cause"] == "eteter" and entree["espece"] == "saule", f"{entree}")
    # Voix épistolaire (§E) : une lettre le désire, SANS condition neuve
    lettres = [q for q in QUETES_CORPUS.values() if "saule" in str(q.condition)]
    check("bonus : une lettre vise le saule, famille de condition existante",
          len(lettres) == 1 and lettres[0].condition[0] == "nombre_vivant_min",
          f"{[q.id for q in lettres]}")


# ---------------------------------------------------------------------------
# Z. Gestes, techniques, outils du ④/⑤ : fiches complètes + bon onglet
# ---------------------------------------------------------------------------

def test_fiches_du_sprint():
    for geste in GESTES_SPRINT:
        f = FICHES_GESTE.get(geste)
        check(f"geste `{geste}` : fiche 3 niveaux non vides",
              f is not None and set(f) == {1, 2, 3}
              and all(f[n].strip() for n in (1, 2, 3)))
        check(f"geste `{geste}` : classé onglet geste", ET.type_de(geste) == "geste")
    for tech in TECHNIQUES_SPRINT:
        f = FICHES_TECHNIQUE.get(tech)
        check(f"technique `{tech}` : fiche 3 niveaux non vides",
              f is not None and set(f) == {1, 2, 3}
              and all(f[n].strip() for n in (1, 2, 3)))
        check(f"technique `{tech}` : classée onglet technique",
              ET.type_de(tech) == "technique", f"{ET.type_de(tech)}")
    for outil in OUTILS_SPRINT:
        f = FICHES_OUTIL.get(outil)
        check(f"outil `{outil}` : fiche 3 niveaux non vides",
              f is not None and set(f) == {1, 2, 3}
              and all(f[n].strip() for n in (1, 2, 3)))
        check(f"outil `{outil}` : classé onglet outil", ET.type_de(outil) == "outil")
    # `creuser` sert AUSSI la mare de bordure (⑤) : pas de geste `creuser_mare` en
    # doublon — la fiche existante doit couvrir les deux cibles.
    check("aucun doublon `creuser_mare` dans le corpus",
          "creuser_mare" not in FICHES_GESTE and "creuser" in FICHES_GESTE)
    # Philo #6 : ce que le N3 doit APPRENDRE n'est pas donné en consigne au N1/N2.
    receper = FICHES_GESTE["receper"]
    check("philo #6 : « le hêtre ne rejette pas » n'est révélé qu'au N3",
          "hêtre" not in receper[1] and "hêtre" not in receper[2]
          and "hêtre" in receper[3])
    check("philo #6 : l'irréversibilité de l'entaille n'est annoncée qu'au N3",
          "JAMAIS" in FICHES_GESTE["entailler"][3])


# ---------------------------------------------------------------------------
# AA. Le parseur : 4 marqueurs reconnus + tables MIROIR de l'émetteur
# ---------------------------------------------------------------------------

def test_parseur_paysage():
    # Miroir EXACT des libellés (le parseur ne les importe pas pour rester pur)
    check("miroir libellés de coupe = paysage.LIBELLE_GESTE",
          evenements._VERBE_COUPE == {v: k for k, v in paysage.LIBELLE_GESTE.items()},
          f"{evenements._VERBE_COUPE}")
    check("miroir libellés d'eau/roche = paysage.LIBELLE_TERRE",
          evenements._VERBE_TERRE == {v: k for k, v in paysage.LIBELLE_TERRE.items()},
          f"{evenements._VERBE_TERRE}")
    check("marqueurs du parseur = ceux des émetteurs",
          paysage.MARQUEUR_COUPE == "🪓" and paysage.MARQUEUR_TERRE == "⛏"
          and MARQUEUR_RUPTURE == "🚧" and MARQUEUR_EBOULIS == "🪨")
    # Les 3 coupes → kind `coupe`, cause = le VERBE, espèce = l'essence
    for verbe in ("abattre", "receper", "eteter"):
        evs = evenements.evenements(_log_coupe(verbe, "charme"))
        check(f"🪓 {verbe} → 1 événement coupe typé",
              len(evs) == 1 and evs[0].kind == "coupe" and evs[0].cause == verbe
              and evs[0].espece == "charme" and evs[0].pos is None, f"{evs}")
    # Les 4 gestes d'eau/roche → kind `terrassement`
    for verbe in ("endiguer", "deriver", "creuser", "entailler"):
        evs = evenements.evenements(_log_terre(verbe))
        check(f"⛏ {verbe} → 1 événement terrassement typé",
              len(evs) == 1 and evs[0].kind == "terrassement"
              and evs[0].cause == verbe, f"{evs}")
    # Un bord sans essence (prairie) : espèce None, jamais de KeyError
    gs = {"log": []}
    paysage._consigner(gs, "abattre",
                       {"cote": 1, "type": "prairie", "essence": None,
                        "souche_memory": "morte"}, "abattre")
    evs = evenements.evenements(gs["log"])
    check("coupe d'un bord sans essence → espèce None (gracieux)",
          len(evs) == 1 and evs[0].espece is None, f"{evs}")
    # Rupture d'ouvrage + éboulis (émis par le tick, pas par le joueur)
    rupture = [f"  {MARQUEUR_RUPTURE} l'ouvrage d'eau (sud) a rompu : "
               f"l'eau reprend son cours (0 cm)"]
    evs = evenements.evenements(rupture)
    check("🚧 rupture → 1 événement rupture",
          len(evs) == 1 and evs[0].kind == "rupture" and evs[0].cause is None, f"{evs}")
    eboulis = ["[T0]",
               f"  {MARQUEUR_EBOULIS} le sol part au bord nord [T0] : "
               f"de la terre nue descend sur les premiers plots"]
    evs = evenements.evenements(eboulis)
    check("🪨 éboulis → 1 événement eboulis, rattaché à la tuile",
          len(evs) == 1 and evs[0].kind == "eboulis"
          and evs[0].tile_id == "T0", f"{evs}")
    # L'API HISTORIQUE (détection de maîtrise) reste AVEUGLE à ces lignes : elle ne
    # consomme que les transitions avance/stagne/repro (aucune régression D12).
    toutes = (_log_coupe() + _log_terre() + rupture + eboulis)
    check("API historique `_evenements` : aucun événement de paysage",
          list(evenements._evenements(toutes)) == [])


# ---------------------------------------------------------------------------
# AB. Le carnet : une note lisible pour chaque fait de paysage
# ---------------------------------------------------------------------------

def _notes_du_log(log, palier=0, concept=None):
    """Notes du carnet produites par un log, pour un joueur dont on pose
    éventuellement le palier d'un concept (bascule interprétative)."""
    gs = {}
    journal.consigner(gs, "j1", log, 20)
    if concept is not None:
        maitrise.decouvrir(gs, "j1", concept)
        gs["maitrise"]["j1"]["objets"][concept]["palier"] = palier
    return carnet.carnet_lire(gs, "j1")


def test_carnet_paysage():
    attendus = {
        ("coupe", "abattre"): "brise_vent",
        ("coupe", "receper"): "rejet_de_souche",
        ("coupe", "eteter"): "lisiere",
        ("terrassement", "endiguer"): "eau",
        ("terrassement", "deriver"): "eau",
        ("terrassement", "creuser"): "eau",
        ("terrassement", "entailler"): "erosion",
        ("rupture", None): "eau",
        ("eboulis", None): "erosion",
    }
    for (kind, cause), concept in attendus.items():
        check(f"concept de ({kind}, {cause}) = {concept}",
              carnet.CONCEPT_DE.get((kind, cause)) == concept)
        for registre in ("descriptif", "interprétatif"):
            texte = carnet.GABARIT.get((kind, cause, registre))
            check(f"gabarit {registre} de ({kind}, {cause}) présent et non vide",
                  bool(texte and texte.strip()))
    # Bout-en-bout : la note est LISIBLE (slots remplis, pas de « sur None »)
    for log in (_log_coupe("abattre", "aulne"), _log_terre("entailler")):
        notes = _notes_du_log(log)
        check("note lisible (slots remplis, jamais « sur None »)",
              len(notes) == 1 and "{" not in notes[0]["texte"]
              and "None" not in notes[0]["texte"], f"{notes}")
    # Registre : descriptif tant que le concept n'est pas maîtrisé, interprétatif au
    # seuil — la révélation rétroactive marche aussi sur les faits de paysage.
    desc = _notes_du_log(_log_coupe("abattre"), 1, "brise_vent")[0]
    interp = _notes_du_log(_log_coupe("abattre"), carnet.SEUIL_CARNET, "brise_vent")[0]
    check("carnet : descriptif avant maîtrise du concept",
          desc["registre"] == "descriptif", f"{desc}")
    check("carnet : interprétatif au seuil du concept",
          interp["registre"] == "interprétatif"
          and interp["texte"] != desc["texte"], f"{interp}")
    # Le fait de paysage n'appartient à aucune tuile → lieu « au jardin » (jamais None)
    check("lieu d'un fait hors tuile = « au jardin »",
          carnet._lieu((None,)) == "au jardin")


# ---------------------------------------------------------------------------
# AC. Neutralité : donnée read-only, parseur pur, saule hors monde du golden
# ---------------------------------------------------------------------------

def test_neutralite():
    log = _log_coupe() + _log_terre()
    copie = list(log)
    evenements.evenements(log)
    check("parseur PUR : le log n'est pas modifié", log == copie)
    gs = {}
    carnet.carnet_lire(gs, "j1")
    check("carnet sans joueur → aucune clé créée", gs == {}, f"{gs}")
    # Le saule ne peut PAS entrer dans le monde du golden : il n'est ni un archétype
    # de succession (banque-sol) ni semé par `build_world` — golden INCHANGÉ.
    check("saule absent des archétypes de succession",
          "saule" not in {k for k, v in WEED_CATALOGUE.items()}
          and PERENNIAL_CATALOGUE["saule"] not in WEED_CATALOGUE.values())
    check("aucun geste de paysage dans la palette de base des coûts",
          all(g in FICHES_GESTE for g in GESTES_SPRINT))


if __name__ == "__main__":
    test_saule_cinq_voix()
    test_fiches_du_sprint()
    test_parseur_paysage()
    test_carnet_paysage()
    test_neutralite()
    ok = sum(1 for _, c in _results if c)
    print("\n" + "=" * 60)
    print(f"RÉSULTAT : {ok}/{len(_results)} vérifications passées")
    print("=" * 60)
