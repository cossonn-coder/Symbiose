# T1 — Signe `ombre` / étiolement (lève dette 0.5.2)

> Lire d'abord `00_etat.md` (invariants) + `docs/narration/semiologie/conception_semiologie_visuelle.md` §2.
> Couche **B pure** (C#). Golden trivialement préservé, build C# vert, F5 = Nico.

## But

Le moteur émet déjà le signe `ombre` dans `leaf_symptoms` (cf. `sim/semiologie.py`,
7 chroniques dont `ombre`), mais la **vue ne le peint pas** : `ColorantTints` n'a
pas d'entrée `ombre`, et `SetSymptoms` ne capte aucun canal texture pour lui.
C'est le trou **dette 0.5.2**. On le comble par DEUX canaux (modèle D33 : couleur
dominante + textures additives).

## Biologie (le pourquoi, pour le rendu)

À l'ombre, la plante s'**étiole** : feuilles **pâles et anémiées** (moins de
chlorophylle), limbe aminci. La morpho étirée (entre-nœuds longs) est couche A
Python → **HORS scope** ici (déjà partiellement émergente via le phototropisme moteur).

## Travail

### A. Canal COULEUR — entrée `ColorantTints["ombre"]`

Dans `visuals/PlantRenderer.cs`, dict `ColorantTints` (~ligne 66), ajouter :

```csharp
["ombre"] = new Color("b8c8a0"), // vert pâle délavé désaturé (étiolement)
```

Rien d'autre à faire pour la couleur : `SetSymptoms` choisit DÉJÀ le colorant
dominant (plus forte intensité) par balayage du dict — `ombre` entre dans la
compétition automatiquement. Sur une plante seulement ombragée, le délavé révèle
l'étiolement ; une chlorose plus intense le masque (canal couleur = 1 dominant,
pas de mélange boueux — invariant D33).

### B. Canal TEXTURE — « limbe chétif » (calotte éclairée réduite)

Nouveau canal additif `_ombre`, lu par les feuilles, qui **réduit le rayon de la
calotte éclairée** du volume de la feuille ∝ intensité (render-only, AUCUNE
géométrie moteur touchée — la feuille paraît amincie/affaiblie).

1. Dans `PlantRenderer.cs`, déclarer le champ à côté de `_ravageurs, _gel, _grele, _drought` :
   ```csharp
   private float _ravageurs, _gel, _grele, _drought, _ombre;
   ```
   Le remettre à 0 dans `SetSymptoms` (ligne `_ravageurs = _gel = _grele = _drought = 0f;`)
   et ajouter un `case` dans le `switch (cause)` :
   ```csharp
   case "ombre": _ombre = it; break;
   ```

2. **Levier de réduction de calotte** — `DrawVolumeEllipse` (`PlantRenderer.Palette.cs`
   ~ligne 104) dessine la masse pleine (ombre) puis une **calotte éclairée**
   `rx*0.66, ry*0.66` décalée vers le sud. Réduire ce facteur 0.66 ∝ `_ombre` :
   une feuille étiolée a une calotte lumineuse plus petite (limbe anémié).
   - ⚠️ **Décision de design à respecter** : `DrawVolumeEllipse` est PARTAGÉE
     (feuilles, fruits, fleurs — cohérence chromatique). `ombre` ne doit toucher
     que **les feuilles**. Deux options propres au choix de l'implémenteur :
     (a) un petit champ-toggle `_litFactor` (défaut 0.66) posé juste avant la
     boucle feuilles et remis à 0.66 après ; (b) une surcharge/variante
     `DrawVolumeEllipse(..., float litScale)` appelée uniquement par le chemin
     feuille. Préférer (b) si elle reste lisible ; documenter le choix en commentaire.
   - **Plancher E4** : la calotte ne disparaît JAMAIS. Borner le facteur réduit
     pour garder ≥ 2 valeurs (ombre + calotte) même à `_ombre = 1` — jamais
     d'aplat. Ex. `lit = Mathf.Lerp(0.66f, 0.30f, _ombre)` (plancher 0.30, à
     ajuster au F5).

## Vérifications

1. `dotnet build Symbiose.csproj` → **0 erreur, 0 warning**.
2. Golden inchangé (aucun Python touché) :
   `cd data/code && python3 -m tests.test_golden` → hash `2ab026ad…`.
3. Relecture : `ombre` n'affecte PAS les fruits/fleurs (calotte normale) — vérifier
   le chemin partagé n'a pas fui.

## Clôture (MAJ `00_etat.md`)

- Passer T1 ✅ dans la table.
- §REPRISE : entrée T1 = teinte ajoutée + champ `_ombre` + mécanisme calotte
  (option a/b retenue + plancher choisi), hash golden vérifié, `dotnet build` vert.
- **Verdict F5 attendu (à écrire pour Nico)** : exhiber le banc **`ombre_dense`**
  (`/sprint-auto` n'exécute pas Godot — Nico lance le banc via le sélecteur). Une
  plante héliophile sous couvert dense doit montrer un feuillage **délavé `b8c8a0`**
  + des feuilles à **calotte lumineuse réduite** (aspect chétif), SANS aplat
  (plancher tient). Comparer à un témoin éclairé. ⚠️ Risque palette à confirmer
  en T3 (§5) : côté nord le hue-shift froid peut rapprocher `b8c8a0` du bleu.
- Commit (ex. `feat(rendu) : T1 signe ombre — teinte b8c8a0 + limbe chétif, lève dette 0.5.2`).
