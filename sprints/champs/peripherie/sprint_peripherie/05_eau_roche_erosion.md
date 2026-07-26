# ⑤ Eau & roche — endiguer, dériver, entailler, et l'érosion

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` + ①→④.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §3.4, §4.3, §4.5.
>
> **Golden attendu : INCHANGÉ.** Gestes hors tick ; érosion no-op sans ceinture.

## Objectif

Les gestes du **milieu pur** (philo #1 dans sa forme la plus nette) et leur conséquence
la plus lisible : l'érosion. Ce tronçon complète l'asymétrie de réversibilité — après le
bois qui repousse, la roche qui ne repousse pas.

## A. Les gestes d'eau

Dans `sim/actions/paysage.py` (créé au ④).

| Geste | Effet | Outil | Coût |
|---|---|---|---|
| `endiguer` | `ligne_eau` ↑ sur un secteur `riviere` | bêche | ÉLEVÉ |
| `deriver` | `ligne_eau` ↓ | bêche | ÉLEVÉ |

La nappe de berge du ③ fait le reste : `ligne_eau` haute ⇒ le bord se gorge ⇒
`marais_memory` monte ⇒ marécage. Rien de scripté, tout émerge (#2). Le joueur découvre
qu'il a **déplacé** l'eau, pas créé — c'est le fond du sujet.

**Mare** : `creuser` **existe déjà** (`sim/actions/gestes.py:552`, coût `ELEVE`, outil
bêche). Étends sa cible aux secteurs de ceinture — **ne crée pas un geste `creuser_mare`
en doublon.**

**Entretien du barrage** (§4.4) : un ouvrage non entretenu **se rompt vers 8 ans**.
Même mécanique déterministe que la repousse (`annees_depuis_...` + seuil, zéro RNG). La
rupture rend `ligne_eau` à sa valeur naturelle et émet un événement au ledger. Leçon :
*l'artefact demande un entretien perpétuel* — cohérent avec le run éternel (#4), où rien
n'est jamais « fini ».

## B. La roche

| Geste | Effet | Outil | Coût |
|---|---|---|---|
| `entailler` | `altitude_relative` ↓ sur un secteur `falaise` | pioche | TRÈS ÉLEVÉ |

**Irréversible** : aucune cinétique de retour. C'est le seul geste du jeu dont on ne
revient pas, et c'est délibéré — *certaines échelles ne nous appartiennent pas.*

Conséquences (toutes déjà supportées) : l'ombre portée diminue (le ② lit
`altitude_relative`), et le matériau mis à nu part en érosion (C).

## C. Érosion (§4.5) — minimale, mais réelle

C'est le retour le plus lisible d'une coupe excessive, et le seul qui rende
l'irréversible **visible** (#5).

Modèle minimal, greffé sur `structure_sol` (D30) — **pas de nouveau champ, pas de
nouvelle boucle** :

- déclencheur : secteur à `densite_ligneuse` effondrée **ou** falaise entaillée ;
- effet : dépôt de colluvions sur les plots du bord → `structure_sol` dégradée, humus
  dilué, sur une portée de ~3 plots avec décroissance ;
- rythme : lent et continu, dans le tick de repousse du ④ (déjà O(4)).

Émet un **signe diégétique** (#5) : le sol qui part, pas un chiffre. Registre
`sim/semiologie.py`.

**No-op strict si `ceinture is None`** ⇒ golden intact.

## Tests

`tests/test_peripherie.py` :

1. **Gating** — `endiguer` sans bêche ⇒ `False`, rien débité, rien modifié.
2. **Déplacement, pas création** — `endiguer` ⇒ l'humidité monte au bord amont ;
   `deriver` ⇒ elle baisse. Après plusieurs ticks à `ligne_eau` fort, `est_marais()`
   finit par répondre vrai près du bord.
3. **Rupture** — barrage non entretenu ⇒ `ligne_eau` revient à sa valeur naturelle vers
   8 ans, et l'événement est au ledger.
4. **Irréversibilité** — après `entailler`, `altitude_relative` ne remonte **jamais**,
   quel que soit le nombre de ticks.
5. **Érosion** — après effondrement de `densite_ligneuse` : `structure_sol` se dégrade
   sur les plots de bord, décroissance avec la distance, plots centraux **intacts**.
6. **Neutralité** — sans ceinture, aucun de ces effets ne s'exécute.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ**.

## Ce qu'il NE faut PAS faire

- **Ne crée pas de `creuser_mare`** : `creuser` existe, étends sa cible.
- **Ne simule pas de cours d'eau hors grille** (§3.4) : `ligne_eau` est une condition aux
  limites, pas une rivière.
- **Pas de RNG** dans la rupture ni dans l'érosion (#3).
- **Ne rends pas `entailler` réversible**, même « un peu ». L'irréversible est le
  contenu.
- **Pas de chiffre d'érosion en HUD** (#5) : un signe.
- **N'exécute JAMAIS** `test_epaisseur_500ans`.
