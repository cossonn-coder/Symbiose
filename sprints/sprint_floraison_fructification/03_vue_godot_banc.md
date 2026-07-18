# ③ Vue Godot + banc F5 — floraison → pollinisation → nouaison → fruit

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_FLORAISON_FRUCTIFICATION.md` §5. Prérequis : ① et ②
> FAITS. **Règle projet** : la vue Godot est TOUJOURS le dernier tronçon d'un
> sprint. Le F5 visuel reste à Nico ; sur la VM = filet `dotnet build
> Symbiose.csproj` (voir `reference_godot`).

## Objectif
Rendre la floraison retypée **observable** et confirmer visuellement que D84/D86
sont corrigés : chaque espèce fleurit dans sa saison, la floraison dure (plus de
flash), le pommier fructifie. **Le gros du travail de rendu est DÉJÀ fait** par le
sprint DÉSYNC PHÉNOLOGIE — ce tronçon est surtout **vérification + banc + éventuel
ajustement de palette**.

## État existant (à NE PAS refaire)
- **Pont** : `tools/simserver/serialize.py` exporte déjà `base["floraison"]`
  (`round(p.floraison,3)`, hors `_PLANT_ATTRS`) — désync ②. Rien à ajouter si le
  scalaire suffit.
- **Vue** : `visuals/PlantRenderer.Organs.cs` dessine déjà les fleurs sur
  `_structure.Floraison >= FloraisonSeuil (0.5)` (désync ③) — plus de proxy
  saisonnier. `core/PlantStructure.cs` lit déjà `Floraison` du snapshot.
→ Le cycle est **déjà branché de bout en bout**. Vérifie que c'est le cas après ①
(le scalaire `floraison` a la même sémantique, seule sa *dynamique temporelle* a
changé) ; aucune modif de câblage attendue.

## Travail réel de ce tronçon
1. **Palettes de fleur** (`visuals/PlantRenderer.Organs.cs`, dict `OrganPalette`
   ~lignes 108-131) : vérifie que les espèces dont la saison de floraison a bougé
   (pommier au printemps, espèces d'automne, etc.) ont une **couleur de fleur**
   correcte et lisible. Ajuste seulement si une fleur manque ou détonne. Ne
   change pas la structure du dict.
2. **Silhouette de fleur** par famille (`PlantRenderer.Flower.cs`,
   `DrawFlowerShape`) : vérifie cohérence (rien à réécrire a priori).
3. **Banc F5 d'observation** : fournis à Nico une carte/scène de démo où l'on voit
   sur une année : un **pommier mûr** (âge ≥ 5) qui fleurit au printemps puis
   fructifie, une **espèce estivale** et une **automnale** qui fleurissent à leur
   saison, des **butineurs** qui pollinisent. Réutilise l'infra de bancs existante
   (`data/code/bancs/`, `tools/sim_server.py` + `SimBridge`, option F5). Si un banc
   proche existe déjà, étends-le plutôt que d'en créer un. Documente à Nico le
   **mode d'emploi F5** (quelle scène lancer, ce qu'il doit observer, à quelles
   semaines).

## Vérifications F5 (à faire par Nico, liste-les-lui)
- Le pommier fleurit au **printemps** (plus « début automne »).
- Les fleurs **durent** plusieurs semaines (plus de flash à S33-34).
- Les espèces estivales/automnales fleurissent à **leur** saison, étalées entre
  pieds (gène-tempo).
- Le pommier **noue plusieurs fruits** quand des butineurs passent (plus « une
  seule pomme »).
- Un pied **à l'ombre** de la maison fleurit **plus tard** (accumulation plus
  lente) — interconnexion.

## Golden & build
- **Golden INTACT** attendu (tronçon de vue). Lance `python3 -m tests.test_golden`
  pour confirmer que rien n'a bougé côté Python.
- **`dotnet build Symbiose.csproj`** doit rester vert (filet de compilation VM).
- **NE LANCE JAMAIS** `test_epaisseur_500ans`.

## Ce qu'il NE faut PAS faire
- Ne re-câble pas le pont/rendu déjà en place (désync ②③).
- Pas de GDScript (C# uniquement).
- Ne touche pas au moteur figé en ①/②.

## En finissant
Mets à jour `00_etat.md` (③ fait, sprint CLOS, points F5 à valider par Nico),
mets à jour `DETTE.md` (D84 + D86 → résolus, préciser le reste F5) et `journal.md`
(nouvelle entrée). Commit (fichiers nommés, `Co-Authored-By: Claude Opus 4.8
<noreply@anthropic.com>`). Le refactor auto-léger de fin de `/sprint-auto`
s'occupe des dépassements de taille éventuels.
