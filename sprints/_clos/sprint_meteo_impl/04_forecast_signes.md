# Sous-sprint 04 — Forecast + signes diégétiques (read-only)

> **Kickoff autosuffisant.** Démarre à froid. Lis ce fichier, puis
> [`00_etat.md`](00_etat.md) et la spec [`CONCEPTION_METEO.md`](../../data/code/CONCEPTION_METEO.md)
> **§3** (forecast), **§4** (signes), **§5** (paliers — pour comprendre ce qui
> est *hors* périmètre). Les sous-sprints 01-03 sont **faits** : `sim/weather.py`
> fournit `weather_at(seed, week)` pure, `WeatherEvent(kind, intensity,
> duration_weeks, scope)` et **`forecast(seed, week, horizon)` est DÉJÀ livré**
> (offert d'avance en 01). Le gel/grêle sont médiés par gène (03).

## Objectif

Donner au moteur la **structure de donnée des signes diégétiques** (Z2) : une
fonction **pure et déterministe** qui, pour une semaine courante, dit quels
**signes perceptifs** sont visibles dans le monde parce qu'un événement météo
arrive dans 1-2 semaines. Plus le **masque déterministe** qui laisse ~20 % des
événements **sans préavis** (§4.3).

C'est le **cadeau de la fonction pure** (§3) : prévoir = évaluer `weather_at` en
avance. `forecast` existe déjà ; 04 ajoute (a) la **table signe → événement**
(§4.1), (b) le **masque de signe** (`K_SIGN`, §4.3), (c) une fonction de lecture
`weather_signs(seed, week, horizon)`. **Côté données pur, AUCUN rendu** (sprites
oiseaux/ciel/anneau = Godot, plus tard) et **AUCun palier** (l'interprétation au
seuil de maîtrise est gated sur D12, non implémentée).

**Succès =** `weather_signs` pure et déterministe livrée + masque ~80 % signés
vérifié statistiquement + **cohérence forecast == réalité** (la semaine venue,
l'événement prévu *est* celui qui tombe) + un test dédié vert +
**golden INCHANGÉ** (`63bfdac4…` PASS *sans* `--capture`) car on ne touche pas
`tick_semaine`.

## Pourquoi ce sous-sprint est « neutre » (golden intact)

04 est **read-only sur la simulation** : il n'écrit dans aucun champ, ne modifie
ni la croissance ni la météo appliquée. Il ne fait que **lire** `weather_at` en
avance et **classer** le résultat. Donc :

- **Ne pas toucher `tick_semaine`** ni aucun chemin d'application d'effet.
- Le golden doit rester `63bfdac4…` et **passer sans régénération**. Si le golden
  change, c'est qu'un couplage a fui dans la simulation → **bug à corriger**, pas
  à re-figer.

## Décision de conception à acter au démarrage (poser la question à Nico)

**Forme du retour de `weather_signs` : exposer le flag `signed`, ou pré-filtrer ?**
Le masque (§4.3) décide si un événement **émet** un signe. Sous le palier
transcendant, le joueur ne voit que les événements signés ; **au transcendant**,
le palier « lève le masque » et même les 20 % deviennent lisibles (§4.3/§5) —
mais *l'événement ne change pas*, seule la **visibilité** dépend de la maîtrise.

→ **Recommandation : retourner la structure COMPLÈTE avec un flag `signed: bool`**
(et les signes), et **laisser l'appelant filtrer** selon le palier. Ainsi la
couche palier/UI (D12, plus tard) décide d'afficher les signes des `signed=True`
seulement, ou de tout révéler au transcendant — **sans re-toucher `weather.py`**.
C'est le design data-driven cohérent avec le reste du moteur. Si Nico préfère
plus simple, `weather_signs` peut ne renvoyer que les événements signés (mais on
perd la marche transcendant gratuite). Acter avant de coder.

## Avant de commencer

1. `git status` propre (le commit de 03 doit être en place, golden `63bfdac4…`).
2. Lire `sim/weather.py` en entier : `weather_at`, `forecast`, le `WeatherEvent`,
   les **canaux-sentinelles** `K_OCC/K_PICK/K_MAG/K_PEST` aux coords `90_00x`,
   `_CATALOGUE` (les `kind` exacts et leurs fenêtres saisonnières).
3. Relire `CONCEPTION_METEO.md` **§4.1** (table signe→événement — les libellés
   des signes sont la source de vérité), **§4.3** (la formule du masque) et la
   note du sous-sprint 02 dans `00_etat.md` (« le forecast sera pleinement
   read-only et honnête » — cadence météo hebdomadaire actée).
4. Repérer qu'il n'existe **pas** encore de test météo dédié (`tests/` = golden,
   génétique, auxiliaires) → 04 en crée un.

## Travail

1. **Canal-sentinelle `K_SIGN = (90_005, 0)`** dans `sim/weather.py` (le prochain
   libre après `K_PEST=90_004`), décorrélé des autres flux.
2. **Table `SIGN_TABLE`** : `kind → tuple[str, ...]` des signes diégétiques,
   recopiée fidèlement de la **table §4.1** (gelée tardive → ciel clair étoilé /
   brume rasante / anneau lunaire ; canicule-sécheresse → ciel laiteux / insectes
   au ras du sol / sol qui craquelle… etc.). Les libellés sont des **données**
   (français, voix naturaliste) ; pas de logique de rendu.
3. **Masque de signe** — fonction pure `is_signed(seed, week) -> bool` :
   `_hash_noise(seed, week, *K_SIGN) > 0.20` (~80 % signés, §4.3). `week` = la
   **semaine de l'événement** → un événement donné est signé (ou non) de façon
   **stable** quelle que soit la semaine d'où on l'observe.
4. **Lecture `weather_signs(seed, week, horizon=2)`** — pure :
   - pour `k` dans `1..horizon`, regarder `ev = weather_at(seed, week + k)` ;
   - ignorer le temps calme (`Beau temps`) ;
   - construire une petite structure par événement à venir : son `kind`, dans
     combien de semaines (`k`), ses signes (`SIGN_TABLE[ev.kind]`), et le flag
     `signed = is_signed(seed, week + k)` (cf. décision actée) ;
   - renvoyer la liste. **Aucun état, aucun RNG live.** (Un `@dataclass
     WeatherSign(kind, in_weeks, signs, signed)` immuable est le bienvenu, à côté
     de `WeatherEvent`.)
5. **Test dédié `tests/test_signes.py`** (lancé `python3 -m tests.test_signes`,
   style des autres tests : `check(...)`, sortie ✅/❌, `SystemExit`) :
   - **déterminisme** : `weather_signs` deux fois → identique ;
   - **cohérence forecast == réalité** : pour un échantillon de semaines, le
     `kind` annoncé à `week` pour l'horizon `k` est **exactement** celui que
     `weather_at(seed, week + k)` renvoie (par construction, mais on le prouve) ;
   - **masque ~80 %** : sur un large échantillon de semaines à événement,
     `is_signed` vrai ≈ 80 % (tolérance large, p.ex. 70-90 %) ;
   - **couverture table** : tout `kind` du `_CATALOGUE` (hors `Beau temps`) a une
     entrée dans `SIGN_TABLE` (sinon `KeyError` silencieux plus tard) ;
   - **ambiguïté voulue** : au moins un signe apparaît pour ≥ 2 `kind` distincts
     (§4.1 « certains signes sont ambigus » — vérifie qu'on l'a bien encodé).

## Vérification (critères de succès)

- **Golden NEUTRE** : `python3 -m tests.test_golden` **PASS sans `--capture`**
  (hash `63bfdac4…` inchangé). Si ça casse → un couplage a fui dans la sim, à
  corriger (ne **pas** re-figer).
- `python3 -m tests.test_signes` → tout vert.
- `python3 -m tests.test_genetique`, `tests.test_auxiliaires` → inchangés.
- `python3 main.py` → exit 0 (on n'a rien changé au comportement ; sert juste de
  non-régression d'import).
- **Déterminisme** : `weather_signs(seed, w)` rejoué = identique.

## Garde-fous

- Français + pédagogie (Nico vient du C/Python embarqué).
- **Pur données / pur calcul** : aucun rendu, aucune dépendance Godot, aucun
  `print` dans `weather.py`. Les signes sont des **chaînes de données** que la
  couche d'affichage (plus tard) traduira en sprites/sons.
- **Hors périmètre, ne PAS faire** : paliers de maîtrise météo et bascule
  interprétative du carnet (gated **D12**) ; révélation transcendant (côté UI) ;
  rendu des signes (Godot) ; tout couplage qui écrirait dans un champ.
- **Couches** : `weather.py` reste dans `sim`, n'importe que `fields`
  (`_hash_noise`). `weather_signs` ne doit **pas** importer `engine` (cycle).
- **Multi-fichiers cohérent assumé** : `weather.py` + nouveau `tests/test_signes.py`.
  Rester surgical : pas de refactor de `weather_at`/`forecast` (ils marchent).
- En fin : mettre à jour `00_etat.md` (04 = FAIT, golden confirmé **inchangé**,
  décision actée sur la forme du retour), **commit**, `/clear`. C'est le **dernier
  sous-sprint** du sprint météo d'implémentation → penser à une entrée
  `journal.md` de clôture de sprint (cf. CLAUDE.md « mettre à jour journal.md à la
  fin de chaque sprint »).
