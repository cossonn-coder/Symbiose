// SYMBIOSE — DecorLayer.Patchwork.cs (FLUIDITÉ PC ③ — assise tramée + tapis du kit)
// Partial de DecorLayer : remplace les APLATS peints de la lisière (3 bandes unies
// par pas, lues comme des « raies » au F5) par un PATCHWORK :
//  • l'ASSISE (DrawAssise) : une grille (u le long du bord × rangs en profondeur)
//    de cellules aux sommets PARTAGÉS, teintées par grandes pièces de 120 × 200 cm
//    (3 pas × 2 rangs) — des parcelles, pas des rayures ;
//  • le TAPIS (DrawTapis) : des pièces du kit (DecorLayer.Kit.cs) semées au hash —
//    ourlet DENSE de touffes collé au jardin, fond plus calme mais tramé. Prairie
//    = herbe + fleurettes ; friche = herbes sèches qui versent + ronciers ;
//    forêt = ourlet de sous-bois et de touffes au pied du rideau d'arbres.
//
// 📖 Pédagogie — les coutures (FLUIDITÉ PC ②) restent fermées : chaque sommet de
// la grille est calculé UNE fois et partagé par les 4 cellules qui le touchent.
// Deux cellules voisines ont donc EXACTEMENT la même arête → l'arrondi au pixel
// du SubViewport les déplace ensemble, aucun fil ne transparaît.
//
// 📖 Pédagogie — pourquoi l'espacement dépend du PALIER : une pièce du kit fait
// toujours ses N px internes (comme les touffes des plantes), donc elle couvre
// 4× moins de terrain à ×1 qu'à ×0,5. On sème en cm monde avec un pas qui suit le
// zoom (≈ 6 px internes entre touffes), borné à 12 cm au gros plan pour que le
// nombre de pièces reste fini. Le décor étant inerte, ce semis n'est recalculé
// qu'au changement de palier — jamais par image.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private enum Tapis { Prairie, Friche, OurletForet, Pierrier }

		private const int RangsAssise = 9;          // rangs de fond (≈ 100 cm chacun)
		private const float OurletCm = 220f;        // profondeur de l'ourlet dense
		private const float PasTouffePx = 6f;       // px internes entre deux touffes
		private const float PasTouffeMinCm = 15f;   // borne au gros plan (×2, ×4)

		// Une pose en attente de tri (peintre : le plus au nord d'abord).
		private readonly record struct Pose(Vector2 Pied, Piece F, int Taille, uint H, Teinte T, Color Mod);
		private readonly List<Pose> _poses = new();

		// ASSISE : la bande hors-jardin en grille de cellules jointives. Rang 0 =
		// seuil sombre collé au tracé sinueux (la frontière se LIT) ; rangs suivants
		// = frange claire puis fond, la limite entre les deux suivant les parcelles
		// (jamais une droite).
		private void DrawAssise(Secteur s)
		{
			(Color near, Color far) = MotifColors(s.Motif);
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			float seuilW = DepthCm * 0.06f;
			var g = new Vector2[steps + 1, RangsAssise + 2];
			for (int i = 0; i <= steps; i++)
			{
				float u = Mathf.Min(i * StepCm, WorldView.WorldCm);
				float b = AmplitudeCm * Ondulation(s.SeedSecteur, u / 200f);
				g[i, 0] = EdgePoint(s.Cote, u, b);
				for (int k = 1; k <= RangsAssise + 1; k++)
					g[i, k] = EdgePoint(s.Cote, u, Mathf.Lerp(b + seuilW, DepthCm, (k - 1) / (float)RangsAssise));
			}
			float[] ecarts = { -0.07f, -0.02f, 0.03f, 0.07f };
			for (int i = 0; i < steps; i++)
				for (int k = 0; k <= RangsAssise; k++)
				{
					uint hp = HashCase(s.SeedSecteur, i / 3, (k + 1) / 2, 7u);
					Color col;
					if (k == 0) col = Assombrir(near, -0.24f + ecarts[hp & 3u] * 0.5f);
					else
					{
						float frac = (k - 0.5f) / RangsAssise;
						float seuil = 0.30f + 0.16f * ((hp >> 8 & 0xff) / 255f - 0.5f);
						col = Assombrir(frac < seuil ? near : far, ecarts[hp & 3u]);
					}
					_lot.PolygoneConvexe(new[] { g[i, k], g[i + 1, k], g[i + 1, k + 1], g[i, k + 1] }, col);
				}
		}

		// TAPIS : semis des pièces du kit sur un secteur, trié puis posé.
		private void DrawTapis(Secteur s, Tapis mode)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm, PasTouffePx / (z * WorldView.PxPerCmX));
			float seuilW = DepthCm * 0.06f;
			float fin = mode == Tapis.OurletForet ? OurletCm : DepthCm;
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			_poses.Clear();
			int id = 0;
			for (float dd = seuilW * 0.4f; dd < fin; id++)
			{
				// Le pas en profondeur s'élargit au fond : ourlet dense, fond calme.
				float k = dd < OurletCm ? 1f : dd < 500f ? 2f : 3f;
				for (int iu = 0; iu < nU; iu++)
				{
					uint h = HashCase(s.SeedSecteur, iu, id, (uint)mode + 11u);
					if ((h & 0xff) < (dd < OurletCm ? 30u : 90u)) continue;   // trous du semis
					float u = (iu + 0.5f + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					if (u < 0f || u > WorldView.WorldCm) continue;
					float d = dd + ((h >> 16 & 0xff) / 255f - 0.5f) * pas * k * 0.9f;
					float b = AmplitudeCm * Ondulation(s.SeedSecteur, u / 200f);
					if (b + d > DepthCm - 10f) continue;
					ChoisirPiece(mode, h, dd, out Piece f, out int taille, out Teinte t);
					float m = 1f - 0.20f * Mathf.Clamp(dd / DepthCm, 0f, 1f);
					_poses.Add(new Pose(EdgePoint(s.Cote, u, b + d), f, taille, Melange(h), t, new Color(m, m, m)));
				}
				dd += pas * k;
			}
			PoserTriees(_poses);
		}

		// Ce qu'on pose à un point du tapis, selon le motif, la profondeur et le hash.
		private static void ChoisirPiece(Tapis mode, uint h, float dd, out Piece f, out int taille, out Teinte t)
		{
			int roll = (int)(h >> 24) % 100;
			int decal = (h >> 20 & 3u) == 0u ? -1 : 0;   // un quart des touffes plus petites
			bool ourlet = dd < OurletCm;
			Teinte herbe = ourlet || (h >> 4 & 3u) == 0u ? Teinte.PrairieClair : Teinte.Prairie;
			Teinte fleur = (h >> 6 & 1u) == 0u ? Teinte.FleurBlanc : Teinte.FleurJaune;
			switch (mode)
			{
				case Tapis.Friche:
					if (roll < 5) { f = Piece.Fleur; t = fleur; }
					else if (roll < 42) { f = Piece.HerbeHaute; t = Teinte.Paille; }
					else if (roll < (ourlet ? 52 : 62)) { f = Piece.Roncier; t = Teinte.Roncier; }
					else { f = Piece.Herbe; t = herbe; }
					break;
				case Tapis.OurletForet:
					if (roll < 50) { f = Piece.SousBois; t = Teinte.SousBois; }
					else if (roll < 62) { f = Piece.Roncier; t = Teinte.Roncier; }
					else { f = Piece.Herbe; t = Teinte.Prairie; }
					break;
				case Tapis.Pierrier:   // ④ : pied et dessus de falaise, herbe sèche et cailloux
					if (roll < 22) { f = Piece.Galet; t = (h >> 6 & 1u) == 0u ? Teinte.Roche : Teinte.RocheClaire; }
					else if (roll < 30) { f = Piece.Bloc; t = Teinte.Roche; }
					else if (roll < 70) { f = Piece.Herbe; t = Teinte.Paille; }
					else { f = Piece.Herbe; t = Teinte.Prairie; }
					break;
				default:
					if (roll < 9) { f = Piece.Fleur; t = fleur; }
					else { f = Piece.Herbe; t = herbe; }
					break;
			}
			taille = TailleZoom(f, decal);
		}

		// Tri du peintre (Y écran croissant : le nord d'abord, le sud devant) puis
		// pose de toutes les pièces en attente. Tri par CLÉS (Array.Sort(clés,
		// valeurs)) : sans délégué de comparaison ni copie de la structure à chaque
		// comparaison — ~3× plus rapide sur des milliers de poses.
		private float[] _cles = new float[0];
		private Pose[] _tri = new Pose[0];

		private void PoserTriees(List<Pose> poses)
		{
			int n = poses.Count;
			if (_cles.Length < n) { _cles = new float[n * 2]; _tri = new Pose[n * 2]; }
			for (int i = 0; i < n; i++) { _tri[i] = poses[i]; _cles[i] = poses[i].Pied.Y; }
			System.Array.Sort(_cles, _tri, 0, n);
			for (int i = 0; i < n; i++)
				PoserPiece(_tri[i].F, _tri[i].Taille, _tri[i].H, _tri[i].T, _tri[i].Pied, _tri[i].Mod);
			poses.Clear();
		}
	}
}
