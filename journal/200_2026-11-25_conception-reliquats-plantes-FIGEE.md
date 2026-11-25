## 2026-11-25 — Conception RELIQUATS DES PLANTES (S1 du style homogène) FIGÉE

`/conception` sur `docs/rendu/splatting/backlog_splatting.md`, suite du sprint (a) plantes.
Doc : `docs/rendu/splatting/conception_reliquats_plantes.md`. Sprint :
`sprints/rendu/splatting/sprint_reliquats_plantes/` (6 tronçons, golden `bce813af…` intact).

**Constat vérifié :** à ×32, les grandes plantes perdent leurs splats. Capture VM (n=1 par
cas) : la tomate garde ses pièces ; le tournesol n'en a aucune, parce que `PlantBaker`
refuse de cuire au-delà de 2048 px par pose. La plante passe alors en dessin direct, et les
codes de palette n'y sont pas lus.

**Décision :** trois sprints en séquence, sans F5 intermédiaire :
- S1, reliquats des plantes ;
- S2, arbres : rendu seul, tube lissé sans angles abrupts, écorce cuite, brins de graminées ;
- S3, lisière (b), puis écran de chargement (g) : un mycélium qui s'arborise en splats et
  sert de barre de progression.

**Décision :** précuisson maximale, avec un budget mémoire de 1 Go. Pour ×32, on relève les
plafonds de cuisson sous ce budget. On cuit 3 classes de taille par recette. Tous les
détails des feuilles seront cuits en couches, chacun visible dès le palier où il se lit.

**Décision :** pas de palier ×64 pour l'instant. Une sonde est prévue au ③ de S1, puis un
proof of concept sur un chanvre entier après S3. Il faudrait aussi recuire par palier le
sol, la faune et le paillage.
