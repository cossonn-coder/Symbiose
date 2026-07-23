# T1 — Forêt : contraste + volume + ombre portée + silhouette de cime

**Sprint :** LISIBILITÉ DÉCOR (reprise D58) · **Type :** rendu / ambiance · **Golden : INCHANGÉ.**
Lire d'abord `00_etat.md` (diagnostic + décisions). Ceci est le tronçon **prioritaire** (le gros gain).

## Contexte minimal
Le décor d'ambiance (`visuals/DecorLayer.cs` + `visuals/DecorLayer.Arbres.cs`) s'affiche
correctement mais la **forêt se lit comme une tache verte plate** : les houppiers sont peints dans
des verts quasi identiques à l'assise du sol forestier et ne se décollent pas du plan-sol. C'est
100 % du rendu C# (`_Draw` statique), **aucun moteur, aucun test golden touché**.

Fichier moteur = source de vérité : **NON concerné**. Ne PAS lancer `test_golden` (rien côté Python
ne change). Filet de compilation : `dotnet build Symbiose.csproj` (doit rester 0 erreur / 0 warning).

## Objectif
La forêt doit se lire comme une **masse volumée détachée du sol**, avec une silhouette de cime
bosselée contre le jardin. Tout reste **déterministe** (hash djb2 + 3-sinus par seed, **zéro
`Random`** — philo #3) et **pixel-art** (2-3 valeurs franches, `Palette16`).

## Fichiers à toucher
- `visuals/DecorLayer.Arbres.cs` (l'essentiel : `DrawVolumeBlob`, `DrawArbre`, `DrawForet`).
- `visuals/Palette16.cs` (ajuster/ajouter des couleurs décor forêt, l.122-158).

## Ce qu'il faut faire
1. **Marches de valeur franches** dans `DrawVolumeBlob` (aujourd'hui `Assombrir(col, -0.16)` masse /
   `+0.14` calotte, soit ±15 % — trop timide). Passer à ~**−0.25 masse / +0.30 calotte**. La calotte
   éclairée doit être décalée vers le **SO** (sud-ouest écran, soleil commun aux plantes et à la
   maison) — vérifier le sens actuel (`Vector2.Down * ry * 0.32f` décale vers le bas/sud) et
   l'orienter aussi légèrement vers l'ouest (x négatif) pour coller au SO.
2. **Ombre portée au pied de chaque arbre.** Dans `DrawArbre`, AVANT `DrawTronc`/`DrawHouppier`,
   peindre une ellipse sombre **aplatie** au sol à `basePos` (rx ≈ canopyR·0.7, ry ≈ canopyR·0.22,
   couleur = assise forêt assombrie, p.ex. `Assombrir(DecorForetFond, -0.30)`). Elle décolle la masse.
   ⚠️ ordre de peinture : l'ombre de CHAQUE arbre doit être sous SON houppier ; comme `DrawForet`
   trie déjà par Y écran et peint du lointain au proche, peindre l'ombre juste avant le tronc dans
   `DrawArbre` suffit (le proche recouvre proprement).
3. **Silhouette de cime.** Ajouter un liseré/calotte éclairé marqué sur le **haut** des houppiers
   (surtout en lisière, faible profondeur `dn`) pour un bord supérieur bosselé lisible. Piste simple :
   dans `DrawHouppier`/`DrawBlobCloud`, un blob de calotte supplémentaire plus clair au sommet de
   l'enveloppe. Ne pas surcharger : 1 accent clair par houppier suffit.
4. **Palette.** Pour que les cimes éclairées ressortent : pousser `DecorForetFond` un cran plus
   **sombre/froid**, et re-répartir les feuillages en **valeurs distinctes** (aujourd'hui hêtre
   `#2c5730` ≈ fond `#2f5738`) — chêne/hêtre/charme ne doivent pas être le même vert. Garder des
   couleurs cohérentes 16-bits (pas de fluo). Documenter chaque changement en commentaire.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher la géométrie de placement (`DrawForet` grille/densité/gradient de lisière) : la
  densité est **bonne**, seul le rendu de chaque arbre change. (Micro-ajustement du gradient toléré
  seulement si nécessaire à la lisibilité, à signaler.)
- Ne PAS introduire de `Random`/`GetHashCode` visuel — rester sur `HashKey`/`Ondulation`.
- Ne PAS passer à des sprites. Ne PAS animer (vent = dette D72, hors sujet).
- Ne PAS toucher `DecorLayer.cs` (rivière/falaise/prairie = T2/T3), sauf si un helper commun
  (`Assombrir`) doit être partagé — dans ce cas ne pas en changer le comportement pour les autres.
- Ne PAS lancer `test_epaisseur_500ans` ni aucun test long.

## Vérification
- `dotnet build Symbiose.csproj` = 0 erreur / 0 warning.
- Garde-fou taille : `python3 tools/compte_ldc.py visuals/DecorLayer.Arbres.cs visuals/Palette16.cs`
  doit rester dans la bande (≤ 300 confortable, 300-400 vigilance si responsabilité unique).
- **Golden : rien à relancer** (aucun changement moteur). Le confirmer dans `00_etat.md`.
- Point F5 (Nico) : la forêt se lit comme masse volumée détachée du sol, cime bosselée.

## Fin de tronçon
Mettre à jour `00_etat.md` (§DÉCISIONS + §REPRISE : T1 fait, cap sur T2), commit
(`feat(lisibilite-decor T1) : forêt volumée — contraste + ombre + cime`), puis stop pour le
sous-agent suivant (T2).
