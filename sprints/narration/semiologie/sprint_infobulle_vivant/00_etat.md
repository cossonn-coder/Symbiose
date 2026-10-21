# Sprint INFO-BULLE DU VIVANT — état partagé

> Conception **FIGÉE le 2026-10-22** (`/conception`) →
> [`docs/narration/semiologie/conception_infobulle_vivant.md`](../../../../docs/narration/semiologie/conception_infobulle_vivant.md)
> (LIRE AVANT TOUT TRONÇON). Absorbe **D110 (a)(b)(g)**. **Golden jamais re-figé** :
> référence `22768f33…` (`cd data/code && python3 -m tests.test_golden`). Jamais
> `test_epaisseur_500ans`. Pont de départ : 0.5.46.

## Décisions clés (Nico, 2026-10-22)
1. Nom bête/champignon révélé par **observation en 3 saisons distinctes** (+1 palier par
   saison neuve au survol, plafond `SEUIL_CARNET`) ; champignon = 3 automnes, assumé.
   Règle CLAUDE.md « non identifiable sans maîtrise » conservée.
2. Affichage technique (Maj+F3) : nomme tout dès le 1er survol, avec chiffres.
3. État bête = **abondance** (vue dans le plot) + **nourriture** (`activite`, révélée avec
   le nom). Pas de maladie animale (absente du moteur).
