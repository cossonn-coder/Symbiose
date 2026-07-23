# 2026-07-23 — Sprint RETOURS UI/HUD post-fenêtrage — CLOS (`/sprint-auto`, T1→T3)

Sprint **pure vue C#/Godot** (avec un petit ajout de sérialisation au pont en
T3, jamais le moteur) : les 5 retours F5 de Nico consécutifs au sprint
fenêtrage, tranchés en Phase A (D1–D5) puis exécutés en 3 tronçons. **Golden
`57c166d8…` INCHANGÉ sur les 3 tronçons** (T1/T2 = zéro touche `data/code/` ;
T3 = champs snapshot hors `_PLANT_ATTRS`), `dotnet build` VERT partout, pont
`0.5.37 → 0.5.38`. Solde la dette **D89**.

## T1 — Palette de gestes gérable (`db53e68`)

Renverse le grisé actuel : **masquage** des gestes non débloqués + **modèle
SLOT** (D2). `WorldView.Palette.cs` réécrit autour d'un tableau `_slots[10]`
(index de geste ou −1), touches **1-9 puis 0**, **auto-remplissage** dans
l'ordre de `Gestes[]` parmi les débloqués, **débordement invisible** au-delà du
10ᵉ (pas de FIFO — le layout ne bouge pas seul). **Édition clic droit**
(`GesteIcon` capte le bouton droit → `PopupMenu` : assigner un débloqué absent /
vider le slot). **Persistance globale** par VERBE (robuste au réordonnancement
de `Gestes[]`) dans `user://palette.json` via nouveau `world/PaletteLayout.cs`.
`Tab` cycle les slots occupés. `CyclePalette` retiré de `WorldView.Actions.cs`.

## T2 — Chrome & navigation (`893e076`)

Trois retouches de chrome du même registre :
- **Légende clavier escamotable** (D3) : le `Label legend` provisoire
  (`WorldView.Hud.cs`) passe `Visible = false` par défaut, toggle **F1** →
  champ de jeu dégagé (premier geste concret de D54(a), sans le compléter).
- **Launcher pleine hauteur** (D5) : plafond `UiScroll.Envelopper` relevé
  360 → ~832 px (`1080 − marges − widgets`), défile toujours si débordement.
- **Retour accueil** (D4) : `Échap → GetTree().ReloadCurrentScene()` immédiat,
  sans confirmation, **seulement si `_started`**. Précédence : si le panneau de
  consultation est ouvert, Échap le **ferme d'abord** (VoicePanel vit dans
  `ConsultationPanel`, donc couvert), sinon → accueil (pont fermé proprement par
  `_ExitTree`, re-`_Ready` = pont neuf + `BuildSelecteur`).

## T3 — Dossier de plante au clic (`86b0f48`) — VUE + PONT

Fork **A tranché** (D1) : dossier **INSTANTANÉ** d'état, pas de log
chronologique moteur (aucun n'existe ; les **mémoires scalaires** SONT
l'histoire compressée). **Pont** (`serialize.py`, plante vivante) : ajout de
`memoires` (8 intégrateurs — noms vérifiés dans `plants/base/instance.py` :
shade/drought/asphyxie/cold/infection/wind/root_herbivory/stress_memory),
`expression` (facteurs ≠ 1.0, filtré), `age_weeks`/`age_years` — hors
`_PLANT_ATTRS` → **golden NEUTRE** (vérifié : hash identique). Pont
**0.5.38**. **Vue** : mode inspection debug touche **F2** → clic gauche =
« inspecter » (picking `FindPlant`), panneau read-only `DossierPlantePanel.cs`
(NEUF, 114 LDC) lisant le dict du **dernier snapshot** via un cache
`_plantPayloads` (`WorldView.Snapshot.cs`, clé `tile|species|x|y`, aucun appel
pont). Glue `WorldView.Dossier.cs` (NEUF). Fermable clic-ailleurs / Échap / F2,
inséré dans la précédence Échap (dossier → consultation → accueil).

## Livraison (Phase C)

- **D89 soldée** (✅ FAIT). **D80(d)** (débordement de palette) résolu autrement
  = cap 10 + masquage + édition, pas de grille multi-colonnes. **D54(a)**
  amorcée (légende hors champ), non complétée (HUD diégétique reste).
- **Refactor auto-léger : no-op** — tous les fichiers touchés 🟢 (max LDC pur =
  276, `world/WorldView.Hud.cs`).
- Intendance : les 3 scripts DeepSeek (`ask-deepseek`/`extract-chat`/
  `write-deepseek`) versionnés (`7b0a17e`, aucun secret en dur, clé lue de
  l'environnement) — ne flaguent plus en untracked.

**Reste F5 Nico** : (T1) palette masquée aux débloqués, touches 1..N, clic droit
assigne/vide un slot, layout conservé après retour accueil ; débordement >10
invisible jusqu'à assignation. (T2) F1 affiche/masque l'aide, launcher descend
jusqu'en bas et défile, Échap → accueil (Échap panneau ouvert → ferme le panneau
seul). (T3) F2 arme l'inspection, clic plante → panneau d'état physiologique ;
une plante stressée montre des mémoires élevées cohérentes ; Échap ferme le
dossier avant tout retour accueil.
