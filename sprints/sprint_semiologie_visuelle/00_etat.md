# SPRINT SÉMIOLOGIE VISUELLE — état partagé

> **Kickoff autosuffisant** (démarrage à froid). Lire CE fichier + le `0N_*.md`
> du tronçon courant suffit à reprendre sans contexte préalable.
>
> Conception FIGÉE (source de vérité) : `docs/conception/CONCEPTION_SEMIOLOGIE_VISUELLE.md`
> (figée le 2026-06-24, tronçonnage §8). Suivi dette : **D48**.
> Modèle moteur sous-jacent (NON retouché ici) :
> `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (D33, clos).

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
| **T3** | Cohérence palette SS² (hue-shift froid × symptômes jaunes) + diagnostic F5 C2/C3 | §5, §6 | B pure | ⬜ |

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

### §REPRISE — PROCHAIN = T3

Lire `00_etat.md` (invariants + entrées T1/T2) + `03_palette.md`. T3 = cohérence
palette SS² (hue-shift froid × symptômes jaunes) + diagnostic F5 C2/C3. Couche B
pure C#, golden trivialement préservé (`2ab026ad…`), build C# vert exigé.
