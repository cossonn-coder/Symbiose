## 2026-06-15 — Sprint décompo & compost · sous-sprint ⑤ : structures posables (bac/pile) — golden NEUTRE — ⑤ CLOS

Le **canal vertueux** qui ferme la boucle de décomposition (③④ posaient « laisser
pourrir → nuisibles » ; ⑤ pose « cueillir & composter → sol vivant », philo #1/#6).
Trois phases internes (modèle ②), chacune golden-NEUTRE et testée, livrées dans la
journée.

**Phase A — modèle + poser + composter/empiler.** `Structure{kind, plot, contenu:
list[Parcelle], compost_mur}` portée par `eco.structures` (couche `fields`, à côté
de `litiere` — décision #1). Contenu = réutilisation de `Parcelle` (#2). Helper
`_fusion_parcelle` extrait (fusion par tissu PARTAGÉE litière ↔ structures,
refactor bit-identique). **Décision ⑤A** (dévie de la lettre du §5) : le bac
**refuse `diffus`** (exsudats DANS le sol, non ramassables) — `STRUCTURE_ACCEPTE =
{bac: {feuille,fleur,herbace,fruit}, pile: {bois}}`. Gestes `poser_bac`/`poser_pile`
(`MODÉRÉ`, planification), `composter`/`empiler_bois` (`FAIBLE`, déplacent les
parcelles plot→structure, masse conservée).

**Phase B — maturation + jauge + retourner.** **Décision #3 volet B** (carte
blanche, interprétation la plus fidèle) : la maturation est une **décompo CONFINÉE**,
miroir de `tick_decomposition` — chaque parcelle mûrit à la cinétique de son tissu
(`TISSU.decay`), la masse quitte le contenu (le tas fond), la fraction humifiée+
minéralisée s'accumule dans `compost_mur`, le reste est respiré (conservation
honnête). `eco.tick_structures()` appelé étape 4b (juste après `tick_decomposition`),
**no-op strict si `structures == []`** (invariant golden). Geste `retourner`
(drapeau `retourne_restant`, ×2 vitesse + lissage d'âges pendant `RETOURNE_DUREE`).
Biais cinétique pile (bois) ≪ bac (tendre).

**Phase C — epandre + amendement pile + habitat.** **Décision #3 volets trio/
habitat** (placeholders kickoff) : `epandre(struct→plot, q)` **borné** par
`compost_mur` (demande > jauge tronquée ; jauge vide → refus EN AMONT, zéro Vigueur,
modèle `planter`) → **trio humus** `EPANDRE_W` : bac `{om_stable:0.6, microbiome:
0.3, fertilite:0.3}`, **pile = bac ×(1.3,0.5,0.4)** (biais structure, humus
forestier peu nourrissant). Dépôt via `GridField.add` **borné** — `microbiome`
ENSEMENCÉ, pas un `set` (philo #4). `epandre` est le SEUL geste ⑤ qui écrit le sol
(comme `becher`/`arroser`, un geste joueur amende un champ ; pas un bonus DIRECT sur
une plante — la réponse émerge au tick). **Habitat pile (§4.1, sobre)** :
`poser_pile` pose une **rondelle `auxiliaire`** sur la tuile (patron exact de
`favoriser_auxiliaire`, lue par `_stability_grid`) — zéro champ neuf ; le local au
plot reste différé (D30). `poser_pile` prend désormais `tile` (asymétrie voulue :
seule la pile a l'habitat).

**Pont `sim_server.py` 0.3.4 → 0.3.5** : snapshot expose `eco.structures` par tuile
(`[{kind, plot, compost_mur}]`, index = `target.structure`) ; routeur des **6
gestes** (poser_bac/poser_pile/composter/empiler_bois/retourner/epandre). Validation
des bornes + cohérence kind/geste (composter↔bac, empiler↔pile) côté serveur = refus
de désignation qui ne coûte rien.

**Décision :** ⑤ touche un état moteur neuf et 5 gestes mais reste **golden NEUTRE
sur les 3 phases** — `908f591bee…` / `435e6f72…` **bit-identiques à ②** (le smoke,
succession pure, ne pose aucune structure ; `tick_structures` est un no-op à liste
vide ; les gestes sont event-driven hors tick). Neutralité **prouvée**, pas supposée.

`tests/test_structures.py` : **65 checks** (A 34 → B 48 → C 65). `tests/
test_sim_server.py` : **123** (+10, pont 0.3.5 + aller-retour réel poser→composter→
retourner→epandre + index/kind invalides refusés). Suites vertes : golden,
population, structures 65, sim_server 123, vigueur 135, croissance 67, competition,
eau 20, génétique 20, maîtrise 35, maîtrise_detection 20, signes 8, ombre_maison 4,
phototropisme 11, planter, sénescence, fruits 21, attraction, auxiliaires (régulation
OK). `main.py 5` exit 0.

**Sous-sprint ⑤ CLOS — sprint décompo & compost : ①②③④⑤ moteur TOUS FAITS.**
**Reste ⑥ vue Godot** (différé tant que l'intégration Godot est en pause :
post-mortem visible, litière, maturité-fruit, bac/pile + jauge, auxiliaires autour
de la pile). Tous les hooks moteur sont posés (`plant.fruits`, `eco.structures` au
snapshot ; rondelle `auxiliaire` de la pile). Reprise : `00_etat.md` §REPRISE.

---
