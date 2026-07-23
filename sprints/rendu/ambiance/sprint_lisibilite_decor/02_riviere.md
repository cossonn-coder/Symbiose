# T2 — Rivière : berges franches + surface d'eau + reflets orientés courant

**Sprint :** LISIBILITÉ DÉCOR (reprise D58) · **Type :** rendu / ambiance · **Golden : INCHANGÉ.**
Lire d'abord `00_etat.md`. T1 (forêt) est fait. Ici on rend la **rivière** lisible comme surface d'eau.

## Contexte minimal
`visuals/DecorLayer.cs` → `DrawRiviere(Secteur s)` dessine aujourd'hui une bande d'eau
(`Palette16.EauProfonde`) au cœur de la bande de décor, semée de reflets = cercles de **2 px**
(sous-pixel au dézoom). Résultat : **bande bleue plate**, sans berge ni sens de courant. C'est du
rendu C# pur (`_Draw` statique) — **aucun moteur, aucun golden touché**.

Fichier moteur = source de vérité : **NON concerné**. Ne PAS lancer `test_golden`.
Filet : `dotnet build Symbiose.csproj` (0 erreur / 0 warning).

## Objectif
La rivière doit se lire comme une **surface d'eau continue** creusée dans le terrain : berges
franches, eau à 2-3 valeurs, reflets lisibles orientés dans le **sens du courant** (l'axe sinueux du
lit). Déterministe (hash + 3-sinus, **zéro `Random`**), pixel-art (`Palette16`, valeurs franches).

## Fichiers à toucher
- `visuals/DecorLayer.cs` → `DrawRiviere` (et au besoin `MotifColors`/assise rivière).
- `visuals/Palette16.cs` (couleurs berge / valeurs d'eau, l.126-152).

## Ce qu'il faut faire
1. **Berges franches.** De part et d'autre du lit (le lit occupe `ax ± half`, `half = DepthCm·0.22`),
   dessiner une bande de **berge** distincte (galets/terre clairs) au lieu de laisser l'assise nue.
   Ajouter au besoin une couleur `Palette16.DecorBerge…` (terre/galets, ton clair contrasté).
2. **Bord d'eau assombri (ombre de berge)** : un liseré d'eau plus sombre le long des deux rives →
   creuse le lit, décolle la surface du plan-sol (même logique d'ombre que T1).
3. **Surface à 2-3 valeurs** : au lieu d'un aplat `EauProfonde`, alterner 2 valeurs d'eau par
   dithering **ordonné** (damier hashé déterministe, comme l'existant) pour donner du frémissement.
4. **Reflets orientés courant** : remplacer les cercles 2 px par des **traits/ellipses allongés**
   dans le sens de l'axe du lit (le tracé `Ondulation(SeedSecteur ^ 0x9e37u, …)` donne la direction
   locale — dériver la tangente ou allonger le reflet le long de `u`). Calibrer la taille pour la
   distance d'observation (visibles à zoom large, pas 2 px).

## Ce qu'il NE faut PAS faire
- Ne PAS déplacer/retracer l'axe du lit ni la géométrie du secteur (ossature T4) — on habille l'eau.
- Ne PAS introduire de `Random`/`GetHashCode` visuel — rester sur `HashKey`/`Ondulation`.
- Ne PAS toucher `DecorLayer.Arbres.cs` (forêt = T1) ni `DrawFalaise` (T3).
- Ne PAS lancer `test_epaisseur_500ans` ni aucun test long.
- ⚠️ Le couplage rivière↔falaise (`BuildProfile`, 2e passage) NE change PAS : on ne touche qu'au rendu.

## Vérification
- `dotnet build Symbiose.csproj` = 0 erreur / 0 warning.
- `python3 tools/compte_ldc.py visuals/DecorLayer.cs visuals/Palette16.cs` dans la bande (⚠️
  `DecorLayer.cs` est déjà à ~352 LDC : **rester ≤ 400**, sinon signaler dans `00_etat.md` — si ça
  dépasse, préférer un helper compact plutôt qu'inflater ; ne PAS scinder ici, c'est le job de `/refactor`).
- **Golden : rien à relancer.** Le confirmer dans `00_etat.md`.
- Point F5 (Nico) : la rivière se lit comme surface d'eau creusée, berges nettes, courant perceptible.

## Fin de tronçon
Mettre à jour `00_etat.md` (T2 fait, cap sur T3), commit
(`feat(lisibilite-decor T2) : rivière — berges + surface + reflets courant`), stop.
