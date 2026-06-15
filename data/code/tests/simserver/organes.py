"""
SYMBIOSE — tests/simserver/organes.py
Section 9 : hints organes (tranche 6·A). Chaque plante du snapshot porte
foliage_density (0..1, saisonnier), organ (proxy REPRO_BY_SEASON + repli DEFAUT)
et organ_site (terminal|lateral) ; caduc en hiver → densité 0 et organ null pour
tout le monde. Pur rendu, lecture seule.
"""
import json

from .harness import check, ServerProc


def test_hints_organes():
    print("[hints organes]")
    ORGANES = {None, "flower", "fruit_unripe", "fruit_ripe"}
    s9 = ServerProc()
    s9.send(cmd="init", seed=42)
    snap = s9.send(cmd="snapshot")["snapshot"]
    check("schéma plante : les 3 hints présents",
          all(all(k in p for k in ("foliage_density", "organ", "organ_site"))
              for p in snap["plants"]))
    check("foliage_density ∈ [0,1]",
          all(0.0 <= p["foliage_density"] <= 1.0 for p in snap["plants"]))
    check("organ_site ∈ {terminal, lateral}",
          all(p["organ_site"] in ("terminal", "lateral")
              for p in snap["plants"]))
    check("organ ∈ {null, flower, fruit_unripe, fruit_ripe}",
          all(p["organ"] in ORGANES for p in snap["plants"]))
    # Semaine 1 = printemps : la table (Tomato/AppleTree) ET le repli DEFAUT
    # disent « flower » — personne ne fructifie au printemps.
    check("printemps : organ = flower partout",
          all(p["organ"] == "flower" for p in snap["plants"]),
          f"organes={ {p['organ'] for p in snap['plants']} }")
    pommier = next(p for p in snap["plants"] if p["species"] == "AppleTree")
    dens_printemps = pommier["foliage_density"]
    check("pommier feuillé au printemps", dens_printemps > 0.0,
          f"densité={dens_printemps}")

    # Traverser été (sem 14 : pommier fruit_unripe ≠ tomate fruit_ripe — les
    # cycles d'espèces divergent, critère F5) puis hiver (sem 40 : caduc nu).
    while snap["week"] < 14:
        snap = s9.send(cmd="step_week")["snapshot"]
    par_espece = {p["species"]: p["organ"] for p in snap["plants"]}
    check("été : pommier fruit_unripe, tomate fruit_ripe (cycles distincts)",
          par_espece.get("AppleTree") == "fruit_unripe"
          and par_espece.get("Tomato", "fruit_ripe") == "fruit_ripe",
          f"été={par_espece}")
    while snap["week"] < 40:
        snap = s9.send(cmd="step_week")["snapshot"]
    check("hiver : organ null partout",
          snap["season"] == "hiver"
          and all(p["organ"] is None for p in snap["plants"]),
          f"semaine {snap['week']}, organes="
          f"{ {p['organ'] for p in snap['plants']} }")
    pommier = next((p for p in snap["plants"] if p["species"] == "AppleTree"),
                   None)
    check("hiver : le pommier (caduc) a foliage_density = 0",
          pommier is not None and pommier["foliage_density"] == 0.0,
          pommier and f"densité={pommier['foliage_density']}")
    # Mesure du surcoût des hints (kickoff : ~+60 o/plante attendu, vérifier).
    size = len(json.dumps(snap, sort_keys=True, separators=(",", ":")))
    print(f"  📏 taille snapshot semaine {snap['week']} avec hints : {size} "
          f"octets ({len(snap['plants'])} plantes)")
    s9.send(cmd="quit")
    check("quit hints → exit 0", s9.close() == 0)
