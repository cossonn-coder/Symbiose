"""
SYMBIOSE — tests/test_peripherie.py
Tests ciblés de la CEINTURE (sprint PÉRIPHÉRIE, tronçon ①, D73).
Spec : `docs/champs/peripherie/conception_peripherie.md` §4.1 + kickoff
`sprints/champs/peripherie/sprint_peripherie/01_ceinture.md`.

Vérifie que `fields/peripherie.py` est :
  A. DÉTERMINISTE  — même seed → même ceinture ; seeds différents → profils
                     différents (philo #3 et #7) ;
  B. D92 REFERMÉE  — LE test qui compte. Sur 300 000 seeds (pas de simulation,
                     juste du hash) : < 15 % de terrains aux 4 côtés identiques
                     (la génération C# était à 96,0 %), ≥ 5 % de terrains portant
                     une falaise (le C# n'en produisait AUCUNE), et chacun des 4
                     types non-falaise présent sur ≥ 10 % des terrains ;
  C. RIPISYLVE     — toute forêt qui touche une rivière porte aulne ou saule ;
  D. BORNÉ         — chaque scalaire dans sa plage, densité ∈ [0,1], et les champs
                     hors-type restent à leur valeur neutre.

Tronçon ② (exposition & abri) ajoute quatre suites — spec §3.1/§3.2/§4.2 + kickoff
`02_exposition_abri.md` :
  E. NEUTRALITÉ    — LE test qui protège le golden : sans ceinture (`None`) ou sur
                     une ceinture NEUTRE (prairie rase), lumière-sol / lumière reçue
                     / `eco.vent` sont BIT-IDENTIQUES, et `eco.turbulence` reste None ;
  F. SAISONNALITÉ  — une lisière au SUD vole la lumière d'hiver et rien de l'été ;
                     au NORD elle n'ombre JAMAIS le jardin. Aucune règle saisonnière
                     n'est écrite : c'est `solar_slice` qui le produit (§3.1) ;
  G. POROSITÉ      — le dense abrite PLUS et turbule PLUS, et la turbulence est
                     NON LINÉAIRE (quadratique) là où la réduction est linéaire (§3.2) ;
  H. CACHES        — ceinture inchangée ⇒ `geom_key` (lumière) et `_signature`
                     (abri) restent HIT ; un changement de densité les invalide (sans
                     quoi une coupe du ④ ne serait jamais vue).

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie
"""
import sys

from fields.light import LightField
from fields.abri import compute_abri
from fields.ecofields import init_eco
from fields.peripherie import (
    generer_ceinture, voisins, COTES, TYPES, NORD, SUD, secteur_neutre,
    MONDE_CM, PROFONDEUR_CM, rect_secteur, occulteurs, obstacles_abri,
    ESSENCES_RIPISYLVE, HAUTEUR_FORET_CM, DENSITE_FORET, DENSITE_FRICHE,
    LIGNE_EAU_CM, ALTITUDE_FALAISE_CM,
)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# Échantillon du test D92 : même taille que la mesure de référence du C#.
N_SEEDS = 300_000


# --- A. Déterminisme -------------------------------------------------------
def test_determinisme():
    print("\n[A] Déterminisme")
    for seed in (42, 7, 12345, 999_983):
        a = generer_ceinture(seed)
        b = generer_ceinture(seed)
        check(f"ceinture reproductible seed={seed}", a == b,
              " · ".join(f"{s['type']}" for s in a))
    # Deux seeds distincts doivent donner des terrains distincts (#7). On échantillonne
    # largement : le nombre de profils distincts doit être élevé, pas juste ≥ 2.
    profils = {tuple((s["type"], s["essence"]) for s in generer_ceinture(k))
               for k in range(2000)}
    check("seeds différents → profils variés", len(profils) >= 50,
          f"{len(profils)} profils distincts sur 2000 seeds")
    check("ceinture = 4 secteurs indexés N/E/S/O",
          [s["cote"] for s in generer_ceinture(1)] == list(COTES))


