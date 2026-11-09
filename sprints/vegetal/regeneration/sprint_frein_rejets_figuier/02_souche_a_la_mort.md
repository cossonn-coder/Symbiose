# ② La souche rejette à la mort de l'arbre

À lire d'abord : `CLAUDE.md`, `00_etat.md`,
`docs/vegetal/regeneration/conception_rejets_de_souche.md` §2, §3.2-3.5.
Prérequis : ① fait.

## Objectif
Un arbre qui meurt avec une souche encore vivante fait partir quelques rejets au
pied, à la saison de végétation suivante. Le figuier perd ses rejets de fond.

## Modèle
1. **Trait d'espèce** `rejet_souche: float = 0.0` sur `PlantBase`
   (`plants/base/familles.py`, près des `clonal_*`, commentaire pédagogique).
   Valeurs [ordre de grandeur, choix de conception] dans `plants/perennials/` :
   figuier, cerisier, charme, aulne, saule, chêne ~0,8 ; pommier, noyer ~0,5 ;
   bouleau, hêtre ~0,2 ; sapin 0 (défaut). Chaque valeur avec une ligne de
   justification botanique.
2. **Figuier** (`plants/perennials/fruitiers.py`, `Fig`) : `clonal_mode` →
   `"none"` (retirer `clonal_radius_cm` ou le laisser commenté inutile — au choix,
   dire lequel) ; mettre à jour le commentaire du ③ de la relève (« rejets après
   perte de la partie aérienne, pas en continu »). Le `_mature` d'arbre de
   `sim/clonal.py` reste (inoffensif).
3. **Souche vivante, lue à la mort** : `deposer_mort` (`sim/effects/perturbations.py`)
   est le point d'entrée unique de la mort (idempotent, garde `plant.morte`) ; c'est
   là que l'état de la plante est encore intact. Y calculer et figer sur
   l'instance un drapeau du genre `souche_vivante` (nom au choix, champ déclaré
   dans `plants/base/instance.py`) : vrai ssi `rejet_souche > 0` ET aucune mémoire
   de dommage au pied au-dessus de son seuil de nuisance :
   `shade_memory` (seuil = `seuil_ombre(plant)` de la relève ①, même module),
   `drought_memory`, `asphyxie_memory`, `root_herbivory_memory`,
   `pourriture_memory` (seuil : celui où chaque mémoire commence à blesser dans
   son module — LE LIRE au code, ne pas l'inventer ; le citer en commentaire).
   `cold_memory`, `wind_memory`, `infection_memory`, sénescence : n'empêchent pas.
   Faire du critère une fonction pure testable (réutilisée au ③).
   Les mortes « non marquées » retirées par le filet de `_tick_skeletons` ne
   rejettent pas : acceptable, le noter.
4. **Émission** : une passe avec accès à la tuile (nouveau module
   `sim/souche.py` recommandé, une responsabilité ; câblage dans
   `sim/engine/boucle.py` près de `emettre_ramets`, ~l.500). Pour chaque arbre
   mort à souche vivante non encore traitée, en semaine hors hiver (même test que
   le ①) : N = borne(round(`rejet_souche` × `N_REJETS_MAX`), 0..4) rejets, tirés
   déterministes (`_hash_noise`, canaux distincts de ceux de `sim/clonal.py`, à
   lister en commentaire), dans un rayon ~60 cm (`RAYON_REJET_CM`) autour de la
   position continue du mort, plot valide, **sans gate de lumière** (la réserve
   racinaire porte le rejet). Rejet = clone : copier `genes`, `expression`,
   `form_seed` comme `emettre_ramets`. Marquer la souche « traitée » (une seule
   vague par mort). Respecter `recrutement_bloque(tile)` (cap perf).
   **À vérifier au code** : le squelette d'un arbre mort reste dans `tile.plants`
   jusqu'à la saison suivante (`_tick_skeletons`, `FRAG_RATE` 0,04 × vitesse locale,
   retrait à bois épuisé). S'il peut disparaître avant, garder la souche ailleurs
   (p. ex. liste sur la tuile) et le dire dans `00_etat.md`.
5. **Log** : une ligne par vague, format nouveau et stable, p. ex.
   `    🌱 Rejet de souche : {nom} @{plot} ×{n} [souche de @{plot_mort}]`.
   Le câblage carnet/événements est au ④ ; ne pas casser le parseur de
   `sim/evenements.py` (vérifier qu'une ligne inconnue est ignorée).

## Golden
**INCHANGÉ** attendu : aucun ligneux ne meurt dans le smoke (seul le pommier
< 5 ans ; à vérifier par un espion sur `deposer_mort` si doute). S'il bouge :
STOP.

## Tests
`tests/test_rejets_souche.py` (neuf) :
(a) figuier mort de vieillesse (mémoires basses) → rejets au printemps suivant,
    au pied (≤ rayon), clones ;
(b) même figuier mort avec `shade_memory` au-dessus de son seuil → 0 rejet ;
(c) sapin mort → 0 rejet ;
(d) mort en hiver → rejets seulement à la 1ʳᵉ semaine de printemps ; une seule vague ;
(e) figuier vivant mûr, 200 semaines → 0 rejet (plus d'émission de fond).
Réécrire `tests/test_figuier_realiste.py` (c) en conséquence (le dire).
Plus : `tests.test_golden`, `test_banque_semis`, `test_figuier_realiste`,
`test_evenements`, `test_stress_chronique`, `bancs.test_verger_mur`.
**Jamais `test_epaisseur_500ans`.**

## Ne PAS faire
- Perte de couronne d'un arbre vivant (c'est le ③).
- Voix encyclopédie/carnet (c'est le ④).
- Gel des rameaux (dette D131).
- Toucher au framboisier (drageon d'arbuste, inchangé).
