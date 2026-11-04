// SYMBIOSE — PlantRenderer.PortTapis.cs (partial, sprint FORMES DES PLANTES ④)
// Le port COUVRE-SOL : tapis bas, stolons ou coussin, pas de tige lisible. Fraisier, violette,
// minette, sphaigne : même fonction, la différence est dans la table (PortsFiches.cs).
//
// 📖 Le TAPIS sort de la géométrie, comme le trèfle (PlantRenderer.Prairie.cs) : un pied couvre
// un disque plus large que l'écart entre ramets d'une colonie. Aucune couche neuve : les disques
// se recouvrent et les quads se trient en Y comme toutes les plantes.
//
// 📖 Pédagogie : les feuilles se posent en TOURNESOL, angle d'or (137,5°) et distance en racine
// carrée de l'index. C'est la façon la plus simple de couvrir un disque sans rangée ni trou :
// l'aire couverte par les k premiers points croît comme k, donc leur densité reste égale.
//
// Échelle cumulative : ×1 une tache par feuille, le grain du tapis ; ×4 le contour des folioles,
// stolons ; ×8 ombre de feuille, gaufrage. Zéro écologie, zéro Random (philo #3).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float PartFeuillesLoinTapis = 0.6f;
		// Bas du dôme : le bord d'un tapis reste plus bas que son centre.
		private const float DomeTapis = 0.6f;

		private void DessinerTapis(FichePort f, Color col)
		{
			FicheTapis t = f.Tapis;
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			float couvert = rayon * t.Couvre;
			_feuillesPort.Clear();
			if (t.SousCouche) PoserSousCouche(couvert, col, ig);
			PoserStolons(t, col, rayon, g, ig);
			if (t.Grains > 0) { PoserCoussin(t, col, couvert, h, ig); return; }
			CollecterFeuillesTapis(f, couvert, h, g, ig);
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			for (int i = 0; i < _feuillesPort.Count; i++)
			{
				FeuillePosee fe = _feuillesPort[i].F;
				PoserFeuilleTapis(f, fe, col);
				if (i >= _feuillesPort.Count * 2 / 3)
					_sitesPrairie.Add((PointFeuille(fe, 0.5f, 0f), fe.Long * 0.7f * WorldView.PxPerCmX, fe.K, fe.BaseZ));
			}
			PoserFleursTapis(f, couvert, h, g, ig);
		}

		private void CollecterFeuillesTapis(FichePort f, float couvert, float h, float g, int ig)
		{
			FicheTapis t = f.Tapis;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1f);
			float loin = AuPalier(PaliersHautsMinZoom) ? 1f : PartFeuillesLoinTapis;
			int n = Mathf.Max(2, Mathf.RoundToInt(f.Feuilles * Mathf.Lerp(0.5f, 1f, g) * dens * loin));
			float taille = t.FeuilleCm * Mathf.Lerp(0.6f, 1f, g);
			float phase = Mathf.Tau * Hash01(421, ig, 0), rMax = Mathf.Max(couvert - taille, 1f);
			for (int k = 0; k < n; k++)
			{
				float a = k * AngleOr + phase;
				float d = rMax * Mathf.Sqrt((k + 0.5f) / n);
				var org = new Vector2(d * Mathf.Cos(a), d * Mathf.Sin(a));
				float z = h * (1f - DomeTapis * d / rMax) * Mathf.Lerp(0.6f, 1f, Hash01(423, ig, k));
				float azimut = Mathf.Tau * Hash01(425, ig, k);
				// Ton 3 ou 2 : à contre-soleil, une feuille perd un ton sans rejoindre la sous-couche.
				int ton = Hash01(427, ig, k) < 0.3f ? PaletteIndexee.TonBase : 3;
				var fe = new FeuillePosee(new Vector2(Mathf.Cos(azimut), Mathf.Sin(azimut)), taille, taille * f.LargeurFeuille,
					Mathf.Max(z - taille * 0.2f, 0.5f), taille * 0.2f, 0f, ton, k, org);
				_feuillesPort.Add((WorldView.WorldToScreenOffset(org.X, org.Y).Y, fe));
			}
		}

		private void PoserFeuilleTapis(FichePort f, FeuillePosee fe, Color col)
		{
			if (!AuPalier(PaliersHautsMinZoom))
			{
				float r = Mathf.Max(fe.Long * 1.05f, PixelInterne / WorldView.PxPerCmX);
				PoserTacheFeuille(new Vector3(fe.Org.X, fe.Org.Y, fe.BaseZ * AplatMort), r, col, fe.Ton);
				return;
			}
			int nb = Mathf.Max(f.Tapis.Folioles, 1);
			Color c = Ton(col, fe.Ton, (int)(Mathf.PosMod(Mathf.Atan2(fe.U.Y, fe.U.X), Mathf.Tau) / Mathf.Tau * 8f) & 7);
			bool pres = AuPalier(PalierOrganesZoom);
			for (int i = 0; i < nb; i++)
			{
				float a = i * Mathf.Tau / nb;
				var fo = fe with { U = fe.U.Rotated(a) };
				_contourPrairie.Clear();
				foreach (Vector2 q in ContourDe(f.Feuille)) _contourPrairie.Add(PointFeuille(fo, q.X, q.Y));
				if (pres) PoserEventail(_contourPrairie, new Vector2(0f, PixelInterne), Ton(col, 0));
				PoserEventail(_contourPrairie, Vector2.Zero, c);
				if (pres) DetaillerLimbe(fo, col);
				if (pres && f.Marque == MarqueFeuille.Gaufre) PoserGaufrage(fo, col);
			}
		}

		// Stolons, dès ×4 : ils courent au sol jusqu'au rayon. Plantule à leur bout (fraisier).
		private void PoserStolons(FicheTapis t, Color col, float rayon, float g, int ig)
		{
			if (t.Stolons == 0 || MortPrairie || !AuPalier(PaliersHautsMinZoom)) return;
			float pix = PixelInterne;
			int n = Mathf.Max(1, Mathf.RoundToInt(t.Stolons * g));
			Color trait = Ton(t.Stolon, PaletteIndexee.TonBase);
			for (int k = 0; k < n; k++)
			{
				float a = k * Mathf.Tau / n + Mathf.Tau * Hash01(431, ig, k) * 0.3f;
				float d = rayon * Mathf.Lerp(0.8f, 1f, Hash01(433, ig, k));
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				Vector2 mi = Iso(u.X * d * 0.55f, u.Y * d * 0.55f, 1.2f), bout = Iso(u.X * d, u.Y * d, 0.2f);
				_lotPrairie.Ligne(Iso(0f, 0f, 0.5f), mi, trait, pix);
				_lotPrairie.Ligne(mi, bout, trait, pix);
				if (!t.Plantules) continue;
				var pl = new FeuillePosee(u, 3f * g, 1.6f * g, 0.2f, 1f, 0f, 3, k, u * d);
				PoserLosange(pl, Ton(col, 3));
				PoserLosange(pl with { U = -u.Orthogonal() }, Ton(col, PaletteIndexee.TonBase));
			}
		}

		// Sphaigne : un coussin plein, grumeleux de capitules, sans feuille ni tige.
		private void PoserCoussin(FicheTapis t, Color col, float couvert, float h, int ig)
		{
			float pxx = WorldView.PxPerCmX, pix = PixelInterne;
			float rx = Mathf.Max(couvert * pxx, pix);
			PoserEllipse(Iso(0f, 0f, h * 0.35f * AplatMort), rx, rx * 0.5f + h * 0.35f * pxx, Ton(col, 3));
			int n = AuPalier(PaliersHautsMinZoom) ? t.Grains : t.Grains / 2;
			float phase = Mathf.Tau * Hash01(435, ig, 0), r = Mathf.Max(couvert * 0.07f * pxx, pix);
			for (int k = 0; k < n; k++)
			{
				float a = k * AngleOr + phase;
				float s = Mathf.Sqrt((k + 0.5f) / n), d = couvert * 0.92f * s;
				float z = h * Mathf.Sqrt(1f - s * s * 0.85f) * AplatMort;
				Vector2 c = Iso(d * Mathf.Cos(a), d * Mathf.Sin(a), z);
				PoserDisque(c, r, Ton(col, Hash01(437, ig, k) < 0.25f ? 4 : Hash01(437, ig, k) < 0.6f ? PaletteIndexee.TonBase : 3));
				if (k % 5 == 0) _sitesPrairie.Add((c, r, k, z));
				if (!AuPalier(PalierOrganesZoom)) continue;
				// La petite étoile du capitule, seul détail qu'on lit de près.
				Color eclat = Ton(col, 1);
				_lotPrairie.Ligne(c - new Vector2(r * 0.6f, 0f), c + new Vector2(r * 0.6f, 0f), eclat, pix);
				_lotPrairie.Ligne(c - new Vector2(0f, r * 0.5f), c + new Vector2(0f, r * 0.5f), eclat, pix);
			}
		}

		// Fleurs juste au-dessus des feuilles. Seul l'état moteur les allume (`floraison`, `organ`) ;
		// une fruitière ne montre que ses fleurs, ses fruits sont les vrais.
		private void PoserFleursTapis(FichePort f, float couvert, float h, float g, int ig)
		{
			FicheTapis t = f.Tapis;
			bool fruit = f.Fruit == null && _structure.Organ.StartsWith("fruit", System.StringComparison.Ordinal);
			if (t.Fleurs == 0 || MortPrairie || _structure.Rabattu > RabattuTete
				|| (_structure.Floraison < FloraisonSeuil && !fruit)) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color tete = _structure.Floraison >= FloraisonSeuil ? pal.Flower : pal.FruitRipe;
			int n = Mathf.Clamp(Mathf.CeilToInt(Mathf.Max(_structure.Floraison, fruit ? 0.5f : 0f) * g * t.Fleurs), 1, t.Fleurs);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(441, ig, k), d = couvert * 0.8f * Mathf.Sqrt(Hash01(443, ig, k));
				float x = d * Mathf.Cos(a), y = d * Mathf.Sin(a);
				Vector2 c = Iso(x, y, h * Mathf.Lerp(0.8f, 1.05f, Hash01(445, ig, k)));
				if (AuPalier(PalierOrganesZoom)) _lotPrairie.Ligne(Iso(x, y, 0.5f), c, Ton(pal.Leaf, 1), PixelInterne);
				PoserTete(f, c, c, tete, ig + k * 11);
			}
		}

		// Corolle (fraisier, violette, framboisier) : une tache loin, 5 pétales ronds et un cœur près.
		// La couleur n'est pas celle de la fleur : une marque de stade, sans détail.
		private static readonly Color CoeurCorolle = new("e8c830");

		private void PoserCorolle(Vector2 c, float r, Color col)
		{
			float pix = PixelInterne;
			if (col != FleurDe() || !AuPalier(PaliersHautsMinZoom)) { PoserDisque(c, r, Ton(col, 3)); return; }
			Color petale = Ton(col, 3);
			if (AuPalier(PalierOrganesZoom)) PoserDisque(c, r * 1.1f + pix, Ton(col, 0));   // contour sélectif
			PoserDisque(c, r, Ton(col, PaletteIndexee.TonBase));
			for (int k = 0; k < 5; k++)
			{
				float a = k * Mathf.Tau / 5f - Mathf.Pi * 0.5f;
				PoserDisque(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.8f) * r * 0.65f, Mathf.Max(r * 0.45f, pix), petale);
			}
			PoserDisque(c, Mathf.Max(r * 0.28f, pix), Ton(CoeurCorolle, 3));
		}
	}
}
