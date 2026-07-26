# 2026-07-26 — Conception PÉRIPHÉRIE (D73) FIGÉE — le jardin n'est pas une île

`/conception` lancée sur l'**amorce de terraforming** rédigée par Nico le même jour
(12 questions ouvertes, aucune décision prise). Résultat : conception figée en
`docs/champs/peripherie/conception_peripherie.md` + 7 tronçons prêts pour
`/sprint-auto` dans `sprints/champs/peripherie/sprint_peripherie/`.

## Ce que le repérage a changé — 6 prémisses de l'amorce périmées

L'amorce était juste sur le fond écologique mais avait été écrite sans lire le moteur.
Le balayage (grep + lecture directe, revérifié) a invalidé six hypothèses, et le
périmètre s'en trouve **considérablement réduit** :

1. **Le vent est implémenté ET branché**, bien au-delà de ce que l'amorce supposait :
   `sim/wind.py` (masse d'air pure) + **`fields/abri.py` = champ d'abri spatial complet**
   (capsule de sillage, portée ∝ hauteur, venturi, cache angulaire, mutualisation de
   `_point_in_capsule`), lu par l'évaporation, le wind chill, la thigmomorphogénèse
   (`wind_memory` → `port_trapu`), les butineurs, l'anémophilie et les dégâts de rafale.
   `_obstacles()` liste maison + plantes hautes ⇒ **la lisière y entre comme une ligne
   de plus**. Le « brise-vent » que l'amorce présentait comme un flux à concevoir fait
   ~20 lignes.
2. **Le patron « obstacle global en coordonnées MONDE » existe** (la maison, dans
   `light.compute` et `abri._obstacles`) ⇒ **aucun « masque d'horizon » à inventer**.
3. **Le point chaud perf redouté n'existe pas** : `light.py` a un cache géométrique
   (`geom_key` → `return []` si inchangé) et `abri.py` son `_signature`. La ceinture
   étant statique, elle y entre comme quelques scalaires. Budget réel **< +2 % de tick**,
   pas le poste D32.
4. **L'hydrologie est implémentée**, pas seulement conçue (`tick_hydrology`,
   `tick_ruissellement`, `tick_marais`, `est_marais`, gestes `creuser`/`drainer` avec
   coûts et outil « bêche » déjà déclarés) ⇒ Q6 tranchée, le barrage a un support.
5. **`sim/outils.py` existe** (D82, l'Atelier) avec registre data-driven et grammaire
   `GESTE_UNLOCK` ⇒ gater `abattre` sur une hache = deux entrées de registre. **D93 est
   partiellement périmée** : il n'y a pas de modèle d'outils à concevoir.
6. **Le golden ne pose aucune maison** ⇒ une ceinture opt-in le laisse **INTACT**. Le
   « re-figeage LARGE » annoncé par l'amorce est **évitable, donc évité** : une dérive
   dont on n'a pas besoin est une dérive qu'on ne saura pas expliquer dans six mois.

**D92 quantifiée** par réplication du hash C# sur 300 000 seeds : **287 929 terrains
(96,0 %) ont les 4 côtés identiques, 0 falaise** (`PPPP` 120 393 · `FFFF` 95 531 ·
`RRRR` 72 005). Le bug est réel et massif — mais il **disparaît par construction** dès
que la génération migre en Python. **D73 absorbe D92** ; ce n'était pas un prérequis.

## Décisions de Nico

- **Maille & vérité** : **4 secteurs cardinaux** en état moteur Python, la vue
  consomme le snapshot (la couture `SurroundingsProfile` de D58·T4 était écrite pour ça).
- **Un seul sprint**, ordre interne entrant → sortant. L'ordre défendu par l'amorce
  reste juste, mais n'avait pas besoin d'être une frontière de sprint : couper en deux
  aurait fait repayer deux fois l'amorçage de la ceinture.
- **« Comptabilisé »** = ledger + trace dans le milieu + matière (`mulch_stock`
  existant), coût Vigueur justifié par l'**effort physique** et non par « action directe
  sur le vivant » (l'arbre périphérique est un agrégat, pas une `PlantInstance` ; fonder
  un barème sur cette fiction se paierait plus tard). **Aucun indicateur cumulé** (#5).

## Trois trous comblés dans l'amorce

- **Le brise-vent poreux, et pourquoi la règle des manuels ne s'applique pas ici.**
  « Une haie poreuse protège jusqu'à 20-30 H contre 10-15 H pour un mur » ne s'exprime
  **pas** à cette échelle : derrière une lisière de 15 m, un jardin de 20 m tient entre
  0 et 1,3 H, où le mur plein est *le plus* protecteur. Ce qui s'exprime à 0-3 H, c'est
  la **turbulence de décollement** — le vent qui tombe par-dessus le mur. D'où deux
  formules : réduction du vent moyen **linéaire** en (1−φ), rafale **quadratique**.
  Leçon de design, entièrement émergente : *une lisière trop dense abrite du vent
  constant mais fait tomber des rafales ; l'éclaircir réduit la casse sans perdre
  l'abri.* Ce n'est pas « couper c'est mal », c'est « couper bien est un savoir-faire ».
- **Le corridor faune était un piège #2.** Le champ de population colonise déjà depuis
  zéro : il n'y a pas de barrière de dispersion à lever, et « la périphérie augmente
  l'habitat » aurait été un bonus déguisé. Formulation retenue : un **champ du milieu**
  `eco.lisiere` que chaque guilde lit à sa manière via un poids déclaré (défaut 0.0).
- **La rivière n'a pas de grille hydraulique hors jardin.** « La même physique appliquée
  hors terrain de jeu » était faux — `altitude`/`eau_surface` s'arrêtent au bord. Le
  barrage devient une **condition aux limites** ; le ruissellement et `marais_memory`
  existants produisent ensuite le marécage, sans script.

## Note d'honnêteté versée à la conception

Le garde-fou « surtout pas de stock » de l'amorce est **déjà contredit par le projet** :
`mulch_stock` existe et est assumé. Le vrai garde-fou n'est pas « pas de stock », c'est
**pas de chiffre en HUD** (#5) et **rien d'épuisable** (#4).

## Le sprint

7 tronçons, **golden INCHANGÉ partout** (aucun re-figeage autorisé) :
① ceinture + D92 → ② exposition/abri → ③ graines/eau/corridor → ④ gestes forestiers
→ ⑤ eau/roche/érosion → ⑥ voix → ⑦ vue Godot.

Une seule espèce ajoutée, le **saule** (archétype de la trogne, se bouture spontanément
→ croise le canal d'acquisition #2), avec ses 5 voix. Noisetier et prunellier écartés,
gardés au backlog.

Cinétiques : trogne 5 ans · recépage 10 ans (mais **le hêtre et le bouleau ne rejettent
pas** — recéper une hêtraie, c'est l'abattre) · abattage → canopée 30 ans · entaille de
falaise **jamais** · barrage non entretenu rompt vers 8 ans.

**Dettes** : D73 conçue et prête · **D92 absorbée** · **D93 périmée** pour ce périmètre ·
**D94 ouverte** (donner leur vraie porosité aux haies du jardin — dérive golden assumée,
sprint de calibrage à part). Re-tag `rendu/ambiance` → **`champs/peripherie`** (le sujet
est moteur, pas rendu), thème documentaire créé.
