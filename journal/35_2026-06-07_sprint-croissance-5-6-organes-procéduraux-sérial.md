## 2026-06-07 — Sprint Croissance·5 + ·6 : organes procéduraux + sérialisation — sprint CLOS (Python)

Les deux derniers tronçons du sprint Croissance procédurale, le même jour que la
clôture du sprint maison.

**Tronçon 5 — organes procéduraux (le risque n°1). Décision : prototype Python SVG
d'abord, port Godot différé** (choix Nico ; l'affinage esthétique se fera mieux
dans le moteur de rendu → D24/D33). Générateur dans `tools/render_structure.py`
(`_draw_organs`) : **feuilles** le long des rameaux feuillés (`_is_leafy` : apex ou
bois fin ≤1,6 cm, tronc nu), **couleur saisonnière** (printemps clair / été plein /
automne jaune-rouge tiré au hash / hiver), **fleurs/fruits** selon `organ_site`
(terminal/latéral) × `REPRO_BY_SEASON`, plafonnés (`MAX_FRUITS`=10), palette par
espèce. **Pur rendu read-only, déterministe** (zéro RNG, tout `_hash_noise`),
structuré « specs 3D → projection iso » pour le portage Godot futur. Couvre les
2 espèces procédurales (Tomato, AppleTree). **Golden + suite INTACTS** (`16a1b937…`).
→ Surfacé **D33** : la couleur ne varie que par saison ; elle devrait porter le
**diagnostic physiologique** (hydratation, chlorose, étiolement, sénescence,
ravageurs, maladies) — canal d'apprentissage central (philo #5), à concevoir.

**Tronçon 6 — sérialisation de la structure. Décision : contrat borné** (le save
GLOBAL n'existe pas encore → on livre le **round-trip** prêt pour lui ; choix
Nico). `Segment.to_dict()/from_dict()` + `PlantInstance.structure_to_dict()/
restore_structure()` (invalide le cache d'empreinte). **Allègement §J par
construction** : les organes ne sont **jamais stockés** (régénérés par le rendu) —
seul le bois est sérialisé. Pures additions → **golden INTACT**. `test_croissance`
**67/67** (dont : structure restaurée pousse **à l'identique** sur 40 ticks).

**Statut.** Sprint Croissance procédurale **CLOS côté Python** (tronçons 1-6).
Reste hors sprint : save global transversal, rendu pixel Godot des organes,
portage C# (D24), profil du reste du catalogue, déclencheurs naturels du seam,
marqueur `🌿`.

---
