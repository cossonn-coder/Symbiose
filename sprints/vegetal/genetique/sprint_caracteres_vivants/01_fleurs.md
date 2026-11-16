# ① Fleurs — six caractères et le coût génétique

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §1, §2.1, §3, §5.
> Golden attendu : **RE-FIGÉ annoncé** — six clés neuves dans le digest, valeurs fondatrices
> tirées avec σ_A, et la nourriture des butineurs dépend désormais de la plante.

## Objectif
Que chaque plante offre une fleur à elle : taille, nectar, pollen, couleur, guides, parfum ;
et que les butineurs choisissent en conséquence.

## À faire
1. **Six caractères en queue** du registre : `taille_fleur`, `nectar`, `pollen`,
   `couleur_fleur`, `guide_nectar`, `parfum` (unités et σ_A : conception §2.1).
2. **`cout_genetique()`** sur `PlantInstance` (conception §3), appliqué partout où
   `cout_defense()` l'est (`sim/engine/croissance.py:163`, `sim/engine/mortalite.py:137` —
   revérifier). Y **rapatrier** `K_THERMO` du sprint ② s'il vit ailleurs. Table `K_g` dans le
   registre (champ `cout`).
3. **`poids_floral`** (`fields/population/registry.py:384`), source unique du champ et des
   agents : `ressource × nectar` (ou `pollen` pour la voie `pollen_vibre`), `floraison ×
   taille_fleur` pour l'attrait, `× preference_couleur(type, plante) × efficacite(guide)`.
   La signature reçoit déjà la plante. Ajouter au **spec de type** (`fields/population/spec.py`
   ≈ l. 92-114) une **couleur préférée** par type de butineur (donnée : abeille bleu/violet/
   jaune, bourdon bleu/violet, papillon rose/rouge/orange, syrphe jaune/blanc ; une seule
   représentation, par exemple un angle de teinte et une largeur de préférence).
4. **Axe de couleur par espèce** (donnée de classe, `plants/base/familles.py` + espèces
   florales) : deux teintes extrêmes ; `couleur_fleur` place la plante sur l'axe. Défaut
   neutre pour les espèces non florales ou anémophiles (la préférence vaut 1).
5. **Pollen** : la dose anémophile (`sim/engine/anemophilie.py`) est multipliée par `pollen`.
6. **Parfum** : (a) multiplie l'attrait dans `poids_floral` ; (b) réduit la pression des
   ravageurs sur la plante (`herbivory_pressure`, `sim/effects/perturbations.py`) d'un
   facteur borné. Une seule lecture par effet.
7. **Perf** : `poids_floral` est appelé par plante × type ; mesurer le smoke avant/après
   (budget ≤ +2 %), mémoïser la préférence de couleur par (type, plante) dans le tick si
   besoin (mémoire « pas de recalcul dans un tick »).
8. **Banc headless** (`mesures/`) : sur 5 ans, la moyenne de `couleur_fleur` d'une bourrache
   dérive vers la couleur du butineur dominant ; une phacélie à gros `nectar` nourrit plus.
   Si rien ne bouge, **enquêter** (un tronçon inerte n'est pas un succès).
9. **Re-figeage** : diff du digest lu, `--capture`, hashes consignés.

## Tests
- Test ciblé : `poids_floral` croît avec `nectar`, `taille_fleur`, `guide_nectar`,
  `parfum` ; la préférence de couleur est maximale sur la teinte préférée ; `cout_genetique`
  baisse avec un excès coûteux et ne passe pas sous le plancher.
- Suites butineurs et pollinisation existantes vertes.

## Ne PAS faire
- Rendu des pétales (⑥). Signal de changement de couleur après pollinisation (BACKLOG).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ① FAIT, mesures, hashes. Commit.
