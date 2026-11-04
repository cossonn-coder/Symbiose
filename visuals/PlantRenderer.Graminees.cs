// SYMBIOSE — PlantRenderer.Graminees.cs (partial, sprint TRÈFLE DOMINANT ④, D126)
// Les trois espèces neuves de la prairie, reconnaissables à leur silhouette plus qu'à leur
// teinte, puisqu'elles se côtoient et sont toutes vertes :
//  • DACTYLE : grosse touffe haute à feuilles larges arquées, panicules aux glomérules en
//    paquets d'un seul côté de la tige (son nom anglais : « cock's foot », patte de coq) ;
//  • FÉTUQUE ROUGE : gazon de brins très fins, 1 px à tous les paliers, panicule rousse ;
//  • PLANTAIN LANCÉOLÉ : rosette plaquée de feuilles étroites à nervures parallèles, et
//    hampe nue terminée par un épi brun court, couronné d'anthères claires en floraison.
// Le lot, la teinte et le dispatch sont dans PlantRenderer.Prairie.cs. Les hauteurs viennent
// de `height_cm` du moteur : une touffe à l'ombre reste courte.
//
// 📖 Pédagogie : un brin est une LANIÈRE de triangles, le long d'une courbe calculée en cm
// puis projetée point par point par Iso. C'est Iso qui applique la flexion du vent : les
// bouts se couchent, le pied ne bouge pas, sans code de vent ici.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const int BrinsDactyle = 20, BrinsFetuque = 26;
		private const float LargeurDactyleCm = 1.5f, LargeurFetuqueCm = 0.3f;
		private const float RayonPlantainCm = 17f;
		private const int FeuillesPlantain = 11;
		private const float LargeurPlantain = 0.12f;   // demi-largeur / longueur : lancéolée
		private const float LeveePlantainCm = 3.5f;     // le bout de la feuille se relève
		// Les hampes se lèvent avant l'anthèse : seuil plus bas que FloraisonSeuil.
		private const float FloraisonHampe = 0.2f;
		private const int SegmentsBrin = 4;

		// Une feuille lancéolée de la rosette : (long, large) relatifs, éventail depuis la base.
		private static readonly Vector2[] ProfilLanceole =
		{
			new(0f, 0f), new(0.2f, 0.45f), new(0.5f, 1f), new(0.8f, 0.6f), new(1f, 0f),
			new(0.8f, -0.6f), new(0.5f, -1f), new(0.2f, -0.45f),
		};

		// ---------------------------------------------------------------------------
		// BRIN — lanière arquée, du pied au bout, de largeur décroissante
		// ---------------------------------------------------------------------------

		// (x, y) = pied, (ux, uy) = direction de l'arc, `port` = écart horizontal du bout.
		private void PoserBrin(float x, float y, float ux, float uy, float port, float h,
							   float largeurCm, Color col)
		{
			float zf = AplatMort;
			Vector2 prec = Iso(x, y, 0f);
			float l0 = Mathf.Max(largeurCm * WorldView.PxPerCmX, PixelInterne);
			Vector2 gPrec = prec, dPrec = prec;
			for (int i = 1; i <= SegmentsBrin; i++)
			{
				float t = i / (float)SegmentsBrin;
				float z = h * t * (2f - t) * zf;              // monte vite, ralentit : l'arc
				float e = port * t * t;                       // s'écarte de plus en plus
				Vector2 p = Iso(x + ux * e, y + uy * e, z);
				Vector2 nrm = (p - prec).Orthogonal().Normalized();
				float l = l0 * 0.5f * (1f - t * t);
				float mini = PixelInterne * 0.5f;
				Vector2 g = p + nrm * Mathf.Max(l, i < SegmentsBrin ? mini : 0f);
				Vector2 d = p - nrm * Mathf.Max(l, i < SegmentsBrin ? mini : 0f);
				if (i == 1)
				{
					gPrec = prec + nrm * Mathf.Max(l0 * 0.5f, mini);
					dPrec = prec - nrm * Mathf.Max(l0 * 0.5f, mini);
				}
				_lotPrairie.Triangle(gPrec, dPrec, d, col);
				_lotPrairie.Triangle(gPrec, d, g, col);
				gPrec = g; dPrec = d; prec = p;
			}
		}

		// ---------------------------------------------------------------------------
		// DACTYLE
		// ---------------------------------------------------------------------------

		private void DessinerDactyle(Color col)
		{
			var (rayon, h) = MesurePrairie(PortPrairie.Dactyle);
			float g = CroissancePrairie(PortPrairie.Dactyle);
			int ig = GraineIndividu;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.DensiteVisible * 1.3f, DensitePlancher, 1f);
			int n = Mathf.Max(3, Mathf.RoundToInt(BrinsDactyle * g * dens));
			float souche = rayon * 0.25f;
			// Hampes derrière le feuillage : elles sortent du cœur de la touffe.
			PoserSouche(souche, col);
			if (FleuriPrairie(FloraisonHampe)) PoserPanicules(h, g, ig);
			for (int k = 0; k < n; k++)
			{
				float a = k * 2.39996f + Mathf.Tau * Hash01(222, ig, 0);
				float ux = Mathf.Cos(a), uy = Mathf.Sin(a);
				float d = souche * Hash01(223, ig, k);
				float hb = h * Mathf.Lerp(0.5f, 0.78f, Hash01(225, ig, k));
				// Le cœur plus clair et plus droit, le bord plus sombre et plus arqué.
				float arc = k / (float)n;
				int ton = arc < 0.35f ? 1 : arc < 0.8f ? PaletteIndexee.TonBase : 3;
				Color c = Ton(col, ton, Orientation(WorldView.WorldToScreenOffset(ux, uy)));
				PoserBrin(ux * d, uy * d, ux, uy, rayon * Mathf.Lerp(0.5f, 1f, 1f - arc), hb, LargeurDactyleCm, c);
				if (k % 3 == 0)
					_sitesPrairie.Add((Iso(ux * rayon * 0.5f, uy * rayon * 0.5f, hb * 0.8f),
						LargeurDactyleCm * 2f * WorldView.PxPerCmX, k, hb));
			}
		}

		// Le collet de la touffe : les brins sortent d'une base sombre, pas de la terre nue.
		private void PoserSouche(float r, Color col)
		{
			float px = Mathf.Max(r * WorldView.PxPerCmX, PixelInterne);
			_lotPrairie.Ellipse(Vector2.Zero, px, px * 0.5f, Ton(col, 1));
		}

		private void PoserPanicules(float h, float g, int ig)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * 5f), 1, 5);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(227, ig, k);
				float ux = Mathf.Cos(a), uy = Mathf.Sin(a);
				float e = 5f * Hash01(229, ig, k);
				float haut = h * Mathf.Lerp(1.0f, 1.2f, Hash01(231, ig, k));
				Vector2 pied = Iso(0f, 0f, 0f), tete = Iso(ux * e, uy * e, haut);
				_lotPrairie.Ligne(pied, tete, Ton(pal.Leaf, 3), PixelInterne);
				// Trois paquets étagés, tous du même côté : la patte de coq.
				float cote = Hash01(233, ig, k) < 0.5f ? 1f : -1f;
				for (int m = 0; m < 3; m++)
				{
					float t = 1f - m * 0.11f;
					Vector2 axe = pied.Lerp(tete, t);
					float bras = (0.6f + m * 1.2f) * cote * WorldView.PxPerCmX * 2f;
					var c = axe + new Vector2(bras, -PixelInterne);
					_lotPrairie.Ligne(axe, c, Ton(pal.Flower, 1), PixelInterne);
					PoserBoule(c, (1.5f + m * 0.3f) * WorldView.PxPerCmX, pal.Flower, ig + k * 7 + m);
				}
			}
		}

		// ---------------------------------------------------------------------------
		// FÉTUQUE ROUGE
		// ---------------------------------------------------------------------------

		private void DessinerFetuque(Color col)
		{
			var (rayon, h) = MesurePrairie(PortPrairie.Fetuque);
			float g = CroissancePrairie(PortPrairie.Fetuque);
			int ig = GraineIndividu;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.DensiteVisible * 2.5f, DensitePlancher, 1f);
			int n = Mathf.Max(4, Mathf.RoundToInt(BrinsFetuque * g * dens));
			PoserSouche(rayon * 0.3f, col);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(241, ig, k);
				float ux = Mathf.Cos(a), uy = Mathf.Sin(a);
				float d = rayon * 0.55f * Mathf.Sqrt(Hash01(243, ig, k));
				float hb = h * Mathf.Lerp(0.55f, 1f, Hash01(245, ig, k));
				int ton = PaletteIndexee.TonBase + (Hash01(247, ig, k) < 0.35f ? 1 : Hash01(247, ig, k) > 0.75f ? -1 : 0);
				PoserBrin(ux * d, uy * d, ux, uy, rayon * 0.45f, hb, LargeurFetuqueCm, Ton(col, ton));
				if (k % 5 == 0)
					_sitesPrairie.Add((Iso(ux * d, uy * d, hb * 0.7f), 1.2f * WorldView.PxPerCmX, k, hb));
			}
			if (!FleuriPrairie(FloraisonHampe)) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int nh = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * 4f), 1, 4);
			for (int k = 0; k < nh; k++)
			{
				float a = Mathf.Tau * Hash01(249, ig, k), e = rayon * 0.4f;
				Vector2 tete = Iso(Mathf.Cos(a) * e, Mathf.Sin(a) * e, h * 1.2f);
				_lotPrairie.Ligne(Iso(0f, 0f, 0f), tete, Ton(pal.Flower, 1), PixelInterne);
				// Panicule lâche : quelques épillets roux autour du bout de la tige.
				for (int m = 0; m < 5; m++)
				{
					float s = (1.8f * Hash01(251, ig + k, m) + 0.5f) * WorldView.PxPerCmX;
					float b = Mathf.Tau * Hash01(253, ig + k, m);
					PoserDisque(tete + new Vector2(s * Mathf.Cos(b), s * (0.8f * Mathf.Sin(b) + 0.8f)),
						Mathf.Max(0.5f * WorldView.PxPerCmX, PixelInterne), Ton(pal.Flower, PaletteIndexee.TonBase));
				}
			}
		}

		// ---------------------------------------------------------------------------
		// PLANTAIN LANCÉOLÉ
		// ---------------------------------------------------------------------------

		private void DessinerPlantain(Color col)
		{
			var (rayon, h) = MesurePrairie(PortPrairie.Plantain);
			float g = CroissancePrairie(PortPrairie.Plantain);
			int ig = GraineIndividu;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.DensiteVisible * 2f, DensitePlancher, 1f);
			int n = Mathf.Max(3, Mathf.RoundToInt(FeuillesPlantain * Mathf.Lerp(0.5f, 1f, g) * dens));
			if (FleuriPrairie(FloraisonHampe)) PoserHampes(h, g, ig);
			// De l'extérieur vers le cœur : les jeunes feuilles se posent sur les vieilles.
			for (int k = 0; k < n; k++)
			{
				float a = k * 2.39996f + Mathf.Tau * Hash01(261, ig, 0);
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				float l = rayon * Mathf.Lerp(1f, 0.6f, k / (float)n) * Mathf.Lerp(0.85f, 1f, Hash01(263, ig, k));
				int ton = k < n / 3 ? 1 : k < n * 3 / 4 ? PaletteIndexee.TonBase : 3;
				PoserFeuillePlantain(u, l, col, ton);
				if (k >= n / 2)
					_sitesPrairie.Add((Iso(u.X * l * 0.6f, u.Y * l * 0.6f, 2f), l * 0.2f * WorldView.PxPerCmX, k, 2f));
			}
		}

		private void PoserFeuillePlantain(Vector2 u, float l, Color col, int ton)
		{
			var v = new Vector2(-u.Y, u.X);
			float w = l * LargeurPlantain, zf = AplatMort;
			_contourPrairie.Clear();
			foreach (Vector2 q in ProfilLanceole)
				_contourPrairie.Add(PointLanceole(u, v, l, w, q.X, q.Y, zf));
			PoserEventail(_contourPrairie, new Vector2(0f, PixelInterne), Ton(col, 0));
			PoserEventail(_contourPrairie, Vector2.Zero,
				Ton(col, ton, Orientation(WorldView.WorldToScreenOffset(u.X, u.Y))));
			if (!AuPalier(PalierOrganesZoom)) return;
			// Nervures parallèles : une dès ×8, trois dès ×16 (le signe de l'espèce).
			Color nerv = Ton(col, Mathf.Min(ton + 2, 4));
			float pix = PixelInterne;
			_lotPrairie.Ligne(PointLanceole(u, v, l, w, 0.1f, 0f, zf), PointLanceole(u, v, l, w, 0.95f, 0f, zf), nerv, pix);
			if (!AuPalier(PalierSymptomesZoom)) return;
			foreach (float cote in new[] { 0.45f, -0.45f })
				_lotPrairie.Ligne(PointLanceole(u, v, l, w, 0.15f, cote * 0.5f, zf),
					PointLanceole(u, v, l, w, 0.85f, cote, zf), nerv, pix);
		}

		// Feuille plaquée au sol, le bout relevé.
		private Vector2 PointLanceole(Vector2 u, Vector2 v, float l, float w, float lg, float lr, float zf)
		{
			Vector2 m = u * (lg * l) + v * (lr * w);
			return Iso(m.X, m.Y, (0.5f + LeveePlantainCm * lg * lg) * zf);
		}

		private void PoserHampes(float h, float g, int ig)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * 4f), 1, 4);
			float pxx = WorldView.PxPerCmX;
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(265, ig, k), e = 4f * Hash01(267, ig, k);
				float haut = h * Mathf.Lerp(1f, 1.25f, Hash01(269, ig, k));
				Vector2 tete = Iso(Mathf.Cos(a) * e, Mathf.Sin(a) * e, haut);
				_lotPrairie.Ligne(Iso(0f, 0f, 0f), tete, Ton(pal.Leaf, 1), PixelInterne);
				// Épi court et trapu, plus sombre vers le bas.
				float rx = Mathf.Max(1.2f * pxx, PixelInterne), ry = Mathf.Max(2.4f * pxx, PixelInterne);
				_lotPrairie.Ellipse(tete, rx, ry, Ton(pal.Flower, 1));
				_lotPrairie.Ellipse(tete - new Vector2(0f, ry * 0.3f), rx * 0.7f, ry * 0.65f,
					Ton(pal.Flower, PaletteIndexee.TonBase));
				if (_structure.Floraison < FloraisonSeuil) continue;
				// Anthèse : couronne d'anthères claires à mi-épi.
				for (int m = 0; m < 6; m++)
				{
					float b = Mathf.Tau * m / 6f;
					PoserDisque(tete + new Vector2((rx + PixelInterne) * Mathf.Cos(b), ry * 0.3f * Mathf.Sin(b)),
						PixelInterne, Ton(pal.FruitRipe, 4));
				}
			}
		}
	}
}
