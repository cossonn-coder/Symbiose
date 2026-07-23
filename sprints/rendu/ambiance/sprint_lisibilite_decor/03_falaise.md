# T3 — Falaise : face verticale + ombre portée (surplomb)

**Sprint :** LISIBILITÉ DÉCOR (reprise D58) · **Type :** rendu / ambiance · **Golden : INCHANGÉ.**
Lire d'abord `00_etat.md`. T1 (forêt) + T2 (rivière) faits. Ici la **falaise** doit surplomber.

## Contexte minimal
`visuals/DecorLayer.cs` → `DrawFalaise(Secteur s)` dessine aujourd'hui des **redans à plat** (bandes
de profondeur à 3 valeurs de roche selon la pente), sans face verticale ni ombre → ça ne surplombe
pas, ça reste des stries au sol. La falaise est **rare** (elle dérive du couplage rivière+prairie
voisine dans `BuildProfile`) : **on NE force PAS sa présence** (décision Nico, philo #7) — on la rend
seulement lisible **quand le seed la produit**. Rendu C# pur, **aucun moteur, aucun golden touché**.

Fichier moteur = source de vérité : **NON concerné**. Ne PAS lancer `test_golden`.
Filet : `dotnet build Symbiose.csproj` (0 erreur / 0 warning).

## Objectif
Quand une falaise existe, elle doit **surplomber** : une vraie face verticale contrastée + une ombre
portée au pied côté jardin. Déterministe (hash + 3-sinus, **zéro `Random`**), pixel-art (3 valeurs de
roche franches, `Palette16`).

## Fichiers à toucher
- `visuals/DecorLayer.cs` → `DrawFalaise` (et au besoin `MotifColors`/assise roche).
- `visuals/Palette16.cs` (valeurs roche / éboulis, l.128-155).

## Ce qu'il faut faire
1. **Face verticale.** Au front de la falaise (bord côté jardin du secteur), dessiner un **pan qui
   monte en −Y écran** (comme un mur : cf. `WorldView.Maison.cs` qui élève `wallCm · PxPerCmZ` en
   `Vector2(0, -h)`) — pas seulement des bandes à plat. Ce pan, assombri (`RocheOmbre`), fait lire le
   relief : sol du décor en bas, sommet végétalisé (`DecorRocheHaut`) en haut. La hauteur du pan peut
   dériver de la pente (`PenteFalaise` : Douce basse → Déversante haute).
2. **Ombre portée au pied**, côté jardin (bande sombre au bas de la face) → le surplomb.
3. **Éboulis** : quelques taches claires (`RocheClair`) au pied de la face, semis déterministe hashé.
4. **3 valeurs de roche plus dures** : conserver les redans (`RocheOmbre/Median/Clair`) mais creuser
   le contraste pour que le relief se lise ; le sommet reste végétalisé.

## Ce qu'il NE faut PAS faire
- Ne PAS forcer l'apparition de la falaise (ne PAS toucher `BuildProfile` / le couplage). Rendu seul.
- Ne PAS introduire de `Random`/`GetHashCode` visuel.
- Ne PAS toucher `DecorLayer.Arbres.cs` (T1) ni `DrawRiviere` (T2).
- ⚠️ La face verticale monte en écran : veiller à ce qu'elle reste **dans la bande de décor** et ne
  déborde pas sur le jardin ni sur un secteur voisin (borner sur `u ∈ [0, WorldCm]`, profondeur du front).
- Ne PAS lancer `test_epaisseur_500ans` ni aucun test long.

## Note diagnostic
Pour tester au build sans dépendre du hasard du seed : la falaise apparaît quand un bord est rivière
ET son voisin horaire est resté prairie (`BuildProfile`, 2e passage). Un sous-agent PEUT, en local et
**temporairement**, forcer un secteur en falaise pour vérifier son propre rendu, mais **doit retirer
ce forçage avant commit** (décision Nico : falaise laissée au seed). Ne rien committer qui altère la
distribution.

## Vérification
- `dotnet build Symbiose.csproj` = 0 erreur / 0 warning.
- `python3 tools/compte_ldc.py visuals/DecorLayer.cs visuals/Palette16.cs` — **rester ≤ 400** sur
  `DecorLayer.cs` (déjà ~352 + T2). Si dépassement inévitable, le **signaler** dans `00_etat.md`
  (candidat `/refactor`), ne pas scinder soi-même.
- **Golden : rien à relancer.** Le confirmer dans `00_etat.md`.
- Point F5 (Nico) : quand une falaise est présente, elle surplombe (face verticale + ombre).

## Fin de tronçon
Mettre à jour `00_etat.md` (T3 fait, cap sur T4), commit
(`feat(lisibilite-decor T3) : falaise — face verticale + ombre surplomb`), stop.
