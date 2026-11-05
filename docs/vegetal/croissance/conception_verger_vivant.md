# Conception VERGER VIVANT : les arbres se renouvellent, fleurissent juste, portent beaucoup

**Figée le 2026-11-05** avec Nico (D129). Sprint : `sprints/vegetal/croissance/sprint_verger_vivant/`, 4 tronçons. Mesures : `00_etat.md` du sprint.

## 1. Demande

F5 du 2026-11-05 : « les noyers et cerisiers ne donnaient pas de fruits, les fleurs quasi invisibles (un cerisier en fleur c'est beau, il y en a partout) ». La dette D129 mesurait trois choses : des arbres qui déclinent, peu de fruits, des fleurs qu'on ne voit presque pas.

## 2. Causes trouvées

| Constat | Cause | Mesure |
|---|---|---|
| Les arbres fondent (cerisier : de 53 à 12 segments, de 16 à 1 apex) | Un segment n'a qu'**un** bourgeon (`has_bud`), consommé à vie par `_debourrement`. Une branche perdue (tempête, neige, ombre) n'est jamais remplacée. | Sans tempête, sans neige et sans ombre, les 5 arbres restent au plafond [`verger_mur`, seed 42, n=1 run par variante, 5 ans, VM] |
| Pommier mort au banc | Banc trop serré (arbres à 4 m) : carence lumineuse, puis asphyxie | Lumière reçue 0,23 à 0,35 en saison feuillée [mêmes conditions] |
| 10 fruits au plus | `MAX_ORGANS = 10`, un fruit par site, sites = apex | — |
| Noyer : 1 à 3 noix | Dose de pollen apportée par le vent de 0,01 à 0,41 par an, et floraison en juin, sur 7 semaines | [`verger_mur`, n=1 run] |
| Fleurs vues 2 semaines | La vue ne dessine les fleurs qu'à `floraison ≥ 0,5`, en tout ou rien ; au plus 120 fleurs, une brindille sur deux | Cerisier : 0,35 / 0,58 / 0,73 / 0,36 / 0,18 [n=1 run] |
| Pommier en fleur avant le cerisier | `bloom_forcing_gdd` pommier 8 < cerisier 12 : l'ordre réel est inversé | Code |

## 3. Décisions (Nico, 2026-11-05)

| # | Décision | Pourquoi |
|---|---|---|
| 1 | **Bourgeons dormants** : un vieux segment peut réveiller un bourgeon quand la couronne est sous son plafond, l'arbre vivant et éclairé ; vaut après toute perte, pas seulement après une casse | C'est la réitération réelle (gourmands, rejets). Essai brut, un bourgeon toutes les 4 semaines : cerisier de `full` en an 5, 17 segments et 1 apex sans → 34 segments et 17 apex avec, 4 → 10 fruits ; tick médian 1 017 → 1 051 ms [`full`, seed 42, n=1 run par côté, VM, charge < 1] ; golden `a10b7225…` identique [smoke, patch mémoire] |
| 2 | **Limites de fruits relevées dans le moteur**, pas seulement à l'écran | Nico : « relève les limites de fruits » |
| 3 | **Noyer** : dose anémophile recalibrée après correction de sa floraison | 1 à 3 noix par an pour un noyer adulte, ce n'est pas réaliste |
| 4 | **Fleurs nombreuses et belles** dans la vue, densité continue selon `floraison`, pétales qui tombent | Nico : « il faut que les fleurs soient nombreuses et belles » |
| 5 | **Floraison réaliste dans le moteur** : ordre des espèces, date, durée, pic de pleine floraison | Nico : « dans le moteur la floraison doit être réaliste » |

## 4. Bourgeons dormants (moteur)

Intention : le bois garde des bourgeons latents. Une fois qu'un arbre a perdu une partie de sa couronne, et tant qu'il reste vivant et reçoit assez de lumière, quelques-uns se réveillent, à un rythme borné, et la couronne se reconstruit vers son plafond. La réponse vient du flux (lumière, vitalité) ; aucun bonus direct n'est appliqué (philo #2). Tout est déterministe, avec un hash sur `form_seed`, la semaine et un ordinal ; aucun RNG (philo #3).

Garde-fous : le collet est exclu ; le rythme est borné, pour ne pas tout regarnir d'un coup ; un sous-arbre condamné par la cladoptose ne doit pas repartir sous la même ombre (sinon on aurait une boucle casse-repousse chaque semaine). Il faut donc que la lumière locale ou la lumière de la plante conditionne le réveil.

## 5. Floraison réaliste (moteur)

Calendrier : wiy 1 ≈ 20 mars. Cibles à sourcer au tronçon et à déclarer `[odg]` : cerisier mi-avril, avant le pommier ; pommier fin avril à mi-mai ; noyer, chatons fin avril à mai, sur 1 à 2 semaines ; figuier, fleur cachée, inchangé. Il faut aussi qu'un arbre en pleine floraison **atteigne** une intensité proche de 1 pendant la durée réelle de sa pleine floraison. Aujourd'hui le pic plafonne à 0,73 : la montée exponentielle (`FLORAISON_MONTEE` 0,35) n'a pas le temps d'arriver en haut en 3 semaines. Le levier est à choisir **par espèce ligneuse** (durée, montée), sans toucher aux herbacées.

## 6. Fruits par cohorte (moteur et pont)

Un `Fruit` devient une **cohorte portée par un site**, avec un **nombre** de fruits. C'est le moyen de compter des centaines, voire des milliers de fruits réels sans multiplier les objets ni le JSON. Le nombre de fruits par site et la masse unitaire viennent de l'espèce : ordres de grandeur à sourcer (cerisier : des milliers ; pommier : des centaines ; figuier : des centaines ; noyer : des centaines à des milliers). Sur un arbre, tous les apex sont des sites, sans le plafond de 10. Manger prend **un** fruit de la cohorte. La chute donne nombre × masse unitaire en litière `fruit`, et cette masse doit rester cohérente avec la litière de feuilles (`FEUILLE_PAR_PLOT`) : à mesurer sur la fertilité et la faune attirée. Pour tomate, fraise, framboise et courgette, une cohorte vaut 1 fruit : leur comportement ne change pas.

## 7. Vue

- **Fleurs** : densité continue avec `floraison`, du bouton à la pleine floraison puis à la chute. Bouquets de plusieurs fleurs par brindille, et non un bouton sur deux brindilles. Au pic, le houppier d'un cerisier paraît blanc ; le pommier passe du bouton rose à la fleur blanc rosé. Des pétales tombent au sol au déclin (vue seule, sans effet moteur). Le plafond de 120 fleurs se relève, sous budget de cuisson mesuré.
- **Fruits** : on dessine le nombre de la cohorte, avec un plafond de dessin pour la perf, réparti sur les brindilles du site.
- **Banc F5** : le verger espacé, avec ses arbres en fleur puis en fruits.

## 8. Coût

Moteur : bourgeons +3 % de tick [`full`, n=1 run par côté]. Les cohortes ne coûtent rien de plus par objet. Budget ≤ +10 % de tick par tronçon. Vue : cuisson et FPS mesurés au ④.

## 9. Hors périmètre

- La hausse d'humidité du sol année après année (2,5 à 2,8, asphyxie des aulnes) reste à D127 : cause non isolée.
- La cladoptose et la casse elles-mêmes ne changent pas : on rend la réitération possible, on ne réduit pas les pertes.
- Les fleurs des herbacées restent à D118.
