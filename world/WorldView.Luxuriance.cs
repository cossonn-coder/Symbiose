// SYMBIOSE — WorldView.Luxuriance.cs (partial de WorldView, sprint LUXURIANCE ⑥, D65)
// Le câblage VUE de la luxuriance par stratification : applique le bloc
// `couverture` du snapshot (tapis au sol) et fournit le BIAIS DE Y PAR STRATE
// qui départage l'empilement multi-strates à pied égal. Lecture seule (protocole
// 0.5.19) — la donnée (couverture, strate) vient du moteur, Python reste source de
// vérité : ici on ne fait que PROJETER et ORDONNER, jamais recalculer.
//
// 📖 Pédagogie — l'ordre de dessin par strate (révisé D112 ②, « maison en verre ») :
// le nœud "Objects" est YSortEnabled → Godot trie ses enfants par Position.Y
// (profondeur iso). PIÈGE Godot 4 : le tri Y ne vaut qu'ENTRE enfants de MÊME
// ZIndex ; un ZIndex différent sépare les nœuds en couches et PRIME sur le Y.
// L'ancien biais de ZIndex par strate (10..14) posait donc TOUTES les plantes par-
// dessus la maison (z 0 relatif) — la maison paraissait en verre — et toute haute
// par-dessus tout couvre-sol, même devant elle. Désormais tout ce qui vit dans
// "Objects" (maison, plantes, supports, conteneurs, compost) se trie PAR Y dans
// deux plans seulement : 0, et −1 pour la maison et ce qui est caché derrière elle
// (ZObjet, WorldView.Maison.cs) ; la strate ne départage qu'à Y quasi égal, par un
// biais de Y infime (rang × 0,001 px monde : ×32 → 0,13 px écran au pire, jamais
// visible) — à pied égal le couvre-sol passe SOUS la haute (invariant ⑥), et à
// quelques pixels d'écart c'est la profondeur réelle qui décide (un trèfle DEVANT
// le tomate cache bien la base de sa tige).

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Tapis de couverture au sol (⑥) : layer batché, enfant direct de WorldView
		// (survit à RebuildWorld). Lit le bloc `couverture` (0.5.19). ZIndex 0 =
		// au ras du sol, sous tout le reste (cf. instanciation dans WorldView.cs).
		private CouvertureLayer _couvertureLayer;

		// Halo de sol pelé de l'allélopathie (sprint ALLÉLOPATHIE ⑥, 0.5.29) : le
		// pendant NÉGATIF du tapis de couverture — même famille d'indice de sol
		// diégétique (philo #5), enfant direct de WorldView (survit à RebuildWorld).
		// Lit le bloc `allelopathie` (foyers > ALLELO_FLOOR côté serveur).
		private AllelopathieLayer _allelopathieLayer;

		// Rang de strate 0..4 dans l'ordre arrière→avant (sol < basse < moyenne <
		// haute < grimpante). Strate inconnue (snapshot pré-0.5.19) → rang « moyenne »
		// (neutre : comportement d'avant).
		private static readonly Dictionary<string, int> StrateRang = new()
		{
			["sol"]       = 0,
			["basse"]     = 1,
			["moyenne"]   = 2,
			["haute"]     = 3,
			["grimpante"] = 4,
		};

		// Biais de Y (px monde) d'un PlantRenderer d'après sa strate : le départage
		// à pied égal du tri Y de "Objects" (cf. en-tête). Plus haut rang = plus
		// grand Y = dessiné APRÈS (devant). Infime par construction : il ne change
		// l'ordre qu'entre plantes au même pied, jamais la position visible.
		private const float BiaisYParRang = 0.001f;
		private static float PlantYBias(string strate)
		{
			int rang = strate != null && StrateRang.TryGetValue(strate, out int r) ? r : 2;
			return rang * BiaisYParRang;
		}

		// Applique le bloc `couverture` (lecture tolérante : un snapshot pré-0.5.19
		// n'a pas la clé → pas de tapis dessiné, jamais de crash). Reconstruction
		// pleine (le tapis est inerte entre deux semaines, pas de fondu à tenir).
		private void ApplyCouverture(GDict couverture)
		{
			_couvertureLayer?.SetCouverture(couverture, _origins);
		}

		// Applique le bloc `allelopathie` (lecture tolérante : un snapshot pré-0.5.29
		// n'a pas la clé → pas de halo dessiné, jamais de crash). Reconstruction pleine
		// (le halo est inerte entre deux semaines, pas de fondu à tenir).
		private void ApplyAllelopathie(GDict allelo)
		{
			_allelopathieLayer?.SetAllelopathie(allelo, _origins);
		}
	}
}
