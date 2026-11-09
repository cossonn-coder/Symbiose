# Conception — Zoochorie : les bêtes qui sèment (D42)

> Conçue le 2026-11-09 avec Nico (`/conception D42`). Suite de la relève ligneuse
> (D130) : « la relève des héliophiles passe par la trouée ou la dispersion loin du
> parent (merle, geai, écureuil) ». Carnet de bord :
> `sprints/faune/vie_macro/sprint_zoochorie/00_etat.md`.

## 1. Le constat (vérifié au code le 2026-11-09)

1. **Le fruit et la recrue sont deux mondes.** Les fruits traçables
   (`sim/engine/decompo.py::_tick_fruits`) nouent, mûrissent, tombent en litière
   `fruit`. La recrue des ligneux vient d'ailleurs : `sim/engine/mortalite.py::
   _reproduction` tire chaque semaine, toute l'année, `p = reproduction_rate`, sans
   regarder s'il y a des fruits.
2. **Le merle lit le fruit tombé sans le prendre.** `_merle_food_grid` additionne le
   fruit frais au sol et le lombric ; aucune faune ne retire un fruit.
3. **Une graine d'arbre en banque-sol ne germe jamais.** `add_species` dépose, mais
   la germination férale ne passe que par les archétypes d'adventices.
4. **Le bon véhicule existe** : `GrainEnAttente` (`fields/seedbank.py`) — gènes
   propres, priming (`expression`), position sous-plot, levée différée gatée par la
   niche (lumière × tolérance, pH, T_sol, allélopathie) dans
   `sim/succession._lever_grains_en_attente`. Il lui manque une durée de vie, une
   dormance, un drapeau « sauvage », un plafond par plot.
5. Pas de geai, d'écureuil, de mulot. Chêne et hêtre sans fruits traçables. Pas de
   noisetier au catalogue.

## 2. L'écologie à incarner

| Bête | Geste réel | Où va la graine | Portée | Ce que le joueur apprend |
|---|---|---|---|---|
| **Merle** | avale les baies **sur la plante** (cerise, framboise, fraise) ; le noyau traverse l'intestin, scarifié | **sous les perchoirs** (arbre, arbre mort debout, piquet, lisière) — nucléation | le monde (20 m) | « les cerisiers poussent sous mes arbres et sous mon piquet » |
| **Geai** | cueille glands, faînes, noix **sur l'arbre**, les enterre un par un, en oublie | **terrain découvert**, sol meuble, près d'un repère vertical | longue : la forêt de la ceinture entre au jardin | « le chêne arrive seul dans la prairie » |
| **Écureuil** | cueille noisettes, noix, glands, les enterre dispersés, en oublie | près des arbres, à la lisière des couronnes | moyenne (≈ 10-15 m) ; il ne vient que si les couronnes se touchent | « un bosquet appelle l'écureuil, l'écureuil plante le bosquet » |
| **Mulot** | **mange** les graines au sol ; en cache quelques-unes sous couvert | sous paillis, litière, herbe haute | courte (≈ 3 m) | « les années de glandée, les chênes lèvent ; les autres, tout est mangé » |

**Glandée (masting).** Chêne, hêtre, noisetier fructifient fort certaines années,
**synchronisées** pour toute l'espèce, et peu les autres. Les rongeurs ne peuvent pas
tout manger une année de masse (satiation) : c'est là que la forêt se renouvelle.

**Pourquoi c'est juste pour le jeu.** Philo #1 : le joueur n'agit pas sur la graine,
il agit sur le milieu (poser un perchoir, garder un arbre mort debout, pailler ou non,
laisser une haie). Philo #2 : aucun bonus — un flux de fruits → une bête → une graine
→ une niche. #3 : tout tirage par `_hash_noise`. #7 : chaque jardin se boise selon
ses perchoirs et ses lisières.

## 3. Décisions (Nico, 2026-11-09)

- **Q1** quatre disperseurs : merle, geai, écureuil, mulot.
- **Q2 recrue unifiée** : pour les **fruitiers pérennes à graine fertile**, la recrue
  passe par les **vrais fruits**. Fruit tombé → graines au pied ; fruit mangé →
  graines au loin. `_reproduction` (dépôt banque-sol + recrue directe) ne s'applique
  plus à eux. Recalibrage de la relève (D130) accepté.
- **Q3** graine du merle sous les perchoirs naturels **+ geste `poser_perchoir`**.
- **Q4** chêne et hêtre deviennent **fruitiers** (glands, faînes) ; **noisetier**
  ajouté au catalogue, avec ses 5 voix.
- **Q5** mulot **prédateur de graines** + **années de glandée**.
- **Q6** la graine tombée au pied est un `GrainEnAttente` (levée par la niche) : fin
  de la pose directe « plot le plus lumineux » pour ces espèces.
- Décidé par Claude (biologie) : durée de vie des grains sauvages par espèce ;
  dormance (un grain sauvage ne lève qu'au printemps qui suit son dépôt) ; plafond
  de grains sauvages par plot.

## 4. Le modèle

### 4.1 Le grain sauvage (socle)
`GrainEnAttente` gagne : `sauvage` (= `not cultive`, jamais `marquer_replante`),
`origine` (`"chute"`, `"merle"`, `"geai"`, `"ecureuil"`, `"mulot"` — pour les voix),
`levee_des` (semaine absolue : printemps qui suit le dépôt), `perime_a` (semaine
absolue : dépôt + `graine_viabilite_ans` × 52). Trait d'espèce
`graine_viabilite_ans` (défaut 1 ; framboisier 5, fraisier 3, cerisier 2, pommier 2,
gland/faîne/noisette/noix 1) [ordres de grandeur, banque de graines persistante des
Rubus]. Plafond `GRAINS_SAUVAGES_MAX_PLOT` (≈ 3) : au-delà, le dépôt est perdu.
La levée prend le **plus ancien grain éligible** du plot (un grain en dormance ne
bloque pas les autres) ; les grains plantés par le joueur gardent leur comportement
exact (pas de péremption, pas de dormance). Un grain périmé disparaît.

### 4.2 La chute → grains au pied (unification)
Quand une cohorte tombe (`deposer_fruits`, déjà appelé par la chute et la nouaison
suivante), elle dépose sa chair en litière (inchangé) **et** des grains : `n =
nombre × P_GRAIN_CHUTE` (part du hasard résolue par `_hash_noise`, borne par plot),
répartis sur les plots foliaires (arbre) ou au pied (herbacée), gènes =
`child_genes(mère, père)` (père = `find_father` comme aujourd'hui), expression =
`child_expression(mère)`. Concerné : `fruitier` + `life_cycle == "perennial"` +
`graine_fertile`. Le figuier (stérile) ne dépose rien. Les annuelles fruitières
(tomate, courgette) ne changent pas.

### 4.3 Glands, faînes, glandée
Chêne et hêtre : `fruitier = True`, `fruits_par_site`, `fruit_masse`,
`fruit_semaines_maturation` (chute en automne). **Glandée** : facteur annuel par
espèce `glandee(cls, annee, seed)` ∈ {fort, maigre}, tiré par `_hash_noise` sur
(espèce, année) seulement — donc synchrone pour tous les pieds de l'espèce.
Multiplie la fraction nouée. Trait `glandee_periode_ans` (chêne ~3-4, hêtre ~5-7,
noisetier ~2) ; espèce sans trait → pas de masting.

### 4.4 Noisetier (espèce neuve)
*Corylus avellana*, Betulaceae. Arbuste en cépée (`rejet_souche` fort), 4-6 m,
semi-sciaphile (`shade_tolerance` ≈ 1,0-1,1), chatons **en février** (anémophile ;
nectar 0 mais **pollen précoce** pour les butineurs au réveil si le modèle de
floraison le permet — sinon noté), noisettes traçables mûres en septembre, glandée
légère. Voix : encyclopédie (3 niveaux), carnet (`CONCEPT_DE`), magazine (famille
Betulaceae/offre), événements (chatons, noisettes), page secrète (le coudrier des
sourciers — optionnelle).

### 4.5 Frugivorie et caches (un module `sim/zoochorie.py`)
Chaque semaine, pour chaque fruitier vivant portant des fruits **mûrs** (maturité ≥
seuil mûr, avant la chute), chaque disperseur qui mange cette espèce prend une part
de chaque cohorte :
`prise = nombre × TAUX_PRISE × densité(disperseur) moyenne sur les plots foliaires`,
bornée par l'**appétit** du disperseur sur la tuile (∝ somme de sa densité) —
réponse saturante (Holling II) : une glandée rassasie, le reste tombe.
- Merle : cerisier, framboisier, fraisier. Chaque graine avalée survit avec
  `P_TRANSIT` ; dépôt pondéré par la grille **perchoir**.
- Geai : chêne, hêtre, noyer, noisetier. Chaque fruit caché est oublié avec
  `P_OUBLI_GEAI` ; dépôt pondéré par la grille **découvert**.
- Écureuil : noisetier, noyer, hêtre, chêne ; oubli `P_OUBLI_ECUREUIL` ; dépôt
  dans un rayon ≈ 15 m, pondéré par la **lisière des couronnes**.
Le fruit pris est retiré de la cohorte (il ne tombe plus) → moins de litière `fruit`
pourrie au sol (le ravageur attiré par le pourri le sent).

**Grilles de dépôt** (calculées seulement s'il y a eu une prise cette semaine) :
- perchoir = plots sous la couronne d'un ligneux haut (≥ 150 cm), sous un **mort
  debout** (`stade_mort == "seche"`), au pied d'un `Support` (tuteur, treillis,
  pergola, **perchoir**), + `eco.lisiere` ;
- découvert = lumière-sol haute × (1 − couverture), bonus près d'un repère vertical ;
- lisière des couronnes = anneau autour des couronnes ligneuses.
Un dépôt hors de la tuile de la mère (merle, geai) passe par un **tampon monde**
vidé en fin de tick, après la boucle des tuiles (l'ordre des tuiles ne décide rien).

**Apport de la ceinture** : un secteur `foret` envoie, l'automne, des grains de
chêne et de hêtre portés par le geai, ∝ `densite_ligneuse` × densité de geai, gènes
`founder_genes`. C'est la forêt qui entre au jardin.

### 4.6 Le mulot
Guilde neuve. Habitat = couvert (paillage, litière, lisière, piles). Ressource =
grains sauvages au sol + fruit tombé + densité de la banque-sol (lue, pas consommée :
la granivorie sur la banque-sol reste en dette). Proie du **rapace** et de la
**couleuvre**. Chaque semaine il prend des grains sauvages : `p = PRED_MAX × mulot(r,c)
× satiation`, satiation = `A / (A + offre de grains de la tuile)` ; une part
`P_CACHE_MULOT` des grains pris est **cachée** à ≤ 3 m sous couvert (oubliée), le
reste est mangé. Il ne touche **pas** aux grains plantés par le joueur (dette).

### 4.7 Le perchoir (geste)
`poser_perchoir` : un `Support` de type `perchoir` (≈ 200 cm, `finesse` « fin »),
famille de `poser_tuteur` (coût modéré, binaire). Tout support compte comme perchoir.
Concept de maîtrise : technique `perchoir` (nucléation).

### 4.8 Catégorie des nouvelles guildes
Geai, écureuil, mulot entrent dans une catégorie **neuve** (`disperseur`), lue par
personne d'autre : ils ne gonflent ni `auxiliaire` ni `herbivore_vertebre` (le
campagnol ronge les racines ; le mulot non). À vérifier au code au tronçon.

## 5. Coût perf
Frugivorie : boucle sur les fruitiers porteurs de fruits mûrs (une poignée), grilles
de dépôt seulement les semaines de prise. Trois guildes neuves : +3 champs de
population sur ~20 → ≈ +15 % du poste population, poste mineur du tick. Grains
sauvages bornés par plot. Budget : ≤ +10 % de tick `full` par tronçon, mesuré.

## 6. Golden
Smoke = tomate (meurt S2-3) + pommier (< 5 ans) : aucun fruit mûr, aucun chêne,
aucune ceinture → ①-⑤ neutres attendus. **⑥ (mulot) re-fige** : le mulot vit de la
banque-sol dès le smoke et nourrit rapace et couleuvre, qui pèsent sur le campagnol
→ dérive localisée à la chaîne rapace/couleuvre/campagnol, annoncée au kickoff.

## 7. Hors sprint (dettes)
- Granivorie du mulot sur la banque-sol et sur les grains plantés par le joueur.
- Myrtille et lierre fruitiers (le lierre nourrit le merle l'hiver).
- Mammifères des pommes (renard, blaireau) ; corneille et noix.
- Annuelles fruitières (tomate qui se ressème au compost).
