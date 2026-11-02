## 2026-11-02 — Sprint AUTOMNE VISIBLE (D123 + D118 (A) arbres) — CLOS côté code (①→⑥)

Ouvert au F5 de CALENDRIER UNIQUE (Nico : la chute des feuilles est invisible, ni sur les
arbres ni au sol). État, bilans et protocole F5 : `sprints/rendu/ambiance/sprint_automne_visible/00_etat.md`.

- ① fiches des 11 arbres (`docs/vegetal/croissance/fiches_arbres.md`) + banc `bancs/mesure_arbres.py`.
  Cause de l'effondrement de hauteur : le filet `_elaguer` coupait la flèche au plafond de segments.
- ② flèche protégée (filet + `axe_porteur`), bourgeon réveillé sous la coupe, ports réglés d'après les
  fiches, fondateurs à 11 ans, bouleau + cerisier + charme de démo. Golden re-figé annoncé
  `bfe6f889…` → `82d522c8…`.
- ③ largage sous toute la couronne, sur 4 semaines, masse selon la surface (`FEUILLE_PAR_PLOT` = 0,30).
  Pont 0.6.3 : 9ᵉ champ de `litiere` + `feuillage`. Golden re-figé annoncé → `ac48b170…`.
- ④ vue : tons d'automne par espèce, couronne éclaircie, recettes des 11 arbres.
- ⑤ vue : tapis lisible dès ×1, calque `LeafFallLayer` en lot, vent réel.
- ⑥ vue : lisière 4 saisons pied par pied dans le shader, table `SignesLisiere`, protocole F5.
- Passe `/refactor` : `plants/perennials.py` (419 LDC) → paquet `plants/perennials/`, golden inchangé.

Limites ouvertes, consignées dans D123 : population −19 % en an 2 [n=1 graine, VM], cause non isolée ;
cerisier à vitalité 0,73 après 3 ans [n=1 run, VM] ; bouleau sans tapis en s36, couvert en s37
[n=1 run, VM], car `semaine_abscission` n'a pas de composante par espèce ; chute et tapis hors palette
indexée ; mortalité de `foret_ports` signalée au ④, non reproduite à l'orchestrateur, non tranchée.

Attend le **F5 de Nico** (protocole « une année », `00_etat.md` §F5).
