// SYMBIOSE — PuddleLayer.cs
// L'EAU DE SURFACE et le MARÉCAGE au sol (sprint HYDROLOGIE & MARÉCAGES ⑧). Deux
// facettes d'une même responsabilité — « le sol est mouillé » — tirées de deux
// blocs creux du snapshot, tous deux PUREMENT lus (le moteur est source de vérité,
// ici on ne recalcule aucune hydrologie) :
//
//   · FLAQUE (bloc `eau_surface`, liste creuse `[[r, c, lame], …]`, 0.5.18) : une
//     LAME d'eau translucide bleutée sur le losange du plot, plus profonde/opaque
//     là où `lame` est haute (∝ profondeur, bornée HUM_CAP=3). Un liseré clair
//     simule le miroitement. La flaque naît dans les CREUX du micro-relief → on la
//     RECALE sur la surface extrudée (altitude + épaisseur, D57/①) via
//     WorldView.ReliefRiseAtPlot : elle brille au fond de la cuvette, pas suspendue.
//
//   · MARÉCAGE (bloc `marais`, liste creuse `[[r, c, marais, etat], …]`, 0.5.27) :
//     un voile SOMBRE tourbeux sur le losange, opacité ∝ `marais_memory` (la
//     mémoire du milieu). Le sol « noircit » là où la tourbe s'installe (philo #5 :
//     indice diégétique, pas un chiffre). Dessous de la flaque (le marais est le
//     milieu, l'eau la surface).
//
// 📖 Pédagogie — MÊME patron que CouvertureLayer/LitterLayer : UN CanvasItem
// redessine tout dans son _Draw (losanges en lot, pas un Node2D par plot), la
// rotation D35 est gratuite (re-projection par WorldToScreen à chaque dessin), et
// l'ensemble est inerte entre snapshots → on ne QueueRedraw qu'à l'arrivée d'un
// snapshot (l'eau ne s'anime pas ici — le miroitement est statique, calibrage F5).

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class PuddleLayer : Node2D
	{
		// Bleu d'eau stagnante (mare/flaque), froid et un peu vert (eau de sol, pas
		// piscine). L'alpha se règle par plot ∝ profondeur.
		private static readonly Color EauColor = new Color("2f6a8f");
		// Liseré de miroitement : bleu clair posé sur l'arête nord du losange.
		private static readonly Color MiroirColor = new Color("9fc8e0");
		// Voile de tourbe : brun-noir humide. Le marais assombrit le sol.
		private static readonly Color TourbeColor = new Color("241d16");

		// Borne physique de la lame (HUM_CAP côté moteur) : normalise la profondeur
		// → opacité. Une lame pleine sature l'opacité, pas au-delà (échelle stable).
		private const float LameMax = 3f;
		// Opacité d'une flaque : plancher (une flaque naissante se voit) + part ∝
		// profondeur normalisée. Bornée < 1 : on garde le sol lisible dessous.
		private const float EauAlphaFloor = 0.28f;
		private const float EauAlphaSpan  = 0.45f;
		// Opacité du voile de marais : part ∝ marais_memory (∈ ]MARAIS_OFF, 1]).
		// Plafond modéré : la tourbe teinte, elle n'efface pas le sol.
		private const float MaraisAlphaMax = 0.5f;

		// LOD : la flaque/le marais se lisent dès la vue d'ensemble (l'eau est un
		// fait de PAYSAGE, pas un détail de sol comme la litière). Visible partout.
		private const float MinZoom = 0.5f;
		private const float CullMarginPx = 48f;

		// Un plot mouillé. Position MONDE du centre (cm) + offset relief (px, vers le
		// haut) recalé au plot ; `Depth` = lame normalisée (flaque) OU intensité de
		// marais ; `IsMarais` distingue les deux voiles au dessin.
		private struct Wet
		{
			public float Cx, Cy;
			public float RisePx;
			public float Depth;
			public bool IsMarais;
		}

		private readonly List<Wet> _flaques = new();
		private readonly List<Wet> _marais = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		// Référence à la vue pour le recalage relief (ReliefRiseAtPlot) : la flaque
		// se pose SUR la surface extrudée, comme les plantes. Posée à la construction.
		private WorldView _view;
		public void Init(WorldView view) => _view = view;

		/// <summary>Applique les blocs `marais` (0.5.27) PUIS `eau_surface` (0.5.18)
		/// d'un snapshot. Reconstruction simple (inerte entre snapshots, pas de
		/// diff/fondu à tenir) ; `origins` = origin_cm par tuile (cache partagé).
		/// L'un ou l'autre bloc peut être absent (snapshot ancien) → liste vide.</summary>
		public void SetWater(GDict eauSurface, GDict marais,
							 Dictionary<string, Vector2> origins)
		{
			_flaques.Clear();
			_marais.Clear();
			// MARÉCAGE d'abord (dessous) : `[r, c, marais, etat]`. On lit l'intensité
			// (marais_memory) pour l'opacité ; `etat` (hystérèse) n'est pas rendu ici
			// (l'intensité continue suffit à la lecture diégétique, philo #5).
			if (marais != null)
				foreach (var tileKv in marais)
				{
					string tileId = tileKv.Key.AsString();
					if (!origins.TryGetValue(tileId, out Vector2 o)) continue;
					foreach (var pv in tileKv.Value.AsGodotArray())
					{
						var e = pv.AsGodotArray();
						int r = e[0].AsInt32(), c = e[1].AsInt32();
						float m = Mathf.Clamp((float)e[2].AsDouble(), 0f, 1f);
						_marais.Add(MakeWet(tileId, o, r, c, m, true));
					}
				}
			// FLAQUE ensuite (dessus) : `[r, c, lame]`. Profondeur normalisée.
			if (eauSurface != null)
				foreach (var tileKv in eauSurface)
				{
					string tileId = tileKv.Key.AsString();
					if (!origins.TryGetValue(tileId, out Vector2 o)) continue;
					foreach (var pv in tileKv.Value.AsGodotArray())
					{
						var e = pv.AsGodotArray();
						int r = e[0].AsInt32(), c = e[1].AsInt32();
						float lame = Mathf.Clamp((float)e[2].AsDouble() / LameMax, 0f, 1f);
						_flaques.Add(MakeWet(tileId, o, r, c, lame, false));
					}
				}
			QueueRedraw();
		}

		// Fabrique un plot mouillé : centre MONDE (convention WorldToScreen : x = est
		// = colonnes, y = sud = lignes, leçon D2) + offset relief recalé au plot.
		private Wet MakeWet(string tileId, Vector2 o, int r, int c, float depth,
							bool isMarais) => new Wet
		{
			Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
			Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
			RisePx = _view != null ? _view.ReliefRiseAtPlot(tileId, r, c) : 0f,
			Depth = depth,
			IsMarais = isMarais,
		};

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// Inerte entre snapshots : on ne redessine qu'au basculement de LOD.
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
			if (WorldView.CurrentZoom < MinZoom) return;
			if (_flaques.Count == 0 && _marais.Count == 0) return;
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			// Marais SOUS la flaque (le milieu d'abord, l'eau ensuite).
			foreach (var w in _marais) DrawWet(w, vis);
			foreach (var w in _flaques) DrawWet(w, vis);
		}

		// Dessine un losange mouillé au plot, recalé de RisePx vers le haut (surface
		// du relief). Le losange reprend les cotes de MakeLozenge du sol (iso 2:1) →
		// il épouse exactement le plot.
		private void DrawWet(Wet w, Rect2 vis)
		{
			Vector2 ctr = WorldView.WorldToScreen(w.Cx, w.Cy)
						  - new Vector2(0f, w.RisePx);
			if (!vis.HasPoint(ctr)) return;
			Vector2 n = new(0f, -WorldView.TileHPx / 2f);
			Vector2 e = new(WorldView.TileWPx / 2f, 0f);
			Vector2 s = new(0f, WorldView.TileHPx / 2f);
			Vector2 o = new(-WorldView.TileWPx / 2f, 0f);
			if (w.IsMarais)
			{
				Color col = TourbeColor;
				col.A = MaraisAlphaMax * w.Depth;
				_lot.Polygone(new[] { ctr + n, ctr + e, ctr + s, ctr + o }, col);
				return;
			}
			// Flaque : lame bleutée ∝ profondeur + liseré clair sur l'arête nord
			// (miroitement statique, calibrage F5).
			Color eau = EauColor;
			eau.A = EauAlphaFloor + EauAlphaSpan * w.Depth;
			_lot.Polygone(new[] { ctr + n, ctr + e, ctr + s, ctr + o }, eau);
			Color mir = MiroirColor;
			mir.A = 0.35f * w.Depth;
			_lot.Ligne(ctr + o * 0.6f + n * 0.4f, ctr + e * 0.6f + n * 0.4f, mir, 1f);
		}
	}
}
