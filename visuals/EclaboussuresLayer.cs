// SYMBIOSE — EclaboussuresLayer.cs (sprint GESTES LISIBLES ③, conception §3.2)
// Les ÉCLABOUSSURES de pluie au sol : quand la météo du snapshot est une averse
// (Pluie prolongée / Orage), des gouttes rebondissent sur les tuiles du jardin, en
// nombre ∝ la charge de l'épisode (MeteoPlantes.Pluie, tirée de `weather.intensity`).
// Hors pluie : rien n'est dessiné et la couche dort (aucune image redessinée).
//
// 📖 Pédagogie — un effet TRANSITOIRE de vue, pas un état : il ne lit qu'un fait du
// snapshot (il pleut, plus ou moins fort) et le rejoue en petites animations. Chaque
// « emplacement » i tire une goutte par cycle de `Periode` s ; son point de chute
// est un hash de (i, n° de cycle) → déterministe, aucune Random. Nombre BORNÉ
// (`MaxGouttes`) et un seul lot (un envoi GPU) par image, quelle que soit l'averse.
// Les gouttes ne tombent que dans le cadre visible et sur une tuile (pas sur la
// maison ni les chemins hors jardin) : `ScreenToWorld` ramène le point au sol.

using System;
using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class EclaboussuresLayer : Node2D
	{
		private const int MaxGouttes = 90;      // à charge pleine (Orage fort)
		private const float Periode = 0.5f;     // s : vie d'une éclaboussure
		private const float MinZoom = 1f;       // sous ×1 : trop petit pour se lire

		private readonly List<(string Id, Rect2 Monde)> _tuiles = new();
		private Func<string, int, int, float> _relief;
		private readonly LotTriangles _lot = new();
		private float _t;
		private bool _actif;

		/// <summary>Tuiles du jardin (rectangles MONDE en cm) + recalage relief.</summary>
		public void Init(IEnumerable<(string Id, Rect2 Monde)> tuiles, Func<string, int, int, float> relief)
		{
			_tuiles.Clear();
			_tuiles.AddRange(tuiles);
			_relief = relief;
		}

		public override void _Process(double delta)
		{
			bool actif = MeteoPlantes.Pluie > 0f && WorldView.CurrentZoom >= MinZoom;
			if (actif) _t += (float)delta;
			if (actif || _actif) QueueRedraw();   // une dernière image pour s'effacer
			_actif = actif;
		}

		public override void _Draw()
		{
			_lot.Vider();
			if (_actif) Peindre();
			_lot.Dessiner(this);
		}

		private void Peindre()
		{
			int n = Mathf.RoundToInt(MaxGouttes * MeteoPlantes.Pluie);
			Rect2 vis = MargeVue.Visible;
			for (int i = 0; i < n; i++)
			{
				// Déphasage propre à l'emplacement : les gouttes ne battent pas ensemble.
				uint hi = (uint)i * 2654435761u;
				float phase = (hi >> 8 & 0xffff) / 65536f * Periode;
				int cycle = (int)((_t + phase) / Periode);
				float u = (_t + phase) / Periode - cycle;
				uint h = hi ^ (uint)cycle * 40503u;
				h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
				Vector2 p = vis.Position + vis.Size * new Vector2((h & 0xffff) / 65536f, (h >> 16) / 65536f);
				if (!AuSol(p, out float rise)) continue;
				Goutte(p - new Vector2(0f, rise), u);
			}
		}

		// Le point canvas tombe-t-il sur une tuile ? (et de combien le sol y est haussé)
		private bool AuSol(Vector2 canvas, out float rise)
		{
			Vector2 w = WorldView.ScreenToWorld(canvas);
			foreach (var (id, m) in _tuiles)
			{
				if (!m.HasPoint(w)) continue;
				int r = (int)((w.Y - m.Position.Y) / WorldView.PlotCm);
				int c = (int)((w.X - m.Position.X) / WorldView.PlotCm);
				rise = _relief?.Invoke(id, r, c) ?? 0f;
				return true;
			}
			rise = 0f;
			return false;
		}

		// Trois temps : la goutte touche (un point), la couronne gicle (deux grains qui
		// montent), l'onde s'étale (deux grains écartés, pâlissants).
		private void Goutte(Vector2 p, float u)
		{
			Color col = Palette16.Eclaboussure;
			if (u < 0.3f)
			{
				col.A = 0.9f;
				TracesSolMotifs.Px(_lot, p, col);
			}
			else if (u < 0.65f)
			{
				col.A = 0.85f;
				TracesSolMotifs.Px(_lot, p + new Vector2(-1f, -1f), col);
				TracesSolMotifs.Px(_lot, p + new Vector2(1f, -1f), col);
				TracesSolMotifs.Px(_lot, p + new Vector2(0f, -2f), col);
			}
			else
			{
				col.A = 0.6f * (1f - u) / 0.35f;
				TracesSolMotifs.Px(_lot, p + new Vector2(-2f, 0f), col);
				TracesSolMotifs.Px(_lot, p + new Vector2(2f, 0f), col);
			}
		}
	}
}
