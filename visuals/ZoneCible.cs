// SYMBIOSE — ZoneCible.cs (sprint GESTES LISIBLES ④, conception §6)
// LES CIBLES VALIDES D'UN OBJET EN MAIN : quand un geste à deux temps attend son 2e
// clic sur la MÊME tuile que sa source (bouture, pelletée de compost, greffon), tous
// les plots de cette tuile s'éclairent d'un voile chaux. La contrainte « même tuile »
// se VOIT au lieu de se découvrir par un refus.
//
// 📖 Pédagogie — même patron que les couches du sol-canvas : un nœud enfant du monde,
// qui ne se redessine que quand sa tuile change ou que la vue pivote (la projection de
// l'origine sert de clé d'orientation). Un losange par plot, posé sur le relief comme
// le losange de survol (PlotHover) : la zone suit le sol creusé ou bombé.

using System;
using Godot;

namespace Symbiose
{
	public partial class ZoneCible : Node2D
	{
		// Voile chaux discret + liseré : lisible sur terre, argile et sable.
		private static readonly Color Voile = new(Palette16.MaitreBlanc, 0.22f);
		private static readonly Color Lisere = new(Palette16.MaitreBlanc, 0.45f);

		private string _tuile;
		private Vector2 _origine;
		private int _rows, _cols;
		private Func<string, int, int, float> _relief;
		private Vector2 _cleVue = new(float.NaN, 0f);

		/// <summary>Éclaire les plots de la tuile `tuile` (origine monde en cm, rows×cols).</summary>
		public void Montrer(string tuile, Vector2 origine, int rows, int cols,
							Func<string, int, int, float> relief)
		{
			_tuile = tuile;
			_origine = origine;
			_rows = rows;
			_cols = cols;
			_relief = relief;
			Visible = true;
			QueueRedraw();
		}

		public void Cacher()
		{
			_tuile = null;
			Visible = false;
		}

		public override void _Process(double delta)
		{
			if (_tuile == null) return;
			Vector2 cle = WorldView.WorldToScreen(0f, 0f);   // pivot de vue (D35)
			if (cle == _cleVue) return;
			_cleVue = cle;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (_tuile == null) return;
			float hw = WorldView.TileWPx / 2f, hh = WorldView.TileHPx / 2f;
			var pts = new Vector2[4];
			var tour = new Vector2[5];
			for (int r = 0; r < _rows; r++)
				for (int c = 0; c < _cols; c++)
				{
					Vector2 p = WorldView.WorldToScreen(_origine.X + (c + 0.5f) * WorldView.PlotCm,
						_origine.Y + (r + 0.5f) * WorldView.PlotCm)
						- new Vector2(0f, _relief?.Invoke(_tuile, r, c) ?? 0f);
					pts[0] = tour[0] = tour[4] = p + new Vector2(0f, -hh);
					pts[1] = tour[1] = p + new Vector2(hw, 0f);
					pts[2] = tour[2] = p + new Vector2(0f, hh);
					pts[3] = tour[3] = p + new Vector2(-hw, 0f);
					DrawColoredPolygon(pts, Voile);
					DrawPolyline(tour, Lisere, -1f);   // 1 px, sans anticrénelage
				}
		}
	}
}
