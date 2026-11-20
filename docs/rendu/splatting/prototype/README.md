# Prototype : une tomate mûre en gaussian splats (2026-11-20)

Première étape de l'étude « passer Symbiose en 3D avec des gaussian splats ».
Rendu fait sur la VM, sans Godot ni carte graphique, avec le moteur de rendu CPU
d'[ink-studio](https://github.com/siliconjungle/shapeshift-labs-ink-studio) (MIT, commit `fb94031`).

| Fichier | Contenu |
|---|---|
| `tomate_final.png` | le plant entier |
| `tomate_zoom.png` | gros plan sur les grappes |
| `turn.png` | le plant vu sous 4 angles |
| `tomate.js` | la scène ink-studio |
| `tomate.json` | la tige du moteur Python (`tools.export_structure._grow(Tomato, 30, "summer")`) |

**Construction.** La tige (hauteur, épaisseur) vient du moteur ; les feuilles
composées (phyllotaxie 137,5°), les grappes (une toutes les 3 feuilles, plus mûres
en bas) et le tuteur sont procéduraux, comme le fait la vue C#.

**Mesures [n=1 plant, VM].** 106 000 splats, cuisson 17 s, rendu 2 s.

**Constats.** (1) Le moteur ne décrit qu'une tige droite de 60 cm : tout le port
vient de la vue. (2) 600 plantes à ce niveau = ~60 M de splats : un niveau de
détail est obligatoire. (3) La cuisson doit devenir incrémentale ou passer sur le
GPU, puisque les plantes poussent chaque semaine. Suite : banc de vérité dans
Godot (addon gdgs) sur le nouveau PC de Nico.

**Relancer.** `git clone https://github.com/siliconjungle/shapeshift-labs-ink-studio ink`
puis, depuis ce dossier : `node <ink>/cli/ink-studio.js render tomate.js --colored --out tomate.png`
(Node 18+). La caméra se règle dans `B.finish({ cam: … })`.
