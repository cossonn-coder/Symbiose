// SYMBIOSE — DecorLayer.Houppiers.cs (FLUIDITÉ PC ③ — arbres de lisière en pièces du kit)
// Partial de DecorLayer : l'ARBRE du décor assemblé en patchwork. Avant ③, un
// houppier était un amas d'ellipses lisses (64 segments chacune, ~3 000 sommets
// par arbre) : de loin une tache sombre sans grain. Ici :
//   ombre au pied (ellipse basse définition) → tronc CERNÉ (contour sombre) →
//   ENVELOPPE pleine à la teinte d'ombre (12 côtés, elle bouche les jours) →
//   BOUQUETS du kit (Feuillu / Conifere) semés dans l'enveloppe, triés du nord au
//   sud : chacun porte son contour, son ombre et sa lumière → le grain SNES.
// Les règles de PLACEMENT des arbres (gradient de lisière, densité/taille du pont)
// restent dans DecorLayer.Arbres.cs ; ici, seulement comment un arbre se dessine.
//
// 📖 Pédagogie — le rideau « arrière sombre, avant clair » : chaque arbre reçoit un
// MODULATEUR de couleur (blanc devant → gris au cœur du bois), multiplié par le GPU
// avec la pièce. Aucune teinte de plus dans l'atlas : la profondeur se lit par la
// valeur, comme les plans successifs d'un décor de Chrono Trigger.
//
// 📖 Pédagogie — combien de bouquets : ∝ l'AIRE de l'enveloppe en px internes
// (donc au palier), bornée à 36 — au-delà l'enveloppe d'ombre fait le fond et les
// bouquets le bord bosselé. Coût d'un arbre : ~250 sommets au lieu de ~3 000.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private const int BouquetsMax = 40;
		private readonly List<Pose> _bouquets = new();

		/// <summary>Un arbre de lisière en pièces du kit. `mod` = valeur du plan
		/// (1 devant, plus sombre au cœur du bois).</summary>
		private void DrawArbreKit(Vector2 basePos, TreeSilhouette sil, float scale, Color mod, uint hb)
		{
			float z = ZoomConstr;
			float trunkH = sil.TrunkHeightCm * WorldView.PxPerCmZ * scale;
			float r = sil.CanopyRadiusCm * WorldView.PxPerCmX * scale;
			Vector2 apex = basePos + Vector2.Up * trunkH;
			// Ombre au pied, décalée NE (soleil au SO), comme avant ③. Immobile au vent.
			// ⑥ : en tissage (le halo d'ancrage du brief, pas une flaque unie).
			Aplats(OrientTissage, 0, "couvert_olive");   // « sous les arbres » : creux du couvert
			EllipseBasse(basePos + new Vector2(r * 0.10f, -r * 0.06f), r * 0.70f, r * 0.22f,
						 Assombrir(Palette16.DecorForetFond, -0.30f), 10);
			bool conique = sil.Port == TreePort.Conique;
			(float up, float rx, float ry) = sil.Port switch
			{
				TreePort.Elance  => (0.60f, 0.75f, 0.95f),
				TreePort.Ovoide  => (0.75f, 0.85f, 1.20f),
				TreePort.Sinueux => (0.45f, 0.95f, 0.85f),
				TreePort.Conique => (0.95f, 0.80f, 1.10f),
				_                => (0.40f, 1.20f, 0.80f),
			};
			// ⑥ : tout ce qui suit plie au vent, nul au pied → max au sommet du houppier.
			VentArbre(basePos, trunkH + r * (up + ry), hb);
			// Tronc : contour = ton CREUX de SA rampe (règle des petits objets, jamais un
			// gris étranger), puis l'écorce en deux flancs ORIENTÉS (le soleil réel éclaire
			// l'un, ombre l'autre — DecorLayer.Indexe.cs).
			float w = Mathf.Max(1.5f / z, r * 0.14f);
			Aplats(OPlat, 0);
			Fuseau(basePos + Vector2.Down / z, apex, w + 1f / z, sil.Ecorce * mod);
			Aplats(OrientEcorceG);
			FuseauDemi(basePos, apex, w, -1f, sil.Ecorce * mod);
			Aplats(OrientEcorceD);
			FuseauDemi(basePos, apex, w, 1f, sil.Ecorce * mod);
			Aplats(OPlat);
			if (sil.Port == TreePort.Elance && DetailsVisibles)   // bouleau : lenticelles
				for (float tl = 0.2f; tl < 0.95f; tl += 0.18f)
				{
					Vector2 c = basePos.Lerp(apex, tl);
					_lot.Ligne(c + Vector2.Left * w * 0.6f, c + Vector2.Right * w * 0.2f, Palette16.EcorceLenticelle, 1f / z);
				}
			// Enveloppe du port (fond du houppier, en TISSAGE du dialecte 2, ton d'ombre)
			// puis bouquets.
			Vector2 c0 = apex + Vector2.Up * r * up;
			rx *= r; ry *= r;
			// LISIÈRE NUE ③ : la charpente, cachée l'été, révélée par le dégarnissement du shader.
			if (!conique) DrawBranches(apex, c0, rx, ry, w, sil.Port, sil.Ecorce * mod, hb);
			Teinte t = TeinteFeuillage(sil.Feuillage);
			Color ombre = sil.Feuillage * mod;   // ⑥ : l'ombre = ton 1 de SA palette (tissage)
			ClasseAplats(conique ? ClasseSansSaison : ClasseFeuillu);   // ⑥ : la couronne suit la saison
			Aplats(OrientTissage, 1);
			if (conique)
				_lot.Triangle(c0 + new Vector2(0f, -ry), c0 + new Vector2(rx, ry), c0 + new Vector2(-rx, ry), ombre);
			else
				EllipseBasse(c0, rx * 0.92f, ry * 0.92f, ombre, 12);
			ClasseAplats(ClasseInerte);
			Aplats(OPlat);
			Piece f = conique ? Piece.Conifere : Piece.Feuillu;
			// Taille des bouquets : la plus grande qui tient ~2,5 fois dans le rayon du
			// houppier À L'ÉCRAN (px internes) → un gros arbre est fait de gros
			// bouquets, pas de centaines de petits (coût borné, lecture « en masses »).
			int taille = Tailles[(int)f].Length - 1;
			while (taille > 0 && Tailles[(int)f][taille].X > rx * z * 0.8f) taille--;
			Vector2 sz = TaillePiece(f, taille);
			int n = Mathf.Clamp(Mathf.RoundToInt(1.5f * Mathf.Pi * rx * ry / (sz.X * sz.Y)), 4, BouquetsMax);
			_bouquets.Clear();
			float rot = (hb & 0xffff) / 65535f * Mathf.Tau;
			for (int k = 0; k < n; k++)
			{
				uint h = HashCase(hb, k, 0, 3u);
				// Spirale de Fibonacci (angle d'or) : n points qui COUVRENT l'ellipse
				// sans s'agglutiner (un tirage au hash pur laissait des trous plats),
				// un léger jitter au hash évite la régularité de grille.
				float a = rot + k * 2.39996f + ((h & 0xff) / 255f - 0.5f) * 0.6f;
				float rho = Mathf.Min(0.95f, Mathf.Sqrt((k + 0.5f) / n) * (0.9f + 0.15f * ((h >> 16 & 0xff) / 255f)));
				Vector2 p;
				if (conique)
				{
					float hy = (h >> 24 & 0xff) / 255f;                 // 0 sommet → 1 base
					p = c0 + new Vector2((((h >> 8 & 0xff) / 255f) - 0.5f) * 1.6f * rx * hy, -ry + 2f * ry * hy);
				}
				else p = c0 + new Vector2(Mathf.Cos(a) * rx * rho, -Mathf.Sin(a) * ry * rho);
				_bouquets.Add(new Pose(p + new Vector2(0f, sz.Y * 0.5f), f, taille, h, t, mod));
			}
			PoserTriees(_bouquets);
			FinArbre();
		}

		/// <summary>SOUS-BOIS : pièces sombres semées dans toute la bande de forêt,
		/// sous les arbres (posées AVANT eux) — on les voit entre les troncs. Densité ∝
		/// la densité ligneuse du pont : une clairière s'éclaircit aussi au sol.</summary>
		private void DrawSousBois(Secteur s, float kDensite)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm * 2f, 2.5f * PasTouffePx / (z * WorldView.PxPerCmX));
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			int nD = Mathf.CeilToInt((DepthCm - OurletCm) / pas);
			_poses.Clear();
			for (int iu = 0; iu < nU; iu++)
				for (int id = 0; id < nD; id++)
				{
					uint h = HashCase(s.SeedSecteur, iu, id, 29u);
					if ((h & 0xff) / 255f > 0.75f * kDensite) continue;
					float u = (iu + 0.5f + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					float d = OurletCm + (id + 0.5f + ((h >> 16 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					if (u < 0f || u > WorldView.WorldCm || d > DepthCm - 10f) continue;
					float m = Mathf.Lerp(0.95f, 0.70f, d / DepthCm);
					Piece f = (h >> 24 & 3u) == 0u ? Piece.Roncier : Piece.SousBois;
					_poses.Add(new Pose(EdgePoint(s.Cote, u, d + AmplitudeCm), f, TailleZoom(f),
										Melange(h), f == Piece.Roncier ? Teinte.Roncier : Teinte.SousBois, new Color(m, m, m)));
				}
			PoserTriees(_poses);
		}

		// Teinte d'atlas d'une essence (par sa couleur de feuillage du registre).
		private static Teinte TeinteFeuillage(Color c) =>
			c == Palette16.FeuillageHetre ? Teinte.Hetre
			: c == Palette16.FeuillageBouleau ? Teinte.Bouleau
			: c == Palette16.FeuillageCharme ? Teinte.Charme
			: c == Palette16.FeuillageSapin ? Teinte.Sapin
			: Teinte.Chene;

		// Ellipse BASSE DÉFINITION (n côtés) : à 10-12 côtés l'œil ne voit pas la
		// différence sous les bouquets, et on paie 3(n−2) sommets au lieu de 192.
		private void EllipseBasse(Vector2 c, float rx, float ry, Color col, int n)
		{
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float a = i * Mathf.Tau / n;
				pts[i] = c + new Vector2(Mathf.Cos(a) * rx, Mathf.Sin(a) * ry);
			}
			_lot.PolygoneConvexe(pts, col);
		}

		// ⑥ : demi-fuseau (côté −1 gauche / +1 droite de l'axe) — un flanc de tronc.
		private void FuseauDemi(Vector2 pied, Vector2 apex, float w, float cote, Color col) =>
			_lot.PolygoneConvexe(new[] { pied, pied + Vector2.Right * w * cote,
								  apex + Vector2.Right * w * 0.5f * cote, apex }, col);

		// Fuseau de tronc : large au sol, moitié moins sous le houppier.
		private void Fuseau(Vector2 pied, Vector2 apex, float w, Color col) =>
			_lot.PolygoneConvexe(new[] { pied + Vector2.Left * w, pied + Vector2.Right * w,
								  apex + Vector2.Right * w * 0.5f, apex + Vector2.Left * w * 0.5f }, col);
	}
}
