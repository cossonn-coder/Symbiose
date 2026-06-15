## 2026-06-02 — Attire-auxiliaires + monde 9 tuiles (Python)

### Contexte

Demande de Nico après la passe 2 : **ajouter des plantes qui attirent les
prédateurs des ravageurs**, et passer `main.py` sur **plusieurs tuiles**.
Décisions actées : **espèce(s) dédiée(s) + signal explicite** (rondelle
`auxiliaire`) ; **9 tuiles** (monde 3×3 complet).

### Réalisé

- **Rondelle `auxiliaire`** (`models.py`, `RONDELLE_TYPES`) — miroir discret de
  `pollinisateur`, posée par les plantes compagnes à la floraison.
- **2 espèces compagnes** : **Achillée millefeuille** (`Yarrow`, Asteraceae,
  vivace — ombelles) et **Phacélie** (`Phacelia`, Boraginaceae, annuelle —
  engrais vert mellifère). Toutes deux posent `auxiliaire` (Phacélie aussi
  `pollinisateur`). Ajoutées au `PLANT_CATALOGUE`.
- **Terme prédateur** (`effects.py`, `herbivory_pressure`) : intègre la rondelle
  `auxiliaire` avec un poids fort →
  `predator = 0.4·biodiversité + 0.2·pollinisateur + 0.15·stabilité + 0.4·auxiliaire`.
- **`main.py` réécrit en monde 3×3** (9 tuiles, sols contrastés terre/argile/
  sable). Tuiles paires = attire-auxiliaires (achillée+phacélie+trèfle), impaires
  = témoins. Rapport agrégé + table par tuile + **contraste attire-aux vs témoins**
  (rondelles `auxiliaire`, vitalité, vivantes). Défaut `N_YEARS=30` (9 tuiles
  lourdes ; CLI pour runs longs).

### Recalibration clé

Le test a révélé que `HERBIVORY_BASE=0.02` plafonnait la pression herbivore
**sous le seuil de morsure** (0.015) → l'herbivorie ne mordait jamais et la
régulation prédateurs (donc les attire-auxiliaires) était **inerte**. Relevé à
**0.05** : désormais une monoculture appauvrie sans auxiliaires **mord** (−1
santé), et diversité **ou** rondelles `auxiliaire` **ou** microbiome riche la
ramènent sous le seuil. La leçon permaculture (critère 4) devient réelle.

### Validation

- Contraste direct : monoculture+sol pauvre+0 aux → pression 0.018 (mord) ;
  +3 `auxiliaire` → régulée ; polyculture → régulée ; sol riche → régulée.
- `main.py` 9 tuiles : exit 0, rondelles `auxiliaire`=3 sur tuiles attire-aux,
  0 sur témoins (contraste net).
- Stabilité : mono-tuile 200 ans, aucune extinction, santé dynamique (1/2/3
  mêlées), vitalité 0.192 — la hausse d'`HERBIVORY_BASE` ne déstabilise pas.

### Note

Mécanique provisoire cohérente avec la **régulation émergente** (passe 2) : le
**champ auxiliaire ambiant dédié** (dynamique proie-prédateur + sprites visibles,
fiche Auxiliaires de `CLAUDE.md`) reste un sprint futur. Portage C# → D27/D24.

### Vérification du contraste (run 500 ans + test dédié)

Le run `main.py` 9 tuiles / 500 ans (69 min, exit 0, 20 plantes/tuile, vitalité
~0.21, mosaïque %vivace 23–87 %) **noie le contraste** attire-aux vs témoins :
à maturité, toutes les tuiles sont diverses + microbiome riche → la régulation
des ravageurs est déjà saturée par la diversité/le sol, les auxiliaires
deviennent redondants (écologiquement correct : un jardin établi s'auto-régule).

Pour **isoler** l'effet, `test_auxiliaires.py` (gardé) : 2 tuiles jumelles sous
**stress chronique** (sol sableux pauvre + monoculture tomate re-semée chaque
an). Instrumentation : wrap de `herbivory_pressure` comptant les dégâts par
tuile. Résultat sur 30 ans, déterministe : **AUX = 0 dégât herbivorie, TÉMOIN =
6** (écart monotone). Le mécanisme attire-prédateurs est donc fonctionnel de
bout en bout (rondelle posée → terme prédateur → dégâts ravageurs réduits) ;
l'amplitude reste modeste car `HERBIVORY_BASE` bas (ravageurs = nuisance, pas
fléau — philo non-punitive).

---
