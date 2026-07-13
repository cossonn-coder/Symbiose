# ④ Vue Godot — vitalité continue

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Prérequis :
> ①②③ faits (`vitalite`, `etat`, constitution, campagnol). Doc :
> `docs/conception/CONCEPTION_SANTE_RESILIENCE.md` §4. **Golden INTACT** (le pont
> et la vue ne touchent pas le moteur — sérialisation pure). Règle permanente :
> le dernier tronçon de chaque sprint est la vue Godot.

## Objectif

Exposer la **vitalité continue** au snapshot et faire passer le rendu C# du palier
0-3 à un **dégradé continu** de flétrissure/teinte, pour que l'observateur LISE
l'usure d'une plante (philo #5 : indice visuel, pas de chiffre).

## Contexte

- Aujourd'hui le snapshot n'envoie PAS la santé : la vue infère l'état via
  `leaf_symptoms` (sémiologie). On AJOUTE `vitalite` (float) + `etat` (str) — un
  descripteur global qui complète les symptômes localisés.
- Protocole pont courant : **0.5.27** (`data/code/tools/simserver/version.py`,
  `ENGINE_VERSION`). Ce tronçon → **0.5.28**.

## Partie Python (pont)

1. **`data/code/tools/simserver/serialize.py`** (~ligne 98, dict `base` du vivant) :
   ajoute `"vitalite": round(p.vitalite, 3)` et `"etat": p.etat`. Idem dans le
   second sérialiseur si présent (~ligne 563, snapshot debug/banc). LECTURE PURE
   d'un état déjà porté par l'instance → hors `_PLANT_ATTRS` du golden → **golden
   NEUTRE**. Champs OPTIONNELS côté vue (tolérance pré-0.5.28, comme les autres).
2. **`data/code/tools/simserver/version.py`** : bump `ENGINE_VERSION = "0.5.28"`
   + entrée de changelog (nouveau : `vitalite`/`etat` par plante, dégradé continu).

## Partie C# (vue)

3. **`visuals/PlantRenderer.cs`** (+ partials `PlantRenderer.Palette.cs`,
   `PlantRenderer.Leaf.cs` selon où vit la teinte) : lire `vitalite`/`etat` du
   snapshot. Remplacer le mapping par palier (0-3) par un **dégradé continu** :
   la vitalité module la teinte/saturation du feuillage (sain = vert plein →
   affaibli = terne/désaturé → malade = jauni/flétri) et éventuellement un léger
   affaissement de silhouette. **Compose** avec les `leaf_symptoms` déjà rendus
   (la vitalité = fond global ; les symptômes = marques localisées) — ne pas les
   écraser. Garde une tolérance si `vitalite`/`etat` absents (ancien snapshot).
4. Respecte la palette pixel-art existante (`PlantRenderer.Palette.cs`,
   `Palette16` — cf. cap rendu pixel-art) : le dégradé doit rester dans la palette
   16 teintes, pas d'interpolation RGB libre hors palette.

## Filet de compilation

`dotnet build Symbiose.csproj` doit passer VERT (SDK 8.0 sur la VM, `~/.dotnet`).
C'est le filet — le **F5 visuel reste à Nico** (Godot n'est pas sur la VM).

## Golden — INTACT

`python3 -m tests.test_golden` : **hash inchangé** (= ③). La sérialisation et la
vue ne touchent aucun état moteur. Vérifie-le explicitement.

## Ce qu'il NE faut PAS faire

- Ne pas ajouter `vitalite` à `_PLANT_ATTRS` (ce n'est pas l'objet du golden ; ①
  l'a déjà géré côté moteur).
- Ne pas recalculer la vitalité côté C# — la vue LIT, le moteur Python est la
  source de vérité.
- Ne pas lancer `test_epaisseur_500ans` (interdit — long/inutile).

## Vérif de sortie

`python3 -m tests.test_golden` vert/inchangé ; `dotnet build Symbiose.csproj`
vert ; note dans `00_etat.md` le point F5 à valider par Nico (dégradé de vitalité
lisible, cohérent avec les symptômes foliaires).