# --- B. D92 refermée -------------------------------------------------------
def test_d92():
    print(f"\n[B] D92 refermée — balayage de {N_SEEDS:,} seeds")
    uniformes = 0
    avec_falaise = 0
    presence = {t: 0 for t in TYPES}
    for seed in range(N_SEEDS):
        types = [s["type"] for s in generer_ceinture(seed)]
        if len(set(types)) == 1:
            uniformes += 1
        if "falaise" in types:
            avec_falaise += 1
        for t in set(types):
            presence[t] += 1

    part_unif = uniformes / N_SEEDS
    part_falaise = avec_falaise / N_SEEDS
    check("terrains aux 4 côtés identiques < 15 % (C# : 96,0 %)",
          part_unif < 0.15, f"{part_unif:.1%} ({uniformes:,})")
    check("terrains portant une falaise ≥ 5 % (C# : 0 %)",
          part_falaise >= 0.05, f"{part_falaise:.1%} ({avec_falaise:,})")
    for t in ("foret", "riviere", "prairie", "friche"):
        part = presence[t] / N_SEEDS
        check(f"type '{t}' présent sur ≥ 10 % des terrains",
              part >= 0.10, f"{part:.1%}")


# --- C. Ripisylve ----------------------------------------------------------
def test_ripisylve():
    print("\n[C] Ripisylve — une forêt de berge est un aulne ou un saule")
    n_ripi = n_seche = 0
    ok_ripi = ok_seche = True
    for seed in range(20_000):
        ceinture = generer_ceinture(seed)
        types = [s["type"] for s in ceinture]
        for s in ceinture:
            if s["type"] != "foret":
                # Hors forêt : aucune essence dominante (la ceinture est un agrégat,
                # une friche n'a pas de dominante — cf. tronçon ③).
                ok_seche = ok_seche and s["essence"] is None
                continue
            bord_de_leau = any(types[v] == "riviere" for v in voisins(s["cote"]))
            if bord_de_leau:
                n_ripi += 1
                ok_ripi = ok_ripi and s["essence"] in ESSENCES_RIPISYLVE
            else:
                n_seche += 1
                ok_seche = ok_seche and s["essence"] not in ("saule",)
    check("toute forêt adjacente à une rivière est aulne/saule", ok_ripi,
          f"{n_ripi:,} secteurs de ripisylve testés")
    check("hors berge : jamais de saule, jamais d'essence sur un non-boisé",
          ok_seche, f"{n_seche:,} forêts sèches testées")
    check("les deux cas existent dans l'échantillon", n_ripi > 0 and n_seche > 0)


# --- D. Bornes -------------------------------------------------------------
def _dans(v, plage):
    return plage[0] - 1e-6 <= v <= plage[1] + 1e-6


def test_bornes():
    print("\n[D] Bornes des scalaires")
    fails = []
    for seed in range(20_000):
        for s in generer_ceinture(seed):
            typ = s["type"]
            if not 0.0 <= s["densite_ligneuse"] <= 1.0:
                fails.append(("densite hors [0,1]", seed, s))
            if typ == "foret":
                if not (_dans(s["hauteur_canopee"], HAUTEUR_FORET_CM)
                        and _dans(s["densite_ligneuse"], DENSITE_FORET)):
                    fails.append(("foret", seed, s))
            elif typ == "friche":
                if not _dans(s["densite_ligneuse"], DENSITE_FRICHE):
                    fails.append(("friche", seed, s))
            elif typ == "riviere":
                if not _dans(s["ligne_eau"], LIGNE_EAU_CM):
                    fails.append(("riviere", seed, s))
            elif typ == "falaise":
                if not _dans(s["altitude_relative"], ALTITUDE_FALAISE_CM):
                    fails.append(("falaise", seed, s))
            # Champs hors-type : restent à leur valeur neutre.
            if typ != "foret" and s["hauteur_canopee"] != 0.0:
                fails.append(("hauteur parasite", seed, s))
            if typ not in ("foret", "friche") and s["densite_ligneuse"] != 0.0:
                fails.append(("densite parasite", seed, s))
            if typ != "riviere" and s["ligne_eau"] != 0.0:
                fails.append(("ligne_eau parasite", seed, s))
            if typ != "falaise" and s["altitude_relative"] != 0.0:
                fails.append(("altitude parasite", seed, s))
            if s["souche_memory"] is not None or s["annees_depuis_coupe"] != 0.0:
                fails.append(("cinetique non vierge", seed, s))
    check("tous les scalaires dans leurs plages, aucun champ parasite",
          not fails, fails[0] if fails else "20 000 seeds × 4 secteurs")


# ===========================================================================
# TRONÇON ② — exposition & abri
# ===========================================================================
# Le jardin fait 20×20 m = 40×40 plots : une grille de cette taille placée à
# l'origine monde (0,0) EST le jardin, donc la ceinture l'encadre exactement.
COTE_PLOTS = int(MONDE_CM / 50.0)


def _neutre():
    """Ceinture NEUTRE : 4 prairies rases. L'état opt-in de référence."""
    return [secteur_neutre(cote) for cote in COTES]


