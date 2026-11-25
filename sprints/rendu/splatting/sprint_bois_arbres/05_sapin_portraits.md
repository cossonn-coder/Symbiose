# ⑤ Cône du sapin et portraits d'arbres — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/splatting/conception_bois_arbres.md` (B3, §3.5),
`tools/splat/README.md` (portraits).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
1. **Sapin conique EN JEU** (B3, vue seule) : le moteur donne un poteau peu ramifié ; la vue dérive
   des étages de rameaux (`RecettesRameaux["FirTree"]`, `PlantRenderer.Rameaux.cs:48`) dont la
   longueur DÉCROÎT avec la hauteur sur le tronc (et à partir du bas du tronc, comme un sapin non
   élagué), étages réguliers, aiguilles portées par ces rameaux. Toujours dans le rayon réel
   `_rayonReelCm` (la vue densifie sans élargir) — si le cône exige plus large, le signaler, ne pas
   tricher. Clé stable conservée (couper une branche ne déplace pas les autres).
2. **Portraits** (`tools/splat/portraits/arbres.js`, `cuire_portraits.js`) : écorces du ② (bouleau
   blanc, etc.) et tube lissé ; sapin conique (même règle qu'en jeu) ; **cerisier** en fleurs et en
   cerises (vérifier pourquoi ni l'un ni l'autre n'apparaît : stades du portrait, `FruitsArbres`) ;
   **figuier** (port buissonnant, grandes feuilles palmées — `RecettesRameaux["Fig"]`).
   Recuire seulement les portraits d'arbres, puis `godot --headless --import` et supprimer les
   `.import` parasites de `docs/` et `sprints/`.

## Mesures
- `houppiers` ×1/×4/×8 sapin avant/après (place du sapin : `data/code/bancs/houppiers.py`) ;
  `-Y FirTree` (coupe d'une branche : rien ne saute ailleurs).
- `mesures/controle_portraits_*.png` relus espèce par espèce ; encyclopédie `-Z encyclo:… -P`.
- Déterminisme : 2 cuissons d'un portrait = mêmes octets. Captures `mesures/05_*`.

## Ne PAS faire
- Modifier le moteur pour le sapin (une architecture de conifère au moteur n'est PAS ouverte en dette).
- `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md`, commit.
