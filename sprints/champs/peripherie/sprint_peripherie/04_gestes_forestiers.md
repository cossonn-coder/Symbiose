# ④ Gestes forestiers — abattre, recéper, étêter

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` + ①→③.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §3.3, §4.3, §4.4, §5.
>
> **Golden attendu : INCHANGÉ.** Gestes event-driven, hors tick ; le golden tourne sans
> joueur ⇒ jamais appelés.

## Objectif

Le joueur mord enfin dans la lisière. Trois gestes que le paysan distingue et que le jeu
doit distinguer — c'est **l'asymétrie de leurs cinétiques** qui enseigne, pas leur effet
immédiat.

## Fichier à créer

`data/code/sim/actions/paysage.py` — nouveau module. **N'ajoute pas ces gestes à
`gestes.py`** (233 LDC, une responsabilité déjà pleine). Exporte-les depuis
`sim/actions/__init__.py` sur le patron des autres (`creuser`, `drainer` y sont ligne 37).

## A. Les trois gestes

| Geste | Effet sur le secteur | Souche | Outil |
|---|---|---|---|
| `abattre` | `densite_ligneuse` ↓ franc (→ ~0.1), `hauteur_canopee` ↓ | `"morte"` | hache |
| `receper` | `densite_ligneuse` ↓ (→ ~0.2), `hauteur_canopee` → ~0 | `"vivante"` **si l'essence rejette**, `"morte"` sinon | serpe |
| `eteter` | `hauteur_canopee` ↓ (~40 %), `densite_ligneuse` **conservée** | `"vivante"` | serpe |

Tous posent `annees_depuis_coupe = 0.0`.

**Le fait discriminant** (§3.3) — toutes les essences ne rejettent pas de souche :

```python
ESSENCES_QUI_REJETTENT = {"charme", "aulne", "saule"}   # + tout futur taillis
# hetre, bouleau : rejettent très mal → recéper une hêtraie, c'est l'abattre.
```

C'est vrai en sylviculture et c'est la meilleure leçon du tronçon : le joueur ne
l'apprend qu'en le faisant, ou en lisant l'encyclopédie une fois la maîtrise acquise
(#6). **Ne l'annonce nulle part dans l'UI, ne bloque pas le geste.**

## B. Cinétiques de repousse (§4.4)

Déterministe : fonction de `annees_depuis_coupe` + `souche_memory` + essence.
**Aucun tirage** (#3) — pas de « l'arbre repousse peut-être ».

| Cas | Retour à densité pleine |
|---|---|
| Étêtage (trogne) | **5 ans** |
| Recépage, essence qui rejette | **10 ans** |
| Recépage, essence qui ne rejette pas | *jamais* (devient un abattage) |
| Abattage → pionnières | 4 ans |
| Abattage → canopée fermée | **30 ans** |

Ces chiffres sont calés sur le réel (noisetier 7-9 ans, charme 10-12, saule têtard 3-5,
canopée tempérée refermée en 25-40 ans). La repousse s'applique dans un tick léger
`tick_repousse(ceinture, semaines)` appelé depuis `sim/engine/boucle.py` — **O(4)**,
et **no-op strict si `ceinture is None`** (golden).

## C. Outils (D93 tombe pour ce périmètre)

Un registre d'outils **existe déjà** : `sim/outils.py` (D82, l'Atelier) + la grammaire
de déblocage `GESTE_UNLOCK` de `sim/actions/deblocage.py:66`. Lis les deux — tu n'as
qu'à ajouter des entrées, **ne conçois pas d'inventaire**.

```python
# sim/outils.py — registre OUTILS
"hache":  {"marqueur": "posseder_hache",  "cout_vigueur": ...,  "offre": True},
"serpe":  {"marqueur": "posseder_serpe",  "cout_vigueur": ...,  "offre": True},
"pioche": {"marqueur": "posseder_pioche", "cout_vigueur": ...,  "offre": True},

