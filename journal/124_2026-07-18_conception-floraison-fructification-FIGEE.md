# 2026-07-18 — Conception FLORAISON & FRUCTIFICATION (grappe D84 + D86) — FIGÉE

Skill `/conception`, diagnostic-first. Symptômes F5 (Nico) : le pommier fleurit
« début automne », les fleurs des « espèces du sud » à la « semaine 6-7 de
l'automne » et **disparaissent aussitôt** (D84) ; en jeu quasi aucun fruit ne
noue, « une seule pomme sur le pommier » (D86). Préalable biologique à D87.

## Diagnostic CONFIRMÉ (sonde empirique GDD/photopériode + lecture code)

Le modèle de floraison (`sim/engine/floraison.py`) = **double porte** : forçage
GDD (`gdd_accum` cumule `max(0, T−6)` depuis S1) ET photopériode (`daylength ∈
[13.5, 16.5] h`). `floraison` monte tant que **les deux** portes sont ouvertes.

**Sonde sous la météo du jeu** (T pic S30, solstice S25) :
- Fenêtre photopériode ouverte **S16 → S34** ;
- GDD franchit **130** (pommier, seuil patché) à **S29** → fleurit S29-34 = début
  automne ✅ ;
- GDD franchit **200** (DÉFAUT, toutes les autres espèces) à **S35**, or la
  photopériode **ferme S34** → **recouvrement NUL** → `floraison` ne monte
  jamais → **aucune espèce sauf le pommier ne peut fleurir** ✅ (= D86 : « une
  seule pomme ») ; les espèces au seuil 200 attrapent 0-1 tick au bord fermant
  → **flash de S33-34** = « fleurs du sud semaine 6-7 de l'automne, disparaissent
  aussitôt » ✅.

→ **Défaut STRUCTUREL** (le cumul GDD-depuis-S1 place toute floraison en fin
d'été/automne ; aucun mécanisme de floraison printanière), pas une régression du
sprint désync — ce dernier n'a fait que le rendre visible. « Semaine 6-7 »
entièrement résolu : comptée depuis le début de l'automne (Nico) = `wiy` S33-34.

## Correctif FIGÉ — forçage thermique événementiel

Direction **B (typage phénologique)** concrétisée, à la demande de Nico, en
**modèle de forçage thermique** (standard *GDD-to-bloom*) : floraison **armée au
FRANCHISSEMENT** d'un seuil `bloom_forcing_gdd` **BAS et par saison-cible**
(printemps/été/automne), qui **dure `bloom_duration` semaines** puis fane ; **porte
photopériode SUPPRIMÉE**. `gdd_accum` conservé (via `temp.at_plot` → intègre météo
+ ombre/ensoleillement). Répond point par point à Nico : année chaude → seuil
franchi plus tôt → **floraison précoce** ; ombre → accumulation plus lente →
**floraison tardive** (interconnexion) ; gène `phenologie_florale` → seuil
individuel (précoce/tardif) ; durée bornée → **fin de la fugacité**. État neuf
`bloom_week` (reset annuel). Calibrages actés : **pommier = printemps** (retrait du
patch `gdd_floraison=130`), `FLORA_GENE_SHIFT` **200→~20**. Limite assumée : vrais
jour-court (aster/lierre) approximés par seuil élevé (résultat juste, mécanisme non
photopériodique ; extension future si demandée). Nouaison (D86 secondaire) :
**calibrage** de la dose (`frac_nouaison`/`POLLEN_DEMI`/débit butineurs), invariant
« 0 pollinisateur → 0 fruit » préservé.

## Découpage (3 tronçons, vue Godot en dernier — règle projet)
- **① moteur floraison retypée** (`floraison.py` + données espèces + `bloom_week`) —
  tests placement/étalement/neutralité ; **golden re-figé maîtrisé SI** un fruitier
  mûr noue dans le smoke, sinon neutre.
- **② nouaison calibrée** (`decompo.py`/`butineurs.py`) — mesure puis tuning.
- **③ vue Godot + banc F5** — vue déjà branchée (désync ②③) : palettes fleur + banc
  d'observation floraison→pollinisation→nouaison→fruit ; golden intact.

Perf : **nul**. Doc `docs/conception/CONCEPTION_FLORAISON_FRUCTIFICATION.md` +
`sprints/sprint_floraison_fructification/` (00_etat + 01→03). DETTE D84/D86 →
🟢 conçu. **Prêt pour `/sprint-auto sprint_floraison_fructification`.**
