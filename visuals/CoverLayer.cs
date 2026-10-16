// SYMBIOSE — CoverLayer.cs
// Les PLACEHOLDERS des COUVERTURES POSÉES par le joueur (sprint effondrement météo
// ③, rendus au tronçon ④). Le moteur porte deux champs de MILIEU — `couvert_pose`
// (écran physique du VOILE d'hivernage / de la CLOCHE, protège gel + grêle) et
// `ombre_pose` (occultation de l'OMBRIÈRE, rafraîchit contre canicule/sécheresse) —
// exposés au snapshot en listes creuses par tuile `[[r, c, dose], …]` (protocole
// 0.5.43). On en tire une SILHOUETTE lisible, pas un asset : un voile translucide
// blafard tendu sur les plots abrités, un filet d'ombre hachuré sur les plots sous
// ombrière. La donnée vient du moteur (source de vérité) : ici on ne recalcule
// RIEN, on rend `dose` tel quel. Golden NEUTRE (le pont ne réinjecte rien).
//
// 📖 Pédagogie — MÊME patron que CouvertureLayer : UN seul CanvasItem redessine
// tout dans son _Draw (les quads partent en lot, pas un Node2D chacun), la rotation
// D35 est gratuite (re-projection par WorldToScreen à chaque dessin), et l'empreinte
// d'un plot = son losange iso (4 coins projetés). ZIndex ÉLEVÉ (au-dessus des
// plantes) : une couverture est TENDUE PAR-DESSUS le jardin, on doit la voir couvrir
// les pieds. Inerte entre deux snapshots → on ne QueueRedraw qu'à l'arrivée d'un
// snapshot et au basculement de LOD.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class CoverLayer : Node2D
	{
		// Voile/cloche : écran physique clair, translucide (on voit le jardin dessous,
		// tamisé). Ombrière : gris froid plus sombre, hachuré comme un filet tendu.
		private static readonly Color VeilFill  = new Color(0.90f, 0.93f, 0.98f, 0.30f);
		private static readonly Color VeilEdge  = new Color(0.98f, 0.99f, 1f, 0.55f);
		private static readonly Color ShadeFill = new Color(0.28f, 0.32f, 0.40f, 0.26f);
		private static readonly Color ShadeNet  = new Color(0.20f, 0.24f, 0.32f, 0.45f);

		// LOD : la couverture est un détail qu'on lit en s'approchant (comme la
		// litière/le tapis). Un palier réglable au F5.
		private const float MinZoom = 1f;
		private const float CullMarginPx = 64f;

		// Un plot couvert. Position MONDE du COIN nord-ouest (cm) ; `Dose` ∈ ]0,1]
		// module l'opacité ; `Shade` distingue l'ombrière (filet) du voile (drap).
		private struct Patch
		{
			public float X0, Y0;   // coin (o + c·PlotCm, o + r·PlotCm)
			public float Dose;
			public bool Shade;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		/// <summary>
		/// Applique les blocs `couvert_pose` (voile/cloche) et `ombre_pose` (ombrière)
		/// d'un snapshot (listes creuses par tuile, 0.5.43). `origins` = origin_cm par
		/// tuile (le même cache que plantes/litière). Reconstruction simple : la
		/// couverture est inerte (pas de diff/fondu à tenir), un snapshot ne tombe qu'à
		/// la semaine. Lecture TOLÉRANTE : un bloc null (binaire pré-0.5.43) est sauté.
		/// </summary>
		public void SetCovers(GDict couvert, GDict ombre,
							   Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			Ingest(couvert, origins, shade: false);
			Ingest(ombre, origins, shade: true);
			QueueRedraw();
		}

		private void Ingest(GDict block, Dictionary<string, Vector2> origins, bool shade)
		{
			if (block == null) return;
			foreach (var tileKv in block)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.5.43 : [r, c, dose].
					var e = pv.AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float dose = Mathf.Clamp((float)e[2].AsDouble(), 0f, 1f);
					_patches.Add(new Patch
					{
						X0 = o.X + c * WorldView.PlotCm,
						Y0 = o.Y + r * WorldView.PlotCm,
						Dose = dose,
						Shade = shade,
					});
				}
			}
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// La couverture ne s'anime pas : redraw au seul basculement de LOD.
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
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);   // cadre commun stable (T4)
			float pc = WorldView.PlotCm;
			foreach (var p in _patches)
			{
				// Les 4 coins du plot projetés → losange iso (l'empreinte du plot à
				// l'écran). x = est (colonnes), y = sud (lignes) : convention
				// WorldToScreen, jamais une 2ᵉ (leçon D2).
				Vector2 nw = WorldView.WorldToScreen(p.X0, p.Y0);
				Vector2 ne = WorldView.WorldToScreen(p.X0 + pc, p.Y0);
				Vector2 se = WorldView.WorldToScreen(p.X0 + pc, p.Y0 + pc);
				Vector2 sw = WorldView.WorldToScreen(p.X0, p.Y0 + pc);
				// Culling par le centre du losange.
				Vector2 center = (nw + se) * 0.5f;
				if (!vis.HasPoint(center)) continue;
				var quad = new Vector2[] { nw, ne, se, sw };

				if (p.Shade)
				{
					Color fill = ShadeFill; fill.A *= 0.5f + 0.5f * p.Dose;
					DrawColoredPolygon(quad, fill);
					// Filet : deux hachures diagonales (indice de « treillis d'ombre »).
					Color net = ShadeNet; net.A *= p.Dose;
					DrawLine((nw + ne) * 0.5f, (sw + se) * 0.5f, net, 1.5f);
					DrawLine((nw + sw) * 0.5f, (ne + se) * 0.5f, net, 1.5f);
				}
				else
				{
					Color fill = VeilFill; fill.A *= 0.5f + 0.5f * p.Dose;
					DrawColoredPolygon(quad, fill);
					// Liseré clair : le drap accroche la lumière sur ses arêtes.
					Color edge = VeilEdge; edge.A *= p.Dose;
					DrawPolyline(new Vector2[] { nw, ne, se, sw, nw }, edge, 1.5f);
				}
			}
		}
	}
}
