"""
SYMBIOSE — tests/peripherie/exposition.py
TRONÇON ② — exposition & abri : ce que la ceinture fait à la LUMIÈRE et au VENT.
Spec `docs/champs/peripherie/conception_peripherie.md` §3.1/§3.2/§4.2 + kickoff
`sprints/champs/peripherie/sprint_peripherie/02_exposition_abri.md`.

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
"""
from fields.light import LightField
from fields.abri import compute_abri
from fields.ecofields import init_eco
from fields.peripherie import (
    NORD, SUD, MONDE_CM, PROFONDEUR_CM, rect_secteur, occulteurs, obstacles_abri,
)

from tests.peripherie.harness import check, COTE_PLOTS, _neutre, _foret, _sol


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
