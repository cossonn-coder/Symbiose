// SYMBIOSE — WorldView.Champignon.cs (partial de WorldView, sol qui respire ⑧)
// MANGER un champignon : le geste `manger` (palette, famille « plante ») désigne un
// CARPOPHORE quand on clique sur un chapeau. Le pont route sur la FORME de la cible
// (`target.carpophore = [r, c, slot]`, protocole 0.5.54, slot exposé en 0.5.56) ;
// l'effet (Vigueur, perte, vision) est décidé par Python (`sim/champignon_manger`).
//
// 📖 Pédagogie — priorité de désignation : un chapeau à moins de CarpoPrioriteCm
// du clic l'emporte sur la plante voisine (on vise un champignon au pied d'une
// salade : c'est le champignon qu'on veut) ; plus loin, la plante d'abord, puis à
// défaut le carpophore dans le rayon de la vie macro. Comme l'observation, on ne
// désigne que ce qui est AFFICHÉ (zoom ≥ ×4, LOD de CarpophoreLayer).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Rayon (cm) où un chapeau passe avant la plante la plus proche.
		private const float CarpoPrioriteCm = 15f;

		/// <summary>Cible `manger` du carpophore le plus proche de `w` (cm monde)
		/// dans `rayonCm`, ou false (rien d'affiché / pont pré-0.5.56).</summary>
		private bool CibleCarpophore(Vector2 w, float rayonCm, out GDict target)
		{
			target = null;
			if (CurrentZoom < MacroObserveMinZoom || _carpophoreLayer == null
				|| !_carpophoreLayer.Cible(w, rayonCm, out string tile, out int r,
										   out int c, out int slot, out _))
				return false;
			target = new GDict
			{
				["tile"] = tile,
				["carpophore"] = new Godot.Collections.Array { r, c, slot },
			};
			return true;
		}

		// DEBUG (D112 ②, touche U) : un psilocybe pousse au plot sous la souris,
		// pour la semaine affichée — même liste de perception que les carpophores
		// poussés (Python) → info-bulle, cueillette `manger`, vision, overdose comme
		// en jeu. Le bloc renvoyé est appliqué tout de suite (pas d'attente du tick).
		// Visible au zoom ≥ ×4 (LOD de CarpophoreLayer).
		private void DebugPsilocybe()
		{
			if (_bridge == null) return;
			if (!FindPlot(ScreenToWorld(WorldMouseCanvas()), out string tile, out int r, out int c))
			{
				GD.Print("[WorldView] DEBUG champignon : aucun plot sous la souris.");
				return;
			}
			var resp = _bridge.DebugCarpophore(tile, r, c);
			if (resp == null || !resp["ok"].AsBool())
			{
				GD.PrintErr($"[WorldView] DEBUG champignon refusé : {resp?["error"]}");
				return;
			}
			_carpophoreLayer?.SetCarpophores(resp["carpophores"].AsGodotDictionary(), _origins, fade: false);
			GD.Print($"[WorldView] DEBUG champignon : psilocybe en {tile} ({r},{c}).");
		}
	}
}
