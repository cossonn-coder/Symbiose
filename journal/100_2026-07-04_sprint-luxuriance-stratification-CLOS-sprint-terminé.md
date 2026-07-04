# 2026-07-04 — Sprint LUXURIANCE PAR STRATIFICATION (D65, absorbe D62, ①→⑥) — SPRINT TERMINÉ (`/sprint-auto`)

Le jardin peut enfin **se remplir et se superposer** : un couvre-sol tapisse le
plot, se propage par ramets, réduit l'évaporation et étouffe les adventices ;
plusieurs strates coexistent visiblement. La compétition ÉMERGE de la
densification (philo #2), pas d'un verdict. **D65 absorbe D62** (rampantes
clonales) — les deux dettes closes ensemble. Golden final **`061934db…`**.

## ① Champ `couverture_sol` + hooks écologiques — golden RE-FIGÉ `15073be1…`→`d26432d3…`
Champ scalaire ∈[0,1] par plot (`fields/ecofields/couverture.py::CouvertureMixin`,
nouveau `GridField` dans `container.py`, exposé `get_field`), recalculé chaque
tick par **scatter** des empreintes des plantes de strate sol+basse (un seul
balayage, jamais un sweep — perf : LightField déjà 53 % CPU). Câblé étape 2d de la
boucle, AVANT ses deux lecteurs. Deux flux (philo #2, jamais de malus direct
plante) : (a) évaporation réduite sous couvert (`hydrologie`, `EVAP_FRAC=0.4`, l'eau
reste sous le tapis) ; (b) germination FÉRALE étouffée au-delà de 0.6 de couverture
(`succession`, bénéfice permacole). Golden re-figé annoncé (Clover strate basse sur
tuiles paires → cascade humidité/population, dérive localisée bornée). Suite
`test_population` re-figée en cascade `e7f1cf19…`→`5a1873db…` (assertions
comportementales inchangées, seul le hash de champ densité glisse). **Nico :
`test_epaisseur_500ans` INTERDIT — plus jamais lancé** (feedback gravé en mémoire).

## ② Mécanique clonale — golden RE-FIGÉ `d26432d3…`→`061934db…`
UNE mécanique paramétrée (D4), pas 3 chemins : traits `clonal_mode ∈ {none, stolon,
rhizome, drageon}` + `clonal_radius_cm` + `clonal_interval` sur `PlantBase`.
`sim/clonal.py::emettre_ramets` : plante mature+vigoureuse émet 1 ramet/tick à
offset HASHÉ (zéro RNG vivant), gaté par `couverture_sol` saturé (auto-limitation
émergente + **cap perf** des ramets) + lumière au sol (stolon/drageon l'exigent ;
rhizome l'ignore → envahissant émergent). Ramet = COPIE génétique (gènes +
expression), coût sur la mère = bouffée `stress_memory` (arbitrage graines↔ramets).
Clover passe en `stolon`. `CLONAL_VIGUEUR_SEUIL` calibré à **0.02** (décision de
l'exécutant, consignée) : la façade `vigueur_plante≈qi_local` plafonne ~0.05 sur un
plot réel — un seuil plus haut n'émettait aucun ramet (gate mort, golden serait
resté inchangé = mécanique non exercée). Re-figeage annoncé (trèfle 1→3 sur le
smoke, pas d'explosion). population INCHANGÉ.

## ③ Descripteur silhouette — NEUTRE (golden `061934db…`)
Descripteur DATA `silhouette` sur `PlantBase` (`silhouette_base()` + table
`STRATE_SILHOUETTE`), pur descripteur de rendu lu au ⑥. **Pas de nouveau champ
écologique** : `canopy_r` pilote seul ombre+uptake (D3). Overrides ciblés HORS
golden : courgette « étalée », carotte/mâche/pissenlit « rosette », myrtille
« buisson ».

## ④ Catalogue clonal ① — NEUTRE : fraisier + menthe + 5 voix
Fraisier (Rosaceae, stolon portée 45, rosette, fruitier — tapissage doux) ; menthe
(Lamiaceae, rhizome portée 90, cadence 3, gate ombre ignoré — envahissement
émergent). 5 voix chacune. Le marqueur ledger « 🌿 Ramet » (émis par `clonal.py`
depuis ② mais jamais parsé) est câblé dans `evenements.py`/`carnet.py` : cause
consignée = le mode clonal (distingue tapissage doux vs colonie envahissante).

## ⑤ Catalogue clonal ② — NEUTRE : framboisier + bambou + violette + 5 voix
Framboisier (Rosaceae, drageon portée 40, fourré) ; bambou traçant (Poaceae,
rhizome portée 120, cadence 3, envahissement extrême borné par le gate couverture
①) ; violette odorante (**Violaceae, famille neuve**, stolon d'ombre
`shade_tolerance=1.6`, mellifère précoce). 5 voix chacune ; carnet+magazine+
événements couverts automatiquement par les gabarits mode-génériques + l'offre
magazine data-driven. P28 (bambou) porte « compagnonnage » plutôt que
« non-action » (invariant `test_pages` fige exactement 3 pages non-action).

## ⑥ Vue Godot — INTACT (golden `061934db…`), build C# vert, pont 0.5.19
Pont (Python read-only) : `serialize.py` expose par plante `strate`, `silhouette`,
`clonal_mode`, + bloc creux `couverture` [[r,c,cov],…] (seuil perception
`COUVERTURE_RENDU_SEUIL=0.05`). C# (données 100 % snapshot) : empilement par strate
via biais ZIndex (sol=10…grimpante=14, y-sort intra-strate, `WorldView.Luxuriance.cs`) ;
`CouvertureLayer.cs` neuf (tapis vert jitteré hash, densité ∝ couverture, indice
visuel philo #5) ; `PlantRenderer.SetSilhouette`/`SilhouetteShape` (tapis ras /
dressée / étalée / buisson) au LOD couronne ; ramets = plantes normales déjà
dessinées. Banc F5 `bancs/luxuriance.py` enregistré. `test_sim_server` 245/245.

## Clôture
Refactor auto-léger **no-op** (fichiers du sprint tous en LDC pur < 300 🟢 ; max
`encyclopedie_corpus.py` 298). **D65 ✅ FAIT, D62 ✅ FERMÉE (absorbée)**. `dotnet
build` vert. Golden final `061934db…`, population `5a1873db…`. **Reste F5 = Nico**
sur le banc `luxuriance` : le tapis de couverture se densifie-t-il visiblement ;
l'empilement couvre-sol/potagère/grimpante est-il lisible ; les silhouettes
distinguent-elles tapis/étalée/dressée/buisson ; vitesse/densité de tapissage du
trèfle et de la violette ; seuils LOD + teinte/opacité du tapis (cosmétique) ;
calibrage `clonal_radius_cm`/`interval` et `CLONAL_VIGUEUR_SEUIL=0.02`. Signalé
(hors périmètre) : banc édaphique `carence_npk` échoue **pré-existant** (dette D41).
