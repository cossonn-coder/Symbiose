# Sprint AUTOMNE VISIBLE (D123 + D118 (A) arbres) — état partagé

**Conception** : `docs/rendu/ambiance/conception_automne_visible.md` (figée le 2026-11-02).
**Où on en est** : ①, ② et ③ faits (③ non commité au moment de cette note), ④ à lancer.

## Décisions clés (Nico, 2026-11-02)

- **A1** Arbres du jardin dans ce sprint ; golden libre de bouger, à annoncer.
- **A2** Feuilles au sol = vérité moteur.
- **A3** Lisière 4 saisons + signes diégétiques macro (style canicule).
- **A4** De D118, seuls les 11 arbres ; le reste est le sprint suivant.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_fiches_banc.md` — fiches des 11 arbres + banc `bancs/mesure_arbres.py` + `mesures/avant.md` | intact | **fait** |
| ② | `02_port_arbres.md` — port par fiche, hauteur qui ne s'effondre plus, arbres âgés et caducs de démo | **re-figé** `82d522c8…` | **fait** |
| ③ | `03_feuilles_moteur.md` — largage étalé sous la couronne + pont (masse de feuilles, `feuillage`) | **re-figé** `ac48b170…` | **fait** |
| ④ | `04_vue_arbres.md` — recettes d'arbres, couleur d'automne par espèce, couronne qui s'éclaircit | intact | à faire |
| ⑤ | `05_vue_tapis_chute.md` — tapis lisible dès ×1 + animation de chute | intact | à faire |
| ⑥ | `06_vue_lisiere.md` — lisière 4 saisons + signes macro + protocole F5 | intact | à faire |

## Diagnostic ① : pourquoi la hauteur s'effondre (vérifié, pour le ②)

Le plafond `max_segments` n'est pas seulement suspect, il coupe la flèche. Lieu : `_elaguer`,
`sim/growth/phases.py`, en mémoire uniquement (aucune modification), `pre_croitre` seed 42.

1. **Plafond atteint vers 10-11,4 ans** (sapin 14,7 ans) [n=1 pied par arbre, grow_plant seul, sans lumière, VM],
   après une ramification brutale (4-9 segments à 5 ans, 10-67 à 10 ans) [banc]. Le relâchement de l'auxine
   en est la cause probable, non isolée. Le filet repasse ensuite souvent : 69 fois chez le bouleau avant
   15 ans [plot (2,2), gènes neutres, sans lumière, VM].
2. **Le filet ignore la flèche** : il prend les vieux improductifs, puis les segments les plus PROFONDS,
   et la flèche est l'axe le plus profond. Bouleau de 15 ans : 28 coupes sur 176 touchent le chemin vers
   le point le plus haut (12 improductifs, 16 profonds) [plot (2,2), gènes neutres, sans lumière, VM].
   Première chute : 900 → 750 cm à 11,5 ans [même pied]. La cladoptose n'y est pour rien (0 segment
   coupé sur les chutes tracées) [même pied].
3. **Second mode, effondrement total** : les coupes finissent par retirer tous les apex. Le rejet de souche
   ouvre alors un bourgeon au collet, le plafond est redépassé, et le plus vieil improductif est le bas du
   tronc : son sous-arbre emporte tout. Noyer à 23,5 ans : 70 → 2 segments en un tick ; aulne à 24,2 ans,
   même chose [plot (3,3), sans gènes fondateurs, sans lumière, VM].

**Contrefactuel** (en mémoire) : protéger le chemin collet → point le plus haut dans les deux listes du
filet rend la hauteur non décroissante de 5 à 25 ans pour les 11 arbres, au plafond inchangé [plot (2,2),
gènes neutres, sans lumière, VM]. Cela ne suffit pas : figuier 12 segments et noyer 21 segments à 25 ans
[même mesure], le mode 3 reste à traiter. `axe_porteur` (`cladoptose.py`) n'est PAS le bon axe : il suit
le plus épais, et le protéger laisse la hauteur chuter (bouleau 251 cm à 15 ans) [même mesure]. Relever
seul le plafond à 300 ne guérit pas non plus (bouleau 515 cm à 15 ans, plafond à nouveau atteint) [même
mesure], et un plafond ôté fait exploser le temps de calcul (arrêté après 3 min sans résultat, n=1, VM).

**Autres constats pour la suite**
- `port_archetype` n'est lu par aucun code (grep Python + C#, hors tests) : au ②, le port ne peut venir
  que des paramètres de croissance.
- `semaine_abscission` n'a pas de composante par espèce : pivot s34, bornes s30-36 commune à tous, seul le
  gène décale. Les fiches visent s29-38 selon l'espèce. Conséquence pour le ③ : les couleurs diffèrent
  (④), pas les dates, sauf décision contraire. Non tranché ici.
- Le banc ne reproduit la conception qu'au plot (3,3) avec gènes fondateurs : d'où ce choix dans
  `bancs/mesure_arbres.py`. Coût : ~8 s [n=1, VM].

## Bilan ② (chiffres et limites : `mesures/apres_port.md`)

- **Effondrement fermé** par 3 changements : le plafond d'un ligneux ne coupe plus le chemin collet → point le plus
  haut et ne retire jamais plus que l'excédent (`_tailler_ligneux`) ; un rameau sec coupé réveille un bourgeon ;
  `axe_porteur` inclut ce chemin, car en jeu une rafale coupait aussi la flèche (cerisier 500 → 211 cm [seed 42, n=1, VM]).
  Écart au diagnostic ① : protéger la flèche dans `_elaguer` ne suffisait pas.
- **Monde de démo** : `_pre_vieillir_ligneux` (11 ans), caducs dans `main.CADUCS_DEMO` (SO, O, SE, hors tuile S).
- **À trancher** : population −19 % en an 2 [n=1 graine, VM], cause non isolée ; cerisier à vitalité 0,73 après 3 ans
  [n=1 run] ; `plants/perennials.py` à 419 LDC, au-dessus de 400 → `/refactor` en fin de sprint.
- **Tests adaptés** : `base.py` (91 plantes), `test_croissance` (couronne du sapin), `test_bois_mort` (plafond 8, un
  plafond à 2 ne laisse plus tomber de bois puisque la flèche est protégée).

## Bilan ③ (chiffres et limites : `mesures/apres_feuilles.md`)

- **Largage** : réparti sur `foliar_plots` de la tuile, étalé sur `CHUTE_SEMAINES` = 4 (dernier dépôt s39, fenêtre de
  `boucle.py` élargie). Masse = `FEUILLE_PAR_PLOT` (0,30) × surface de couronne. Pont **0.6.3** : 9ᵉ champ de `litiere`
  (masse `feuille`) et `feuillage` par plante vivante, lue par ④ et ⑤. Le pont delta ne porte que les segments ; `_snapshot` n'a pas de cache de
  plante : rien à adapter.
- **Golden** : `82d522c8…` → `ac48b170…`. Raison : la litière de feuilles se redistribue et augmente sous les caducs.
- **Décisions hors kickoff** : la ligne 🍂 ne sort qu'à la 1ʳᵉ semaine, sinon `sim/evenements` en ferait 4 événements carnet
  par arbre ; la part de couronne hors tuile n'est pas déposée, pour ne pas doubler la masse sur les bords.
- **Limites** : critère s36 partiel, car `semaine_abscission` n'a pas de composante par espèce (bouleau 0/70 plots en s36,
  6 arbres sur 6 couverts en s37 [n=1 run, VM]) ; `foliage_density_at` inchangée (§3.3). Pour ⑤ : `LeafLitterLayer.MasseRef` = 2,5
  est loin de la masse par plot réelle (médiane 0,145 [s37, n=1 run, VM]), à recaler.
- **Vigilance** : `tools/simserver/serialize.py` à 398 LDC, tout près de 400 → `/refactor` en fin de sprint.
- **Tests** : `tests/test_feuilles_automne.py` (14/14), `tests/simserver` (310/310), version 0.6.3 consignée dans leurs checks.

## Ce qui reste

Tronçons ④ à ⑥. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans de jeu.
`test_succession` et `test_edaphique` sont rouges AVANT ce sprint (vérifié le 2026-10-30).

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancer : `/sprint-auto sprint_automne_visible` (reprend au ④). Rejouer les bancs : `python3 -m bancs.mesure_arbres`, `python3 -m bancs.mesure_feuilles 3`.