def _foret(cote, hauteur=1500.0, densite=0.9):
    """Ceinture neutre SAUF un secteur boisé (hauteur en cm, densité ∈ [0,1])."""
    ceinture = _neutre()
    ceinture[cote].update(type="foret", essence="hetre",
                          hauteur_canopee=hauteur, densite_ligneuse=densite)
    return ceinture


def _sol(ceinture, saison, rows=COTE_PLOTS, cols=COTE_PLOTS):
    """Grille de lumière-sol du jardin entier pour une saison + une ceinture."""
    lf = LightField(rows, cols)
    lf.compute([], saison, ceinture=ceinture)
    return [row[:] for row in lf.data]


# --- E. Neutralité (protège le golden) -------------------------------------
def test_neutralite():
    print("\n[E] Neutralité — ceinture absente ou neutre ⇒ champs bit-identiques")
    check("géométrie : aucun occulteur sur une ceinture neutre",
          occulteurs(None) == [] and occulteurs(_neutre()) == [])
    check("géométrie : aucun obstacle d'abri sur une ceinture neutre",
          obstacles_abri(None) == [] and obstacles_abri(_neutre()) == [])
    # La bande encadre bien le jardin (repère sol x=Est, y=Sud → Nord en y<0).
    check("bande nord = [0,MONDE]×[−PROFONDEUR,0]",
          rect_secteur(NORD) == (0.0, -PROFONDEUR_CM, MONDE_CM, 0.0))
    check("bande sud = [0,MONDE]×[MONDE,MONDE+PROFONDEUR]",
          rect_secteur(SUD) == (0.0, MONDE_CM, MONDE_CM, MONDE_CM + PROFONDEUR_CM))

    for saison in ("hiver", "printemps", "ete", "automne"):
        sans = _sol(None, saison, 12, 12)
        avec = _sol(_neutre(), saison, 12, 12)
        check(f"lumière-sol bit-identique sans/ceinture-neutre ({saison})",
              sans == avec)

    # Abri : même champ `vent`, et pas de champ de turbulence alloué.
    eco_a = init_eco("a", 12, 12)
    eco_b = init_eco("b", 12, 12)
    compute_abri(eco_a, [], None, (0.0, 0.0), 0.0, 0.8)
    compute_abri(eco_b, [], None, (0.0, 0.0), 0.0, 0.8, _neutre())
    check("eco.vent bit-identique sans/ceinture-neutre",
          eco_a.vent.data == eco_b.vent.data)
    check("eco.turbulence reste None (aucun obstacle poreux)",
          eco_a.turbulence is None and eco_b.turbulence is None)


# --- F. Saisonnalité de l'ombre (§3.1) -------------------------------------
def test_saisonnalite():
    print("\n[F] Saisonnalité — la géométrie solaire suffit (aucun `if saison`)")
    # Un plot témoin au BORD NORD du jardin, à 20 m de la lisière sud.
    r_nord, c_mid = 0, COTE_PLOTS // 2
    sud = _foret(SUD, hauteur=1500.0, densite=0.9)

    h_sans = _sol(None, "hiver")[r_nord][c_mid]
    h_avec = _sol(sud, "hiver")[r_nord][c_mid]
    e_sans = _sol(None, "ete")[r_nord][c_mid]
    e_avec = _sol(sud, "ete")[r_nord][c_mid]
    perte_hiver = 1.0 - h_avec / h_sans
    perte_ete   = 1.0 - e_avec / e_sans
    # À 20 m de la lisière, l'hiver perd la tranche de MIDI (ombre de 47 m) ; les
    # tranches ±45° arrivent trop obliquement pour que la bande de 20 m de LONG
    # projette encore sur ce plot (le soleil bas du matin jette son ombre au NO,
    # à côté du terrain). D'où une perte franche mais partielle — attendu.
    check("lisière SUD : bord nord fortement assombri en HIVER",
          perte_hiver > 0.40, f"{h_sans:.3f} → {h_avec:.3f} (−{perte_hiver:.0%})")
    check("lisière SUD : bord nord quasi inchangé en ÉTÉ",
          perte_ete < 0.05, f"{e_sans:.3f} → {e_avec:.3f} (−{perte_ete:.0%})")
    check("l'asymétrie hiver/été sort de la seule géométrie solaire",
          perte_hiver > 8.0 * max(perte_ete, 1e-9))

    # Une lisière au NORD n'ombre JAMAIS le jardin : à nos trois tranches
    # horaires (−45°/0/+45°) le soleil reste dans la moitié SUD du ciel, donc
    # l'ombre part toujours vers le nord — elle s'éloigne du terrain.
    nord = _foret(NORD, hauteur=1500.0, densite=0.95)
    ok_nord = all(_sol(None, s) == _sol(nord, s)
                  for s in ("hiver", "printemps", "ete", "automne"))
    check("lisière NORD : lumière-sol INCHANGÉE aux 4 saisons", ok_nord)


