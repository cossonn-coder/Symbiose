// SYMBIOSE — PlantRenderer.PortBuisson.cs (partial, sprint FORMES DES PLANTES ④)
// Le port BUISSON ou COUSSIN : masse d'aspect ligneux. Coussin de thym, boule de lavande à
// épis, balai de la myrtille, cannes arquées du framboisier : même fonction, deux briques
// (masse de grains, cannes) que la table dose (PlantRenderer.PortsFiches.cs).
//
// 📖 Pédagogie : la canne est une FONCTION de t ∈ [0,1], `PointCanne`, sans rien en mémoire.
// Le dessin l'échantillonne, et le point d'un fruit la relit (`PointFruitCanne`) : le fruit est
// ainsi posé sur la canne dessinée, et le clic qui le récolte vise le même point. C'est le
// principe de « une seule source de vérité », ici à l'échelle d'une formule.
//
// 📖 L'arc : on parcourt un quart de cercle, élargi par `Arc`. Au-delà de 90°, le sinus redescend :
// le bout de la canne retombe sous son sommet, et rien d'autre n'est à coder.
//
// Mort : plus de feuilles ni de masse, le bois sec reste debout (comme un squelette ligneux du
// moteur) et s'aplatit quand le pied se couche. Zéro écologie, zéro Random (philo #3).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private void DessinerBuisson(FichePort f, Color col)
		{
			FicheBuisson b = f.Buisson;
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			// Sans plancher : un caduc d'hiver montre son bois nu, c'est ce qui le distingue.
			float dens = MortPrairie ? 0f : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, 0f, 1f);
			Color bois = MortPrairie ? col : b.Bois;
			_axesTige.Clear();
			_tetesTige.Clear();
			_feuillesPort.Clear();

			float souche = Mathf.Max(rayon * 0.25f * WorldView.PxPerCmX, PixelInterne * 2f);
			PoserEllipse(Vector2.Zero, souche, souche * 0.5f, Ton(bois, 1));
			float zMasse = HauteurFeuilles(f) * h / Mathf.Max(MesureBrute(f), 1f);
			PoserBoisBas(f, b, bois, rayon, zMasse, ig);
			if (b.Grains > 0 && !MortPrairie) PoserMasse(f, b, col, rayon, zMasse, dens, ig);
			if (b.Cannes > 0 && (f.Hampes == 0 || HampeLevee(f)))
			{
				CollecterCannes(f, b, rayon, h, g, dens, ig);
				_feuillesPort.Sort(static (x, y) => x.Prof.CompareTo(y.Prof));
				PeindreFeuillesEtAxes(f, col, bois);
				PoserTetesPort(f, col, b.EpiCm);
			}
			PoserFleursMasse(f, b, rayon, zMasse, g, ig);
		}

		private static int CannesDe(FicheBuisson b, float g) => Mathf.Max(1, Mathf.RoundToInt(b.Cannes * Mathf.Lerp(0.5f, 1f, g)));

		// Point de la canne `a` sur `n`, à t ∈ [0,1], et sa direction au sol.
		private (Vector3 P, Vector2 U) PointCanne(FicheBuisson b, int a, int n, float t, float rayon, float h, int ig)
		{
			float azimut = a * AngleOr + Mathf.Tau * Hash01(451, ig, 0);
			var u = new Vector2(Mathf.Cos(azimut), Mathf.Sin(azimut));
			float d = rayon * b.Ecart * Mathf.Sqrt((a + 0.5f) / n);
			float haut = h * (a == 0 ? 1f : Mathf.Lerp(0.72f, 0.95f, Hash01(453, ig, a)));
			float thMax = Mathf.Pi * 0.5f * (1f + 0.6f * b.Arc), th = t * thMax;
			float s = d + rayon * b.Evase * (1f - Mathf.Cos(th)) / (1f - Mathf.Cos(thMax));
			return (new Vector3(u.X * s, u.Y * s, haut * Mathf.Sin(th)), u);
		}

		private void CollecterCannes(FichePort f, FicheBuisson b, float rayon, float h, float g, float dens, int ig)
		{
			int n = CannesDe(b, g);
			int tronçons = b.Arc > 0f ? 4 : 1;
			float large = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX, PixelInterne * 1.25f);
			float loin = AuPalier(PaliersHautsMinZoom) ? 1f : PartFeuillesLoinTige;
			for (int a = 0; a < n; a++)
			{
				int graine = ig + a * 37;
				Vector3 prec = PointCanne(b, a, n, 0f, rayon, h, ig).P;
				for (int i = 1; i <= tronçons; i++)
				{
					Vector3 cour = PointCanne(b, a, n, i / (float)tronçons, rayon, h, ig).P;
					_axesTige.Add((prec, cour, large));
					prec = cour;
				}
				var (bout, ub) = PointCanne(b, a, n, 1f, rayon, h, ig);
				_tetesTige.Add((bout, ub, graine));
				int nf = b.FeuillesCanne == 0 ? 0 : Mathf.Max(2, Mathf.RoundToInt(b.FeuillesCanne * Mathf.Lerp(0.5f, 1f, g) * loin));
				for (int i = 0; i < nf; i++)
				{
					float s = (i + 0.5f) / nf;
					var (p, _) = PointCanne(b, a, n, Mathf.Lerp(b.BasNu, 1f, s), rayon, h, ig);
					float l = Mathf.Lerp(b.FeuilleBasCm, b.FeuilleHautCm, s) * Mathf.Lerp(0.4f, 1f, g);
					AjouterFeuilleTige(f, p, Mathf.Tau * Hash01(455, graine, i), l, s, rayon, dens, graine + i * 2, b.Penche);
				}
				for (int i = 0; i < b.Rameaux; i++)
					CollecterRameauBalai(f, b, a, n, i, rayon, h, g, dens, large, ig);
			}
		}

		// Balai de la myrtille : rameaux droits et anguleux, qui repartent vers le haut.
		private void CollecterRameauBalai(FichePort f, FicheBuisson b, int a, int n, int i, float rayon, float h, float g, float dens, float large, int ig)
		{
			float s = (i + 0.5f) / b.Rameaux;
			var (p, u) = PointCanne(b, a, n, Mathf.Lerp(0.3f, 0.85f, s), rayon, h, ig);
			float az = Mathf.Atan2(u.Y, u.X) + (i % 2 == 0 ? 1f : -1f) * 0.8f;
			var ur = new Vector2(Mathf.Cos(az), Mathf.Sin(az));
			float l = rayon * b.RameauLong * (1f - 0.5f * s);
			var bout = new Vector3(p.X + ur.X * l, p.Y + ur.Y * l, Mathf.Min(p.Z + l * 0.9f, h));
			_axesTige.Add((p, bout, Mathf.Max(large * 0.7f, PixelInterne)));
			if (i % 2 == 0) _tetesTige.Add((bout, ur, ig + a * 41 + i));   // une tête sur deux : la grappe coûte
			int k = ig + a * 43 + i * 5;
			AjouterFeuilleTige(f, p.Lerp(bout, 0.5f), az + 1f, b.FeuilleHautCm * Mathf.Lerp(0.4f, 1f, g), s, rayon, dens, k, b.Penche);
			AjouterFeuilleTige(f, bout, az - 1f, b.FeuilleHautCm * Mathf.Lerp(0.4f, 1f, g), s, rayon, dens, k + 1, b.Penche);
		}

		/// <summary>Là où le moteur a un fruit `i`, sur une canne : le fruit tient à ce qu'on voit.
		/// Le haut des cannes en porte le plus, jamais le pied.</summary>
		private Vector3 PointFruitCanne(FichePort f, FicheBuisson b, int i, float rayon, float h)
		{
			int ig = GraineIndividu, n = CannesDe(b, CroissancePort(f));
			var (p, u) = PointCanne(b, i % n, n, Mathf.Lerp(0.4f, 0.95f, Hash01(457, ig, i)), rayon, h, ig);
			float cote = Hash01(459, ig, i) < 0.5f ? 1f : -1f;
			return p + new Vector3(-u.Y * cote * 2f, u.X * cote * 2f, -1.5f);
		}

		// Bois bas : ce qu'on voit au pied d'un vieux coussin, et tout ce qui reste d'un pied mort.
		private void PoserBoisBas(FichePort f, FicheBuisson b, Color bois, float rayon, float zMasse, int ig)
		{
			if (b.BoisBas == 0 || (!MortPrairie && !AuPalier(PaliersHautsMinZoom))) return;
			float large = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX * 0.6f, PixelInterne);
			float haut = MortPrairie ? zMasse * 0.8f : zMasse * 0.4f;
			Color c = Ton(bois, PaletteIndexee.TonBase);
			for (int k = 0; k < b.BoisBas; k++)
			{
				float a = k * AngleOr + Mathf.Tau * Hash01(461, ig, 0), d = rayon * 0.7f;
				float ux = Mathf.Cos(a), uy = Mathf.Sin(a);
				// Tortueux : un coude au hash, à mi-longueur.
				float e = Mathf.Lerp(0.2f, 0.7f, Hash01(463, ig, k));
				Vector2 mi = Iso(ux * d * e, uy * d * e, haut * 0.55f * AplatMort);
				_lotPrairie.Ligne(Iso(0f, 0f, 0f), mi, c, large);
				_lotPrairie.Ligne(mi, Iso(ux * d, uy * d, haut * AplatMort), c, large);
			}
		}

		// La masse : un dôme sombre et, dessus, des grains ou des lames (lavande, feuille linéaire).
		// `dens` les fait tomber ; le dôme reste tant que le pied vit : ce sont des persistants.
		private void PoserMasse(FichePort f, FicheBuisson b, Color col, float rayon, float z, float dens, int ig)
		{
			float pxx = WorldView.PxPerCmX, pix = PixelInterne;
			Vector2 centre = Iso(0f, 0f, z * 0.45f);
			float rx = rayon * pxx * 0.9f, ry = rayon * 0.45f * pxx + z * 0.45f * pxx;
			PoserEllipse(centre, rx, ry, Ton(col, 1));
			bool lameuse = f.Feuille == FormeFeuille.Ruban, lames = lameuse && AuPalier(PaliersHautsMinZoom);
			float loin = AuPalier(PaliersHautsMinZoom) ? 1f : PartFeuillesLoinTige;
			int n = Mathf.Max(4, Mathf.RoundToInt(b.Grains * Mathf.Lerp(0.5f, 1f, dens) * loin));
			float phase = Mathf.Tau * Hash01(465, ig, 0);
			float r = Mathf.Max((lameuse ? b.GrainCm * 0.4f : b.GrainCm) * pxx, pix);
			float lame = b.GrainCm * pxx;
			for (int k = 0; k < n; k++)
			{
				float a = k * AngleOr + phase, s = Mathf.Sqrt((k + 0.5f) / n);
				float ux = Mathf.Cos(a), uy = Mathf.Sin(a);
				// Sur le disque que le dôme occupe À L'ÉCRAN : posés en 3D, les grains montaient
				// tous vers son sommet et laissaient son flanc avant nu (captures ×8).
				Vector2 c = centre + new Vector2(ux * s * rx, uy * s * ry);
				float h1 = Hash01(467, ig, k);
				int ton = h1 < 0.55f ? PaletteIndexee.TonBase : h1 < 0.88f ? 3 : 4;
				Color teinte = Ton(col, ton, Orientation(new Vector2(ux, uy)));
				if (lames)
					_lotPrairie.Ligne(c, c + new Vector2(ux * lame * 0.5f, -lame), teinte, Mathf.Max(0.9f * pxx, pix));
				else PoserDisque(c, r, teinte);
				if (k % 5 == 0) _sitesPrairie.Add((c, r * 1.5f, k, z));
			}
		}

		// Têtes collées à la masse, sans hampe (thym).
		private void PoserFleursMasse(FichePort f, FicheBuisson b, float rayon, float z, float g, int ig)
		{
			if (b.FleursMasse == 0 || MortPrairie || _structure.Rabattu > RabattuTete || _structure.Floraison < FloraisonSeuil) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * b.FleursMasse), 1, b.FleursMasse);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(471, ig, k), s = Mathf.Sqrt(Hash01(473, ig, k)) * 0.9f;
				Vector2 c = Iso(rayon * s * Mathf.Cos(a), rayon * s * Mathf.Sin(a), z * Mathf.Sqrt(1f - s * s * 0.85f));
				PoserTete(f, c, c, pal.Flower, ig + k * 11);
			}
		}
	}
}
