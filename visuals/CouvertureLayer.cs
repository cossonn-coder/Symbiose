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
//
// D106 T5 — UN SEUL TAPIS (D5) : les plantes trop petites pour être lisibles au
// palier courant (PlantRenderer.EnTapis) ne sont plus dessinées seules ; leur
// agrégat par plot (WorldView.Tapis.cs) arrive par SetPetites et se FOND ici avec
// `couverture_sol` : même patch, teinte de l'espèce dominante (saison comprise),
// densité = couverture + aire des petites. Un plot qui porte des petites plantes
// se voit à TOUT palier (une plante reste toujours visible, D4) ; un plot de
// couverture seule garde son LOD d'avant (dès ×1).

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
			public (string, int, int) Cle;   // tuile|ligne|colonne (fusion des petites, T5)
		}

		private readonly List<Patch> _patches = new();

		/// <summary>Agrégat des petites plantes d'un plot (WorldView.Tapis.cs) :
		/// `Fraction` = aire cumulée / aire du plot, `Teinte` = espèce dominante.</summary>
		public readonly record struct Petites(string Tile, int R, int C, float Fraction, Color Teinte);
		private readonly Dictionary<(string, int, int), Petites> _petites = new();
		private readonly HashSet<(string, int, int)> _dejaDessine = new();
		private Dictionary<string, Vector2> _origins;
		// Plot de petites plantes : opacité plancher (la présence se LIT même pour un
		// seul semis) et semis de taches à ≤ ~2,6 px internes (pas plus gros que
		// les plantes qu'il remplace, quel que soit le palier).
		private const float AlphaPetitesMin = 0.55f;
		private const float SpeckRadiusPx = 2.6f;
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
					_patches.Add(NewPatch(tileId, r, c, o, cov));
				}
			}
			QueueRedraw();
		}

		// Un plot (r, c) de la tuile d'origine `o` → patch au centre du plot.
		// x = est (colonnes), y = sud (lignes) — convention WorldToScreen (leçon D2).
		private static Patch NewPatch(string tileId, int r, int c, Vector2 o, float cov) => new()
		{
			Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
			Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
			Cov = cov,
			Hash = HashKey(tileId + "|" + r + "|" + c),
			Cle = (tileId, r, c),
		};

		/// <summary>Agrégat des petites plantes par plot (D106 T5), recalculé par
		/// WorldView au snapshot et au changement de palier — jamais par frame.</summary>
		public void SetPetites(List<Petites> petites, Dictionary<string, Vector2> origins)
		{
			_origins = origins;
			_petites.Clear();
			foreach (var p in petites) _petites[(p.Tile, p.R, p.C)] = p;
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
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			_dejaDessine.Clear();
			// 1) Plots de couverture : fondus avec les petites plantes du même plot.
			foreach (var p in _patches)
			{
				bool aPetites = TryPetites(p, out var pet);
				if (!zoomOk && !aPetites) continue;   // couverture seule : LOD d'avant
				DrawPatch(p, vis, aPetites, pet);
			}
			// 2) Plots de petites plantes SANS couverture moteur (semis isolé).
			if (_origins == null) return;
			foreach (var kv in _petites)
			{
				if (_dejaDessine.Contains(kv.Key)
					|| !_origins.TryGetValue(kv.Value.Tile, out Vector2 o)) continue;
				DrawPatch(NewPatch(kv.Value.Tile, kv.Value.R, kv.Value.C, o, 0f), vis, true, kv.Value);
			}
		}

		// Le plot `p` porte-t-il des petites plantes ? (même clé tuile|ligne|colonne)
		private bool TryPetites(Patch p, out Petites pet)
		{
			if (!_petites.TryGetValue(p.Cle, out pet)) return false;
			_dejaDessine.Add(p.Cle);
			return true;
		}

		// Un patch = un semis de taches au jitter stable. Densité = couverture +
		// aire des petites plantes ; teinte = espèce dominante des petites, sinon
		// le vert de couvre-sol.
		private void DrawPatch(Patch p, Rect2 vis, bool aPetites, Petites pet)
		{
			Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
			if (!vis.HasPoint(center)) return;   // hors cadre : rien
			float dens = Mathf.Clamp(p.Cov + (aPetites ? pet.Fraction : 0f), 0f, 1f);
			Color col = aPetites ? pet.Teinte : TapisColor;
			col.A = AlphaFloor + AlphaSpan * dens;
			if (aPetites) col.A = Mathf.Max(col.A, AlphaPetitesMin);
			int specks = 1 + Mathf.RoundToInt((SpecksMax - 1) * dens) + (aPetites ? 1 : 0);
			float rad = aPetites ? SpeckRadiusPx / Mathf.Max(1f, WorldView.CurrentZoom) : 2.6f;
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
				DrawCircle(center + off, rad, col);
			}
		}
	}
}
