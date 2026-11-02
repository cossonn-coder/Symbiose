## 2026-11-02 — Retours F5 de la lisière (D125) — CLOS

Ouvert au F5 de LISIÈRE NUE. Fait hors sprint, trois petits correctifs. Golden intact `ac48b170…`.

- `649b5a2` brume : la trame `bayer` 4×4 posait tous les points sur une même grille ; hash, densité et ton abaissés.
- `649b5a2` zoom : la maille ×4 du décor sert aussi à ×8, ×16 et ×32, butineurs de bord compris.
- `0950823` puis `0a954af` neige : première version sur semaines sèches rejetée par Nico (« c'est par définition une pluie
  quand il fait froid »). Règle : une pluie sous `SEUIL_NEIGE_C` = 1,5 °C tombe en neige. 1,02 semaine de neige par an
  [30 graines × 5 ans, météo pure, VM].

Rejeu de 9 ans pour expliquer l'inondation du sud et les champignons de la mare, à la demande de Nico : détail en `DETTE_ARCHIVE.md`
et dans l'historique de D125 (`1c1a1dc`). Cause de la montée d'humidité non isolée.

**F5 de Nico, le 2026-11-02** : validé, D125 fermée. Reste versé en D126, dont la dominance du trèfle, à concevoir.
