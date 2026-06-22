# 2026-06-22 — Sprint PLASTICITÉ & EXPRESSION DE GÈNES ADAPTOGÈNES · tronçon ⑤ (signe d'acclimatation) — SPRINT TERMINÉ

> Conception figée : `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md`.
> État partagé : `sprints/sprint_plasticite/00_etat.md`.
> Tronçons ①②③④④bis déjà clos (commits `2e9f97f`→`8bb6599`).

## Objectif du tronçon ⑤

Rendre la plasticité **apprenable, pas magique** (philo #5/#6, P3) : une plante
fortement acclimatée le **montre**. Le joueur voit le signe → formule une
hypothèse → consulte → comprend l'acclimatation. Golden **NEUTRE** attendu
(détecteur = lecture pure, comme toute la sémiologie foliaire).

## Décision tranchée (laissée ouverte par le kickoff)

Le kickoff demandait de **trancher dans le journal** : un signe générique ou un
par stress dominant. **Choix : UN signe générique unique `acclimatation`.**
Raisons :
1. **Simplicité** (CLAUDE.md #2) — une cause, un mapping C#, pas cinq.
2. Au stade découverte, le joueur apprend d'abord « cette plante s'est
   **endurcie** » ; la finesse par stress (sécheresse vs froid vs ombre) est un
   raffinement futur, cohérent avec la dette P4 (carnet interprétatif).
3. **Forward-compatible** : on pourra raffiner par stress sans casser le schéma.

## Réalisé

### Moteur Python — `sim/semiologie.py`
- Nouveau détecteur chronique pur `acclimatation(plant, eco, saison)` : intensité
  = la **plus forte sur-expression** parmi les gènes adaptogènes, en **rampe de
  `EXPR_MIN` à `EXPR_MAX`** (bornes mêmes de la dynamique d'expression — DRY, pas
  de nombre dupliqué). Équivaut au `max_g(expression[g] − 1)` du kickoff.
  Particularité assumée : contrairement aux autres détecteurs (miroir du SEUIL
  d'une mécanique qui *blesse*), l'acclimatation est une **RÉPONSE** continue, pas
  un dégât → la rampe couvre toute la plage utile, pas de seuil de souffrance.
- Ajouté au registre `DETECTEURS` et à `PRIORITE` avec **priorité 9** (la plus
  basse) : à intensité égale, on montre toujours d'abord le signe de **dégât**,
  le durcissement en dernier (le moins urgent à diagnostiquer).
- Import `ADAPTOGENIC_GENES, EXPR_MIN, EXPR_MAX` depuis `plants.genetics`
  (`sim` ← `plants`, couche basse, import légal).

### Pont — `tools/simserver/version.py`
- Bump **0.5.2 → 0.5.3**. Nouvelle cause `acclimatation` dans la liste ouverte
  `leaf_symptoms` = **extension de DONNÉES**, pas de schéma (la vue ignore une
  cause inconnue, tolérance pré-0.5.3). Aucune écriture moteur.

### Vue C# — `visuals/PlantRenderer.cs`
- Teinte glauque `#9db8b0` (cire bleu-gris, feuillage coriace, synthèse bio §4)
  ajoutée à `ColorantTints`. Réutilise le **canal COULEUR** existant : un vrai
  signe de souffrance (intensité plus forte) la masque, mais sur une plante sans
  pathologie le glauque **révèle** qu'elle s'est endurcie. Aucune nouvelle
  plomberie (mécanisme `SetSymptoms`/`SymptomTint` du sprint sémiologie ③).
  **F5 visuel = Nico.**

### Test — `tests/test_plasticite.py`
- `test_signe_acclimatation` : plante nue → aucun signe ; acclimatation max d'un
  gène → intensité 1.0 ; mi-plage → 0.5 (rampe linéaire) ; tri = un dégât d'ombre
  d'égale intensité passe **devant** l'acclimatation.

## Vérifications

- `python3 -m tests.test_golden` → **NEUTRE**, hash inchangé `2ab026ad…`
  (détecteur hors `_PLANT_ATTRS`, espèces du smoke sans stress vécu ⇒ expression
  = EXPR_MIN ⇒ aucun signe).
- `tests/test_plasticite` 8/8 (dont ⑤), `test_signes` 8/8,
  `test_stress_chronique` PASS, `test_genetique` 20/20.
- `dotnet build Symbiose.csproj` → **0 avertissement, 0 erreur**.

## Dette créée

- **D43** — lien **Maîtrise → carnet interprétatif** de l'acclimatation (P4) :
  au palier du concept *adaptation/génétique* (D12), le carnet bascule de
  descriptif (« feuillage cireux ») à interprétatif (« cette lignée s'est
  acclimatée à la sécheresse, ses descendants naîtront pré-armés »). Dépend du
  système Maîtrise (déjà en Python) ET du carnet auto (non implémenté).

## Bilan du sprint (①→⑤)

Trois échelles d'adaptation coexistent désormais : **génotype** (darwinien, figé),
**expression** plastique (lamarckien, réversible, `expressed_gene = clamp_gene(
genes × expression)`), et **priming transgénérationnel** (l'expression voyage avec
la graine par tous les canaux). Le coût croissance/défense (③) empêche
l'anti-sélection ; l'oubli est émergent (pas de compteur). Le tronçon ⑤ rend le
tout **visible et apprenable**. Golden final `2ab026ad…` (inchangé depuis ④,
NEUTRE en ④bis et ⑤), pont **0.5.3**.
