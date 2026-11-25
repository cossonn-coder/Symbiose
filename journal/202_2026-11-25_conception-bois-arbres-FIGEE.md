# 2026-11-25 — conception BOIS ET ARBRES (S2 du style homogène) FIGÉE

`/conception` avec Nico → `docs/rendu/splatting/conception_bois_arbres.md`, sprint
`sprints/rendu/splatting/sprint_bois_arbres/` (6 tronçons, golden `bce813af…` intact, rendu seul).

Constat en image (captures VM, n=1 par cas) : tronc en marches, branches en bâtons, branche
derrière le tronc peinte devant (tri par épaisseur), sapin sans cône EN JEU, racines plates.

Décisions de Nico : **B1** courbe interpolante par tous les nœuds + géométrie unique du bois
(rameaux, fruits, clic, sécateur, neige) ; **B2** écorce cuite en splats, 12 essences × 3 âges ;
**B3** cône du sapin par la vue (moteur intact). Décisions dans le cadre : tri par profondeur,
primitive « ruban texturé » partagée bois / graminées / lisière S3, orientation des flancs par la
géométrie et tons par l'écorce (mécanisme tranché par maquette), pied évasé et cols de branche,
fleurs ×4 en bouquets cuits. Vérifié au code : `parent` arrive dans la trame delta mais
`core/PontDelta.cs` le saute → lu côté C# au ①. Référence PC (rapport C) : ×32 FPS 23, précuisson
599/1024 Mo, 4 replis → le ① enrichit le rapport (qui est en repli, ms de cuisson).

Tronçons : ① axes et tube lissé · ② écorces · ③ rubans des graminées + petit bois · ④ arbres ×4 ·
⑤ sapin conique + portraits d'arbres · ⑥ revue et clôture.
