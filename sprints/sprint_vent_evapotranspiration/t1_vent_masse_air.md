# Tronçon ① — Vent masse d'air (scalaires O(1))

> Kickoff autonome. Design : `CONCEPTION_VENT_EVAPOTRANSPIRATION.md` **§2** (champ
> de vent) + **§2.3** (vent↔nébulosité). **Tout scalaire/tuile, O(1).** Golden
> **neutre** (on calcule le vent, on ne le LIT pas encore).

## But
Créer la **masse d'air** : une fonction pure `wind_at(seed, week)` sur le modèle de
`weather_at` (`sim/weather.py`, canaux-sentinelles décorrélés, zéro RNG vivant) :
- **force** ∈ [0,1+] (0 nul · ~0.3 brise · ~0.7 soutenu · >1 coup de vent), dérivée
  d'un canal `K_WIND` + saisonnalité (automne/hiver plus venteux) ; les événements
  `Tempête`/`Orage` forcent une force haute (continuise le vent déjà présent comme
  dégât ponctuel), `Beau temps` ≈ brise faible.
- **direction** ∈ [0,2π) : marche lente déterministe (le vent « tourne »).
- **régimes intra-jour** (§2.2) : enveloppe temporelle pure (nul / risées / brise de
  fin de journée) modulant la force hebdo — **scalaire par sous-tick, pas de fluide**.
- **nébulosité dynamique** (§2.3) : remplacer la table figée `NEBULOSITE` lue par
  `weather_state` par une nébulosité **pilotée par le vent** (amène / chasse /
  disperse / stagne). ⚠ ce câblage touchera lumière+rosée+thermique → mais ICI on le
  calcule **sans le brancher en aval** (rester golden-neutre ; le branchement réel
  = tronçon ②).

## Garde-fou golden
À ce stade, **rien ne lit `wind_at`** dans la boucle → le golden doit rester
**bit-identique**. Si le simple fait d'introduire le calcul touche un ordre
d'appel, l'isoler derrière une fonction pure non câblée.

## Critères de succès
- `wind_at` pure, déterministe (même seed+week → même état), testée (un
  `test_vent.py` neuf : monotonie saisonnière, reproductibilité, bornes).
- `python3 -m tests.test_golden` **inchangé**.
- Budget perf : O(1), coût négligeable (vérifier ms/tick stable vs ⓪).

## Clôture
MAJ `00_etat.md` (① ✅). Commit. `/clear`. Lancer `t2_evapotranspiration.md`.
