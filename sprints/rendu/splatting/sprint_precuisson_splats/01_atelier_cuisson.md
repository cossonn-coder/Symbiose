# ① Atelier de cuisson + preuve de faisabilité (PORTE DE DÉCISION)

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (§3 surtout)
et `docs/rendu/splatting/prototype/README.md` (+ `tomate.js`, scène qui marche).

## Existant (vérifié 2026-11-20)
- Prototype : `docs/rendu/splatting/prototype/tomate.js` rendu par
  `node <ink>/cli/ink-studio.js render tomate.js --colored --out x.png` (Node 20 sur
  la VM). ink-studio testé au commit `fb94031` (2026-11-20).
- Commandes ink-studio utiles (lues dans son README) : `passes <scene>` (couverture,
  profondeur, **normales**, IDs, `--px1` = pixels d'art natifs), `atlas <scene>
  --directions N --pitches … --w --h --maps depth,normal,silhouette`, `stats`.
  API Node : `require(<ink>).load()` → `{ makeBuilder, makeSculpt, KIT }`,
  `render(world, { passes })`.
- Format cible = palette indexée de la vue : `visuals/PaletteIndexee.cs:12-25`
  (ton 0-4, orientation 0-7 par 45° en repère ÉCRAN, 0 = droite, 2 = bas, 6 =
  haut, 8 = plat). Les pièces du kit actuel portent leur code dans le canal G
  (`visuals/PlantRenderer.Kit.cs` en-tête, `PlantRenderer.KitCodes.cs`) et
  l'assemblage les pose avec `modulate` = n° de palette
  (`PlantRenderer.Assemblee.cs` en-tête). **Relire ces trois fichiers et produire
  les pièces dans le format que l'assemblage sait DÉJÀ lire** (ne pas inventer un
  second format).

## Objectif
1. **Copier ink-studio** au commit `fb94031` dans `tools/splat/vendor/ink/` (sans
   `.git`, avec sa LICENSE MIT), plus une ligne de provenance (URL + commit + date)
   dans `tools/splat/README.md`. ~15 Mo : mesurer et noter.
2. **Outil de cuisson** `tools/splat/` (JavaScript, Node ≥ 18, sans dépendance npm
   autre que la copie d'ink-studio) : une recette = un module JS qui sculpte UNE
   pièce (organe) ; l'outil la cuit sous V vues (lacet × inclinaison) et à chaque
   palier ×0,5 ×1 ×2 ×4 ×8 ×16 ×32, en pixels natifs, et écrit :
   - par pixel : **orientation** (normale visible projetée en repère écran,
     quantifiée 45°, ou 8 si quasi face caméra / plate — choisir le seuil, le
     dire) et **ton** (volume HORS soleil : occlusion, creux, revers ; jamais
     d'ombre portée solaire — le shader de la vue s'en charge) ; alpha posé/vide ;
   - les pièces rangées en **planche** PNG + **manifeste JSON** (recette, palier,
     vue, variante, rectangle, point d'attache = où l'organe tient à sa tige).
   - Taille d'une pièce par palier : dérivée de la taille réelle de l'organe (cm)
     et de l'échelle de la vue à ce palier — **lire l'échelle réelle dans le code
     de projection** (`world/WorldView.Projection.cs`, calibrage 78×39 px/plot de
     50 cm à ×1 selon CLAUDE.md : vérifier) ; jamais de mise à l'échelle d'une
     image.
3. **Une seule recette** pour ce tronçon : la **feuille composée** (tomate),
   reprise du prototype (`tomate.js`, fonction `feuille`).
4. **Déterminisme** : deux cuissons = octets identiques (le vérifier : `sha256`).
5. **Planche de contrôle** lisible par un humain : chaque pièce recolorée par une
   rampe de 5 tons et éclairée par un soleil fixe (simulation du shader), côte à
   côte avec la pièce actuelle de la vue au même palier si on peut l'obtenir
   (sinon le dire).

## Mesures à rendre (dans `00_etat.md`)
- Temps de cuisson d'une pièce et de la planche entière [n, VM].
- Poids PNG de la planche.
- Nombre de vues V retenu et pourquoi (la plus petite valeur sans « saut » visible
  quand l'organe tourne).
- **Verdict de lisibilité à ×0,5 / ×1 / ×2 (3-9 px)** : regarder les PNG (outil
  Read) et juger honnêtement.

## Porte de décision
Si la pièce réduite n'est **pas lisible** aux paliers bas, OU si l'orientation /
le ton ne peuvent pas être extraits proprement d'ink-studio : **s'arrêter**,
consigner le constat et les essais dans `00_etat.md`, **ne pas lancer ②**. Pas de
contournement silencieux (ex. retomber sur le kit pixel sans le dire).

## Golden
**INTACT** (aucun fichier de `data/code/` touché). Le lancer quand même une fois
(`python3 -m tests.test_golden` depuis `data/code/`) pour le consigner.

## Ne PAS faire
- Toucher au C# (c'est ④⑤⑦), modifier les sources d'ink-studio copiées (si une
  limite d'ink-studio bloque, la noter), écrire d'autres recettes, appeler
  DeepSeek, lancer `test_epaisseur_500ans`.
