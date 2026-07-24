# 2026-07-24 — Sprint MIGRATION DES 9 ARBRES EN CROISSANCE PROCÉDURALE (D91) — CLOS

**Type :** sprint (`/sprint-auto`) · **Thème :** `vegetal/croissance` · **Statut :** CLOS (①→④)

Solde **D91** : les 9 arbres restants (figuier, cerisier, noyer, chêne, hêtre,
bouleau, charme, sapin, aulne) passent de l'empreinte-couronne tabulée
(`age_curve`) à la **croissance procédurale en segments** (`procedural_growth=True`),
comme le pommier (D29) → ils se dessinent en branches et portent le taper D90.

**Golden `57c166d8…` INCHANGÉ sur les 4 tronçons** (les 9 arbres sont hors
scénario golden — le smoke n'instancie que le pommier ; les 2 leviers neufs ont un
défaut neutre). `dotnet build` VERT.

## ① Feuillus étalés + levier `auxin_release_scale` (`14c4560`)
Attribut moteur **`auxin_release_scale`** (défaut 400.0 → pommier/Tomato/grimpantes
bit-identiques). `_update_auxin` prend un paramètre `release_scale`, passé par
`grow_plant` via `cls.auxin_release_scale`. Défauts procéduraux d'arbre mutualisés
sur `PerennialWoody` (sans flipper `procedural_growth`). 5 feuillus migrés
(cerisier, charme, hêtre, noyer, chêne), calibrés à la sonde (520 ticks, an 10,
montée monotone, structure bornée). **Décision de calibrage** : la fourchette
release_scale 900-1500 suggérée par le kickoff pour chêne/hêtre donne un **poteau
nu** (le débourrement latéral est étouffé dans la fenêtre d'observation) →
release_scale modéré (~500) + **largeur de couronne portée par `foliage_halfwidth`**
(qui sert AUSSI la survie hydrique du jeune arbre). 2 tests D91.

## ② Cas atypiques — aulne / figuier / sapin (`b1a72a0`)
- **Aulne** (etale élancé) `rs=800` — un release_scale « petit » ferait s'étaler le
  leader trop tôt, saturant le cap segments, hauteur bloquée. Rôle hydro D61
  (fixation N₂ Frankia + tolérance asphyxie) préservé et testé.
- **Figuier** (buissonnant mono-collet) `max_segments 70→90` — un buissonnant
  ramifie plus, le cap défaut amputait la charpente. Multi-tronc laissé en **option
  F5 différée** (mono-collet lit correctement).
- **Sapin** (fleche conique, `deciduous=False`) dominance haute + release_scale long.
4 tests T2 (migration, déterminisme, sapin étroit, aulne hydro). 125/125 verts.

## ③ Bouleau + levier `gravitropism_gain` (`ebfcad2`)
Levier moteur **`gravitropism_gain`** (défaut 0.0 = neutre → golden bit-identique),
helper pur `_gravitropic_droop` (`geometrie.py`), greffé dans `_elongate_emit` APRÈS
le phototropisme, passé via `grow_plant`. Bouleau migré en pleureur : leader dressé
+ rameaux distaux pendants, déterministe (biais géométrique pur, zéro RNG).
**Correction d'implémentation vs D1** : le discriminant `depth` prescrit ployait la
flèche elle-même (chaîne axiale profonde à 800 cm) → hauteur effondrée à la sonde.
Remplacé par l'**éloignement horizontal à l'axe (`off_axis`)**, fidèle à l'intention
(« seuls les rameaux distaux retombent »), sans état neuf. Réutilisable saule (D23).
2 tests. 133/133.

## ④ Vue Godot + banc F5 `foret_ports` (`60626ed`)
Pur-vue C#, moteur non touché. Rendu branches **générique** : les 9 arbres sortent du
snapshot en segments comme le pommier, aucune ossature C# neuve. Sapin mappé sur
l'archétype **`Aciculaire`** existant (aiguilles, hors `LeafOutlines`) —
anti-sur-ingénierie. Couverture par espèce : `LeafProfiles` +5, `LeafOutlines` +1
(aulne), `Palettes` +4. Banc d'observation **`foret_ports`** (`bancs/croissance.py`)
= les 10 arbres en grille 5×2, montable par `init config="foret_ports"`.
**Décision imprévue** : le banc utilise la **morphogénèse pure** (`grow_plant`,
oracle des sondes T1-T3), PAS le déroulé Engine complet — les besoins hydriques
inconciliables aulne (berge) / figuier (méditerranéen) tuent des arbres <an 2 sous
une nappe forcée unique ; le banc observe l'architecture, pas l'équilibre écolo.

## Bilan
Refactor auto-léger **no-op** : aucun fichier passé en zone rouge (>400 LDC pur) ;
`perennials.py` à 324 LDC est en vigilance 🟡 mais responsabilité unique (catalogue)
→ toléré, signalé. DETTE **D91 → CLOSE**. Reste **F5 Nico** : lecture visuelle de
chaque port sur `init config="foret_ports"` (flèche du sapin, étalé
chêne/hêtre/noyer, ovoïde cerisier/charme, bas-ramifié figuier, élancé aulne,
**pleureur du bouleau** = le plus incertain), survie hydrique des jeunes arbres, et
calibrage fin à l'œil de tous les placeholders (`growth_speed`,
`auxin_release_scale`, `gravitropism_gain`, `foliage_halfwidth`).
