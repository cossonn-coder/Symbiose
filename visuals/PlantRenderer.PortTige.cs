// SYMBIOSE — PlantRenderer.PortTige.cs (partial, sprint FORMES DES PLANTES ③)
// Le port TIGE À FEUILLES ÉTAGÉES : axes dressés, rameaux, feuilles opposées ou alternes qui
// rapetissent en montant, sommet fleuri. Tournesol, ortie, basilic, poivron, phacélie,
// bourrache, moutarde, armoise, chanvre, achillée, consoude, menthe : même fonction, leur
// différence est dans la table (PlantRenderer.PortsFiches.cs). Le gros capitule unique du
// tournesol est 1 axe sans rameau, et le nuage de la moutarde 1 axe à 7 rameaux fleuris.
// Feuilles et têtes propres à ce port : PlantRenderer.PortTigeFormes.cs.
//
// 📖 Pédagogie : le dessin se fait en deux temps, COLLECTER puis PEINDRE. On calcule d'abord
// tous les axes, feuilles et têtes dans des listes réutilisées (aucune allocation par
// cuisson, comme un tampon statique en C). On peint ensuite dans l'ordre du peintre : feuilles
// du fond, tiges, feuilles de devant, têtes. Sans ce tri, une tige passerait devant une
// feuille censée la cacher, ou l'inverse selon l'ordre de calcul.
//
// 📖 Le vent ne s'écrit nulle part ici : tout passe par Iso, qui plie selon la hauteur. Seule
// précaution : un axe droit de 300 cm, plié, ne suivrait pas ses feuilles. On le trace donc
// en 3 tronçons dès qu'il y a de la flexion, et en 1 seul sinon.
//
// Échelle cumulative : ×1 et ×2, masse (losanges, moins de feuilles) ; ×4, forme de la feuille ;
// ×8, ombre de feuille, nervure et marques. Zéro écologie, zéro Random (philo #3).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float PartFeuillesLoinTige = 0.7f;
		private const float AngleOr = 2.39996f;   // alterne : chaque feuille tourne de 137,5°

		private readonly List<(Vector3 A, Vector3 B, float Largeur)> _axesTige = new();
		private readonly List<(Vector3 P, Vector2 Sens, int Graine)> _tetesTige = new();

		private void DessinerTige(FichePort f, Color col)
		{
			FicheTige t = f.Tige;
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			_axesTige.Clear();
			_tetesTige.Clear();
			_feuillesPort.Clear();

			float largeTige = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX, PixelInterne * 1.25f);
			float dens = MortPrairie ? DensitePlancher
				: Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1f);
			int nAxes = Mathf.Max(1, Mathf.RoundToInt(t.Axes * Mathf.Lerp(0.5f, 1f, g)));
			float phase = Mathf.Tau * Hash01(361, ig, 0);
			for (int a = 0; a < nAxes; a++)
			{
				var u = new Vector2(Mathf.Cos(a * AngleOr + phase), Mathf.Sin(a * AngleOr + phase));
				float d = nAxes == 1 ? 0f : rayon * t.EcartPied * Mathf.Sqrt((a + 0.5f) / nAxes);
				float haut = h * (a == 0 ? 1f : Mathf.Lerp(0.72f, 0.95f, Hash01(363, ig, a)));
				var pied = new Vector3(u.X * d, u.Y * d, 0f);
				var cime = new Vector3(u.X * (d + rayon * t.Evase), u.Y * (d + rayon * t.Evase), haut);
				_axesTige.Add((pied, cime, largeTige));
				_tetesTige.Add((cime, u, ig + a * 11));
				CollecterFeuillesAxe(f, pied, cime, rayon, g, dens, a * 17 + ig);
				CollecterRameaux(f, pied, cime, u, rayon, h, g, dens, largeTige, a * 29 + ig);
			}
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			PeindreTige(f, col, rayon, h);
		}

		// Feuilles d'un axe, de bas en haut. La taille et la phyllotaxie viennent de la fiche.
		private void CollecterFeuillesAxe(FichePort f, Vector3 pied, Vector3 cime, float rayon, float g, float dens, int graine)
		{
			FicheTige t = f.Tige;
			float loin = AuPalier(PaliersHautsMinZoom) ? 1f : PartFeuillesLoinTige;
			int n = Mathf.Max(2, Mathf.RoundToInt(f.Feuilles * Mathf.Lerp(0.5f, 1f, g) * loin));
			float azimut = Mathf.Tau * Hash01(365, graine, 0);
			for (int i = 0; i < n; i++)
			{
				float s = (i + 0.5f) / n;
				Vector3 p = pied.Lerp(cime, Mathf.Lerp(t.BasNu, 1f - t.HautNu, s));
				float l = Mathf.Lerp(t.FeuilleBasCm, t.FeuilleHautCm, s) * Mathf.Lerp(0.4f, 1f, g);
				float a = azimut + i * (t.Opposees ? Mathf.Pi * 0.5f : AngleOr);
				AjouterFeuilleTige(f, p, a, l, s, rayon, dens, graine + i * 2);
				if (t.Opposees) AjouterFeuilleTige(f, p, a + Mathf.Pi, l, s, rayon, dens, graine + i * 2 + 1);
				if (i >= n - t.TetesAisselle)
					_tetesTige.Add((p, new Vector2(Mathf.Cos(a), Mathf.Sin(a)), graine + i));
			}
		}

		// Rameaux d'un axe : le bas de la plante porte les plus longs, sauf fiche contraire
		// (`RameauFin`). Chacun porte quelques feuilles et sa propre tête. Le pincement en ajoute :
		// c'est ce qui rend le basilic pincé plus touffu (conception §4.4).
		private void CollecterRameaux(FichePort f, Vector3 pied, Vector3 cime, Vector2 sens, float rayon, float h,
			float g, float dens, float largeTige, int graine)
		{
			FicheTige t = f.Tige;
			if (t.Rameaux == 0) return;
			int n = Mathf.RoundToInt((t.Rameaux + 2f * _structure.Pince) * Mathf.Lerp(0.4f, 1f, g));
			float azimut = Mathf.Atan2(sens.Y, sens.X);
			for (int i = 0; i < n; i++)
			{
				float s = (i + 0.5f) / n;
				Vector3 p = pied.Lerp(cime, Mathf.Lerp(t.RameauDes, 1f, s));
				float a = azimut + i * AngleOr;
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				float l = rayon * t.RameauLong * Mathf.Lerp(1f, t.RameauFin, s) * Mathf.Lerp(0.85f, 1f, Hash01(367, graine, i));
				var bout = new Vector3(p.X + u.X * l, p.Y + u.Y * l, Mathf.Min(p.Z + l * t.RameauMonte, h));
				_axesTige.Add((p, bout, Mathf.Max(largeTige * 0.6f, PixelInterne)));
				_tetesTige.Add((bout, u, graine + i * 7));
				float taille = Mathf.Lerp(t.FeuilleBasCm, t.FeuilleHautCm, s) * 0.7f * Mathf.Lerp(0.4f, 1f, g);
				for (int j = 0; j < t.FeuillesRameau; j++)
				{
					float sr = (j + 0.6f) / t.FeuillesRameau;
					float ar = a + (j % 2 == 0 ? 1f : -1f) * 1.1f;
					AjouterFeuilleTige(f, p.Lerp(bout, sr), ar, taille, Mathf.Max(s, sr), rayon, dens, graine + i * 13 + j);
				}
			}
		}

		private void AjouterFeuilleTige(FichePort f, Vector3 p, float a, float l, float s, float rayon, float dens, int k)
		{
			if (dens < 1f && Hash01(369, k, 0) > dens) return;   // défeuillé : la tige reste
			var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
			var org = new Vector2(p.X, p.Y);
			// La feuille reste sous le rayon du port : la boîte de cuisson et le clic s'y fient.
			l = Mathf.Min(l, Mathf.Max(rayon - org.Length(), l * 0.5f));
			// Pas de ton 1 ici : le soleil retire déjà un ton à contre-jour, le limbe tournerait au noir.
			int ton = s < 0.6f ? PaletteIndexee.TonBase : 3;
			var fe = new FeuillePosee(u, l, l * f.LargeurFeuille, p.Z, l * f.Tige.Penche, 0f, ton, k, org);
			Vector2 ecran = WorldView.WorldToScreenOffset(org.X + u.X * l, org.Y + u.Y * l);
			// Du fond et du bas vers l'avant et le haut : vue d'au-dessus, le haut couvre le bas.
			_feuillesPort.Add((ecran.Y + p.Z * WorldView.PxPerCmZ * 0.5f, fe));
		}

		private void PeindreTige(FichePort f, Color col, float rayon, float h)
		{
			FicheTige t = f.Tige;
			Color tige = MortPrairie ? col : t.Tige;
			float souche = Mathf.Max(rayon * t.EcartPied * 0.5f * WorldView.PxPerCmX, PixelInterne * 2f);
			PoserEllipse(Vector2.Zero, souche, souche * 0.5f, Ton(col, 1));
			// Fond d'abord : ce qui part vers le nord de l'écran est derrière la tige.
			foreach (var (_, fe) in _feuillesPort)
				if (WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y).Y < 0f) PoserFeuilleTige(f, fe, col);
			foreach (var (a, b, large) in _axesTige) PoserAxe(a, b, large, tige);
			int devant = 0;
			foreach (var (_, fe) in _feuillesPort)
			{
				if (WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y).Y < 0f) continue;
				PoserFeuilleTige(f, fe, col);
				// Quelques sites suffisent à neige et symptômes, sans répéter sur toute la tige.
				if (devant++ % 3 == 0)
					_sitesPrairie.Add((PointFeuille(fe, 0.6f, 0f), Mathf.Max(fe.Large * 0.8f, 1.2f) * WorldView.PxPerCmX, fe.K, fe.BaseZ));
			}
			PoserTetesTige(f, col);
		}

		private void PoserAxe(Vector3 a, Vector3 b, float large, Color tige)
		{
			int n = _bendFlex > 0f ? 3 : 1;
			Color c = Ton(tige, PaletteIndexee.TonBase);
			Vector2 prec = Iso(a.X, a.Y, a.Z * AplatMort);
			for (int i = 1; i <= n; i++)
			{
				Vector3 p = a.Lerp(b, i / (float)n);
				Vector2 cour = Iso(p.X, p.Y, p.Z * AplatMort);
				_lotPrairie.Ligne(prec, cour, c, large);
				prec = cour;
			}
		}

		// Têtes : seulement en fleur, en bouton ou en fruit, et pas sur un pied coupé. Le chemin
		// des couleurs est celui des hampes de rosette. Ces états viennent de la structure
		// moteur (`floraison`, `organ`), rien n'est inventé pour faire joli.
		private void PoserTetesTige(FichePort f, Color col)
		{
			bool fruit = _structure.Organ.StartsWith("fruit", System.StringComparison.Ordinal);
			if (MortPrairie || _structure.Rabattu > RabattuTete
				|| (_structure.Floraison < FloraisonHampe && !fruit)) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color tete = _structure.Floraison >= FloraisonSeuil ? pal.Flower : fruit ? pal.FruitRipe : pal.FruitUnripe;
			// Le « pied » d'une tête allongée (épi, ombelle) : sous le sommet, dans le sens de la tige.
			float sousTete = f.Tige.EpiCm * WorldView.PxPerCmZ;
			foreach (var (p, sens, graine) in _tetesTige)
			{
				Vector2 c = Iso(p.X, p.Y, p.Z);
				Vector2 pied = c + new Vector2(0f, Mathf.Max(sousTete, PixelInterne));
				PoserTete(f, pied, c, tete, graine);
			}
		}
	}
}
