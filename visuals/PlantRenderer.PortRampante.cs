// SYMBIOSE — PlantRenderer.PortRampante.cs (partial, sprint FORMES DES PLANTES ④)
// Le port GRANDE RAMPANTE : immenses feuilles palmées portées par leur pétiole, large et bas,
// grosse trompette jaune. Courgette seule ; le fruit est celui du moteur, dessiné par le socle
// (PlantRenderer.Ports.cs) et récolté au clic. Le port ne court pas : c'est une touffe, à
// l'empreinte que le moteur lui donne.
//
// 📖 Pédagogie : la feuille-paume se pose en éventail depuis son attache, comme toutes les
// feuilles de port : son contour doit donc être ÉTOILÉ depuis la base (chaque point visible depuis
// (0,0)). Les 5 lobes tiennent dans ce cadre tant que leurs creux restent sur le rayon qui les
// sépare. Le limbe fait 9 px à ×1 : ici le contour est utile dès le palier le plus bas, et il
// coûte 15 triangles, bien moins qu'une colonie de losanges.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private static readonly Vector2[] ContourPaume = Symetrique(new(0f, 0f), new(-0.05f, 0.45f), new(0.14f, 0.92f),
			new(0.27f, 1f), new(0.34f, 0.55f), new(0.53f, 0.86f), new(0.66f, 0.78f), new(0.66f, 0.3f), new(0.92f, 0.3f), new(1f, 0f));

		private void DessinerRampante(FichePort f, Color col)
		{
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			float souche = Mathf.Max(rayon * 0.2f * WorldView.PxPerCmX, PixelInterne * 2f);
			PoserEllipse(Vector2.Zero, souche, souche * 0.5f, Ton(col, 0));   // « sol à peine visible » : l'ombre dense
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1f);
			int n = Mathf.Max(2, Mathf.RoundToInt(f.Feuilles * Mathf.Lerp(0.4f, 1f, g) * dens));
			float phase = Mathf.Tau * Hash01(481, ig, 0);
			_feuillesPort.Clear();
			for (int k = 0; k < n; k++)
			{
				float a = k * AngleOr + phase, part = k / (float)n;
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				// Du pourtour vers le cœur : les vieilles feuilles au loin et bas, les jeunes en haut.
				float d = rayon * Mathf.Lerp(0.5f, 0.2f, part), l = rayon * Mathf.Lerp(0.5f, 0.42f, part) * Mathf.Lerp(0.85f, 1f, Hash01(483, ig, k));
				float z = h * Mathf.Lerp(0.5f, 0.95f, part) * Mathf.Lerp(0.85f, 1f, Hash01(485, ig, k));
				int ton = part < 0.33f ? 1 : part < 0.75f ? PaletteIndexee.TonBase : 3;
				var fe = new FeuillePosee(u, l, l * f.LargeurFeuille, z, -z * 0.25f, 0f, ton, k, u * d);
				_feuillesPort.Add((WorldView.WorldToScreenOffset(u.X * d, u.Y * d).Y + z * WorldView.PxPerCmZ * 0.5f, fe));
			}
			_feuillesPort.Sort(static (x, y) => x.Prof.CompareTo(y.Prof));
			for (int i = 0; i < _feuillesPort.Count; i++)
			{
				FeuillePosee fe = _feuillesPort[i].F;
				PoserFeuillePaume(fe, col);
				if (i >= _feuillesPort.Count / 2)
					_sitesPrairie.Add((PointFeuille(fe, 0.6f, 0f), fe.Large * 0.5f * WorldView.PxPerCmX, fe.K, fe.BaseZ));
			}
			PoserTrompettes(f, h, g, ig);
		}

		private void PoserFeuillePaume(FeuillePosee fe, Color col)
		{
			float pix = PixelInterne;
			Vector2 attache = PointFeuille(fe, 0f, 0f);
			_lotPrairie.Ligne(Iso(0f, 0f, 1f), attache, Ton(col, 3), AuPalier(PaliersHautsMinZoom) ? pix * 2f : pix);
			_contourPrairie.Clear();
			foreach (Vector2 q in ContourPaume) _contourPrairie.Add(PointFeuille(fe, q.X, q.Y));
			if (AuPalier(PaliersHautsMinZoom)) PoserEventail(_contourPrairie, new Vector2(0f, pix * 2f), Ton(col, 0));
			PoserEventail(_contourPrairie, Vector2.Zero, Ton(col, fe.Ton, Orientation(WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y))));
			if (!AuPalier(PalierOrganesZoom)) return;
			DetaillerLimbe(fe, col);
			// Marbrure argent le long des nervures, le signe de l'espèce de près.
			Color argent = Ton(col, 4);
			_lotPrairie.Ligne(attache, PointFeuille(fe, 0.9f, 0f), argent, pix);
			foreach (float cote in new[] { 1f, -1f })
			{
				_lotPrairie.Ligne(attache, PointFeuille(fe, 0.55f, 0.65f * cote), argent, pix);
				_lotPrairie.Ligne(attache, PointFeuille(fe, 0.18f, 0.8f * cote), argent, pix);
			}
		}

		// Une ou deux trompettes au cœur de la touffe, en vraie floraison seulement.
		private void PoserTrompettes(FichePort f, float h, float g, int ig)
		{
			if (MortPrairie || _structure.Rabattu > RabattuTete || _structure.Floraison < FloraisonSeuil) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * 2f), 1, 2);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(487, ig, k), d = f.RayonCm * g * 0.12f;
				Vector2 c = Iso(d * Mathf.Cos(a), d * Mathf.Sin(a), h * Mathf.Lerp(1f, 0.85f, k));
				PoserTete(f, c, c, pal.Flower, ig + k);
			}
		}

		// Trompette : un cornet, un pavillon à 5 lobes, le fond orangé. Icône de l'espèce à ×1.
		private void PoserTrompette(Vector2 c, float r, Color col)
		{
			float pix = PixelInterne;
			Color fond = Ton(col, 1), corps = Ton(col, PaletteIndexee.TonBase), clair = Ton(col, 3);
			_lotPrairie.Triangle(c + new Vector2(-r * 0.7f, 0f), c + new Vector2(r * 0.7f, 0f), c + new Vector2(0f, r * 1.1f), corps);
			PoserEllipse(c, r, r * 0.7f, clair);
			if (AuPalier(PaliersHautsMinZoom))
				for (int k = 0; k < 5; k++)
				{
					float a = k * Mathf.Tau / 5f + 0.3f;
					Vector2 bout = c + new Vector2(Mathf.Cos(a) * r * 1.2f, Mathf.Sin(a) * r * 0.85f);
					var flanc = new Vector2(-Mathf.Sin(a), Mathf.Cos(a)) * r * 0.45f;
					_lotPrairie.Triangle(c + flanc, bout, c - flanc, clair);
				}
			PoserEllipse(c, Mathf.Max(r * 0.42f, pix), Mathf.Max(r * 0.3f, pix), fond);
		}
	}
}
