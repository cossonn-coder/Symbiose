# ③ Vue : branches + couronne d'hiver réaliste + protocole F5 — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3.4 et §3.5.

## Objectif

En hiver, un vrai arbre : des branches, un bouleau nu, quelques feuilles sèches sur hêtre, charme et chêne.

## À faire

1. **Branches** dans `DrawArbreKit` (`visuals/DecorLayer.Houppiers.cs`), AVANT l'enveloppe, après `VentArbre` : l'axe monte dans la
   couronne en s'affinant, 3-5 charpentières à la forme selon `sil.Port` (bouleau fin et retombant, chêne étalé, hêtre ascendant, charme
   sinueux), hash déterministe. Rameaux seulement si `DetailsVisibles`. Rien pour `conique`. Classe `ClasseSansSaison` pour la neige et le
   givre : vérifier le rendu. Tenir sous les ~300 LDC (`DecorLayer.Arbres.cs` : voir s'il faut un fichier dédié).
2. **Couronne** (`lisiere` dans `visuals/decor_indexe.gdshader`) : enveloppe absente en plein hiver ; `DEGARNI_MAX` relevé. Passer `id` à
   `lisiere` : les bouquets de hêtre, charme et chêne gardent ~10 % de touches rousses, plus en bas (`hauteur`), à grain fin (pas la cellule
   de 4 px) ; bouleau nu. Uniform d'id de palette posé dans `DecorLayer.Saison.cs`. Vérifier que l'id d'un bouquet est bien constant par
   essence, palier ×1 compris. Vérifier que le printemps refait une couronne pleine.
3. **Mesure** : captures `smoke -B`, ×0,5 et ×1 : s20 (branches invisibles), s34, s40, s46, avec `-m "Neige,1"`, `-m "Gelée tardive"`.
   Lire les PNG. `tools/perf_vm.sh` avant/après : draw calls constants, sommets, FPS `[n=…, VM]`. Si le gain de sommets est lourd,
   réduire les rameaux au palier bas.
4. `dotnet build Symbiose.csproj` vert.
5. **Clôture** : `00_etat.md` §F5, protocole court pour un ressenti (taches de fleurs, insectes, prairie, branches en automne et en hiver,
   neige sur les branches, feuilles sèches).

## Golden

**INTACT** (vue pure).

## NE PAS

Toucher aux sapins, aux arbres du jardin ou au moteur. Lancer `tests/test_epaisseur_500ans.py`.