# sim/actions/deblocage.py — GESTE_UNLOCK
"abattre":   [("action", "posseder_hache")],
"receper":   [("action", "posseder_serpe")],
"eteter":    [("action", "receper")],       # on apprend la trogne après le taillis
```

Coûts Vigueur dans `sim/actions/couts.py` : `abattre` **TRÈS ÉLEVÉ**, `receper`/`eteter`
**ÉLEVÉ** (palier existant le plus proche ; placeholders de calibrage F5, comme
`creuser`). Renseigne aussi `OBJETS_TOUCHES` (technique + outil), patron
`"creuser": ("terrassement", "bêche")` ligne 115.

⚠️ **Justification du coût** (décision D-3, §5) : c'est l'**effort physique**, PAS
« action directe sur le vivant ». L'arbre périphérique est un agrégat, pas une
`PlantInstance` ; fonder un barème sur cette fiction se paierait plus tard. Écris-le
dans le commentaire.

## D. Comptabilité (§5) — trois traces, pas une jauge

1. **Ledger** — consigne chaque geste via `sim/journal.py` (`consigner`). Alimente
   carnet, encyclopédie du geste (découverte à la 1ʳᵉ utilisation, D60) et détection de
   maîtrise. Le geste est *enregistré*, jamais *scoré*.
2. **Trace dans le milieu** — `souche_memory`, `annees_depuis_coupe`, densité effondrée.
   État écologique persistant, pas un compteur.
3. **Retour de matière — le bois est une MATIÈRE POSÉE, pas une jauge.** Attention,
   c'est un point où il est facile de se tromper : **il n'existe PAS de nature `"bois"`
   dans `mulch_stock`** (`NATURES_MULCH` = paille · brf · aiguilles · feuilles).
   Dans ce projet le bois vit comme **parcelle de litière typée `bois`** au sol, et deux
   gestes le manipulent :
   - `empiler_bois` (`sim/actions/compost.py:131`) — déplace les parcelles `bois` d'un
     plot vers une **pile à bois** (`STRUCTURE_ACCEPTE["pile"] = {"bois"}`, le bac le
     **refuse**) ;
   - `broyer` (`sim/actions/paillage.py`) — consomme le `bois_restant` d'un squelette et
     crédite `mulch_stock["brf"]`.

   Donc : **l'abattage dépose des parcelles `bois`** sur les plots du bord, via
   `eco.deposer_litiere(r, c, "bois", masse)`
   (`fields/ecofields/matiere_organique.py:47`). Le joueur va ensuite le chercher,
   l'empile ou le broie — avec sa décompo lente, son habitat de pile, ses champignons
   saproxyliques et la faim d'azote du BRF (D40). **Ne crédite AUCUN stock directement**
   et ne crée pas de nature `"bois"` : ce serait un raccourci qui court-circuite tout le
   circuit décompo/structures déjà en place, et remplacerait une matière qu'on voit par
   un compteur qu'on lit (#5).

**AUCUN indicateur d'impact cumulé, aucune jauge à l'écran** (#5).

## Tests

`tests/test_peripherie.py` :

1. **Golden neutre** — sans joueur, rien n'est appelé.
2. **Gating** — `abattre` sans hache ⇒ `False`, **aucune Vigueur débitée**, secteur
   inchangé (patron « refuser sans rien coûter »).
3. **Rejet de souche** — `receper` sur `charme` ⇒ `souche_memory == "vivante"` ;
   sur `hetre` ⇒ `"morte"`.
4. **Cinétiques** — après recépage d'un charme : densité pleine à 10 ans, pas à 5.
   Après abattage : toujours pas pleine à 10 ans.
5. **Matière** — abattre dépose des parcelles `bois` sur les plots du bord (et **pas**
   sur les plots centraux) ; ces parcelles sont bien acceptées par `empiler_bois` et
   refusées par le bac.
6. **Idempotence/bornes** — `densite_ligneuse` reste dans [0,1] après gestes répétés.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ**.

## Ce qu'il NE faut PAS faire

- **Ne bloque JAMAIS le geste destructeur** (#6). Abattre toute la lisière sud doit être
  possible ; c'est le jardin qui répond, pas un avertissement.
- **Ne conçois pas d'inventaire d'outils** : `sim/outils.py` existe (D82).
- **Pas de jauge d'exploitation, pas de compteur d'impact** (#4, #5).
- **Pas de RNG dans la repousse** (#3).
- **Ne gonfle pas `gestes.py`** : module dédié.
- **N'exécute JAMAIS** `test_epaisseur_500ans`.
