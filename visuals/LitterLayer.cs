// SYMBIOSE — LitterLayer.cs
// La LITIÈRE au sol (décompo·compost ①, vue 03·B) : la couche fraîche de
// nécromasse (feuilles, herbacées, fruits, bois tombés) déposée par le tick et
// exposée en LECTURE par le snapshot (`litiere[tile] = [[r, c, tissu, masse], …]`,
// protocole 0.3.7). Indice écologique DISCRET (philo #5) — surtout PAS une
// heatmap (la heatmap des champs reste F6) : de petits amas semi-transparents
// jitterés au plot, teintés par le tissu DOMINANT, plus ou moins denses selon la
// masse. Le jitter est STABLE (hash, zéro Random — philo #3) : un amas ne
// frétille pas d'une frame à l'autre.
//
// 📖 Pédagogie — MÊME patron que MacroLife : UN seul CanvasItem redessine tout
// dans son _Draw (les amas partent en lot au renderer, pas un Node2D chacun), et
// la rotation D35 est gratuite — on (re)projette par WorldToScreen / Offset à
// chaque dessin. La litière, elle, ne s'anime PAS (matière inerte) : on ne
// QueueRedraw qu'à l'arrivée d'un snapshot et au basculement de LOD.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class LitterLayer : Node2D
	{
		// Couleur par tissu de surface (TISSU_ORDER côté moteur, hors `diffus`
		// qui n'est PAS de la litière de surface et n'est jamais exposé). Teintes
		// terreuses sobres — on lit « matière en décomposition », pas un signal UI.
		private static readonly Dictionary<string, Color> TissuColor = new()
		{
			["feuille"] = new Color("b5893f"),   // ocre — feuillage tombé
			["fleur"]   = new Color("c890a0"),   // rosé fané
			["herbace"] = new Color("c2b066"),   // paille
			["fruit"]   = new Color("a85a32"),   // rouille — fruit au sol
			["bois"]    = new Color("6e4a2e"),   // brun — bois mort / BRF
		};
		private static readonly Color TissuInconnu = new Color("8a8a6a");

		// LOD : invisible en vue d'ensemble (la litière est un détail de sol qu'on
		// lit en s'approchant). Un palier SOUS la vie macro (4) — la nécromasse au
		// sol est un indice plus « gros » qu'un puceron. Réglable au F5.
		private const float MinZoom = 2f;
		// Marge de culling (px canvas) : couvre l'étalement du jitter d'un plot.
		private const float CullMarginPx = 48f;
		// Référence de masse pour saturer la densité d'un amas. Calibrage post-F5
		// (la masse d'une litière fraîche dépend de l'organe tombé) — au-delà,
		// l'amas est « plein » (alpha + nombre de taches plafonnés).
		private const float MasseRef = 2.5f;
		// Étalement du jitter dans le plot, en cm (un plot = 50 cm) : on reste DANS
		// le losange du plot (±18 cm autour du centre).
		private const float SpreadCm = 18f;
		// Opacité d'un amas : plancher (même une trace ténue se voit) + part ∝ masse.
		private const float AlphaFloor = 0.14f;
		private const float AlphaSpan  = 0.42f;

		// Un plot porteur de litière. Position MONDE du centre (cm) ; le tissu
		// dominant fixe la couleur, la masse le nombre de taches et l'opacité.
		// `Hash` = graine déterministe du jitter (stable inter-frames et sessions).
		private struct Patch
		{
			public float Cx, Cy;
			public Color Col;
			public int Specks;
			public float Alpha;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		// Hash djb2-xor (même choix que MacroLife : jamais GetHashCode pour du
		// visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>
		/// Applique le bloc `litiere` d'un snapshot (liste creuse par tuile).
		/// `origins` = origin_cm par tuile (le même cache que plantes/macro).
		/// Reconstruction simple : la litière est inerte (pas de diff/fondu à
		/// tenir) et un snapshot ne tombe qu'à la semaine — pas de churn.
		/// </summary>
		public void SetLitiere(GDict litiere, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			foreach (var tileKv in litiere)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.3.7 : [r, c, tissu_dominant, masse].
					var e = pv.AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					string tissu = e[2].AsString();
					float masse = (float)e[3].AsDouble();
					float sat = Mathf.Clamp(masse / MasseRef, 0f, 1f);
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// FindPlot/WorldToScreen, pas une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Col = TissuColor.TryGetValue(tissu, out var col) ? col : TissuInconnu,
						Specks = 1 + Mathf.RoundToInt(4f * sat),
						Alpha = AlphaFloor + AlphaSpan * sat,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// La litière ne s'anime pas : on ne redessine qu'au basculement de LOD
			// (zoom franchit MinZoom) — sinon le canvas dort.
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
				Color col = p.Col;
				col.A = p.Alpha;
				for (int i = 0; i < p.Specks; i++)
				{
					// Jitter déterministe : deux tirages du hash (déphasés par i)
					// → angle + distance dans le plot. Projeté en OFFSET (vecteur)
					// → l'amas pivote avec la vue sans glisser de 20 m (D35).
					uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
					float ang = (hi & 0xffff) * (Mathf.Tau / 65536f);
					float dist = SpreadCm * ((hi >> 16 & 0xff) / 255f);
					Vector2 off = WorldView.WorldToScreenOffset(
						dist * Mathf.Cos(ang), dist * Mathf.Sin(ang));
					DrawCircle(center + off, 2.2f, col);
				}
			}
		}
	}
}
