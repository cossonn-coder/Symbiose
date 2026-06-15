## 2026-06-04 — Sprint conception paliers de maîtrise : D12 (conception seule)

**Conception seule, aucun code.** Spec → `docs/conception/CONCEPTION_MAITRISE.md`.
Couvre **D12** ; remplit l'interface stubbée par le Sprint Vigueur
(`sim/vigueur.py:palier_bonus() == 1.0`). **Périmètre : squelette réutilisable
seulement** (décision Nico) — le câblage fin est déclaré en sous-sprints.

**Pivot structurant (décision Nico).** L'unité atomique de maîtrise n'est **ni la
famille ni l'espèce** mais l'**objet de maîtrise** générique, data-driven,
catalogue-agnostique — coller la maîtrise aux 5 familles condamnerait le modèle au
premier ajout (catalogue qui grossit, D23/D26). Catégories ouvertes : êtres
vivants (espèces), concepts transversaux, **outils, structures, techniques/gestes**
— vision Nico d'un « énorme ensemble d'objets interfaçables, système vivant aux
milliers de secrets ». Chaque objet porte un palier `0..5`
(`inconnu → découverte → investissement → maîtrise → expertise → transcendant`).

**Progression intra-objet.** Découverte (`0→1`) = **observation seule** (gratuite,
motive). Paliers sup. = **succès conditionnés**, de plus en plus pointus et
**répétés** aux hauts paliers (fiabilité/régularité valorisées). Difficulté
**log/exponentielle** (`preuves(k) ≈ BASE·R^(k-1)`) : qui sait déjà passe le début
vite puis ralentit. **Réversibilité monotone** (un palier ne se perd pas ; philo #6
+ le savoir voyage à l'avatar).

**Agrégats.** Famille = spillover **intra-famille uniquement** (tomate accélère
aubergine, pas haricot). **Deux mesures globales distinctes** (désamorce la
dilution par catalogue grossissant) : *complétude-ratio* sur les **découverts**
(→ seuils de déblocage) ≠ *accumulation-log absolue* (→ Vigueur max + régen,
« jardinier actif = vigoureux mais pas super-héros »).

**Trois effets, deux seams (décision Nico).** `palier_bonus(player)` reste
**scalaire intact** = `1 + K·log1p(accumulation)` → plafond Vigueur (log) + régen ;
**`sim/vigueur.py` non retouché** (découplage acté tient). Le **coût d'action** est
un **seam SÉPARÉ** sur `actions.py`, **contextuel** : `cout_action(player, action,
objets_touchés)` lit (1) connaissance globale éco/bio + (2) maîtrise des **objets
que l'action touche**. **Maîtrise stockée PAR OBJET, action = lecteur** (pas d'état
par paire action×objet → pas d'explosion combinatoire). Exemple : tailler
framboisier lit maîtrise(framboisier)+maîtrise(sécateur)+global → indépendant de
construire(serre) ; pratiquer la taille fait monter *l'objet framboisier* →
spillover gratuit sur tous ses gestes. Deux **sources ponctuelles** de Vigueur en
plus : découverte (+ motivation), succès/palier (+ récompense).

**Méta-état** dans `game_state["maitrise"][player]`, **par avatar** (pas de
méta-savoir inter-avatars), au-dessus du tick. Golden écolo (sans joueur) **intact,
jamais re-figé** — un hash qui bouge serait un bug.

**Sous-sprints déclarés (hors squelette) :** (1) définition du « succès » par
axe ; (2) table palier→déblocage (D13/D14/D15 + encyclopédie) ; (3) taxonomie des
objets + liste des objets-touchés par action ; (4) calibrage (`K/BASE/R`,
atténuations) ; (5) portage C# (D24).

**Question ouverte (calibrage, post-test) :** valeurs `K`, `BASE`, `R`,
atténuations de coût et gains ponctuels — comme toute la couche Vigueur.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code).

---
