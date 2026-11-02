// SYMBIOSE — DecorLayer.Patchwork.cs (FLUIDITÉ PC ③ — assise tramée + tapis du kit)
// Partial de DecorLayer : remplace les APLATS peints de la lisière (3 bandes unies
// par pas, lues comme des « raies » au F5) par un PATCHWORK :
//  • l'ASSISE (DrawAssise) : une grille (u le long du bord × rangs en profondeur)
//    de cellules aux sommets PARTAGÉS, teintées par des nappes de bruit basse fréquence
//    (LISIÈRE NUE ② : les parcelles de 120 × 200 cm se lisaient en damier) ;
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
		// ⑥ DIALECTE 2 : chaque cellule est un aplat en TISSAGE (chevrons 2×3 px
		// procéduraux, decor_indexe.gdshader) — plus aucun aplat uni ; les parcelles
		// ne varient plus par une couleur voisine mais par le TON de base (patchs plus
		// clairs du brief). Forêt = couvert olive EXACT du brief (près ton 2, fond ton 1).
		// Résidu (a) : un rang de plus prolonge la bande jusqu'à FondCm (bord du cadre au
		// dézoom maximal) et le coin extérieur entre ce bord et le suivant est couvert.
		private const float FondCm = 3600f;   // ≥ cadre ×0,5 caméra au bout de sa butée
		// Nappes de l'assise (LISIÈRE NUE ②), en cellules : pas de 40 cm, rangs de 100 cm.
		private const float NappeTonPas = 11f, NappeTonRangs = 3.5f;
		private const float NappePhasePas = 14f, NappePhaseRangs = 4.5f;
		private const float SeuilTonClair = 0.60f;   // ≈ 1/4 de cellules plus claires
		private const float BordFondAmpCm = 160f;
		private const float CouturePas = 12f;        // friche : cellules effilochées à chaque bout

		// Bruit de valeur (4 hashes lissés) : des nappes aux contours souples, stables au
		// seed, sans bloc. Même recette que `bruit` du shader, côté construction.
		private static float BruitValeur(uint graine, float x, float y, uint canal)
		{
			int ix = Mathf.FloorToInt(x), iy = Mathf.FloorToInt(y);
			float fx = x - ix, fy = y - iy;
			fx = fx * fx * (3f - 2f * fx);
			fy = fy * fy * (3f - 2f * fy);
			float V(int i, int j) => (HashCase(graine, i, j, canal) >> 8 & 0xffff) / 65535f;
			return Mathf.Lerp(Mathf.Lerp(V(ix, iy), V(ix + 1, iy), fx),
							  Mathf.Lerp(V(ix, iy + 1), V(ix + 1, iy + 1), fx), fy);
		}

		// Limite extérieure de la bande : sinueuse, sinon une longue droite iso se lit au
		// dézoom, là où le tapis s'arrête et où commence le rang du fond.
		private static float BordFond(Secteur s, float u) =>
			DepthCm - BordFondAmpCm * (0.5f + 0.5f * Ondulation(s.SeedSecteur ^ 0x7a3du, u / 170f));

		private void DrawAssise(Secteur s)
		{
			(Color near, Color far) = MotifColors(s.Motif);
			// Le fond d'une friche (lisière de bois) ne continue pas au-delà de sa bande : sinon
			// sa limite avec la prairie voisine file en droite jusqu'au bord du cadre.
			bool friche = s.Motif == Motif.Friche;
			Color farLoin = friche ? Palette16.DecorPrairie : far;
			string mat = s.Motif == Motif.Foret ? "couvert_olive" : null;
			int tonFond = s.Motif == Motif.Foret ? 1 : TonB;
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			float seuilW = DepthCm * 0.06f;
			// ⑥ : tout le sol vivant suit la saison, parcelle par parcelle (phase au hash) ;
			// sous la falaise, le fond reste de la roche.
			int classeFond = s.Motif == Motif.Falaise ? ClasseInerte : ClassePrairie;
			var g = new Vector2[steps + 1, RangsAssise + 3];
			for (int i = 0; i <= steps; i++)
			{
				float u = Mathf.Min(i * StepCm, WorldView.WorldCm);
				float b = AmplitudeCm * Ondulation(s.SeedSecteur, u / 200f);
				g[i, 0] = EdgePoint(s.Cote, u, b);
				for (int k = 1; k <= RangsAssise + 1; k++)
					g[i, k] = EdgePoint(s.Cote, u, Mathf.Lerp(b + seuilW, BordFond(s, u), (k - 1) / (float)RangsAssise));
				g[i, RangsAssise + 2] = EdgePoint(s.Cote, u, FondCm);
			}
			for (int i = 0; i < steps; i++)
				for (int k = 0; k <= RangsAssise + 1; k++)
				{
					// ⚠️ Avant LISIÈRE NUE ② : uint hp = HashCase(s.SeedSecteur, i / 3, (k + 1) / 2, 7u),
					// blocs de 120 × 200 cm pour le ton, le seuil et la phase de saison : un damier.
					// Ici, trois nappes indépendantes, et un hash par cellule qui effiloche leurs limites.
					float g0 = (HashCase(s.SeedSecteur, i, k, 7u) >> 8 & 0xff) / 255f - 0.5f;
					float nappeTon = BruitValeur(s.SeedSecteur, i / NappeTonPas, k / NappeTonRangs, 7u);
					float nappePhase = BruitValeur(s.SeedSecteur, i / NappePhasePas, k / NappePhaseRangs, 8u);
					Color col;
					int ton;
					if (k == 0) { col = near; ton = 1; }
					else if (k > RangsAssise) { col = farLoin; ton = tonFond; }   // au-delà de la bande
					else
					{
						float frac = (k - 0.5f) / RangsAssise;
						// La frange claire ondule le long du bord, sans marche de bloc.
						float seuil = 0.30f + 0.20f * Ondulation(s.SeedSecteur ^ 0x51edu, i * StepCm / 300f) + 0.10f * g0;
						bool pres = frac < seuil;
						col = pres ? near : far;
						// Aux deux bouts du bord, la friche s'effiloche dans la prairie, sans couture droite.
						if (friche && !pres)
						{
							float bout = 1f - Mathf.Min(i, steps - 1 - i) / CouturePas;
							if (bout > 0f && BruitValeur(s.SeedSecteur, i / 4f, k / 2f, 9u) + 0.2f * g0 < bout)
								col = farLoin;
						}
						ton = nappeTon + 0.12f * g0 > SeuilTonClair ? 3 : pres ? TonB : tonFond;
					}
					ClasseAplats(col == far || col == farLoin ? classeFond : ClassePrairie);
					// Le rang du fond a des cellules de 40 cm × 27 m : une phase propre à chacune
					// les rendait visibles en longues barres aux semaines de transition.
					Vent(0f, 0f, 1f, k > RangsAssise ? 0.5f : Mathf.Clamp(nappePhase + 0.25f * g0, 0f, 1f));
					Aplats(OrientTissage, ton, mat);
					_lot.PolygoneConvexe(new[] { g[i, k], g[i + 1, k], g[i + 1, k + 1], g[i, k + 1] }, col);
				}
			// Coin extérieur entre ce bord et le suivant (sens horaire : NE, SE, SO, NO).
			float W = WorldView.WorldCm;
			(float x0, float y0) = s.Cote switch { 0 => (W, -FondCm), 1 => (W, W), 2 => (-FondCm, W), _ => (-FondCm, -FondCm) };
			Vent(0f, 0f, 1f, 0.5f);
			ClasseAplats(classeFond);
			Aplats(OrientTissage, tonFond, mat);
			_lot.PolygoneConvexe(new[] { WorldView.WorldToScreen(x0, y0), WorldView.WorldToScreen(x0 + FondCm, y0),
										 WorldView.WorldToScreen(x0 + FondCm, y0 + FondCm), WorldView.WorldToScreen(x0, y0 + FondCm) }, farLoin);
			ClasseAplats(ClasseInerte);
			Vent(0f, 0f, 1f, 0f);
			Aplats(OPlat);
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
					if (b + d > BordFond(s, u) - 10f) continue;
					ChoisirPiece(mode, h, dd, out Piece f, out int taille, out Teinte t);
					float m = 1f - 0.20f * Mathf.Clamp(dd / DepthCm, 0f, 1f);
					_poses.Add(new Pose(EdgePoint(s.Cote, u, b + d), f, taille, Melange(h), t, new Color(m, m, m)));
				}
				dd += pas * k;
			}
			SemerColonies(s);   // LISIÈRE NUE ② : les fleurs ne viennent plus que des colonies
			PoserTriees(_poses);
		}

		// Ce qu'on pose à un point du tapis, selon le motif, la profondeur et le hash.
		private static void ChoisirPiece(Tapis mode, uint h, float dd, out Piece f, out int taille, out Teinte t)
		{
			int roll = (int)(h >> 24) % 100;
			int decal = (h >> 20 & 3u) == 0u ? -1 : 0;   // un quart des touffes plus petites
			bool ourlet = dd < OurletCm;
			Teinte herbe = ourlet || (h >> 4 & 3u) == 0u ? Teinte.PrairieClair : Teinte.Prairie;
			// ⚠️ Avant LISIÈRE NUE ② : Teinte fleur = (h >> 6 & 1u) == 0u ? Teinte.FleurBlanc : Teinte.FleurJaune;
			switch (mode)
			{
				case Tapis.Friche:
					// ⚠️ Avant LISIÈRE NUE ② : if (roll < 5) { f = Piece.Fleur; t = fleur; } (fleurs partout)
					if (roll < 42) { f = Piece.HerbeHaute; t = Teinte.Paille; }
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
					// ⚠️ Avant LISIÈRE NUE ② : if (roll < 9) { f = Piece.Fleur; t = fleur; } (fleurs partout)
					f = Piece.Herbe; t = herbe;
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
			if (!_ventArbre) Vent(0f, 0f, 1f, 0f);   // ⑥ : le vent des pièces ne fuit pas sur les aplats suivants
		}
	}
}
