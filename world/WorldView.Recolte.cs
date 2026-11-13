// SYMBIOSE — WorldView.Recolte.cs (partial de WorldView, GESTES LISIBLES ④)
// LA DÉSIGNATION DE `recolter` (conception §6) : on récolte en cliquant le FRUIT, pas le
// tronc. La vue résout la plante, le moteur reste juge de ce que vaut la récolte (gain
// ∝ maturité de la plante, `sim/actions/gestes.recolter`).
//
// Trois cas, dans cet ordre :
//  1. un fruit MÛR est dessiné sous le clic → on récolte la plante qui le porte ;
//  2. le clic tombe sur une plante qui PORTE des fruits, mais pas sur un mûr (le tronc,
//     une feuille, un fruit vert) → rien n'est envoyé, et on le dit en mots ;
//  3. le clic tombe sur une plante SANS fruit au snapshot (lavande, salade, trèfle à
//     quatre feuilles…) → c'est la plante entière qui est l'organe : on la récolte comme
//     avant. Décidé ici, à confirmer au F5 : sans ce repli, le trèfle à quatre feuilles
//     (récolté par `recolter`) ne serait plus cueillable.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		/// <summary>Résout la cible de `recolter` (cf. en-tête). False = refus déjà dit
		/// au HUD, rien à envoyer.</summary>
		private bool CibleRecolte(Vector2 canvasPos, Vector2 w, out PlantRenderer node, out GDict target)
		{
			target = null;
			node = FruitMurSous(canvasPos);
			if (node == null)
			{
				PlantRenderer plante = FindFruitPortSous(canvasPos) ?? FindPlant(w, PickRadiusCm)
					?? FindPortSous(canvasPos);
				string refus = plante == null ? "récolter : aucune plante à portée du clic"
					: plante.NombreFruits == 0 ? null   // cas 3 : la plante entière
					: plante.AFruitMur ? "récolter : visez un fruit mûr, pas la plante"
					: "récolter : ses fruits ne sont pas encore mûrs";
				if (refus != null)
				{
					_lastActionMsg = refus;
					UpdateActionHud(); FlashActionLabel();
					return false;
				}
				node = plante;
			}
			target = new GDict
			{
				["tile"] = node.GetMeta("tile"),
				["x_cm"] = node.GetMeta("lx"),
				["y_cm"] = node.GetMeta("ly"),
			};
			return true;
		}

		/// <summary>Plante dont un fruit MÛR est dessiné sous le clic (le plus proche), ou
		/// null. Balayage linéaire des plantes (patron FindFruitPortSous).</summary>
		private PlantRenderer FruitMurSous(Vector2 canvasMouse)
		{
			PlantRenderer best = null;
			float bestD = float.PositiveInfinity;
			foreach (var node in _plantNodes.Values)
			{
				if (node.NombreFruits == 0) continue;
				float d = node.DistanceFruitMur(canvasMouse);
				if (d < bestD) { bestD = d; best = node; }
			}
			return best;
		}
	}
}