4. Champignon : rôle lu sur place (bois → décompose ; racines → relie ; sinon lie l'humus) ;
   état = densité du réseau.
5. (g) seuil de visibilité **mesuré au rendu** ; voix saine (vert franc / automne / terne).
6. Crédit saisonnier : effet de bord assumé sur `palier_bonus` (Vigueur max ↑ un peu).

## Constats d'entrée (vérifiés au code)
- `SigneDominant` retient l'intensité > 0 ; teinte = intensité × 0,7 puis palette 34.
- Faune : sprite `[r, c, x, y, activite]` ; carpophore `[r, c, x, y, densite]`.
- `ForagerLayer` : aucune ressource reçue (à vérifier/ajouter en ①).
- Dédup vue `_especesMacroObservees` = une fois par session → bloque le crédit saisonnier.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_python_corpus_credit.md` | corpus, crédit saisonnier, `appris` champignon, snapshot rôle carpophore, bandes nourriture mesurées, légende, pont bumpé | intact `22768f33…` | **FAIT** (2026-10-22, pont 0.5.47) |
| ② | `02_vue_plante_seuil_voix.md` | seuil mesuré (capture VM) + voix saine + technique | intact | **FAIT** (2026-10-22, golden intact, build vert) |
| ③ | `03_vue_faune_champignon_bilan.md` | lignes bête/carpophore, dédup (clé, saison), technique, bilan, F5, clôture | intact | à faire |

## Livré en ① — formes dont la vue dépend (pont 0.5.47)
- **Snapshot** `carpophores[tuile]` = `[r, c, x_frac, y_frac, densite, role]`, `role` ∈
  `b` (bois frais) / `r` (racines vivantes) / `h` (humus) — `sim/champignon_role.py`.
- **Snapshot** `foragers[tuile]` = `[guild, r, c, x_frac, y_frac, cible, charge, nourriture]`
  (8ᵉ champ = `activite` du champ pollinisateur au plot, 2 déc.).
- `player.appris.faune` contient aussi **`champignon`** (même liste, en dernier).
- `observer` (bête ou `champignon`) : +1 palier par saison absolue neuve, plafond
  `SEUIL_CARNET` ; mémoire `maitrise[joueur]["_saisons_vues"] = {clé: saison}`
  (`sim/signes.crediter_saison`). Jamais les plantes. La vue doit renvoyer `observer`
  au moins une fois par (clé, saison) → dédup ③.
- **`legende`** ajoute : `faune_role {bête: rôle}`, `champignon {vu, roles{b,r,h}}`,
  `voix_saine {franc, automne, terne}`, `abondance {libelles{seule,quelques,nombreuses},
  quelques: 2, nombreuses: 4}`, `nourriture {libelles{rare,suffisante,abondante},
  suffisante, abondante}`, `reseau {libelles{clairseme,dense}, dense: 0.70}`.
  Règles : n < `quelques` → seule ; < `nombreuses` → quelques ; activite < `suffisante`
  → rare ; < `abondante` → suffisante ; densite ≥ `dense` → dense.

## Prémisses corrigées / points ouverts (①)
- « Cap 4 par plot » (conception §3) est FAUX depuis 0.5.45 : `peindre_presence` peint
  1 individu/espèce/tuile + ≤ 3 points chauds, grappes ≤ 6 (puceron, moustique,
  cloporte). Les bornes d'abondance 1 / 2-3 / ≥ 4 restent valables.
- **Lombric et pollinisateurs ne sont jamais peints en sprite** : lombric jamais
  survolable (jamais nommé) ; pollinisateurs seulement via `ForagerLayer`.
- `ForagerLayer` ne recevait aucune ressource → ajoutée (8ᵉ champ, coût nul : grille du
  tick). Mais leur distribution diffère : avec les bornes des sprites, les butineurs
  lisent surtout « rare » (médiane 0,07 [VM, n=3205]) — à trancher en ③ (accepter, ou
  bornes propres ; tertile 1/3 butineurs = 0,00, dégénéré).
- **Aucun save global n'existe** (hook OnSeasonEnd seulement posé) : la mémoire est un
  dict str → int dans la tranche maîtrise, JSON-sérialisable tel quel ; elle sera
  conservée dès que le save sérialisera `game_state["maitrise"]`.
- Crédit via `maitrise.enregistrer_preuve` (preuve = exactement ce qui manque au palier)
  → pas de récompense de Vigueur par palier (`crediter_succes` non utilisé, conforme
  kickoff). Semaine 0 (survol avant le 1er tick) = saison de la semaine 1.
- `tools/simserver/serialize.py` à 374 LDC (🟡, était 368) — candidat `/refactor`.

## Livré en ② (vue plante)
- `PlantRenderer.SigneVisible(cause, intensité, zoom)` : colorant = palier ≥ ×2 ET i ≥
  `SeuilTeinte[cause]` (mesuré) ; marque fine = ×16 ET i > 0 (calcul : `ceil(i×4)` trous,
  trait de gel ≥ 1 px). `SigneDominant` / `ObserverSigne` ne partent plus sous le seuil.
- Voix saine (`legende.voix_saine`) : `automne ≥ SeuilAutomne` → automne ; sinon dès ×2
  seulement : `vitalite ≥ VitaliteFranche` → franc, sinon terne. **Sous ×2 : seul
  l'automne parle** (la santé n'y est pas dessinée — décision ②, non prescrite).
- Technique (Maj+F3) : ligne `vitalité x.xx · automne x.xx` + symptômes marqués
  « (sous seuil) » ou « (hors palier) ».
- Banc : `world/WorldView.BancSeuil.cs` + `visuals/PlantRenderer.BancSeuil.cs`, lancé par
  `mesures/mesure_seuil.sh` (`-p` palette SNES, `-P cause,i,png` = pose + info-bulle).
  Captures ×4 (après seulement) : `mesures/infobulle_x4_{saine,sous_seuil,au_dessus}.png`.

## Prémisses corrigées / points ouverts (②)
- La palette 34 couleurs est **OFF par défaut** (F11, F5 du 2026-10-15) : en rendu par
  défaut, toute teinte change un pixel dès i = 0,005 [VM, n=1 témoin]. Les seuils retenus
  = max des deux rendus → c'est la quantification SNES qui les fixe.
- **(g) n'est que partiellement levé** : `mesure_sante.py` montre que presque toutes les
  plantes portent `acclimatation` (n=10835 sur 10935 relevés, médiane 0,33 ≫ seuil 0,05)
  et que la vitalité médiane est 0,73 (69 % < 0,999) [VM, monde full, 104 sem., 1 relevé/4
  sem.]. Le dessin MONTRE donc bien le glauque et la ternissure : le texte reste fidèle,
  mais le pessimisme ressenti vient du moteur (acclimatation quasi universelle, vitalité
  basse), pas de l'info-bulle → à arbitrer par Nico (D110 ou nouvelle dette).

## Mesures
- Seuils colorants (max ×2/×4/×8 × palette OFF/ON) : chlorose 0,03 · asphyxie 0,075 ·
  sécheresse 0,01 · sénescence 0,1 · maladie 0,075 · ombre 0,02 · rongeur 0,2 ·
  acclimatation 0,05 ; vitalité franche ≥ 0,925 ; automne ≥ 0,03 [VM llvmpipe, n=1 témoin
  Clover banc smoke s12, grille 13 pas : seuil réel dans ]pas précédent, valeur]] — bruit
  de contrôle 0 px partout. Durée : OFF ~3 min 50, ON ~11 min 30 [VM, n=1].
- Bornes de nourriture (tertiles d'`activite` des sprites peints) : **0,23 / 0,50**
  [VM, n=18697 sprites, monde `full` seed 0x5AB1057E, 104 semaines] — script
  `mesures/mesure_nourriture.py` (~87 s [VM, n=1]). Médiane 0,42 [même run].
- Butineurs : médiane 0,07, tertiles 0,00 / 0,27 [VM, n=3205, même run].

## §F5
(procédure écrite par ③)

## §REPRISE
`/sprint-auto sprint_infobulle_vivant` — reprendre au premier tronçon « à faire »
(③ `03_vue_faune_champignon_bilan.md`). ① commité (11317ea) ; ② fait, NON commité
(commit par l'orchestrateur).
Tests ①: `python3 -m tests.test_infobulle_vivant` (27/27) ; `test_sim_server` 285/285.
