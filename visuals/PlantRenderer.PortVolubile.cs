// SYMBIOSE — PlantRenderer.PortVolubile.cs (partial, sprint FORMES DES PLANTES ⑥)
// Le port VOLUBILE : le haricot. Accroché, sa tige monte en spires régulières autour de l'appui
// que donne le pont (`support` : type, hauteur, écart au pied) ; libre, c'est un tas emmêlé qui
// tient debout sur `hauteur_autoportante`. Feuilles en triades, grappes de papillons blancs,
// gousses en marque de stade (haricot non `fruitier` au moteur : ni état ni récolte, fiches §Lire).
// Il n'a pas de vrilles : c'est la tige qui s'enroule (fiche), le moteur le nomme `vrille_volubile`.
//
// 📖 Pédagogie : le haricot et son tuteur sont DEUX nœuds, triés par leur pied ; la plante ne peut
// pas passer à la fois devant et derrière le pieu. Pour le faire croire, la moitié d'une spire qui
// passe derrière s'interrompt au droit du pieu et prend un ton plus sombre ; la moitié de devant
// passe dessus. C'est ainsi qu'un sprite SNES « entoure » un objet sans vraie profondeur.
//
// 📖 Pourquoi un écart venu du pont. Le moteur accroche une grimpante à un appui jusqu'à 75 cm de
// son pied (`RAYON_ACCROCHE_CM`) et ne la déplace pas. Spiraler autour du collet ferait monter le
// haricot dans le vide à côté de son tuteur. Le segment moteur reste, lu par `sim/grimpe.py`.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Appui du pont (FORMES ⑥, 0.6.8), écart mesuré du pied, repère de la tuile.
		private float _appuiHauteurCm, _appuiDxCm, _appuiDyCm;

		private const float PasSpireCm = 22f;      // un tour `[choix]` : pas régulier, fiche
		private const float RayonSpireCm = 5f;     // tuteur de 3 cm de demi-largeur + la tige
		private const float CimeLibreCm = 18f;     // ce qui dépasse et cherche encore
		private const float PiedSpireCm = 6f;      // le départ, depuis le sol
		private const float DemiPieuCm = 3f;       // là où la spire de derrière s'interrompt
		private const int BouclesTas = 6;

		private bool VolubileAccrochee =>
			!string.IsNullOrEmpty(_supportKind) && FicheDeLaPlante is { Forme: FormePort.Volubile };

		// Hauteur montrée : sur l'appui, jusqu'à son sommet et un peu plus ; sans appui, le tas.
		private float HauteurVolubile(FichePort f) => VolubileAccrochee
			? Mathf.Min(_hauteurLisseeCm, _appuiHauteurCm + CimeLibreCm)
			: Mathf.Min(_hauteurLisseeCm, f.HautFeuillesCm);

		// Axe des spires. Treillis et pergola (SupportRenderer) : le montant le plus proche du pied.
		private Vector2 AxeVolubile()
		{
			float demi = _supportKind switch { "treillis" => 18f, "pergola" => 22f, _ => 0f };
			return new Vector2(_appuiDxCm + (_appuiDxCm > 0f ? -demi : demi), _appuiDyCm);
		}

		private float AxeVolubileEcranX(FichePort f) => f.Forme == FormePort.Volubile && VolubileAccrochee
			? WorldView.WorldToScreenOffset(AxeVolubile().X, AxeVolubile().Y).X : 0f;

		private float RayonSpireEcran(FichePort f) =>
			f.Forme == FormePort.Volubile && VolubileAccrochee ? RayonSpireCm * WorldView.PxPerCmX * 1.5f : 0f;

		private Rect2 EtendreBoiteVolubile(Rect2 r, FichePort f, float rayon, float h)
		{
			if (!VolubileAccrochee) return r;
			Vector2 a = AxeVolubile();
			foreach (float z in new[] { 0f, h + f.Tige.FeuilleBasCm })
				r = r.Expand(Iso(a.X + rayon, a.Y - rayon, z)).Expand(Iso(a.X - rayon, a.Y + rayon, z))
					 .Expand(Iso(a.X + rayon, a.Y + rayon, z)).Expand(Iso(a.X - rayon, a.Y - rayon, z));
			return r;
		}

		private void DessinerVolubile(FichePort f, Color col)
		{
			var (rayon, h) = MesurePort(f);
			float g = CroissancePort(f);
			int ig = GraineIndividu;
			float dens = MortPrairie ? DensitePlancher : Mathf.Clamp(_structure.Feuillage * _structure.FacteurTaille, DensitePlancher, 1f);
			float large = Mathf.Max(f.EpaisseurTigeCm * WorldView.PxPerCmX, PixelInterne * 1.25f);
			_axesTige.Clear();
			_tetesTige.Clear();
			_feuillesPort.Clear();
			Color tige = MortPrairie ? col : f.Tige.Tige;
			if (VolubileAccrochee && !MortPrairie) CollecterSpires(f, tige, rayon, h, dens, large, ig);
			else CollecterTas(f, rayon, h, g, dens, large, ig);
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			PeindreFeuillesEtAxes(f, col, tige);
			PoserTetesPort(f, col, 0f);
		}

		// Du pied à l'appui, puis les tours. Moitié de derrière peinte ici, moitié de devant laissée
		// à `_axesTige`, que le peintre pose entre les feuilles du fond et celles de devant.
		private void CollecterSpires(FichePort f, Color tige, float rayon, float h, float dens, float large, int ig)
		{
			FicheTige t = f.Tige;
			Vector2 axe = AxeVolubile();
			float rs = _supportKind == "hote" ? RayonSpireCm * 0.6f : RayonSpireCm;
			float phase = Mathf.Tau * Hash01(401, ig, 0);
			Vector3 Spire(float th) => new(axe.X + rs * Mathf.Cos(th + phase), axe.Y + rs * Mathf.Sin(th + phase),
				Mathf.Min(PiedSpireCm + th / Mathf.Tau * PasSpireCm, h));
			_axesTige.Add((Vector3.Zero, Spire(0f), large));

			int parTour = AuPalier(PaliersHautsMinZoom) ? 8 : 4;   // ×1 : le zigzag de la fiche suffit
			float tours = Mathf.Max((h - PiedSpireCm) / PasSpireCm, 0.25f);
			int n = Mathf.CeilToInt(tours * parTour);
			Color fond = Ton(tige, 1);
			float pieu = _supportKind is "hote" ? 0f : DemiPieuCm * WorldView.PxPerCmX;
			for (int i = 0; i < n; i++)
			{
				float th0 = i * Mathf.Tau / parTour, th1 = (i + 1) * Mathf.Tau / parTour;
				Vector3 a = Spire(th0), b = Spire(th1);
				Vector2 milieu = WorldView.WorldToScreenOffset(Mathf.Cos(th0 + phase) + Mathf.Cos(th1 + phase), Mathf.Sin(th0 + phase) + Mathf.Sin(th1 + phase));
				if (milieu.Y >= 0f) { _axesTige.Add((a, b, large)); continue; }
				if (Mathf.Abs(milieu.X) * rs * 0.5f >= pieu)
					_lotPrairie.Ligne(Iso(a.X, a.Y, a.Z), Iso(b.X, b.Y, b.Z), fond, large);
			}

			int noeuds = Mathf.Max(2, Mathf.RoundToInt(f.Feuilles * Mathf.Clamp(h / f.HauteurAdulteCm, 0.2f, 1f)));
			if (!AuPalier(PaliersHautsMinZoom)) noeuds = Mathf.Max(2, noeuds * 2 / 3);
			for (int i = 0; i < noeuds; i++)
			{
				float s = (i + 0.5f) / noeuds, th = s * tours * Mathf.Tau;
				Vector3 p = Spire(th);
				float l = Mathf.Lerp(t.FeuilleBasCm, t.FeuilleHautCm, s);
				// Du tuteur vers l'extérieur, au hasard du hash : les feuilles s'écartent (fiche).
				float a = th + phase + (Hash01(403, ig, i) - 0.5f) * 1.2f;
				AjouterFeuilleTige(f, p, a, l, s, rayon + axe.Length(), dens, ig + i * 3, t.Penche);
				if (i >= noeuds - t.TetesAisselle)
					_tetesTige.Add((p, new Vector2(Mathf.Cos(a), Mathf.Sin(a)), ig + i));
			}
			// Le bout qui dépasse de l'appui, sans rien à enrouler.
			Vector3 sommet = Spire(tours * Mathf.Tau);
			if (h > _appuiHauteurCm)
				_axesTige.Add((sommet, sommet + new Vector3(rs * 1.5f * Mathf.Cos(phase), rs * 1.5f * Mathf.Sin(phase), -PiedSpireCm), large));
		}

		// Sans appui : des boucles qui montent et retombent, emmêlées, sous `hauteur_autoportante`.
		private void CollecterTas(FichePort f, float rayon, float h, float g, float dens, float large, int ig)
		{
			FicheTige t = f.Tige;
			int boucles = Mathf.Max(2, Mathf.RoundToInt(BouclesTas * g));
			float parBoucle = Mathf.Max(1f, 1.6f * f.Feuilles * g / boucles);
			for (int b = 0; b < boucles; b++)
			{
				float a = b * AngleOr + Mathf.Tau * Hash01(405, ig, 0);
				var bout = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * rayon * Mathf.Lerp(0.5f, 1f, Hash01(407, ig, b));
				float haut = h * Mathf.Lerp(0.55f, 1f, Hash01(409, ig, b));
				Vector3 c0 = new(bout.X * 0.35f, bout.Y * 0.35f, haut * 0.8f), c1 = new(bout.X * 0.7f, bout.Y * 0.7f, haut);
				Vector3 c2 = new(bout.X, bout.Y, haut * 0.25f);
				_axesTige.Add((Vector3.Zero, c0, large));
				_axesTige.Add((c0, c1, large));
				_axesTige.Add((c1, c2, large));
				for (int i = 0; i < parBoucle; i++)
				{
					float s = (i + 0.5f) / parBoucle;
					Vector3 p = s < 0.5f ? c0.Lerp(c1, s * 2f) : c1.Lerp(c2, s * 2f - 1f);
					float l = t.FeuilleBasCm * Mathf.Lerp(0.5f, 1f, g);
					AjouterFeuilleTige(f, p, a + i * AngleOr, l, 0.4f + s * 0.5f, rayon, dens, ig + b * 19 + i, t.Penche);
				}
				_tetesTige.Add((c1, new Vector2(Mathf.Cos(a), Mathf.Sin(a)), ig + b * 7));
			}
		}

		// ---------------------------------------------------------------------------
		// FEUILLES COMPOSÉES : triade du haricot, pennée de la tomate et du jasmin
		// ---------------------------------------------------------------------------

		// Une foliole : une petite feuille dont l'attache est au point (lg, 0) de sa feuille mère.
		private static FeuillePosee Foliole(FeuillePosee fe, float lg, float tourne, float longueur, float large)
		{
			float z = fe.BaseZ + fe.HautZ * (lg * lg);
			Vector2 org = fe.Org + fe.U * (lg * fe.Long);
			return new FeuillePosee(fe.U.Rotated(tourne), longueur, large, z, fe.HautZ * 0.25f, 0f, fe.Ton, fe.K, org);
		}

		private void PoserFoliole(FeuillePosee fo, Vector2[] contour, Color col, Color c, bool pres)
		{
			if (!AuPalier(PaliersHautsMinZoom) || fo.Long * WorldView.PxPerCmX * WorldView.CurrentZoom < 5f) { PoserLosange(fo, c); return; }
			_contourPrairie.Clear();
			foreach (Vector2 q in contour) _contourPrairie.Add(PointFeuille(fo, q.X, q.Y));
			if (pres) PoserEventail(_contourPrairie, new Vector2(0f, PixelInterne), Ton(col, 0));
			PoserEventail(_contourPrairie, Vector2.Zero, c);
			if (!pres) return;
			DetaillerLimbe(fo, col);
			_lotPrairie.Ligne(PointFeuille(fo, 0.08f, 0f), PointFeuille(fo, 0.9f, 0f), Ton(col, Mathf.Min(fo.Ton + 2, 4)), PixelInterne);
		}

		// Haricot : le pétiole, deux folioles latérales écartées, la centrale plus loin.
		private void PoserTriade(FichePort f, FeuillePosee fe, Color col, Color c)
		{
			bool pres = AuPalier(PalierOrganesZoom);
			float l = fe.Long * 0.62f, w = l * f.LargeurFeuille;
			Vector2 centre = PointFeuille(fe, 0.42f, 0f);
			if (AuPalier(PaliersHautsMinZoom)) _lotPrairie.Ligne(PointFeuille(fe, 0f, 0f), centre, Ton(col, 3), PixelInterne);
			PoserFoliole(Foliole(fe, 0.42f, 1.35f, l * 0.9f, w), ContourCoeur, col, c, pres);
			PoserFoliole(Foliole(fe, 0.42f, -1.35f, l * 0.9f, w), ContourCoeur, col, c, pres);
			PoserFoliole(Foliole(fe, 0.42f, 0f, l, w), ContourCoeur, col, c, pres);
		}

		// Tomate, jasmin : un rachis, des paires de folioles, une terminale. `Feuilles` de la fiche.
		private void PoserComposee(FichePort f, FeuillePosee fe, Color col, Color c)
		{
			bool pres = AuPalier(PalierOrganesZoom), loin = !AuPalier(PaliersHautsMinZoom);
			Vector2[] contour = f.Marque == MarqueFeuille.Gaufre ? ContourScie : ContourOvale;
			int paires = loin ? 1 : (f.Feuilles - 1) / 2;
			float pas = 1f / (paires + 1), l = fe.Long * Mathf.Max(pas * 1.4f, 0.3f);
			if (!loin) _lotPrairie.Ligne(PointFeuille(fe, 0f, 0f), PointFeuille(fe, 1f - pas * 0.5f, 0f), Ton(col, 3), PixelInterne);
			for (int i = 0; i < paires; i++)
			{
				float lg = pas * (i + 0.8f);
				// Tomate : folioles inégales au hash (fiche). Plus petites vers le bout.
				float taille = l * Mathf.Lerp(1f, 0.75f, i / Mathf.Max(paires, 1f)) * Mathf.Lerp(0.7f, 1f, Hash01(411, fe.K, i));
				PoserFoliole(Foliole(fe, lg, 1.05f, taille, taille * f.LargeurFeuille), contour, col, c, pres);
				PoserFoliole(Foliole(fe, lg, -1.05f, taille, taille * f.LargeurFeuille), contour, col, c, pres);
			}
			PoserFoliole(Foliole(fe, 1f - pas * 0.6f, 0f, l, l * f.LargeurFeuille), contour, col, c, pres);
		}

		// Grappe de papillons : 2 ou 3 taches blanches à l'aisselle. Hors fleur, les gousses.
		private void PoserPapillons(Vector2 c, float r, Color col, int graine)
		{
			float pix = PixelInterne;
			if (col != FleurDe()) { PoserGousses(c, r, col, graine); return; }
			int n = AuPalier(PalierOrganesZoom) ? 3 : 2;
			for (int k = 0; k < n; k++)
			{
				var q = c + new Vector2((k - 0.5f * (n - 1)) * r * 1.5f, k * r * 0.7f);
				if (AuPalier(PalierOrganesZoom)) PoserDisque(q, r + pix, Ton(col, 0));   // contour sélectif
				PoserDisque(q, r, Ton(col, 3));
				if (AuPalier(PalierOrganesZoom)) PoserDisque(q - new Vector2(r, r) * 0.3f, Mathf.Max(r * 0.35f, pix), Ton(col, 4));
			}
		}

		// Gousse fine qui pend : 15 cm de long [fiche], marque de stade sans état moteur.
		private void PoserGousses(Vector2 c, float r, Color col, int graine)
		{
			float pix = PixelInterne, lg = 15f * WorldView.PxPerCmZ;
			for (int k = 0; k < 2; k++)
			{
				float dx = (Hash01(413, graine, k) - 0.5f) * lg * 0.4f;
				Vector2 a = c + new Vector2(k * r * 1.6f, 0f), b = a + new Vector2(dx, lg);
				_lotPrairie.Ligne(a, b, Ton(col, 1), Mathf.Max(0.8f * WorldView.PxPerCmX, pix) + pix);
				_lotPrairie.Ligne(a, b, Ton(col, 3), Mathf.Max(0.8f * WorldView.PxPerCmX, pix));
			}
		}
	}
}
