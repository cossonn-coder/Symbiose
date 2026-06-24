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
| **T1** | `ombre` — teinte `b8c8a0` (`ColorantTints`) + canal texture `_ombre` (limbe chétif : calotte éclairée réduite, plancher­née) — **lève dette 0.5.2** | §2 | B pure | ⬜ |
| **T2** | `maladie` — canal texture `_maladie` (semis de taches par hash) distinct de l'asphyxie uniforme | §3 | B pure | ⬜ |
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

(vide — sprint pas encore démarré. Chaque tronçon clos écrit ici : ce qui a été
fait, le hash golden vérifié, le résultat `dotnet build`, et le verdict F5 attendu.)
