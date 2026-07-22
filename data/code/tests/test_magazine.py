"""
SYMBIOSE — tests/test_magazine.py
Test du MAGAZINE DE BOTANIQUE (sprint Voix narratives, tronçon ⑥, dette D13).
Spec : `docs/narration/voix/conception_voix_narratives.md` §2.4 + §3 (décision C) +
kickoff `sprints/sprint_voix_narratives/06_magazine.md`.

Propriétés exigées (« Définition de done » du kickoff) :
  A. SANS palier 3 → offre VIDE (golden-safe, lecture pure).
  B. PALIER 3 sur un membre de famille → ses SŒURS offertes (catalogue maître moins
     banque joueur ; le membre déjà en banque n'est PAS dans l'offre).
  C. ACHAT VALIDE → Vigueur DÉBITÉE + lot en BANQUE ; renvoie True.
  D. ACHAT HORS OFFRE → False, AUCUN effet (ni Vigueur ni banque).
  E. FONDS INSUFFISANTS → False (la Vigueur tentée est drainée par spend, mais pas
     de lot livré — achat annulé).
  F. PAS DE BANQUE → False sans effet (on ne débite pas sans destination).
  G. FICHE PRODUIT (couplage ④) : réutilise le corpus, tronquée niveau ≤ 2.
  H. FILTRE SAISON = TODO nommé (signature acceptée, inactif tant que le catalogue
     ne porte pas de fenêtre de semis) — l'offre est STABLE quelle que soit la saison.

Le palier est posé directement (raccourci de test, comme test_encyclopedie/carnet).
Lecture/écriture event-driven hors tick → déterminisme total, aucun RNG.

Usage (depuis data/code/) :
  python3 -m tests.test_magazine
"""
from sim import magazine, maitrise, vigueur
from sim.seeds import PlayerSeedBank, Seed
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _poser_palier(gs, player, espece, p):
    """Pose DIRECTEMENT le palier d'une espèce (raccourci de test) : découverte via
    l'API puis écriture du palier — évite de compter les preuves de la courbe."""
    maitrise.decouvrir(gs, player, espece)
    gs["maitrise"][player]["objets"][espece]["palier"] = p


def _gs(avec_banque=True):
    """game_state jouet minimal : une banque vide optionnelle, pas de tick."""
    gs = {}
    if avec_banque:
        gs["player_seed_bank"] = PlayerSeedBank()
    return gs


# Famille à plusieurs membres pour exercer les sœurs : Solanaceae = tomate/poivron.
P = "joueur_test"


# ---------------------------------------------------------------------------
# A. Sans palier 3 → offre vide
# ---------------------------------------------------------------------------

def test_sans_palier3():
    gs = _gs()
    # rien découvert → vide
    check("aucune maîtrise → offre vide", magazine.magazine_offres(gs, P, "ete") == [])
    # tomate au palier 2 (investissement) → toujours pas d'ouverture
    _poser_palier(gs, P, "tomate", 2)
    check("palier 2 → offre vide (seuil = 3)", magazine.magazine_offres(gs, P, "ete") == [])
    # sans aucune clé maîtrise, magazine ne crée RIEN (no-op golden)
    gs2 = _gs()
    magazine.magazine_offres(gs2, P, "ete")
    check("offre pure : ne crée pas de clé maitrise", "maitrise" not in gs2)


# ---------------------------------------------------------------------------
# B. Palier 3 sur un membre → sœurs offertes
# ---------------------------------------------------------------------------

def test_soeurs_offertes():
    gs = _gs()
    _poser_palier(gs, P, "tomate", 3)         # maîtrise tomate (Solanaceae)
    offres = magazine.magazine_offres(gs, P, "ete")
    # le poivron (sœur Solanaceae, absent de la banque) est offert
    check("sœur poivron offerte au palier 3 tomate", "poivron" in offres,
          f"offres={offres}")
    # tomate elle-même : absente de la banque → reste offrable (cas limite assumé)
    # mais une espèce d'une AUTRE famille non maîtrisée ne l'est jamais
    check("haricot (Fabaceae non maîtrisée) hors offre", "haricot" not in offres)
    # une sœur DÉJÀ en banque n'est pas (re)proposée
    gs["player_seed_bank"].add(Seed(species="poivron"))
    offres2 = magazine.magazine_offres(gs, P, "ete")
    check("sœur déjà en banque → retirée de l'offre", "poivron" not in offres2,
          f"offres2={offres2}")


# ---------------------------------------------------------------------------
# C. Achat valide → Vigueur débitée + lot en banque
# ---------------------------------------------------------------------------

