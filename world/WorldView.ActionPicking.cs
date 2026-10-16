// SYMBIOSE — WorldView.ActionPicking.cs (partial de WorldView)
// Scindé de WorldView.Actions.cs (/refactor) : le PICKING au clic/survol.
// FindPlant (plante la plus proche), FindPlot (tuile + plot sous le point),
// FindSegmentGlobal (la branche sous la souris, toutes plantes) + tolérance de
// segment et UpdateTailleHighlight (surbrillance de taille). Recherche linéaire
// assumée (~170 nœuds — mesurer avant d'optimiser, pas de quadtree). L'ÉTAT
// (rayons, _highlightNode) vit dans WorldView.Actions.cs (même classe).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		/// <summary>Plante affichée la plus proche du point MONDE (cm), dans
		/// `radiusCm`, ou null. ~170 nœuds : recherche linéaire, pas de quadtree
		/// à inventer (leçon perf : mesurer avant d'optimiser).</summary>
		private PlantRenderer FindPlant(Vector2 w, float radiusCm)
		{
			PlantRenderer best = null;
			float bestD = radiusCm * radiusCm;
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = node; }
			}
			return best;
		}

		/// <summary>Tuile + plot contenant le point MONDE (cm). False si le
		/// point tombe entre les tuiles (chemins) ou sur la maison.</summary>
		private bool FindPlot(Vector2 w, out string tileId, out int r, out int c)
		{
			foreach (var tv in _world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				float ox = (float)t["origin_x_cm"].AsDouble();
				float oy = (float)t["origin_y_cm"].AsDouble();
				int rows = t["rows"].AsInt32(), cols = t["cols"].AsInt32();
				if (w.X >= ox && w.X < ox + cols * PlotCm
					&& w.Y >= oy && w.Y < oy + rows * PlotCm)
				{
					tileId = t["id"].AsString();
					c = (int)((w.X - ox) / PlotCm);
					r = (int)((w.Y - oy) / PlotCm);
					return true;
				}
			}
			tileId = null; r = c = 0;
			return false;
		}

		// Tolérance du hit-test de segment en px CANVAS : 8 px ÉCRAN quel que
		// soit le palier de zoom (le canvas est multiplié par Zoom à l'écran).
		private float SegmentPickTolPx() =>
			SegmentPickPx / (_camera != null ? _camera.Zoom.X : 1f);

		/// <summary>
		/// LA branche sous la souris, toutes plantes confondues (correctif
		/// t5·B) : le segment le plus proche du curseur sous la tolérance,
		/// cherché chez TOUTES les plantes dont la portée (PickExtentCm,
		/// étalement + hauteur) atteint le point souris — plus de filtre par
		/// collet à 30 cm, qui excluait la couronne des arbres. Préfiltre
		/// monde au carré (pas de racine), puis hit-test exact par segment ;
		/// ~170 plantes dont une poignée passent le préfiltre : trivial.
		/// Survol ET clic passent ici : ce qui est surligné = ce qui part.
		/// </summary>
		private PlantRenderer FindSegmentGlobal(Vector2 canvasMouse, out int segIndex)
		{
			segIndex = -1;
			PlantRenderer best = null;
			float bestD = SegmentPickTolPx();
			Vector2 w = ScreenToWorld(canvasMouse);
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float ext = node.PickExtentCm;
				if (dx * dx + dy * dy > ext * ext) continue;
				int seg = node.FindSegmentNear(canvasMouse, bestD, out float d);
				if (seg >= 0 && d < bestD) { bestD = d; best = node; segIndex = seg; }
			}
			return best;
		}

		// Surbrillance de la branche sous la souris en mode tailler (tranche
		// 5) : MÊME résolution que le clic (FindSegmentGlobal) — ce qui est
		// surligné est EXACTEMENT ce qui partira en target.segment. Appelée
		// chaque frame ; les setters HighlightSegment font early-out, le
		// redraw ne part qu'au changement.
		private void UpdateTailleHighlight()
		{
			if (!_survolSale) return;   // clé de survol inchangée (T3)
			PlantRenderer node = null;
			int seg = -1;
			if (_gesteIndex >= 0 && Gestes[_gesteIndex].Verb == "tailler"
				&& _plantNodes.Count > 0)
				node = FindSegmentGlobal(_sourisCanvas, out seg);
			if (_highlightNode != null && _highlightNode != node
				&& IsInstanceValid(_highlightNode))
				_highlightNode.HighlightSegment = -1;
			_highlightNode = node;
			if (node != null) node.HighlightSegment = seg;
		}
	}
}
