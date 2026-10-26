// SYMBIOSE — DecorLayer.Eau.cs (FLUIDITÉ PC ④ — la RIVIÈRE de lisière en patchwork)
// Partial de DecorLayer : remplace la rivière en aplats (damier rayé, conservée dans
// DecorLayer.Aplats.cs) par le langage du ③ :
//   prairie du kit sur les deux rives (DrawTapis) → LIT en grille aux sommets
//   PARTAGÉS (berge | liseré d'ombre | eau claire | eau profonde | eau claire |
//   liseré | berge), rampe de bleus par parcelles → REFLETS statiques (tirets
//   horizontaux calés au pixel interne) → BERGES en pièces : galets au bord de
//   l'eau, massifs de roseaux, herbe de berge sur le haut de rive.
// La largeur du lit reste pilotée par la ligne d'eau du pont (FacteurLit :
// `endiguer` élargit, `deriver` réduit à un filet) — la vue lit, ne décide pas.
//
// 📖 Pédagogie — le SCINTILLEMENT sans redessiner le décor : le décor entier est
// UN maillage reconstruit seulement au changement de palier (35-58 ms [VM], ③).
// Le redessiner à chaque étincelle coûterait ce prix 3 fois par seconde. Les
// étincelles vivent donc dans un nœud ENFANT (EauScintillement) qui n'a que
// quelques centaines de petits quads : c'est lui seul qui se redessine, ~3 Hz.
// Même idée qu'un sprite clignotant sur une couche à part sur la SNES : on ne
// recompose pas le décor de fond pour faire clignoter une étoile.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private const float PasRefletPx = 9f;   // px internes entre deux tirets de reflet
		private EauScintillement _scintille;

		public override void _Ready()
		{
			_scintille = new EauScintillement { Name = "Scintillement" };
			AddChild(_scintille);
		}

		// Axe sinueux du lit (profondeur cm depuis le bord) à l'abscisse u.
		private static float AxeLit(Secteur s, float u) =>
			DepthCm * 0.5f + AmplitudeCm * Ondulation(s.SeedSecteur ^ 0x9e37u, u / 230f);

		private void DrawRiviere(Secteur s)
		{
			// L'autre rive et le haut de berge sont une PRAIRIE : le tapis du kit est
			// posé sur tout le secteur, puis le lit le recouvre (les touffes qui
			// débordent sur l'eau sont coupées net par la berge, comme une rive).
			DrawTapis(s, Tapis.Prairie);
			float half = DepthCm * 0.22f * FacteurLit(s);
			const float berge = DepthCm * 0.11f;
			float lis = half * 0.18f;
			Color sombre = Assombrir(Palette16.EauProfonde, -0.18f);
			Color[] teinte = { Palette16.BergeGalet, sombre, Palette16.EauSurface, Palette16.EauProfonde,
							   Palette16.EauSurface, sombre, Palette16.BergeGalet };
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			var g = new Vector2[steps + 1, teinte.Length + 1];
			for (int i = 0; i <= steps; i++)
			{
				float u = Mathf.Min(i * StepCm, WorldView.WorldCm), ax = AxeLit(s, u);
				// Les limites eau claire / profonde ondulent pour leur compte (pas de
				// bandes parallèles à l'axe = pas de « rails »).
				float n = 0.40f + 0.14f * Ondulation(s.SeedSecteur * 7u, u / 90f);
				float[] col = { -half - berge, -half, -half + lis, -half * n, half * (0.80f - n), half - lis, half, half + berge };
				for (int c = 0; c < col.Length; c++)
					g[i, c] = EdgePoint(s.Cote, u, ax + col[c]);
			}
			float[] ecarts = { -0.05f, -0.015f, 0.02f, 0.05f };
			for (int i = 0; i < steps; i++)
				for (int b = 0; b < teinte.Length; b++)
				{
					uint hp = HashCase(s.SeedSecteur, i / 3, b, 41u);
					Color c = Assombrir(teinte[b], ecarts[hp & 3u] * (b == 0 || b == teinte.Length - 1 ? 1f : 0.5f));
					_lot.PolygoneConvexe(new[] { g[i, b], g[i + 1, b], g[i + 1, b + 1], g[i, b + 1] }, c);
				}
			DrawReflets(s, half - lis);
			DrawBerges(s, half, berge);
		}

		// REFLETS : tirets HORIZONTAUX de 2-6 px internes, 1 px de haut, calés sur la
		// grille de pixels du SubViewport (comme les pièces). Statiques, dans le lot.
		// Une partie d'entre eux devient aussi le support des étincelles animées.
		private void DrawReflets(Secteur s, float demiEau)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm, PasRefletPx / (z * WorldView.PxPerCmX));
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			var uv = new Rect2(UvBlanc, Vector2.Zero);
			Color clair = Assombrir(Palette16.EauReflet, 0.12f);
			for (int iu = 0; iu < nU; iu++)
				for (int r = -2; r <= 2; r++)
				{
					uint h = HashCase(s.SeedSecteur, iu, r, 43u);
					if ((h & 0xff) > 70u) continue;                        // ~28 % des cases
					float u = (iu + ((h >> 8 & 0xff) / 255f)) * pas;
					if (u > WorldView.WorldCm) continue;
					float d = AxeLit(s, u) + demiEau * (r * 0.36f + ((h >> 16 & 0xff) / 255f - 0.5f) * 0.3f);
					Vector2 p = (EdgePoint(s.Cote, u, d) * z).Round() / z;
					int lg = 2 + (int)(h >> 24 & 3u) + (r == 0 ? 2 : 0);   // plus longs au fil de l'eau
					_lot.Quad(new Rect2(p, new Vector2(lg, 1f) / z), uv, (h >> 26 & 1u) == 0u ? Palette16.EauReflet : clair);
					if ((h >> 27 & 1u) == 0u)
						_eauCible?.Ajouter(p + new Vector2(lg * 0.5f, 0f) / z, Melange(h));
				}
		}

		// BERGES : sur chaque rive, galets au ras de l'eau, massifs de roseaux (par
		// groupes : un massif occupe 4 pas, un sur quatre en porte) et herbe de berge
		// sur le haut de rive. Pose triée nord → sud, comme le tapis.
		private void DrawBerges(Secteur s, float half, float berge)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm, PasTouffePx / (z * WorldView.PxPerCmX));
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			_poses.Clear();
			for (int rive = -1; rive <= 1; rive += 2)
				for (int iu = 0; iu < nU; iu++)
				{
					uint h = HashCase(s.SeedSecteur, iu, rive, 45u);
					float u = (iu + 0.5f + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					if (u < 0f || u > WorldView.WorldCm) continue;
					float ax = AxeLit(s, u);
					float t = (h >> 16 & 0xff) / 255f;                   // 0 bord d'eau → 1 haut de rive
					bool massif = (HashCase(s.SeedSecteur, iu / 4, rive, 47u) & 3u) == 0u;
					Piece f; Teinte te;
					if (massif && t < 0.55f) { f = Piece.Roseau; te = Teinte.Roseau; t *= 0.5f; }
					else if (t < 0.45f) { f = Piece.Galet; te = (h & 1u) == 0u ? Teinte.Roche : Teinte.RocheClaire; }
					else if ((h & 0xff) < 150u) { f = Piece.Herbe; te = Teinte.Prairie; }
					else continue;
					float d = ax + rive * (half + berge * (t - 0.08f));
					int decal = (h >> 4 & 3u) == 0u ? -1 : 0;
					_poses.Add(new Pose(EdgePoint(s.Cote, u, d), f, TailleZoom(f, decal), Melange(h), te, Colors.White));
				}
			PoserTriees(_poses);
		}
	}
}
