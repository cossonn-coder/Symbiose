// SYMBIOSE — PlantRenderer.PortTetes.cs (partial, sprint FORMES DES PLANTES ②)
// Hampes et têtes des ports : capitule, bouquet, chapelet, épi, ombelle, boule, grappe. La
// fleur est l'icône de l'espèce à ×1 : ces formes tiennent à tous les paliers (conception
// §4.5 : motif estampillé, 3 tons, contour sélectif sur les fleurs). Une hampe coupée
// (`rabattu`) perd sa tête : c'est le geste qui se voit.
//
// Tête d'une hampe levée : couleur de fleur en anthèse, de fruit mûr si le moteur en est à la
// fructification (`organ`), de fruit vert en bouton. Le chapelet de la bourse-à-pasteur et la
// tête de graines ne sont PAS des fruits moteur (non `fruitier`) : marques de stade, sans
// état ni récolte (fiches §Lire).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Au-dessus, le pied a été coupé : plus de tête tant qu'il n'a pas repoussé.
		private const float RabattuTete = 0.25f;

		private void PoserHampesPort(FichePort f, float h, float g, int ig, Color col, OrganPalette pal)
		{
			int n = f.StadesHampe != null ? f.Hampes
				: Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * f.Hampes), 1, f.Hampes);
			float large = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX, PixelInterne * 1.25f);   // un trait plus fin que le pixel saute des pixels
			bool coupee = _structure.Rabattu > RabattuTete;
			Color tete = _structure.Floraison >= FloraisonSeuil ? pal.Flower
				: _structure.Organ.StartsWith("fruit", System.StringComparison.Ordinal) ? pal.FruitRipe : pal.FruitUnripe;
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(321, ig, k), e = f.RayonCm * 0.12f * Hash01(323, ig, k);
				// La première hampe fait la hauteur moteur, les autres sont un peu plus courtes.
				float haut = h * (k == 0 ? 1f : Mathf.Lerp(0.72f, 0.95f, Hash01(325, ig, k)));
				Vector2 pied = Iso(0f, 0f, 0f), sommet = Iso(Mathf.Cos(a) * e, Mathf.Sin(a) * e, haut);
				_lotPrairie.Ligne(pied, sommet, Ton(pal.Leaf, k == 0 ? 3 : PaletteIndexee.TonBase), large);
				if (k == 0 && f.FeuillesHampe > 0) PoserFeuillesHampe(f, haut, ig, col);
				if (!coupee) PoserTete(f, pied, sommet, tete, ig + k * 11);
			}
		}

		// Feuilles collées à la hampe, plus petites en montant (molène).
		private void PoserFeuillesHampe(FichePort f, float h, int ig, Color col)
		{
			for (int i = 0; i < f.FeuillesHampe; i++)
			{
				float t = (i + 0.5f) / f.FeuillesHampe;
				float a = i * 2.39996f + Hash01(327, ig, 0) * Mathf.Tau;
				float l = f.RayonCm * Mathf.Lerp(0.5f, 0.12f, t);
				var fe = new FeuillePosee(new Vector2(Mathf.Cos(a), Mathf.Sin(a)), l, l * f.LargeurFeuille,
					h * 0.62f * t, l * 0.3f, 0.3f, i % 3 == 0 ? 1 : PaletteIndexee.TonBase, i);
				_contourPrairie.Clear();
				foreach (Vector2 q in ContourDe(f.Feuille)) _contourPrairie.Add(PointFeuille(fe, q.X, q.Y));
				PoserEventail(_contourPrairie, Vector2.Zero, Ton(col, fe.Ton));
			}
		}

		private void PoserTete(FichePort f, Vector2 pied, Vector2 sommet, Color c, int graine)
		{
			float pix = PixelInterne, pxx = WorldView.PxPerCmX;
			float r = Mathf.Max(f.TeteCm * pxx, pix);
			switch (f.Tete)
			{
				case FormeTete.Capitule:
					// Tête de graines (aigrette) : boule claire ; en fleur : disque plein à plat.
					if (c != FleurDe()) { PoserBoule(sommet, r * 1.3f, c, graine); break; }
					PoserEllipse(sommet, r + pix, (r + pix) * 0.7f, Ton(c, 0));
					PoserEllipse(sommet, r, r * 0.7f, Ton(c, PaletteIndexee.TonBase));
					PoserEllipse(sommet - new Vector2(0f, r * 0.12f), r * 0.65f, r * 0.42f, Ton(c, 3));
					break;
				case FormeTete.Boule: PoserBoule(sommet, r, c, graine); break;
				case FormeTete.Bouquet: PoserBouquet(sommet, r, c, graine, 6); break;
				case FormeTete.Grappe: PoserGrappe(sommet, r, c, graine); break;
				case FormeTete.Chapelet: PoserChapelet(pied, sommet, r, c, graine); break;
				case FormeTete.Epi: PoserEpi(pied, sommet, r, c, graine); break;
				case FormeTete.Soleil: PoserSoleil(sommet, r, c); break;
				case FormeTete.Etoile: PoserEtoile(sommet, r, c); break;
				case FormeTete.Pendante: PoserPendante(sommet, r, c, graine); break;
				case FormeTete.Corolle: PoserCorolle(sommet, r, c); break;
				case FormeTete.Trompette: PoserTrompette(sommet, r, c); break;
				case FormeTete.Aucune: break;
				default: PoserOmbelle(pied, sommet, r, c, graine); break;
			}
		}

		// Ellipse à 12 côtés : à la taille d'une tête, les 64 de LotTriangles.Ellipse (fidélité
		// au pixel de l'ancien draw_ellipse) coûtent 5 fois plus de sommets pour le même dessin.
		private void PoserEllipse(Vector2 c, float rx, float ry, Color col)
		{
			int N = CotesPour(Mathf.Max(rx, ry), 12);
			Vector2 prem = c + new Vector2(rx, 0f), prec = prem;
			for (int i = 1; i < N; i++)
			{
				float a = i * Mathf.Tau / N;
				Vector2 cour = c + new Vector2(rx * Mathf.Cos(a), ry * Mathf.Sin(a));
				if (i > 1) _lotPrairie.Triangle(prem, prec, cour, col);
				prec = cour;
			}
		}

		// Côtés utiles à ce rayon : sous 1,5 px d'écran un disque est un losange, sous 4 px un
		// hexagone, mêmes pixels à un près (FORMES DES PLANTES ③, coût de cuisson au sommet).
		private static int CotesPour(float r, int max)
		{
			float px = r * WorldView.CurrentZoom;
			return px < 1.5f ? 4 : px < 4f ? 6 : max;
		}

		private Color FleurDe() =>
			(Palettes.TryGetValue(_structure.SpeciesName, out var pal) ? pal : DefaultPalette).Flower;

		// Petits points serrés autour du sommet.
		private void PoserBouquet(Vector2 c, float r, Color col, int graine, int n)
		{
			float pix = PixelInterne;
			PoserDisque(c, r * 0.7f, Ton(col, 1));
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(331, graine, k), d = r * Mathf.Sqrt(Hash01(333, graine, k));
				PoserDisque(c + new Vector2(d * Mathf.Cos(a), d * 0.8f * Mathf.Sin(a)), Mathf.Max(r * 0.28f, pix), Ton(col, k % 3 == 0 ? 4 : 3));
			}
		}

		// Grappe penchée d'un côté (drosera) : quelques points en crosse.
		private void PoserGrappe(Vector2 c, float r, Color col, int graine)
		{
			float sens = Hash01(335, graine, 0) < 0.5f ? 1f : -1f;
			for (int k = 0; k < 4; k++)
				PoserDisque(c + new Vector2(sens * k * r * 0.9f, k * k * r * 0.25f), Mathf.Max(r * 0.8f, PixelInterne), Ton(col, 3));
		}

		// Bourse-à-pasteur : petit bouquet au sommet, silicules en triangle le long de la hampe.
		private void PoserChapelet(Vector2 pied, Vector2 sommet, float r, Color col, int graine)
		{
			float pix = PixelInterne;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			PoserBouquet(sommet, r, pal.Flower, graine, 4);
			Color sil = Ton(pal.FruitUnripe, 3), fil = Ton(pal.FruitUnripe, 1);
			float s = Mathf.Max(r * 1.3f, pix);
			for (int k = 0; k < 8; k++)
			{
				var axe = pied.Lerp(sommet, Mathf.Lerp(0.42f, 0.92f, k / 7f));
				float cote = k % 2 == 0 ? 1f : -1f;
				var bout = axe + new Vector2(cote * (s + pix), -pix);
				_lotPrairie.Ligne(axe, bout, fil, pix);
				// Le cœur renversé : pointe vers la tige, large vers l'extérieur.
				_lotPrairie.Triangle(bout, bout + new Vector2(cote * s, -s * 0.9f), bout + new Vector2(cote * s, s * 0.9f), sil);
			}
		}

		// Molène : tiers haut du cierge couvert de fleurs serrées, plus étroit au bout.
		private void PoserEpi(Vector2 pied, Vector2 sommet, float r, Color col, int graine)
		{
			// Autant de fleurs qu'il en faut pour que l'épi reste plein, quelle que soit sa hauteur.
			int N = Mathf.Clamp(Mathf.CeilToInt(pied.DistanceTo(sommet) * 0.34f / Mathf.Max(r * 0.6f, PixelInterne)), 3, 24);
			for (int k = 0; k < N; k++)
			{
				float t = k / (float)(N - 1);
				Vector2 c = pied.Lerp(sommet, Mathf.Lerp(0.66f, 1f, t));
				float rk = r * Mathf.Lerp(1f, 0.45f, t);
				int ton = Hash01(337, graine, k) < 0.35f ? 1 : k % 2 == 0 ? PaletteIndexee.TonBase : 3;
				PoserEllipse(c, rk, rk * 0.7f, Ton(col, ton));
			}
		}

		// Carotte : rayons qui partent d'un point, ombelle plate au-dessus.
		private void PoserOmbelle(Vector2 pied, Vector2 sommet, float r, Color col, int graine)
		{
			float pix = PixelInterne;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Vector2 foyer = sommet.Lerp(pied, 0.12f);
			if (AuPalier(PaliersHautsMinZoom))
				for (int k = 0; k < 7; k++)
				{
					float x = r * (k / 3f - 1f);
					_lotPrairie.Ligne(foyer, sommet + new Vector2(x, 0f), Ton(pal.Leaf, 1), pix);
				}
			PoserEllipse(sommet, r + pix, (r + pix) * 0.32f, Ton(col, 1));
			PoserEllipse(sommet - new Vector2(0f, pix), r, r * 0.28f, Ton(col, PaletteIndexee.TonBase));
			if (!AuPalier(PalierOrganesZoom)) return;
			for (int k = 0; k < 10; k++)
			{
				float a = Mathf.Tau * Hash01(339, graine, k), d = r * Mathf.Sqrt(Hash01(341, graine, k));
				PoserDisque(sommet + new Vector2(d * Mathf.Cos(a), d * 0.25f * Mathf.Sin(a) - pix), pix, Ton(col, 4));
			}
		}
	}
}
