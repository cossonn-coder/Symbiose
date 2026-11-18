# ④ Souches à réserve finie — fin de la cascade de rejets

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/sante/conception_plante_vivante.md` §6,
`docs/vegetal/regeneration/conception_rejets_de_souche.md`, `sim/souche.py`.

## Constat (mesuré le 2026-11-18, monde `full`, seed 42)
Vagues de chênes nés toutes les ~4 semaines, ×3 par vague (9 → 27 → 75 → 153,
s20-s32), 100 % à < 1,5 m d'un arbre mort ; idem saule, noisetier, charme, aulne.
Cause : `sim/souche.py` `_vague` crée des rejets qui sont des plantes neuves
(`souche_traitee = False`) ; quand un rejet meurt, `deposer_mort`
(`sim/effects/perturbations.py` ~l. 112) lui fige `souche_vivante` → il rejette à
son tour. Réaction en chaîne.

## À faire
1. À la mort d'un ligneux à souche vivante, figer `reserve_souche` = ses
   `reserves × capacite_reserve` (①). Chaque rejet posé coûte de cette réserve
   (constante `COUT_REJET` en semaines d'entretien, à justifier) ; plus de réserve
   → plus de rejet. Le nombre reste borné par `N_REJETS_MAX` (4).
2. Un rejet **n'a pas de souche propre** tant qu'il n'est pas établi :
   `AGE_SOUCHE_PROPRE` (âge vrai `age_years`, ≈ 3 ans, à justifier) — en dessous,
   sa mort ne fige pas `souche_vivante`.
3. Les rejets démarrent avec des réserves prises sur la souche (ils sont portés par
   elle, sans besoin de lumière au départ — cf. docstring de `sim/souche.py`).
4. Même règle pour la perte de couronne d'un arbre vivant (③ de D130) : la vague
   puise dans les réserves de l'arbre.
5. Test `tests/test_souche_reserve.py` : un arbre mort → ≤ 4 rejets au total, même
   si tous les rejets meurent ; un rejet de 5 ans qui meurt peut rejeter.

## Golden
**INTACT attendu** (aucun ligneux à souche ne meurt dans le smoke à vérifier au
lancement). S'il bouge : prouver que la dérive vient des seules souches
(neutraliser → retombe sur le hash du ③), consigner, re-figer.

## Ne PAS faire
- Toucher la levée de semis (succession, banque de graines) : la cascade est
  entièrement due aux rejets.
- Lancer `test_epaisseur_500ans`.

## Contrôle
Monde `full`, seed 42, 52 semaines depuis s10 : naissances d'OakTree par semaine
(script du `00_etat.md`, `diag_chene`) ; plus aucune vague géométrique. Consigner.
