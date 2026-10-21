# Tronçon ② — Vue plante : seuil de visibilité mesuré + voix saine

> Lire d'abord `CLAUDE.md`, `00_etat.md` (formes de légende livrées par ①) et
> `docs/narration/semiologie/conception_infobulle_vivant.md` (§2.5, §2.6, §3, §4.2).
> Golden **INTACT** (aucun Python moteur touché). Filet : `dotnet build Symbiose.csproj`.
> Capture : `tools/capture_vm.sh` (Xvfb → PNG). Jamais `test_epaisseur_500ans`.

## Objectif
L'info-bulle d'une plante ne dit un symptôme que s'il **se voit** au rendu, et dit quelque
chose de juste quand la plante va bien.

## À faire
1. **Mesurer le seuil colorant** : pour chaque cause de `PlantRenderer.ColorantTints`,
   trouver la plus petite intensité `i` telle que la teinte (`i × SymptomTintMax`, puis
   palette / tramage réels du rendu) change **au moins un pixel** d'une plante témoin par
   rapport à `i = 0`, aux paliers où le signe est dit visible (×2, ×4, ×8). Méthode libre
   mais reproductible : soit un mode de capture forçant une intensité (banc dédié, comme les
   bancs F existants), soit un calcul hors moteur qui reproduit exactement la chaîne
   couleur → palette du rendu (vérifie dans `Palette16` / la quantification où elle a lieu).
   Prendre le **max sur les paliers** (le plus prudent) par cause → constante nommée par
   cause (ou une seule si les écarts sont faibles), chiffre `[VM, n=…]` en commentaire.
2. **Seuil des marques fines** (ravageurs / gel / grêle) : lire `DrawLeafDamage`
   (`visuals/PlantRenderer.PaliersHauts.cs`) et en déduire l'intensité à partir de laquelle
   au moins une marque est dessinée (c'est un calcul, pas une mesure, si le nombre de marques
   est une fonction de l'intensité).
3. `SigneVisible(cause, zoom)` → prend aussi l'intensité ; `SigneDominant` ne retient que ce
   qui passe le seuil. **Effet voulu** : `ObserverSigne` (note carnet) ne part plus pour un
   signe invisible.
4. **Voix saine** (aucun signe visible) : une ligne tirée de `voix_saine` (légende ①) :
   `automne` de la plante > 0 (phénophase, déjà lue au snapshot — trouve où) → « automne » ;
   sinon `vitalite` ≥ borne → « franc » ; sinon « terne ». Borne de vitalité : prendre celle
   à partir de laquelle `ApplyVitality` ternit visiblement (même logique qu'au point 1 —
   c'est le dessin qui fait foi) ; constante nommée commentée.
5. **Technique** (Maj+F3) : ajouter `vitalité x.xx · automne x.xx` et marquer les symptômes
   sous le seuil (« sous seuil ») au lieu de les taire.
6. Capture avant/après : plante saine, plante à faible symptôme (sous seuil → voix saine),
   plante au-dessus du seuil ; zoom ×4. PNG dans `mesures/` du sprint.

## NE PAS
- Changer le dessin des plantes (seule l'info-bulle change ; images identiques au pixel).
- Mettre du texte en dur côté C# (tout vient de la légende ①).
- Toucher à la faune / aux carpophores (tronçon ③).

## Fin de tronçon
`00_etat.md` : cocher ②, seuils mesurés avec leur `[VM, n=…]`. `dotnet build` vert. Commit.
