// SYMBIOSE — WorldView.Luxuriance.cs (partial de WorldView, sprint LUXURIANCE ⑥, D65)
// Le câblage VUE de la luxuriance par stratification : applique le bloc
// `couverture` du snapshot (tapis au sol) et fournit le BIAIS DE ZINDEX PAR STRATE
// qui rend l'empilement multi-strates lisible. Lecture seule (protocole 0.5.19) —
// la donnée (couverture, strate) vient du moteur, Python reste source de vérité :
// ici on ne fait que PROJETER et ORDONNER, jamais recalculer (Godot est « bête »).
//
// 📖 Pédagogie — l'ordre de dessin par strate :
// le nœud "Objects" est YSortEnabled → Godot trie ses enfants par Position.Y
// (profondeur iso). Mais on veut EN PLUS que le couvre-sol passe SOUS la potagère,
// SOUS la grimpante, même quand leurs collets sont à la même profondeur. Dans
// Godot, le ZIndex prime sur le tri Y : deux plantes de même Y mais de ZIndex
// différents se départagent par le ZIndex. On donne donc à chaque PlantRenderer un
// petit biais de ZIndex ∝ sa strate (sol < basse < moyenne < haute < grimpante).
// Le biais est PETIT (bande dédiée sous +10 des objets) → à l'INTÉRIEUR d'une même
// strate, le tri Y reprend la main (y-sort intra-strate, cf. kickoff §B).

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

		// Biais de ZIndex par strate : rang 0..4 dans l'ordre arrière→avant. Le nœud
		// "Objects" est en ZIndex 10 ; on décale chaque plante de son rang (10..14)
		// pour que le couvre-sol (sol=10) passe SOUS la potagère (basse/moyenne) et la
		// grimpante (14). Bande étroite (5 valeurs) : à strate ÉGALE, le y-sort du
		// parent départage (intra-strate). Strate inconnue (snapshot pré-0.5.19) →
		// rang « moyenne » (neutre : tout au même plan, comportement d'avant).
		private static readonly Dictionary<string, int> StrateRang = new()
		{
			["sol"]       = 0,
			["basse"]     = 1,
			["moyenne"]   = 2,
			["haute"]     = 3,
			["grimpante"] = 4,
		};

		// ZIndex d'un PlantRenderer d'après sa strate (lue au snapshot). Base = ZIndex
		// des objets (10) + rang de strate. Défaut « moyenne » (2) si strate absente/
		// inconnue → aucune régression sur un snapshot ancien.
		private static int PlantZIndex(string strate)
		{
			int rang = strate != null && StrateRang.TryGetValue(strate, out int r) ? r : 2;
			return 10 + rang;
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
