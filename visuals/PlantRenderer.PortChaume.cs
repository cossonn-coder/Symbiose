// SYMBIOSE — PlantRenderer.PortChaume.cs (partial, sprint FORMES DES PLANTES ④)
// Le port CHAUME : brins qui partent de la base, feuille-ruban, épi ou panicule, nœuds pour le
// bambou. Blé, seigle, pâturin, bambou : même fonction, la différence est dans la table
// (PlantRenderer.PortsFiches.cs). Le ruban est le brin du dactyle (PoserBrin, Graminees.cs).
//
// 📖 Pédagogie : le seigle se reconnaît à son épi qui PENCHE. On ne dessine pas un épi puis on
// le tourne : on calcule une direction 3D, `(u·sin θ, cos θ)`, où θ grandit avec `Penche`, et
// chaque point de l'épi passe par Iso. La flexion du vent s'y applique donc toute seule. Et
// pour que la hauteur dessinée reste `height_cm`, le chaume s'arrête plus bas d'autant que
// l'épi monte : ce n'est pas l'axe qui fait la hauteur, c'est son sommet.
//
// La maturité vient du STADE moteur (`mature`), rien d'autre : un blé vert ne dore pas.
// Échelle cumulative : ×1, masse et hauteur ; ×4, épi, barbes, nœuds ; ×8, grains, gaines.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const string StadeMur = "mature";
		private const float PartDoree = 0.75f;      // chaume mûr : tiré vers la couleur du grain
		private const float AngleEpiMax = 2.2f;     // rad, à `Penche` 1 : l'épi retombe

		private void DessinerChaume(FichePort f, Color col)
		{
			FicheChaume c = f.Chaume;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			bool leve = f.Hampes == 0 || HampeLevee(f);
			bool mur = !MortPrairie && _structure.StageName == StadeMur;
			if (mur) col = col.Lerp(pal.FruitRipe, PartDoree);
			_axesTige.Clear();
			_tetesTige.Clear();
			_feuillesPort.Clear();

			float souche = Mathf.Max(rayon * Mathf.Max(c.EcartPied, 0.25f) * WorldView.PxPerCmX, PixelInterne * 2f);
			PoserEllipse(Vector2.Zero, souche, souche * 0.5f, Ton(col, 1));
			float zRubans = HauteurFeuilles(f) * h / Mathf.Max(MesureBrute(f), 1f);
			PoserRubans(c, col, rayon, zRubans, g, ig, devant: false);
			if (leve) CollecterBrins(f, c, rayon, h, g, ig);
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			Color tige = MortPrairie ? col : mur ? c.Couleur.Lerp(pal.FruitRipe, PartDoree) : c.Couleur;
			PeindreFeuillesEtAxes(f, col, tige);
			if (leve && c.Noeuds > 0) PoserNoeuds(f, c, rayon, h, g, ig, tige);
			PoserRubans(c, col, rayon, zRubans, g, ig, devant: true);
			if (leve && _structure.Rabattu <= RabattuTete && !MortPrairie) PoserEpis(c, pal, mur, rayon, h, g, ig);
		}

		// Nombre de brins : un jeune pied en a moitié moins.
		private static int BrinsDe(FicheChaume c, float g) => Mathf.Max(1, Mathf.RoundToInt(c.Brins * Mathf.Lerp(0.5f, 1f, g)));

		// Géométrie d'un brin : pied, sommet, direction au sol, pure fonction de l'individu. Tout ce
		// qui s'accroche à un brin (nœud, panache, épi) la relit, plutôt que de la mémoriser.
		private (Vector3 Pied, Vector3 Cime, Vector2 U) Brin(FicheChaume c, int a, int n, float rayon, float h, float g, int ig)
		{
			float angle = a * AngleOr + Mathf.Tau * Hash01(401, ig, 0);
			var u = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
			float d = n == 1 ? 0f : rayon * c.EcartPied * Mathf.Sqrt((a + 0.5f) / n);
			float haut = h * (a == 0 ? 1f : Mathf.Lerp(0.82f, 0.97f, Hash01(403, ig, a)));
			haut -= c.EpiCm * Mathf.Lerp(0.6f, 1f, g) * Mathf.Max(Mathf.Cos(c.Penche * AngleEpiMax), 0f);
			var pied = new Vector3(u.X * d, u.Y * d, 0f);
			return (pied, new Vector3(u.X * (d + rayon * c.Evase), u.Y * (d + rayon * c.Evase), Mathf.Max(haut, 1f)), u);
		}

		private void CollecterBrins(FichePort f, FicheChaume c, float rayon, float h, float g, int ig)
		{
			float large = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX, PixelInterne * 1.25f);
			float dens = MortPrairie ? 0f : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, 0f, 1f);
			int n = BrinsDe(c, g);
			for (int a = 0; a < n; a++)
			{
				var (pied, cime, u) = Brin(c, a, n, rayon, h, g, ig);
				_axesTige.Add((pied, cime, large));
				for (int i = 0; i < c.Panaches; i++)
					CollecterPanache(f, c, pied, cime, u, i, rayon, h, g, dens, large, a * 31 + ig);
				// Une feuille de chaume, à mi-hauteur : « rare en haut » (fiche).
				if (c.Rubans > 0 && dens > 0f)
				{
					Vector3 p = pied.Lerp(cime, 0.5f);
					_axesTige.Add((p, p + new Vector3(u.X * rayon * 0.6f, u.Y * rayon * 0.6f, -h * 0.03f), PixelInterne));
				}
			}
		}

		// Un rameau court du bambou, et son éventail de 3 feuilles qui retombent.
		private void CollecterPanache(FichePort f, FicheChaume c, Vector3 pied, Vector3 cime, Vector2 sens, int i,
			float rayon, float h, float g, float dens, float large, int graine)
		{
			float s = (i + 0.5f) / c.Panaches;
			Vector3 p = pied.Lerp(cime, Mathf.Lerp(0.45f, 1f, s));
			float a = Mathf.Atan2(sens.Y, sens.X) + i * AngleOr;
			var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
			float l = rayon * 0.4f * Mathf.Lerp(1f, 0.6f, s);
			var bout = new Vector3(p.X + u.X * l, p.Y + u.Y * l, Mathf.Min(p.Z + l * 0.5f, h));
			_axesTige.Add((p, bout, Mathf.Max(large * 0.3f, PixelInterne)));
			float taille = c.PanacheCm * Mathf.Lerp(0.4f, 1f, g);
			for (int j = -1; j <= 1; j++)
				AjouterFeuilleTige(f, bout, a + j * 0.7f, taille, s, rayon, dens, graine + i * 7 + j, -0.35f);
		}

		// Les rubans de la base, en deux passes autour des chaumes. Le cœur est plus clair.
		private void PoserRubans(FicheChaume c, Color col, float rayon, float z, float g, int ig, bool devant)
		{
			if (c.Rubans == 0) return;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1f);
			int n = Mathf.Max(3, Mathf.RoundToInt(c.Rubans * Mathf.Lerp(0.5f, 1f, g) * dens));
			float phase = Mathf.Tau * Hash01(405, ig, 0);
			for (int k = 0; k < n; k++)
			{
				float a = k * AngleOr + phase;
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				Vector2 ecran = WorldView.WorldToScreenOffset(u.X, u.Y);
				if (ecran.Y >= 0f != devant) continue;
				float d = rayon * c.EcartPied * 0.5f * Hash01(407, ig, k);
				float hb = z * Mathf.Lerp(0.6f, 1f, Hash01(409, ig, k));
				int ton = k * 3 < n ? 1 : k * 4 < n * 3 ? PaletteIndexee.TonBase : 3;
				PoserBrin(u.X * d, u.Y * d, u.X, u.Y, rayon * Mathf.Lerp(0.6f, 1f, Hash01(411, ig, k)), hb, c.RubanCm, Ton(col, ton, Orientation(ecran)));
				if (devant && k % 3 == 0)
					_sitesPrairie.Add((Iso(u.X * rayon * 0.5f, u.Y * rayon * 0.5f, hb * 0.8f), c.RubanCm * WorldView.PxPerCmX, k, hb));
			}
		}

		// Cannes du bambou : un trait sombre par nœud, dès ×4 ; dès ×8 une gaine brune en bas.
		private void PoserNoeuds(FichePort f, FicheChaume c, float rayon, float h, float g, int ig, Color tige)
		{
			if (!AuPalier(PaliersHautsMinZoom)) return;
			float large = f.EpaisseurTigeCm * WorldView.PxPerCmX, pix = PixelInterne;
			int n = BrinsDe(c, g);
			for (int a = 0; a < n; a++)
			{
				var (pied, cime, _) = Brin(c, a, n, rayon, h, g, ig);
				for (int i = 1; i <= c.Noeuds; i++)
				{
					Vector3 p = pied.Lerp(cime, i / (c.Noeuds + 1f));
					Vector2 q = Iso(p.X, p.Y, p.Z * AplatMort), e = new Vector2(large * 0.6f, 0f);
					bool gaine = i <= 2 && AuPalier(PalierOrganesZoom);
					_lotPrairie.Ligne(q - e, q + e, gaine ? Ton(new Color("7a5a3a"), PaletteIndexee.TonBase) : Ton(tige, 1), gaine ? pix * 2f : pix);
				}
			}
		}

		private void PoserEpis(FicheChaume c, OrganPalette pal, bool mur, float rayon, float h, float g, int ig)
		{
			if (c.EpiCm <= 0f) return;
			int n = BrinsDe(c, g);
			Color teinte = mur ? pal.FruitRipe : pal.FruitUnripe;
			bool anthese = _structure.Floraison >= FloraisonSeuil;
			for (int a = 0; a < n; a++)
			{
				var (_, cime, u) = Brin(c, a, n, rayon, h, g, ig);
				if (c.Panicule) { PoserPanicule(cime, c.EpiCm * Mathf.Lerp(0.6f, 1f, g), pal, a + ig); continue; }
				float t = c.Penche * AngleEpiMax * Mathf.Lerp(0.8f, 1.1f, Hash01(413, ig, a));
				var dir = new Vector3(u.X * Mathf.Sin(t), u.Y * Mathf.Sin(t), Mathf.Cos(t));
				float len = c.EpiCm * Mathf.Lerp(0.6f, 1f, g);
				PoserEpiChaume(c, cime, dir, u, len, teinte, anthese ? pal.Flower : default);
			}
		}

		// Épi : un trait épais loin ; grains en deux rangs dès ×8 ; barbes dès ×4.
		private void PoserEpiChaume(FicheChaume c, Vector3 base3, Vector3 dir, Vector2 u, float len, Color teinte, Color anthere)
		{
			float pix = PixelInterne;
			Vector3 bout3 = base3 + dir * len;
			Vector2 b = Iso(base3.X, base3.Y, base3.Z), p = Iso(bout3.X, bout3.Y, bout3.Z);
			float large = Mathf.Max(c.EpiLargeCm * WorldView.PxPerCmX, pix * 1.25f);
			_lotPrairie.Ligne(b, p, Ton(teinte, PaletteIndexee.TonBase), large);
			if (c.BarbeCm > 0f && AuPalier(PaliersHautsMinZoom))
			{
				int nb = AuPalier(PalierOrganesZoom) ? 5 : 3;
				for (int i = 1; i <= nb; i++)
				{
					Vector3 q = base3 + dir * (len * i / nb);
					Vector3 fin = q + new Vector3(u.X, u.Y, 0.6f) * c.BarbeCm;
					_lotPrairie.Ligne(Iso(q.X, q.Y, q.Z), Iso(fin.X, fin.Y, fin.Z), Ton(teinte, 3), pix);
				}
			}
			if (!AuPalier(PalierOrganesZoom)) return;
			Vector2 axe = p - b, cote = axe.Orthogonal().Normalized() * large * 0.45f;
			for (int i = 0; i < 6; i++)
			{
				Vector2 q = b + axe * ((i + 0.5f) / 6f) + cote * (i % 2 == 0 ? 1f : -1f);
				PoserDisque(q, Mathf.Max(large * 0.3f, pix), Ton(teinte, i % 2 == 0 ? 3 : 1));
				if (anthere.A > 0f && i % 2 == 0) PoserDisque(q + cote * 1.6f, pix, Ton(anthere, 4));
			}
		}

		// Panicule en triangle ajouré du pâturin : des branches plus longues vers le bas.
		private void PoserPanicule(Vector3 cime, float len, OrganPalette pal, int graine)
		{
			float pix = PixelInterne, pxx = WorldView.PxPerCmX;
			Vector2 haut = Iso(cime.X, cime.Y, cime.Z + len), bas = Iso(cime.X, cime.Y, cime.Z);
			Color fil = Ton(pal.FruitUnripe, 3), grain = Ton(pal.Flower, 3);
			_lotPrairie.Ligne(bas, haut, fil, pix);
			int etages = AuPalier(PaliersHautsMinZoom) ? 4 : 2;
			for (int e = 0; e < etages; e++)
			{
				float t = (e + 0.5f) / etages;
				Vector2 q = haut.Lerp(bas, t);
				var bras = new Vector2((t * len * 0.4f + 0.5f) * pxx, t * 2f * pxx);
				foreach (float cote in new[] { 1f, -1f })
				{
					Vector2 fin = q + new Vector2(bras.X * cote, bras.Y);
					_lotPrairie.Ligne(q, fin, fil, pix);
					PoserDisque(fin, Mathf.Max(0.5f * pxx, pix), Hash01(415, graine, e) < 0.5f ? grain : fil);
				}
			}
		}
	}
}
