// SYMBIOSE — MulchLayer.cs
// Le MULCH au sol (sprint équilibre invasion ⑧, D69) : la couche de PAILLAGE
// déposée par le geste `pailler` et exposée en LECTURE par le snapshot
// (`paillage[tile] = [[r, c, profondeur, nature], …]`, protocole 0.5.20). C'est le
// levier permacole anti-adventice RENDU VISIBLE : là où le sol est mulché, la levée
// férale est étouffée — on doit VOIR la couverture pour lire l'écologie (philo #5).
//
// 📖 Pédagogie — MÊME patron que LitterLayer (et MacroLife) : UN seul CanvasItem
// redessine tout dans son _Draw (les brins partent en lot au renderer, pas un
// Node2D par plot). La rotation D35 est gratuite — on (re)projette par
// WorldToScreen / Offset à chaque dessin. Le mulch est INERTE (matière au sol qui
// ne s'anime pas) : on ne QueueRedraw qu'à l'arrivée d'un snapshot et au
// basculement de LOD. Différence avec la litière : le mulch est une couverture
// DENSE et RÉGULIÈRE (un tapis, pas des amas épars), teintée par le MATÉRIAU et
// d'autant plus opaque/dense que la profondeur est grande.
//
// 📖 Pédagogie — pourquoi une couche distincte de LitterLayer : la litière est de
// la nécromasse SPONTANÉE (feuilles/fruits qui tombent) ; le paillage est un GESTE
// DÉLIBÉRÉ du joueur. Sémantique différente, source différente (bloc snapshot
// différent), rendu différent (tapis régulier vs amas). On ne mélange pas les deux.
//
// GESTES LISIBLES ③ (conception §3) : le paillis COUVRE TOUT LE PLOT (un losange de
// matière, opaque ∝ profondeur) et chaque nature a sa TEXTURE — paille en brins dorés,
// BRF en copeaux bien visibles, aiguilles en traits fins serrés, feuilles en taches
// rousses. Il se pose SUR le relief (ReliefRiseAtPlot), comme les flaques. Quand la
// profondeur d'un plot AUGMENTE entre deux snapshots (fait moteur : quelqu'un a
// paillé), une courte chute de brins le montre — transition, pas invention. Le dessin
// des textures vit dans MulchMotifs.cs.

using Godot;
using System;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class MulchLayer : Node2D
	{
		/// <summary>Teinte d'une nature de mulch — source unique (Palette16), relue par
		/// la rangée de réglages de la palette (world/ReglagePastille.cs).</summary>
		internal static Color CouleurNature(string nature) => MulchMotifs.Base(nature);

		// LOD : invisible en vue d'ensemble (le mulch est un détail de sol qu'on lit
		// en s'approchant), MÊME palier que la litière (2×). Réglable au F5.
		private const float MinZoom = 2f;
		// Marge de culling (px canvas) : couvre le losange d'un plot.
		private const float CullMarginPx = 48f;
		// Pose (③) : durée de la chute de brins (s) et seuil de « profondeur qui monte »
		// (au-dessous : décroissance moteur ou arrondi, pas un geste).
		private const float DureePose = 0.9f;
		private const float HausseMin = 0.02f;

		// Un plot mulché : centre MONDE (cm), clé du relief, matériau, profondeur.
		// `Hash` = graine déterministe des textures (jamais de Random, philo #3).
		private struct Patch
		{
			public float Cx, Cy;
			public string Tile;
			public int R, C;
			public string Nature;
			public float Depth;
			public uint Hash;
			public float Pose;   // instant de début de la chute de brins (−1 : aucune)
		}

		private readonly List<Patch> _patches = new();
		private readonly Dictionary<string, float> _depthAvant = new();
		private bool _premier = true;    // le tout premier snapshot n'anime rien
		private Func<string, int, int, float> _relief;
		private float _t;
		private bool _anime;
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		/// <summary>
		/// Applique le bloc `paillage` d'un snapshot (liste creuse par tuile,
		/// protocole 0.5.20). `origins` = origin_cm par tuile (le même cache que
		/// plantes/litière/macro) ; `relief` = WorldView.ReliefRiseAtPlot.
		/// </summary>
		public void SetPaillage(GDict paillage, Dictionary<string, Vector2> origins,
								Func<string, int, int, float> relief = null)
		{
			_relief = relief;
			_patches.Clear();
			var vus = new Dictionary<string, float>();
			foreach (var tileKv in paillage)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.5.20 : [r, c, profondeur, nature].
					var e = pv.AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float d = Mathf.Clamp((float)e[2].AsDouble(), 0f, 1f);
					string cle = tileId + "|" + r + "|" + c;
					_depthAvant.TryGetValue(cle, out float avant);
					vus[cle] = d;
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// FindPlot/WorldToScreen, pas une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Tile = tileId, R = r, C = c,
						Nature = e[3].AsString(),
						Depth = d,
						Hash = TracesSolMotifs.Hash(cle),
						Pose = !_premier && d > avant + HausseMin ? _t : -1f,
					});
				}
			}
			_depthAvant.Clear();
			foreach (var kv in vus) _depthAvant[kv.Key] = kv.Value;
			_premier = false;
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			_t += (float)delta;
			// Le mulch est inerte : on ne redessine qu'au basculement de LOD, au
			// ré-ancrage du cadre (pan/zoom) et PENDANT une chute de brins.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version || _anime)
			{
				_lastZoomOk = zoomOk;
				_margeVersion = MargeVue.Version;   // pan/zoom : cadre ré-ancré
				QueueRedraw();
			}
		}

		// PLANTE ASSEMBLÉE ① : les primitives partent en UN lot (LotTriangles,
		// ordre des anciens appels conservé) → un seul draw call pour la couche.
		private readonly LotTriangles _lot = new();

		public override void _Draw()
		{
			_lot.Vider();
			_anime = false;
			Peindre();
			_lot.Dessiner(this);
		}

		private void Peindre()
		{
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy)
					- new Vector2(0f, _relief?.Invoke(p.Tile, p.R, p.C) ?? 0f);
				if (!vis.HasPoint(center)) continue;   // hors cadre : rien
				float age = p.Pose < 0f ? DureePose : _t - p.Pose;
				float pose = Mathf.Clamp(age / DureePose, 0f, 1f);
				if (pose < 1f) _anime = true;
				MulchMotifs.Plot(_lot, p.Nature, center, p.Depth, p.Hash, pose);
			}
		}
	}
}
