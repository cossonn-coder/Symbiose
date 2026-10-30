# ③ Vue — signaux de l'eau + faune de mare visible

**Golden INCHANGÉ**. `dotnet build` vert. Lire `00_etat.md` (notes ① et ②). Dernier
tronçon : clôt le sprint (vue Godot = toujours le dernier tronçon).

## Signaux (DA : l'animation dit un état — hors signal l'eau ne fait que scintiller, ②)
1. **Rides au vent** : direction/force du vent du snapshot (mêmes uniforms que
   `decor_indexe.gdshader` / `WorldView` vent) → rides tramées qui filent dans le sens du
   vent, d'autant plus serrées qu'il souffle fort. Calme → aucune ride.
2. **Ronds de pluie** : quand il pleut (même source que `WeatherLayer`), petits ronds
   pixel qui naissent et s'élargissent sur l'eau libre (pas sur la glace).
3. **Ronds de gobage** : quand moustique ou libellule sont PEINTS sur la mare (bloc
   `sprites` du snapshot), un rond isolé de temps en temps sous la nuée / la libellule.
4. Sous la glace : aucun de ces signaux.

## Faune de mare lisible
5. **Moustiques en nuée dès ×4** : la grappe envoyée par le serveur (≤ 6) se dessine en
   petite nuée animée (quelques pixels qui dansent, icône `FauneSilhouettes`) au lieu de
   la taille réelle 0,6 cm ; reste discrète (pas un essaim de mouches noires).
6. **Libellule** : vérifier qu'elle est visible en été à ×1-×4 au-dessus de l'eau ; si
   elle ne l'est pas, corriger (taille plancher, contraste avec l'eau sombre du ②).

## Vérification obligatoire
Captures `tools/capture_vm.sh` sur la mare (≈ 1725,425, `full` seed 42, été an 1 vers
s25) : calme, vent fort (`--capture-vent`), pluie (`--capture-meteo`), ×1 / ×4 / ×8 ;
regarder les PNG ; perf (FPS banc) sans régression notable. Mettre à jour `00_etat.md`
(sprint clos) + liste des points F5 pour Nico.
