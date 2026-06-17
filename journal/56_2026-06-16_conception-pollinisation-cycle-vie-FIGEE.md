## 2026-06-16 — Arc Pollinisation & cycle de vie — CONCEPTION FIGÉE (conception seule)

**Conception seule, aucun code moteur** → golden inchangé. Livrables : kickoff
`sprints/sprint_pollinisation_cycle_vie/00_conception_kickoff.md` + spec figée
`docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` (§A–§F). S'appuie sur
l'horloge `daylength(wiy)` posée au sprint saisonnalité vie macro.

**Audit clé** : le **brassage génétique pollinisé existe déjà** (`reproduction.py`
`find_father`/`child_genes` + `pollinator_reach` modulé par le champ
`pollinisateur`, D31.2). L'arc ne le reconstruit pas — il ajoute ce qui manque.

**Décisions Nico (A–E)** :
- **A — Floraison réelle** : scalaire `floraison ∈[0,1]` sur `PlantInstance` ;
  **double porte** = forçage thermique (degrés-jours `gdd_accum`, reset annuel,
  `T_BASE_FLORAISON`≈6) **ET** photopériode (`daylength` dans `bloom_daylen_min/max`
  par espèce) ; une fenêtre par espèce, surtout estivale. Remplace le proxy de rendu.
- **B — Nouaison pollinisée** : dose `pollen_recu += pollinisateur_local × floraison`
  intégrée pendant la floraison ; nouaison **continue** (fraction des `organ_sites`
  ∝ dose) déclenchée **en fin de floraison PAR PLANTE** (remplace le rendez-vous
  global `FRUIT_NOUAISON_WEEK`) ; `self`/`wind` nouent pleinement (sans insectes),
  entomophiles **SANS plancher** (0 pollinisateur → 0 fruit → extinction locale
  possible, pression assumée).
- **C — Rétroaction** : ressource du champ `pollinisateur` =
  `Σ(floraison × attractivite_pollinisateur)` (nouveau trait nectar, mellifères
  forts) en remplacement de `_flower_grid` ; **pas de Vigueur joueur** (récompense
  écosystémique, philo #1).
- **D — Chenille → papillon (cycle bouclé)** : 2 champs légers `chenille` +
  `chenille_nourrie` (PAS une 5ᵉ guilde) ; **ponte des papillons** (`chenille ∝
  pollinisateur × feuillage`) ; les chenilles s'ajoutent à l'herbivorie
  (`HERBIVORY_GAIN` lira `ravageur + chenille`) ; **maturation par la nourriture** ;
  **famine → mortalité** ; métamorphose (`chenille_nourrie ≥ seuil`) → transfert
  vers `pollinisateur` avec perte partielle. Effet émergent visé : chenilles du
  printemps → bouffée de pollinisateurs en été, pile pour la nouaison.
- **E — Brassage multi-pères** : NON retenu (l'existant suffit).

**Garde-fous** : philo #2 (flux→contrainte→émergence, jamais de malus direct),
#3 (déterministe via `daylength`/`_hash_noise`), #6 (apprentissage diffus),
interconnexion totale (fleurs ↔ pollinisateurs ↔ fruits ↔ graines ↔ chenilles).

**Découpe d'impl (§F, sprint MOTEUR à venir)** : ① floraison+phénologie (golden
visé NEUTRE) → ② nouaison pollinisée (golden probablement neutre — tomate meurt
w2-3, pommier pas de fruit < 5 ans) → ③ reconnexion ressource pollinisateur
(golden RE-FIGÉ maîtrisé) → ④ cycle chenille (golden RE-FIGÉ maîtrisé, invariant
`chenille=0` ⇒ herbivorie inchangée). Pas de ⑤. Vue Godot ensuite (hors sprint).

**PROCHAIN** : implémentation tronçon ① (kickoffs `01_*.md`… à écrire au démarrage).

---
