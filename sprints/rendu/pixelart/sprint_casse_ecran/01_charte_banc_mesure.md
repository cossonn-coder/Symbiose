# ① Charte + banc de mesure DA — l'instrument avant le dessin

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/etude_brief_da_16bits.md`
(EN ENTIER — c'est la référence), `docs/rendu/pixelart/conception_casse_ecran.md` §2-§3.
**Golden intact.** Filet : `dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.
Ne JAMAIS lancer `test_epaisseur_500ans`.

## Objectif
Avant de toucher au rendu, poser (1) la **table des rampes** et (2) un **banc de mesure**
qui transforme la checklist du brief en chiffres sur les PNG du banc de capture. Les
tronçons ③→⑥ s'en servent pour se valider seuls (Nico ne valide plus qu'au ressenti).

## (1) Table des rampes (données de vue, C#)
- Un fichier C# de données (ex. `visuals/RampesDa.cs`, nom libre) : par **matière** une rampe
  de 3 à 5 tons (+ éclat isolé optionnel), sombre → clair, hex. Matières minimales :
  canopée de jour, tronc/racines, buisson vif, couvert olive (dialecte 2), touffe claire,
  fleur jaune, fleur magenta/violette, terre cuite (bacs/pots), pierre, crème.
  Valeurs de départ = celles du brief (§ Palettes mesurées).
- Par **espèce** (plantes du catalogue vue, faune de `MacroLife.Especes`, carpophores de
  `CarpophoreStyles`) : quelle matière pour feuillage / tige / organe / fleur. Les teintes
  d'espèce existantes (`PlantRenderer.Organs.cs` `OrganPalette`, `PlantRenderer.Palette.cs`)
  servent de point de départ : décliner chacune en rampe à **teinte qui dérive** (ombre vers
  ~133° bleu-vert, éclat vers ~78-87° jaune pour les verts ; règle analogue chaud/froid pour
  les autres) — une petite fonction de dérivation OKLab/HSV documentée vaut mieux que 100
  hex tapés à la main, mais les matières du brief restent en hex tel quel.
- ≤ 5 tons par matière (6 avec éclat). Aucun ton `#000` ni gris neutre quasi noir.
- Ce tronçon ne BRANCHE pas la table au rendu (c'est ③) : elle est lue par le banc.

## (2) Banc de mesure (outil Python hors moteur, ex. `tools/mesure_da.py`)
Entrée : un dossier de PNG de `tools/capture_vm.sh` (+ si utile un masque). Sorties chiffrées
par image, en texte :
- **tons distincts** par zone de matière (au minimum : par sprite isolé sur fond uni de la
  planche L / `WorldView.Planche.cs`, qui pose les espèces séparément) ;
- **pixels noirs** : `#000` et quasi-noirs neutres (chroma OKLab < seuil et L < seuil) ;
- **contour noir sur masse** : fraction des pixels de bord de silhouette qui sont quasi-noirs ;
- **dérive de teinte** : teinte moyenne du quartile sombre vs quartile clair d'un sprite
  (signe attendu : sombre plus bleu-vert, clair plus jaune) ;
- **aplat** : plus grande zone connexe d'une seule couleur à l'intérieur d'une masse (px) ;
- **voisins identiques** : deux sprites de la même espèce côte à côte → distance pixel ;
- **côté de l'éclat** : barycentre des pixels du ton le plus clair vs centre du sprite,
  comparé à la direction du soleil donnée en argument.
Bibliothèque : ce qui est dispo sur la VM (PIL si présent ; sinon `venv` dans /tmp,
cf. mémoire rendu SVG). Déterministe, aucun réseau.

## (3) Mesure de référence AVANT
Lancer le banc sur l'état actuel (planche ×1, ×2, ×4, ×16 ; F11 on/off) et consigner les
chiffres dans `00_etat.md` §Notes ① : c'est la ligne de base que ③→⑥ doivent battre.

## Ne PAS faire
Changer un pixel du rendu ; toucher `data/code/` ; inventer des tolérances sans les
documenter (chaque seuil = une ligne de rationale).

## Fin de tronçon
`00_etat.md` (tableau ① → fait, mesures de base), commit.
