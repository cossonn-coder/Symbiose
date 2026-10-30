# ② Vue — l'eau de la mare en DA 16 bits (marnage, glace, scintillement)

**Golden INCHANGÉ** (aucun Python). `dotnet build` vert. Lire `00_etat.md` (notes du ①
pour le format exact du bloc `marais` 0.6.2 : lame + glace).

## But (critère = ce qu'on VOIT, vérifié au banc de capture)
1. **Eau en DA 16 bits** : remplacer les aplats de `PuddleLayer.Mare.cs` par un rendu
   tramé (rampe de 3-4 tons de l'eau, tramage Bayer, cœur plus profond = plus sombre),
   dans la grammaire de la palette indexée (`RampesDa`, cf. `PaletteIndexee.cs`).
   Patron recommandé : un shader dédié `visuals/eau_mare.gdshader` sur la couche (comme
   `decor_indexe.gdshader` pour la lisière) — un seul draw call conservé.
2. **Scintillement au repos** : reflets clairs tramés qui scintillent LENTEMENT (TIME
   dans le shader, déphasés par plot, 2-3 tons). **Visibles dès ×1** (pas de trait de
   1 px) — c'était le défaut constaté par Nico.
3. **Marnage progressif** : lame (bloc `marais` 0.6.2) → eau profonde / eau peu profonde
   (tramage eau-vase) / vase LUISANTE (vase + éclats humides) / vase sèche. Plus jamais
   de bascule eau → terre brune d'un plot à l'autre d'une semaine sur l'autre.
4. **Glace** (champ glace du bloc `marais`) : surface gelée claire, blanc-bleuté tramé,
   fêlures ; scintillement coupé sous la glace ; glace partielle = bords gelés d'abord.
5. Rive et berge du ⑤ conservées, recolorées dans la même rampe.

## Vérification obligatoire
Captures `tools/capture_vm.sh` sur la mare (centre monde ≈ 1725,425 ; `full` seed 42) :
été (eau + marnage), hiver (glace — choisir `--capture-semaines` en hiver), à ×1, ×2,
×4, ×8. Mesurer avec `tools/da_image.py` (quasi-noir, nombre de tons) et **regarder les
PNG** : reflets visibles à ×1, pas d'aplat uni, pas de brun en plein milieu de l'eau.
Consigner chemins des PNG + constats dans `00_etat.md`. Perf : pas de draw call en plus.
