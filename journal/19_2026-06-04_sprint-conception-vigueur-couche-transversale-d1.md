## 2026-06-04 — Sprint conception Vigueur : couche transversale D11 (conception seule)

Conception de la **Vigueur universelle** (D11), aucun code. Produit la spec
`docs/conception/CONCEPTION_VIGUEUR.md`, sur le modèle de `CONCEPTION_METEO.md`.

**Le pivot :** la Vigueur n'est pas *un* système mais **deux strates**. Le moteur
modélise déjà la quasi-totalité de la « Vigueur des plantes » sous d'autres noms
(uptake = puiser, nécromasse = retour au sol, santé/`vitalite`/gène = énergie
propre, `game_state["current_player"]`/`scores` = logement joueur,
`HARVEST_VIGUEUR_COST` = hook coût déjà câblé). Le seul *vrai nouveau* système est
la **couche Vigueur joueur + coûts d'action**, event-driven, **au-dessus** du tick.

**Décisions (2 questions) :** (1) **Vigueur des plantes = façade dérivée**
(`vigueur_plante = sante × maturite × qi_local × gène`), read-only, zéro état
nouveau, **golden intact** — vs champ stocké rejeté ; (2) **interface paliers
stubbée** : Vigueur conçue de façon autonome, `palier_bonus()` renvoie `1.0` tant
que D12 absent, se branche plus tard sans retoucher la Vigueur.

**Propriété clé actée :** le golden écologique est une succession spontanée pure
(aucune action joueur) → activer les coûts, la régen joueur, la façade
**ne re-fige PAS le golden**. Si un hash bouge à l'implémentation, c'est un bug
(fuite dans le tick). Un *golden joueur* distinct testera la couche gameplay.

Le gène `vigueur` provisoire (D22b) est **enveloppé** par la façade, pas recâblé
de façon destructrice → son sens passe de « provisoire » à « stabilisé ».

**Catalogue d'actions joueur** (§3 du doc) : trois axes (cible milieu/vivant ·
phase planif./saison · signe Vigueur ±). Milieu (canal vertueux philo #2 : semer,
**multiplier végétativement** (clone), arroser, **drainer**, pailler, amender,
**inoculer**, **favoriser un auxiliaire**, **grelinette/biner**, structures/tuteur)
→ modifie un **champ**, jamais la plante. Vivant (coûteux philo #1 : manger,
récolter, déraciner, écraser, **tailler**) → net positif sur le mûr, net négatif
sec sur déraciner/écraser, pas de punition scriptée (philo #6). Ressourcement :
méditer (source), **observer (gratuit)**.

Deux trous comblés (suggestion Nico) : **favoriser un auxiliaire** = pendant
vertueux d'« écraser » (agir sur l'habitat → régulation émergente, pas de
suppression manuelle) ; couple **biner/grelinette** = pédagogie par l'outil (même
but décompacter, le bêchage casse le `microbiome`, la grelinette le préserve —
no-dig). `Pailler` élargi en **`Pailler / mulcher`** (paille/BRF/feuilles/broyat).
Ouvre une question de modélisation inscrite en dette **D30** : champ
`structure/compaction du sol` pour porter le bénéfice d'aération de la grelinette.

**Dette surfacée : D29 (auxine / dominance apicale).** `tailler` est acquis en v1
(effet géométrique : réduction d'empreinte → lumière), mais sa vraie richesse
hormonale (levée de dominance apicale → débourrement latéral → ramification/mise à
fruit) **mérite un sprint dédié** (décision Nico). Hook posé, D29 s'y branchera.

**Périmètre impl. à venir** (sprint moyen, découpable, golden préservé sans
re-figeage) : couche Vigueur joueur → coûts d'action → façade lecture diégétique →
(tandem D19) action manger. Gated : paliers réels (D12), magazine (D13), prépa
météo (Godot), auxine/taille riche (D29), portage C# (D24).

### Hash golden (journal de re-figeage)
`ee79dd66…` (gènes du vecteur) → **inchangé** (conception seule, aucun code).

---
