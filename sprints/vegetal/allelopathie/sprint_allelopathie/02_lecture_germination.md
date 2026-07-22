# ② Lecture à la GERMINATION

> Kickoff autosuffisant. Reprise à froid = `CLAUDE.md` + `00_etat.md` + ce fichier
> + `docs/vegetal/allelopathie/conception_allelopathie.md` §B. Prérequis : tronçon ① fait (champ
> `allelopathie` + injection + décroissance). Golden **probable neutre**.

## Objectif

Faire **lire** le champ `allelopathie` par la germination : une forte concentration
sur un plot **referme la niche** des graines sensibles → pas de levée. Introduire le
trait de **sensibilité** par espèce et l'**auto-tolérance** de l'émetteur. Rampe
douce continue (pas de seuil dur, philo `niche_index` continu).

## Fichiers à toucher

- `fields/seedbank.py` — dans `niche_index` (≈ l.381) ou `germination_candidates`
  (≈ l.402) : escompter la niche du candidat par `f_allelo ∈ [0,1]`.
- `plants/base/` (traits d'espèce) — nouveau trait **`allelopathie_sensibilite:
  float = 1.0`** (1 = sensible standard, 0 = tolérant/insensible). **Ne pas
  renseigner** de valeurs marquantes ici (défaut 1.0 partout) — le calibrage des
  sensibilités emblématiques est au §E / tronçon ⑤.
- `sim/succession.py` si les portes de levée y dupliquent une logique de niche
  (vérifier ; sinon laisser).

## Modèle / formules

- `f_allelo = 1 − SENS_esp · rampe(allelopathie[r,c])`, borné [0,1].
- `rampe(x)` = saturante douce type Monod : `x / (x + K)` (K placeholder calibrage).
  Continue, pas de seuil dur (D6).
- Niche finale du candidat = `niche_index_actuel × f_allelo`.
- **Auto-tolérance** (D2) : l'émetteur ne s'inhibe pas lui-même. Champ unique →
  approximation **préférée : sensibilité propre basse** de l'émetteur à sa propre
  molécule (ex. `allelopathie_sensibilite` ≈ 0 sur l'espèce émettrice, posé au ⑤).
  Alternative (auto-exclusion du champ auto-produit) plus lourde → **ne pas**
  l'implémenter sauf blocage. Trancher **surgical**, documenter le choix.

## Golden attendu

**Probable NEUTRE** (à confirmer). Raison : au smoke, peu d'émetteurs matures (noyer
maturity > 2 ans ; adventices non émettrices, trait défaut 0 au ①). **Invariant
dur** : `allelopathie = 0` partout ⇒ `rampe(0) = 0` ⇒ `f_allelo = 1` ⇒ germination
**strictement inchangée**. Lancer `python3 -m tests.test_golden` → hash inchangé
attendu. Si dérive : soit un émetteur charge le champ (alors le ⑤ n'est pas censé
être fait — vérifier qu'aucun trait `allelopathie_emission > 0` n'a fuité), soit
bug de la rampe à x=0.

## Ce qu'il NE faut PAS faire

- Ne PAS toucher la croissance des plantes établies (tronçon ③).
- Ne PAS introduire de seuil dur (rampe continue obligatoire, D6).
- Ne PAS renseigner de sensibilités marquantes par espèce (tronçon ⑤).
- Ne PAS faire de malus direct : tout passe par l'escompte de niche (philo #2).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

Golden neutre + test ad hoc : injecter `allelopathie` fort sur un plot, y semer une
graine sensible (`sensibilite=1`) → niche effondrée, pas de levée ; une graine
tolérante (`sensibilite=0`) → lève normalement.
