// SYMBIOSE — PlantRenderer.PortRosette.cs (partial, sprint FORMES DES PLANTES ②)
// Le port ROSETTE, ± hampe : feuilles en étoile au sol, hampe selon le stade ou la floraison.
// Pissenlit, mâche, bourse-à-pasteur, molène, drosera, carotte, ail : même fonction, leur
// différence est dans la table (PlantRenderer.PortsFiches.cs). Les têtes sont dans
// PlantRenderer.PortTetes.cs. Lot, teinte et détails : ceux de la prairie.
//
// 📖 Pédagogie : la feuille est un CONTOUR à plat, en coordonnées (long, large) relatives,
// posé dans le plan de sa direction u et projeté point par point par Iso. C'est Iso qui
// applique la flexion du vent, sans code de vent ici. On trie les feuilles par Y écran : le
// peintre pose celles du fond d'abord, comme à la main.
//
// Échelle cumulative (conception_rendu_visible.md §4 D4) : santé dès ×2, ombre de feuille et
// nervure dès ×8, marques (duvet, gouttes, pli) dès ×8. À ×1, on lit une masse et une couleur.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Contours (long, large), base en tête, moitié gauche seule : le reste s'en déduit.
		private static readonly Vector2[] ContourDente = Symetrique(new(0f, 0f), new(0.12f, 0.35f), new(0.2f, 0.12f),
			new(0.34f, 0.65f), new(0.44f, 0.2f), new(0.58f, 0.9f), new(0.67f, 0.3f), new(0.82f, 1f), new(1f, 0f));
		private static readonly Vector2[] ContourSpatule = Symetrique(new(0f, 0f), new(0.25f, 0.22f), new(0.55f, 0.8f),
			new(0.8f, 1f), new(0.97f, 0.6f), new(1f, 0f));
		private static readonly Vector2[] ContourLobe = Symetrique(new(0f, 0f), new(0.15f, 0.5f), new(0.25f, 0.2f),
			new(0.4f, 0.7f), new(0.5f, 0.25f), new(0.65f, 0.85f), new(0.75f, 0.35f), new(0.95f, 0.7f), new(1f, 0f));
		private static readonly Vector2[] ContourOvale = Symetrique(new(0f, 0f), new(0.15f, 0.6f), new(0.45f, 1f),
			new(0.75f, 0.8f), new(0.95f, 0.3f), new(1f, 0f));

		// Complète un contour par sa moitié droite, parcourue du bout vers la base.
		private static Vector2[] Symetrique(params Vector2[] gauche)
		{
			var tout = new List<Vector2>(gauche);
			for (int i = gauche.Length - 2; i >= 1; i--) tout.Add(new Vector2(gauche[i].X, -gauche[i].Y));
			return tout.ToArray();
		}

		private static Vector2[] ContourDe(FormeFeuille f) => f switch
		{
			FormeFeuille.Dentee => ContourDente,
			FormeFeuille.Spatule => ContourSpatule,
			FormeFeuille.Lobee => ContourLobe,
			FormeFeuille.Coeur => ContourCoeur,
			FormeFeuille.Scie => ContourScie,
			FormeFeuille.Lanceolee => ProfilLanceole,
			FormeFeuille.Lierre => ContourLierre,
			_ => ContourOvale,
		};

		// Ce qui décrit une feuille à poser : rassemblé pour ne pas traîner 8 paramètres.
		// `Org` : point d'attache sur le sol (rosette : le collet ; tige : le nœud de l'axe).
		private readonly record struct FeuillePosee(Vector2 U, float Long, float Large, float BaseZ, float HautZ,
			float Dressee, int Ton, int K, Vector2 Org = default);
		private readonly List<(float Prof, FeuillePosee F)> _feuillesPort = new();

		// Sous-couche, hampe et feuilles, dans l'ordre où elles se recouvrent.
		private void DessinerRosette(FichePort f, Color col)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			if (!MortPrairie && f.MelangeFruit > 0f) col = col.Lerp(pal.FruitRipe, f.MelangeFruit);
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			float zFeuilles = HauteurFeuilles(f) * h / Mathf.Max(MesureBrute(f), 1f);   // la coupe rabat aussi les feuilles
			int ig = GraineIndividu;

			float souche = Mathf.Max(rayon * (f.Dressee >= 0.5f ? 0.16f : 0.45f) * WorldView.PxPerCmX, PixelInterne);
			PoserEllipse(Vector2.Zero, souche, souche * 0.5f, Ton(col, 1));
			PoserPied(f, rayon);
			bool hampe = HampeLevee(f);
			// Touffe dressée : la hampe sort de son cœur, donc derrière les feuilles. Rosette
			// plaquée : la hampe se pose sur les feuilles qui sont à plat.
			if (hampe && f.Dressee >= 0.5f) PoserHampesPort(f, h, g, ig, col, pal);
			PoserFeuillesRosette(f, col, rayon, zFeuilles, g, ig);
			if (hampe && f.Dressee < 0.5f) PoserHampesPort(f, h, g, ig, col, pal);
		}

		// Hauteur sans coupe : la mesure, dont on ne garde que le rapport coupé / non coupé.
		private float MesureBrute(FichePort f) => HampeLevee(f) ? _hauteurLisseeCm : HauteurFeuilles(f);

		private void PoserFeuillesRosette(FichePort f, Color col, float rayon, float zf, float g, int ig)
		{
			float loin = WorldView.CurrentZoom < PalierSanteZoom ? 0.7f : 1f;
			float dens = MortPrairie ? DensitePlancher
				: Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1.3f);
			int n = Mathf.Max(3, Mathf.RoundToInt(f.Feuilles * Mathf.Lerp(0.4f, 1f, g) * dens * loin));
			float phase = Mathf.Tau * Hash01(301, ig, 0);
			_feuillesPort.Clear();
			for (int k = 0; k < n; k++)
			{
				// Angle d'or, ou deux rangs opposés (ail : un éventail, pas une étoile).
				float a = f.Feuille == FormeFeuille.Ruban
					? phase + (k % 2 == 0 ? 0f : Mathf.Pi) + Mathf.Lerp(-0.45f, 0.45f, Hash01(303, ig, k))
					: k * 2.39996f + phase;
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				float part = k / (float)n;
				// De l'extérieur vers le cœur : les jeunes feuilles sont plus courtes.
				float l = rayon * Mathf.Lerp(1f, 0.55f, part) * Mathf.Lerp(0.85f, 1f, Hash01(305, ig, k));
				int ton = part < 0.33f ? 1 : part < 0.75f ? PaletteIndexee.TonBase : 3;
				var feuille = new FeuillePosee(u, l, l * f.LargeurFeuille, 0f,
					zf * Mathf.Lerp(0.75f, 1f, Hash01(307, ig, k)), f.Dressee, ton, k);
				_feuillesPort.Add((WorldView.WorldToScreenOffset(u.X * l, u.Y * l).Y, feuille));
			}
			_feuillesPort.Sort((a, b) => a.Prof.CompareTo(b.Prof));   // du fond vers l'avant
			for (int i = 0; i < _feuillesPort.Count; i++)
			{
				FeuillePosee fe = _feuillesPort[i].F;
				PoserFeuillePort(f, fe, col);
				if (i >= _feuillesPort.Count * 2 / 3)   // devant : où posent neige et symptômes
				{
					Vector2 s = PointFeuille(fe, 0.6f, 0f);
					_sitesPrairie.Add((s, Mathf.Max(fe.Large * 0.8f, 1.2f) * WorldView.PxPerCmX, fe.K, fe.HautZ * 0.5f));
				}
			}
		}

		private void PoserFeuillePort(FichePort f, FeuillePosee fe, Color col)
		{
			switch (f.Feuille)
			{
				case FormeFeuille.Ruban:
					PoserBrin(fe.U.X * 1.2f, fe.U.Y * 1.2f, fe.U.X, fe.U.Y, fe.Long, fe.HautZ, f.LargeurFeuille, Ton(col, fe.Ton));
					return;
				case FormeFeuille.Plume: PoserPlume(fe, col); return;
				case FormeFeuille.Cuillere: PoserCuillere(fe, col, f.Marque); return;
			}
			float pix = PixelInterne;
			_contourPrairie.Clear();
			foreach (Vector2 q in ContourDe(f.Feuille)) _contourPrairie.Add(PointFeuille(fe, q.X, q.Y));
			// Ombre portée de la feuille sur la feuille d'en dessous, dès ×8 : à ×4, les tons
			// et l'orientation séparent déjà les feuilles, et elle doublait le coût (③).
			if (AuPalier(PalierOrganesZoom)) PoserEventail(_contourPrairie, new Vector2(0f, pix), Ton(col, 0));
			PoserEventail(_contourPrairie, Vector2.Zero,
				Ton(col, fe.Ton, Orientation(WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y))));
			if (!AuPalier(PalierOrganesZoom)) return;
			DetaillerLimbe(fe, col);
			_lotPrairie.Ligne(PointFeuille(fe, 0.05f, 0f), PointFeuille(fe, 0.9f, 0f), Ton(col, Mathf.Min(fe.Ton + 2, 4)), pix);
			if (f.Marque == MarqueFeuille.Duvet) PoserDuvet(fe, col);
		}

		// Point (lg, lr) d'une feuille. `Dressee` raccourcit l'emprise au sol et monte plus tôt ;
		// plaquée, seul le bout se relève.
		private Vector2 PointFeuille(FeuillePosee fe, float lg, float lr)
		{
			var v = new Vector2(-fe.U.Y, fe.U.X);
			float d = fe.Dressee;
			Vector2 m = fe.U * (lg * fe.Long * (1f - 0.6f * d)) + v * (lr * fe.Large);
			float monte = d * lg * (2f - lg) + (1f - d) * lg * lg;
			return Iso(fe.Org.X + m.X, fe.Org.Y + m.Y, (fe.BaseZ + 0.4f + fe.HautZ * monte) * AplatMort);
		}

		// Plume (carotte, ×1 : un petit nuage) : une tache loin, un rachis et ses lanières près.
		private void PoserPlume(FeuillePosee fe, Color col)
		{
			float pix = PixelInterne;
			Color c = Ton(col, fe.Ton, Orientation(WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y)));
			if (!AuPalier(PaliersHautsMinZoom))
			{
				PoserDisque(PointFeuille(fe, 0.65f, 0f), Mathf.Max(fe.Large * WorldView.PxPerCmX * 1.2f, pix), c);
				return;
			}
			_lotPrairie.Ligne(PointFeuille(fe, 0f, 0f), PointFeuille(fe, 1f, 0f), c, pix);
			int paires = AuPalier(PalierOrganesZoom) ? 5 : 3;   // ×4 : la découpe, pas le détail
			for (int i = 1; i <= paires; i++)
			{
				float t = 0.2f + i * 0.7f / paires, lr = 1f - t * 0.75f;
				Vector2 axe = PointFeuille(fe, t, 0f);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.12f, lr), c, pix);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.12f, -lr), c, pix);
			}
		}

		// Cuillère (drosera) : long pétiole, disque rouge ; dès ×8, ses gouttes claires au bord.
		private void PoserCuillere(FeuillePosee fe, Color col, MarqueFeuille marque)
		{
			float pix = PixelInterne;
			Vector2 centre = PointFeuille(fe, 0.82f, 0f);
			float r = Mathf.Max(fe.Large * WorldView.PxPerCmX, pix);
			_lotPrairie.Ligne(PointFeuille(fe, 0f, 0f), centre, Ton(col, 1), pix);
			PoserDisque(centre, r, Ton(col, fe.Ton));
			if (marque != MarqueFeuille.Gouttes || !AuPalier(PalierOrganesZoom)) return;
			for (int i = 0; i < 6; i++)
			{
				float a = i * Mathf.Tau / 6f + fe.K;
				PoserDisque(centre + new Vector2(r * Mathf.Cos(a), r * 0.8f * Mathf.Sin(a)), pix, Ton(col, 4));
			}
		}

		// Duvet (molène) : grain clair sur le limbe, à la place d'une nervation qu'on ne voit pas.
		private void PoserDuvet(FeuillePosee fe, Color col)
		{
			int ig = GraineIndividu;
			for (int i = 0; i < 6; i++)
				PoserDisque(PointFeuille(fe, Mathf.Lerp(0.2f, 0.85f, Hash01(311, ig + fe.K, i)),
					Mathf.Lerp(-0.6f, 0.6f, Hash01(313, ig + fe.K, i))), PixelInterne, Ton(col, 4));
		}

		// Ce qui se voit au collet dès ×8 : base blanche de l'ail, épaule orange de la carotte.
		private void PoserPied(FichePort f, float rayon)
		{
			if (f.Pied == null || MortPrairie || !AuPalier(PalierOrganesZoom)) return;
			float rx = Mathf.Max(rayon * 0.14f * WorldView.PxPerCmX, PixelInterne);
			Color c = new Color(f.Pied);
			PoserEllipse(Vector2.Zero, rx, rx * 0.6f, Ton(c, PaletteIndexee.TonBase));
		}
	}
}
