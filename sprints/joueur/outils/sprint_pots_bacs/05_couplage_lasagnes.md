# ⑤ Couplage fond ouvert + lasagnes (arc complet)

> Lire `00_etat.md` + conception §5, §6. Dépend de ④. Dernier tronçon moteur.
> Golden NEUTRE. Clôt le sprint (hors vue ⑥ différée).

## Objectif
Faire COMMUNIQUER un bac à fond ouvert avec la tuile sous lui (interconnexion des
acteurs) et valider l'arc lasagne de bout en bout.

## À faire

### A. Couplage fond ouvert (bac `fond_ouvert=True`)
Un bac est posé à `(x_cm, y_cm)` → repérer le **plot de tuile dessous**
(`floor(pos / PLOT_CM)` + la tuile qui contient ce point). Le `Container` doit
connaître sa tuile/plot d'assise (passés à la pose, `poser_bac`).
1. **drainage → tuile** : dans `tick_chimie`, capter la part d'eau évacuée par
   `tick_hydrology` (aujourd'hui `h *= drainage`, la perte `h*(1-drainage)` est
   jetée). Pour un bac couplé, **injecter** cette perte dans l'humidité du plot de
   tuile (`tile_eco.humidite.add(r, c, perte)`). Pont matière. (Implémentation
   propre : faire calculer à `tick_hydrology` la perte et la retourner, ou exposer
   un hook ; éviter de dupliquer la boucle hydrologique.)
2. **racines → tuile** : quand le root-bound est atteint (③, `occupation >
   ROOTBOUND_SEUIL`), autoriser les `root_plots` de la plante du bac à **s'étendre
   dans le plot de tuile** sous le bac → `eco`-uptake AUSSI sur `tile_eco` à ce
   plot → **lève l'effet nain** (la plante puise enfin en profondeur).
3. **microbiome/om → tuile** : diffusion LENTE bidirectionnelle entre la cellule
   du bac et le plot de tuile (knob d'échange faible, ex. `COUPLAGE_DIFFUSION`),
   colonisation par le bas. Déterministe.

**Pot** (`fond_ouvert=False`) : SEUL le drainage s'écoule vers la tuile dessous
(point 1) ; racines confinées (pas de point 2) ; pas de diffusion (pas de point 3).

### B. Lasagnes — arc complet validé
- Aucune mécanique neuve : la `litiere_precharge` (① registre, ② injection) se
  décompose dans le mini-sol (`tick_decomposition`, déjà tické) → NPK disponible
  progressivement → la plante en pot (③) est nourrie dans le temps.
- Test de bout en bout : un pot `lasagnes` planté → la plante reçoit un flux NPK
  CROISSANT sur N semaines (faim d'azote initiale due au `bois`, puis libération),
  à comparer à un pot `drainant_mineral` (pauvre, plante chétive). C'est la
  validation de l'astuce « lasagne = litière pré-chargée ».

## Définition de done
- `tests/test_couplage.py` : bac fond ouvert → humidité de la tuile dessous monte
  après arrosage du bac (drainage transmis) ; root-bound atteint → uptake sur la
  tuile détecté + croissance reprend (nain levé) ; microbiome diffuse bac↔tuile.
  Pot fond fermé → drainage transmis MAIS racines confinées, pas de diffusion.
- `tests/test_lasagnes.py` (ou section dans test_conteneur) : flux NPK croissant
  d'un pot lasagnes, plante mieux nourrie que substrat pauvre, faim d'azote
  initiale. Déterminisme h1==h2.
- **Golden PROUVÉ NEUTRE** (smoke + population bit-identiques) — aucun bac/pot dans
  le smoke. Suites amont TOUTES vertes.
- Pont `sim_server` : exposer `fond_ouvert` + le couplage dans le snapshot si
  utile à la vue (sinon laisser à ⑥). MAJ version protocole si touché.
- MAJ `00_etat.md` (⑤ FAIT, **sprint moteur CLOS**, reste ⑥ vue différée) + commit.

## Pièges
- Ne pas dupliquer la boucle hydrologique pour capter la perte de drainage —
  préférer un retour/hook propre sur `tick_hydrology`.
- Le couplage racines→tuile doit RESTER déterministe (ordre d'itération stable).
- Golden : le couplage ne s'exerce que sur des conteneurs ; le smoke n'en a pas →
  neutralité. La PROUVER, et si dérive : analyser (probable fuite d'un défaut).
- Clôturer en pointant la vue Godot ⑥ vers la dette/le sprint vue (Option B).
