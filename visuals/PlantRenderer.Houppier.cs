// SYMBIOSE — PlantRenderer.Houppier.cs (partial, sprint HOUPPIER ⑤)
// Le DESSIN d'un houppier, sur les rameaux dérivés (Rameaux.cs) :
//   ×0,5 à ×4  une gerbe (Gerbes.cs) au bout de chaque rameau et de chaque brindille, à la place des
//              touffes autour des rameaux (×2) et des masses ovales (×4), les « pompons » ;
//   ×8 et plus de vraies feuilles de la forme de l'espèce, portées par le petit bois.
// L'hiver, la couche bois des gerbes reste seule : la dentelle se lit. Présence de feuille au hash,
// `< DensiteVisible` : les feuilles restantes de l'automne sont déjà là en été, rien ne saute.
//
// 📖 Pédagogie : pourquoi une gerbe. Une gerbe de ~30 cm porte une dizaine de touffes en UN seul
// tracé d'atlas, comme une copie de bloc plutôt qu'une boucle d'octets. Le nombre de tracés reste
// donc celui des bouts de rameau, quelques centaines par arbre, pour une couronne qui se ferme.
// Hors pinceau indexé (dessin direct, F11 OFF), la même gerbe se pose en couleurs littérales.
//
// Zéro Random (philo #3) ; canaux de hash 521-559 ; golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Le bois d'un arbre n'a plus de grand segment vert : le bout seul reste tendre.
		private const float LigPlancherArbre = 0.6f;
		private const float BoutTendreCm = 8f;
		private const float LigBoutTendre = 0.1f;
		// Largeur minimale du bois d'un arbre aux paliers hauts, en px internes.
		private const float BoisArbreMinPx = 2f;
		// Largeur du petit bois, en cm : à ×8 et plus, l'épaisseur réelle lit mieux que 1 px.
		private const float RameauLargeCm = 1.2f, BrindilleLargeCm = 0.5f;
		private const float LigRameau = 0.8f, LigBrindille = 0.45f;
		private const float GerbeDemiCm = 15f;   // le pied de la gerbe descend de ça : son milieu est au bout
		private const float NeigeGerbes = 0.6f;
		private const int PalierGerbeLoin = 1;   // ×0,5 et ×1
		private const float PartGerbesLoin = 0.33f;
		// Neige, symptômes, reflets à ×8 et plus : une feuille sur…, sans répéter sur tout l'arbre.
		private const int SiteDetailsPas = 6;
		// `DensiteVisible` vaut la densité de l'espèce × la part en place, soit 0,45 à 0,85 en plein
		// été selon l'espèce : elle règle aussi la lumière. Prise telle quelle, une brindille sur deux restait nue en juillet.
		// Le gain garde la proportion à l'automne et la couronne fermée en été [choix].
		private const float GainDensite = 1.6f;

		/// <summary>Part ligneuse d'un segment telle qu'on la peint (arbre : jamais tendre sur toute sa longueur).</summary>
		private float LigVue(in Segment s, bool houppier) =>
			houppier ? Mathf.Max(LigPlancherArbre, Mathf.Clamp(s.AgeWeeks / LignifyFullWeeks, 0f, 1f)) : Lignification(s);

		// L'extrémité fine d'un apex, seule à rester vert tendre.
		private void DrawBoutTendre(in Segment s, Vector3 collet)
		{
			if (!s.IsApex) return;
			Vector3 tip = s.Base + s.Dir * s.LengthCm, de = tip - s.Dir * Mathf.Min(BoutTendreCm, s.LengthCm * 0.5f);
			DrawLine(Iso(de.X - collet.X, de.Y - collet.Y, de.Z), Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z),
				Lit(WoodRamp(LigBoutTendre)), PixelInterne * BoisArbreMinPx * 0.5f, antialiased: false);
		}

		/// <summary>Rameaux à tous les paliers, brindilles dès ×2 (en dessous, moins d'un pixel de long).</summary>
		private void DrawPetitBois()
		{
			Vector3 c = _structure.ColletCm;
			float pix = PixelInterne;
			bool brindilles = WorldView.CurrentZoom >= PalierSanteZoom;
			Color rameau = Lit(WoodRamp(LigRameau)), brindille = Lit(WoodRamp(LigBrindille));
			foreach (var e in BoisDuHouppier())
			{
				if (!e.EstRameau && !brindilles) continue;
				float w = Mathf.Max(pix, (e.EstRameau ? RameauLargeCm : BrindilleLargeCm) * WorldView.PxPerCmX);
				DrawLine(Iso(e.A.X - c.X, e.A.Y - c.Y, e.A.Z), Iso(e.B.X - c.X, e.B.Y - c.Y, e.B.Z),
					e.EstRameau ? rameau : brindille, w, antialiased: false);
			}
		}

		// ---------------------------------------------------------------------------
		// ×0,5 À ×4 — GERBES
		// ---------------------------------------------------------------------------

		/// <summary>Une gerbe par bout de petit bois. `tons` : les teintes du feuillage, tirées au hash
		/// (une aux paliers bas, celles de l'automne à ×4).</summary>
		private void DrawGerbes(Color[] tons, float density)
		{
			int palier = PalierGerbe(WorldView.CurrentZoom);
			if (palier < 0) return;
			float z = WorldView.CurrentZoom;
			Vector3 c = _structure.ColletCm;
			bool idx = Indexe;
			if (!LeafProfiles.TryGetValue(_structure.SpeciesName, out var prof)) prof = DefaultLeaf;
			bool pend = RecettesRameaux[_structure.SpeciesName].Port <= PortPendant;
			int palBois = idx ? PaletteIndexee.Palette(WoodRamp(LigRameau)) : -1;
			var palFeuilles = new int[tons.Length];
			var rampes = new Color[tons.Length][];
			bool inverse = SouthDir().Y < 0f;
			for (int t = 0; t < tons.Length; t++)
				if (idx) palFeuilles[t] = PaletteIndexee.Palette(tons[t]);
				else rampes[t] = RampeLitterale(tons[t], inverse);
			Color[] rampeBois = idx ? null : RampeLitterale(WoodRamp(LigRameau), inverse);
			float demi = GerbeDemiCm * WorldView.PxPerCmZ;
			foreach (var e in BoisDuHouppier())
			{
				// De loin, une gerbe sur trois en moins : chaque pose du vent repeint l'arbre à la cuisson.
				if (palier <= PalierGerbeLoin && Hash01(555, e.Cle, e.Rang) < PartGerbesLoin) continue;
				float zPied = e.B.Z + (pend ? demi / WorldView.PxPerCmZ : -GerbeDemiCm);
				Vector2 pied = Iso(e.B.X - c.X, e.B.Y - c.Y, zPied);
				bool feuille = Hash01(537, e.Cle, e.Rang) < density * GainDensite;
				int t = Mathf.Min(tons.Length - 1, (int)(Hash01(13, e.Cle, e.Rang) * tons.Length));
				int v = (int)(Hash01(539, e.Cle, e.Rang) * GerbeVariantes) % GerbeVariantes;
				bool miroir = Hash01(541, e.Cle, e.Rang) < 0.5f;
				// Le bois sous les feuilles serait une forêt de tiges verticales : il ne se montre que nu.
				if (idx) DrawGerbeIndexee(prof.Shape, palier, v, feuille ? CoucheGerbe.Feuilles : CoucheGerbe.Bois, pied, z,
					feuille ? palFeuilles[t] : palBois, miroir, pend);
				else DrawGerbeLitterale(prof.Shape, palier, v, feuille ? CoucheGerbe.Feuilles : CoucheGerbe.Bois, pied, z,
					feuille ? rampes[t] : rampeBois, miroir, pend);
				if (feuille && _snow > 0f && Hash01(77, e.Cle, e.Rang) < _snow * NeigeGerbes)
				{
					float d = demi * 0.6f;
					DrawSnowCrown(pied - new Vector2(0f, pend ? -demi : demi), d, d * 0.7f);
				}
			}
		}

		private static Color[] RampeLitterale(Color c, bool inverse)
		{
			Color[] rampe = RampeKit(c);
			if (inverse) (rampe[KitOmbre], rampe[KitLumiere]) = (rampe[KitLumiere], rampe[KitOmbre]);
			return rampe;
		}

		/// <summary>Paliers bas, arbre feuillé : tiges, petit bois, gerbes, fleurons (dès ×0,5), fruits.</summary>
		private void DrawHouppierBas(Color c)
		{
			DrawTigesAssemblees(WorldView.CurrentZoom);
			DrawPetitBois();
			DrawGerbes(new[] { c }, Mathf.Clamp(_structure.DensiteVisible, 0f, 1f));
			DrawFleuronsHouppier();
			DrawFruitsHouppier();
		}

		/// <summary>Paliers bas, arbre nu : le bois fin par-dessus les segments, gerbes sans feuilles.
		/// Les fleurs aussi : le cerisier fleurit avant ses feuilles (VERGER VIVANT ②).</summary>
		private void DrawHouppierNu()
		{
			DrawPetitBois();
			DrawGerbes(new[] { WoodColor }, 0f);
			DrawFleuronsHouppier();
			DrawFruitsHouppier();
		}

		/// <summary>Palier ×4 : gerbes (bois seul si l'arbre est nu), avec tons d'automne et santé.</summary>
		private void DrawGerbesPalierMasses(OrganPalette pal, float automne, float density)
		{
			var tons = new Color[automne > 0f ? 3 : 1];
			for (int t = 0; t < tons.Length; t++)
				tons[t] = Frosted(SymptomTint(LeafColor(pal, automne, (t + 0.5f) / tons.Length)));
			DrawGerbes(tons, density);
		}

		// ---------------------------------------------------------------------------
		// ×8 ET PLUS — VRAIES FEUILLES SUR LES BRINDILLES
		// ---------------------------------------------------------------------------

		// Les feuilles de la fiche, peintes comme celles des lianes (Lianes.cs, Tige) : un contour d'espèce en
		// triangles, un seul envoi pour tout l'arbre. Les ovales à motifs (DrawLeafShape, ~0,35 ms pièce
		// [figuier, ④]) lisaient comme des pompons à cette échelle, et leur coût interdisait le nombre.
		private void DrawFeuillesHouppier(Vector3 collet, OrganPalette pal, float automne, float density)
		{
			RecetteRameaux r = RecettesRameaux[_structure.SpeciesName];
			FichePort fiche = FicheLimbe(r);
			var tons = new Color[automne > 0f ? 3 : 1];
			for (int t = 0; t < tons.Length; t++)
			{
				tons[t] = Frosted(SymptomTint(LeafColor(pal, automne, (t + 0.5f) / tons.Length)));
				tons[t].A = 1f;
			}
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			_sitesPrairie.Clear();
			_feuillesPort.Clear();
			var pied = new Vector3(collet.X, collet.Y, 0f);
			float penche = r.Port <= PortPendant ? -0.8f : -0.25f;
			foreach (var e in BoisDuHouppier())
			{
				int n = e.EstRameau ? Mathf.Max(1, r.FeuillesBrin / 2) : r.FeuillesBrin;
				int i = Melange(e.Cle, e.Rang) & 0xFFFFF;   // borné : `k` reste positif
				for (int j = 0; j < n; j++)
				{
					if (Hash01(17, i, j) >= density * GainDensite) continue;
					Vector3 p = e.A.Lerp(e.B, 1f - (j + Hash01(547, i, j)) * 0.7f / n) - pied;
					p.Z = Mathf.Max(p.Z - LeafDropCm(p.Z), 0.5f);
					float l = r.LimbeCm * e.Croissance * Mathf.Lerp(0.75f, 1.1f, Hash01(549, i, j));
					AjouterFeuilleTige(fiche, p, Mathf.Tau * Hash01(551, i, j), Mathf.Max(l, 1f), Hash01(553, i, j), float.MaxValue, 1f, i * 41 + j, penche);
				}
			}
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			int compte = 0;
			foreach (var (_, fe) in _feuillesPort)
			{
				PoserFeuilleTige(fiche, fe, tons[fe.K % tons.Length]);
				if (compte++ % SiteDetailsPas == 0)
					_sitesPrairie.Add((PointFeuille(fe, 0.6f, 0f), Mathf.Max(fe.Large * 0.8f, 1.2f) * WorldView.PxPerCmX, fe.K, fe.BaseZ));
			}
			_lotPrairie.DessinerSansMaille(this);
			PoserDetailsPrairie(tons[0]);
		}

		// Fleurs : PlantRenderer.FleursArbre.cs ; fruits : PlantRenderer.FruitsArbre.cs (VERGER VIVANT ④).
	}
}
