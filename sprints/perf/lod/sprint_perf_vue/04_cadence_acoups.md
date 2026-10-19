# ④ — Cadence adaptative « au plus vite », à-coups, reliquats D109

> Lire d'abord `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_perf_vue.md` §3.3-3.4 et §3.7,
> et D109 dans `DETTE.md`. Vue C# (+ lancement du serveur dans `core/SimBridge.cs`). Golden intact.

## Objectif
1. **Nominal** (60 s par semaine) : plus aucun à-coup visible — le « 3 FPS alors qu'une image
   coûte 57 ms » des rapports de Nico doit être expliqué par le banc ① puis éliminé. Suspects
   à départager **par mesure** : application de la semaine (`WorldView.Etalement.cs`, budget par
   image), parsing du snapshot sur le fil principal, cuisson `BakeQueue`, GC .NET.
2. **Mode test « au plus vite »** : en accéléré, la semaine suivante part dès que la précédente
   est **appliquée** (pas seulement reçue) ; le serveur Python tourne à **priorité réduite** pour
   ne pas affamer l'affichage sur 2 cœurs (`SimBridge` lance via `System.Diagnostics.Process` :
   la priorité se règle après `Start()` ; vérifier le comportement Windows ET Linux — baisser une
   priorité ne demande pas de droits). Critère : **aucune image > 100 ms**, cadence maximale
   compatible. Partir de l'existant : `SimMode.Turbo` (touche M, `spw = 0` dans
   `world/WorldView.cs`) et `DebugSecondsPerWeek` (aujourd'hui `1f` par défaut — **ne pas changer
   ce défaut** sans le dire : c'est le confort de test de Nico ; le banc pose sa cadence lui-même).
3. **D109** :
   - (a) `AllelopathieLayer` créée en `ZIndex = 0` (`world/WorldView.cs`) → passer au-dessus du
     sol comme `CouvertureLayer` (corrigé en ZIndex 1 au D106 T5) ; vérifier sur capture après
     rotation de vue ;
   - (b) absorbé par ② (vérifier seulement) ;
   - (c) poses de vent atteignables : seulement si le banc ① montre la mémoire ou la cuisson
     comme poste significatif ;
   - (d) regroupement des plantes cuites : **minimum** — seulement si, après ②③, les plantes
     restent le poste qui empêche 60 FPS à ×4 au banc ; sinon le noter et laisser au sprint
     plante assemblée.
4. Vent et animations des plantes à **vitesse normale** à 60 s par semaine (critère Nico) : rien
   ne doit être ralenti pour gagner des FPS.

## Mesure (banc ①)
Nominal : p99 du temps d'image et nombre d'images > 33 ms sur la fenêtre de mesure. Accéléré :
cadence obtenue (s par semaine) et max du temps d'image. Avant/après pour chaque correctif.

## Ne pas faire
Ne pas modifier le moteur Python ni le protocole (sauf la priorité du processus, côté C#).
Ne pas toucher au rendu des plantes au-delà du minimum D109 (d). Pas de `test_epaisseur_500ans`.

## Fin de tronçon
`00_etat.md` (à-coups expliqués + chiffres), `DETTE.md` D109 mise à jour (points traités /
reportés), commit.
