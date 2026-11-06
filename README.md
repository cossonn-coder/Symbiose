# Symbiose

**Un jardin éternel en permaculture.** Symbiose est un bac à sable écologique : un seul
jardin, persistant, dont le sol garde la mémoire de tout ce qui s'y est passé. On n'y
gagne rien et on n'y perd jamais. On observe, on agit sur le milieu, et l'écosystème
répond.

> Projet personnel, en développement, destiné aux amis et à la famille.
> Une version physique (tuiles imprimées en 3D + cartes) est conçue en parallèle.

---

## L'idée

- **On agit sur le milieu, pas sur les plantes.** Pailler, arroser, composter, creuser
  une mare, poser un brise-vent… On ne donne jamais de bonus à une plante : on change un
  flux (eau, lumière, azote, abri), et la plante y répond à sa façon. Arracher ou écraser
  reste possible, mais coûte cher en **Vigueur**, l'énergie du jardinier.
- **Tout est simulé, rien n'est scripté.** Sol vivant (pH, azote, phosphore, potassium,
  humus, microbiome, mycélium), eau qui ruisselle et forme des mares, lumière au
  centimètre près, météo, faune (pollinisateurs, ravageurs, auxiliaires, décomposeurs),
  succession spontanée, génétique et plasticité des plantes.
- **Déterministe.** Une graine de monde donne toujours le même terrain et la même
  histoire. Deux graines différentes donnent deux jardins jamais pareils.
- **Pas de chiffres à l'écran.** On lit son jardin comme un naturaliste : feuilles qui
  jaunissent, sol qui craquelle, oiseaux qui annoncent l'orage. Trois voix aident à
  comprendre : une **encyclopédie** qui se remplit à mesure des découvertes, un
  **carnet** tenu automatiquement, d'abord descriptif puis interprétatif quand on a
  compris, et des **pages secrètes** à trouver.
- **La connaissance ouvre l'espace.** Maîtriser une famille de plantes ou un concept
  écologique agrandit le terrain et augmente la Vigueur. Au dernier palier, on n'a plus
  besoin d'agir : le jardin tient tout seul.

## Architecture

Deux processus qui se parlent en JSON :

```
┌──────────────────────────┐   stdin/stdout JSON   ┌──────────────────────────┐
│  Godot 4.6 .NET (C#)     │ ───────────────────▶  │  Moteur Python           │
│  la VUE                  │                       │  la VÉRITÉ écologique    │
│  rendu pixel-art iso,    │ ◀───────────────────  │  data/code/              │
│  caméra, gestes, HUD     │      instantanés      │  tools/sim_server.py     │
└──────────────────────────┘                       └──────────────────────────┘
```

- **Le moteur Python (`data/code/`) est la source de vérité.** Toute mécanique y vit.
  Godot ne simule rien, il dessine et transmet les gestes.
- Couches du moteur, sans import vers le haut : `plants ← fields ← sim ← engine`.
  - `plants/` : espèces, génétique, familles, catalogue
  - `world/` : tuiles, maison
  - `fields/` : lumière, sol, banque de graines, vie macro, ceinture périphérique
  - `sim/` : croissance, reproduction, succession, météo, Vigueur, gestes, maîtrise
- Côté Godot : `core/` (pont `SimBridge`, données), `visuals/` (rendu des plantes,
  ombres, vie macro, heatmaps), `world/` (`WorldView.tscn`, la scène principale).

## Lancer le jeu

**Prérequis** : Godot 4.6 **.NET**, .NET SDK 8.0 et Python 3 récent, testé en 3.13 et 3.14 (bibliothèque standard
uniquement, aucune dépendance à installer).

1. Ouvrir `project.godot` dans Godot 4.6 .NET.
2. Lancer avec **F5**. Godot démarre le moteur (`python3`, ou `python`) tout seul.
3. Choisir un monde au démarrage : `full` (le jardin complet de 20 × 20 m, 8 tuiles
   autour de la maison) ou un banc d'essai (`verger_mur`, `succession`, `lianes`…).

### Commandes principales

| Touche | Effet |
|---|---|
| Espace | Planification (temps figé) ↔ saison (temps réel) |
| Clic | Geste courant (planter, arroser, pailler, tailler, manger…) |
| Tab | Geste suivant |
| S / B / N | Espèce à planter / substrat / nature du paillis |
| Molette, Page↑/↓ | Zoom par paliers entiers / rotation de la vue |
| M | Vitesse de simulation |
| F1 | Texte du HUD : jeu → nu → aide |
| X | Paramètres |
| C | Copier le rapport de performance |

Touches de debug : F2 (dossier d'une plante), F6 (heatmaps des champs écologiques),
F7 (température du sol), G (gènes au survol), I (vie macro), O (ombres), F12 (défilé
météo).

## Le moteur seul

Tout se lance depuis `data/code/` :

```bash
cd data/code
python3 main.py                  # démo : 8 tuiles + maison
python3 -m tests.test_golden     # test de déterminisme (2 tuiles × 4 ans)
python3 -m tests.test_croissance # une des suites ciblées (tests/)
```

**Le golden est sacré** : tout changement du moteur doit laisser son empreinte
identique. S'il bouge, c'est voulu, expliqué et annoncé, jamais par accident.

## Méthode de travail

Le projet est mené avec un assistant IA (Claude Code), selon un cycle documenté dans le
dépôt :

- `docs/<type>/<thème>/` : conceptions (champs, végétal, faune, joueur, narration,
  rendu, perf, méta). Carte complète dans `docs/ARBORESCENCE.md`.
- `sprints/` : chaque chantier est découpé en tronçons autonomes (`00_etat.md` +
  kickoffs `0N_*.md`). Les sprints clos sont rangés sous `sprints/_clos/`.
- `journal.md` + `journal/` : l'historique des décisions.
- `DETTE.md` et `BACKLOG.md` : ce qui reste à faire.
- `CLAUDE.md` : les règles du projet, dont les 7 principes de design.

## État

Le moteur est riche et tourne sur des siècles simulés. La vue Godot affiche le monde
complet en pixel-art isométrique (inspiration 16 bits). Reste notamment : packaging
(moteur gelé en binaire + export Godot), extension du terrain par la maîtrise, et
beaucoup de calibrage au ressenti.
