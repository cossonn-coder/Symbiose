# T3 — Vent en onde : 8 poses de flexion par plante

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (mesures T2 !), `docs/rendu/pixelart/conception_jardin_vivant.md` §3-§4.

## Objectif
Le vent devient **visible et lisible** : un front d'onde traverse le jardin
dans le sens du vent et **appuie** sur les plantes, qui se couchent puis se
relèvent l'une après l'autre. Sans vent, rien ne bouge.

## Contexte vérifié
- `data/code/sim/wind.py` : `wind_at(seed, week) -> WindState(force, direction)`,
  PUR ; `force` ∈ [0,1+] (~0.3 brise, ~0.7 soutenu, >1 coup de vent) ;
  `direction` ∈ [0,2π) = **d'où vient** le vent. `gust_profile(seed, week)` =
  4 facteurs intra-journaliers.
- `fields/abri.py` → `eco.vent` = force LOCALE par plot (abri haie/maison,
  venturi), **LAZY** (`None` au repos, D99 — ne pas le forcer).
- Snapshot (`data/code/tools/simserver/serialize.py`) : bloc `weather` SANS
  vent (~l.626) ; plante : `wind_memory` (l.191). Version pont
  `ENGINE_VERSION = "0.5.43"` (`tools/simserver/version.py:669`).
- Golden (`tests/test_golden.py`) hache le log moteur, PAS le snapshot.
- Infra de cuisson T2 (poses par plante, file à budget) — cf. `00_etat.md`.

## À faire
1. **Pont (Python, lecture pure)** : `weather.wind = {force, direction, gusts}`
   depuis `wind_at`/`gust_profile` (seed + semaine courante) ; par plante, un
   facteur d'abri local **seulement si `eco.vent` est déjà calculé** (sinon
   omettre la clé → la vue prend 1.0). Bump `ENGINE_VERSION` + entrée de
   changelog dans `version.py` (patron existant) ; test dans
   `tests/simserver/` (clés présentes, déterminisme, snapshot == dernier step
   via `_scrub`). `SimBridge`/`WorldView.Snapshot.cs` lisent les clés.
2. **8 poses = 8 degrés de flexion** cuits par T2 : courbure croissante du
   collet (≈0) vers l'apex (max), dans la direction du vent **projetée en iso
   à l'écran** (composante latérale gauche/droite + légère composante
   profondeur). Re-cuisson des 8 poses quand la direction projetée dérive
   au-delà d'un seuil (passe par la file à budget de T2).
3. **Onde** (vue, par frame, O(plantes visibles), sans allocation) :
   `phase = (pos_monde · dir_unitaire)/λ − ω·t` ;
   `flexion = clamp(raideur × force_locale × (fond + enveloppe(phase)), 0, 1)` →
   pose `round(flexion × 7)`. Enveloppe **asymétrique** (montée rapide = la
   poussée, descente lente = la plante se relève). `fond` ∝ force (sous vent
   soutenu, les plantes restent penchées). λ, ω ∝ force (rafale plus rapide).
   Calibrer λ/ω/seuils en constantes nommées commentées.
4. **Balancement propre** : + petit terme `a × sin(ω₂t + hash(id))`,
   `a ∝ force` (nul sans vent) → chaque plante a sa vie, sans casser le front.
5. **Raideur par port** : ligneux/arbres plient peu et **en retard**
   (déphasage ∝ hauteur), herbacées plient fort. Dériver le port de données
   DÉJÀ au snapshot ou au catalogue C# (vérifier ce qui existe : silhouette,
   espèce, structure) — ne pas créer de champ moteur.
6. `WeatherLayer.cs` : les stries de vent et l'inclinaison de la pluie suivent
   la vraie direction/force (aujourd'hui inclinaison fixe `_slantPx`).

## Critère de réussite
Banc T0 : séquence de PNG à ×8 sous vent fort → on VOIT le front passer
(décrire la séquence dans `00_etat.md`) ; sous calme → images identiques
frame à frame. Coût/frame mesuré. `dotnet build` vert, `test_sim_server` vert,
golden intact. Question F5 Nico : « le vent se voit-il, comme une main qui
appuie ? ».

## NE PAS
- Faire bouger les plantes sans vent ; synchroniser toutes les plantes.
- Calculer `eco.vent` dans le serveur s'il est `None` ; toucher au tick moteur.
- Recuire les 8 poses à chaque frame (seulement sur invalidation, via la file).
- GDScript ; `test_epaisseur_500ans` ; fichiers > 400 LDC.
