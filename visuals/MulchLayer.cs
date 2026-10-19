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

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class MulchLayer : Node2D
	{
		// Couleur par NATURE de mulch (NATURES_MULCH côté moteur). Teintes de matière
		// sèche, sobres — on lit « couverture de sol », pas un signal UI :
		//  · paille = jaune-doré (chaume de céréale) ;
		//  · brf    = brun ligneux (bois raméal fragmenté) ;
		//  · aiguilles = brun-vert sombre (litière de conifère).
		private static readonly Dictionary<string, Color> NatureColor = new()
		{
			["paille"]    = new Color("cbb35a"),
			["brf"]       = new Color("6e5334"),
			["aiguilles"] = new Color("5a6340"),
		};
		private static readonly Color NatureInconnue = new Color("9a9060");

		// LOD : invisible en vue d'ensemble (le mulch est un détail de sol qu'on lit
		// en s'approchant), MÊME palier que la litière (2×) — la couverture de sol est
		// un indice « gros ». Réglable au F5.
		private const float MinZoom = 2f;
		// Marge de culling (px canvas) : couvre l'étalement des brins d'un plot.
		private const float CullMarginPx = 48f;
		// Étalement des brins dans le plot, en cm (un plot = 50 cm) : on reste DANS le
		// losange du plot (±20 cm autour du centre) — un peu plus large que la litière
		// (le paillage COUVRE le plot, il ne fait pas un tas).
		private const float SpreadCm = 20f;
		// Densité de brins : un tapis plein à profondeur 1. Plancher à 3 brins (une
		// couverture ténue se voit déjà), plafond ∝ profondeur.
		private const int SpecksFloor = 3;
		private const int SpecksSpan = 7;
		// Opacité : plancher (une fine couche se voit) + part ∝ profondeur (un mulch
		// épais masque le sol).
		private const float AlphaFloor = 0.20f;
		private const float AlphaSpan  = 0.45f;

		// Un plot mulché. Position MONDE du centre (cm) ; la nature fixe la couleur,
		// la profondeur le nombre de brins et l'opacité. `Hash` = graine déterministe
		// du jitter (stable inter-frames et sessions — jamais de Random, philo #3).
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
		/// Applique le bloc `paillage` d'un snapshot (liste creuse par tuile,
		/// protocole 0.5.20). `origins` = origin_cm par tuile (le même cache que
		/// plantes/litière/macro). Reconstruction simple : le mulch est inerte (pas
		/// de diff/fondu à tenir) et un snapshot ne tombe qu'à la semaine.
		/// </summary>
		public void SetPaillage(GDict paillage, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
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
					float depth = (float)e[2].AsDouble();
					string nature = e[3].AsString();
					float d = Mathf.Clamp(depth, 0f, 1f);
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// FindPlot/WorldToScreen, pas une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Col = NatureColor.TryGetValue(nature, out var col) ? col : NatureInconnue,
						Specks = SpecksFloor + Mathf.RoundToInt(SpecksSpan * d),
						Alpha = AlphaFloor + AlphaSpan * d,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// Le mulch ne s'anime pas : on ne redessine qu'au basculement de LOD
			// (zoom franchit MinZoom) — sinon le canvas dort.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version)
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
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;   // hors cadre : rien
				Color col = p.Col;
				col.A = p.Alpha;
				for (int i = 0; i < p.Specks; i++)
				{
					// Jitter déterministe : deux tirages du hash (déphasés par i)
					// → angle + distance dans le plot. Projeté en OFFSET (vecteur)
					// → le tapis pivote avec la vue sans glisser de 20 m (D35).
					uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
					float ang = (hi & 0xffff) * (Mathf.Tau / 65536f);
					float dist = SpreadCm * ((hi >> 16 & 0xff) / 255f);
					Vector2 off = WorldView.WorldToScreenOffset(
						dist * Mathf.Cos(ang), dist * Mathf.Sin(ang));
					// Brin = court segment (≠ point de litière) : une couverture de
					// mulch est faite de brins couchés, pas de granules. Orientation
					// dérivée du même hash → tapis « fibreux » cohérent.
					float bl = 3.2f;
					Vector2 dir = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)) * bl;
					_lot.Ligne(center + off - dir, center + off + dir, col, 1.4f);
				}
			}
		}
	}
}
