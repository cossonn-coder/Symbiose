# SPRINT SÉMIOLOGIE VISUELLE — état partagé

> ## 🏁 SPRINT SÉMIOLOGIE VISUELLE — CLOS (2026-06-24)
> T1 `ombre` (`a07702c`), T2 `maladie` (`213c97b`), T3 palette + diagnostic
> C2/C3 — tous couche B pure C#, golden INCHANGÉ `2ab026ad…`, build vert.
> **Dette 0.5.2 levée** (mapping `ombre`, T1) + **D48 levée**. D47 : C2/C3
> instrumentés (mémo ci-dessous), reste à exécuter le protocole au F5 (Nico).

> **Kickoff autosuffisant** (démarrage à froid). Lire CE fichier + le `0N_*.md`
> du tronçon courant suffit à reprendre sans contexte préalable.
>
> Conception FIGÉE (source de vérité) : `docs/narration/semiologie/conception_semiologie_visuelle.md`
> (figée le 2026-06-24, tronçonnage §8). Suivi dette : **D48**.
> Modèle moteur sous-jacent (NON retouché ici) :
> `docs/narration/semiologie/conception_semiologie_foliaire.md` (D33, clos).

## En une phrase

Compléter et unifier la **traduction en pixels** des signes de souffrance/réponse
émis par le moteur. Couche **B pure** (`visuals/PlantRenderer.*`, C#) — le **modèle
moteur** (détecteurs, champ `leaf_symptoms`, intensités) est déjà figé par D33 et
**n'est PAS touché**. On consomme `leaf_symptoms` (déjà au snapshot), on le rend mieux.

## Invariants ABSOLUS (toute la durée du sprint)

1. **Golden trivialement préservé.** Aucun fichier Python touché. Vérifier après
   chaque tronçon : `cd data/code && python3 -m tests.test_golden` reste vert,
   hash **`2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`**
   INCHANGÉ. Si le hash bouge → on a touché le moteur par erreur, on revient.
2. **Build C# vert.** Filet de compilation = `dotnet build Symbiose.csproj`
   (SDK 8.0 sur la VM, `~/.dotnet`) → **0 erreur, 0 warning** après chaque tronçon.
3. **F5 visuel = Nico** (Godot pas sur la VM). L'orchestrateur code + compile ;
   la validation à l'écran reste à Nico. Décrire à chaque clôture CE QUE Nico
   doit voir (banc d'essai à exhiber + verdict attendu).
4. **GDScript INTERDIT, tout en C#, namespace `Symbiose`.** Pas de bump
   `ENGINE_VERSION` (pont 0.5.6 inchangé : `ombre` et `maladie` sont DÉJÀ dans
   `leaf_symptoms` côté moteur, on ne fait que mieux les peindre).
5. **Déterminisme** : toute texture posée au **hash** (`Hash01(salt, i, j)`),
   jamais de `Random` — stable inter-frames (philo #3).

## Tronçons

| Tr | Contenu | § conception | Couche | Statut |
|----|---------|--------------|--------|--------|
| **T1** | `ombre` — teinte `b8c8a0` (`ColorantTints`) + canal texture `_ombre` (limbe chétif : calotte éclairée réduite, plancher­née) — **lève dette 0.5.2** | §2 | B pure | ✅ |
| **T2** | `maladie` — canal texture `_maladie` (semis de taches par hash) distinct de l'asphyxie uniforme | §3 | B pure | ✅ |
| **T3** | Cohérence palette SS² (hue-shift froid × symptômes jaunes) + diagnostic F5 C2/C3 | §5, §6 | B pure | ✅ |

(L'affaissement sécheresse est DÉJÀ fait — `Organs.cs` `lz -= _drought * DroughtDroopCm`,
cf. §4 — pas de tronçon.)

## Fichiers concernés (couche B, tous en C#)

- `visuals/PlantRenderer.cs` — `ColorantTints` (dict teintes), `SetSymptoms`
  (ingestion `leaf_symptoms` → canaux couleur/texture), `SymptomTint`,
  champs `_ravageurs/_gel/_grele/_drought`.
- `visuals/PlantRenderer.Organs.cs` — boucle de placement des feuilles,
  `DrawLeafShape(...)`, `DrawLeafDamage(...)` (criblage + bords gelés).
- `visuals/PlantRenderer.Leaf.cs` — `DrawShapeBySpecies`, nervures.
- `visuals/PlantRenderer.Palette.cs` — `DrawVolumeEllipse` (calotte éclairée =
  `rx*0.66, ry*0.66` décalée sud) = le levier du « limbe chétif » T1.

## Boucle projet (rappel)

`0N` → coder (C#) → `dotnet build` vert + golden inchangé → MAJ ce fichier
(passer le tronçon ✅ + §REPRISE) → commit → `/clear` → `0N+1`.

## §REPRISE

### T1 — signe `ombre` / étiolement ✅ (lève dette 0.5.2)

- **Canal COULEUR** : entrée `ColorantTints["ombre"] = b8c8a0` (vert pâle délavé)
  ajoutée dans `visuals/PlantRenderer.cs`. Entre automatiquement dans la
  compétition « colorant dominant » de `SetSymptoms` — aucune autre logique.
- **Canal TEXTURE** : champ `_ombre` ajouté (à côté de `_ravageurs/_gel/_grele/
  _drought`), remis à 0 dans `SetSymptoms`, alimenté par `case "ombre"`.
- **Limbe chétif** : `DrawVolumeEllipse` (`PlantRenderer.Palette.cs`) lit
  désormais la taille de calotte dans un **champ-toggle `_litFactor`** (défaut
  `LitFactorDefault = 0.66`). **Option (a) retenue** (toggle, pas surcharge
  `litScale`) : `DrawVolumeEllipse` est appelée par les 6 archétypes de feuille
  (`Leaf.cs`) ; propager un paramètre à travers tous serait illisible. Le toggle
  est posé à l'entrée de la boucle feuilles (`Organs.cs`) à
  `Mathf.Lerp(0.66, 0.30, _ombre)` puis **remis à 0.66 après la boucle** →
  fruits/fleurs (`DrawVolumeCircle`, calotte propre codée en dur) intacts.
- **Plancher E4** : `LitFactorFloor = 0.30` → calotte jamais nulle, jamais
  d'aplat même à `_ombre = 1` (à ajuster au F5).
- **Golden** : INCHANGÉ, hash `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` (aucun Python touché).
- **`dotnet build Symbiose.csproj`** : VERT — 0 erreur, 0 warning.
- **Fichiers touchés** : `visuals/PlantRenderer.cs`, `PlantRenderer.Palette.cs`,
  `PlantRenderer.Organs.cs`.
- **Verdict F5 attendu (Nico)** : exhiber le banc **`ombre_dense`** (Godot pas
  sur la VM, lancement via le sélecteur). Une plante héliophile sous couvert
  dense doit montrer un feuillage **délavé `b8c8a0`** + des feuilles à **calotte
  lumineuse réduite** (aspect chétif), SANS aplat (plancher tient). Comparer à un
  témoin éclairé. ⚠️ Risque palette à confirmer en T3 (§5) : côté nord le
  hue-shift froid peut rapprocher `b8c8a0` du bleu.

### T2 — signe `maladie` / taches cryptogamiques ✅

- **Canal COULEUR inchangé** : `ColorantTints["maladie"] = 8a6a4a` (brun) RESTE —
  les deux canaux coexistent (D33), la teinte n'est PAS retirée.
- **Canal TEXTURE** : champ `_maladie` ajouté à côté de `_ombre` dans
  `visuals/PlantRenderer.cs`, remis à 0 dans `SetSymptoms`, alimenté par
  `case "maladie": _maladie = it; break;`.
- **Semis de taches** (`DrawLeafDamage`, `PlantRenderer.Organs.cs`) : si
  `_maladie > 0`, `Mathf.CeilToInt(_maladie * 5f)` taches (1 à 5), posées au
  **hash salt NEUF 37/41** (≠ criblage 23/29 → pas de superposition exacte),
  rayon `r * 0.12f` (vs criblage `r * 0.22f` → pustules ponctuées plus petites),
  couleur dédiée `LeafSpotColor = 4a3320` (brun foncé). Additif, indépendant du
  criblage/bords gelés.
- **Golden** : INCHANGÉ, hash `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` (aucun Python touché).
- **`dotnet build Symbiose.csproj`** : VERT — 0 erreur, 0 warning.
- **Fichiers touchés** : `visuals/PlantRenderer.cs`, `visuals/PlantRenderer.Organs.cs`.
- **Verdict F5 attendu (Nico)** : sur une plante malade, le limbe brun doit
  désormais porter un **semis de petites taches sombres ponctuées**, visuellement
  DISTINCT du brun-vert UNIFORME de l'asphyxie (qui reste un aplat — vérifier
  qu'elle n'a PAS régressé). Exhiber un banc avec pathogène si disponible.

### T3 — cohérence palette SS² + diagnostic C2/C3 ✅ (CLÔT le sprint)

- **(A) Repli palette §5** : l'amplitude du hue-shift **FROID** (lum<0, vers le
  bleu) est multipliée par un facteur `_coolShiftScale` lu dans `HueShift`
  (`PlantRenderer.Palette.cs`, méthode rendue **instance**). Seule la dérive de
  TEINTE est bornée — VALEUR (clarté) et SATURATION inchangées (le volume reste
  lisible). `_coolShiftScale = Mathf.Lerp(1f, ColorCoolShiftFloor, _colorAmount)`
  avec **K = `ColorCoolShiftFloor` = 0.5** (retenu, à régler au F5). Posé comme
  TOGGLE à l'entrée de la boucle feuilles (`Organs.cs`, à côté de `_litFactor`),
  **remis à 1 juste après** → branches, fruits, fleurs, silhouette gardent le
  froid PLEIN. **Tissu SAIN** (`_colorAmount = 0` → `_coolShiftScale = 1`) =
  hue-shift SS² PLEIN, **zéro régression** (invariant vérifié par relecture).
- **(B) Chaleur `ombre`** : teinte délavée relevée **`b8c8a0` → `c2c8a0`**
  (`ColorantTints["ombre"]`, `PlantRenderer.cs`) — un poil plus chaude pour
  rester DISTINCTE du froid du hue-shift côté nord (risque noté en T1).
- **Golden** : INCHANGÉ `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
  (aucun Python touché). **`dotnet build`** : VERT — 0 erreur, 0 warning.
- **Fichiers touchés** : `visuals/PlantRenderer.Palette.cs` (`HueShift` instance
  + atténuation froid + champ/const `_coolShiftScale`/`ColorCoolShiftFloor`),
  `visuals/PlantRenderer.Organs.cs` (toggle posé/remis), `visuals/PlantRenderer.cs`
  (teinte `ombre`).
- **Verdict F5 attendu (Nico)** : parcourir `ombre_dense`, `asphyxie_argile`,
  `infestation_ravageur`. Côté NORD, chaque symptôme reste lisible (un jaune
  chlorose/sénescence ne reverdit/bleuit plus jusqu'à l'illisible) ; le délavé
  `ombre` `c2c8a0` se distingue d'une simple ombre de volume ; une plante SAINE
  est inchangée vs SS² (même volume, même froid de profondeur). Régler K si le
  froid est encore trop fort (baisser) ou si le volume s'aplatit (remonter).

### §Mémo de protocole de diagnostic F5 — C2/C3 (T3, instrumente D47)

But : trancher un **suspect rendu C#** (oracle moteur vert ↔ écran muet ⇒ bug
de mapping `PlantRenderer`). Chaque banc a un oracle Python qui asserte le signe
au plot/semaine (source `sim/semiologie.py`, le MÊME endroit que la vue lit).
**Aucune mécanique à coder ici** — c'est une grille d'observation pour le F5.

| Cas | Cause moteur | Banc d'essai | Attendu écran | Verdict |
|-----|--------------|--------------|----------------|---------|
| **C2** asphyxie | `asphyxie_memory > 0.10` (intégration lente 0.05/sem) → `leaf_symptoms` cause `asphyxie`, intensité en rampe ; canal COULEUR `ColorantTints["asphyxie"]=6e6a4a` (brun-vert), APLAT uniforme (pas de texture). | `asphyxie_argile` (sol argileux gorgé, plusieurs sem d'excès d'eau soutenu). | Le limbe vire **brun-vert terne `6e6a4a` proportionnellement** à l'intensité (faible = à peine teinté, fort = bien brun) — **gradué, pas binaire**. Reste UN APLAT (≠ taches de `maladie`). | **OK** si la teinte se lit ET module avec l'intensité. **BUG rendu** si muet malgré l'oracle vert (→ vérifier `SetSymptoms`/`SymptomTint`, dette ciblée). |
| **C3** ravageurs | densité ravageur > ~0.025 (floor TRÈS bas) → cause `ravageurs`, canal TEXTURE `_ravageurs` → criblage (`DrawLeafDamage`, 1-4 trous sombres ∝ intensité). | `infestation_ravageur` **vs un TÉMOIN sain** (même espèce, sans pression). | L'infesté porte un **criblage VISIBLEMENT plus dense** que le témoin. Le témoin doit être **propre** (pas de trous). | **OK** (criblage sincère) si témoin propre + infesté criblé. **BUG rendu** (criblage FANTÔME) si le TÉMOIN montre AUSSI des trous → distinguer du rendu normal des feuilles (nervures/points), dette ciblée. |

Note : `ombre` (le 3ᵉ suspect D47) est LEVÉ depuis T1 (mapping couleur `c2c8a0`
+ texture limbe chétif) — il n'a plus besoin de protocole, juste de la
confirmation `ombre_dense` du verdict F5 ci-dessus.