# --- G. Porosité : réduction linéaire, turbulence quadratique (§3.2) -------
def _abri_lisiere(densite, force=0.8):
    """`(vent, turbulence)` au plot témoin sous le vent d'une lisière nord."""
    eco = init_eco("t", COTE_PLOTS, COTE_PLOTS)
    # Vent venant du NORD (direction 0) → sillage vers le sud, dans le jardin.
    compute_abri(eco, [], None, (0.0, 0.0), 0.0, force,
                 _foret(NORD, hauteur=1500.0, densite=densite))
    r, c = 0, COTE_PLOTS // 2
    return eco.vent.at_plot(r, c), eco.turbulence.at_plot(r, c)


def test_porosite():
    print("\n[G] Porosité — le dense abrite plus ET turbule plus (non linéairement)")
    force = 0.8
    v_dense, t_dense = _abri_lisiere(0.9, force)
    v_clair, t_clair = _abri_lisiere(0.5, force)
    check("le dense réduit PLUS le vent moyen", v_dense < v_clair,
          f"dense {v_dense:.3f} < clair {v_clair:.3f} (masse d'air {force})")
    check("le dense produit PLUS de turbulence", t_dense > t_clair,
          f"dense {t_dense:.3f} > clair {t_clair:.3f}")
    check("turbulence ≥ 1 (c'est un surcroît de rafale, jamais un abri)",
          t_dense >= 1.0 and t_clair >= 1.0)
    # NON-LINÉARITÉ : l'écart RELATIF de turbulence doit dépasser celui de la
    # réduction — c'est toute la leçon (§3.2), la quadratique ne mord que sur le
    # très dense, donc éclaircir un peu coupe les rafales sans perdre l'abri.
    ratio_red  = (force - v_dense) / (force - v_clair)
    ratio_turb = (t_dense - 1.0) / (t_clair - 1.0)
    check("turbulence NON LINÉAIRE (écart plus marqué que la réduction)",
          ratio_turb > ratio_red + 1e-9,
          f"turbulence ×{ratio_turb:.2f} vs réduction ×{ratio_red:.2f}")


# --- H. Caches (perf) ------------------------------------------------------
def test_caches():
    print("\n[H] Caches — HIT à ceinture figée, MISS dès qu'une densité bouge")
    ceinture = _foret(SUD, hauteur=1500.0, densite=0.8)

    # LUMIÈRE : on marque le champ après le 1er calcul. Un cache HIT ne le
    # réécrit pas (la marque survit) ; un MISS le recalcule (la marque disparaît).
    lf = LightField(12, 12)
    lf.compute([], "ete", ceinture=ceinture)
    lf.data[0][0] = -42.0
    lf.compute([], "ete", ceinture=ceinture)
    check("light : ceinture inchangée ⇒ cache HIT (champ réutilisé)",
          lf.data[0][0] == -42.0)
    eclairci = [dict(s) for s in ceinture]
    eclairci[SUD]["densite_ligneuse"] = 0.4
    lf.compute([], "ete", ceinture=eclairci)
    check("light : densité changée ⇒ cache MISS (une coupe est VUE)",
          lf.data[0][0] != -42.0)

    # ABRI : le cache stocke la grille de facteur ; à signature stable c'est le
    # MÊME objet qui ressort (aucune reconstruction géométrique).
    eco = init_eco("t", 12, 12)
    compute_abri(eco, [], None, (0.0, 0.0), 0.0, 0.8, ceinture)
    facteur = eco._abri_cache[1]
    compute_abri(eco, [], None, (0.0, 0.0), 0.0, 0.6, ceinture)
    check("abri : ceinture inchangée ⇒ facteur non reconstruit",
          eco._abri_cache[1] is facteur)
    compute_abri(eco, [], None, (0.0, 0.0), 0.0, 0.6, eclairci)
    check("abri : densité changée ⇒ facteur reconstruit",
          eco._abri_cache[1] is not facteur)


def main():
    test_determinisme()
    test_ripisylve()
    test_bornes()
    test_neutralite()
    test_saisonnalite()
    test_porosite()
    test_caches()
    test_d92()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_peripherie] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_peripherie] PASS")


if __name__ == "__main__":
    main()
