# ④ Extractions enchâssées + réparation des liens vivants

**Préalable** : lire `00_etat.md` — **décision 4** (les 126 entrées de journal ne
sont PAS réécrites) est l'arbitrage central de ce tronçon.

## A — Extraire les thèmes enchâssés

Certains thèmes n'ont pas de doc dédié parce qu'ils vivent **à l'intérieur**
d'un autre fichier. Les extraire, en laissant un pointeur à l'emplacement d'origine.

**Cas identifié** : l'**éclairement (zone Z7)** vit dans `docs/meta/vision.md`
(ex-`docs/desktop/vision.md`, section Z7) et dans `BACKLOG.md` (section « Zone Z7
— éclairement spatial — CONCEPTION CLOSE », ~ligne 117).

1. Créer `docs/champs/lumiere/conception_eclairement.md` avec le contenu extrait,
   **verbatim**, en conservant la mention de statut « CONCEPTION CLOSE ».
2. À l'emplacement d'origine, laisser :
   `> Déplacé → voir [`champs/lumiere/conception_eclairement.md`](...)`.
3. **Rien n'est supprimé sans pointeur.** C'est la contrainte « zéro perte ».

Avant d'extraire, chercher d'autres cas :
`grep -n '^#\{2,3\} ' docs/meta/vision.md docs/meta/architecture.md` — un titre de
section qui correspond à un thème de la taxonomie est un candidat. En signaler
la liste dans `00_etat.md` ; n'extraire que ce qui est clairement un thème
autonome (ne pas démembrer un doc de synthèse par excès de zèle).

## B — Réparer les liens des fichiers VIVANTS

**Périmètre strict** — ces fichiers seulement :

| Fichier | Nature du renvoi |
|---|---|
| `CLAUDE.md` | cite `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`, `docs/conception/`, l'arbo cible |
| `BACKLOG.md` | liens vers conceptions et sprints |
| `DETTE.md` | idem |
| `journal.md` (l'index) | idem |
| `world/SolTexture.cs` | **du C# cite un doc de conception** — commentaire à mettre à jour |
| `.claude/skills/audit-projet/SKILL.md` | ⚠️ code `docs/conception/` **en dur** |
| `.claude/skills/conception/SKILL.md` | ⚠️ idem — c'est le skill qui crée les docs ! |
| les nouveaux `docs/**/*.md` | 22 liens relatifs internes seulement |

⚠️ **Les deux skills sont le point le plus important du tronçon.** `/conception`
écrit ses livrables dans `docs/conception/` et `/audit-projet` y cherche les docs
à auditer. Si on les oublie, ils continuent de fonctionner en apparence mais
recréent l'ancienne arborescence à plat au prochain usage — le rangement se
défait tout seul. Les mettre à jour pour qu'ils **écrivent dans le bon thème**
(et documenter la règle de choix du thème dans le skill `conception`).

## C — Ce qu'on NE réécrit PAS

Les **126 entrées de `journal/` et `journal_archive/`**. Ce sont des comptes
rendus historiques, fidèles à l'état du dépôt à leur date. Les réécrire, c'est
400+ modifications à risque pour un gain nul, et c'est falsifier des archives.
La table « ancien chemin → nouveau » de `docs/ARBORESCENCE.md` (tronçon ①) sert
de clé de lecture. **Ajouter une note explicite** en tête de `journal.md` :

```markdown
> Les entrées d'avant le 2026-07-22 citent les anciens chemins
> (`docs/conception/CONCEPTION_*.md`). Table de correspondance :
> [`docs/ARBORESCENCE.md`](docs/ARBORESCENCE.md).
```

## Vérification — chasse aux liens morts

Script de contrôle (à écrire dans `tools/` seulement s'il n'existe pas déjà) ou
one-liner : pour chaque lien Markdown relatif des fichiers **vivants**, vérifier
que la cible existe.

```bash
# repérer les cibles inexistantes citées par les fichiers vivants
grep -roh '](\([^)]*\.md\))' CLAUDE.md BACKLOG.md DETTE.md journal.md docs/ \
  | sed 's/](\(.*\))/\1/' | sort -u | while read f; do
      [ -e "$f" ] || echo "MORT: $f"; done
```

Attendu : **aucune sortie** (hors liens vers `journal/` depuis la racine, à
vérifier à la main selon le répertoire de base).

- `grep -rn 'docs/conception' CLAUDE.md BACKLOG.md DETTE.md journal.md .claude/ world/` → **aucun résultat**.
- `cd data/code && python3 -m tests.test_golden` → **inchangé** (`SolTexture.cs`
  n'est qu'un commentaire ; si le golden bouge, quelque chose a mal tourné).

## Commit

`docs(rangement) ④ : extraction éclairement Z7 + liens vivants réparés (skills inclus)`

Puis cocher ④ dans `00_etat.md`.
