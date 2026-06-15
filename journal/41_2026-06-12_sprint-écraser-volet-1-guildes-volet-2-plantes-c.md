## 2026-06-12 — Sprint « écraser » : volet 1 (guildes) + volet 2 (plantes) CLOS

Retour F5 de Nico (« il faut pouvoir se tromper ou être maladroit ») → sprint
en deux volets, **moteur Python**.

- **Volet 1 (livré `4f4a7f2`)** : `ecraser` frappe la **guilde du sprite cliqué**
  (ravageur/auxiliaire/pollinisateur/vers), plus seulement `ravageur` codé en dur
  — la maladresse devient possible et instructive (philo #1). Pont `target.guilde`,
  protocole 0.3.1.
- **Volet 2 (ce sprint)** : réponse des **plantes** à l'écrasement. Conception
  **FIGÉE** Q1–Q6 (`docs/conception/CONCEPTION_ECRASEMENT.md`). Le geste réutilise le
  **seam de perturbation partagé** (`growth.py:atteindre_segment`, le même que
  `tailler`) — zéro mécanique neuve dans le moteur de croissance.

**Décision (modèle) :** deux traits d'espèce sur `PlantBase`,
`resistance_ecrasement` (∈[0,1], résistance structurelle, pilote l'intensité au
seam) et `stimulation_ecrasement` (∈[0,1], bénéfice de repousse).
`intensité = INTENSITE_PIED·(1 − resistance·f_lignification(âge))`. **DOUX**
(intensité < `COUPE_NETTE`) → auxine baissée → ramification émergente (déformation) ;
**NET** (≥) → écimage du sous-arbre. Deux axes, trois issues : pâturin (0.9/0.9)
talle, tournesol (0.15/0.05) décapité, basilic (0.4/0.85) écimé **mais repart** =
le pincement.

**Décision (mort, Q3 — sentier) :** le **rejet de souche** (`growth.py`) ressuscite
toute plante sans apex → la structure seule ne peut pas tuer. En régime **NET** on
entame donc la **santé** (`health -= 1`, geste direct comme `deraciner`), **sauf**
si l'espèce profite de l'écrasement (`(1 − stimulation) ≥ SEUIL_DEGAT`). Écraser le
**collet** (cible par défaut, Q2 ; collet protégé du retrait) d'un semis fragile le
tue en ~3 passages → **sentier émergent** (la santé réalise la mort, pas la structure).
C'est un **raffinement du kickoff** par rapport à la conception §3.4 (qui pensait la
mort purement structurelle, sans voir le rejet de souche).

**Calibrage (divergence documentée) :** la table §4 notait « base 0.1 × âge » pour
les arbres, mais avec la formule figée une résistance 0.1 laisse un tronc établi à
intensité 0.9 ≥ `COUPE_NETTE` (toujours écimable/tuable). Les **ligneux portent donc
une résistance 0.9** et la **rampe d'âge** `f_lignification` réalise l'intention Q4
(semis s'écrase, tronc établi plie). `INTENSITE_PIED=1.0`, `SEUIL_DEGAT=0.5`,
`LIGNIFICATION_SCALE=52` (valeurs de DÉPART, calibrage post-test).

**Pont (0.3.1 → 0.3.2) :** `ecraser` route aussi vers une **plante** quand le
`target` la désigne par position (`x_cm/y_cm`, + `segment` optionnel ; le collet 0
est ici une cible valide, ≠ `tailler`) — routage sur la **forme** du target (Q6).
Message diégétique « écrasé {plante} : déformée / écimée / meurt ».

**Garanties :** golden écolo **INTACT** `16a1b937…` (geste event-driven hors tick,
traits à défaut neutres). `test_vigueur` **115 → 135/135** (bloc A8b : DOUX/NET,
santé en NET seulement, basilic épargné, sentier, coût=tailler×urgence binaire).
`test_sim_server` **89 → 98/98** (routage plante vs guilde, collet valide,
déterminisme byte-à-byte). `test_croissance` 67/67 (seam partagé non régressé).
`main.py` OK.

**Reste (vue) :** le **rendu Godot** du geste sur plante (cliquer → écraser, montrer
déformation/mort) = volet vue ultérieur, le pont est prêt (0.3.2).
