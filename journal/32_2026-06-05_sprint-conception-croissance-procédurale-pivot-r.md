## 2026-06-05 — Sprint conception Croissance procédurale : pivot rendu + morphogénèse (conception seule)

Parti d'un découpage de l'impl. D29 hormones, **audit** déclenché par Nico : le
modèle « réponse à la **taille** » ne connaissait qu'un déclencheur (l'action joueur
`tailler`). Or la dominance apicale pilote la croissance **en permanence**, et l'apex
est atteint aussi par l'**écosystème** (grêle, herbivorie du bourgeon par un
ravageur, vent) — **déjà dans le tick déterministe** (`weather_at`/grêle dans
`engine.py`, champ ravageur D31.1, exercés par le golden). Faire du débourrement un
privilège du joueur contredit la philo #1/#2.

**3 décisions hormones revues** (via questions structurées) :
- **Moteur permanent** (et non déviation ponctuelle) : l'auxine pilote l'architecture
  à chaque tick, pour **toutes** les plantes (jeune = flèche, vieux = étalé). → le
  critère « repos neutre / golden intact » du doc hormones **tombe**, re-figeage
  assumé.
- **Intensité continue** `[0,1]` (seam `atteindre_*(intensité)`), pas binaire.
- **Déclencheurs naturels plus tard**, par étapes : ce chantier = moteur permanent +
  `tailler` joueur ; grêle/chenille/vent appelleront **le même seam** dans un sprint
  ultérieur.

**Pivot majeur — rendu.** Nico veut afficher la croissance **autrement que par
sprites** : un **empilement de pixels guidé par l'auxine**. Cela **fait tomber le mur
du rendu** sur lequel `CONCEPTION_HORMONES.md` §B justifiait le repli scalaire → la
**vraie topologie** redevient possible et plus fidèle. Rendu et modèle hormonal
deviennent **le même sujet**.

**8 décisions-racines actées** : 1. structure de **segments** (branches) ; 2. vit en
**Python** (source de vérité, déterministe) ; 3. **accumulation bornée** (structure
présente vivante, vieux bois qui tombe — pas de journal infini, compat run éternel) ;
4. **auxine = niveau le long des segments** (remplace les 2 scalaires) ;
5. **phototropisme** (biais `LightField`) ; 6. **empreinte dérivée de la structure**
(les classmethods `height_at`/`canopy_radius_at`… gardent leur **contrat**, seule la
source change → golden re-figé **localisé**) ; 7. organes **tout procéduraux**
(feuilles/fleurs/fruits dessinés, zéro sprite) ; 8. racines = **rayon dérivé** (pas
de structure souterraine).

**Exigence Nico — profil de croissance PAR ESPÈCE** : chaque plante a sa **vitesse**
et sa **stratégie** (`port_archetype` : flèche/étalé/buissonnant/rosette/graminée/
grimpant/rampant), à **décrire pour chaque espèce** du catalogue (14). Schéma
d'attributs sur `PlantBase` ; les `growth_stages`/`age_curve` existants deviennent
**cibles de calibration** (on ne jette rien). `reponse_taille` (doc hormones) absorbé :
une graminée `port_archetype="graminee"` est insensible à l'écimage **par
construction**.

**Livrable** : `docs/conception/CONCEPTION_CROISSANCE.md` (volets A–M) qui **absorbe et
refond** `CONCEPTION_HORMONES.md` (modèle 2 scalaires abandonné ; doc conservé avec
en-tête de renvoi). Découpage du chantier (**gros, 6 tronçons** + nature/marqueur
`🌿`/reste du catalogue « plus tard ») en §M.

**Conséquences statut :** D29 **réorienté** (scalaire → topologie/structure) ; le
`sprints/sprint_D29_impl/` préparé plus tôt dans la session est **superseded**
(conservé, en-tête de renvoi). **Risque n°1 identifié** : générateur d'organes pixel
art procéduraux (sous-sprint itératif dédié). Aucun code touché, aucun golden touché
(conception pure) — le re-figeage viendra à l'implémentation, **espèce par espèce**.

**Statut.** Prochain = sprint impl. Croissance procédurale
(`sprints/sprint_croissance/`).

---
