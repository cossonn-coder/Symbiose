// SYMBIOSE — ForagerLayer.Bord.cs (LISIÈRE NUE ② — les butineurs des colonies de bord)
// Partial de ForagerLayer : les insectes qui volent au-dessus des colonies de fleurs de
// la ceinture. Le COMBIEN vient du pont (`butineurs` par colonie : 0 sans floraison) ;
// le vol est une pure mise en scène, sans effet sur le moteur.
//
// 📖 Pédagogie — aucun état par insecte, comme une table de phase en embarqué : le n-ᵉ
// insecte d'une colonie et l'horloge donnent sa fleur, son saut, sa position. L'horloge
// `_tBord` ne court que si le temps du jeu court : en pause, ils restent suspendus.
// Même lot que les butineurs du jardin : au palier ×4, aucun draw call de plus.
//
// Ces insectes ne sont pas dans `_entries` : ni le survol, ni la piqûre, ni le pollen ne
// les voient (ce sont des bêtes de la lisière, hors du jardin que le joueur soigne).

using Godot;
using System;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;
using GArray = Godot.Collections.Array;

namespace Symbiose
{
	public partial class ForagerLayer
	{
		private const float BordZoomMin = 1f;     // en dessous, un point sur une fleur : illisible
		private const float BordZoomMax = 4f;     // au-delà, le décor n'est plus peint
		private const int BordFleurs = 4;         // fleurs visitées en boucle par un insecte
		private const float BordRayonVol = 0.85f; // part de l'ellipse où il vole
		private const float BordHauteurPx = 5f;   // au-dessus des fleurs, px canvas

		private static readonly string[] GuildesBord = { "abeille", "abeille", "syrphe", "bourdon", "papillon", "osmie" };

		private readonly record struct ColonieVol(int Cote, float U, float Depth, float Ru, float Rd, int N, uint Graine);
		private readonly List<ColonieVol> _coloniesVol = new();
		private double _tBord;
		private bool _bordVuAvant;

		/// <summary>Le temps du jeu court-il ? (posé par WorldView, Saison seulement).</summary>
		public Func<bool> TempsCourt;

		private bool BordVisible => _coloniesVol.Count > 0
			&& WorldView.CurrentZoom >= BordZoomMin && WorldView.CurrentZoom <= BordZoomMax;

		/// <summary>Le bloc `ceinture` du snapshot : ne garde que les colonies peuplées cette
		/// semaine. `null` (monde sans périphérie) : plus aucun insecte de bord.</summary>
		public void SetColoniesBord(GArray ceinture)
		{
			_coloniesVol.Clear();
			if (ceinture == null) return;
			foreach (var sv in ceinture)
			{
				GDict d = sv.AsGodotDictionary();
				if (!d.ContainsKey("colonies")) continue;
				int cote = d["cote"].AsInt32();
				foreach (var cv in d["colonies"].AsGodotArray())
				{
					GDict c = cv.AsGodotDictionary();
					int n = c.ContainsKey("butineurs") ? c["butineurs"].AsInt32() : 0;
					if (n > 0)
						_coloniesVol.Add(new ColonieVol(cote, (float)c["u"].AsDouble(), (float)c["depth"].AsDouble(),
							(float)c["ru"].AsDouble(), (float)c["rd"].AsDouble(), n, (uint)c["graine"].AsInt64()));
				}
			}
		}

		private void ProcessBord(double delta)
		{
			if (TempsCourt?.Invoke() ?? true) _tBord += delta;
			bool vu = BordVisible;
			if (vu != _bordVuAvant) { _bordVuAvant = vu; QueueRedraw(); }
		}

		// Un point de vol dans l'ellipse de la colonie : la i-ᵉ fleur de cet insecte.
		private static Vector2 FleurDeVol(ColonieVol c, uint graine, int i)
		{
			uint h = DecorLayer.Melange(graine ^ (uint)(i + 1) * 0x9e3779b1u);
			float a = (h & 0xffff) / 65536f * Mathf.Tau;
			float r = BordRayonVol * Mathf.Sqrt((h >> 16) / 65536f);
			return new Vector2(c.U + c.Ru * r * Mathf.Cos(a), c.Depth + c.Rd * r * Mathf.Sin(a));
		}

		// Pose tous les insectes de bord dans le lot courant. Rend true si au moins un l'est.
		private bool PoserBord(Rect2 vis)
		{
			if (!BordVisible) return false;
			float t = (float)_tBord, z = WorldView.CurrentZoom, px1 = 1f / z;
			bool pose = false;
			foreach (ColonieVol c in _coloniesVol)
				for (int j = 0; j < c.N; j++)
				{
					uint h = DecorLayer.Melange(c.Graine ^ (uint)(j + 1) * 0x85ebca77u);
					string guilde = GuildesBord[(h >> 24) % (uint)GuildesBord.Length];
					var (col, rayonPx, hopSec) = Guilds.TryGetValue(guilde, out var g) ? g : GuildeInconnue;
					float seg = t / hopSec + (h & 0xffff) / 65536f * BordFleurs;
					float n = Mathf.Floor(seg), f = seg - n;
					int i = Mathf.PosMod((int)n, BordFleurs);
					Vector2 p = FleurDeVol(c, h, i);
					float lift = BordHauteurPx;
					if (f >= DwellRatio)
					{
						float s = (f - DwellRatio) / (1f - DwellRatio);
						s = s * s * (3f - 2f * s);
						p = p.Lerp(FleurDeVol(c, h, (i + 1) % BordFleurs), s);
						lift += 7f * Mathf.Sin(Mathf.Pi * s);   // arc de vol, comme au jardin
					}
					Vector2 scr = DecorLayer.EdgePoint(c.Cote, p.X, p.Y) + new Vector2(0f, -lift);
					if (!vis.HasPoint(scr)) continue;
					pose = true;
					if (_icones) FauneIcones.Poser(_lot, guilde, scr, 2f * rayonPx * z, Vector2.One * px1, px1, h, 1f);
					else { col.A = BaseAlpha; _lot.Grain(scr, rayonPx, col); }
				}
			return pose;
		}
	}
}
