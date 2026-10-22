# ③ Règne fongique — 13 espèces, niche, fructification après la pluie

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.1-§3.2.
**Golden** : NEUTRE attendu (perception pure, hors tick). Si un seuil moteur doit bouger
(ex. dynamique du mycélium), c'est un re-figeage NON prévu → STOP et remontée.

## Objectif
Des carpophores qui sortent en jeu normal, et dont l'ESPÈCE dépend de la niche locale.

- **Registre data-driven** des 13 espèces (table de conception §3.2), en DONNÉE PURE dans
  la couche `fields` (lisible par `fields/population/perception.py` ; ex. un module
  `fields/fongique.py` ou équivalent — à placer en respectant `plants ← fields ← sim`).
  Par espèce : clé, nom, groupe (bois / humus / prairie / verger / mycorhize / parasite),
  substrat requis, familles hôtes (mycorhize/parasite/verger), fenêtre saisonnière
  (semaines), comestibilité (`comestible` / `veneneux` / `mortel` / `psychedelique`,
  amanite tue-mouches = psychédélique ET toxique), éventuel pH. Aucun hôte en dur ailleurs.
- **Espèce d'un carpophore** = déduite à l'échantillonnage de la niche du plot :
  bois frais (`eco.bois_fresh_at`) ; humus/compost (`om_active`, sol remué, structures) ;
  prairie (racines de Poaceae / couverture herbacée) ; racines vivantes d'un hôte
  (familles, via `root_plots` des plantes — patron `sim/champignon_role.plots_racines`,
  calculé UNE fois par tuile). Plusieurs candidates → hash spatial déterministe.
  Les sosies (hypholome/armillaire/collybie, clitocybe/rosé, phalloïde/cèpe) doivent
  partager réellement leurs niches.
- **Fructification** (`sample_carpophores`, `fields/population/perception.py`) : la
  semaine qui SUIT une semaine de pluie (la pluie est un `WeatherEvent` depuis ① ; la
  couche `fields` n'importe pas `sim` → l'appelant `tools/simserver/serialize.py` ~l.357
  calcule « pluie la semaine précédente » et le passe), mycélium ≥ seuil, sol humide,
  fenêtre de l'espèce (remplace le gate automne seul `_CARPO_AUTOMNE`). Recalibrer
  `CARPO_MYCEL_MIN` / `CARPO_HUMIDE_MIN` APRÈS mesure sur le monde réel post ①②.
- **Pont** : chaque carpophore porte la clé d'espèce (nouveau champ en fin de liste
  compacte, l.359-362 ; le rôle `b/r/h` reste). Bump version + note.
- **Mesure** (`mesures/`) sur `full`, 3 graines, 156 sem. : carpophores par an, par
  espèce, par saison [n=…]. Attendu : des carpophores chaque saison de leur fenêtre
  après pluie, plusieurs espèces. Vérifier aussi le banc pluie hebdo du ① : carpophores
  chaque semaine une fois le mycélium installé.

## Ne PAS faire
Pas de champ mycélium par espèce (coût ×13). Pas de voix/fiches (⑤), pas de parasite (④),
pas de dessin (⑧). Le carpophore ne nourrit ni ne décompose (perception).
