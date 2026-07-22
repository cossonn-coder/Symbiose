# ③ Vue Godot — overlay F6 à la nouvelle échelle + banc d'observation

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Spec de
> référence : `docs/meta/calibrage/conception_calibration_realiste.md` (§7③).
> **Prérequis : tronçons ① et ② terminés** (échelle réalignée côté moteur).
> Dernier tronçon (règle permanente : la vue Godot clôt tout sprint). **Golden
> INTACT** (rendu/pont pur — rien dans `summary()` ni le tick).

## Objectif

Rendre la recalibration **visible et jugeable au F5** : (1) l'overlay F6 microbiome
lit enfin sa vraie plage (aujourd'hui `FixMax=3f` → tout paraît « inerte ») ; (2)
exposer la **métrique de vitalité du sol** en overlay F6 (elle n'est aujourd'hui
qu'un champ de `summary()`, jamais rendue) ; (3) un banc d'observation pour comparer
un coin de sol riche vs pauvre.

## Contexte technique (déjà repéré)

- `visuals/FieldOverlay.cs:59` : palette `microbiome` bornée `(0f, 3f)` — même
  mismatch d'échelle que le moteur. `MICROBE_EFFECT_REF = 0.6` (constante du ①).
- `eco.vitalite(r,c)` est une **méthode DÉRIVÉE**, pas un `GridField` → **absente du
  registre** `cmd_fields` (`tools/simserver/commands.py:242`), donc non demandable par
  l'overlay. Il faut la matérialiser en grille à la demande (VUE-only, golden intact).
- Le `p["vitalite"]` lu côté C# (`WorldView.Snapshot.cs`, `WorldView.Conteneurs.cs`)
  est `plant.vitalite` (santé plante → usure `PlantRenderer`) : **NE PAS y toucher**,
  ce n'est PAS la métrique sol.

## À faire

### A. Pont — exposer la vitalité sol en overlay (`tools/simserver/commands.py`)
Dans `cmd_fields` :
- **Registre (sans `field`)** : ajoute la clé synthétique `"vitalite"` à la liste
  retournée (`direct + populations + ["vitalite"]`), pour que le cycle d'overlay C#
  la propose.
- **Grille (avec `field == "vitalite"`)** : cas spécial — matérialise, par tuile, une
  grille `[eco.vitalite(r, c) for r, c ...]` (row-major, `round(v, 4)`), même forme de
  retour que les `GridField`. PURE lecture, aucun tick, aucun état stocké.
- Vérifie que le filet de compilation moteur passe (`python3 -m tests.test_golden`
  reste VERT — cmd_fields n'est pas dans le golden ; c'est une garantie, pas un
  re-figeage).

### B. C# `visuals/FieldOverlay.cs`
- Palette `microbiome` (l.59) : `FixMax` **`3f` → `0.6f`** (= `MICROBE_EFFECT_REF`).
  Le microbiome réel (~0.05–0.5) occupe alors la bande couleur au lieu d'être aplati
  à « inerte ». Garde les couleurs/libellés existants.
- Ajoute une entrée `"vitalite"` au dictionnaire `Palettes` : couleurs bas/haut
  distinctes (ex. bas `d8d2c0` parchemin « sol pauvre » → haut vert profond
  `2f6f3a` « sol vivant »), libellés `"pauvre"`/`"vivant"`, bornes fixes `0f, 0.8f`
  (la bande recalibrée ; ajuste après lecture du banc si besoin — commentaire
  pédagogique EXIGÉ expliquant la borne). Champ auto-découvert via la liste du
  registre (A).
- `dotnet build Symbiose.csproj` doit compiler (filet C# de la VM).

### C. Banc d'observation F5 (pour Nico)
Rédige, en fin de `00_etat.md`, la **checklist F5** : lancer le jeu, ouvrir le mode
technique F6, cycler jusqu'aux overlays `microbiome` puis `vitalite`, et vérifier
qu'un coin de sol riche (sous canopée jeune / amendé) se distingue NETTEMENT d'un
coin pauvre (le but du sprint : « le sol vivant se lit »). Pas de nouvelle scène si
la carte de démo existante suffit à montrer un contraste ; sinon, note ce qui
manque en dette (ne pas bloquer).

## Ce qu'il NE faut PAS faire
- Toucher `plant.vitalite` / `SetVitality` / `PlantRenderer` (santé plante, hors
  sujet).
- Modifier `summary()` ou quoi que ce soit du tick (golden doit rester INTACT).
- Re-caler les bornes d'un autre champ que microbiome/vitalite.

## Golden
**INTACT** aux deux niveaux : `python3 -m tests.test_golden` VERT (hash du ②
inchangé). Si le hash bouge, tu as touché le tick par erreur → annule.

## Fin de tronçon (clôture du sprint)
Mets à jour `00_etat.md` (§REPRISE = sprint CLOS, checklist F5, hash golden final du
②), commit (fichiers nommés : `tools/simserver/commands.py`, `visuals/FieldOverlay.cs`,
`00_etat.md`). Signale à Nico que le F5 lui revient (Godot pas sur la VM). Mets à jour
`DETTE.md` (D-cal : calibration MO/décompo des modulateurs de rythme, §6 du doc) et
`BACKLOG.md` (sprint calibration réaliste CLOS).
