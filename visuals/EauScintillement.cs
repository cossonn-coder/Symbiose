// SYMBIOSE — EauScintillement.cs (FLUIDITÉ PC ④ — étincelles de la rivière de lisière)
// Nœud ENFANT de DecorLayer : la SEULE animation du décor (admise par la DA : un
// signal d'eau vive, pas une décoration qui bouge partout). DecorLayer lui confie,
// à chacun de ses redessins (build, palier, rotation), des points d'eau en px
// canvas ; ce nœud en allume ~1 sur 4 à chaque PHASE (3 par seconde), tirés au
// hash (point, phase) — zéro Random (philo #3), même rendu à temps de jeu égal.
//
// 📖 Pédagogie — pourquoi un nœud à part : un CanvasItem se redessine EN ENTIER.
// Si les étincelles vivaient dans le lot du décor, chaque clignotement relancerait
// le dessin des dizaines de milliers de sommets du décor (35-58 ms [VM]). Ici, le
// lot ne compte que quelques centaines de sommets : on paie un redessin minuscule,
// et seulement quand la phase change (jamais à chaque image). Le temps vient du
// `delta` accumulé dans _Process : pause du jeu ou Movie Maker → temps cohérent.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class EauScintillement : Node2D
	{
		private const float PhasesParSeconde = 3f;
		private const float MaxZoom = 4f;   // miroir de DecorLayer.MaxZoom (décor éteint au-delà)
		private static readonly Color Etincelle = new Color("e4f4f8");

		private readonly List<Vector2> _pts = new();
		private readonly List<uint> _h = new();
		private readonly LotTriangles _lot = new();
		private double _t;
		private long _phase = -1;
		// Instrument : coût moyen d'un redessin, écrit 2 fois (après 30 et 300).
		private int _nDessins;
		private double _msCumul;

		/// <summary>Vide les points (appelé au début du redessin du décor).</summary>
		public void Vider() { _pts.Clear(); _h.Clear(); }

		/// <summary>Un point d'eau candidat (px canvas, déjà calé au pixel interne).</summary>
		public void Ajouter(Vector2 p, uint h) { _pts.Add(p); _h.Add(h); }

		/// <summary>Fin du redessin du décor : on redessine les étincelles à la
		/// nouvelle géométrie (palier, rotation) ou on s'efface s'il n'y a plus d'eau.</summary>
		public void Publier() => QueueRedraw();

		public override void _Process(double delta)
		{
			if (_pts.Count == 0 || WorldView.CurrentZoom > MaxZoom || !IsVisibleInTree()) return;
			_t += delta;
			long phase = (long)(_t * PhasesParSeconde);
			if (phase == _phase) return;
			_phase = phase;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (_pts.Count == 0 || WorldView.CurrentZoom > MaxZoom) return;
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			float z = WorldView.CurrentZoom;
			float px = 1f / z;   // 1 px interne en unités canvas
			_lot.Vider();
			uint ph = (uint)_phase * 0x9e3779b1u;
			for (int i = 0; i < _pts.Count; i++)
			{
				uint h = DecorLayer.Melange(_h[i] ^ ph);
				if ((h & 3u) != 0u) continue;   // ~1 point sur 4 allumé par phase
				Vector2 p = _pts[i];
				if ((h >> 3 & 1u) == 0u)
				{
					// Étoile en « + » de 3 px : l'éclat franc.
					Rect(p + new Vector2(-px, 0f), 3f * px, px);
					Rect(p + new Vector2(0f, -px), px, 3f * px);
				}
				else Rect(p, 2f * px, px);   // éclat couché de 2 px
			}
			_lot.Dessiner(this);
			Mesurer(t0);
		}

		private void Rect(Vector2 coin, float w, float h) =>
			_lot.PolygoneConvexe(new[] { coin, coin + new Vector2(w, 0f), coin + new Vector2(w, h),
										 coin + new Vector2(0f, h) }, Etincelle);

		private void Mesurer(long t0)
		{
			_msCumul += (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0
					  / System.Diagnostics.Stopwatch.Frequency;
			_nDessins++;
			if (_nDessins == 30 || _nDessins == 300)
				GD.Print($"[DecorLayer] scintillement : {_pts.Count} points d'eau,"
					   + $" {_msCumul / _nDessins:F2} ms/redessin (moy. {_nDessins})");
		}
	}
}
