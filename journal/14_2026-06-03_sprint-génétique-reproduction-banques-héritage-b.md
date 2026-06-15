## 2026-06-03 — Sprint génétique / reproduction : banques + héritage biparental (Python)

**Objectif** : lever D17 (deux banques de graines) + D22 (génétique des
populations) et **remplacer** le renouvellement provisoire M7 (`_renewal`) par
la vraie reproduction génétique. Python seul (source de vérité) ; le portage C#
rejoint la dette D24 — le C# n'a aujourd'hui que des stubs Godot de 15 lignes,
aucun moteur à porter, donc la « parité 1 saison » du kickoff était intestable
(décision actée en début de session).

**Zones blanches tranchées (2026-06-03)** :
- Granularité banque-sol = **moyenne + variance par espèce × plot** (pas
  d'échantillons stockés) → `GeneStat` (Welford pondéré).
- Compatibilité d'hybridation = **par famille botanique** (`species_compatible`).
- Coût Vigueur de la récolte sélective = **différé** (hook `HARVEST_VIGUEUR_COST
  = 0`, branché au Sprint 4 Vigueur / D11).

**Vecteur de gènes (D22)** — `models.GENE_NAMES = ("hauteur",)`, extensible sans
refactor. Plage normale [0.7, 1.3] (gaussienne σ=0.10), bornes dures [0.4, 1.6]
que l'introgression peut atteindre (vigueur hybride). `PlantInstance.genes` (vide
⇒ neutre 1.0) + `gene()`. `genetic_factor` enfin **branché** :
`current_height = potentiel × growth_factor × gene("hauteur")` (annuelles ET
pérennes ligneuses).

**Deux banques (D17)** :
- **Banque-sol** = couche `species` ajoutée **par-dessus** les archétypes dans
  `fields.SeedBank` (`add_species`, `sample_genes`, `tick_species_aging`). Par
  espèce × plot : densité + distribution `GeneStat` par gène. Vieillit (0.997/sem),
  les dépôts récents pèsent plus → la lignée locale dérive. Reste au terrain.
- **Banque-joueur** = `seeds.py` (`Seed`, `PlayerSeedBank`) : lots par espèce,
  transportable (suit l'avatar), **sérialisation JSON** (save lisible).

**Reproduction biparentale (D22)** — `reproduction.py`, déterministe (hash, pas
de RNG live) :
- `find_father` : père de même famille, en âge de fleurir, à portée de
  pollinisation. `pollination_mode` (wind/insect/self) + `pollination_radius_cm`
  par espèce (graminées + chêne/noyer = anémophiles longue portée).
- En mode insecte, le rayon est modulé par les rondelles `pollinisateur` +
  `auxiliaire` de la tuile (×0.5 sans → ×1.5 à saturation) : **favoriser les
  auxiliaires = plus de brassage = meilleures graines** (mécanique permaculture).
  Sans partenaire à portée → **autofécondation** (mutation réduite, consanguinité).
- `child_genes` : moyenne(parents) + mutation gaussienne par gène. Introgression
  intra-famille = père hétérospécifique décale les gènes, l'enfant **garde
  l'espèce de la mère** (aucune nouvelle `PlantData`).

**Intégration moteur** — `_renewal` (M7) **supprimé**, remplacé par
`_reproduction` (même phase : récolte d'automne). Chaque parent fécond qui
fructifie dépose ses graines (gènes hérités) dans la banque-sol [pont chute→sol],
puis recrute directement **uniquement** ce que la succession par archétype ne
germe pas (vivaces/arbres sans archétype — ex-domaine de M7), gated par la
lumière. Les germinations de `_succession`/`_spring_flush` échantillonnent les
gènes du pool du plot (vide ⇒ neutre, rétro-compatible). Pont récolte→banque-
joueur dans la phase récolte (inerte si aucune banque-joueur attachée au
`game_state`, donc `main.py` inchangé).

**Tests** (`test_genetique.py`, gardé) — **20/20** déterministe :
genetic_factor branché ; **sélection émergente** (lignée sélectionnée 1.00→1.33
sur 14 générations vs dérive neutre ~1.00) ; **brassage** (auxiliaires → rayon
75→225 cm → outcrossing au lieu d'autoféc.) ; introgression intra-famille,
inter-familles interdite ; banque-sol dépôt/échantillonnage ; intégration moteur
4 ans + pont récolte. Non-régression : `main.py 30` stable, sans crash ;
circulation des gènes féraux confirmée (été an 25, 6/33 vivantes portent des
gènes hérités, dérive autour de 1.0).

**Reste** : portage C# (→ D24, avec tout le moteur) ; nouveaux gènes du vecteur
(vigueur, résistance pathogène, tolérance sécheresse) = extensions futures ;
coût Vigueur récolte = Sprint 4 (D11).

---
