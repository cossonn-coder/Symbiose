# ② Bibliothèque des feuilles

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (§3-4) et le
compte rendu du ① dans `00_etat.md` (format, V vues, échelles, mesures).
**Ne démarrer que si la porte du ① est passée.**

## Existant
- Outil `tools/splat/` + recette « feuille composée » (①).
- Vocabulaire des feuilles dans la vue (lire, ne pas modifier) :
  - `visuals/PlantRenderer.PortsFiches.cs` : `enum FormeFeuille` (15 formes :
    Dentee, Spatule, Lobee, Ovale, Cuillere, Plume, Ruban, Coeur, Scie, Lanceolee,
    Palmee, Paume, Triade, Composee, Lierre) et `enum MarqueFeuille` (8 marques) ;
  - `visuals/PlantRenderer.Leaf.cs` : `enum LeafShape` (6 formes des paliers
    hauts : Elliptique, Lanceolee, Cordee, Lobee, Composee, Aciculaire) et le
    profil par espèce (`LeafProfile`) ;
  - le kit des paliers bas : `visuals/PlantRenderer.Kit.cs` (touffes = quelques
    feuilles rayonnant d'un point, 4 tailles internes × 3 variantes).
  Vérifier comment ces trois vocabulaires se recoupent (une même forme sous deux
  noms ?) et cuire **une recette par forme distincte**, en le documentant dans le
  manifeste (table « nom vue → recette »).

## Objectif
1. Une recette JS par forme de feuille distincte, plus une recette **touffe**
   (pour les paliers bas, D4) construite à partir des feuilles.
2. Chaque recette : vues V, tous paliers, **3 variantes** au hash, et pour les
   paliers où la vue montre les symptômes (×16, ×32 — vérifier `PaliersHauts.cs`)
   les **trous** en 2-3 degrés (D5) : morsures (bord grignoté) et criblage de grêle
   (petits trous). Les couleurs (nécrose, taches, givre) ne sont PAS cuites (D5).
3. Les **marques** (`MarqueFeuille` : duvet, gouttes, pli, éclat, gaufre, revers,
   nervures) : les cuire si elles sont du relief (pli, gaufre, nervures) ; les
   laisser à la vue si ce sont des effets de couleur/brillance — dire lesquelles.
4. Planche de contrôle (comme ①) de toutes les feuilles + mesure du **poids**.

## Mesures (dans `00_etat.md`)
Nombre de pièces, poids des planches, temps de cuisson total [VM]. **Alerte (D2) :
si le kit dépasse ~200 Mo, s'arrêter et consigner** (réduire V ou les variantes
est une décision à remonter).

## Golden
**INTACT**.

## Ne PAS faire
Toucher au C#, aux fiches d'espèces, aux sources d'ink-studio ; régénérer des
planches dont la recette n'a pas changé (D2).
