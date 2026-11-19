// SYMBIOSE — StrawLitterLayer.cs
// Les TIGES D'HERBACÉE couchées au sol (LISIBILITÉ DU BILAN ③, conception
// `docs/vegetal/sante/conception_lisibilite_bilan.md` §2.3). Sœur de `LeafLitterLayer`
// (tapis de feuilles mortes) : une herbacée morte — poivron, tomate, ortie — ne laisse
// pas des feuilles à plat mais un lit de TIGES couleur paille, qui brunissent puis
// fondent dans l'humus à mesure que le moteur décompose leur masse.
//
// Donnée lue : bloc `litiere` du snapshot, index 9-10 (pont 0.6.23) = masse et âge
// PROPRES de la parcelle `herbace` du plot, même sous un autre tissu dominant. Rien
// n'est calculé ici : la masse règle le nombre de tiges, l'âge leur teinte (philo #5 :
// aucun chiffre, une matière qu'on voit). `LitterLayer` continue de poser ses amas
// abstraits (tous tissus) : les tiges se couchent PAR-DESSUS, comme les feuilles.
//
// 📖 Pédagogie — MÊME patron batché que `LeafLitterLayer` : UN CanvasItem, toutes les
// tiges partent en UN lot de triangles (`LotTriangles`, un draw call pour la couche).
// Le semis est DÉTERMINISTE : chaque tige tire sa place, son angle et son ton d'un
// hash du plot (jamais de Random, jamais GetHashCode — philo #3), donc une tige ne
// saute pas d'une frame ni d'une session à l'autre. La litière est INERTE : on ne
// redessine qu'à l'arrivée d'un snapshot et au ré-ancrage du cadre (pan/zoom).
//
// 📖 Pourquoi un calque À PART plutôt qu'une branche de `LeafLitterLayer` : une feuille
// se dessine en losange à plat (et en silhouette au gros plan, ce qui exige d'hériter
// de `PlantRenderer`) ; une tige est un trait fin. Deux matières, deux dessins — un
// fichier = une responsabilité. Le coût est le même : un semis plafonné par plot.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class StrawLitterLayer : Node2D
	{
		// LOD : visible dès ×1 (zoom de jeu). Sous ZoomTige un grain, au-dessus une tige.
		private const float MinZoom = 1f;
		private const float ZoomTige = 4f;
		private const float CullMarginPx = 64f;

		// Masse `herbace` qui sature le lit de tiges. Mesure ③ (banc `plante_vivante`,
		// seed 42, n=1) : un poivron mort laisse ~1,9-2,2 sur son plot, qui fond à
		// ~0,6 en 12 semaines. MasseRef 1,5 : le tas frais est plein, il s'éclaircit au fil
		// des semaines au lieu de rester plein tant qu'il dépasse la référence.
		private const float MasseRef = 1.5f;
		// En deçà, plus rien à voir (sinon la moindre herbe fanée poserait une tige à vie).
		private const float MasseMin = 0.05f;
		// Semis par plot à saturation : moins de tiges que de feuilles (une tige est
		// plus longue, le tas reste lisible sans boucher le plot).
		private const int MaxGrains = 30, MaxTiges = 22;
		// Le lit couvre le cœur du plot (±20 cm autour du centre, un plot = 50 cm) : un
		// pied mort laisse son tas autour de son collet, pas un tapis jusqu'aux bords.
		private const float SemisDemiCm = 20f;
		private const float GrainPx = 1f;
		// Tige couchée : demi-longueur de 6 à 11 cm (tirée du hash), trait fin.
		private const float TigeDemiMinCm = 6f, TigeDemiSpanCm = 5f;
		private const float TigeLargePx = 0.8f;

		// Dérive vers l'humus (§2.3) : paille blonde fraîche → brun sombre désaturé. Tons
		// du semis du plus clair au plus roux (l'œil lit un mélange de brins, pas un aplat).
		private static readonly Color[] TonsPaille =
		{
			new("e0c878"), new("d1b562"), new("bfa052"), new("a88a48"),
		};
		private static readonly Color Humus = new("5a4630");
		// Âge (semaines) où la tige a pris la teinte de l'humus. Mesure ③ : à 12 semaines
		// il reste ~30 % de la masse déposée [seed 42, n=1] — un tas brun, presque sol.
		// Calibrage F5.
		private const float AgeHumusSem = 12f;
		private const int NbStades = 4;
		private static readonly Color[,] TonsSemis = CalculerTons();
		private static Color[,] CalculerTons()
		{
			var t = new Color[NbStades, TonsPaille.Length];
			for (int s = 0; s < NbStades; s++)
				for (int i = 0; i < TonsPaille.Length; i++)
					t[s, i] = TonsPaille[i].Lerp(Humus, s / (NbStades - 1f));
			return t;
		}

		// Un plot porteur de tiges : centre MONDE (cm), saturation de masse, stade de
		// teinte, graine du semis.
		private struct Patch
		{
			public float Cx, Cy;
			public float Sat;
			public int Stade;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)
		private readonly LotTriangles _lot = new();

		// Hash djb2-xor (même choix que LitterLayer/LeafLitterLayer : visuel stable).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>Applique le bloc `litiere` (liste creuse par tuile) en ne retenant
		/// que la masse `herbace` (index 9-10, pont 0.6.23). Pont plus ancien → aucune
		/// tige (lecture tolérante, `LitterLayer` garde ses amas).</summary>
		public void SetLitiere(GDict litiere, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			foreach (var tileKv in litiere)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				using var plots = tileKv.Value.AsGodotArray();
				for (int i = 0; i < plots.Count; i++)
				{
					using var e = LectureSnap.Tab(plots, i);   // PERF VUE ④ : sans finaliseur
					if (e.Count <= 10) continue;
					float masse = (float)e[9].AsDouble();
					if (masse < MasseMin) continue;
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float decomp = Mathf.Clamp((float)e[10].AsDouble() / AgeHumusSem, 0f, 1f);
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention FindPlot/WorldToScreen.
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Sat = Mathf.Clamp(masse / MasseRef, 0f, 1f),
						Stade = Mathf.RoundToInt(decomp * (NbStades - 1)),
						Hash = HashKey(tileId + "|" + r + "|" + c + "|tige"),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// Inerte : ne redessiner qu'au basculement de LOD et au ré-ancrage du cadre.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version)
			{
				_lastZoomOk = zoomOk;
				_margeVersion = MargeVue.Version;
				QueueRedraw();
			}
		}

		public override void _Draw()
		{
			_lot.Vider();
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			bool tige = WorldView.CurrentZoom >= ZoomTige;
			int max = tige ? MaxTiges : MaxGrains;
			// Base projetée de la vue : la tige pivote avec elle sans glisser (D35).
			Vector2 bx = WorldView.WorldToScreenOffset(1f, 0f);
			Vector2 by = WorldView.WorldToScreenOffset(0f, 1f);
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;
				int semis = Mathf.Max(1, Mathf.RoundToInt(max * p.Sat));
				for (int i = 0; i < semis; i++)
				{
					uint h = LeafFallLayer.Melange(p.Hash + (uint)i * 0x9e3779b1u);
					float dx = SemisDemiCm * ((h & 0xff) / 127.5f - 1f);
					float dy = SemisDemiCm * ((h >> 8 & 0xff) / 127.5f - 1f);
					Vector2 c = center + bx * dx + by * dy;
					Color col = TonsSemis[p.Stade, (h >> 16) % (uint)TonsPaille.Length];
					if (!tige) { _lot.Grain(c, GrainPx, col); continue; }
					// Tige couchée : angle et longueur tirés du hash, trait fin. Un liseré
					// plus sombre décalé d'un demi-trait donne le relief d'un brin rond.
					float a = (h >> 18 & 0xff) * (Mathf.Tau / 256f);
					float demi = TigeDemiMinCm + TigeDemiSpanCm * ((h >> 26) / 63f);
					Vector2 d = (bx * Mathf.Cos(a) + by * Mathf.Sin(a)) * demi;
					Vector2 ombre = new(0f, TigeLargePx * 0.5f);
					_lot.Ligne(c - d + ombre, c + d + ombre, col.Darkened(0.35f), TigeLargePx);
					_lot.Ligne(c - d, c + d, col, TigeLargePx);
				}
			}
			_lot.Dessiner(this);
		}
	}
}
