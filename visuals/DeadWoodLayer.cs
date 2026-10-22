// SYMBIOSE — DeadWoodLayer.cs (sprint « le sol qui respire » ⑧)
// Le BOIS MORT au sol, enfin visible : brindilles, branches et souches posées à
// plat sur les plots qui portent une parcelle `bois` (pont ≥ 0.5.51 : entrée
// `litiere` = [r, c, tissu, masse, age, bois_masse, bois_age_sem, bois_diam_cm]).
// Le bois se lit MÊME quand des feuilles dominent le plot (index 5-7 exposés à part).
//
// Ce que la vue montre (et seulement ça — la décompo elle-même est calculée par
// Python, `fields/ecofields/litiere.py`) :
//   - la GROSSEUR (index 7) choisit la silhouette : brindilles (< 1 cm), branche
//     (1-10 cm), souche (≥ 10 cm) ;
//   - la MASSE (index 5) la taille : un tas épais est plus long, plus fourni ;
//   - l'ÂGE (index 6) le STADE : fraîche (écorce brune) → grise → moussue →
//     fragments qui fondent dans le sol.
// L'âge seul ne dit pas où en est une souche : à âge égal une brindille est déjà
// en miettes quand un tronc est à peine gris. L'échelle de temps VISUELLE est donc
// étirée par la grosseur, (1 + d) / 1,5 an — la même allure que la décompo Python
// (`facteur_grosseur`) pour que l'image ne contredise pas le moteur. Elle ne sert
// qu'à la teinte : la masse qui disparaît, c'est Python qui la retire.
//
// 📖 Pédagogie — MÊME patron batché que LitterLayer : UN CanvasItem, toutes les
// pièces de bois partent en UN lot de triangles (LotTriangles = un draw call),
// orientation et jitter par HASH du plot (zéro Random — philo #3 : une branche ne
// pivote pas d'une frame à l'autre). Inerte : redessiné au snapshot, au
// basculement de LOD et au ré-ancrage pan/zoom (MargeVue), jamais par frame.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class DeadWoodLayer : Node2D
	{
		// LOD aligné sur la litière (détail de sol qu'on lit en s'approchant).
		private const float MinZoom = 2f;
		private const float CullMarginPx = 64f;
		// En deçà, la parcelle est une miette invisible (évite des traits fantômes).
		private const float MasseMin = 0.02f;
		// Masse qui « remplit » la pièce (longueur et nombre de rameaux plafonnés).
		private const float MasseRef = 1.5f;
		// Diamètres de bascule de silhouette (cm) — mêmes seuils que le récit du pont.
		private const float DiamBranche = 1f, DiamSouche = 10f;
		// Une souche dessinée ne dépasse pas ce diamètre (un plot = 50 cm).
		private const float DiamDessinMax = 30f;

		// Palette des stades (teintes de sous-bois sobres, cf. LitterLayer).
		private static readonly Color Fraiche = new("6e4a2e");   // écorce brune
		private static readonly Color Grise = new("8a8274");     // bois lavé, gris
		private static readonly Color Moussue = new("6c7650");   // gris verdi
		private static readonly Color Humus = new("4a3a2a");     // miettes brunes
		private static readonly Color Mousse = new("7fa040");    // touffes de mousse
		private static readonly Color Coeur = new("b89a6a");     // section claire d'une souche
		// Ombre portée au sol (1 px sous chaque pièce) : sans elle, le bois brun se
		// perd sur la terre brune (capture VM ⑧ : brindilles quasi invisibles).
		private static readonly Color OmbreSol = new(0.16f, 0.10f, 0.06f, 0.55f);

		private struct Piece
		{
			public float Cx, Cy;     // centre MONDE (cm), déjà jitté dans le plot
			public float Ang;        // orientation au sol (rad, repère monde)
			public float Diam;       // cm (grosseur moyenne pondérée, pont)
			public float Sat;        // masse / MasseRef ∈ [0, 1]
			public float Stade;      // 0 fraîche → 1 grise → 2 moussue → 3 miettes
			public uint Hash;
		}

		private readonly List<Piece> _pieces = new();
		private readonly LotTriangles _lot = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;

		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>Applique le bloc `litiere` (lecture tolérante : un pont
		/// pré-0.5.51 n'a pas les index 5-7 → rien ; pré-0.5.55, pas de diamètre →
		/// branche par défaut 0,5 cm comme le moteur).</summary>
		public void SetLitiere(GDict litiere, Dictionary<string, Vector2> origins)
		{
			_pieces.Clear();
			foreach (var tileKv in litiere)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o)) continue;
				using var plots = tileKv.Value.AsGodotArray();
				for (int i = 0; i < plots.Count; i++)
				{
					using var e = LectureSnap.Tab(plots, i);
					if (e.Count < 7) continue;
					float masse = (float)e[5].AsDouble();
					if (masse < MasseMin) continue;
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float age = (float)e[6].AsDouble();
					float diam = e.Count > 7 ? (float)e[7].AsDouble() : 0f;
					if (diam <= 0f) diam = 0.5f;   // BOIS_DIAM_DEFAUT du moteur
					uint h = HashKey(tileId + "|" + r + "|" + c);
					// Jitter ±12 cm et orientation libre, tirés du hash.
					float jx = ((h & 0xff) / 255f - 0.5f) * 24f;
					float jy = ((h >> 8 & 0xff) / 255f - 0.5f) * 24f;
					_pieces.Add(new Piece
					{
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm + jx,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm + jy,
						Ang = (h >> 16 & 0xffff) * (Mathf.Tau / 65536f),
						Diam = diam,
						Sat = Mathf.Clamp(masse / MasseRef, 0f, 1f),
						Stade = Stade(age, diam),
						Hash = h,
					});
				}
			}
			QueueRedraw();
		}

		// Stade visuel ∈ [0, 3] : âge rapporté à l'échelle de temps de la grosseur
		// (en-tête). 0 = fraîche, 1 = grise (~1/4 de vie), 2 = moussue, 3 = miettes.
		private static float Stade(float ageSem, float diam)
			=> Mathf.Clamp(ageSem / (52f * (1f + diam) / 1.5f) * 3f, 0f, 3f);

		private static Color Teinte(float stade)
			=> stade < 1f ? Fraiche.Lerp(Grise, stade)
			 : stade < 2f ? Grise.Lerp(Moussue, stade - 1f)
			 : Moussue.Lerp(Humus, stade - 2f);

		public override void _Process(double delta)
		{
			if (!Visible) return;
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
			if (_pieces.Count > 0 && WorldView.CurrentZoom >= MinZoom)
			{
				Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
				// Un trait ne descend jamais sous 1 px du SubViewport (lisible).
				float px1 = 1f / WorldView.CurrentZoom;
				foreach (var p in _pieces)
				{
					Vector2 centre = WorldView.WorldToScreen(p.Cx, p.Cy);
					if (!vis.HasPoint(centre)) continue;
					if (p.Diam >= DiamSouche) Souche(p, centre, px1);
					else if (p.Diam >= DiamBranche) Branche(p, centre, px1);
					else Brindilles(p, centre, px1);
				}
			}
			_lot.Dessiner(this);
		}

		// Vecteur ÉCRAN d'un déplacement MONDE de `cm` selon l'angle `ang` (la
		// pièce pivote avec la vue D35 sans glisser, comme le jitter de la litière).
		private static Vector2 Dir(float ang, float cm)
			=> WorldView.WorldToScreenOffset(cm * Mathf.Cos(ang), cm * Mathf.Sin(ang));

		// Brindilles : 2 à 5 petits rameaux croisés, fins (1 px), 8-16 cm.
		private void Brindilles(Piece p, Vector2 centre, float px1)
		{
			Color col = Teinte(p.Stade);
			int n = 2 + Mathf.RoundToInt(3f * p.Sat);
			for (int i = 0; i < n; i++)
			{
				uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
				float ang = p.Ang + (hi & 0xff) / 255f * Mathf.Pi;
				float lon = 8f + 8f * ((hi >> 8 & 0xff) / 255f);
				if (p.Stade >= 2.5f) lon *= 0.5f;   // miettes : rameaux cassés
				Vector2 off = Dir(ang + 1.3f, 6f * ((hi >> 16 & 0xff) / 255f));
				Vector2 d = Dir(ang, lon * 0.5f);
				Trait(centre + off - d, centre + off + d, col, px1, px1);
			}
		}

		// Branche : un axe épais ∝ grosseur, long ∝ masse (20-45 cm), 1-2 rameaux
		// latéraux. Moussue : touffes vertes sur le dos ; miettes : axe en tronçons.
		private void Branche(Piece p, Vector2 centre, float px1)
		{
			Color col = Teinte(p.Stade);
			float lon = 20f + 25f * p.Sat;
			float larg = Mathf.Max(px1, p.Diam * WorldView.PxPerCmX);
			Vector2 d = Dir(p.Ang, lon * 0.5f);
			if (p.Stade < 2.5f)
				Trait(centre - d, centre + d, col, larg, px1);
			else   // fragments : trois tronçons disjoints, décalés
				for (int k = -1; k <= 1; k++)
				{
					Vector2 m = centre + d * (k * 0.66f) + Dir(p.Ang + 1.57f, 2f * k);
					Trait(m - d * 0.22f, m + d * 0.22f, col, larg, px1);
				}
			// Rameaux latéraux (absents des miettes) : fins, partent de l'axe.
			if (p.Stade < 2.5f)
				for (int k = 0; k < 1 + (p.Sat > 0.5f ? 1 : 0); k++)
				{
					Vector2 depart = centre + d * (k == 0 ? 0.3f : -0.4f);
					float a = p.Ang + (k == 0 ? 0.6f : -0.7f);
					Trait(depart, depart + Dir(a, lon * 0.3f), col, Mathf.Max(px1, larg * 0.4f), px1);
				}
			if (p.Stade >= 1.6f) MousseSur(p, centre, d, larg);
		}

		// Souche / tronc : section (ellipse) claire cernée d'écorce + un court fût.
		// Au-delà de 2,5 : la souche s'affaisse en un tas brun avec mousse.
		private void Souche(Piece p, Vector2 centre, float px1)
		{
			Color col = Teinte(p.Stade);
			float diam = Mathf.Min(p.Diam, DiamDessinMax);
			float rx = diam * 0.5f * WorldView.PxPerCmX;
			float ry = rx * 0.5f;                                 // iso 2:1
			float h = diam * 0.5f * WorldView.PxPerCmZ * (p.Stade < 2.5f ? 1f : 0.3f);
			Vector2 haut = centre - new Vector2(0f, h);
			// Fût : quad vertical entre l'ellipse du sol et celle du haut.
			_lot.Ligne(centre, haut, col, rx * 2f);
			Ellipse(centre, rx, ry, col);
			Ellipse(haut, rx, ry, col);
			if (p.Stade < 2.5f)   // section claire + un cerne (le bois se lit)
			{
				Ellipse(haut, rx * 0.8f, ry * 0.8f, Coeur.Lerp(Grise, Mathf.Min(1f, p.Stade)));
				Ellipse(haut, rx * 0.35f, ry * 0.35f, col);
			}
			if (p.Stade >= 1.6f) MousseSur(p, haut, new Vector2(rx * 0.8f, 0f), Mathf.Max(px1, ry));
		}

		// Un trait de bois posé au sol : son ombre (1 px plus bas) puis lui.
		private void Trait(Vector2 a, Vector2 b, Color col, float larg, float px1)
		{
			Vector2 bas = new(0f, px1);
			_lot.Ligne(a + bas, b + bas, OmbreSol, larg);
			_lot.Ligne(a, b, col, larg);
		}

		// Quelques touffes de mousse (losanges verts) le long d'un segment.
		private void MousseSur(Piece p, Vector2 centre, Vector2 demiAxe, float taille)
		{
			int n = p.Stade >= 2.5f ? 2 : 3;
			float t = Mathf.Max(taille, 1.2f / WorldView.CurrentZoom);
			for (int i = 0; i < n; i++)
			{
				float u = ((p.Hash >> (i * 5) & 0x1f) / 31f) * 1.6f - 0.8f;
				Vector2 m = centre + demiAxe * u - new Vector2(0f, t * 0.4f);
				_lot.Triangle(m + new Vector2(-t, 0f), m + new Vector2(0f, -t * 0.7f), m + new Vector2(t, 0f), Mousse);
				_lot.Triangle(m + new Vector2(-t, 0f), m + new Vector2(t, 0f), m + new Vector2(0f, t * 0.4f), Mousse);
			}
		}

		// Ellipse basse définition (12 secteurs) : à 3-20 px, l'œil n'en voit pas plus.
		private void Ellipse(Vector2 c, float rx, float ry, Color col)
		{
			const int n = 12;
			Vector2 prec = c + new Vector2(rx, 0f);
			for (int i = 1; i <= n; i++)
			{
				float a = i * Mathf.Tau / n;
				Vector2 cour = c + new Vector2(Mathf.Cos(a) * rx, Mathf.Sin(a) * ry);
				_lot.Triangle(c, prec, cour, col);
				prec = cour;
			}
		}
	}
}
