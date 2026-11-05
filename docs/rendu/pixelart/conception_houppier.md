# Conception HOUPPIER : arbres denses, grimpantes sans fin de pousse, fruits des arbres

**Figée le 2026-11-05** avec Nico (D118). Sprint : `sprints/rendu/pixelart/sprint_houppier/`, 5 tronçons. Mesures et audit : `00_etat.md` du sprint.

## 1. Demande

Retour F5 du 2026-11-05 : beaucoup plus de feuilles dans le houppier et de petites branches pour les porter, plus de pompons ovales sur rameaux verts. Le lierre régresse ; hors coupe il doit continuer de grandir et de grossir. Une grimpante arrivée en haut de son appui ne s'arrête pas : elle cherche un autre appui, sinon elle plie et sa partie effondrée meurt.

## 2. Décisions

| # | Décision | Pourquoi |
|---|---|---|
| 1 | Rameaux et brindilles dans la vue seule, dérivés à la cuisson | Vrais segments (plafond 400) : tick +16 % [`full` an 2, seed 42, n=1 run par côté, VM, charge 3 à 17], JSON ×2,4 [mêmes runs], pommier 405 → 261 cm [mêmes runs], golden changé, 11 arbres à recalibrer. Conséquence assumée : on ne taille pas une brindille, la taille reste sur la charpente |
| 2 | Clé de hash stable au lieu de l'indice de segment | `_rebuild` réindexe à chaque coupe : les présences sautent, très visible une fois dense |
| 3 | Gerbes précuites à l'écran de chargement, cadre de départ cuit avant d'ouvrir le jeu, recuisson seulement si le dessin change | Un coup de pinceau coûte jusqu'à 78 ms à ×8 [figuier, an 10, n=1 coup, VM] et chaque arbre est sali à chaque snapshot |
| 4 | Lierre et jasmin : emit 20, cap 80, `wood_persistence` 4000, fragilité 0,3, girth 6, plafonds relevés | Chiffres §3 |
| 5 | Grimpantes sans fin de pousse, levier inerte par défaut | Le haricot, validé au F5, ne change pas |
| 6 | Cerisier, figuier, noyer fruitiers ; durée de maturation par espèce ; figuier en `self` | Une seule vitesse commune interdit la pomme d'automne et la cerise de juin |
| 7 | Fleurs et fruits des arbres sur les brindilles | Les fleurs herbacées restent à D118 |

## 3. Grimpantes

**Tenue.** Aux réglages de la décision 4, plafonds à 2000 : lierre 1 262 → 1 342 cm, jasmin 1 337 → 1 526 cm entre s26 et s156, épaisseur max 3,03 → 4,18 cm [`accroches_adultes`, seed 42, n=1 run, VM]. La longueur finit en plateau au cap 80 (1 600 cm au mieux) : la liane se renouvelle, elle ne s'allonge plus, elle grossit encore. Plafond conservé, accord de Nico.

**Relais.** Aujourd'hui `chercher_support` ne scanne que les plantes libres et mesure depuis le pied. Une liane accrochée dont l'apex a dépassé son appui cherche depuis cet apex, une fois toutes les 4 semaines [choix] : structure, mur ou plante non grimpante plus haute que l'apex, sur sa tuile, dans le rayon d'accroche. Exclure les grimpantes comme hôtes de relais supprime les cycles entre deux lianes. Zéro RNG, départage distance puis identité stable.

**Longueur critique.** Une tige libre flambe selon Greenhill : L ∝ (E/ρ)^⅓ · d^⅔, où E/ρ dit la raideur du matériau pour son poids et d l'épaisseur. Forme retenue : `L_crit = rigidite_tige × f(lignification) × d^⅔`, `rigidite_tige` par espèce, `None` par défaut (levier inerte). Repères : environ 2 m pour une tige ligneuse de 1 cm, 30 cm pour une herbacée de 0,5 cm [odg]. Pédagogie : la tige fine et jeune plie vite, la tige épaisse et lignifiée tient plus loin, sans aucune règle « par espèce » sur la hauteur. C'est une contrainte physique, pas un malus (philo #2).

**Effondrement.** Longueur libre au-dessus de `L_crit` : l'apex plie vers le sol (`DROOP_Z` existe). Au-delà d'une marge [choix], le sous-arbre tombe en litière `bois` par `deposer_bois_tombe`, cause `effondrement`, et un bourgeon repart. Le port en cascade émerge. L'étranglement d'un hôte reste émergent par le `LightField`.

**Jasmin.** Reste `sarmenteux` : le geste `palisser` reste le seul accès au mur. Le relais s'appuie sur plantes et structures. La docstring de `Jasmine` (« le SEUL canal d'accroche ») est à mettre à jour.

**Limites assumées.** Le relais reste sur la tuile de la plante. Le cap 80 borne la longueur.

## 4. Fruits

Levier `fruit_semaines_maturation` par espèce, défaut = valeur actuelle (mûr en ~12,5 semaines par `FRUIT_DMAT`) : tomate, fraise, framboise, courgette inchangées. Valeurs à caler sur le calendrier (`calendrier.saison_de`) et `docs/vegetal/croissance/fiches_arbres.md` : pommier long (pommes en sept.-oct.), cerisier court (cerises en début d'été), noyer long, figuier moyen.

Le golden reste identique avec les trois fruitiers et le figuier en `self` [smoke, patch mémoire]. Ce smoke n'atteint pas leur maturité : l'effet réel se mesure sur `full` et sur un banc.

## 5. Vue

**Gerbe** : pièce d'atlas, rameau + brindilles + feuilles, par forme de feuille, palier et variante, en codes de palette comme `KitTouffe`. Couche bois et couche feuilles séparées, pour que l'hiver montre la dentelle. L'arbre s'assemble de gerbes le long de ses segments feuillés et dans son rayon réel `_rayonReelCm` (le snapshot ne porte pas `CanopyRadiusCm`). À ×16 et ×32 la feuille reste dessinée, sur rameaux dérivés.

**Bois** : le segment apex de 40-50 cm n'est plus vert vif sur toute sa longueur chez les arbres.

**Recuisson** : `DessinInchange` existe pour les ports (`TailleAuPied`) ; il s'étend aux arbres avec une clé quantifiée, pour qu'un arbre ne soit plus sali chaque semaine sans changement visible. Le critère de cuisson est la durée totale, arbitrage de Nico du 2026-11-05 (D118).

**Mesures attendues** : remplissage du houppier sur capture, durée totale de cuisson, RAM de l'atlas, FPS.

## 6. Coût

Moteur : scan de relais toutes les 4 semaines, réservé aux lianes accrochées à l'apex dépassant : négligeable attendu, à mesurer. Budget ≤ +10 % de tick par tronçon. Vue : mesure de référence au ④, avant toute densification.

## 7. Hors périmètre

Reste de D118 : piquants d'ortie, fleurs herbacées, point de pollen, gestes, DA hors plantes. D127 (herbivorie de banc, pires ticks).