def test_achat_valide():
    gs = _gs()
    _poser_palier(gs, P, "tomate", 3)
    # Vigueur suffisante : on gonfle le plafond (palier 3 donne un bonus) puis on
    # crédite au-delà du coût.
    vigueur.ensure_player(gs, P)
    gs["vigueur"][P]["max_base"] = 500.0
    gs["vigueur"][P]["courante"] = 500.0
    avant = gs["vigueur"][P]["courante"]
    ok = magazine.acheter_au_magazine(gs, P, "poivron", "ete")
    check("achat valide → True", ok is True)
    check("Vigueur débitée du COUT_MAGAZINE",
          abs((avant - gs["vigueur"][P]["courante"]) - magazine.COUT_MAGAZINE) < 1e-9,
          f"débité={avant - gs['vigueur'][P]['courante']}")
    check("lot poivron déposé en banque", gs["player_seed_bank"].count("poivron") == 1)
    # après achat, le poivron n'est plus offert (il est en banque)
    check("poivron retiré de l'offre après achat",
          "poivron" not in magazine.magazine_offres(gs, P, "ete"))


# ---------------------------------------------------------------------------
# D. Achat hors offre → False, aucun effet
# ---------------------------------------------------------------------------

def test_achat_hors_offre():
    gs = _gs()
    _poser_palier(gs, P, "tomate", 3)
    vigueur.ensure_player(gs, P)
    gs["vigueur"][P]["max_base"] = 500.0
    gs["vigueur"][P]["courante"] = 500.0
    avant = gs["vigueur"][P]["courante"]
    # haricot n'est pas dans l'offre (Fabaceae non maîtrisée) → gate refuse
    ok = magazine.acheter_au_magazine(gs, P, "haricot", "ete")
    check("achat hors offre → False", ok is False)
    check("hors offre : Vigueur intacte", gs["vigueur"][P]["courante"] == avant)
    check("hors offre : banque intacte", gs["player_seed_bank"].count("haricot") == 0)


# ---------------------------------------------------------------------------
# E. Fonds insuffisants → False, lot non livré
# ---------------------------------------------------------------------------

def test_fonds_insuffisants():
    gs = _gs()
    _poser_palier(gs, P, "tomate", 3)
    vigueur.ensure_player(gs, P)
    gs["vigueur"][P]["courante"] = magazine.COUT_MAGAZINE - 1.0   # juste en dessous
    ok = magazine.acheter_au_magazine(gs, P, "poivron", "ete")
    check("fonds insuffisants → False", ok is False)
    check("fonds insuffisants : lot NON livré", gs["player_seed_bank"].count("poivron") == 0)


# ---------------------------------------------------------------------------
# F. Pas de banque → False sans effet
# ---------------------------------------------------------------------------

def test_pas_de_banque():
    gs = _gs(avec_banque=False)
    _poser_palier(gs, P, "tomate", 3)
    vigueur.ensure_player(gs, P)
    gs["vigueur"][P]["max_base"] = 500.0
    gs["vigueur"][P]["courante"] = 500.0
    avant = gs["vigueur"][P]["courante"]
    # l'offre existe (poivron sœur) mais aucune destination
    check("offre existe même sans banque", "poivron" in magazine.magazine_offres(gs, P, "ete"))
    ok = magazine.acheter_au_magazine(gs, P, "poivron", "ete")
    check("pas de banque → False", ok is False)
    check("pas de banque : Vigueur NON débitée", gs["vigueur"][P]["courante"] == avant)


# ---------------------------------------------------------------------------
# G. Fiche produit (couplage ④)
# ---------------------------------------------------------------------------

def test_fiche_produit():
    fiche = magazine.magazine_fiche("poivron")
    check("fiche produit poivron non None", fiche is not None)
    check("fiche produit tronquée niveau ≤ 2",
          fiche and fiche["niveau_max"] <= 2 and set(fiche["niveaux"]) <= {1, 2},
          f"niveau_max={fiche['niveau_max'] if fiche else '?'}")
    check("fiche produit espèce inconnue → None", magazine.magazine_fiche("zzz") is None)


# ---------------------------------------------------------------------------
# H. Filtre saison = TODO nommé (offre stable quelle que soit la saison)
# ---------------------------------------------------------------------------

def test_filtre_saison_todo():
    gs = _gs()
    _poser_palier(gs, P, "tomate", 3)
    o_ete = magazine.magazine_offres(gs, P, "ete")
    o_hiver = magazine.magazine_offres(gs, P, "hiver")
    o_none = magazine.magazine_offres(gs, P, None)
    check("offre stable été/hiver/None (filtre saison inactif, TODO catalogue)",
          o_ete == o_hiver == o_none, f"{o_ete} | {o_hiver} | {o_none}")


# ---------------------------------------------------------------------------
# Cohérence corpus : toute clé du catalogue maître a une fiche produit
# ---------------------------------------------------------------------------

def test_couverture_catalogue():
    maitre = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}
    sans_fiche = [e for e in maitre if magazine.magazine_fiche(e) is None]
    check("toute espèce du catalogue maître a une fiche produit",
          sans_fiche == [], f"sans fiche : {sans_fiche}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Magazine de botanique (Voix narratives ⑥)")
    print("=" * 60)
    test_sans_palier3()
    test_soeurs_offertes()
    test_achat_valide()
    test_achat_hors_offre()
    test_fonds_insuffisants()
    test_pas_de_banque()
    test_fiche_produit()
    test_filtre_saison_todo()
    test_couverture_catalogue()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
