<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Mortalité réaliste passe 2 : fonte, fongique, ravageurs régulés, renouvellement (Python)

### Contexte

Suite de D27. Passe 2 = M4–M7 + nécromasse ∝ hauteur. **Ajout de Nico** : les
ravageurs doivent avoir des **prédateurs** (auxiliaires) — décision actée :
**régulation émergente** (dérivée des signaux existants), pas de champ auxiliaire
dédié (ce dernier = sprint futur, cf. fiche Auxiliaires de `CLAUDE.md`).

### Réalisé

- **`models.py`** : `fungal_susceptibility` par famille (Solanacées 1.0 = mildiou,
  Brassicacées 0.6, défaut 0.5, Poacées/Astéracées 0.4, Lamiacées 0.2) ; trèfle
  `reproduction_rate=0.35` (ressemis M7, vivace sans archétype).
- **`fields.py`** : `DAMPOFF_BASE=0.08`, `DAMPOFF_HUM_SEUIL=0.50`,
  `FUNGAL_BASE=0.04`, `RESEED_RADIUS_CM=150`, `NECROMASS_PER_CM=0.03`.
- **`effects.py`** :
  - `damping_off` (M4) — fonte des semis ∝ excès d'humidité × densité × saison
    fraîche, atténuée par le microbiome (logistique `disease_probability`). Létale.
  - `fungal_disease` (M5) — pression ∝ humidité × densité **même famille**
    (monoculture propage) × susceptibilité, atténuée microbiome. −1 santé.
  - `herbivory_pressure` (M6) — **régulation prédateurs émergente** :
    `predator = 0.5·biodiversité + 0.3·pollinisateur + 0.2·stabilité` ; pression
    `×(1−microbiome)×(1−predator)`. **Létalité** (dégâts ×2) si monoculture non
    régulée (`predator<0.2` et `microbiome<0.2`).
  - `necromass_biomass(plant)` = `current_height × NECROMASS_PER_CM` (D27 #5).
  - `background_mortality` : **résistance des sujets établis** (`×(1−0.8·min(1,
    height/200))`) — la mortalité de fond frappe surtout les jeunes/petits
    (démographie végétale réelle) ; un arbre adulte ne meurt quasi que de sénescence.
- **`engine.py`** : `_renewal` (M7, à la récolte d'automne) — un parent mûr
  (vivace sans archétype, ou arbre `age_years≥maturity_years`) qui fructifie
  (`p=reproduction_rate`, hash) sème la même espèce sur le **plot libre le mieux
  éclairé** à portée (gap de lumière ; sous canopée fermée → pas de recrutement,
  auto-limitation). Nécromasse ∝ hauteur sur **tous** les sites de mort.
- **`perennials.py`** : taux mast — fruitiers 0.15, noyer 0.10, chêne 0.08.

### Calibration (run 500 ans)

Premier jet (renouvellement double-verrouillé + taux annuels 0.02) → 0 ressemis,
extinction. Corrigé : M7 **mono-verrou** + porte lumière, taux relevés
(trèfle 0.35, arbres 0.08–0.15) + résistance des sujets établis (sinon un arbre
mourait à ~28 ans d'un cumul fonte/fongique/fond au lieu de sénescence).

### Validation

- **500 ans, exit 0, aucune extinction généralisée** (16 survivants minette/pâturin).
- **Santé dynamique à l'échelle** : survivants en santé 1/2/3 mêlées (fini les
  zombies tous à 1/3 d'avant le sprint). Vitalité moyenne 0.217 (dopée par la
  nécromasse des arbres morts).
- Mécanismes vérifiés en isolation : fonte (humide/dense/froid), fongique
  (~0.024/sem sur Solanacée en patch dense), renouvellement (trèfle ×7, pommier
  ×2 sur 200 ans), régulation prédateurs (herbivorie étouffée en milieu divers/stable).
- **Renouvellement arboré = PROVISOIRE** : sur 108 m², un arbre dont la canopée
  (350–700 cm) dépasse le rayon de dispersion (150 cm) ombrage ses propres semis
  → un sujet isolé ne forme pas de bosquet auto-perpétué (réaliste à cette
  échelle). La persistance arborée paysagère relèvera de la **SeedBank-espèce
  (D17)** + friche périphérique. Ne pas doubler le système au Sprint génétique.

### Reste

Portage C# de toute la mortalité réaliste (passes 1+2) → dette D27/D24.
Unification du renouvellement provisoire par D17+D22 (Sprint génétique).

---
