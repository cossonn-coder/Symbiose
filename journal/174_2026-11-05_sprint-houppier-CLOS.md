# 2026-11-05 — Sprint HOUPPIER (D118) — CLOS côté code (①→⑤)

Golden `a10b7225…` intact sur les 5 tronçons. F5 de Nico attendu (`sprints/rendu/pixelart/sprint_houppier/00_etat.md`, §F5). Tous les chiffres et leurs limites : même fichier, bilans ① à ⑤.

## ⑤ Vue
- **Rameaux et brindilles dérivés dans la vue**, géométrie pure tirée de la clé stable, dans le rayon réel (`PlantRenderer.Rameaux.cs`).
- **Gerbes** de ×0,5 à ×4, à la place des touffes et des masses ovales ; hiver : bois seul (`PlantRenderer.Houppier.cs`).
- **×8 et plus** : limbes d'espèce, peints comme ceux des lianes.
- **Bois** : plus de segment vert entier, seul le bout reste tendre.
- **Fleurs et fruits sur les brindilles**, fruits à leur taille en cm, clic `manger` sur le même point que le dessin.

## Décisions de ⑤
- Limbes de ×8+ passés au peintre des lianes, écart au kickoff : l'ovale à motifs restait un pompon, même réduit.
- Gain de densité 1,6 [choix] : `DensiteVisible` règle aussi la lumière et laissait des brindilles nues en été.
- Masques de gerbes pour le dessin direct : le repli sur touffes montrait un arbre nu avant cuisson.

## À retenir
- Remplissage ×4, été : 25 → 54 % [charme, `houppiers`, n=1 capture, VM]. Plus dense, pas fermé.
- FPS en turbo : 5,5 → 4,1 sur `houppiers_25` ×1 [n=1 par côté, VM, llvmpipe, charges différentes]. À juger au PC.
- Cascade et relais des lianes non validés en capture.
