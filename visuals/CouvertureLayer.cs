// SYMBIOSE — CouvertureLayer.cs
// Le TAPIS DE COUVERTURE au sol (sprint LUXURIANCE ⑥, D65 §2.1/§2.3). Le champ
// `couverture_sol` du moteur — fraction du sol couverte par les strates basses
// (sol+basse), scattée par les empreintes — est exposé au snapshot (bloc
// `couverture` = liste creuse `[[r, c, cov], …]`, protocole 0.5.19). On en tire un
// INDICE DIÉGÉTIQUE (philo #5) : un tapis vert semi-transparent au sol, plus DENSE
// et plus OPAQUE là où la couverture est forte. Sol nu ↔ sol tapissé se distingue
// à l'œil, SANS chiffre. La donnée vient du moteur (source de vérité) : ici on ne
// recalcule RIEN, on rend `cov` tel quel.
//
// 📖 Pédagogie — MÊME patron que LitterLayer : UN seul CanvasItem redessine tout
// dans son _Draw (les taches partent en lot, pas un Node2D chacun), la rotation
// D35 est gratuite (re-projection par WorldToScreen/Offset à chaque dessin), et le
// jitter est STABLE (hash, zéro Random — philo #3) : le tapis ne frétille pas. Le
// tapis est inerte entre deux snapshots → on ne QueueRedraw qu'à l'arrivée d'un
// snapshot et au basculement de LOD.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class CouvertureLayer : Node2D
	{
		// Vert de couvre-sol frais (trèfle/violette), teinte sobre : on lit « le sol
		// est tapissé », pas un signal UI criard. Un poil désaturé pour rester sous le
		// bois des plantes qui poussent par-dessus.
		private static readonly Color TapisColor = new Color("5a8f3c");

		// LOD : le tapis est un détail de sol qu'on lit en s'approchant (comme la
		// litière) — invisible en vue d'ensemble. Un palier réglable au F5.
		private const float MinZoom = 1f;
		// Marge de culling (px canvas) : couvre l'étalement du jitter d'un plot.
		private const float CullMarginPx = 48f;
		// Étalement du semis DANS le plot (un plot = 50 cm) : on reste dans le losange.
		private const float SpreadCm = 20f;
		// Opacité d'une tache : plancher (même un début de tapis se voit) + part ∝ cov.
		private const float AlphaFloor = 0.10f;
		private const float AlphaSpan  = 0.45f;
		// Nombre de taches à couverture pleine (densité du semis) — cov module de 1 à ce max.
		private const int SpecksMax = 7;

		// Un plot tapissé. Position MONDE du centre (cm) ; `Cov` ∈ ]0,1] pilote densité
		// et opacité ; `Hash` = graine déterministe du jitter (stable inter-frames).
		private struct Patch
		{
			public float Cx, Cy;
			public float Cov;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		// Hash djb2-xor (même choix que LitterLayer/MacroLife : jamais GetHashCode
		// pour du visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>
		/// Applique le bloc `couverture` d'un snapshot (liste creuse par tuile,
		/// 0.5.19). `origins` = origin_cm par tuile (le même cache que plantes/litière).
		/// Reconstruction simple : le tapis est inerte (pas de diff/fondu à tenir) et
		/// un snapshot ne tombe qu'à la semaine — pas de churn.
		/// </summary>
		public void SetCouverture(GDict couverture, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			foreach (var tileKv in couverture)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.5.19 : [r, c, cov].
					var e = pv.AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float cov = Mathf.Clamp((float)e[2].AsDouble(), 0f, 1f);
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// WorldToScreen, jamais une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Cov = cov,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// Le tapis ne s'anime pas : on ne redessine qu'au basculement de LOD.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version)
			{
				_lastZoomOk = zoomOk;
				_margeVersion = MargeVue.Version;   // pan/zoom : cadre ré-ancré
				QueueRedraw();
			}
		}

		public override void _Draw()
		{
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;   // hors cadre : rien
				Color col = TapisColor;
				col.A = AlphaFloor + AlphaSpan * p.Cov;
				int specks = 1 + Mathf.RoundToInt((SpecksMax - 1) * p.Cov);
				for (int i = 0; i < specks; i++)
				{
					// Jitter déterministe (même schéma que LitterLayer) : deux tirages
					// du hash (déphasés par i) → angle + distance dans le plot. Projeté
					// en OFFSET → le semis pivote avec la vue sans glisser (D35).
					uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
					float ang = (hi & 0xffff) * (Mathf.Tau / 65536f);
					float dist = SpreadCm * ((hi >> 16 & 0xff) / 255f);
					Vector2 off = WorldView.WorldToScreenOffset(
						dist * Mathf.Cos(ang), dist * Mathf.Sin(ang));
					DrawCircle(center + off, 2.6f, col);
				}
			}
		}
	}
}
