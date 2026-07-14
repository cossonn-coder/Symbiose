# 2026-07-14 — Sprint ALLÉLOPATHIE RACINAIRE — CLOS (`/sprint-auto`)

Exécution autonome des 6 tronçons figés (`sprints/sprint_allelopathie/`,
conception FIGÉE 2026-07-13, entrée `117`). Chimie plante↔plante : une plante
libère par ses racines des composés qui inhibent germination et croissance des
voisines. Comble un trou mécanique NET (concept jusqu'ici purement narratif) et
**lève le TODO `plants/base/familles.py:440`** (injection NÉGATIVE dans un champ,
fin de la triche `adjacency_bonus`).

## Tronçons livrés (①→⑥)

- **① champ + injection + décroissance** (`5494f53`) — champ de sol UNIQUE
  `allelopathie` (D4, GridField borné) initialisé nul, alimenté par
  `inject_field` (route auto via `get_field`, aucune modif `resolution.py`).
  Décroissance labile **modulée microbiome** (sol vivant détoxifie) dans un helper
  PUR `fields/ecofields/allelopathie.py` (patron `mycelium.py`), wrappé par
  `ticks.tick_allelopathie`, appelé en `boucle.py`. Trait `allelopathie_emission`
  déclaré (renseigné au ⑤). **Golden NEUTRE inchangé** `ebe04b44…`.
- **② lecture germination** (`c63fe31`) — escompte de niche de levée par rampe
  douce **Monod** `f = 1 − sensibilité·x/(x+K)`, sur les deux chemins (grains
  plantés `_lever_grains_en_attente` + adventices férales `arch_allelo`, patron
  `arch_ph`/`arch_temp`). Trait `allelopathie_sensibilite`, auto-tolérance ≈
  sensibilité basse de l'émetteur. **Golden inchangé** (champ nul ⇒ f=1).
- **③ escompte croissance** (`cb28348`) — rabotage multiplicatif borné
  (`ALLELO_GROWTH_ESC_MAX=0.6`) de la cible de croissance selon la concentration
  moyenne sur l'empreinte racinaire (`root_plots` **réutilisée, pas recalculée**),
  même rampe Monod que ②. Escompte le GAIN, jamais `vitalite` (philo #2).
  **Golden inchangé**.
- **④ autotoxicité / fatigue du sol** (`406847e`) — champ `autotox` + traceur
  léger d'espèce récurrente par plot (`autotox_espece`) : la ré-occupation d'un
  plot par la même espèce ÉMETTRICE accumule une fatigue **spécifique**, redescente
  à la rotation/sol nu (détox ∝ microbiome). Méthode `allelo_effectif(r,c,class)` =
  allélopathie ambiante + autotox propre à l'émetteur ; lu par ②/③. **Golden
  inchangé** de fait (traceur non armé tant qu'aucun émetteur ⇒ invariant du
  kickoff satisfait ; le re-figeage prévu se matérialise au ⑤).
- **⑤ espèces émettrices + voix** (`296ff7e`) — traits d'émission via
  `family_effects inject_field allelopathie` : **noyer** (fort 0.20), **tournesol**
  (modéré 0.08), **basilic/aulx** (léger 0.02 — **lève le TODO `familles.py:440`**)
  + sensibilités (tomate 1.5, Poaceae 0.4). Deux espèces neuves complètes avec
  leurs **5 voix** : **armoise** (Artemisia, vivace toxique, pages P32) et
  **seigle** (Secale, engrais vert allélopathique, P33) — encyclopédie 3 niveaux,
  magazine, carnet, événements. **Golden RE-FIGÉ MAÎTRISÉ ANNONCÉ**
  `ebe04b44…` → **`da2729c5…`** : re-figeage prévu (décalé du ④), dérive PROUVÉE
  localisée aux émetteurs du smoke (tournesol + basilic) — neutralisation ciblée ⇒
  retour bit-identique au baseline. Tests voix verts (encyclopédie 68/68, pages
  60/60).
- **⑥ vue Godot** (`82e9306`) — bloc snapshot **creux** `allelopathie` par tuile
  (pont **protocole 0.5.29**, patron `alarme`/`couverture`). Overlay F6 sur
  `allelopathie`/`autotox` (GridField déjà exposés par introspection → zéro code
  registre). Indice diégétique `visuals/AllelopathieLayer.cs` : halo de sol **pelé**
  ∝ charge (pendant négatif exact de `CouvertureLayer`, philo #5). **Golden INTACT**
  `da2729c5…`, `dotnet build` **vert** (0 erreur, 0 avertissement).

## Bilan

**Golden final `da2729c5962d2f61c106c8ec9d766e52f75fc72e09bb5914595e33f4461898b7`**
(1 seul re-figeage maîtrisé, au ⑤, comme annoncé au kickoff). Refactor auto-léger :
**no-op** — aucun fichier touché en zone rouge (> 400 LDC pur) ; plus chargés en
zone jaune tolérée (responsabilité unique) : `encyclopedie_corpus.py` 362,
`cultivees.py` 349, `container.py` 315.

**Interconnexions** (règle projet) : décroissance modulée microbiome, autotoxicité
spécifique à l'espèce, escompte sur l'empreinte racinaire partagée.

**Reste F5 Nico** : overlay F6 `allelopathie`/`autotox` lisible ; halo de terre
pelée sous les émetteurs (tournesol/basilic au smoke, noyer/armoise sur carte
fournie) ; densité/opacité/teinte du halo + constantes de calibrage
(`ALLELO_GERM_K`, `ALLELO_GROWTH_ESC_MAX`, montée/repos autotox, sensibilités par
espèce) = placeholders à affiner en jeu.
