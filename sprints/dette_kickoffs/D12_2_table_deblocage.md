# Dette D12.2 — Table de mapping palier → déblocage

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception SEULE.** Ampleur **petite**.
> ⚠️ **BLOQUÉ tant que D13/D14/D15 ne sont pas conçus** — ce sprint ne fait que les
> **coordonner**. Ne le lance qu'**après** `D13_magazine_botanique.md`,
> `D14_carnet_auto.md`, `D15_extension_terrain.md`.

## Ce que c'est, en une phrase
Écrire **la table unique** qui dit *quel palier de maîtrise débloque quoi* : quel
palier ouvre le **magazine** (D13), bascule le **carnet** en interprétatif (D14), fait
apparaître la **tuile thématique** (D15), et enrichit l'**encyclopédie**. C'est de la
**coordination inter-dettes**, **pas** de la mécanique interne (chaque dette a déjà la
sienne).

## Pourquoi c'est un sprint séparé (et pas dans D12, D13, D14, D15)
- `CONCEPTION_MAITRISE.md` **§8 point 2** l'isole explicitement : « Table de mapping
  palier → déblocage […] La coordination inter-dettes, **sans leur mécanique
  interne**. » Chaque consommateur (D13/D14/D15) définit *ce qu'il fait* ; D12.2 dit
  *à partir de quel palier*. Mettre les seuils dans chaque dette les éparpillerait —
  on veut **une source unique** pour équilibrer le rythme de progression d'un coup
  d'œil.
- `CONCEPTION_MAITRISE.md` **§3.2** : rappel des **deux mesures globales** que la
  table peut lire — la **complétude-ratio** (`completude_ratio`, → seuils de
  déblocage) et l'**accumulation-log** (→ Vigueur, hors sujet ici). La table travaille
  surtout sur les **paliers par objet** (`0..5`) et la complétude.

## Ce qui est déjà tranché (ne pas re-débattre)
- Paliers `0..5` : **découverte → investissement → maîtrise → expertise →
  transcendant** (CLAUDE.md + `CONCEPTION_MAITRISE.md` §2).
- Spillover **intra-famille** déjà actif (la maîtrise d'une espèce nourrit sa famille).
- Le **transcendant** (palier 5) = non-action existentielle (écosystème
  auto-suffisant) — la table doit réserver quelque chose de fort à ce palier.
- La table est **data-driven** (comme tout le reste de la maîtrise), pas du code en
  dur — c'est un dictionnaire/tableau lisible.

## 🔵 Choix de design à trancher (à figer une fois D13/D14/D15 connus)
Ces choix **ne peuvent se trancher proprement qu'après** la conception des trois
consommateurs — c'est pourquoi ce sprint vient en dernier. Les voici listés pour que
tu saches ce qui t'attend :

### Choix 1 — Échelle de lecture : palier par objet, par famille, ou complétude globale ?
- Magazine (D13) : reco probable = **complétude de famille** (cf. D13 choix 2).
- Carnet (D14) : reco = **palier du concept** concerné (bascule par concept).
- Terrain (D15) : reco = **palier de famille** (verger ↔ Rosaceae maîtrisées).
- Encyclopédie : **palier de l'espèce** (basique → bio → effets écosystémiques).
→ La table n'est donc **pas** une colonne unique : c'est **4 sous-tables**, chacune
lisant la bonne granularité. **À confirmer** quand D13/D14/D15 auront figé la leur.

### Choix 2 — Densité des seuils (le rythme de jeu)
À quel palier ouvre-t-on chaque chose ? Esquisse de défaut sobre (à calibrer) :
| Palier | Nom | Déblocage type |
|---|---|---|
| 1 | découverte | entrée d'encyclopédie **basique** |
| 2 | investissement | **carnet interprétatif** sur le concept ; encyclopédie « bio » |
| 3 | maîtrise | **tuile thématique** (D15) ; offres **magazine** (D13) de la famille |
| 4 | expertise | encyclopédie « effets écosystémiques » ; offres magazine élargies |
| 5 | transcendant | météo entièrement prévisible (déjà spécifié) ; signe `🌿` |

> C'est une **esquisse**, pas une décision. La vraie densité dépend de la difficulté
> des Nᵢ (répétitions/palier, ← calibrage D12.4). À poser après test.

### Choix 3 — Couplage avec le calibrage D12.4
Les **valeurs** (combien de succès pour franchir un palier) sont du **calibrage
post-test** (D12.4). D12.2 fige la **structure** (qui-débloque-quoi-à-quel-palier),
pas les nombres. **À garder séparé** pour ne pas re-figer la table à chaque réglage.

## Périmètre — phase CONCEPTION (livrable)
Une section **§8.2** dans `CONCEPTION_MAITRISE.md` (ou un `CONCEPTION_DEBLOCAGE.md`)
contenant les **4 sous-tables** (encyclopédie / carnet / magazine / terrain) en format
data-driven, renvoyant les **valeurs numériques** à D12.4. Plus une note sur
l'**interface** : un seul lecteur (`deblocages_actifs(game_state, player) -> {...}`)
que D13/D14/D15 interrogent, pour garder la coordination en un point.

## Hors périmètre
Les **mécaniques internes** de D13/D14/D15 (leurs sprints). Les **nombres** de
calibrage (← D12.4, post-test). Le portage C# (D24). Toute UI.

## Golden / vérification
Conception = zéro code. À l'impl. : pur lecteur read-only au-dessus du tick → **golden
intact**. Test : `deblocages_actifs` renvoie le bon ensemble pour un état de maîtrise
donné. MAJ `DETTE.md` (D12.2 ✅) + `BACKLOG.md`.
