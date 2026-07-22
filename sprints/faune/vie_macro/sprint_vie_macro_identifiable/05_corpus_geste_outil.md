# ⑤ Corpus geste + outil (3 niveaux) (D60)

> Kickoff autosuffisant. Reprise à froid : `CLAUDE.md` + `00_etat.md` + ce fichier.
> Dépend de ① (dispatch + registre) et de ③ (progression qui rend N2/N3
> atteignables). Golden **NEUTRE** (données pures). Tronçon de RÉDACTION.

## Objectif
Écrire les fiches d'encyclopédie **3 niveaux** pour les onglets **geste** et
**outil**, et les brancher au dispatch de ①. Même registre/structure que ④
(Observation / Biologie·Mécanisme / Écosystème·Maîtrise).

## Périmètre — clés à couvrir
- **Gestes** (source de vérité = clés de `sim/actions/couts.COUTS`) :
  `planter`, `arroser`, `recolter`, `deraciner`, `ecraser`, `favoriser_auxiliaire`,
  `becher`, `grelinette`, `tailler`, `manger`, `poser_bac`, `poser_pile`,
  `composter`, `empiler_bois`, `retourner`, `epandre`, `poser_ruche`,
  `recolter_miel`, `poser_pot`, `poser_bac_culture`, `deplacer_pot`.
  ⚠️ Couvrir TOUTES les clés que `type_de` classe `"geste"` au moment de l'impl.
- **Outils** (ensemble `outils` de ① = membres de `OBJETS_TOUCHES` − `TECHNIQUES`) :
  `arrosoir`, `sécateur`, `bêche`, `grelinette`, `fourche`, `bac-à-compost`,
  `pile-à-bois`, `ruche`, `équipement-apicole`, `pot`, `bac`, `amendement`.
  ⚠️ Idem : aligner exactement sur ce que `type_de` classe `"outil"`.

## Fichiers à créer
- **CRÉER `sim/geste_corpus.py`** — `FICHES_GESTE: dict[str, dict[int, str]]`.
- **CRÉER `sim/outil_corpus.py`** — `FICHES_OUTIL: dict[str, dict[int, str]]`.
- **BRANCHER** ces corpus dans `CORPUS_PAR_TYPE` (`sim/encyclopedie.py`) pour les
  types `geste` et `outil`. Troncature `min(palier, 3)` uniforme.

## Registre & style
- Voix naturaliste, factuelle. Un geste : N1 = ce qu'il fait de visible, N2 = la
  mécanique écologique qu'il engage (ex. `arroser` → humidité du sol, seuils de
  germination), N3 = son rôle dans l'équilibre du jardin et ses effets de bord (ex.
  `becher` casse le réseau mycélien — cf. `CONCEPTION_MYCELIUM_INTERCONNEXIONS`).
- Un outil : N1 = l'objet, N2 = son usage juste, N3 = quand s'en passer (sagesse
  écologique, non-action, philo transcendant).
- Interconnexions dans le texte (relier geste↔technique↔outil↔effet). Pas de
  chiffres de gameplay (#5), pas d'injonction (#6).
- Respecter le garde-fou de taille (scinder si un corpus gonfle).

## Ce qu'il NE faut PAS faire
- Ne PAS toucher tick / moteur / golden.
- Ne PAS inventer de clés hors `encyclopedie_types` (fiche morte sinon).
- Ne PAS re-styler l'UI (⑥).
- Ne PAS dupliquer la classification outil/technique : la table de ① fait foi.

## Golden
NEUTRE. Test : chaque clé geste/outil de `encyclopedie_types` a une fiche 3
niveaux ; troncature palier correcte ; alignement clés ↔ classification (zéro trou,
zéro surplus). Après ④+⑤, un test global peut vérifier que **tout** objet classé
par `type_de` (tous types) a une source de fiche.

## Points F5
Aucun (données). Rendu = ⑥.
